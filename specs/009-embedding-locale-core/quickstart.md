# Quickstart: validare l'embedding locale in `core`

## 1. Dipendenze

```bash
cd core && .venv/bin/pip install -r requirements.txt   # ora include sentence-transformers
```

## 2. Configurazione minima (modalità locale, default)

`core/.env`:
```bash
DB_PATH=./core.db
CORE_API_TOKEN=<segreto di sviluppo>
EMBEDDING_MODEL_CACHE=./.model-cache
# EMBEDDING_MODE non necessaria: "local" è il default
```

## 3. Avvio e primo caricamento del modello

```bash
.venv/bin/uvicorn src.main:app --port 8000
```

**Atteso**: al primo avvio, download dei pesi (~470MB, richiede rete) in
`EMBEDDING_MODEL_CACHE`; log di avvio pronto solo dopo il caricamento del modello (FR-003).

## 4. Nessuna chiamata esterna (SC-001, US1)

```bash
# in un altro terminale, monitorare eventuale traffico in uscita durante una richiesta:
curl -s -X POST http://localhost:8000/api/events \
  -H "Authorization: Bearer $CORE_API_TOKEN" -H "Content-Type: application/json" \
  -d '{"source":"test","user_id":"u1","type":"text","content":"Prova di embedding locale","timestamp":"2026-08-25T10:00:00Z"}'
```

**Atteso**: nessuna richiesta HTTP verso un endpoint esterno di embedding durante l'elaborazione
in background (verificabile con `netstat`/log applicativo — nessun endpoint esterno configurato in
modalità locale, quindi strutturalmente impossibile).

## 5. Riavvio senza ri-download (SC-003, US3)

```bash
# ferma il processo (Ctrl-C), poi riavvia:
.venv/bin/uvicorn src.main:app --port 8000
```

**Atteso**: nessun nuovo download — i pesi sono già in `EMBEDDING_MODEL_CACHE`, avvio più rapido
del primo.

## 6. Tempo di generazione entro budget (SC-002, US2)

```bash
time curl -s -X POST http://localhost:8000/api/events \
  -H "Authorization: Bearer $CORE_API_TOKEN" -H "Content-Type: application/json" \
  -d '{"source":"test","user_id":"u1","type":"text","content":"Seconda nota per testare i tempi","timestamp":"2026-08-25T10:01:00Z"}'
```

**Atteso**: la risposta HTTP torna immediatamente (elaborazione embedding in background,
invariato); controllando i log applicativi, l'embedding risulta generato entro pochi secondi
dalla ricezione.

## 7. Modalità esterna di fallback (FR-005)

```bash
# core/.env
EMBEDDING_MODE=external
EMBEDDING_API_URL=<endpoint del provider esterno>
EMBEDDING_API_TOKEN=<token del provider>
```

**Atteso**: comportamento identico a `002-core-similarity-engine` prima di questa feature
(chiamata HTTP al provider configurato).
