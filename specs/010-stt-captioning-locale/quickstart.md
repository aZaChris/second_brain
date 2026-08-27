# Quickstart: validare STT e captioning locali in `pipeline`

## 1. Dipendenze

```bash
cd pipeline && .venv/bin/pip install torch --index-url https://download.pytorch.org/whl/cpu
.venv/bin/pip install -r requirements.txt   # ora include faster-whisper, transformers
```

## 2. Configurazione minima (modalità locale, default per entrambe)

`pipeline/.env`:
```bash
CORE_API_URL=http://localhost:8000
CORE_API_TOKEN=<segreto di sviluppo, stesso di core/.env>
STT_MODEL_CACHE=./.model-cache/stt
CAPTIONING_MODEL_CACHE=./.model-cache/captioning
# STT_MODE/CAPTIONING_MODE non necessarie: "local" è il default per entrambe
```

## 3. Avvio e primo caricamento dei modelli

```bash
.venv/bin/python -m src.worker
```

**Atteso**: al primo avvio, download dei pesi di entrambi i modelli (STT ~150MB per `base` int8,
captioning ~990MB per BLIP-base, richiede rete) nelle rispettive cache; il worker inizia il primo
poll solo dopo che entrambi i modelli sono caricati (FR-004).

## 4. Nessuna chiamata esterna (SC-001, US1)

Con `core` in esecuzione e un evento audio/immagine in stato `pending` (creato via `ingestion` o
direttamente via `POST /api/events` su `core`), il worker lo elabora al poll successivo.

**Atteso**: nessuna richiesta HTTP verso un endpoint esterno di STT/captioning durante
l'elaborazione (strutturalmente impossibile: nessun `STT_API_URL`/`CAPTIONING_API_URL`
configurato in modalità locale).

## 5. Riavvio senza ri-download (SC-003, US3)

```bash
# ferma il processo (Ctrl-C), poi riavvia:
.venv/bin/python -m src.worker
```

**Atteso**: nessun nuovo download — i pesi sono già nelle cache configurate, avvio più rapido del
primo.

## 6. Tempo di elaborazione entro budget (SC-002, US2)

Inviare un evento audio (nota vocale breve) e un evento immagine (una foto), misurare il tempo
dalla creazione dell'evento (`status=received`, `normalized_text=null`) alla sua elaborazione
(`normalized_text` valorizzato, visibile via `GET /api/events/pending` che non lo elenca più).

**Atteso**: entrambi entro pochi minuti (stesso budget di `006-pipeline-transcription-captioning`).

## 7. Modalità esterna di fallback, indipendente per audio/immagine (FR-006)

```bash
# pipeline/.env — esempio: solo STT esterno, captioning resta locale
STT_MODE=external
STT_API_URL=<endpoint del provider esterno>
STT_API_TOKEN=<token del provider>
# CAPTIONING_MODE non impostata: resta "local"
```

**Atteso**: la trascrizione usa il servizio esterno configurato, il captioning continua a usare il
modello locale — le due modalità sono indipendenti.
