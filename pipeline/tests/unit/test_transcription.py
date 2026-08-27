"""Verifica transcribe()/preload() senza scaricare pesi reali (WhisperModel mockato)."""

from __future__ import annotations

import httpx
import pytest

from src import transcription
from src.config import Config
from src.transcription import TranscriptionError, transcribe


class FakeSegment:
    def __init__(self, text: str) -> None:
        self.text = text


class FakeWhisperModel:
    def __init__(self, model_name: str, *, device: str, compute_type: str, download_root: str | None) -> None:
        self.model_name = model_name
        self.download_root = download_root

    def transcribe(self, audio):
        return [FakeSegment("ciao"), FakeSegment("mondo")], object()


class EmptyWhisperModel(FakeWhisperModel):
    def transcribe(self, audio):
        return [], object()


@pytest.fixture(autouse=True)
def reset_local_model():
    transcription._local_model = None
    yield
    transcription._local_model = None


def _local_config(**overrides) -> Config:
    return Config(
        core_api_url="http://core",
        core_api_token="t",
        stt_mode="local",
        stt_model_cache="/tmp/second-brain-test-cache/stt",
        **overrides,
    )


def _external_config(**overrides) -> Config:
    return Config(
        core_api_url="http://core",
        core_api_token="t",
        stt_mode="external",
        stt_api_url="http://stt",
        stt_api_token="t",
        **overrides,
    )


def test_preload_loads_model_once_in_local_mode(monkeypatch):
    monkeypatch.setattr("faster_whisper.WhisperModel", FakeWhisperModel)
    transcription.preload(_local_config())
    assert isinstance(transcription._local_model, FakeWhisperModel)


def test_transcribe_local_returns_text_without_instantiating_http_client(monkeypatch):
    monkeypatch.setattr("faster_whisper.WhisperModel", FakeWhisperModel)
    config = _local_config()
    transcription.preload(config)

    def fail_if_called(*args, **kwargs):
        raise AssertionError("transcribe() in modalità locale non deve chiamare httpx")

    monkeypatch.setattr(httpx, "post", fail_if_called)

    assert transcribe(b"audio", config=config) == "ciao mondo"


def test_transcribe_local_without_preload_raises():
    with pytest.raises(TranscriptionError):
        transcribe(b"audio", config=_local_config())


def test_transcribe_local_raises_on_empty_result(monkeypatch):
    monkeypatch.setattr("faster_whisper.WhisperModel", EmptyWhisperModel)
    config = _local_config()
    transcription.preload(config)
    with pytest.raises(TranscriptionError):
        transcribe(b"audio", config=config)


def test_transcribe_external_returns_text_on_success(monkeypatch):
    def fake_post(url, content=None, headers=None, timeout=None):
        return httpx.Response(200, json={"text": "ciao mondo"})

    monkeypatch.setattr(httpx, "post", fake_post)
    assert transcribe(b"audio", config=_external_config()) == "ciao mondo"


def test_transcribe_external_retries_then_succeeds(monkeypatch):
    attempts = {"count": 0}

    def fake_post(url, content=None, headers=None, timeout=None):
        attempts["count"] += 1
        if attempts["count"] < 2:
            return httpx.Response(503)
        return httpx.Response(200, json={"text": "ok"})

    monkeypatch.setattr(httpx, "post", fake_post)
    result = transcribe(b"audio", config=_external_config(max_retries=3, retry_backoff_seconds=0))
    assert result == "ok"
    assert attempts["count"] == 2


def test_transcribe_external_raises_after_max_retries(monkeypatch):
    def fake_post(url, content=None, headers=None, timeout=None):
        return httpx.Response(503)

    monkeypatch.setattr(httpx, "post", fake_post)
    with pytest.raises(TranscriptionError):
        transcribe(b"audio", config=_external_config(max_retries=2, retry_backoff_seconds=0))
