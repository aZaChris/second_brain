# graph

Grafo dei progetti ed eventi collegati, costruito a partire dagli embedding/similarità
calcolati in `core`. Espone gli endpoint definiti in [`../API_CONTRACT.md`](../API_CONTRACT.md)
(sezione 3).

Design e task: [`../specs/003-knowledge-graph/`](../specs/003-knowledge-graph/).

## Setup

```bash
cd graph
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

export DB_PATH="./graph.db"
export GRAPH_API_TOKEN="<token condiviso, vedi API_CONTRACT.md>"

uvicorn src.main:app --host 0.0.0.0 --port 8001
```

## Test

```bash
pytest
```

Vedi [`../specs/003-knowledge-graph/quickstart.md`](../specs/003-knowledge-graph/quickstart.md)
per gli scenari di validazione end-to-end.
