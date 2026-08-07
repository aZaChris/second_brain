"""Client verso core: GET /api/events/pending, PATCH /api/events/{event_id}
(API_CONTRACT.md sezioni 2, 8)."""

from __future__ import annotations

import time

import httpx


class CoreUnavailableError(RuntimeError):
    pass


def get_pending(
    *,
    core_api_url: str,
    core_api_token: str,
    types: list[str] | None = None,
    limit: int = 20,
    max_retries: int = 3,
    backoff_seconds: float = 1.0,
) -> list[dict]:
    params = {"limit": limit}
    if types:
        params["type"] = ",".join(types)

    response = _request_with_retry(
        "GET",
        f"{core_api_url}/api/events/pending",
        headers={"Authorization": f"Bearer {core_api_token}"},
        params=params,
        max_retries=max_retries,
        backoff_seconds=backoff_seconds,
    )
    return response.json()["events"]


def patch_event(
    event_id: str,
    normalized_text: str,
    pipeline_meta: dict,
    *,
    core_api_url: str,
    core_api_token: str,
    max_retries: int = 3,
    backoff_seconds: float = 1.0,
) -> None:
    _request_with_retry(
        "PATCH",
        f"{core_api_url}/api/events/{event_id}",
        headers={"Authorization": f"Bearer {core_api_token}"},
        json={"normalized_text": normalized_text, "pipeline_meta": pipeline_meta},
        max_retries=max_retries,
        backoff_seconds=backoff_seconds,
    )


def _request_with_retry(
    method: str,
    url: str,
    *,
    max_retries: int,
    backoff_seconds: float,
    **kwargs,
) -> httpx.Response:
    last_error: Exception | None = None
    for attempt in range(max_retries):
        try:
            response = httpx.request(method, url, timeout=10.0, **kwargs)
        except httpx.RequestError as exc:
            last_error = exc
        else:
            if response.status_code < 300:
                return response
            last_error = CoreUnavailableError(f"core ha risposto {response.status_code}")

        if attempt < max_retries - 1:
            time.sleep(backoff_seconds * (2**attempt))

    raise CoreUnavailableError(f"{method} {url} fallita dopo {max_retries} tentativi: {last_error}") from last_error
