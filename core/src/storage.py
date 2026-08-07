"""Accesso SQLite: eventi, embedding, preferenze utente (data-model.md)."""

from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass, field
from typing import Any

DEFAULT_DEPTH_LEVEL = "equilibrato"

SCHEMA = """
CREATE TABLE IF NOT EXISTS events (
    event_id TEXT PRIMARY KEY,
    source TEXT NOT NULL,
    user_id TEXT NOT NULL,
    type TEXT NOT NULL,
    content TEXT,
    media_url TEXT,
    normalized_text TEXT,
    embedding TEXT,
    status TEXT NOT NULL,
    timestamp TEXT NOT NULL,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS user_preferences (
    user_id TEXT PRIMARY KEY,
    interests TEXT NOT NULL,
    depth_level TEXT NOT NULL,
    notify_on TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
"""


def get_conn(db_path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def init_db(db_path: str) -> None:
    conn = get_conn(db_path)
    try:
        conn.executescript(SCHEMA)
        conn.commit()
    finally:
        conn.close()


def insert_event(conn: sqlite3.Connection, event: dict[str, Any]) -> bool:
    """Inserisce l'evento. Ritorna False se l'event_id esiste già (FR-007: idempotenza)."""
    cursor = conn.execute(
        """
        INSERT INTO events
            (event_id, source, user_id, type, content, media_url, normalized_text,
             embedding, status, timestamp, created_at)
        VALUES (:event_id, :source, :user_id, :type, :content, :media_url, :normalized_text,
                :embedding, :status, :timestamp, :created_at)
        ON CONFLICT(event_id) DO NOTHING
        """,
        event,
    )
    conn.commit()
    return cursor.rowcount > 0


def get_event(conn: sqlite3.Connection, event_id: str) -> dict[str, Any] | None:
    row = conn.execute("SELECT * FROM events WHERE event_id = ?", (event_id,)).fetchone()
    return dict(row) if row else None


def update_event(conn: sqlite3.Connection, event_id: str, **fields: Any) -> None:
    if not fields:
        return
    columns = ", ".join(f"{key} = :{key}" for key in fields)
    conn.execute(f"UPDATE events SET {columns} WHERE event_id = :event_id", {**fields, "event_id": event_id})
    conn.commit()


def get_embedded_events(conn: sqlite3.Connection, exclude_event_id: str) -> list[dict[str, Any]]:
    rows = conn.execute(
        "SELECT event_id, embedding FROM events WHERE status = 'embedded' AND event_id != ?",
        (exclude_event_id,),
    ).fetchall()
    return [{"event_id": row["event_id"], "embedding": json.loads(row["embedding"])} for row in rows]


def get_embedded_events_all(conn: sqlite3.Connection) -> list[dict[str, Any]]:
    """Tutti gli eventi con status=embedded (FR-003: base per la ricerca semantica)."""
    rows = conn.execute(
        "SELECT event_id, content, normalized_text, type, timestamp, embedding "
        "FROM events WHERE status = 'embedded'"
    ).fetchall()
    return [
        {
            "event_id": row["event_id"],
            "content": row["content"],
            "normalized_text": row["normalized_text"],
            "type": row["type"],
            "timestamp": row["timestamp"],
            "embedding": json.loads(row["embedding"]),
        }
        for row in rows
    ]


def get_events_page(conn: sqlite3.Connection, before: str | None, limit: int) -> list[dict[str, Any]]:
    """Pagina di cronologia ordinata per timestamp decrescente (keyset pagination, research.md)."""
    if before is not None:
        rows = conn.execute(
            "SELECT event_id, content, normalized_text, type, timestamp FROM events "
            "WHERE timestamp < ? ORDER BY timestamp DESC LIMIT ?",
            (before, limit),
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT event_id, content, normalized_text, type, timestamp FROM events "
            "ORDER BY timestamp DESC LIMIT ?",
            (limit,),
        ).fetchall()
    return [dict(row) for row in rows]


def get_pending_events(conn: sqlite3.Connection, types: list[str], limit: int) -> list[dict[str, Any]]:
    """Eventi audio/immagine non ancora trascritti/descritti (research.md: il segnale è
    normalized_text IS NULL, non `status`, per non dipendere dall'esito dell'embedding)."""
    if not types:
        return []
    placeholders = ",".join("?" for _ in types)
    rows = conn.execute(
        f"SELECT event_id, type, media_url, timestamp FROM events "
        f"WHERE type IN ({placeholders}) AND normalized_text IS NULL "
        f"ORDER BY timestamp ASC LIMIT ?",
        (*types, limit),
    ).fetchall()
    return [dict(row) for row in rows]


def get_preferences(conn: sqlite3.Connection, user_id: str) -> dict[str, Any]:
    row = conn.execute("SELECT * FROM user_preferences WHERE user_id = ?", (user_id,)).fetchone()
    if row is None:
        return {
            "user_id": user_id,
            "interests": [],
            "depth_level": DEFAULT_DEPTH_LEVEL,
            "notify_on": [],
        }
    return {
        "user_id": row["user_id"],
        "interests": json.loads(row["interests"]),
        "depth_level": row["depth_level"],
        "notify_on": json.loads(row["notify_on"]),
    }


def upsert_preferences(conn: sqlite3.Connection, user_id: str, prefs: dict[str, Any], updated_at: str) -> None:
    conn.execute(
        """
        INSERT INTO user_preferences (user_id, interests, depth_level, notify_on, updated_at)
        VALUES (:user_id, :interests, :depth_level, :notify_on, :updated_at)
        ON CONFLICT(user_id) DO UPDATE SET
            interests = excluded.interests,
            depth_level = excluded.depth_level,
            notify_on = excluded.notify_on,
            updated_at = excluded.updated_at
        """,
        {
            "user_id": user_id,
            "interests": json.dumps(prefs.get("interests", [])),
            "depth_level": prefs.get("depth_level", DEFAULT_DEPTH_LEVEL),
            "notify_on": json.dumps(prefs.get("notify_on", [])),
            "updated_at": updated_at,
        },
    )
    conn.commit()
