import httpx
import pytest

from src.graph_client import GraphUnavailableError, get_related


def test_get_related_returns_parsed_data(monkeypatch):
    def fake_get(url, params=None, headers=None, timeout=None):
        return httpx.Response(200, json={"node_id": "node_1", "related": [{"node_id": "node_2", "relation": "collegato-a", "weight": 0.8}]})

    monkeypatch.setattr(httpx, "get", fake_get)
    result = get_related("node_1", 1, api_url="http://graph", api_token="t")
    assert result["related"][0]["node_id"] == "node_2"


def test_get_related_returns_none_on_404(monkeypatch):
    def fake_get(url, params=None, headers=None, timeout=None):
        return httpx.Response(404)

    monkeypatch.setattr(httpx, "get", fake_get)
    assert get_related("node_missing", 1, api_url="http://graph", api_token="t") is None


def test_get_related_raises_on_network_error(monkeypatch):
    def fake_get(url, params=None, headers=None, timeout=None):
        raise httpx.ConnectError("boom", request=httpx.Request("GET", url))

    monkeypatch.setattr(httpx, "get", fake_get)
    with pytest.raises(GraphUnavailableError):
        get_related("node_1", 1, api_url="http://graph", api_token="t")


def test_get_related_raises_on_unexpected_status(monkeypatch):
    def fake_get(url, params=None, headers=None, timeout=None):
        return httpx.Response(500)

    monkeypatch.setattr(httpx, "get", fake_get)
    with pytest.raises(GraphUnavailableError):
        get_related("node_1", 1, api_url="http://graph", api_token="t")
