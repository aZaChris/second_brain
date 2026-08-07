"""Gate HTTP Basic con un utente mock (una sola coppia utente/password da env var).

Non un sistema di account: nessun database, nessuna sessione, nessun hashing con salt.
Sufficiente a non lasciare companion completamente aperto su rete locale (research.md).
"""

from __future__ import annotations

import secrets

from fastapi import Depends, HTTPException
from fastapi.security import HTTPBasic, HTTPBasicCredentials

from .config import Config

_security = HTTPBasic()


def require_user(config: Config):
    def _verify(credentials: HTTPBasicCredentials = Depends(_security)) -> None:
        valid_username = secrets.compare_digest(credentials.username, config.companion_username)
        valid_password = secrets.compare_digest(credentials.password, config.companion_password)
        if not (valid_username and valid_password):
            raise HTTPException(
                status_code=401,
                detail="credenziali non valide",
                headers={"WWW-Authenticate": "Basic"},
            )

    return _verify
