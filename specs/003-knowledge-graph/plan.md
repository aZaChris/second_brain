# Implementation Plan: Grafo di Progetti ed Eventi Collegati

**Branch**: `003-knowledge-graph` | **Date**: 2026-08-07 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/003-knowledge-graph/spec.md`

## Summary

Servizio `graph` che espone `POST /api/graph/nodes`, `POST /api/graph/edges` e
`GET /api/graph/related/{node_id}` secondo `API_CONTRACT.md`. Nodi e relazioni salvati in
SQLite; esplorazione dei collegamenti tramite BFS in-process fino alla profondità richiesta —
nessuna libreria di grafi dedicata (`networkx` o simili): a poche migliaia di nodi un BFS su un
dizionario di adiacenza costruito da due query SQL resta rapido e non giustifica una nuova
dipendenza.

## Technical Context

**Language/Version**: Python 3.11+ (stesso stack di `ingestion`/`core`, per coerenza nel
monorepo).

**Primary Dependencies**: FastAPI (endpoint del contratto) — nessun'altra dipendenza: la
traversata a bassa profondità (FR-006, tipicamente 1-3) è un BFS su un dizionario di adiacenza
costruito in memoria da SQLite, poche righe di stdlib.

**Storage**: SQLite (stdlib `sqlite3`) — tabelle `nodes` ed `edges`.

**Testing**: `pytest` con `TestClient` di FastAPI per i contract test.

**Target Platform**: Linux, nessun vincolo hardware specifico (non gira sul Raspberry Pi).

**Project Type**: Servizio web singolo (API REST).

**Performance Goals**: Creazione nodo/relazione confermata entro 1s (SC-001); query di
esplorazione sotto 1s anche su alcune migliaia di nodi/relazioni (SC-004).

**Constraints**: Nessuno storage di dati non necessario (privacy-first — si salvano solo tipo,
etichetta, riferimento all'evento originale, relazioni con peso).

**Scale/Scope**: 1 utente, ordine di migliaia di nodi/relazioni nel tempo — un BFS in memoria
su questo volume resta ampiamente entro il budget di risposta.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **I. Privacy-First** — PASS. Si salva solo tipo, etichetta e riferimento all'evento
  originale per i nodi, e tipo/peso per le relazioni — nessun contenuto testuale duplicato qui
  (resta in `core`).
- **II. Modularità** — PASS. `graph` vive in `graph/`, riceve scritture solo da `core` e letture
  solo da `companion`, tramite gli endpoint di `API_CONTRACT.md`.
- **III. API testabili indipendentemente** — PASS. `TestClient` di FastAPI su SQLite in un
  file temporaneo permette di testare `graph` senza altri moduli in esecuzione.
- **IV. Servizi esterni preferiti a modelli locali pesanti** — N/A: questa feature non usa
  LLM/STT, nessuna violazione.
- **Vincoli Tecnici** — PASS. SQLite invece di un DB a grafo dedicato riduce l'impronta
  infrastrutturale; nessun requisito hardware specifico dato che non gira sul Raspberry Pi.

Nessuna violazione: tabella "Complexity Tracking" non necessaria.

## Project Structure

### Documentation (this feature)

```text
specs/003-knowledge-graph/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
└── tasks.md
```

### Source Code (repository root)

```text
graph/
├── src/
│   ├── api.py         # app FastAPI: route POST/GET del contratto
│   ├── storage.py       # accesso SQLite: nodi, relazioni
│   ├── traversal.py      # BFS su dizionario di adiacenza, fino a una profondità data
│   ├── auth.py           # verifica token Bearer condiviso
│   └── config.py         # variabili d'ambiente (DB path, token API interno)
└── tests/
    ├── unit/               # traversal, idempotenza nodi, validazione relazioni
    └── contract/           # payload/risposte conformi ad API_CONTRACT.md
```

**Structure Decision**: Progetto singolo dentro il modulo `graph/` già esistente nel monorepo —
stessa struttura di `ingestion/` e `core/`, coerente con la modularità della constitution.

## Complexity Tracking

> Nessuna violazione del Constitution Check: tabella vuota per questa feature.
