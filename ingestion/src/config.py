"""Configurazione da variabili d'ambiente. Nessun default per i segreti: il bot non deve
partire senza una configurazione esplicita (privacy-first, niente token hardcoded)."""

from __future__ import annotations

import os
from dataclasses import dataclass


class MissingConfigError(RuntimeError):
    pass


@dataclass(frozen=True)
class Config:
    bot_token: str
    authorized_user_ids: frozenset[int]
    core_events_url: str
    core_api_token: str
    max_retries: int = 3
    retry_backoff_seconds: float = 1.0

    @classmethod
    def from_env(cls) -> "Config":
        bot_token = _require_env("BOT_TOKEN")
        core_events_url = _require_env("CORE_EVENTS_URL")
        core_api_token = _require_env("CORE_API_TOKEN")
        raw_ids = _require_env("AUTHORIZED_USER_IDS")
        try:
            user_ids = frozenset(int(uid.strip()) for uid in raw_ids.split(",") if uid.strip())
        except ValueError as exc:
            raise MissingConfigError(
                f"AUTHORIZED_USER_IDS deve essere una lista di interi separati da virgola: {raw_ids!r}"
            ) from exc
        if not user_ids:
            raise MissingConfigError("AUTHORIZED_USER_IDS non può essere vuoto")

        return cls(
            bot_token=bot_token,
            authorized_user_ids=user_ids,
            core_events_url=core_events_url,
            core_api_token=core_api_token,
        )


def _require_env(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        raise MissingConfigError(f"Variabile d'ambiente mancante: {name}")
    return value
