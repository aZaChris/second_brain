# Quickstart: Grafo di Progetti ed Eventi Collegati

## Prerequisiti

- Python 3.11+

## Setup

```bash
cd graph
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt   # fastapi, uvicorn, pytest

export DB_PATH="./graph.db"
export GRAPH_API_TOKEN="<token condiviso, vedi API_CONTRACT.md>"
```

## Esecuzione

```bash
uvicorn src.main:app --host 0.0.0.0 --port 8001
```

## Scenari di validazione (da spec.md)

1. **Creazione nodo (US1 / SC-001)**: `POST /api/graph/nodes` con `node_type`, `label`,
   `source_event_id` → `201` con `node_id` entro 1s.
2. **Idempotenza nodo (US1, edge case / SC-003)**: ripetere la stessa richiesta con lo stesso
   `source_event_id` → stesso `node_id`, nessun duplicato.
3. **Creazione relazione (US2)**: creare due nodi, poi `POST /api/graph/edges` tra loro → `201`
   con `edge_id`.
4. **Relazione verso nodo inesistente (US2, edge case)**: `POST /api/graph/edges` con un
   `to_node_id` mai creato → `400`, nessuna relazione creata.
5. **Esplorazione (US3 / SC-002)**: creare un piccolo grafo (3-4 nodi, 2-3 relazioni), poi
   `GET /api/graph/related/{node_id}?depth=1` → nodi collegati diretti attesi, con relazione e
   peso.
6. **Nessun collegamento (US3, edge case)**: `GET /api/graph/related/{node_id}` su un nodo
   isolato → lista vuota, non errore.

## Test automatici

```bash
pytest tests/unit         # traversal BFS, idempotenza, validazione relazioni
pytest tests/contract     # payload/risposte conformi ad API_CONTRACT.md
```
