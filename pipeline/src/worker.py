"""Loop principale: interroga core, elabora gli eventi in attesa, invia il risultato."""

from __future__ import annotations

import time

from . import core_client
from .captioning import CaptioningError, caption
from .config import Config
from .media import MediaUnreachableError, download_media
from .transcription import TranscriptionError, transcribe


def process_event(event: dict, config: Config) -> None:
    event_id = event["event_id"]

    try:
        media_bytes = download_media(
            event["media_url"], max_retries=config.max_retries, backoff_seconds=config.retry_backoff_seconds
        )
    except MediaUnreachableError as exc:
        _patch_failure(event_id, config, reason="file_unreachable", detail=str(exc))
        return

    try:
        if event["type"] == "audio":
            text = transcribe(
                media_bytes,
                api_url=config.stt_api_url,
                api_token=config.stt_api_token,
                max_retries=config.max_retries,
                backoff_seconds=config.retry_backoff_seconds,
            )
            model_used = "stt-external"
        else:
            text = caption(
                media_bytes,
                api_url=config.captioning_api_url,
                api_token=config.captioning_api_token,
                max_retries=config.max_retries,
                backoff_seconds=config.retry_backoff_seconds,
            )
            model_used = "captioning-external"
    except (TranscriptionError, CaptioningError) as exc:
        _patch_failure(event_id, config, reason="service_unavailable", detail=str(exc))
        return

    core_client.patch_event(
        event_id,
        text,
        {"model_used": model_used, "status": "ok"},
        core_api_url=config.core_api_url,
        core_api_token=config.core_api_token,
        max_retries=config.max_retries,
        backoff_seconds=config.retry_backoff_seconds,
    )


def _patch_failure(event_id: str, config: Config, *, reason: str, detail: str) -> None:
    """Fallimento definitivo: PATCH con testo segnaposto invece di lasciare l'evento
    bloccato in pending (FR-006, FR-007, research.md)."""
    core_client.patch_event(
        event_id,
        f"[pipeline: elaborazione non riuscita — {reason}]",
        {"status": "failed", "reason": reason, "detail": detail},
        core_api_url=config.core_api_url,
        core_api_token=config.core_api_token,
        max_retries=config.max_retries,
        backoff_seconds=config.retry_backoff_seconds,
    )


def run_once(config: Config) -> int:
    events = core_client.get_pending(
        core_api_url=config.core_api_url,
        core_api_token=config.core_api_token,
        max_retries=config.max_retries,
        backoff_seconds=config.retry_backoff_seconds,
    )
    for event in events:
        process_event(event, config)
    return len(events)


def main() -> None:
    config = Config.from_env()
    while True:
        run_once(config)
        time.sleep(config.poll_interval_seconds)


if __name__ == "__main__":
    main()
