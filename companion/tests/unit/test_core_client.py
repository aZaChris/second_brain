import httpx
import pytest

from src.core_client import CoreUnavailableError, search_events


def test_search_events_returns_results(monkeypatch):
    def fake_get(url, params=None, headers=None, timeout=None):
        return httpx.Response(200, json={"results": [{"event_id": "evt_1", "preview": "ciao", "type": "text", "timestamp": "2026-08-07T10:00:00Z", "score": 0.9}]})

    monkeypatch.setattr(httpx, "get", fake_get)
    results = search_events("ciao", 10, api_url="http://core", api_token="t")
    assert results[0]["event_id"] == "evt_1"


def test_search_events_raises_on_network_error(monkeypatch):
    def fake_get(url, params=None, headers=None, timeout=None):
        raise httpx.ConnectError("boom", request=httpx.Request("GET", url))

    monkeypatch.setattr(httpx, "get", fake_get)
    with pytest.raises(CoreUnavailableError):
        search_events("ciao", 10, api_url="http://core", api_token="t")


def test_search_events_raises_on_unexpected_status(monkeypatch):
    def fake_get(url, params=None, headers=None, timeout=None):
        return httpx.Response(500)

    monkeypatch.setattr(httpx, "get", fake_get)
    with pytest.raises(CoreUnavailableError):
        search_events("ciao", 10, api_url="http://core", api_token="t")
