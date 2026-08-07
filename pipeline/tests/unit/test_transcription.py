import httpx
import pytest

from src.transcription import TranscriptionError, transcribe


def test_transcribe_returns_text_on_success(monkeypatch):
    def fake_post(url, content=None, headers=None, timeout=None):
        return httpx.Response(200, json={"text": "ciao mondo"})

    monkeypatch.setattr(httpx, "post", fake_post)
    assert transcribe(b"audio", api_url="http://stt", api_token="t") == "ciao mondo"


def test_transcribe_retries_then_succeeds(monkeypatch):
    attempts = {"count": 0}

    def fake_post(url, content=None, headers=None, timeout=None):
        attempts["count"] += 1
        if attempts["count"] < 2:
            return httpx.Response(503)
        return httpx.Response(200, json={"text": "ok"})

    monkeypatch.setattr(httpx, "post", fake_post)
    result = transcribe(b"audio", api_url="http://stt", api_token="t", max_retries=3, backoff_seconds=0)
    assert result == "ok"
    assert attempts["count"] == 2


def test_transcribe_raises_after_max_retries(monkeypatch):
    def fake_post(url, content=None, headers=None, timeout=None):
        return httpx.Response(503)

    monkeypatch.setattr(httpx, "post", fake_post)
    with pytest.raises(TranscriptionError):
        transcribe(b"audio", api_url="http://stt", api_token="t", max_retries=2, backoff_seconds=0)
