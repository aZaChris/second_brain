"""Trascrive un file audio: modello locale in-process di default (Principio IV della
constitution v2.0.0), servizio esterno HTTP come alternativa configurabile.
"""

from __future__ import annotations

import io
import time

import httpx

from .config import Config

_local_model = None  # caricato una volta da preload(), mai per singola richiesta (FR-004)


class TranscriptionError(RuntimeError):
    pass


def preload(config: Config) -> None:
    """Carica il modello locale in memoria una sola volta, se in modalità locale.
    Va chiamato una sola volta all'avvio del processo (worker.main()), non per richiesta."""
    global _local_model
    if config.stt_mode != "local" or _local_model is not None:
        return

    from faster_whisper import WhisperModel  # import pesante: solo se serve

    _local_model = WhisperModel(
        config.stt_model_name, device="cpu", compute_type="int8", download_root=config.stt_model_cache
    )


def transcribe(audio_bytes: bytes, *, config: Config) -> str:
    if config.stt_mode == "local":
        return _transcribe_local(audio_bytes)
    return _transcribe_external(
        audio_bytes,
        api_url=config.stt_api_url,
        api_token=config.stt_api_token,
        max_retries=config.max_retries,
        backoff_seconds=config.retry_backoff_seconds,
    )


def _transcribe_local(audio_bytes: bytes) -> str:
    if _local_model is None:
        raise TranscriptionError("modello locale non caricato: preload(config) non è stato chiamato all'avvio")

    try:
        segments, _info = _local_model.transcribe(io.BytesIO(audio_bytes))
        text = " ".join(segment.text.strip() for segment in segments).strip()
    except Exception as exc:  # formato non supportato, file corrotto, ecc. (FR-007)
        raise TranscriptionError(f"trascrizione locale fallita: {exc}") from exc

    if not text:
        raise TranscriptionError("trascrizione locale ha prodotto un risultato vuoto")
    return text


def _transcribe_external(
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
