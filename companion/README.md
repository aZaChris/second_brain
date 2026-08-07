# companion

App di consultazione del Second Brain (ricerca, esplorazione del grafo, cronologia eventi).
Espone `GET /explore` (esplorazione grafo, US2) e `GET /search` (ricerca semantica, US1).
Cronologia (US3) non ancora implementata, anche se `core` la supporta già
(`005-core-search-history`). Tutte le route richiedono autenticazione HTTP Basic (utente mock,
una sola coppia utente/password — non un sistema di account).

Design e task: [`../specs/004-companion-app/`](../specs/004-companion-app/).

## Setup

```bash
cd companion
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

export GRAPH_API_URL="http://localhost:8001"
export GRAPH_API_TOKEN="<stesso token configurato su graph, vedi ../DEPLOY.md>"
export CORE_API_URL="http://localhost:8000"
export CORE_API_TOKEN="<stesso token configurato su core, vedi ../DEPLOY.md>"
export COMPANION_USERNAME="<scegli un nome utente>"
export COMPANION_PASSWORD="<scegli una password, segreto vero>"

uvicorn src.main:app --host 0.0.0.0 --port 8002
```

Poi apri `http://localhost:8002/explore` o `http://localhost:8002/search` nel browser — verrà
richiesta l'autenticazione con le credenziali configurate sopra.

## Test

```bash
pytest
```

Vedi [`../specs/004-companion-app/quickstart.md`](../specs/004-companion-app/quickstart.md) per
gli scenari di validazione end-to-end.
