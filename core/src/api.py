"""App FastAPI: endpoint del contratto (API_CONTRACT.md sezioni 1, 2, 5)."""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from typing import Literal

from fastapi import BackgroundTasks, Depends, FastAPI, HTTPException, Query
from pydantic import BaseModel

from . import storage
from .auth import require_bearer_token
from .config import Config
from .embedding import EmbeddingError, embed
from .insight import decide_insight
from .logging_setup import configure_logging, log_event
from .similarity import cosine_similarity, find_similar, is_low_signal

_MEDIA_PREVIEWS = {"audio": "[audio] in attesa di trascrizione", "image": "[immagine] in attesa di trascrizione"}
_VALID_PENDING_TYPES = {"audio", "image"}


def build_preview(event: dict, max_length: int = 140) -> str:
    """Anteprima del contenuto per ricerca/cronologia (research.md)."""
    text = event["content"] or event["normalized_text"]
    if not text:
        return _MEDIA_PREVIEWS.get(event["type"], "[contenuto non disponibile]")
    return text if len(text) <= max_length else text[:max_length] + "..."


class EventIn(BaseModel):
    source: str
    user_id: str
    type: Literal["text", "audio", "image"]
    content: str | None = None
    media_url: str | None = None
    timestamp: str


class EventPatchIn(BaseModel):
    normalized_text: str
    pipeline_meta: dict | None = None


class PreferencesIn(BaseModel):
    interests: list[str] = []
    depth_level: Literal["minimo", "equilibrato", "approfondito"] = "equilibrato"
    notify_on: list[str] = []


def _process_event_text(event_id: str, config: Config, logger) -> None:
    """Genera l'embedding (se c'è testo), cerca collegamenti e decide se segnalarli.
    Eseguito in background: la risposta HTTP non attende questo passo (SC-001)."""
    conn = storage.get_conn(config.db_path)
    try:
        event = storage.get_event(conn, event_id)
        if event is None:
            return

        text = event["content"] if event["type"] == "text" else event["normalized_text"]
        if not text:
            return  # media senza testo ancora normalizzato (FR-003): si riprova al PATCH

        if is_low_signal(text):
            storage.update_event(conn, event_id, status="skipped_low_signal")
            log_event(logger, event_id=event_id, esito="skipped_low_signal", message="contenuto troppo generico")
            return

        try:
            vector = embed(text, api_url=config.embedding_api_url, api_token=config.embedding_api_token)
        except EmbeddingError as exc:
            log_event(logger, event_id=event_id, esito="errore_embedding", message=str(exc), level=40)
            return

        storage.update_event(conn, event_id, embedding=json.dumps(vector), status="embedded")

        saved_events = storage.get_embedded_events(conn, exclude_event_id=event_id)
        matches = find_similar(vector, saved_events, threshold=config.similarity_threshold)

        preferences = storage.get_preferences(conn, event["user_id"])
        matched_texts = {}
        for match in matches:
            matched_event = storage.get_event(conn, match.event_id)
            if matched_event:
                matched_texts[match.event_id] = matched_event["content"] or matched_event["normalized_text"] or ""

        insight = decide_insight(
            matches,
            preferences,
            current_text=text,
            matched_text_by_event_id=matched_texts,
        )
        log_event(
            logger,
            event_id=event_id,
            esito="embedded",
            message=f"matches={len(matches)} insight={'si' if insight else 'no'}",
        )
    finally:
        conn.close()


