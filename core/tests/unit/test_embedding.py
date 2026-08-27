"""Verifica embed()/preload() senza scaricare pesi reali (SentenceTransformer mockato)."""

from __future__ import annotations

import httpx
import pytest

from src import embedding
from src.config import Config


class FakeSentenceTransformer:
    def __init__(self, model_name: str, cache_folder: str | None = None) -> None:
        self.model_name = model_name
        self.cache_folder = cache_folder

    def encode(self, text: str):
        import numpy as np

        return np.array([0.1, 0.2, 0.3, 0.4])


@pytest.fixture(autouse=True)
def reset_local_model():
    embedding._local_model = None
    yield
    embedding._local_model = None


def _local_config(**overrides) -> Config:
    return Config(
        db_path=":memory:",
        core_api_token="test-token",
        embedding_mode="local",
        embedding_model_cache="/tmp/second-brain-test-cache",
        **overrides,
    )


def _external_config(**overrides) -> Config:
    return Config(
        db_path=":memory:",
        core_api_token="test-token",
        embedding_mode="external",
        embedding_api_url="http://fake/embed",
        embedding_api_token="external-token",
        **overrides,
    )


def test_preload_loads_model_once_in_local_mode(monkeypatch):
    monkeypatch.setattr("sentence_transformers.SentenceTransformer", FakeSentenceTransformer)
    embedding.preload(_local_config())
    assert isinstance(embedding._local_model, FakeSentenceTransformer)


def test_embed_local_returns_vector_without_instantiating_http_client(monkeypatch):
    monkeypatch.setattr("sentence_transformers.SentenceTransformer", FakeSentenceTransformer)
    config = _local_config()
    embedding.preload(config)

    def fail_if_called(*args, **kwargs):
        raise AssertionError("embed() in modalità locale non deve istanziare httpx.Client")

    monkeypatch.setattr(httpx, "Client", fail_if_called)

    vector = embedding.embed("una nota di prova abbastanza lunga", config=config)
    assert vector == [0.1, 0.2, 0.3, 0.4]


def test_embed_local_without_preload_raises_embedding_error():
    config = _local_config()
    with pytest.raises(embedding.EmbeddingError):
        embedding.embed("testo qualsiasi", config=config)


def test_embed_external_uses_http_and_returns_vector():
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.headers["Authorization"] == "Bearer external-token"
        return httpx.Response(200, json={"embedding": [1.0, 2.0]})

    client = httpx.Client(transport=httpx.MockTransport(handler))
    vector = embedding.embed("testo", config=_external_config(), client=client)
    assert vector == [1.0, 2.0]


def test_embed_external_raises_on_non_200_status():
    client = httpx.Client(transport=httpx.MockTransport(lambda request: httpx.Response(500)))
    with pytest.raises(embedding.EmbeddingError):
        embedding.embed("testo", config=_external_config(), client=client)


def test_embed_external_raises_on_missing_embedding_field():
    client = httpx.Client(transport=httpx.MockTransport(lambda request: httpx.Response(200, json={})))
    with pytest.raises(embedding.EmbeddingError):
        embedding.embed("testo", config=_external_config(), client=client)
