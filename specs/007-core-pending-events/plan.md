# Implementation Plan: Eventi in Attesa di Elaborazione (Core)

**Branch**: `007-core-pending-events` | **Date**: 2026-08-07 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/007-core-pending-events/spec.md`

## Summary

Estende il servizio `core` esistente con `GET /api/events/pending`, secondo la sezione 8 di
`API_CONTRACT.md`. Nessun nuovo progetto: si aggiunge una query a `core/src/storage.py` e una
route a `core/src/api.py`, come già fatto per `005-core-search-history`.

## Technical Context

**Language/Version**: Python 3.11+ (stesso codebase di `core`).

**Primary Dependencies**: nessuna nuova dipendenza — solo FastAPI, già presente.

**Storage**: stesso SQLite di `core` (tabella `events`), nessuna nuova tabella o migrazione.

**Testing**: `pytest` con `TestClient`, stesso approccio già usato in `core`.

**Target Platform**: stesso di `core`.

**Project Type**: estensione di un servizio web esistente.

**Performance Goals**: risposta entro 2s (SC-001).

**Constraints**: nessuna modifica al comportamento di scrittura esistente — solo un nuovo
endpoint di lettura.

**Scale/Scope**: stesso di `core` (1 utente, ordine di migliaia di eventi).

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **I. Privacy-First** — PASS. Nessun nuovo dato salvato; si espone solo `media_url` (già
  presente) agli eventi che ne hanno bisogno per l'elaborazione, non contenuto testuale.
- **II. Modularità** — PASS. Estende `core` senza toccare gli altri moduli; nuovo punto di
  contatto solo tramite il contratto (sezione 8).
- **III. API testabili indipendentemente** — PASS. `TestClient` + dati seminati in SQLite,
  stesso approccio già validato in `002`/`005`.
- **IV. Servizi esterni preferiti a modelli locali pesanti** — N/A: questa feature non genera
  embedding né usa LLM/STT, si limita a leggere lo stato degli eventi.
- **Vincoli Tecnici** — N/A diretto (non riguarda il Raspberry Pi).

Nessuna violazione: tabella "Complexity Tracking" non necessaria.

## Project Structure

### Documentation (this feature)

```text
specs/007-core-pending-events/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
└── tasks.md
```

### Source Code (repository root)

Nessuna nuova cartella: si estendono i file già esistenti del modulo `core/`.

```text
core/
├── src/
│   ├── api.py         # + GET /api/events/pending
│   └── storage.py       # + get_pending_events
└── tests/
    ├── unit/               # + test_storage: get_pending_events
    └── contract/           # + test_pending_contract.py
```

**Structure Decision**: estensione del modulo `core/` esistente, stesso pattern di
`005-core-search-history`.

## Complexity Tracking

> Nessuna violazione del Constitution Check: tabella vuota per questa feature.
