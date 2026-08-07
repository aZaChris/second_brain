"""Entrypoint del bot: long polling, whitelist, normalizzazione e inoltro a core."""

from __future__ import annotations

import time

from telegram import Message, Update
from telegram.ext import Application, ContextTypes, MessageHandler, filters

from .auth import is_authorized
from .config import Config
from .events import EventDeliveryError, NormalizedEvent, normalize_media, normalize_text, send_event
from .logging_setup import configure_logging, log_event

DEDUP_TTL_SECONDS = 600  # ponytail: set in-memory con eviction lazy, upgrade a store esterno se il bot gira in più processi

_seen_message_ids: dict[int, float] = {}


def _is_duplicate(message_id: int) -> bool:
    now = time.monotonic()
    for mid, expires_at in list(_seen_message_ids.items()):
        if expires_at <= now:
            del _seen_message_ids[mid]

    if message_id in _seen_message_ids:
        return True

    _seen_message_ids[message_id] = now + DEDUP_TTL_SECONDS
    return False


async def _reply_and_forward(message: Message, config: Config, logger, event: NormalizedEvent) -> None:
    try:
        result = send_event(
            event,
            core_events_url=config.core_events_url,
            core_api_token=config.core_api_token,
            max_retries=config.max_retries,
            backoff_seconds=config.retry_backoff_seconds,
        )
    except EventDeliveryError as exc:
        log_event(logger, event_id="-", esito="fallito", message=str(exc), level=40)
        await message.reply_text("Non sono riuscito a salvare il messaggio, riprova più tardi.")
        return

    event_id = result.get("event_id", "-")
    log_event(logger, event_id=event_id, esito="ricevuto", message=f"type={event.type}")
    await message.reply_text("Ricevuto ✅")


async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    config: Config = context.bot_data["config"]
    logger = context.bot_data["logger"]
    message = update.message
    user_id = update.effective_user.id

    if not is_authorized(user_id, config.authorized_user_ids):
        return
    if _is_duplicate(message.message_id):
        return

    event = normalize_text(user_id, message.text)
    await _reply_and_forward(message, config, logger, event)


async def handle_media(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    config: Config = context.bot_data["config"]
    logger = context.bot_data["logger"]
    message = update.message
    user_id = update.effective_user.id

    if not is_authorized(user_id, config.authorized_user_ids):
        return
    if _is_duplicate(message.message_id):
        return

    if message.voice or message.audio:
        file_id = (message.voice or message.audio).file_id
        media_type = "audio"
    else:
        file_id = message.photo[-1].file_id
        media_type = "image"

    # ponytail: usiamo l'URL temporaneo servito da Telegram come media_url; scade dopo un po',
    # upgrade a upload su storage condiviso quando pipeline ne avrà bisogno oltre quella finestra.
    tg_file = await context.bot.get_file(file_id)
    media_url = tg_file.file_path

    event = normalize_media(user_id, media_type, media_url)
    await _reply_and_forward(message, config, logger, event)


async def handle_unsupported(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    config: Config = context.bot_data["config"]
    user_id = update.effective_user.id

    if not is_authorized(user_id, config.authorized_user_ids):
        return

    await update.message.reply_text("Tipo di contenuto non supportato.")


def build_application(config: Config) -> Application:
    logger = configure_logging()
    application = Application.builder().token(config.bot_token).build()
    application.bot_data["config"] = config
    application.bot_data["logger"] = logger

    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    application.add_handler(MessageHandler(filters.VOICE | filters.AUDIO | filters.PHOTO, handle_media))
    application.add_handler(MessageHandler(~filters.TEXT & ~filters.VOICE & ~filters.AUDIO & ~filters.PHOTO, handle_unsupported))
    return application


def main() -> None:
    config = Config.from_env()
    application = build_application(config)
    application.run_polling()


if __name__ == "__main__":
    main()
