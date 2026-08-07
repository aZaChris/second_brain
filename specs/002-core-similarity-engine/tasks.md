---

description: "Task list for Motore di Similarità e Approfondimento (Core)"
---

# Tasks: Motore di Similarità e Approfondimento (Core)

**Input**: Design documents from `/specs/002-core-similarity-engine/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/events-and-preferences.md, quickstart.md

**Tests**: Incluse — coerente con la scelta fatta per `ingestion` e col principio "API
testabili indipendentemente" della constitution.

**Organization**: Task raggruppati per user story (spec.md).

## Path Conventions

Progetto singolo dentro il modulo esistente `core/` del monorepo (per `plan.md`):
`core/src/`, `core/tests/unit/`, `core/tests/contract/`.

---

## Phase 1: Setup

- [X] T001 Crea la struttura `core/src/`, `core/tests/unit/`, `core/tests/contract/` per plan.md
- [X] T002 Crea `core/requirements.txt` con `fastapi`, `uvicorn`, `httpx`, `numpy`, `pytest`
- [X] T003 [P] Implementa il caricamento configurazione da env var (`DB_PATH`, `EMBEDDING_API_URL`, `EMBEDDING_API_TOKEN`, `CORE_API_TOKEN`) in `core/src/config.py`

---

## Phase 2: Foundational (Blocking Prerequisites)

**⚠️ CRITICAL**: nessuna user story può iniziare prima che questa fase sia completa

- [X] T004 [P] Implementa lo schema SQLite (tabelle `events`, `user_preferences` per data-model.md) e le funzioni di accesso base (`init_db`, `get_conn`) in `core/src/storage.py`
- [X] T005 [P] Implementa il client verso il servizio esterno di embedding (`embed(text) -> list[float]`) in `core/src/embedding.py`
- [X] T006 [P] Implementa cosine similarity tra vettori in `core/src/similarity.py`
- [X] T007 [P] Implementa la verifica del token `Authorization: Bearer` condiviso in `core/src/auth.py`
- [X] T008 Crea lo scheletro dell'app FastAPI con dependency wiring (config/storage/auth) in `core/src/api.py` (depends on T003, T004, T007)

**Checkpoint**: fondamenta pronte, le user story possono iniziare

---

## Phase 3: User Story 1 - Ogni nota inviata viene salvata e resa ritrovabile (Priority: P1) 🎯 MVP

**Goal**: `core` accetta un evento normalizzato, lo persiste e ne genera la rappresentazione
semantica non appena il testo è disponibile (subito per `text`, dopo il `PATCH` per
audio/immagine)

**Independent Test**: scenari 1 e 5 di `quickstart.md`

### Tests for User Story 1

- [X] T009 [P] [US1] Contract test: `POST /api/events` con `type: text` → `201`, `event_id`, `status` conformi ad `API_CONTRACT.md` in `core/tests/contract/test_events_contract.py`
- [X] T010 [P] [US1] Contract test: `POST /api/events` con solo `media_url` (senza `content`) → `201`, evento salvato senza embedding in `core/tests/contract/test_events_contract.py`
- [X] T011 [P] [US1] Unit test: un evento con testo genera un embedding e passa a `status: embedded` (embedding client mockato) in `core/tests/unit/test_storage.py`
- [X] T012 [P] [US1] Unit test: lo stesso `event_id` ricevuto due volte non genera un secondo salvataggio/embedding (FR-007) in `core/tests/unit/test_storage.py`
- [X] T013 [P] [US1] Unit test: contenuto troppo corto/generico → `status: skipped_low_signal`, nessun embedding generato (FR-008) in `core/tests/unit/test_similarity.py`

### Implementation for User Story 1

- [X] T014 [US1] Implementa `POST /api/events` (validazione, persistenza, generazione embedding se il testo è già disponibile) in `core/src/api.py` (depends on T009-T012)
- [X] T015 [US1] Implementa `is_low_signal(text)` e collegala al flusso di embedding (FR-008) in `core/src/similarity.py` (depends on T013)
- [X] T016 [US1] Implementa `PATCH /api/events/{event_id}` (valorizza `normalized_text`, genera l'embedding mancante per audio/immagine — FR-003/FR-009) in `core/src/api.py`
- [X] T017 [US1] Collega il logging strutturato (event_id, esito) al flusso di ricezione/embedding in `core/src/api.py`

**Checkpoint**: User Story 1 funzionante e testabile in isolamento

---

## Phase 4: User Story 2 - Segnalazione di collegamenti con contenuti già salvati (Priority: P2)

**Goal**: un nuovo evento viene confrontato con quelli già salvati; se trova un collegamento
pertinente, lo individua (la segnalazione all'utente vera e propria è fuori scope, vedi
Assumptions in spec.md)

**Independent Test**: scenari 2 e 3 di `quickstart.md`

### Tests for User Story 2

- [X] T018 [P] [US2] Unit test: due embedding simili producono un collegamento sopra soglia in `core/tests/unit/test_similarity.py`
- [X] T019 [P] [US2] Unit test: nessun evento precedente salvato → nessun collegamento trovato (lista vuota) in `core/tests/unit/test_similarity.py`

### Implementation for User Story 2

- [X] T020 [US2] Implementa `find_similar(embedding, saved_events, threshold) -> list[Match]` in `core/src/similarity.py` (depends on T018, T019)
- [X] T021 [US2] Collega `find_similar` al flusso di `POST /api/events`/`PATCH` dopo la generazione dell'embedding e logga i collegamenti trovati in `core/src/api.py` (depends on T020, T014, T016)

**Checkpoint**: User Story 1 e 2 entrambe funzionanti in isolamento

---

## Phase 5: User Story 3 - Rispetto delle preferenze dell'utente sugli approfondimenti (Priority: P3)

**Goal**: la decisione di segnalare (o meno) un collegamento trovato rispetta le preferenze
salvate dall'utente, con un default ragionevole se non ne ha impostate

**Independent Test**: scenario 4 di `quickstart.md`

### Tests for User Story 3

- [X] T022 [P] [US3] Unit test: `depth_level: minimo` → nessuna segnalazione anche con collegamento pertinente in `core/tests/unit/test_insight.py`
- [X] T023 [P] [US3] Unit test: collegamento su un interesse specifico → priorità maggiore rispetto a un collegamento fuori interesse in `core/tests/unit/test_insight.py`
- [X] T024 [P] [US3] Unit test: utente senza preferenze salvate → default `equilibrato` (FR-006) in `core/tests/unit/test_storage.py`
- [X] T025 [P] [US3] Contract test: `GET /api/users/{user_id}/preferences` senza preferenze salvate risponde con i default, non `404` in `core/tests/contract/test_preferences_contract.py`
- [X] T026 [P] [US3] Contract test: `PUT /api/users/{user_id}/preferences` aggiorna e un `GET` successivo riflette il cambiamento in `core/tests/contract/test_preferences_contract.py`

### Implementation for User Story 3

- [X] T027 [US3] Implementa `decide_insight(matches, preferences) -> Insight | None` in `core/src/insight.py` (depends on T022, T023, T024)
- [X] T028 [US3] Implementa `GET`/`PUT /api/users/{user_id}/preferences` con default in `core/src/api.py` (depends on T025, T026)
- [X] T029 [US3] Collega `decide_insight` al flusso di `POST /api/events`/`PATCH`, dopo `find_similar` (depends on T027, T021)

**Checkpoint**: tutte e tre le user story funzionanti in isolamento

---

## Phase 6: Polish & Cross-Cutting Concerns

- [X] T030 [P] Aggiorna `core/README.md` con istruzioni di setup/esecuzione, rimandando a `quickstart.md`
- [ ] T031 Esegui tutti gli scenari di `quickstart.md` end-to-end (incluso `ingestion` reale, se disponibile) — verificato invece via contract test con `TestClient` e servizio di embedding mockato (vedi Notes)
- [X] T032 [P] Aggiungi una riga in `CHANGELOG.md` per il motore core completato (regola della constitution sul changelog condiviso)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: nessuna dipendenza
- **Foundational (Phase 2)**: dipende da Setup — blocca tutte le user story
- **US1 (Phase 3)**: dipende da Foundational — nessuna dipendenza da US2/US3
- **US2 (Phase 4)**: dipende da Foundational e dall'embedding generato in US1 (T014/T016) —
  logicamente estende il flusso di US1, non può essere validata in modo pienamente indipendente
  senza eventi già embeddati
- **US3 (Phase 5)**: dipende da Foundational e dai collegamenti trovati in US2 (T020) per poter
  decidere se segnalarli
- **Polish (Phase 6)**: dipende dalle user story che si vogliono rilasciare

### Parallel Opportunities

- T003-T007 (Setup/Foundational) in parallelo — file diversi
- Tutti i test `[P]` di una stessa user story in parallelo tra loro
- `api.py` è toccato da tutte e tre le user story (T014/T016, T021, T028/T029): coordinatevi se
  lavorate in parallelo su questo file, o implementate le user story in sequenza P1→P2→P3

---

## Implementation Strategy

### MVP First

1. Setup → Foundational → US1
2. **STOP e valida**: scenari 1 e 5 di `quickstart.md`
3. US1 da sola è già un motore che accetta e indicizza eventi — deployabile come MVP anche
   senza segnalazione di collegamenti

### Incremental Delivery

1. Setup + Foundational → base pronta
2. US1 (salvataggio + embedding) → valida → MVP
3. US2 (collegamenti trovati) → valida
4. US3 (rispetto preferenze) → valida
5. Polish

## Notes

- Nessun endpoint nuovo per "segnalare un collegamento": in questa feature il collegamento
  trovato/deciso resta interno (log strutturato); il canale verso l'utente è responsabilità di
  `companion` (fuori scope, vedi Assumptions in spec.md).
- La creazione di nodi/archi nel grafo (`API_CONTRACT.md`, sezione 3) è fuori scope: rimandata
  a una feature dedicata al modulo `graph`.
- Verificato senza servizi esterni reali: 20 test automatici (`pytest`, unit + contract) tutti
  verdi, `create_app()` istanziato e route verificate senza errori. Il servizio esterno di
  embedding è mockato nei test contract; manca la verifica con un provider reale e con
  `ingestion` in esecuzione contro questa istanza (T031, da fare quando entrambi saranno
  disponibili insieme).
- `POST`/`PATCH /api/events` rispondono subito e delegano embedding + ricerca similarità +
  decisione insight a un `BackgroundTask` di FastAPI (SC-001): la risposta non attende la
  chiamata al servizio esterno.
- Commit dopo ogni task o gruppo logico, con aggiornamento di `CHANGELOG.md` per i commit
  rilevanti (regola constitution).
