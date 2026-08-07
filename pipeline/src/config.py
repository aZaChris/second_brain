"""Configurazione da variabili d'ambiente. Nessun default per i segreti."""

from __future__ import annotations

import os
from dataclasses import dataclass


class MissingConfigError(RuntimeError):
    pass


@dataclass(frozen=True)
class Config:
    core_api_url: str
    core_api_token: str
    stt_api_url: str
    stt_api_token: str
    captioning_api_url: str
    captioning_api_token: str
    poll_interval_seconds: float = 30.0
    max_retries: int = 3
    retry_backoff_seconds: float = 1.0

    @classmethod
    def from_env(cls) -> "Config":
        return cls(
            core_api_url=_require_env("CORE_API_URL"),
            core_api_token=_require_env("CORE_API_TOKEN"),
            stt_api_url=_require_env("STT_API_URL"),
            stt_api_token=_require_env("STT_API_TOKEN"),
            captioning_api_url=_require_env("CAPTIONING_API_URL"),
            captioning_api_token=_require_env("CAPTIONING_API_TOKEN"),
            poll_interval_seconds=float(os.environ.get("POLL_INTERVAL_SECONDS", "30")),
        )


def _require_env(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        raise MissingConfigError(f"Variabile d'ambiente mancante: {name}")
    return value
