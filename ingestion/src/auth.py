"""Controllo whitelist utenti autorizzati (FR-001)."""

from __future__ import annotations


def is_authorized(user_id: int, authorized_user_ids: frozenset[int]) -> bool:
    return user_id in authorized_user_ids
