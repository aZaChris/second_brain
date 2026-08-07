---

description: "Task list for App di Consultazione (Companion) — solo US2"
---

# Tasks: App di Consultazione (Companion) — solo US2

**Input**: Design documents from `/specs/004-companion-app/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/graph-exploration.md, quickstart.md

**Tests**: Incluse — stesso approccio già usato per gli altri moduli.

**Scope**: solo User Story 2 (esplorazione grafo), come da plan.md. US1/US3 non hanno task qui.

## Path Conventions

Nuovo modulo `companion/`: `companion/src/`, `companion/src/templates/`,
`companion/tests/unit/`, `companion/tests/contract/`.

---

## Phase 1: Setup

- [X] T001 Crea la struttura `companion/src/`, `companion/src/templates/`, `companion/tests/unit/`, `companion/tests/contract/` per plan.md
- [X] T002 Crea `companion/requirements.txt` con `fastapi`, `uvicorn`, `jinja2`, `httpx`, `pytest`
- [X] T003 [P] Implementa il caricamento configurazione da env var (`GRAPH_API_URL`, `GRAPH_API_TOKEN`) in `companion/src/config.py`

---

## Phase 2: Foundational (Blocking Prerequisites)

- [X] T004 [P] Implementa `graph_client.get_related(node_id, depth)` (chiamata a `GET /api/graph/related/{node_id}`, gestione `404`/errori di rete) in `companion/src/graph_client.py`
- [X] T005 Crea lo scheletro dell'app FastAPI con `Jinja2Templates` e dependency wiring (config/graph_client) in `companion/src/api.py` (depends on T003, T004)

**Checkpoint**: fondamenta pronte per US2

---

## Phase 3: User Story 2 - Esplorazione dei collegamenti di un contenuto (Priority: P2) 🎯 unica story di questo piano

**Goal**: `GET /explore?node_id=...` mostra i nodi collegati (tipo di relazione e peso),
gestendo in modo chiaro nodo inesistente e nessun collegamento

**Independent Test**: scenari 1-4 di `quickstart.md`

### Tests for User Story 2

- [X] T006 [P] [US2] Unit test: `graph_client.get_related` con risposta valida ritorna i dati parsati in `companion/tests/unit/test_graph_client.py`
- [X] T007 [P] [US2] Unit test: `graph_client.get_related` su nodo inesistente (`404` da graph) segnala l'assenza in modo distinguibile da un errore di rete in `companion/tests/unit/test_graph_client.py`
- [X] T008 [P] [US2] Contract test: `GET /explore?node_id=...` con collegamenti esistenti → pagina con nodi, relazione e peso in `companion/tests/contract/test_explore_contract.py`
- [X] T009 [P] [US2] Contract test: `GET /explore?node_id=...` senza collegamenti → messaggio "nessun collegamento trovato" (FR-007) in `companion/tests/contract/test_explore_contract.py`
- [X] T010 [P] [US2] Contract test: `GET /explore?node_id=<inesistente>` → messaggio "nodo non trovato", non un errore generico in `companion/tests/contract/test_explore_contract.py`
- [X] T011 [P] [US2] Contract test: `GET /explore` senza `node_id` → `200` con solo il form, nessuna chiamata a `graph` in `companion/tests/contract/test_explore_contract.py`

### Implementation for User Story 2

- [X] T012 [US2] Implementa il template `explore_form.html` (input `node_id`, `depth`) in `companion/src/templates/explore_form.html`
- [X] T013 [US2] Implementa il template `related_results.html` (lista nodi collegati con link per esplorazione incrementale, research.md) in `companion/src/templates/related_results.html`
- [X] T014 [US2] Implementa `GET /explore` in `companion/src/api.py` (form, chiamata a `graph_client`, rendering risultati/errori) (depends on T004, T006-T013)

**Checkpoint**: User Story 2 funzionante e testabile in isolamento

---

## Phase 4: Polish & Cross-Cutting Concerns

- [X] T015 [P] Scrivi `companion/README.md` con istruzioni di setup/esecuzione, rimandando a `quickstart.md`
- [X] T016 Esegui tutti gli scenari di `quickstart.md` end-to-end
- [X] T017 [P] Aggiungi una riga in `CHANGELOG.md` per companion (US2) completato (regola della constitution sul changelog condiviso)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: nessuna dipendenza
- **Foundational (Phase 2)**: dipende da Setup — blocca US2
- **US2 (Phase 3)**: dipende da Foundational
- **Polish (Phase 4)**: dipende da US2

### Parallel Opportunities

- T003, T004 (Foundational) in parallelo — file diversi
- Tutti i test `[P]` di US2 in parallelo tra loro
- T012, T013 (i due template) in parallelo — file diversi

---

## Implementation Strategy

1. Setup → Foundational → US2
2. **STOP e valida**: scenari 1-4 di `quickstart.md`
3. Fine di questo piano — US1 (ricerca) e US3 (cronologia) di companion saranno pianificate a
   parte, riusando `core/src/api.py` (`GET /api/events/search`, `GET /api/events`) già pronto
   da `005-core-search-history`

## Notes

- Nessuna autenticazione utente sull'interfaccia di `companion` in questa v1 (research.md);
  solo la chiamata `companion → graph` è autenticata con `GRAPH_API_TOKEN`.
- Nessun frontend build/JS: template Jinja2 server-rendered.
- Commit dopo ogni task o gruppo logico, con aggiornamento di `CHANGELOG.md` per i commit
  rilevanti (regola constitution).
