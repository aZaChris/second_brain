# companion

App di consultazione del Second Brain (ricerca, esplorazione del grafo, cronologia eventi).
Espone `GET /explore` (esplorazione grafo, US2) — ricerca e cronologia (US1/US3) non ancora
implementate qui, anche se `core` le supporta già (`005-core-search-history`).

Design e task: [`../specs/004-companion-app/`](../specs/004-companion-app/).

## Setup

```bash
cd companion
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

export GRAPH_API_URL="http://localhost:8001"
export GRAPH_API_TOKEN="<stesso token configurato su graph, vedi ../DEPLOY.md>"

uvicorn src.main:app --host 0.0.0.0 --port 8002
```

Poi apri `http://localhost:8002/explore` nel browser.

## Test

```bash
pytest
```

Vedi [`../specs/004-companion-app/quickstart.md`](../specs/004-companion-app/quickstart.md) per
gli scenari di validazione end-to-end.
