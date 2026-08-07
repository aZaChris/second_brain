import logging

import pytest

from src.bot import _is_duplicate, _reply_and_forward, _seen_message_ids
from src.config import Config
from src.events import normalize_text


class FakeMessage:
    def __init__(self):
        self.replies: list[str] = []

    async def reply_text(self, text: str) -> None:
        self.replies.append(text)


def make_config(**overrides) -> Config:
    defaults = dict(
        bot_token="t",
        authorized_user_ids=frozenset({123}),
        core_events_url="http://core/api/events",
        core_api_token="token",
        max_retries=1,
        retry_backoff_seconds=0,
    )
    defaults.update(overrides)
    return Config(**defaults)


@pytest.fixture(autouse=True)
def clear_dedup_state():
    _seen_message_ids.clear()
    yield
    _seen_message_ids.clear()


def test_same_message_id_is_deduplicated():
    assert _is_duplicate(42) is False
    assert _is_duplicate(42) is True


def test_different_message_ids_are_not_duplicates():
    assert _is_duplicate(1) is False
    assert _is_duplicate(2) is False


@pytest.mark.asyncio
async def test_user_is_notified_on_permanent_delivery_failure(monkeypatch):
    def failing_send_event(*args, **kwargs):
        from src.events import EventDeliveryError

        raise EventDeliveryError("core irraggiungibile")

    monkeypatch.setattr("src.bot.send_event", failing_send_event)

    message = FakeMessage()
    config = make_config()
    logger = logging.getLogger("test")
    event = normalize_text(123, "ciao")

    await _reply_and_forward(message, config, logger, event)

    assert message.replies == ["Non sono riuscito a salvare il messaggio, riprova più tardi."]
