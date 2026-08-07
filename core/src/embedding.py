"""Client verso il servizio esterno di embedding (principio IV della constitution:
servizi esterni preferiti a modelli locali pesanti).

Interfaccia minima e disaccoppiata dal provider concreto (research.md): ci si aspetta un
endpoint che accetti {"input": text} e risponda {"embedding": [float, ...]}. Se il provider
scelto in produzione usa un formato diverso, va adattato solo qui.
"""

from __future__ import annotations

import httpx


class EmbeddingError(RuntimeError):
    pass


def embed(text: str, *, api_url: str, api_token: str, client: httpx.Client | None = None) -> list[float]:
    own_client = client is None
    http_client = client or httpx.Client(timeout=10.0)
    try:
        response = http_client.post(
            api_url,
            json={"input": text},
            headers={"Authorization": f"Bearer {api_token}"},
        )
        if response.status_code != 200:
            raise EmbeddingError(f"servizio di embedding ha risposto {response.status_code}")
        vector = response.json().get("embedding")
        if not vector:
            raise EmbeddingError("risposta del servizio di embedding senza campo 'embedding'")
        return vector
    except httpx.RequestError as exc:
        raise EmbeddingError(f"errore di rete verso il servizio di embedding: {exc}") from exc
    finally:
        if own_client:
            http_client.close()
