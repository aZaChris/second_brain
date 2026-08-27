"""Genera l'embedding del testo di un evento: modello locale in-process di default
(Principio IV della constitution v2.0.0), servizio esterno HTTP come alternativa configurabile
per il caso in cui la qualità del modello locale risulti insufficiente.
"""

from __future__ import annotations

import httpx

from .config import Config

_local_model = None  # caricato una volta da preload(), mai per singola richiesta (FR-003)


class EmbeddingError(RuntimeError):
    pass


def preload(config: Config) -> None:
    """Carica il modello locale in memoria una sola volta, se in modalità locale.
    Va chiamato una sola volta all'avvio del processo (main.py), non da create_app(): così i
    test che costruiscono l'app direttamente non innescano un caricamento reale del modello."""
    global _local_model
    if config.embedding_mode != "local" or _local_model is not None:
        return

    from sentence_transformers import SentenceTransformer  # import pesante: solo se serve

    _local_model = SentenceTransformer(config.embedding_model_name, cache_folder=config.embedding_model_cache)


def embed(text: str, *, config: Config, client: httpx.Client | None = None) -> list[float]:
    if config.embedding_mode == "local":
        return _embed_local(text)
    return _embed_external(
        text, api_url=config.embedding_api_url, api_token=config.embedding_api_token, client=client
    )


def _embed_local(text: str) -> list[float]:
    if _local_model is None:
        raise EmbeddingError("modello locale non caricato: preload(config) non è stato chiamato all'avvio")
    return _local_model.encode(text).tolist()


def _embed_external(
    text: str, *, api_url: str, api_token: str, client: httpx.Client | None = None
) -> list[float]:
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
