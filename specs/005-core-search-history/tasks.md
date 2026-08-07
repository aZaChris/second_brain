---

description: "Task list for Ricerca e Cronologia Eventi (Core)"
---

# Tasks: Ricerca e Cronologia Eventi (Core)

**Input**: Design documents from `/specs/005-core-search-history/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/search-and-history.md, quickstart.md

**Tests**: Incluse — stesso approccio già usato per le altre feature di `core`.

**Organization**: Task raggruppati per user story (spec.md). Nessuna fase di Setup: questa
feature estende `core` già esistente, nessuna nuova dipendenza da installare.

## Path Conventions

Estensione del modulo `core/` esistente: `core/src/api.py`, `core/src/storage.py`,
`core/tests/unit/`, `core/tests/contract/`.

---

## Phase 1: Foundational (Blocking Prerequisites)

**⚠️ CRITICAL**: condiviso da entrambe le user story

- [X] T001 [P] Implementa `build_preview(event, max_length=140)` in `core/src/api.py` (usato sia da ricerca sia da cronologia, research.md)

**Checkpoint**: le user story possono iniziare

---

## Phase 2: User Story 1 - Ricerca tra i contenuti salvati (Priority: P1) 🎯 MVP

**Goal**: `GET /api/events/search` restituisce gli eventi più pertinenti al significato della
query, escludendo quelli senza rappresentazione semantica

**Independent Test**: scenari 1, 2, 3 di `quickstart.md`

### Tests for User Story 1

- [X] T002 [P] [US1] Contract test: `GET /api/events/search` con query pertinente → risultati con `preview`/`type`/`timestamp`/`score` in `core/tests/contract/test_search_contract.py`
- [X] T003 [P] [US1] Contract test: `GET /api/events/search` senza eventi pertinenti → `results: []` (FR-004) in `core/tests/contract/test_search_contract.py`
- [X] T004 [P] [US1] Contract test: un evento senza embedding (mai avuto testo) non compare mai tra i risultati (FR-003) in `core/tests/contract/test_search_contract.py`
- [X] T005 [P] [US1] Unit test: `get_embedded_events_all` ritorna solo eventi con `status: embedded` in `core/tests/unit/test_storage.py`

### Implementation for User Story 1

- [X] T006 [US1] Implementa `get_embedded_events_all` in `core/src/storage.py` (depends on T005)
- [X] T007 [US1] Implementa `GET /api/events/search` (embed della query, cosine similarity, ordinamento, `limit`, `preview`) in `core/src/api.py` (depends on T001, T002-T004, T006)

**Checkpoint**: User Story 1 funzionante e testabile in isolamento

---

## Phase 3: User Story 2 - Cronologia degli eventi salvati (Priority: P2)

**Goal**: `GET /api/events` restituisce gli eventi salvati in ordine cronologico, sfogliabili a
pagine senza duplicati/omissioni

**Independent Test**: scenari 4, 5, 6 di `quickstart.md`

### Tests for User Story 2

- [X] T008 [P] [US2] Contract test: `GET /api/events` restituisce gli eventi dal più recente al meno recente in `core/tests/contract/test_history_contract.py`
- [X] T009 [P] [US2] Contract test: paginazione con `next_before` — nessun evento duplicato né mancante tra due pagine consecutive in `core/tests/contract/test_history_contract.py`
- [X] T010 [P] [US2] Contract test: nessun evento salvato → `events: []`, `next_before: null` (FR-007) in `core/tests/contract/test_history_contract.py`
- [X] T011 [P] [US2] Unit test: `get_events_page` rispetta `before`/`limit` e ordina per `timestamp` decrescente in `core/tests/unit/test_storage.py`

### Implementation for User Story 2

- [X] T012 [US2] Implementa `get_events_page` in `core/src/storage.py` (depends on T011)
- [X] T013 [US2] Implementa `GET /api/events` (`before`, `limit`, calcolo `next_before`) in `core/src/api.py` (depends on T001, T008-T010, T012)

**Checkpoint**: entrambe le user story funzionanti in isolamento

---

## Phase 4: Polish & Cross-Cutting Concerns

- [X] T014 [P] Aggiorna `core/README.md` se necessario (nuovi endpoint già coperti da `API_CONTRACT.md`, linkato)
- [X] T015 Esegui tutti gli scenari di `quickstart.md` end-to-end
- [X] T016 [P] Aggiungi una riga in `CHANGELOG.md` per ricerca/cronologia completate (regola della constitution sul changelog condiviso)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Foundational (Phase 1)**: nessuna dipendenza — blocca entrambe le user story
- **US1 (Phase 2)**: dipende da Foundational — nessuna dipendenza da US2
- **US2 (Phase 3)**: dipende da Foundational — nessuna dipendenza da US1 (query e storage
  separati da quelli di US1, anche se entrambe toccano `api.py`)
- **Polish (Phase 4)**: dipende dalle user story che si vogliono rilasciare

### Parallel Opportunities

- US1 e US2 sono indipendenti tra loro (query diverse, nessuna dipendenza di dati) e possono
  procedere in parallelo dopo la Fase 1 — coordinatevi solo su `api.py`, toccato da entrambe
- Tutti i test `[P]` di una stessa user story in parallelo tra loro

---

## Implementation Strategy

### MVP First

1. Foundational → US1
2. **STOP e valida**: scenari 1-3 di `quickstart.md`
3. US1 da sola sblocca già la ricerca di `companion`

### Incremental Delivery

1. Foundational → base pronta
2. US1 (ricerca) → valida → MVP per companion US1
3. US2 (cronologia) → valida → sblocca companion US3
4. Polish

## Notes

- Nessuna nuova dipendenza: si riusano `embedding.py` e `similarity.py` già presenti in `core`.
- Nessuna modifica al comportamento di scrittura esistente (`POST`/`PATCH /api/events`,
  preferenze) — solo endpoint aggiuntivi di lettura.
- Commit dopo ogni task o gruppo logico, con aggiornamento di `CHANGELOG.md` per i commit
  rilevanti (regola constitution).