def create_app(config: Config) -> FastAPI:
    storage.init_db(config.db_path)
    logger = configure_logging()
    app = FastAPI()
    verify_token = require_bearer_token(config)

    @app.post("/api/events", status_code=201)
    async def create_event(payload: EventIn, background_tasks: BackgroundTasks, _: None = Depends(verify_token)):
        event_id = f"evt_{uuid.uuid4().hex[:8]}"
        event = {
            "event_id": event_id,
            "source": payload.source,
            "user_id": payload.user_id,
            "type": payload.type,
            "content": payload.content,
            "media_url": payload.media_url,
            "normalized_text": None,
            "embedding": None,
            "status": "received",
            "timestamp": payload.timestamp,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        conn = storage.get_conn(config.db_path)
        try:
            storage.insert_event(conn, event)
        finally:
            conn.close()

        log_event(logger, event_id=event_id, esito="ricevuto", message=f"type={payload.type}")
        background_tasks.add_task(_process_event_text, event_id, config, logger)
        return {"event_id": event_id, "status": "received"}

    @app.patch("/api/events/{event_id}")
    async def patch_event(event_id: str, payload: EventPatchIn, background_tasks: BackgroundTasks, _: None = Depends(verify_token)):
        conn = storage.get_conn(config.db_path)
        try:
            existing = storage.get_event(conn, event_id)
            if existing is None:
                raise HTTPException(status_code=404, detail="evento non trovato")
            storage.update_event(conn, event_id, normalized_text=payload.normalized_text)
        finally:
            conn.close()

        background_tasks.add_task(_process_event_text, event_id, config, logger)
        return {"event_id": event_id, "status": "normalized"}

    @app.get("/api/users/{user_id}/preferences")
    async def get_preferences(user_id: str, _: None = Depends(verify_token)):
        conn = storage.get_conn(config.db_path)
        try:
            prefs = storage.get_preferences(conn, user_id)
        finally:
            conn.close()
        return {k: v for k, v in prefs.items() if k != "user_id"}

    @app.put("/api/users/{user_id}/preferences")
    async def put_preferences(user_id: str, payload: PreferencesIn, _: None = Depends(verify_token)):
        conn = storage.get_conn(config.db_path)
        try:
            storage.upsert_preferences(conn, user_id, payload.model_dump(), datetime.now(timezone.utc).isoformat())
        finally:
            conn.close()
        return payload.model_dump()

    @app.get("/api/events/search")
    async def search_events(
        q: str = "",
        limit: int = Query(default=10, ge=1, le=50),
        _: None = Depends(verify_token),
    ):
        if not q.strip():
            return {"results": []}

        query_vector = embed(q, api_url=config.embedding_api_url, api_token=config.embedding_api_token)

        conn = storage.get_conn(config.db_path)
        try:
            candidates = storage.get_embedded_events_all(conn)
        finally:
            conn.close()

        scored = sorted(
            (
                {"event": candidate, "score": cosine_similarity(query_vector, candidate["embedding"])}
                for candidate in candidates
            ),
            key=lambda item: item["score"],
            reverse=True,
        )[:limit]

        return {
            "results": [
                {
                    "event_id": item["event"]["event_id"],
                    "preview": build_preview(item["event"]),
                    "type": item["event"]["type"],
                    "timestamp": item["event"]["timestamp"],
                    "score": item["score"],
                }
                for item in scored
            ]
        }

    @app.get("/api/events")
    async def list_events(
        before: str | None = None,
        limit: int = Query(default=20, ge=1, le=100),
        _: None = Depends(verify_token),
    ):
        conn = storage.get_conn(config.db_path)
        try:
            page = storage.get_events_page(conn, before=before, limit=limit)
        finally:
            conn.close()

        next_before = page[-1]["timestamp"] if len(page) == limit else None
        return {
            "events": [
                {
                    "event_id": event["event_id"],
                    "preview": build_preview(event),
                    "type": event["type"],
                    "timestamp": event["timestamp"],
                }
                for event in page
            ],
            "next_before": next_before,
        }

    @app.get("/api/events/pending")
    async def pending_events(
        type: str | None = None,
        limit: int = Query(default=20, ge=1, le=100),
        _: None = Depends(verify_token),
    ):
        requested = {t.strip() for t in type.split(",")} if type else set()
        types = sorted(requested & _VALID_PENDING_TYPES) or sorted(_VALID_PENDING_TYPES)

        conn = storage.get_conn(config.db_path)
        try:
            events = storage.get_pending_events(conn, types=types, limit=limit)
        finally:
            conn.close()

        return {"events": events}

    return app
