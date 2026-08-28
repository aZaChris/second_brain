# core

Riceve un evento normalizzato, genera embedding, cerca similarità con eventi/progetti salvati e
decide se proporre un approfondimento. Espone gli endpoint definiti in
[`../API_CONTRACT.md`](../API_CONTRACT.md).

Design e task: [`../specs/002-core-similarity-engine/`](../specs/002-core-similarity-engine/),
embedding locale: [`../specs/009-embedding-locale-core/`](../specs/009-embedding-locale-core/).

## Setup

```bash
cd core
python -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt

export DB_PATH="./core.db"
export CORE_API_TOKEN="<token condiviso, vedi API_CONTRACT.md>"
export EMBEDDING_MODEL_CACHE="./models"  # EMBEDDING_MODE=local è il default, scarica qui i pesi

uvicorn src.main:app --host 0.0.0.0 --port 8000
```

Per usare un servizio esterno di embedding invece del modello locale: `EMBEDDING_MODE=external` +
`EMBEDDING_API_URL`/`EMBEDDING_API_TOKEN` al posto di `EMBEDDING_MODEL_CACHE` (vedi
`specs/009-embedding-locale-core/`).

> In alternativa a `venv`+`pip`: `uv venv` + `uv pip install -r requirements-dev.txt`
> ([astral.sh/uv](https://astral.sh/uv)) — stessi file di requirements, ma condivide su disco i
> pacchetti identici tra le venv dei diversi moduli (es. `torch` tra `core` e `pipeline`) invece di
> duplicarli.

## Test

```bash
pytest
```

Vedi [`../specs/002-core-similarity-engine/quickstart.md`](../specs/002-core-similarity-engine/quickstart.md)
per gli scenari di validazione end-to-end.
