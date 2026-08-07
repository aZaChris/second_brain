"""BFS su un dizionario di adiacenza costruito dalle relazioni (FR-006, FR-007, FR-009).

Le relazioni sono trattate come non orientate (assumption in spec.md): l'adiacenza include
ogni arco in entrambe le direzioni.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

Adjacency = dict[str, list[tuple[str, str, float]]]


@dataclass(frozen=True)
class Related:
    node_id: str
    relation: str
    weight: float


def build_adjacency(edges: list[dict[str, Any]]) -> Adjacency:
    adjacency: Adjacency = {}
    for edge in edges:
        adjacency.setdefault(edge["from_node_id"], []).append(
            (edge["to_node_id"], edge["relation"], edge["weight"])
        )
        adjacency.setdefault(edge["to_node_id"], []).append(
            (edge["from_node_id"], edge["relation"], edge["weight"])
        )
    return adjacency


def bfs_related(node_id: str, adjacency: Adjacency, depth: int) -> list[Related]:
    visited = {node_id}
    found: dict[str, Related] = {}
    frontier = [node_id]

    for _ in range(max(depth, 0)):
        next_frontier: list[str] = []
        for current in frontier:
            for neighbor_id, relation, weight in adjacency.get(current, []):
                if neighbor_id in visited:
                    continue
                visited.add(neighbor_id)
                found[neighbor_id] = Related(neighbor_id, relation, weight)
                next_frontier.append(neighbor_id)
        frontier = next_frontier
        if not frontier:
            break  # profondità richiesta oltre l'estensione reale del grafo (FR-009)

    return list(found.values())
