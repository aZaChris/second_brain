import json

import pytest
from fastapi.testclient import TestClient

from src import storage
from src.api import create_app
from src.config import Config

AUTH_HEADERS = {"Authorization": "Bearer test-token"}


@pytest.fixture
def client_and_config(tmp_path, monkeypatch):
    def fake_embed(text, **kwargs):
        # vettore deterministico dipendente dal testo, per rendere prevedibile la similarità
        return [1.0, 0.0] if "robotica" in text.lower() else [0.0, 1.0]

    monkeypatch.setattr("src.api.embed", fake_embed)
    config = Config(
        db_path=str(tmp_path / "core.db"),
        embedding_api_url="http://unused",
        embedding_api_token="unused",
        core_api_token="test-token",
    )
    app = create_app(config)
    return TestClient(app), config


def seed_embedded_event(config, event_id, content, embedding, timestamp="2026-08-07T10:00:00+00:00"):
    conn = storage.get_conn(config.db_path)
    storage.insert_event(
        conn,
        {
            "event_id": event_id,
            "source": "telegram",
            "user_id": "tg_1",
            "type": "text",
            "content": content,
            "media_url": None,
            "normalized_text": None,
            "embedding": json.dumps(embedding),
            "status": "embedded",
            "timestamp": timestamp,
            "created_at": timestamp,
        },
    )
    conn.close()


def test_search_returns_relevant_result_with_score(client_and_config):
    client, config = client_and_config
    seed_embedded_event(config, "evt_robotica", "appunti sul braccio robotico", [1.0, 0.0])
    seed_embedded_event(config, "evt_altro", "lista della spesa", [0.0, 1.0])

    response = client.get("/api/events/search?q=robotica", headers=AUTH_HEADERS)
    assert response.status_code == 200
    results = response.json()["results"]
    assert results[0]["event_id"] == "evt_robotica"
    assert results[0]["score"] > results[1]["score"]
    assert set(results[0].keys()) == {"event_id", "preview", "type", "timestamp", "score"}


def test_search_with_no_relevant_events_returns_empty_list(client_and_config):
    client, _ = client_and_config
    response = client.get("/api/events/search?q=robotica", headers=AUTH_HEADERS)
    assert response.status_code == 200
    assert response.json()["results"] == []


def test_event_without_embedding_never_appears_in_search(client_and_config):
    client, config = client_and_config
    conn = storage.get_conn(config.db_path)
    storage.insert_event(
        conn,
        {
            "event_id": "evt_pending",
            "source": "telegram",
            "user_id": "tg_1",
            "type": "audio",
            "content": None,
            "media_url": "https://example.com/audio.ogg",
            "normalized_text": None,
            "embedding": None,
            "status": "received",
            "timestamp": "2026-08-07T10:00:00+00:00",
            "created_at": "2026-08-07T10:00:00+00:00",
        },
    )
    conn.close()

    response = client.get("/api/events/search?q=robotica", headers=AUTH_HEADERS)
    event_ids = [r["event_id"] for r in response.json()["results"]]
    assert "evt_pending" not in event_ids
