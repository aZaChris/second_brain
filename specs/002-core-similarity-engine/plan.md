# Implementation Plan: Motore di Similarità e Approfondimento (Core)

**Branch**: `002-core-similarity-engine` | **Date**: 2026-08-07 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/002-core-similarity-engine/spec.md`

## Summary

Servizio `core` che espone `POST /api/events` e `PATCH /api/events/{event_id}` (per
`ingestion`/`pipeline`) e `GET/PUT /api/users/{user_id}/preferences`, secondo
`API_CONTRACT.md`. Genera un embedding del testo tramite un servizio esterno, lo confronta con
gli eventi già salvati (cosine similarity in-process) e decide se segnalare un collegamento in
base alle preferenze utente. Storage locale in SQLite, nessun vector database dedicato: il
volume (uso personale) non lo giustifica.

## Technical Context

**Language/Version**: Python 3.11+

**Primary Dependencies**: FastAPI (endpoint del contratto), `httpx` (chiamata al servizio
esterno di embedding), `numpy` (cosine similarity in-process) — nessun vector database dedicato,
nessun ORM: il volume (uso personale, ordine di migliaia di eventi) non lo giustifica.

**Storage**: SQLite (file locale, `sqlite3` di stdlib) — eventi, embedding (salvati come blob
JSON), preferenze utente.

**Testing**: `pytest` con `TestClient` di FastAPI per i contract test; client di embedding
mockato per i test unitari (principio "API testabili indipendentemente").

**Target Platform**: Linux — non necessariamente il Raspberry Pi: `core` può girare su una
macchina diversa da quella di `ingestion`, il vincolo di leggerezza del Raspberry Pi si applica
solo al nodo di ingestion.

**Project Type**: Servizio web singolo (API REST).

**Performance Goals**: Conferma di ricezione entro 2s dall'arrivo di un evento (SC-001,
per non far scattare i retry lato `ingestion`).

**Constraints**: Nessuno storage di dati non necessario (privacy-first); l'embedding usa un
servizio esterno invece di un modello pesante locale (principio IV della constitution).

**Scale/Scope**: 1 utente, ordine di centinaia/migliaia di eventi salvati nel tempo — cosine
similarity calcolata in-process con `numpy` su questo volume resta rapida senza infrastruttura
dedicata.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **I. Privacy-First** — PASS. Si salva solo ciò che serve (testo dell'evento, embedding,
  preferenze); il servizio esterno di embedding riceve solo il testo necessario a generare il
  vettore, nessun altro dato personale.
- **II. Modularità** — PASS. `core` vive in `core/`, comunica con `ingestion`/`pipeline`/
  `companion` solo tramite gli endpoint di `API_CONTRACT.md`.
- **III. API testabili indipendentemente** — PASS. `TestClient` di FastAPI + client di
  embedding mockabile permettono di testare `core` senza servizi esterni reali in esecuzione.
- **IV. Servizi esterni preferiti a modelli locali pesanti** — PASS. L'embedding è generato via
  API esterna, non un modello locale.
- **Vincoli Tecnici** — PASS (parzialmente N/A: il vincolo hardware del Raspberry Pi riguarda
  `ingestion`, non `core`). SQLite invece di un DB server riduce comunque l'impronta
  infrastrutturale.

Nessuna violazione: tabella "Complexity Tracking" non necessaria.

## Project Structure

### Documentation (this feature)

```text
specs/002-core-similarity-engine/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
└── tasks.md
```

### Source Code (repository root)

```text
core/
├── src/
│   ├── api.py           # app FastAPI: route POST/PATCH /api/events, GET/PUT /api/users/{id}/preferences
│   ├── storage.py        # accesso SQLite: eventi, embedding, preferenze
│   ├── embedding.py       # client verso il servizio esterno di embedding
│   ├── similarity.py      # cosine similarity + selezione dei collegamenti pertinenti
│   ├── insight.py         # decisione se/come segnalare un collegamento in base alle preferenze
│   └── config.py          # variabili d'ambiente (DB path, URL/token servizio embedding, token API interno)
└── tests/
    ├── unit/               # similarity, insight decision, storage
    └── contract/           # payload/risposte conformi ad API_CONTRACT.md
```

**Structure Decision**: Progetto singolo dentro il modulo `core/` già esistente nel monorepo,
in linea con la modularità della constitution — stessa struttura del modulo `ingestion/` già
implementato.

## Complexity Tracking

> Nessuna violazione del Constitution Check: tabella vuota per questa feature.
