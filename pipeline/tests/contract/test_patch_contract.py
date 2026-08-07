"""Verifica che il payload di PATCH /api/events/{event_id} rispetti API_CONTRACT.md
(sezione 2), sia sul percorso di successo sia sul fallimento definitivo."""

import httpx

from src.config import Config
from src.worker import process_event


def make_config() -> Config:
    return Config(
        core_api_url="http://core",
        core_api_token="t",
        stt_api_url="http://stt",
        stt_api_token="t",
        captioning_api_url="http://cap",
        captioning_api_token="t",
        max_retries=1,
        retry_backoff_seconds=0,
    )


def test_patch_payload_on_success_matches_contract_schema(monkeypatch):
    monkeypatch.setattr("src.worker.download_media", lambda url, **kwargs: b"bytes")
    monkeypatch.setattr("src.worker.transcribe", lambda audio, **kwargs: "trascrizione")

    captured = {}

    def fake_request(method, url, headers=None, json=None, timeout=None):
        captured["method"] = method
        captured["json"] = json
        return httpx.Response(200, json={"event_id": "evt_1", "status": "normalized"})

    monkeypatch.setattr(httpx, "request", fake_request)

    process_event({"event_id": "evt_1", "type": "audio", "media_url": "http://x/a.ogg"}, make_config())

    assert captured["method"] == "PATCH"
    assert set(captured["json"].keys()) == {"normalized_text", "pipeline_meta"}
    assert captured["json"]["normalized_text"] == "trascrizione"
    assert captured["json"]["pipeline_meta"]["status"] == "ok"
    assert "model_used" in captured["json"]["pipeline_meta"]


def test_patch_payload_on_definitive_failure_includes_reason(monkeypatch):
    from src.media import MediaUnreachableError

    def raise_unreachable(url, **kwargs):
        raise MediaUnreachableError("boom")

    monkeypatch.setattr("src.worker.download_media", raise_unreachable)

    captured = {}

    def fake_request(method, url, headers=None, json=None, timeout=None):
        captured["json"] = json
        return httpx.Response(200, json={"event_id": "evt_1", "status": "normalized"})

    monkeypatch.setattr(httpx, "request", fake_request)

    process_event({"event_id": "evt_2", "type": "audio", "media_url": "http://x/missing.ogg"}, make_config())

    assert set(captured["json"].keys()) == {"normalized_text", "pipeline_meta"}
    assert captured["json"]["normalized_text"]
    assert captured["json"]["pipeline_meta"]["status"] == "failed"
    assert captured["json"]["pipeline_meta"]["reason"] == "file_unreachable"
