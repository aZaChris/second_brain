import pytest
from fastapi.testclient import TestClient

from src.api import create_app
from src.config import Config
from src.graph_client import GraphUnavailableError


@pytest.fixture
def client():
    config = Config(graph_api_url="http://unused", graph_api_token="unused")
    return TestClient(create_app(config))


def test_explore_without_node_id_shows_only_form(client):
    response = client.get("/explore")
    assert response.status_code == 200
    assert "form" in response.text.lower()
    assert "Nodo non trovato" not in response.text


def test_explore_with_related_nodes_shows_relation_and_weight(client, monkeypatch):
    monkeypatch.setattr(
        "src.api.graph_client.get_related",
        lambda node_id, depth, **kwargs: {
            "node_id": node_id,
            "related": [{"node_id": "node_2", "relation": "collegato-a", "weight": 0.8}],
        },
    )
    response = client.get("/explore?node_id=node_1")
    assert response.status_code == 200
    assert "node_2" in response.text
    assert "collegato-a" in response.text
    assert "0.8" in response.text


def test_explore_with_no_related_nodes_shows_empty_message(client, monkeypatch):
    monkeypatch.setattr(
        "src.api.graph_client.get_related",
        lambda node_id, depth, **kwargs: {"node_id": node_id, "related": []},
    )
    response = client.get("/explore?node_id=node_isolated")
    assert response.status_code == 200
    assert "Nessun collegamento trovato" in response.text


def test_explore_with_missing_node_shows_clear_message(client, monkeypatch):
    monkeypatch.setattr("src.api.graph_client.get_related", lambda node_id, depth, **kwargs: None)
    response = client.get("/explore?node_id=node_missing")
    assert response.status_code == 200
    assert "Nodo non trovato" in response.text


def test_explore_with_graph_unavailable_shows_error(client, monkeypatch):
    def raise_unavailable(node_id, depth, **kwargs):
        raise GraphUnavailableError("boom")

    monkeypatch.setattr("src.api.graph_client.get_related", raise_unavailable)
    response = client.get("/explore?node_id=node_1")
    assert response.status_code == 200
    assert "Impossibile raggiungere il grafo" in response.text
