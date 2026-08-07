# Quickstart: Trascrizione Audio e Captioning Immagini (Pipeline)

## Prerequisiti

- `core` in esecuzione e raggiungibile, con `GET /api/events/pending` disponibile
  (`007-core-pending-events`)
- Credenziali per un servizio esterno di STT e uno di captioning immagini

## Setup

```bash
cd pipeline
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt   # httpx, pytest

export CORE_API_URL="http://localhost:8000"
export CORE_API_TOKEN="<stesso token configurato su core, vedi DEPLOY.md>"
export STT_API_URL="<endpoint del servizio esterno di trascrizione>"
export STT_API_TOKEN="<token del servizio>"
export CAPTIONING_API_URL="<endpoint del servizio esterno di captioning>"
export CAPTIONING_API_TOKEN="<token del servizio>"
export POLL_INTERVAL_SECONDS=30
```

## Esecuzione

```bash
python -m src.worker
```

## Scenari di validazione (da spec.md)

1. **Trascrizione audio (US1 / SC-001)**: salvare un evento `type: audio` con un `media_url`
   valido su `core` → entro pochi minuti l'evento risulta aggiornato (`GET /api/events`) con
   `normalized_text` coerente col contenuto audio, e non compare più in
   `GET /api/events/pending`.
2. **Idempotenza (US1, edge case / SC-003)**: lasciare girare `pipeline` su un evento già
   trascritto → non deve ritrascriverlo (non è più in `pending`, quindi non viene nemmeno
   ripreso in considerazione).
3. **Captioning immagine (US2 / SC-002)**: come sopra, con un evento `type: image`.
4. **File irraggiungibile (US3 / SC-004)**: salvare un evento con `media_url` non valido →
   dopo i retry, l'evento riceve un `PATCH` con testo segnaposto e `pipeline_meta.status:
   "failed"`, e non resta bloccato in `pending`.
5. **Servizio esterno non disponibile (US3 / SC-004)**: simulare il servizio di
   STT/captioning non raggiungibile → `pipeline` riprova con backoff prima di considerare il
   fallimento definitivo (stesso esito del punto 4).

## Test automatici

```bash
pytest tests/unit         # media, transcription, captioning, worker (servizi esterni mockati)
pytest tests/contract     # payload PATCH conforme ad API_CONTRACT.md
```
