import httpx
import pytest

from src.captioning import CaptioningError, caption


def test_caption_returns_text_on_success(monkeypatch):
    def fake_post(url, content=None, headers=None, timeout=None):
        return httpx.Response(200, json={"text": "una foto di un gatto"})

    monkeypatch.setattr(httpx, "post", fake_post)
    assert caption(b"image", api_url="http://cap", api_token="t") == "una foto di un gatto"


def test_caption_retries_then_succeeds(monkeypatch):
    attempts = {"count": 0}

    def fake_post(url, content=None, headers=None, timeout=None):
        attempts["count"] += 1
        if attempts["count"] < 2:
            return httpx.Response(503)
        return httpx.Response(200, json={"text": "ok"})

    monkeypatch.setattr(httpx, "post", fake_post)
    result = caption(b"image", api_url="http://cap", api_token="t", max_retries=3, backoff_seconds=0)
    assert result == "ok"
    assert attempts["count"] == 2


def test_caption_raises_after_max_retries(monkeypatch):
    def fake_post(url, content=None, headers=None, timeout=None):
        return httpx.Response(503)

    monkeypatch.setattr(httpx, "post", fake_post)
    with pytest.raises(CaptioningError):
        caption(b"image", api_url="http://cap", api_token="t", max_retries=2, backoff_seconds=0)
