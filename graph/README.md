# graph

Grafo dei progetti ed eventi collegati, costruito a partire dagli embedding/similarità
calcolati in `core`. Espone gli endpoint definiti in [`../API_CONTRACT.md`](../API_CONTRACT.md)
(sezione 3).

Design e task: [`../specs/003-knowledge-graph/`](../specs/003-knowledge-graph/).

## Setup

```bash
cd graph
python -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt

export DB_PATH="./graph.db"
export GRAPH_API_TOKEN="<token condiviso, vedi API_CONTRACT.md>"

uvicorn src.main:app --host 0.0.0.0 --port 8001
```

> In alternativa a `venv`+`pip`: `uv venv` + `uv pip install -r requirements-dev.txt`
> ([astral.sh/uv](https://astral.sh/uv)) — stessi file di requirements, ma condivide su disco i
> pacchetti identici tra le venv dei diversi moduli (es. `torch` tra `core` e `pipeline`) invece di
> duplicarli.

## Test

```bash
pytest
```

Vedi [`../specs/003-knowledge-graph/quickstart.md`](../specs/003-knowledge-graph/quickstart.md)
per gli scenari di validazione end-to-end.
