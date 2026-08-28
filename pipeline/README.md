# pipeline

Trascrizione audio e captioning immagini per gli eventi audio/immagine già salvati in `core`
(non prima: `ingestion` invia l'evento direttamente a `core`, `pipeline` lo arricchisce dopo).
Interroga periodicamente `GET /api/events/pending` e invia il risultato con
`PATCH /api/events/{event_id}`, secondo [`../API_CONTRACT.md`](../API_CONTRACT.md).

Design e task: [`../specs/006-pipeline-transcription-captioning/`](../specs/006-pipeline-transcription-captioning/).

## Setup

```bash
cd pipeline
python -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt

export CORE_API_URL="http://localhost:8000"
export CORE_API_TOKEN="<stesso token configurato su core, vedi ../DEPLOY.md>"
export STT_API_URL="<endpoint del servizio esterno di trascrizione>"
export STT_API_TOKEN="<token del servizio>"
export CAPTIONING_API_URL="<endpoint del servizio esterno di captioning>"
export CAPTIONING_API_TOKEN="<token del servizio>"
export POLL_INTERVAL_SECONDS=30

python -m src.worker
```

> In alternativa a `venv`+`pip`: `uv venv` + `uv pip install -r requirements-dev.txt`
> ([astral.sh/uv](https://astral.sh/uv)) — stessi file di requirements, ma condivide su disco i
> pacchetti identici tra le venv dei diversi moduli (es. `torch` tra `core` e `pipeline`) invece di
> duplicarli.

## Test

```bash
pytest
```

Vedi [`../specs/006-pipeline-transcription-captioning/quickstart.md`](../specs/006-pipeline-transcription-captioning/quickstart.md)
per gli scenari di validazione end-to-end.
