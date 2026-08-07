import pytest

from src import storage


def make_node(node_id="node_1", source_event_id="evt_1"):
    return {
        "node_id": node_id,
        "node_type": "note",
        "label": "una nota",
        "source_event_id": source_event_id,
        "embedding_ref": None,
        "created_at": "2026-08-07T10:00:00+00:00",
    }


def make_edge(from_id="node_1", to_id="node_2"):
    return {
        "edge_id": "edge_1",
        "from_node_id": from_id,
        "to_node_id": to_id,
        "relation": "collegato-a",
        "weight": 0.8,
        "created_at": "2026-08-07T10:00:00+00:00",
    }


def test_insert_node_creates_new_node(tmp_path):
    db_path = str(tmp_path / "graph.db")
    storage.init_db(db_path)
    conn = storage.get_conn(db_path)
    saved = storage.insert_node(conn, make_node())
    assert saved["node_id"] == "node_1"
    assert storage.get_node(conn, "node_1") is not None


def test_insert_node_is_idempotent_on_source_event_id(tmp_path):
    db_path = str(tmp_path / "graph.db")
    storage.init_db(db_path)
    conn = storage.get_conn(db_path)
    first = storage.insert_node(conn, make_node(node_id="node_1", source_event_id="evt_1"))
    second = storage.insert_node(conn, make_node(node_id="node_2", source_event_id="evt_1"))
    assert first["node_id"] == second["node_id"] == "node_1"
    assert storage.get_node(conn, "node_2") is None


def test_insert_edge_between_existing_nodes(tmp_path):
    db_path = str(tmp_path / "graph.db")
    storage.init_db(db_path)
    conn = storage.get_conn(db_path)
    storage.insert_node(conn, make_node("node_1", "evt_1"))
    storage.insert_node(conn, make_node("node_2", "evt_2"))
    saved = storage.insert_edge(conn, make_edge("node_1", "node_2"))
    assert saved["edge_id"] == "edge_1"


def test_insert_edge_rejects_missing_node(tmp_path):
    db_path = str(tmp_path / "graph.db")
    storage.init_db(db_path)
    conn = storage.get_conn(db_path)
    storage.insert_node(conn, make_node("node_1", "evt_1"))
    with pytest.raises(storage.InvalidEdgeError):
        storage.insert_edge(conn, make_edge("node_1", "node_missing"))


def test_insert_edge_rejects_self_loop(tmp_path):
    db_path = str(tmp_path / "graph.db")
    storage.init_db(db_path)
    conn = storage.get_conn(db_path)
    storage.insert_node(conn, make_node("node_1", "evt_1"))
    with pytest.raises(storage.InvalidEdgeError):
        storage.insert_edge(conn, make_edge("node_1", "node_1"))
