"""Client verso core: GET /api/events/search (API_CONTRACT.md sezione 6)."""

from __future__ import annotations

import httpx


class CoreUnavailableError(RuntimeError):
    pass


def search_events(q: str, limit: int, *, api_url: str, api_token: str) -> list[dict]:
    try:
        response = httpx.get(
            f"{api_url}/api/events/search",
            params={"q": q, "limit": limit},
            headers={"Authorization": f"Bearer {api_token}"},
            timeout=10.0,
        )
    except httpx.RequestError as exc:
        raise CoreUnavailableError(f"errore di rete verso core: {exc}") from exc

    if response.status_code != 200:
        raise CoreUnavailableError(f"core ha risposto {response.status_code}")
    return response.json()["results"]
