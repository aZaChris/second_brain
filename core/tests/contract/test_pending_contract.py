import pytest
from fastapi.testclient import TestClient

from src import storage
from src.api import create_app
from src.config import Config

AUTH_HEADERS = {"Authorization": "Bearer test-token"}


@pytest.fixture
def client_and_config(tmp_path):
    config = Config(
        db_path=str(tmp_path / "core.db"),
        embedding_api_url="http://unused",
        embedding_api_token="unused",
        core_api_token="test-token",
    )
    return TestClient(create_app(config)), config


def seed_event(config, event_id, type_, media_url, timestamp="2026-08-07T10:00:00+00:00", normalized_text=None, status="received"):
    conn = storage.get_conn(config.db_path)
    storage.insert_event(
        conn,
        {
            "event_id": event_id,
            "source": "telegram",
            "user_id": "tg_1",
            "type": type_,
            "content": None,
            "media_url": media_url,
            "normalized_text": normalized_text,
            "embedding": None,
            "status": status,
            "timestamp": timestamp,
            "created_at": timestamp,
        },
    )
    conn.close()


def test_pending_lists_audio_and_image_events(client_and_config):
    client, config = client_and_config
    seed_event(config, "evt_audio", "audio", "https://example.com/a.ogg")
    seed_event(config, "evt_image", "image", "https://example.com/b.jpg")

    response = client.get("/api/events/pending", headers=AUTH_HEADERS)
    assert response.status_code == 200
    events = response.json()["events"]
    assert {e["event_id"] for e in events} == {"evt_audio", "evt_image"}
    assert events[0]["media_url"] is not None


def test_pending_excludes_already_normalized_event(client_and_config):
    client, config = client_and_config
    seed_event(config, "evt_1", "audio", "https://example.com/a.ogg")
    seed_event(config, "evt_2", "audio", "https://example.com/b.ogg", normalized_text="già trascritto")

    response = client.get("/api/events/pending", headers=AUTH_HEADERS)
    event_ids = [e["event_id"] for e in response.json()["events"]]
    assert event_ids == ["evt_1"]


def test_pending_with_no_events_returns_empty_list(client_and_config):
    client, _ = client_and_config
    response = client.get("/api/events/pending", headers=AUTH_HEADERS)
    assert response.status_code == 200
    assert response.json()["events"] == []


def test_pending_filtered_by_type(client_and_config):
    client, config = client_and_config
    seed_event(config, "evt_audio", "audio", "https://example.com/a.ogg")
    seed_event(config, "evt_image", "image", "https://example.com/b.jpg")

    response = client.get("/api/events/pending?type=audio", headers=AUTH_HEADERS)
    event_ids = [e["event_id"] for e in response.json()["events"]]
    assert event_ids == ["evt_audio"]


def test_pending_ignores_invalid_type_and_falls_back_to_default(client_and_config):
    client, config = client_and_config
    seed_event(config, "evt_audio", "audio", "https://example.com/a.ogg")

    response = client.get("/api/events/pending?type=text", headers=AUTH_HEADERS)
    event_ids = [e["event_id"] for e in response.json()["events"]]
    assert event_ids == ["evt_audio"]
