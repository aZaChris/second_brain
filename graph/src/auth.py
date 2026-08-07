"""Verifica del token Bearer condiviso tra moduli (API_CONTRACT.md)."""

from __future__ import annotations

from fastapi import Header, HTTPException

from .config import Config


def require_bearer_token(config: Config):
    async def _verify(authorization: str = Header(default="")) -> None:
        expected = f"Bearer {config.graph_api_token}"
        if authorization != expected:
            raise HTTPException(status_code=401, detail="token mancante o non valido")

    return _verify
