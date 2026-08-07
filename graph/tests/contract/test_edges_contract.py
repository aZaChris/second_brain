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


def test_create_edge_between_existing_nodes_returns_201(client):
    node_a = create_node(client, "evt_a")
    node_b = create_node(client, "evt_b")

    response = client.post(
        "/api/graph/edges",
        json={"from_node_id": node_a, "to_node_id": node_b, "relation": "collegato-a", "weight": 0.8},
        headers=AUTH_HEADERS,
    )
    assert response.status_code == 201
    assert response.json()["edge_id"].startswith("edge_")


def test_create_edge_to_missing_node_returns_400(client):
    node_a = create_node(client, "evt_a")

    response = client.post(
        "/api/graph/edges",
        json={"from_node_id": node_a, "to_node_id": "node_missing", "relation": "collegato-a", "weight": 0.8},
        headers=AUTH_HEADERS,
    )
    assert response.status_code == 400
