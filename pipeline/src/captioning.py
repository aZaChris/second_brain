"""Client verso il servizio esterno di captioning immagini (principio IV della constitution).

Stessa interfaccia minima di transcription.py: endpoint che accetta l'immagine nel body e
risponde {"text": "..."}, adattabile in questo solo file se il provider scelto differisce.
"""

from __future__ import annotations

import time

import httpx


class CaptioningError(RuntimeError):
    pass


def caption(
    image_bytes: bytes,
    *,
    api_url: str,
    api_token: str,
    max_retries: int = 3,
    backoff_seconds: float = 1.0,
) -> str:
    last_error: Exception | None = None
    for attempt in range(max_retries):
        try:
            response = httpx.post(
                api_url,
                content=image_bytes,
                headers={"Authorization": f"Bearer {api_token}", "Content-Type": "application/octet-stream"},
                timeout=60.0,
            )
        except httpx.RequestError as exc:
            last_error = exc
        else:
            if response.status_code == 200:
                text = response.json().get("text")
                if text:
                    return text
                last_error = CaptioningError("risposta del servizio di captioning senza campo 'text'")
            else:
                last_error = CaptioningError(f"servizio di captioning ha risposto {response.status_code}")

        if attempt < max_retries - 1:
            time.sleep(backoff_seconds * (2**attempt))

    raise CaptioningError(f"captioning fallito dopo {max_retries} tentativi: {last_error}") from last_error
