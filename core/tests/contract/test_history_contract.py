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


def seed_event(config, event_id, timestamp):
    conn = storage.get_conn(config.db_path)
    storage.insert_event(
        conn,
        {
            "event_id": event_id,
            "source": "telegram",
            "user_id": "tg_1",
            "type": "text",
            "content": "una nota",
            "media_url": None,
            "normalized_text": None,
            "embedding": None,
            "status": "received",
            "timestamp": timestamp,
            "created_at": timestamp,
        },
    )
    conn.close()


def test_history_returns_events_most_recent_first(client_and_config):
    client, config = client_and_config
    seed_event(config, "evt_1", "2026-08-01T10:00:00+00:00")
    seed_event(config, "evt_2", "2026-08-03T10:00:00+00:00")
    seed_event(config, "evt_3", "2026-08-02T10:00:00+00:00")

    response = client.get("/api/events", headers=AUTH_HEADERS)
    assert response.status_code == 200
    event_ids = [e["event_id"] for e in response.json()["events"]]
    assert event_ids == ["evt_2", "evt_3", "evt_1"]


def test_history_pagination_has_no_duplicates_or_gaps(client_and_config):
    client, config = client_and_config
    seed_event(config, "evt_1", "2026-08-01T10:00:00+00:00")
    seed_event(config, "evt_2", "2026-08-03T10:00:00+00:00")
    seed_event(config, "evt_3", "2026-08-02T10:00:00+00:00")

    first = client.get("/api/events?limit=2", headers=AUTH_HEADERS).json()
    assert [e["event_id"] for e in first["events"]] == ["evt_2", "evt_3"]
    assert first["next_before"] is not None

    second = client.get(f"/api/events?limit=2&before={first['next_before']}", headers=AUTH_HEADERS).json()
    assert [e["event_id"] for e in second["events"]] == ["evt_1"]
    assert second["next_before"] is None


def test_history_with_no_events_returns_empty(client_and_config):
    client, _ = client_and_config
    response = client.get("/api/events", headers=AUTH_HEADERS)
    assert response.status_code == 200
    body = response.json()
    assert body["events"] == []
    assert body["next_before"] is None
