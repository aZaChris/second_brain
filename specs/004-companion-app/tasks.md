---

description: "Task list for App di Consultazione (Companion) — US1 + utente mock"
---

# Tasks: App di Consultazione (Companion) — US1 + utente mock

**Input**: Design documents from `/specs/004-companion-app/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/search.md, quickstart.md

**Tests**: Incluse — stesso approccio già usato per gli altri moduli.

**Scope**: User Story 1 (ricerca) + un gate di autenticazione trasversale ("utente mock") che
si applica anche a `/explore` (US2, già implementata). US3 (cronologia) resta fuori.

## Path Conventions

Estensione del modulo `companion/` esistente: `companion/src/`, `companion/src/templates/`,
`companion/tests/unit/`, `companion/tests/contract/`.

---

## Phase 1: Foundational — utente mock (Blocking Prerequisites)

**⚠️ CRITICAL**: si applica anche a `/explore` (US2): nessuna route resta senza gate dopo
questa fase

### Tests

- [X] T001 [P] Unit test: `auth` verifica correttamente utente/password validi in `companion/tests/unit/test_auth.py`
- [X] T002 [P] Unit test: `auth` rifiuta credenziali errate o assenti in `companion/tests/unit/test_auth.py`
- [X] T003 [P] Contract test (regressione US2): `GET /explore` senza credenziali → `401` in `companion/tests/contract/test_explore_contract.py`
- [X] T004 [P] Contract test (regressione US2): `GET /explore` con credenziali corrette → comportamento invariato rispetto a prima del gate in `companion/tests/contract/test_explore_contract.py`

### Implementation

- [X] T005 [P] Aggiungi `COMPANION_USERNAME`, `COMPANION_PASSWORD`, `CORE_API_URL`, `CORE_API_TOKEN` in `companion/src/config.py`
- [X] T006 Implementa il gate `HTTPBasic` (utente mock, `secrets.compare_digest`) in `companion/src/auth.py` (depends on T001, T002, T005)
- [X] T007 Applica il gate a tutte le route esistenti in `companion/src/api.py` e aggiorna i test di US2 con le credenziali (depends on T003, T004, T006)

**Checkpoint**: utente mock attivo, `/explore` (US2) continua a funzionare con le credenziali corrette

---

## Phase 2: User Story 1 - Ricerca tra i contenuti salvati (Priority: P1) 🎯

**Goal**: `GET /search?q=...` mostra i contenuti più pertinenti dalla ricerca semantica di
`core`, gestendo in modo chiaro l'assenza di risultati

**Independent Test**: scenari 5, 6 di `quickstart.md`

### Tests for User Story 1

- [X] T008 [P] [US1] Unit test: `core_client.search_events` chiama `GET /api/events/search` e ritorna i risultati parsati in `companion/tests/unit/test_core_client.py`
- [X] T009 [P] [US1] Unit test: `core_client.search_events` gestisce un errore di rete verso `core` in modo distinguibile in `companion/tests/unit/test_core_client.py`
- [X] T010 [P] [US1] Contract test: `GET /search?q=...` con risultati pertinenti → pagina con `preview`/`type`/`timestamp`/`score` in `companion/tests/contract/test_search_contract.py`
- [X] T011 [P] [US1] Contract test: `GET /search?q=...` senza risultati pertinenti → "nessun risultato trovato" (FR-005) in `companion/tests/contract/test_search_contract.py`
- [X] T012 [P] [US1] Contract test: `GET /search` senza `q` → `200` con solo il form, nessuna chiamata a `core` in `companion/tests/contract/test_search_contract.py`

### Implementation for User Story 1

- [X] T013 [US1] Implementa `core_client.search_events(q, limit)` in `companion/src/core_client.py` (depends on T008, T009)
- [X] T014 [US1] Implementa il template `search_results.html` in `companion/src/templates/search_results.html`
- [X] T015 [US1] Implementa `GET /search` in `companion/src/api.py` (depends on T010-T014)

**Checkpoint**: User Story 1 funzionante e testabile in isolamento (con utente mock attivo)

---

## Phase 3: Polish & Cross-Cutting Concerns

- [X] T016 [P] Aggiorna `companion/README.md` con le nuove variabili d'ambiente e `GET /search`, rimandando a `quickstart.md`
- [X] T017 Esegui tutti gli scenari di `quickstart.md` end-to-end
- [X] T018 [P] Aggiungi una riga in `CHANGELOG.md` per companion US1 + utente mock completati (regola della constitution sul changelog condiviso)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Foundational (Phase 1)**: nessuna dipendenza — blocca US1 e retrofit su tutte le route
  esistenti
- **US1 (Phase 2)**: dipende da Foundational (serve il gate già attivo per testare `/search`
  con le credenziali)
- **Polish (Phase 3)**: dipende da US1

### Parallel Opportunities

- Tutti i test `[P]` di una stessa fase in parallelo tra loro
- T005 (config) può procedere in parallelo a T001/T002 (test di `auth`, file diverso)

---

## Implementation Strategy

1. Foundational (utente mock, incluso retrofit su `/explore`) → valida che US2 continui a
   funzionare con le credenziali
2. US1 (ricerca) → valida → scenari 5, 6 di `quickstart.md`
3. Polish

## Notes

- Nessuna nuova dipendenza: `HTTPBasic` è già incluso in FastAPI (research.md).
- `api.py` è toccato sia dal retrofit di autenticazione sia da `GET /search`: fateli in
  sequenza (Foundational poi US1) per evitare conflitti se in due lavorate in parallelo.
- Commit dopo ogni task o gruppo logico, con aggiornamento di `CHANGELOG.md` per i commit
  rilevanti (regola constitution).
