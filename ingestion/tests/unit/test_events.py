import httpx
import pytest

from src.events import EventDeliveryError, normalize_media, normalize_text, send_event


def test_normalize_text_produces_text_event():
    event = normalize_text(123, "ciao")
    assert event.type == "text"
    assert event.content == "ciao"
    assert event.media_url is None
    assert event.user_id == "tg_123"


def test_normalize_media_produces_media_event_with_url():
    event = normalize_media(123, "audio", "https://example.com/file.ogg")
    assert event.type == "audio"
    assert event.content is None
    assert event.media_url == "https://example.com/file.ogg"


def test_send_event_succeeds_on_first_try():
    event = normalize_text(123, "ciao")

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(201, json={"event_id": "evt_1", "status": "received"})

    client = httpx.Client(transport=httpx.MockTransport(handler))
    result = send_event(
        event,
        core_events_url="http://core/api/events",
        core_api_token="token",
        client=client,
    )
    assert result["event_id"] == "evt_1"


def test_send_event_retries_on_503_then_succeeds():
    event = normalize_text(123, "ciao")
    attempts = {"count": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        attempts["count"] += 1
        if attempts["count"] < 3:
            return httpx.Response(503)
        return httpx.Response(201, json={"event_id": "evt_2", "status": "received"})

    client = httpx.Client(transport=httpx.MockTransport(handler))
    result = send_event(
        event,
        core_events_url="http://core/api/events",
        core_api_token="token",
        max_retries=3,
        backoff_seconds=0,
        client=client,
    )
    assert result["event_id"] == "evt_2"
    assert attempts["count"] == 3


def test_send_event_raises_after_max_retries():
    event = normalize_text(123, "ciao")

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(503)

    client = httpx.Client(transport=httpx.MockTransport(handler))
    with pytest.raises(EventDeliveryError):
        send_event(
            event,
            core_events_url="http://core/api/events",
            core_api_token="token",
            max_retries=3,
            backoff_seconds=0,
            client=client,
        )
