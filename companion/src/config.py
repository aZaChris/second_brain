"""Configurazione da variabili d'ambiente. Nessun default per i segreti."""

from __future__ import annotations

import os
from dataclasses import dataclass


class MissingConfigError(RuntimeError):
    pass


@dataclass(frozen=True)
class Config:
    graph_api_url: str
    graph_api_token: str
    core_api_url: str
    core_api_token: str
    companion_username: str
    companion_password: str

    @classmethod
    def from_env(cls) -> "Config":
        return cls(
            graph_api_url=_require_env("GRAPH_API_URL"),
            graph_api_token=_require_env("GRAPH_API_TOKEN"),
            core_api_url=_require_env("CORE_API_URL"),
            core_api_token=_require_env("CORE_API_TOKEN"),
            companion_username=_require_env("COMPANION_USERNAME"),
            companion_password=_require_env("COMPANION_PASSWORD"),
        )


def _require_env(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        raise MissingConfigError(f"Variabile d'ambiente mancante: {name}")
    return value
