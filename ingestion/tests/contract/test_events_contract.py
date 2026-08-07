"""Verifica che il payload prodotto rispetti lo schema di POST /api/events in API_CONTRACT.md."""

from src.events import normalize_media, normalize_text

CONTRACT_FIELDS = {"source", "user_id", "type", "content", "media_url", "timestamp"}


def test_text_event_payload_matches_contract_schema():
    payload = normalize_text(123, "ciao").to_payload()
    assert set(payload.keys()) == CONTRACT_FIELDS
    assert payload["source"] == "telegram"
    assert payload["type"] == "text"
    assert payload["content"] == "ciao"
    assert payload["media_url"] is None


def test_media_event_payload_matches_contract_schema():
    payload = normalize_media(123, "image", "https://example.com/photo.jpg").to_payload()
    assert set(payload.keys()) == CONTRACT_FIELDS
    assert payload["type"] == "image"
    assert payload["content"] is None
    assert payload["media_url"] == "https://example.com/photo.jpg"
