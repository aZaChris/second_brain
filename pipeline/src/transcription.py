"""Client verso il servizio esterno di trascrizione (STT, principio IV della constitution).

Interfaccia minima disaccoppiata dal provider concreto (stesso pattern di core/src/embedding.py):
ci si aspetta un endpoint che accetti il file audio nel body e risponda {"text": "..."}. Se il
provider scelto in produzione usa un formato diverso, va adattato solo qui.
"""

from __future__ import annotations

import time

import httpx


class TranscriptionError(RuntimeError):
    pass


def transcribe(
    audio_bytes: bytes,
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
                content=audio_bytes,
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
                last_error = TranscriptionError("risposta del servizio STT senza campo 'text'")
            else:
                last_error = TranscriptionError(f"servizio STT ha risposto {response.status_code}")

        if attempt < max_retries - 1:
            time.sleep(backoff_seconds * (2**attempt))

    raise TranscriptionError(f"trascrizione fallita dopo {max_retries} tentativi: {last_error}") from last_error
