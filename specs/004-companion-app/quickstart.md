# Quickstart: App di Consultazione (Companion) — US2, poi US1 + utente mock

## Prerequisiti

- `graph` in esecuzione e raggiungibile (US2, vedi `graph/README.md` / `DEPLOY.md`)
- `core` in esecuzione e raggiungibile, con `GET /api/events/search` disponibile (US1,
  `005-core-search-history`)

## Setup

```bash
cd companion
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt   # fastapi, uvicorn, jinja2, httpx, pytest

export GRAPH_API_URL="http://localhost:8001"
export GRAPH_API_TOKEN="<stesso token configurato su graph, vedi DEPLOY.md>"
export CORE_API_URL="http://localhost:8000"
export CORE_API_TOKEN="<stesso token configurato su core, vedi DEPLOY.md>"
export COMPANION_USERNAME="<scegli un nome utente>"
export COMPANION_PASSWORD="<scegli una password, segreto vero — vedi DEPLOY.md>"
```

## Esecuzione

```bash
uvicorn src.main:app --host 0.0.0.0 --port 8002
```

Apri `http://localhost:8002/explore` o `http://localhost:8002/search` — il browser chiederà le
credenziali configurate sopra.

## Scenari di validazione (da spec.md)

### US2 (esplorazione, invariati)

1. **Collegamenti diretti (SC-003)**: inserire il `node_id` di un nodo con relazioni note →
   la pagina mostra i nodi collegati con tipo di relazione e peso.
2. **Nessun collegamento (edge case, FR-007)**: inserire il `node_id` di un nodo isolato → la
   pagina mostra "nessun collegamento trovato", non un errore.
3. **Nodo inesistente (edge case)**: inserire un `node_id` mai creato → la pagina mostra un
   messaggio chiaro ("nodo non trovato"), non un errore generico/stack trace.
4. **Esplorazione incrementale**: dai risultati, cliccare su un nodo collegato → la pagina si
   ricarica mostrando i collegamenti di quel nodo.

### US1 (ricerca, nuovi)

5. **Ricerca pertinente (SC-001, SC-002)**: cercare parole legate a un contenuto salvato in
   precedenza (anche diverse da quelle originali) → il contenuto compare tra i risultati con
   anteprima, tipo, data e punteggio, entro 2s.
6. **Nessun risultato (edge case, FR-005)**: cercare qualcosa senza contenuti pertinenti
   salvati → la pagina mostra "nessun risultato trovato", non un errore.

### Utente mock (trasversale)

7. **Accesso senza credenziali**: aprire `/explore` o `/search` senza autenticarsi → il server
   richiede le credenziali (`401` con header `WWW-Authenticate`), nessuna pagina mostrata.
8. **Credenziali sbagliate**: autenticarsi con utente/password diversi da quelli configurati →
   accesso negato.

## Test automatici

```bash
pytest tests/unit         # graph_client, core_client, auth (tutto mockato)
pytest tests/contract     # route HTML via TestClient, incluso il gate di autenticazione
```
