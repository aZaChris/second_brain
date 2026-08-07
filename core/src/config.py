"""Configurazione da variabili d'ambiente. Nessun default per i segreti."""

from __future__ import annotations

import os
from dataclasses import dataclass


class MissingConfigError(RuntimeError):
    pass


@dataclass(frozen=True)
class Config:
    db_path: str
    embedding_api_url: str
    embedding_api_token: str
    core_api_token: str
    similarity_threshold: float = 0.75

    @classmethod
    def from_env(cls) -> "Config":
        return cls(
            db_path=_require_env("DB_PATH"),
            embedding_api_url=_require_env("EMBEDDING_API_URL"),
            embedding_api_token=_require_env("EMBEDDING_API_TOKEN"),
            core_api_token=_require_env("CORE_API_TOKEN"),
        )


def _require_env(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        raise MissingConfigError(f"Variabile d'ambiente mancante: {name}")
    return value
