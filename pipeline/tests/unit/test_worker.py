from src.captioning import CaptioningError
from src.config import Config
from src.media import MediaUnreachableError
from src.transcription import TranscriptionError
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


def test_audio_event_transcribed_and_patched_with_success(monkeypatch):
    monkeypatch.setattr("src.worker.download_media", lambda url, **kwargs: b"bytes")
    monkeypatch.setattr("src.worker.transcribe", lambda audio, **kwargs: "trascrizione")

    calls = []
    monkeypatch.setattr(
        "src.worker.core_client.patch_event",
        lambda event_id, text, meta, **kwargs: calls.append((event_id, text, meta)),
    )

    process_event({"event_id": "evt_1", "type": "audio", "media_url": "http://x/a.ogg"}, make_config())

    assert calls == [("evt_1", "trascrizione", {"model_used": "stt-external", "status": "ok"})]


def test_image_event_captioned_and_patched_with_success(monkeypatch):
    monkeypatch.setattr("src.worker.download_media", lambda url, **kwargs: b"bytes")
    monkeypatch.setattr("src.worker.caption", lambda image, **kwargs: "descrizione")

    calls = []
    monkeypatch.setattr(
        "src.worker.core_client.patch_event",
        lambda event_id, text, meta, **kwargs: calls.append((event_id, text, meta)),
    )

    process_event({"event_id": "evt_2", "type": "image", "media_url": "http://x/b.jpg"}, make_config())

    assert calls == [("evt_2", "descrizione", {"model_used": "captioning-external", "status": "ok"})]


def test_unreachable_media_patches_placeholder_with_failed_status(monkeypatch):
    def raise_unreachable(url, **kwargs):
        raise MediaUnreachableError("boom")

    monkeypatch.setattr("src.worker.download_media", raise_unreachable)

    calls = []
    monkeypatch.setattr(
        "src.worker.core_client.patch_event",
        lambda event_id, text, meta, **kwargs: calls.append((event_id, text, meta)),
    )

    process_event({"event_id": "evt_3", "type": "audio", "media_url": "http://x/missing.ogg"}, make_config())

    assert len(calls) == 1
    event_id, text, meta = calls[0]
    assert event_id == "evt_3"
    assert "non riuscita" in text
    assert meta["status"] == "failed"
    assert meta["reason"] == "file_unreachable"


def test_external_service_unavailable_patches_placeholder_with_failed_status(monkeypatch):
    monkeypatch.setattr("src.worker.download_media", lambda url, **kwargs: b"bytes")

    def raise_unavailable(audio, **kwargs):
        raise TranscriptionError("boom")

    monkeypatch.setattr("src.worker.transcribe", raise_unavailable)

    calls = []
    monkeypatch.setattr(
        "src.worker.core_client.patch_event",
        lambda event_id, text, meta, **kwargs: calls.append((event_id, text, meta)),
    )

    process_event({"event_id": "evt_4", "type": "audio", "media_url": "http://x/a.ogg"}, make_config())

    assert len(calls) == 1
    _, text, meta = calls[0]
    assert meta["status"] == "failed"
    assert meta["reason"] == "service_unavailable"
