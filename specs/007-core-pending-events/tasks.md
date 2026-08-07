---

description: "Task list for Eventi in Attesa di Elaborazione (Core)"
---

# Tasks: Eventi in Attesa di Elaborazione (Core)

**Input**: Design documents from `/specs/007-core-pending-events/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/pending-events.md, quickstart.md

**Tests**: Incluse — stesso approccio già usato per le altre feature di `core`.

**Organization**: Task raggruppati per user story (spec.md). Nessuna fase di Setup: estensione
di `core` già esistente, nessuna nuova dipendenza.

## Path Conventions

Estensione del modulo `core/` esistente: `core/src/api.py`, `core/src/storage.py`,
`core/tests/unit/`, `core/tests/contract/`.

---

## Phase 1: Foundational (Blocking Prerequisites)

- [X] T001 [P] Implementa `get_pending_events(conn, types, limit)` in `core/src/storage.py` (filtro su `normalized_text IS NULL`, non su `status` — research.md)

**Checkpoint**: le user story possono iniziare

---

## Phase 2: User Story 1 - Scoperta degli eventi da elaborare (Priority: P1) 🎯 MVP

**Goal**: `GET /api/events/pending` elenca gli eventi audio/immagine non ancora trascritti/
descritti, escludendo quelli già elaborati indipendentemente dallo stato di embedding

**Independent Test**: scenari 1, 2, 3 di `quickstart.md`

### Tests for User Story 1

- [X] T002 [P] [US1] Contract test: `GET /api/events/pending` con eventi audio/immagine in attesa → `events` con `type`/`media_url`/`timestamp` in `core/tests/contract/test_pending_contract.py`
- [X] T003 [P] [US1] Contract test: un evento con `normalized_text` già valorizzato (anche se `status` è ancora `received` per un embedding fallito) non compare (FR-004) in `core/tests/contract/test_pending_contract.py`
- [X] T004 [P] [US1] Contract test: nessun evento in attesa → `events: []` (FR-005) in `core/tests/contract/test_pending_contract.py`
- [X] T005 [P] [US1] Unit test: `get_pending_events` esclude eventi con `normalized_text` valorizzato, indipendentemente da `status` in `core/tests/unit/test_storage.py`
- [X] T006 [P] [US1] Unit test: `get_pending_events` ordina per `timestamp` crescente (FIFO, research.md) in `core/tests/unit/test_storage.py`

### Implementation for User Story 1

- [X] T007 [US1] Implementa `GET /api/events/pending` (senza filtro `type`, `limit` di default) in `core/src/api.py` (depends on T001, T002-T006)

**Checkpoint**: User Story 1 funzionante e testabile in isolamento

---

## Phase 3: User Story 2 - Filtro per tipo di contenuto (Priority: P2)

**Goal**: `GET /api/events/pending?type=audio` (o `image`) restituisce solo eventi del tipo
richiesto

**Independent Test**: scenario 4 di `quickstart.md`

### Tests for User Story 2

- [X] T008 [P] [US2] Contract test: `GET /api/events/pending?type=audio` restituisce solo eventi `audio` anche in presenza di eventi `image` in attesa in `core/tests/contract/test_pending_contract.py`
- [X] T009 [P] [US2] Unit test: `get_pending_events` rispetta il filtro `types` passato in `core/tests/unit/test_storage.py`

### Implementation for User Story 2

- [X] T010 [US2] Aggiungi il parsing del parametro `type` (CSV, default `audio,image`) a `GET /api/events/pending` in `core/src/api.py` (depends on T008, T009)

**Checkpoint**: entrambe le user story funzionanti in isolamento

---

## Phase 4: Polish & Cross-Cutting Concerns

- [X] T011 [P] Aggiorna `core/README.md` se necessario (nuovo endpoint già coperto da `API_CONTRACT.md`, linkato)
- [X] T012 Esegui tutti gli scenari di `quickstart.md` end-to-end
- [X] T013 [P] Aggiungi una riga in `CHANGELOG.md` per la scoperta eventi in attesa completata (regola della constitution sul changelog condiviso)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Foundational (Phase 1)**: nessuna dipendenza — blocca entrambe le user story
- **US1 (Phase 2)**: dipende da Foundational — nessuna dipendenza da US2
- **US2 (Phase 3)**: dipende da Foundational e T001 (stessa query di US1, solo parametro
  aggiuntivo) — logicamente estende US1, non del tutto indipendente
- **Polish (Phase 4)**: dipende dalle user story che si vogliono rilasciare

### Parallel Opportunities

- Tutti i test `[P]` di una stessa user story in parallelo tra loro
- T007 e T010 toccano lo stesso endpoint in `api.py`: implementare US1 prima di US2 evita
  conflitti, anche se sono piccole modifiche incrementali allo stesso handler

---

## Implementation Strategy

1. Foundational → US1
2. **STOP e valida**: scenari 1-3 di `quickstart.md`
3. US1 da sola sblocca già la scoperta base degli eventi per `pipeline`
4. US2 (filtro per tipo) → valida → comodità operativa aggiuntiva

## Notes

- Nessuna nuova dipendenza, nessuna nuova tabella.
- Nessuna modifica al comportamento di scrittura esistente (`POST`/`PATCH /api/events`,
  preferenze, ricerca, cronologia).
- Commit dopo ogni task o gruppo logico, con aggiornamento di `CHANGELOG.md` per i commit
  rilevanti (regola constitution).
