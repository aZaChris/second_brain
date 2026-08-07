from src import storage


def make_event(event_id="evt_1", **overrides):
    event = {
        "event_id": event_id,
        "source": "telegram",
        "user_id": "tg_1",
        "type": "text",
        "content": "ciao",
        "media_url": None,
        "normalized_text": None,
        "embedding": None,
        "status": "received",
        "timestamp": "2026-08-07T10:00:00+00:00",
        "created_at": "2026-08-07T10:00:00+00:00",
    }
    event.update(overrides)
    return event


def test_insert_and_get_event(tmp_path):
    conn = storage.get_conn(str(tmp_path / "core.db"))
    storage.init_db(str(tmp_path / "core.db"))
    assert storage.insert_event(conn, make_event()) is True
    fetched = storage.get_event(conn, "evt_1")
    assert fetched["content"] == "ciao"
    assert fetched["status"] == "received"


def test_duplicate_event_id_is_idempotent(tmp_path):
    db_path = str(tmp_path / "core.db")
    storage.init_db(db_path)
    conn = storage.get_conn(db_path)
    assert storage.insert_event(conn, make_event()) is True
    assert storage.insert_event(conn, make_event()) is False


def test_update_event_sets_embedding_and_status(tmp_path):
    db_path = str(tmp_path / "core.db")
    storage.init_db(db_path)
    conn = storage.get_conn(db_path)
    storage.insert_event(conn, make_event())
    storage.update_event(conn, "evt_1", embedding="[0.1, 0.2]", status="embedded")
    fetched = storage.get_event(conn, "evt_1")
    assert fetched["status"] == "embedded"
    assert fetched["embedding"] == "[0.1, 0.2]"


def test_preferences_default_when_not_saved(tmp_path):
    db_path = str(tmp_path / "core.db")
    storage.init_db(db_path)
    conn = storage.get_conn(db_path)
    prefs = storage.get_preferences(conn, "tg_1")
    assert prefs["depth_level"] == "equilibrato"
    assert prefs["interests"] == []


def test_upsert_preferences_roundtrip(tmp_path):
    db_path = str(tmp_path / "core.db")
    storage.init_db(db_path)
    conn = storage.get_conn(db_path)
    storage.upsert_preferences(
        conn,
        "tg_1",
        {"interests": ["robotica"], "depth_level": "approfondito", "notify_on": ["nuova_idea"]},
        "2026-08-07T10:00:00+00:00",
    )
    prefs = storage.get_preferences(conn, "tg_1")
    assert prefs["depth_level"] == "approfondito"
    assert prefs["interests"] == ["robotica"]
