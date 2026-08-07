---

description: "Task list for Grafo di Progetti ed Eventi Collegati"
---

# Tasks: Grafo di Progetti ed Eventi Collegati

**Input**: Design documents from `/specs/003-knowledge-graph/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/graph-endpoints.md, quickstart.md

**Tests**: Incluse — stesso approccio già usato per `ingestion` e `core`.

**Organization**: Task raggruppati per user story (spec.md).

## Path Conventions

Progetto singolo dentro il modulo esistente `graph/` del monorepo: `graph/src/`,
`graph/tests/unit/`, `graph/tests/contract/`.

---

## Phase 1: Setup

- [X] T001 Crea la struttura `graph/src/`, `graph/tests/unit/`, `graph/tests/contract/` per plan.md
- [X] T002 Crea `graph/requirements.txt` con `fastapi`, `uvicorn`, `pytest`
- [X] T003 [P] Implementa il caricamento configurazione da env var (`DB_PATH`, `GRAPH_API_TOKEN`) in `graph/src/config.py`

---

## Phase 2: Foundational (Blocking Prerequisites)

**⚠️ CRITICAL**: nessuna user story può iniziare prima che questa fase sia completa

- [X] T004 [P] Implementa lo schema SQLite (tabelle `nodes`, `edges` per data-model.md) e le funzioni di accesso base (`init_db`, `get_conn`) in `graph/src/storage.py`
- [X] T005 [P] Implementa la verifica del token `Authorization: Bearer` condiviso in `graph/src/auth.py`
- [X] T006 Crea lo scheletro dell'app FastAPI con dependency wiring (config/storage/auth) in `graph/src/api.py` (depends on T003, T004, T005)

**Checkpoint**: fondamenta pronte, le user story possono iniziare

---

## Phase 3: User Story 1 - Ogni contenuto salvato diventa un nodo esplorabile (Priority: P1) 🎯 MVP

**Goal**: `graph` accetta la creazione di un nodo con tipo, etichetta e riferimento all'evento
originale, senza duplicarlo se richiesto più volte per lo stesso evento

**Independent Test**: scenari 1 e 2 di `quickstart.md`

### Tests for User Story 1

- [X] T007 [P] [US1] Contract test: `POST /api/graph/nodes` → `201`, `node_id` in `graph/tests/contract/test_nodes_contract.py`
- [X] T008 [P] [US1] Contract test: stesso `source_event_id` inviato due volte → stesso `node_id`, nessun duplicato (FR-002) in `graph/tests/contract/test_nodes_contract.py`
- [X] T009 [P] [US1] Unit test: `insert_node` è idempotente su `source_event_id` in `graph/tests/unit/test_storage.py`

### Implementation for User Story 1

- [X] T010 [US1] Implementa `insert_node`/`get_node_by_source_event` in `graph/src/storage.py` (depends on T009)
- [X] T011 [US1] Implementa `POST /api/graph/nodes` (validazione, idempotenza) in `graph/src/api.py` (depends on T007, T008, T010)

**Checkpoint**: User Story 1 funzionante e testabile in isolamento

---

## Phase 4: User Story 2 - Le relazioni tra contenuti vengono registrate (Priority: P2)

**Goal**: `graph` accetta relazioni pesate tra nodi esistenti, rifiutando quelle verso nodi
inesistenti o self-loop

**Independent Test**: scenari 3 e 4 di `quickstart.md`

### Tests for User Story 2

- [X] T012 [P] [US2] Contract test: `POST /api/graph/edges` tra due nodi esistenti → `201`, `edge_id` in `graph/tests/contract/test_edges_contract.py`
- [X] T013 [P] [US2] Contract test: `POST /api/graph/edges` verso un nodo inesistente → `400`, nessuna relazione creata (FR-004) in `graph/tests/contract/test_edges_contract.py`
- [X] T014 [P] [US2] Unit test: relazione che collega un nodo a sé stesso viene rifiutata (FR-005) in `graph/tests/unit/test_storage.py`

### Implementation for User Story 2

- [X] T015 [US2] Implementa `insert_edge` con validazione esistenza nodi e rifiuto self-loop in `graph/src/storage.py` (depends on T013, T014)
- [X] T016 [US2] Implementa `POST /api/graph/edges` in `graph/src/api.py` (depends on T012, T015)

**Checkpoint**: User Story 1 e 2 entrambe funzionanti in isolamento

---

## Phase 5: User Story 3 - Esplorazione dei collegamenti a partire da un nodo (Priority: P3)

**Goal**: interrogare i nodi collegati a un nodo dato fino a una profondità data, con relazione
e peso per ciascuno

**Independent Test**: scenari 5 e 6 di `quickstart.md`

### Tests for User Story 3

- [X] T017 [P] [US3] Unit test: BFS con profondità 1 restituisce solo i vicini diretti in `graph/tests/unit/test_traversal.py`
- [X] T018 [P] [US3] Unit test: nodo senza relazioni → lista vuota (FR-007) in `graph/tests/unit/test_traversal.py`
- [X] T019 [P] [US3] Unit test: profondità richiesta maggiore dell'estensione reale del grafo non si blocca né genera errori (FR-009) in `graph/tests/unit/test_traversal.py`
- [X] T020 [P] [US3] Contract test: `GET /api/graph/related/{node_id}?depth=1` → nodi collegati con `relation`/`weight` in `graph/tests/contract/test_related_contract.py`

### Implementation for User Story 3

- [X] T021 [US3] Implementa `bfs_related(node_id, adjacency, depth) -> list[Related]` in `graph/src/traversal.py` (depends on T017-T019)
- [X] T022 [US3] Implementa `GET /api/graph/related/{node_id}` (costruzione adiacenza da `edges`, default `depth=1`) in `graph/src/api.py` (depends on T020, T021)

**Checkpoint**: tutte e tre le user story funzionanti in isolamento

---

## Phase 6: Polish & Cross-Cutting Concerns

- [X] T023 [P] Aggiorna `graph/README.md` con istruzioni di setup/esecuzione, rimandando a `quickstart.md`
- [X] T024 Esegui tutti gli scenari di `quickstart.md` end-to-end
- [X] T025 [P] Aggiungi una riga in `CHANGELOG.md` per il modulo graph completato (regola della constitution sul changelog condiviso)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: nessuna dipendenza
- **Foundational (Phase 2)**: dipende da Setup — blocca tutte le user story
- **US1 (Phase 3)**: dipende da Foundational — nessuna dipendenza da US2/US3
- **US2 (Phase 4)**: dipende da Foundational e da nodi esistenti (US1, servono nodi da collegare
  per un test end-to-end reale, anche se `insert_edge`/`storage` sono testabili in isolamento
  con nodi creati ad hoc nel test)
- **US3 (Phase 5)**: dipende da Foundational e da relazioni esistenti (US2) per un'esplorazione
  end-to-end reale, anche se `bfs_related` è testabile in isolamento su un'adiacenza costruita
  a mano nel test
- **Polish (Phase 6)**: dipende dalle user story che si vogliono rilasciare

### Parallel Opportunities

- T003-T005 (Setup/Foundational) in parallelo — file diversi
- Tutti i test `[P]` di una stessa user story in parallelo tra loro
- `storage.py` e `api.py` sono toccati da più user story: implementate US1→US2→US3 in sequenza
  se lavorate in parallelo su questi file, o coordinatevi

---

## Implementation Strategy

### MVP First

1. Setup → Foundational → US1
2. **STOP e valida**: scenari 1 e 2 di `quickstart.md`
3. US1 da sola è già un grafo che registra nodi in modo idempotente — deployabile come base,
   anche senza relazioni/esplorazione

### Incremental Delivery

1. Setup + Foundational → base pronta
2. US1 (nodi) → valida → MVP
3. US2 (relazioni) → valida
4. US3 (esplorazione) → valida
5. Polish

## Notes

- Nessuna libreria di grafi dedicata (`networkx`): BFS in poche righe su un dizionario di
  adiacenza costruito da SQLite (research.md).
- Le relazioni sono trattate come non orientate in fase di esplorazione (assumption in
  spec.md): l'adiacenza in `traversal.py` va costruita in entrambe le direzioni per ogni arco.
- Commit dopo ogni task o gruppo logico, con aggiornamento di `CHANGELOG.md` per i commit
  rilevanti (regola constitution).
