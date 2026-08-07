---

description: "Task list for Bot Telegram di Ingestion"
---

# Tasks: Bot Telegram di Ingestion

**Input**: Design documents from `/specs/001-ingestion-bot/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/events.md, quickstart.md

**Tests**: Incluse — logica non banale (whitelist, normalizzazione, retry/backoff) va coperta
per rispettare il principio "API testabili indipendentemente" della constitution.

**Organization**: Task raggruppati per user story (spec.md) per implementazione e test
indipendenti.

## Path Conventions

Progetto singolo dentro il modulo esistente `ingestion/` del monorepo (per `plan.md`):
`ingestion/src/`, `ingestion/tests/unit/`, `ingestion/tests/contract/`.

---

## Phase 1: Setup

**Purpose**: Inizializzazione del progetto Python dentro `ingestion/`

- [X] T001 Crea la struttura `ingestion/src/`, `ingestion/tests/unit/`, `ingestion/tests/contract/` per plan.md
- [X] T002 Crea `ingestion/requirements.txt` con `python-telegram-bot`, `httpx`, `pytest`
- [X] T003 [P] Implementa il caricamento configurazione da env var (`BOT_TOKEN`, `AUTHORIZED_USER_IDS`, `CORE_EVENTS_URL`, `CORE_API_TOKEN`) in `ingestion/src/config.py`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Componenti condivisi da tutte le user story

**⚠️ CRITICAL**: nessuna user story può iniziare prima che questa fase sia completa

- [X] T004 [P] Implementa il controllo whitelist in `ingestion/src/auth.py` (`is_authorized(user_id) -> bool`, FR-001)
- [X] T005 [P] Configura logging strutturato su stdout (livello, event_id, esito) in `ingestion/src/logging_setup.py`
- [X] T006 Implementa il modello `NormalizedEvent` per `data-model.md` in `ingestion/src/events.py`
- [X] T007 Implementa il client HTTP verso `core` (`send_event`) su `POST /api/events` per `contracts/events.md`, in `ingestion/src/events.py` (depends on T006)
- [X] T008 Crea lo scheletro del bot (avvio long polling, dependency wiring di config/auth/events) in `ingestion/src/bot.py` (depends on T003, T004, T007)

**Checkpoint**: fondamenta pronte, le user story possono iniziare

---

## Phase 3: User Story 1 - Invio messaggio di testo (Priority: P1) 🎯 MVP

**Goal**: l'utente autorizzato invia testo, riceve conferma, `core` riceve l'evento normalizzato

**Independent Test**: scenario 1 di `quickstart.md` — inviare un messaggio di testo e
verificare conferma entro 5s e ricezione dell'evento da parte di `core`

### Tests for User Story 1

- [X] T009 [P] [US1] Unit test: utente non in whitelist viene bloccato in `ingestion/tests/unit/test_auth.py`
- [X] T010 [P] [US1] Unit test: normalizzazione di un messaggio di testo → `NormalizedEvent` in `ingestion/tests/unit/test_events.py`
- [X] T011 [P] [US1] Contract test: payload di un evento `type: text` rispetta `API_CONTRACT.md` in `ingestion/tests/contract/test_events_contract.py`

### Implementation for User Story 1

- [X] T012 [US1] Implementa l'handler dei messaggi di testo (whitelist → normalizza → invia a core) in `ingestion/src/bot.py` (depends on T009-T011)
- [X] T013 [US1] Implementa la risposta di conferma ricezione all'utente in `ingestion/src/bot.py` (depends on T012)
- [X] T014 [US1] Collega il logging strutturato (event_id, esito) al flusso testo in `ingestion/src/bot.py` (depends on T012)

**Checkpoint**: User Story 1 funzionante e testabile in isolamento

---

## Phase 4: User Story 2 - Invio messaggio audio o immagine (Priority: P2)

**Goal**: l'utente invia un vocale o una foto, il bot inoltra un evento con `media_url` e
conferma la ricezione

**Independent Test**: scenario 2 di `quickstart.md` — inviare un audio/foto e verificare che
l'evento abbia `type: audio`/`image` e `media_url` valorizzato

### Tests for User Story 2

- [X] T015 [P] [US2] Unit test: normalizzazione di un messaggio audio/immagine → `NormalizedEvent` con `media_url` in `ingestion/tests/unit/test_events.py`
- [X] T016 [P] [US2] Contract test: payload di un evento `type: audio`/`image` rispetta `API_CONTRACT.md` in `ingestion/tests/contract/test_events_contract.py`

### Implementation for User Story 2

- [X] T017 [US2] Implementa l'handler audio/immagine (upload su storage condiviso, `media_url`) in `ingestion/src/bot.py` (depends on T015, T016)
- [X] T018 [US2] Implementa la risposta "tipo non supportato" per sticker/video/documenti, senza inoltro (FR-009) in `ingestion/src/bot.py`

**Checkpoint**: User Story 1 e 2 entrambe funzionanti in isolamento

---

## Phase 5: User Story 3 - Gestione errori di rete verso il backend (Priority: P3)

**Goal**: retry con backoff sulle chiamate a `core`; notifica l'utente in caso di fallimento
definitivo; nessun evento duplicato sui doppi recapiti Telegram

**Independent Test**: scenario 4 di `quickstart.md` — fermare `core`, inviare un messaggio,
verificare i retry nei log e la notifica di fallimento all'utente

### Tests for User Story 3

- [X] T019 [P] [US3] Unit test: retry con backoff esponenziale su 503/timeout, max 3 tentativi in `ingestion/tests/unit/test_events.py`
- [X] T020 [P] [US3] Unit test: notifica utente dopo fallimento definitivo in `ingestion/tests/unit/test_bot.py`
- [X] T021 [P] [US3] Unit test: stesso `message_id` ricevuto due volte genera un solo evento in `ingestion/tests/unit/test_bot.py`

### Implementation for User Story 3

- [X] T022 [US3] Completa la logica di retry/backoff in `send_event` (`ingestion/src/events.py`, estende T007) (depends on T019)
- [X] T023 [US3] Implementa la notifica di fallimento definitivo all'utente in `ingestion/src/bot.py` (depends on T020, T022)
- [X] T024 [US3] Implementa la deduplica in-memory su `message_id` (TTL breve) in `ingestion/src/bot.py` (depends on T021)

**Checkpoint**: tutte e tre le user story funzionanti in isolamento

---

## Phase 6: Polish & Cross-Cutting Concerns

- [X] T025 [P] Aggiorna `ingestion/README.md` con istruzioni di setup/esecuzione, rimandando a `quickstart.md`
- [ ] T026 Esegui tutti gli scenari di `quickstart.md` end-to-end contro un'istanza di `core` (bloccato: `core` non ancora implementato — verificato invece con test automatici e avvio a secco del bot, vedi Notes)
- [X] T027 [P] Aggiungi una riga in `CHANGELOG.md` per il bot ingestion completato (regola della constitution sul changelog condiviso)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: nessuna dipendenza
- **Foundational (Phase 2)**: dipende da Setup — blocca tutte le user story
- **User Story 1 (Phase 3)**: dipende da Foundational — nessuna dipendenza da US2/US3
- **User Story 2 (Phase 4)**: dipende da Foundational — indipendente da US1/US3, ma richiede lo stesso handler skeleton di `bot.py` creato in T008
- **User Story 3 (Phase 5)**: dipende da Foundational — estende `send_event` (T007) e `bot.py`, indipendente nella logica ma tocca gli stessi file di US1/US2 (attenzione ai conflitti se lavorate in parallelo su `bot.py`)
- **Polish (Phase 6)**: dipende dalle user story che si vogliono rilasciare

### Parallel Opportunities

- T003, T004, T005 (Setup/Foundational) in parallelo — file diversi
- Tutti i test [P] di una stessa user story in parallelo tra loro
- US1 e US2 possono procedere in parallelo dopo la Fase 2 se lavorate da persone diverse; US3 tocca gli stessi file (`events.py`, `bot.py`) di US1/US2 quindi va coordinata (sync breve, come da constitution) o fatta dopo

---

## Implementation Strategy

### MVP First

1. Fase 1 (Setup) → Fase 2 (Foundational) → Fase 3 (US1)
2. **STOP e valida**: scenario 1 di `quickstart.md`
3. US1 da sola è già un bot di ingestion testuale funzionante — deployabile come MVP

### Incremental Delivery

1. Setup + Foundational → base pronta
2. US1 (testo) → valida → MVP
3. US2 (audio/immagine) → valida
4. US3 (affidabilità di rete) → valida
5. Polish

## Notes

- Nessuna user story richiede storage persistente (privacy-first, constitution I).
- `events.py` e `bot.py` sono toccati da più user story: se in due lavorate in parallelo su
  questa feature, coordinatevi su questi due file per evitare conflitti di merge.
- Commit dopo ogni task o gruppo logico, con aggiornamento di `CHANGELOG.md` per i commit
  rilevanti (regola constitution).
- Verificato senza `core` reale: 12 test automatici (`pytest`, unit + contract) tutti verdi,
  `build_application()` istanziato con token/whitelist fittizi senza errori, `Config.from_env()`
  fallisce correttamente in assenza di variabili d'ambiente. Manca la verifica end-to-end vera
  (bot Telegram reale + `core` in esecuzione) — da fare quando `core` sarà pronto (T026).
- Il `media_url` per audio/immagine usa l'URL temporaneo servito da Telegram
  (`bot.get_file().file_path`, vedi `ponytail:` in `ingestion/src/bot.py::handle_media`): scade
  dopo un po', va sostituito con un upload su storage condiviso quando `pipeline` sarà
  implementato e avrà bisogno di leggere il file oltre quella finestra.
