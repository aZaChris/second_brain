import pytest
from fastapi.testclient import TestClient

from src.api import create_app
from src.config import Config

AUTH_HEADERS = {"Authorization": "Bearer test-token"}


@pytest.fixture
def client(tmp_path):
    config = Config(db_path=str(tmp_path / "graph.db"), graph_api_token="test-token")
    return TestClient(create_app(config))


def create_node(client, source_event_id):
    response = client.post(
        "/api/graph/nodes",
        json={"node_type": "note", "label": "nota", "source_event_id": source_event_id},
        headers=AUTH_HEADERS,
    )
    return response.json()["node_id"]


def test_related_returns_direct_neighbors_with_relation_and_weight(client):
    node_a = create_node(client, "evt_a")
    node_b = create_node(client, "evt_b")
    client.post(
        "/api/graph/edges",
        json={"from_node_id": node_a, "to_node_id": node_b, "relation": "collegato-a", "weight": 0.8},
        headers=AUTH_HEADERS,
    )

    response = client.get(f"/api/graph/related/{node_a}?depth=1", headers=AUTH_HEADERS)
    assert response.status_code == 200
    body = response.json()
    assert body["node_id"] == node_a
    assert body["related"] == [{"node_id": node_b, "relation": "collegato-a", "weight": 0.8}]


def test_related_for_isolated_node_returns_empty_list(client):
    node_a = create_node(client, "evt_a")
    response = client.get(f"/api/graph/related/{node_a}", headers=AUTH_HEADERS)
    assert response.status_code == 200
    assert response.json()["related"] == []


def test_related_for_missing_node_returns_404(client):
    response = client.get("/api/graph/related/node_missing", headers=AUTH_HEADERS)
    assert response.status_code == 404
