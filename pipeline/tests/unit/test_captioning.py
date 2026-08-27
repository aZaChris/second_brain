"""Verifica caption()/preload() senza scaricare pesi reali (classi BLIP mockate)."""

from __future__ import annotations

import io

import httpx
import pytest
from PIL import Image

from src import captioning
from src.captioning import CaptioningError, caption
from src.config import Config


def _fake_image_bytes() -> bytes:
    buf = io.BytesIO()
    Image.new("RGB", (1, 1)).save(buf, format="PNG")
    return buf.getvalue()


class FakeProcessor:
    def __call__(self, image, return_tensors=None):
        return {}

    def decode(self, output_ids, skip_special_tokens=True):
        return output_ids  # il fake modello ritorna già la stringa attesa


class FakeModel:
    generated_text = "una foto di prova"

    def generate(self, **inputs):
        return [type(self).generated_text]


class EmptyModel(FakeModel):
    generated_text = ""


@pytest.fixture(autouse=True)
def reset_local_model():
    captioning._local_processor = None
    captioning._local_model = None
    yield
    captioning._local_processor = None
    captioning._local_model = None


def _local_config(**overrides) -> Config:
    return Config(
        core_api_url="http://core",
        core_api_token="t",
        captioning_mode="local",
        captioning_model_cache="/tmp/second-brain-test-cache/captioning",
        **overrides,
    )


def _external_config(**overrides) -> Config:
    return Config(
        core_api_url="http://core",
        core_api_token="t",
        captioning_mode="external",
        captioning_api_url="http://cap",
        captioning_api_token="t",
        **overrides,
    )


def _patch_blip(monkeypatch, model=None):
    monkeypatch.setattr("src.captioning._load_processor", lambda name, cache_dir: FakeProcessor())
    monkeypatch.setattr("src.captioning._load_model", lambda name, cache_dir: model or FakeModel())


def test_preload_loads_model_once_in_local_mode(monkeypatch):
    _patch_blip(monkeypatch)
    captioning.preload(_local_config())
    assert isinstance(captioning._local_model, FakeModel)
    assert isinstance(captioning._local_processor, FakeProcessor)


def test_caption_local_returns_text_without_instantiating_http_client(monkeypatch):
    _patch_blip(monkeypatch)
    config = _local_config()
    captioning.preload(config)

    def fail_if_called(*args, **kwargs):
        raise AssertionError("caption() in modalità locale non deve chiamare httpx")

    monkeypatch.setattr(httpx, "post", fail_if_called)

    assert caption(_fake_image_bytes(), config=config) == "una foto di prova"


def test_caption_local_without_preload_raises():
    with pytest.raises(CaptioningError):
        caption(_fake_image_bytes(), config=_local_config())


def test_caption_local_raises_on_empty_result(monkeypatch):
    _patch_blip(monkeypatch, model=EmptyModel())
    config = _local_config()
    captioning.preload(config)
    with pytest.raises(CaptioningError):
        caption(_fake_image_bytes(), config=config)


def test_caption_external_returns_text_on_success(monkeypatch):
    def fake_post(url, content=None, headers=None, timeout=None):
        return httpx.Response(200, json={"text": "una foto di un gatto"})

    monkeypatch.setattr(httpx, "post", fake_post)
    assert caption(b"image", config=_external_config()) == "una foto di un gatto"


def test_caption_external_retries_then_succeeds(monkeypatch):
    attempts = {"count": 0}

    def fake_post(url, content=None, headers=None, timeout=None):
        attempts["count"] += 1
        if attempts["count"] < 2:
            return httpx.Response(503)
        return httpx.Response(200, json={"text": "ok"})

    monkeypatch.setattr(httpx, "post", fake_post)
    result = caption(b"image", config=_external_config(max_retries=3, retry_backoff_seconds=0))
    assert result == "ok"
    assert attempts["count"] == 2


def test_caption_external_raises_after_max_retries(monkeypatch):
    def fake_post(url, content=None, headers=None, timeout=None):
        return httpx.Response(503)

    monkeypatch.setattr(httpx, "post", fake_post)
    with pytest.raises(CaptioningError):
        caption(b"image", config=_external_config(max_retries=2, retry_backoff_seconds=0))
