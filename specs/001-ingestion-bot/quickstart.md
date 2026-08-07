# Quickstart: Bot Telegram di Ingestion

## Prerequisiti

- Python 3.11+
- Un bot Telegram creato con [@BotFather](https://t.me/BotFather) → `BOT_TOKEN`
- `core` in esecuzione e raggiungibile (per validare l'inoltro end-to-end); in sua assenza si
  può comunque validare whitelist/normalizzazione con i test unitari (vedi sotto)

## Setup

```bash
cd ingestion
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt   # python-telegram-bot, httpx, pytest

export BOT_TOKEN="<token da BotFather>"
export AUTHORIZED_USER_IDS="123456789"        # whitelist, CSV di user id Telegram
export CORE_EVENTS_URL="http://localhost:8000/api/events"
export CORE_API_TOKEN="<token condiviso, vedi API_CONTRACT.md>"
```

## Esecuzione

```bash
python -m src.bot
```

## Scenari di validazione (da spec.md)

1. **Testo (US1 / SC-001)**: da un account Telegram in whitelist, invia un messaggio di testo
   al bot → il bot deve rispondere con una conferma entro 5s e `core` deve ricevere un evento
   `type: text` con `content` valorizzato.
2. **Audio/immagine (US2)**: invia un vocale o una foto → l'evento ricevuto da `core` deve avere
   `type: audio`/`image` e `media_url` valorizzato, `content` nullo.
3. **Utente non autorizzato (Edge case / SC-002)**: da un account non in whitelist, invia un
   messaggio → nessuna richiesta deve arrivare a `core` (verificabile dai log del bot).
4. **Backend non disponibile (US3 / SC-003, SC-004)**: ferma `core`, invia un messaggio → nei
   log del bot si devono vedere i retry con backoff; dopo il fallimento definitivo, l'utente
   deve ricevere un messaggio che lo informa del mancato salvataggio.
5. **Tipo non supportato (Edge case)**: invia uno sticker o un video → il bot deve rispondere
   indicando che il tipo non è supportato, senza generare alcun evento.

## Test automatici

```bash
pytest tests/unit         # whitelist, normalizzazione, backoff, idempotenza (core mockato)
pytest tests/contract     # verifica che il payload rispetti API_CONTRACT.md
```
