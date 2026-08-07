import base64

import pytest
from fastapi.testclient import TestClient

from src.api import create_app
from src.config import Config
from src.core_client import CoreUnavailableError

AUTH_HEADERS = {"Authorization": "Basic " + base64.b64encode(b"alice:s3cret").decode()}


@pytest.fixture
def client():
    config = Config(
        graph_api_url="http://unused",
        graph_api_token="unused",
        core_api_url="http://unused",
        core_api_token="unused",
        companion_username="alice",
        companion_password="s3cret",
    )
    return TestClient(create_app(config))


def test_search_without_credentials_is_rejected(client):
    response = client.get("/search?q=robotica")
    assert response.status_code == 401


def test_search_without_query_shows_only_form(client):
    response = client.get("/search", headers=AUTH_HEADERS)
    assert response.status_code == 200
    assert "form" in response.text.lower()
    assert "Nessun risultato" not in response.text


def test_search_with_results_shows_preview_type_timestamp_score(client, monkeypatch):
    monkeypatch.setattr(
        "src.api.core_client.search_events",
        lambda q, limit, **kwargs: [
            {"event_id": "evt_1", "preview": "appunti sulla robotica", "type": "text", "timestamp": "2026-08-07T10:00:00Z", "score": 0.91}
        ],
    )
    response = client.get("/search?q=robotica", headers=AUTH_HEADERS)
    assert response.status_code == 200
    assert "appunti sulla robotica" in response.text
    assert "0.91" in response.text


def test_search_with_no_results_shows_empty_message(client, monkeypatch):
    monkeypatch.setattr("src.api.core_client.search_events", lambda q, limit, **kwargs: [])
    response = client.get("/search?q=nulla", headers=AUTH_HEADERS)
    assert response.status_code == 200
    assert "Nessun risultato trovato" in response.text


def test_search_with_core_unavailable_shows_error(client, monkeypatch):
    def raise_unavailable(q, limit, **kwargs):
        raise CoreUnavailableError("boom")

    monkeypatch.setattr("src.api.core_client.search_events", raise_unavailable)
    response = client.get("/search?q=robotica", headers=AUTH_HEADERS)
    assert response.status_code == 200
    assert "Impossibile raggiungere la ricerca" in response.text
