# Quickstart: App di Consultazione (Companion) — solo US2

## Prerequisiti

- `graph` in esecuzione e raggiungibile (vedi `graph/README.md` / `DEPLOY.md`)

## Setup

```bash
cd companion
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt   # fastapi, uvicorn, jinja2, httpx, pytest

export GRAPH_API_URL="http://localhost:8001"
export GRAPH_API_TOKEN="<stesso token configurato su graph, vedi DEPLOY.md>"
```

## Esecuzione

```bash
uvicorn src.main:app --host 0.0.0.0 --port 8002
```

Apri `http://localhost:8002/explore` nel browser.

## Scenari di validazione (da spec.md, US2)

1. **Collegamenti diretti (SC-003)**: inserire il `node_id` di un nodo con relazioni note →
   la pagina mostra i nodi collegati con tipo di relazione e peso.
2. **Nessun collegamento (edge case, FR-007)**: inserire il `node_id` di un nodo isolato → la
   pagina mostra "nessun collegamento trovato", non un errore.
3. **Nodo inesistente (edge case)**: inserire un `node_id` mai creato → la pagina mostra un
   messaggio chiaro ("nodo non trovato"), non un errore generico/stack trace.
4. **Esplorazione incrementale**: dai risultati, cliccare su un nodo collegato → la pagina si
   ricarica mostrando i collegamenti di quel nodo.

## Test automatici

```bash
pytest tests/unit         # graph_client (graph mockato)
pytest tests/contract     # route HTML via TestClient
```
