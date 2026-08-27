"""Configurazione da variabili d'ambiente. Nessun default per i segreti."""

from __future__ import annotations

import os
from dataclasses import dataclass


class MissingConfigError(RuntimeError):
    pass


DEFAULT_EMBEDDING_MODEL_NAME = "paraphrase-multilingual-MiniLM-L12-v2"


@dataclass(frozen=True)
class Config:
    db_path: str
    core_api_token: str
    embedding_mode: str = "local"  # "local" (default, Principio IV) | "external" (fallback)
    embedding_model_name: str = DEFAULT_EMBEDDING_MODEL_NAME
    embedding_model_cache: str | None = None
    embedding_api_url: str | None = None
    embedding_api_token: str | None = None
    similarity_threshold: float = 0.75

    @classmethod
    def from_env(cls) -> "Config":
        embedding_mode = os.environ.get("EMBEDDING_MODE", "local")
        embedding_model_name = os.environ.get("EMBEDDING_MODEL_NAME", DEFAULT_EMBEDDING_MODEL_NAME)

        if embedding_mode == "local":
            embedding_model_cache = _require_env("EMBEDDING_MODEL_CACHE")
            embedding_api_url = None
            embedding_api_token = None
        else:
            embedding_model_cache = None
            embedding_api_url = _require_env("EMBEDDING_API_URL")
            embedding_api_token = _require_env("EMBEDDING_API_TOKEN")

        return cls(
            db_path=_require_env("DB_PATH"),
            core_api_token=_require_env("CORE_API_TOKEN"),
            embedding_mode=embedding_mode,
            embedding_model_name=embedding_model_name,
            embedding_model_cache=embedding_model_cache,
            embedding_api_url=embedding_api_url,
            embedding_api_token=embedding_api_token,
        )


def _require_env(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        raise MissingConfigError(f"Variabile d'ambiente mancante: {name}")
    return value
