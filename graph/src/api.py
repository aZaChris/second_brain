"""App FastAPI: endpoint del contratto (API_CONTRACT.md sezione 3)."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Literal

from fastapi import Depends, FastAPI, HTTPException, Query
from pydantic import BaseModel

from . import storage
from .auth import require_bearer_token
from .config import Config
from .storage import InvalidEdgeError
from .traversal import bfs_related, build_adjacency


class NodeIn(BaseModel):
    node_type: Literal["project", "note", "idea", "person", "concept"]
    label: str
    source_event_id: str
    embedding_ref: str | None = None


class EdgeIn(BaseModel):
    from_node_id: str
    to_node_id: str
    relation: str
    weight: float


def create_app(config: Config) -> FastAPI:
    storage.init_db(config.db_path)
    app = FastAPI()
    verify_token = require_bearer_token(config)

    @app.post("/api/graph/nodes", status_code=201)
    async def create_node(payload: NodeIn, _: None = Depends(verify_token)):
        node = {
            "node_id": f"node_{uuid.uuid4().hex[:8]}",
            "node_type": payload.node_type,
            "label": payload.label,
            "source_event_id": payload.source_event_id,
            "embedding_ref": payload.embedding_ref,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        conn = storage.get_conn(config.db_path)
        try:
            saved = storage.insert_node(conn, node)
        finally:
            conn.close()
        return {"node_id": saved["node_id"]}

    @app.post("/api/graph/edges", status_code=201)
    async def create_edge(payload: EdgeIn, _: None = Depends(verify_token)):
        edge = {
            "edge_id": f"edge_{uuid.uuid4().hex[:8]}",
            "from_node_id": payload.from_node_id,
            "to_node_id": payload.to_node_id,
            "relation": payload.relation,
            "weight": payload.weight,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        conn = storage.get_conn(config.db_path)
        try:
            try:
                saved = storage.insert_edge(conn, edge)
            except InvalidEdgeError as exc:
                raise HTTPException(status_code=400, detail=str(exc)) from exc
        finally:
            conn.close()
        return {"edge_id": saved["edge_id"]}

    @app.get("/api/graph/related/{node_id}")
    async def get_related(node_id: str, depth: int = Query(default=1, ge=1), _: None = Depends(verify_token)):
        conn = storage.get_conn(config.db_path)
        try:
            if storage.get_node(conn, node_id) is None:
                raise HTTPException(status_code=404, detail="nodo non trovato")
            edges = storage.get_all_edges(conn)
        finally:
            conn.close()

        adjacency = build_adjacency(edges)
        related = bfs_related(node_id, adjacency, depth)
        return {
            "node_id": node_id,
            "related": [{"node_id": r.node_id, "relation": r.relation, "weight": r.weight} for r in related],
        }

    return app
