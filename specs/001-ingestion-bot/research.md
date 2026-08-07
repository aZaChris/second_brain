# Research: Bot Telegram di Ingestion

Nessun `[NEEDS CLARIFICATION]` residuo nel Technical Context: le decisioni sotto derivano
direttamente dai vincoli della constitution (Raspberry Pi, privacy-first, servizi esterni
preferiti) e dal contratto già definito in `API_CONTRACT.md`.

## Libreria Telegram

**Decision**: `python-telegram-bot`, in modalità long polling.

**Rationale**: libreria matura, async, tipizzata sugli oggetti dell'API Telegram (messaggi,
audio, foto). Il long polling evita di esporre un endpoint HTTP pubblico dal Raspberry Pi, che
tipicamente sta dietro NAT/firewall domestico — un webhook richiederebbe reverse proxy/tunnel
aggiuntivo, complessità non giustificata per un bot a basso volume.

**Alternatives considered**: `aiogram` (valida alternativa async, meno diffusa),
`pyTelegramBotAPI` (più semplice ma meno tipizzata); webhook mode (scartato per il vincolo
NAT/Raspberry Pi sopra).

## Chiamata verso `core`

**Decision**: `httpx` per una chiamata HTTP sincrona diretta a `POST /api/events`, con retry
manuale a backoff esponenziale (max 3 tentativi) implementato con un semplice loop e
`time.sleep`, senza librerie di retry dedicate.

**Rationale**: il volume è basso (uso personale) e la richiesta è singola per messaggio: una
coda/broker (Redis, RabbitMQ, Celery) aggiungerebbe un servizio da gestire sul Raspberry Pi
senza un beneficio misurabile a questo volume. Per lo stesso motivo, 3 tentativi con backoff
esponenziale in un ciclo `for` coprono il caso reale (blip di rete) senza introdurre una
dipendenza come `tenacity` per una logica di poche righe.

**Alternatives considered**: coda con broker esterno (rimandata a quando/se il volume lo
richiederà — annotato come possibile evoluzione, non implementata ora); libreria `tenacity` per
il retry (scartata, YAGNI: il backoff a 3 tentativi è poche righe di stdlib).

## Idempotenza sui duplicati Telegram

**Decision**: si usa l'`update_id`/`message_id` di Telegram come chiave per evitare di
processare due volte lo stesso messaggio recapitato più volte dall'infrastruttura Telegram
(comportamento noto in caso di retry lato Telegram sul long polling).

**Rationale**: `python-telegram-bot` espone questi identificativi nativamente; non serve uno
store esterno, un set in memoria con TTL breve basta dato che il processo gira long-running e i
duplicati arrivano ravvicinati nel tempo.

**Alternatives considered**: deduplica lato `core` tramite `event_id` — scartata come unico
meccanismo perché lo spec richiede che il bot stesso non generi eventi duplicati (FR-008), non
solo che `core` li scarti a valle.
