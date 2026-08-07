import pytest
from fastapi.testclient import TestClient

from src.api import create_app
from src.config import Config

AUTH_HEADERS = {"Authorization": "Bearer test-token"}


@pytest.fixture
def client(tmp_path):
    config = Config(db_path=str(tmp_path / "graph.db"), graph_api_token="test-token")
    return TestClient(create_app(config))


def test_create_node_returns_201_with_node_id(client):
    response = client.post(
        "/api/graph/nodes",
        json={"node_type": "note", "label": "una nota", "source_event_id": "evt_1", "embedding_ref": "vec_1"},
        headers=AUTH_HEADERS,
    )
    assert response.status_code == 201
    assert response.json()["node_id"].startswith("node_")


def test_create_node_without_token_is_rejected(client):
    response = client.post(
        "/api/graph/nodes",
        json={"node_type": "note", "label": "una nota", "source_event_id": "evt_1"},
    )
    assert response.status_code == 401


def test_create_node_twice_for_same_source_event_returns_same_node_id(client):
    first = client.post(
        "/api/graph/nodes",
        json={"node_type": "note", "label": "una nota", "source_event_id": "evt_1"},
        headers=AUTH_HEADERS,
    )
    second = client.post(
        "/api/graph/nodes",
        json={"node_type": "note", "label": "una nota (di nuovo)", "source_event_id": "evt_1"},
        headers=AUTH_HEADERS,
    )
    assert first.json()["node_id"] == second.json()["node_id"]
