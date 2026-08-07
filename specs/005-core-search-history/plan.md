# Implementation Plan: Ricerca e Cronologia Eventi (Core)

**Branch**: `005-core-search-history` | **Date**: 2026-08-07 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/005-core-search-history/spec.md`

## Summary

Estende il servizio `core` già esistente (`002-core-similarity-engine`) con due endpoint di
sola lettura — `GET /api/events/search` e `GET /api/events` — secondo le sezioni 6-7 di
`API_CONTRACT.md`. Nessun nuovo progetto: si aggiunge codice a `core/src/storage.py` e
`core/src/api.py` già esistenti, riusando l'embedding client e la cosine similarity già
implementati per `002-core-similarity-engine`.

## Technical Context

**Language/Version**: Python 3.11+ (stesso codebase di `core`).

**Primary Dependencies**: nessuna nuova dipendenza — riusa FastAPI, `numpy` (cosine similarity)
e il client di embedding già presenti in `core/src/`.

**Storage**: stesso SQLite di `core` (`events`, `user_preferences`); nessuna nuova tabella o
migrazione — i campi necessari (`content`, `normalized_text`, `type`, `timestamp`, `embedding`,
`status`) esistono già.

**Testing**: `pytest` con `TestClient` di FastAPI, stesso approccio già usato in `core`.

**Target Platform**: stesso di `core` (non il Raspberry Pi).

**Project Type**: estensione di un servizio web esistente, non un nuovo progetto.

**Performance Goals**: ricerca entro 2s (SC-001); paginazione della cronologia scorrevole su
centinaia di eventi (SC-004) — stesso ordine di grandezza già gestito da `core` per la
similarità in `002-core-similarity-engine`.

**Constraints**: nessuna modifica al comportamento di scrittura già esistente (`POST`/
`PATCH /api/events`, preferenze) — solo endpoint aggiuntivi di lettura.

**Scale/Scope**: stesso di `core` (1 utente, ordine di migliaia di eventi).

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **I. Privacy-First** — PASS. Nessun nuovo dato salvato: si leggono solo campi già persistiti
  per altri scopi; le anteprime restano interne al contratto tra moduli.
- **II. Modularità** — PASS. Si estende `core` senza toccare gli altri moduli; l'unico punto di
  contatto nuovo è il contratto (`API_CONTRACT.md` sezioni 6-7).
- **III. API testabili indipendentemente** — PASS. `TestClient` + dati seminati direttamente in
  SQLite (via le funzioni di storage già testate in `002`) permettono di testare ricerca e
  cronologia senza altri moduli in esecuzione.
- **IV. Servizi esterni preferiti a modelli locali pesanti** — PASS. La ricerca riusa lo stesso
  servizio esterno di embedding già in uso, nessun modello locale aggiunto.
- **Vincoli Tecnici** — N/A diretto (non riguarda il Raspberry Pi, come già per `core`).

Nessuna violazione: tabella "Complexity Tracking" non necessaria.

## Project Structure

### Documentation (this feature)

```text
specs/005-core-search-history/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
└── tasks.md
```

### Source Code (repository root)

Nessuna nuova cartella: si estendono i file già esistenti del modulo `core/` (creato in
`002-core-similarity-engine`).

```text
core/
├── src/
│   ├── api.py         # + GET /api/events/search, GET /api/events
│   ├── storage.py       # + get_embedded_events_all, get_events_page
│   └── similarity.py     # riusato as-is (cosine_similarity già presente)
└── tests/
    ├── unit/               # + test_storage: nuove query
    └── contract/           # + test_search_contract.py, test_history_contract.py
```

**Structure Decision**: estensione del modulo `core/` esistente, nessuna nuova struttura —
coerente con la modularità della constitution (un solo posto per la logica di `core`).

## Complexity Tracking

> Nessuna violazione del Constitution Check: tabella vuota per questa feature.
