# ingestion

Bot Telegram: riceve messaggi da utenti in whitelist e li inoltra come evento normalizzato a
`core`, secondo [`../API_CONTRACT.md`](../API_CONTRACT.md).

Design e task: [`../specs/001-ingestion-bot/`](../specs/001-ingestion-bot/).

## Setup

```bash
cd ingestion
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

export BOT_TOKEN="<token da BotFather>"
export AUTHORIZED_USER_IDS="123456789"
export CORE_EVENTS_URL="http://localhost:8000/api/events"
export CORE_API_TOKEN="<token condiviso, vedi API_CONTRACT.md>"

python -m src.bot
```

## Test

```bash
pytest
```

Vedi [`../specs/001-ingestion-bot/quickstart.md`](../specs/001-ingestion-bot/quickstart.md) per
gli scenari di validazione end-to-end.
