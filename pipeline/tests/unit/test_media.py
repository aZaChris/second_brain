import httpx
import pytest

from src.media import MediaUnreachableError, download_media


def test_download_media_returns_bytes_on_success(monkeypatch):
    def fake_get(url, timeout=None):
        return httpx.Response(200, content=b"audio-bytes")

    monkeypatch.setattr(httpx, "get", fake_get)
    assert download_media("http://x/file.ogg") == b"audio-bytes"


def test_download_media_raises_after_retries_on_404(monkeypatch):
    def fake_get(url, timeout=None):
        return httpx.Response(404)

    monkeypatch.setattr(httpx, "get", fake_get)
    with pytest.raises(MediaUnreachableError):
        download_media("http://x/file.ogg", max_retries=2, backoff_seconds=0)


def test_download_media_raises_after_retries_on_network_error(monkeypatch):
    def fake_get(url, timeout=None):
        raise httpx.ConnectError("boom", request=httpx.Request("GET", url))

    monkeypatch.setattr(httpx, "get", fake_get)
    with pytest.raises(MediaUnreachableError):
        download_media("http://x/file.ogg", max_retries=2, backoff_seconds=0)
