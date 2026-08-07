"""Client verso graph: GET /api/graph/related/{node_id} (API_CONTRACT.md sezione 3)."""

from __future__ import annotations

import httpx


class GraphUnavailableError(RuntimeError):
    pass


def get_related(node_id: str, depth: int, *, api_url: str, api_token: str) -> dict | None:
    """Ritorna la risposta di graph, o None se il nodo non esiste (404).
    Solleva GraphUnavailableError su errori di rete o risposte inattese."""
    try:
        response = httpx.get(
            f"{api_url}/api/graph/related/{node_id}",
            params={"depth": depth},
            headers={"Authorization": f"Bearer {api_token}"},
            timeout=10.0,
        )
    except httpx.RequestError as exc:
        raise GraphUnavailableError(f"errore di rete verso graph: {exc}") from exc

    if response.status_code == 404:
        return None
    if response.status_code != 200:
        raise GraphUnavailableError(f"graph ha risposto {response.status_code}")
    return response.json()
