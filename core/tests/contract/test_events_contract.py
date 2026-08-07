import pytest
from fastapi.testclient import TestClient

from src import storage
from src.api import create_app
from src.config import Config

AUTH_HEADERS = {"Authorization": "Bearer test-token"}


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setattr("src.api.embed", lambda text, **kwargs: [0.1, 0.2, 0.3])
    config = Config(
        db_path=str(tmp_path / "core.db"),
        embedding_api_url="http://unused",
        embedding_api_token="unused",
        core_api_token="test-token",
    )
    app = create_app(config)
    return TestClient(app), config


def test_post_text_event_returns_201_with_event_id(client):
    test_client, _ = client
    response = test_client.post(
        "/api/events",
        json={
            "source": "telegram",
            "user_id": "tg_1",
            "type": "text",
            "content": "una nota abbastanza lunga da avere significato",
            "media_url": None,
            "timestamp": "2026-08-07T10:00:00+00:00",
        },
        headers=AUTH_HEADERS,
    )
    assert response.status_code == 201
    body = response.json()
    assert body["event_id"].startswith("evt_")
    assert body["status"] == "received"


def test_post_event_without_token_is_rejected(client):
    test_client, _ = client
    response = test_client.post(
        "/api/events",
        json={
            "source": "telegram",
            "user_id": "tg_1",
            "type": "text",
            "content": "ciao",
            "media_url": None,
            "timestamp": "2026-08-07T10:00:00+00:00",
        },
    )
    assert response.status_code == 401


def test_post_media_event_is_accepted_without_embedding_yet(client):
    test_client, config = client
    response = test_client.post(
        "/api/events",
        json={
            "source": "telegram",
            "user_id": "tg_1",
            "type": "audio",
            "content": None,
            "media_url": "https://example.com/audio.ogg",
            "timestamp": "2026-08-07T10:00:00+00:00",
        },
        headers=AUTH_HEADERS,
    )
    assert response.status_code == 201
    event_id = response.json()["event_id"]

    conn = storage.get_conn(config.db_path)
    saved = storage.get_event(conn, event_id)
    assert saved["status"] == "received"
    assert saved["embedding"] is None


def test_patch_event_with_normalized_text_triggers_embedding(client):
    test_client, config = client
    post_response = test_client.post(
        "/api/events",
        json={
            "source": "telegram",
            "user_id": "tg_1",
            "type": "audio",
            "content": None,
            "media_url": "https://example.com/audio.ogg",
            "timestamp": "2026-08-07T10:00:00+00:00",
        },
        headers=AUTH_HEADERS,
    )
    event_id = post_response.json()["event_id"]

    patch_response = test_client.patch(
        f"/api/events/{event_id}",
        json={"normalized_text": "trascrizione abbastanza lunga da avere senso", "pipeline_meta": {"model_used": "whisper"}},
        headers=AUTH_HEADERS,
    )
    assert patch_response.status_code == 200
    assert patch_response.json()["status"] == "normalized"

    conn = storage.get_conn(config.db_path)
    saved = storage.get_event(conn, event_id)
    assert saved["status"] == "embedded"
