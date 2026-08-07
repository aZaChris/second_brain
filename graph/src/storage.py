"""Accesso SQLite: nodi e relazioni (data-model.md)."""

from __future__ import annotations

import sqlite3
from typing import Any

SCHEMA = """
CREATE TABLE IF NOT EXISTS nodes (
    node_id TEXT PRIMARY KEY,
    node_type TEXT NOT NULL,
    label TEXT NOT NULL,
    source_event_id TEXT NOT NULL UNIQUE,
    embedding_ref TEXT,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS edges (
    edge_id TEXT PRIMARY KEY,
    from_node_id TEXT NOT NULL,
    to_node_id TEXT NOT NULL,
    relation TEXT NOT NULL,
    weight REAL NOT NULL,
    created_at TEXT NOT NULL
);
"""


class InvalidEdgeError(ValueError):
    pass


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


def get_node(conn: sqlite3.Connection, node_id: str) -> dict[str, Any] | None:
    row = conn.execute("SELECT * FROM nodes WHERE node_id = ?", (node_id,)).fetchone()
    return dict(row) if row else None


def get_node_by_source_event(conn: sqlite3.Connection, source_event_id: str) -> dict[str, Any] | None:
    row = conn.execute("SELECT * FROM nodes WHERE source_event_id = ?", (source_event_id,)).fetchone()
    return dict(row) if row else None


def insert_node(conn: sqlite3.Connection, node: dict[str, Any]) -> dict[str, Any]:
    """Crea il nodo, o ritorna quello già esistente per lo stesso source_event_id (FR-002)."""
    existing = get_node_by_source_event(conn, node["source_event_id"])
    if existing is not None:
        return existing

    conn.execute(
        """
        INSERT INTO nodes (node_id, node_type, label, source_event_id, embedding_ref, created_at)
        VALUES (:node_id, :node_type, :label, :source_event_id, :embedding_ref, :created_at)
        """,
        node,
    )
    conn.commit()
    return node


def insert_edge(conn: sqlite3.Connection, edge: dict[str, Any]) -> dict[str, Any]:
    """Crea la relazione. Solleva InvalidEdgeError se un nodo non esiste o è un self-loop
    (FR-004, FR-005)."""
    if edge["from_node_id"] == edge["to_node_id"]:
        raise InvalidEdgeError("una relazione non può collegare un nodo a sé stesso")
    if get_node(conn, edge["from_node_id"]) is None:
        raise InvalidEdgeError(f"nodo inesistente: {edge['from_node_id']}")
    if get_node(conn, edge["to_node_id"]) is None:
        raise InvalidEdgeError(f"nodo inesistente: {edge['to_node_id']}")

    conn.execute(
        """
        INSERT INTO edges (edge_id, from_node_id, to_node_id, relation, weight, created_at)
        VALUES (:edge_id, :from_node_id, :to_node_id, :relation, :weight, :created_at)
        """,
        edge,
    )
    conn.commit()
    return edge


def get_all_edges(conn: sqlite3.Connection) -> list[dict[str, Any]]:
    rows = conn.execute("SELECT from_node_id, to_node_id, relation, weight FROM edges").fetchall()
    return [dict(row) for row in rows]
