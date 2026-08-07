import pytest
from fastapi.testclient import TestClient

from src.api import create_app
from src.config import Config

AUTH_HEADERS = {"Authorization": "Bearer test-token"}


@pytest.fixture
def client(tmp_path):
    config = Config(
        db_path=str(tmp_path / "core.db"),
        embedding_api_url="http://unused",
        embedding_api_token="unused",
        core_api_token="test-token",
    )
    return TestClient(create_app(config))


def test_get_preferences_without_saved_data_returns_defaults(client):
    response = client.get("/api/users/tg_1/preferences", headers=AUTH_HEADERS)
    assert response.status_code == 200
    body = response.json()
    assert body["depth_level"] == "equilibrato"
    assert body["interests"] == []


def test_put_then_get_reflects_updated_preferences(client):
    put_response = client.put(
        "/api/users/tg_1/preferences",
        json={"interests": ["robotica", "AI"], "depth_level": "approfondito", "notify_on": ["nuova_idea"]},
        headers=AUTH_HEADERS,
    )
    assert put_response.status_code == 200

    get_response = client.get("/api/users/tg_1/preferences", headers=AUTH_HEADERS)
    body = get_response.json()
    assert body["depth_level"] == "approfondito"
    assert body["interests"] == ["robotica", "AI"]
