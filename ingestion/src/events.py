"""Normalizzazione dei messaggi in eventi e invio a core (POST /api/events, API_CONTRACT.md)."""

from __future__ import annotations

import time
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Literal

import httpx

EventType = Literal["text", "audio", "image"]


class EventDeliveryError(RuntimeError):
    """Sollevato quando l'invio a core fallisce dopo tutti i retry (FR-007)."""


@dataclass(frozen=True)
class NormalizedEvent:
    source: str
    user_id: str
    type: EventType
    content: str | None
    media_url: str | None
    timestamp: str

    def to_payload(self) -> dict:
        return {
            "source": self.source,
            "user_id": self.user_id,
            "type": self.type,
            "content": self.content,
            "media_url": self.media_url,
            "timestamp": self.timestamp,
        }


def normalize_text(telegram_user_id: int, text: str, received_at: datetime | None = None) -> NormalizedEvent:
    return NormalizedEvent(
        source="telegram",
        user_id=f"tg_{telegram_user_id}",
        type="text",
        content=text,
        media_url=None,
        timestamp=_iso(received_at),
    )


def normalize_media(
    telegram_user_id: int,
    media_type: Literal["audio", "image"],
    media_url: str,
    received_at: datetime | None = None,
) -> NormalizedEvent:
    return NormalizedEvent(
        source="telegram",
        user_id=f"tg_{telegram_user_id}",
        type=media_type,
        content=None,
        media_url=media_url,
        timestamp=_iso(received_at),
    )


def _iso(received_at: datetime | None) -> str:
    return (received_at or datetime.now(timezone.utc)).isoformat()


def send_event(
    event: NormalizedEvent,
    *,
    core_events_url: str,
    core_api_token: str,
    max_retries: int = 3,
    backoff_seconds: float = 1.0,
    client: httpx.Client | None = None,
) -> dict:
    """Invia l'evento a core con retry a backoff esponenziale (FR-006).

    Riprova solo su errori transitori (timeout, errori di rete, 503); un 400 è un
    errore permanente del payload e non va ritentato.
    """
    own_client = client is None
    http_client = client or httpx.Client(timeout=10.0)
    headers = {"Authorization": f"Bearer {core_api_token}"}
    last_error: Exception | None = None

    try:
        for attempt in range(max_retries):
            try:
                response = http_client.post(core_events_url, json=event.to_payload(), headers=headers)
            except httpx.RequestError as exc:
                last_error = exc
            else:
                if response.status_code in (200, 201):
                    return response.json()
                if response.status_code == 503:
                    last_error = EventDeliveryError(f"core non disponibile (503) al tentativo {attempt + 1}")
                else:
                    response.raise_for_status()

            if attempt < max_retries - 1:
                time.sleep(backoff_seconds * (2**attempt))

        raise EventDeliveryError(
            f"invio evento fallito dopo {max_retries} tentativi: {last_error}"
        ) from last_error
    finally:
        if own_client:
            http_client.close()
