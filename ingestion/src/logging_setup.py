"""Logging strutturato su stdout: livello, event_id, esito. Nessun contenuto del messaggio
viene loggato (privacy-first)."""

from __future__ import annotations

import logging
import sys


def configure_logging(level: str = "INFO") -> logging.Logger:
    logging.basicConfig(
        stream=sys.stdout,
        level=level,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )
    return logging.getLogger("ingestion")


def log_event(logger: logging.Logger, *, event_id: str, esito: str, message: str, level: int = logging.INFO) -> None:
    logger.log(level, "event_id=%s esito=%s %s", event_id, esito, message)
