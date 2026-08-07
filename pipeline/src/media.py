"""Download del file referenziato da un evento (FR-006)."""

from __future__ import annotations

import time

import httpx


class MediaUnreachableError(RuntimeError):
    pass


def download_media(media_url: str, *, max_retries: int = 3, backoff_seconds: float = 1.0) -> bytes:
    last_error: Exception | None = None
    for attempt in range(max_retries):
        try:
            response = httpx.get(media_url, timeout=30.0)
        except httpx.RequestError as exc:
            last_error = exc
        else:
            if response.status_code == 200:
                return response.content
            last_error = MediaUnreachableError(f"file non raggiungibile: HTTP {response.status_code}")

        if attempt < max_retries - 1:
            time.sleep(backoff_seconds * (2**attempt))

    raise MediaUnreachableError(f"impossibile scaricare {media_url} dopo {max_retries} tentativi: {last_error}") from last_error
