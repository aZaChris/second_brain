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

    @classmethod
    def from_env(cls) -> "Config":
        return cls(
            graph_api_url=_require_env("GRAPH_API_URL"),
            graph_api_token=_require_env("GRAPH_API_TOKEN"),
        )


def _require_env(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        raise MissingConfigError(f"Variabile d'ambiente mancante: {name}")
    return value
