"""Configurazione da variabili d'ambiente. Nessun default per i segreti."""

from __future__ import annotations

import os
from dataclasses import dataclass


class MissingConfigError(RuntimeError):
    pass


DEFAULT_STT_MODEL_NAME = "base"
DEFAULT_CAPTIONING_MODEL_NAME = "Salesforce/blip-image-captioning-base"


@dataclass(frozen=True)
class Config:
    core_api_url: str
    core_api_token: str
    stt_mode: str = "local"  # "local" (default, Principio IV) | "external" (fallback)
    stt_model_name: str = DEFAULT_STT_MODEL_NAME
    stt_model_cache: str | None = None
    stt_api_url: str | None = None
    stt_api_token: str | None = None
    captioning_mode: str = "local"  # indipendente da stt_mode (FR-006)
    captioning_model_name: str = DEFAULT_CAPTIONING_MODEL_NAME
    captioning_model_cache: str | None = None
    captioning_api_url: str | None = None
    captioning_api_token: str | None = None
    poll_interval_seconds: float = 30.0
    max_retries: int = 3
    retry_backoff_seconds: float = 1.0

    @classmethod
    def from_env(cls) -> "Config":
        stt_mode = os.environ.get("STT_MODE", "local")
        stt_model_name = os.environ.get("STT_MODEL_NAME", DEFAULT_STT_MODEL_NAME)
        if stt_mode == "local":
            stt_model_cache = _require_env("STT_MODEL_CACHE")
            stt_api_url = None
            stt_api_token = None
        else:
            stt_model_cache = None
            stt_api_url = _require_env("STT_API_URL")
            stt_api_token = _require_env("STT_API_TOKEN")

        captioning_mode = os.environ.get("CAPTIONING_MODE", "local")
        captioning_model_name = os.environ.get("CAPTIONING_MODEL_NAME", DEFAULT_CAPTIONING_MODEL_NAME)
        if captioning_mode == "local":
            captioning_model_cache = _require_env("CAPTIONING_MODEL_CACHE")
            captioning_api_url = None
            captioning_api_token = None
        else:
            captioning_model_cache = None
            captioning_api_url = _require_env("CAPTIONING_API_URL")
            captioning_api_token = _require_env("CAPTIONING_API_TOKEN")

        return cls(
            core_api_url=_require_env("CORE_API_URL"),
            core_api_token=_require_env("CORE_API_TOKEN"),
            stt_mode=stt_mode,
            stt_model_name=stt_model_name,
            stt_model_cache=stt_model_cache,
            stt_api_url=stt_api_url,
            stt_api_token=stt_api_token,
            captioning_mode=captioning_mode,
            captioning_model_name=captioning_model_name,
            captioning_model_cache=captioning_model_cache,
            captioning_api_url=captioning_api_url,
            captioning_api_token=captioning_api_token,
            poll_interval_seconds=float(os.environ.get("POLL_INTERVAL_SECONDS", "30")),
        )


def _require_env(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        raise MissingConfigError(f"Variabile d'ambiente mancante: {name}")
    return value
