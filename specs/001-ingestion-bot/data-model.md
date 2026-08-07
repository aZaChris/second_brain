# Data Model: Bot Telegram di Ingestion

Nessuno storage persistente (principio privacy-first): le entità sotto vivono solo in memoria
per la durata dell'elaborazione di un messaggio.

## IncomingTelegramMessage

Rappresentazione del messaggio grezzo così come arriva da `python-telegram-bot`.

| Campo | Tipo | Note |
|---|---|---|
| `telegram_user_id` | int | usato per il controllo whitelist (FR-001) |
| `message_id` | int | id Telegram, usato per idempotenza (FR-008) |
| `type` | enum: `text` \| `audio` \| `image` \| `unsupported` | derivato dal contenuto del messaggio |
| `text` | str \| null | presente solo se `type == text` |
| `file_ref` | str \| null | file_id Telegram, presente solo se `type in {audio, image}` |
| `received_at` | datetime (UTC) | timestamp di arrivo |

## NormalizedEvent

Corrisponde 1:1 al body di `POST /api/events` definito in `API_CONTRACT.md` — nessun campo
aggiuntivo qui, per non duplicare/divergere dal contratto condiviso.

| Campo | Da `IncomingTelegramMessage` |
|---|---|
| `source` | costante `"telegram"` |
| `user_id` | `telegram_user_id` (prefissato, es. `tg_<id>`) |
| `type` | `type` (solo `text`/`audio`/`image`; `unsupported` non genera un evento — FR-009) |
| `content` | `text`, se `type == text`, altrimenti `null` |
| `media_url` | riferimento al file caricato su storage condiviso a partire da `file_ref`, altrimenti `null` |
| `timestamp` | `received_at` in ISO 8601 UTC |

**Validazione**: un `NormalizedEvent` con `type == text` deve avere `content` valorizzato e
`media_url` nullo; un evento con `type` in `{audio, image}` deve avere `media_url` valorizzato e
`content` nullo — mutuamente esclusivi, coerente con lo schema di `API_CONTRACT.md`.

## Chiave di idempotenza (in-memory)

Set di `message_id` già inoltrati con successo, con eviction dopo un TTL breve (es. 10 minuti):
sufficiente a coprire i doppi recapiti ravvicinati di Telegram (FR-008) senza persistenza su
disco.
