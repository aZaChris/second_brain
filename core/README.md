# core

Riceve un evento normalizzato, genera embedding, cerca similarità con eventi/progetti salvati e
decide se proporre un approfondimento. Espone gli endpoint definiti in
[`../API_CONTRACT.md`](../API_CONTRACT.md).

Design e task: [`../specs/002-core-similarity-engine/`](../specs/002-core-similarity-engine/).

## Setup

```bash
cd core
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

export DB_PATH="./core.db"
export EMBEDDING_API_URL="<endpoint del servizio esterno di embedding>"
export EMBEDDING_API_TOKEN="<token del servizio esterno>"
export CORE_API_TOKEN="<token condiviso, vedi API_CONTRACT.md>"

uvicorn src.main:app --host 0.0.0.0 --port 8000
```

## Test

```bash
pytest
```

Vedi [`../specs/002-core-similarity-engine/quickstart.md`](../specs/002-core-similarity-engine/quickstart.md)
per gli scenari di validazione end-to-end.
