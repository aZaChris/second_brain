---

description: "Task list for Trascrizione Audio e Captioning Immagini (Pipeline)"
---

# Tasks: Trascrizione Audio e Captioning Immagini (Pipeline)

**Input**: Design documents from `/specs/006-pipeline-transcription-captioning/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/pipeline-core.md, quickstart.md

**Tests**: Incluse — stesso approccio già usato per gli altri moduli.

**Organization**: Task raggruppati per user story (spec.md).

## Path Conventions

Nuovo modulo `pipeline/`: `pipeline/src/`, `pipeline/tests/unit/`, `pipeline/tests/contract/`.

---

## Phase 1: Setup

- [X] T001 Crea la struttura `pipeline/src/`, `pipeline/tests/unit/`, `pipeline/tests/contract/` per plan.md
- [X] T002 Crea `pipeline/requirements.txt` con `httpx`, `pytest`
- [X] T003 [P] Implementa il caricamento configurazione da env var (`CORE_API_URL`, `CORE_API_TOKEN`, `STT_API_URL`/`STT_API_TOKEN`, `CAPTIONING_API_URL`/`CAPTIONING_API_TOKEN`, `POLL_INTERVAL_SECONDS`) in `pipeline/src/config.py`

---

## Phase 2: Foundational (Blocking Prerequisites)

**⚠️ CRITICAL**: nessuna user story può iniziare prima che questa fase sia completa

- [X] T004 [P] Implementa `core_client.get_pending(types, limit)` e `core_client.patch_event(event_id, normalized_text, meta)` con retry/backoff in `pipeline/src/core_client.py`
- [X] T005 [P] Implementa `media.download_media(media_url)` con retry/backoff, `MediaUnreachableError` su fallimento definitivo (FR-006) in `pipeline/src/media.py`
- [X] T006 Crea lo scheletro del worker (loop di polling, dispatch per `type`, dependency wiring) in `pipeline/src/worker.py` (depends on T003, T004, T005)

**Checkpoint**: fondamenta pronte, le user story possono iniziare

---

## Phase 3: User Story 1 - Trascrizione dei messaggi vocali (Priority: P1) 🎯 MVP

**Goal**: gli eventi audio in attesa vengono trascritti e il risultato inviato a `core`

**Independent Test**: scenari 1, 2 di `quickstart.md`

### Tests for User Story 1

- [X] T007 [P] [US1] Unit test: `transcription.transcribe` chiama il servizio esterno e ritorna il testo in `pipeline/tests/unit/test_transcription.py`
- [X] T008 [P] [US1] Unit test: `transcription.transcribe` riprova con backoff su errore transitorio del servizio STT in `pipeline/tests/unit/test_transcription.py`
- [X] T009 [P] [US1] Contract test: il `PATCH` inviato a `core` per un evento audio ha `normalized_text` e `pipeline_meta` conformi ad `API_CONTRACT.md` in `pipeline/tests/contract/test_patch_contract.py`

### Implementation for User Story 1

- [X] T010 [US1] Implementa `transcription.transcribe(audio_bytes)` via servizio esterno, con retry/backoff in `pipeline/src/transcription.py` (depends on T007, T008)
- [X] T011 [US1] Implementa la gestione degli eventi audio nel worker (scarica, trascrive, `PATCH` con `pipeline_meta.status: "ok"`) in `pipeline/src/worker.py` (depends on T009, T010)

**Checkpoint**: User Story 1 funzionante e testabile in isolamento

---

## Phase 4: User Story 2 - Descrizione delle immagini (Priority: P2)

**Goal**: gli eventi immagine in attesa vengono descritti e il risultato inviato a `core`

**Independent Test**: scenario 3 di `quickstart.md`

### Tests for User Story 2

- [X] T012 [P] [US2] Unit test: `captioning.caption` chiama il servizio esterno e ritorna il testo in `pipeline/tests/unit/test_captioning.py`
- [X] T013 [P] [US2] Unit test: `captioning.caption` riprova con backoff su errore transitorio del servizio di captioning in `pipeline/tests/unit/test_captioning.py`
- [X] T014 [P] [US2] Contract test: il `PATCH` inviato a `core` per un evento immagine ha `normalized_text` e `pipeline_meta` conformi ad `API_CONTRACT.md` in `pipeline/tests/contract/test_patch_contract.py`

### Implementation for User Story 2

- [X] T015 [US2] Implementa `captioning.caption(image_bytes)` via servizio esterno, con retry/backoff in `pipeline/src/captioning.py` (depends on T012, T013)
- [X] T016 [US2] Implementa la gestione degli eventi immagine nel worker in `pipeline/src/worker.py` (depends on T014, T015)

**Checkpoint**: User Story 1 e 2 entrambe funzionanti in isolamento

---

## Phase 5: User Story 3 - Gestione di file non raggiungibili o servizi esterni non disponibili (Priority: P3)

**Goal**: un fallimento definitivo (file irraggiungibile o servizio esterno esaurito dopo i
retry) viene sempre comunicato a `core`, l'evento non resta mai bloccato in `pending`

**Independent Test**: scenari 4, 5 di `quickstart.md`

### Tests for User Story 3

- [X] T017 [P] [US3] Unit test: `media.download_media` solleva `MediaUnreachableError` dopo i retry su file irraggiungibile in `pipeline/tests/unit/test_media.py`
- [X] T018 [P] [US3] Unit test: il worker invia un `PATCH` con testo segnaposto e `pipeline_meta.status: "failed"` su file irraggiungibile in `pipeline/tests/unit/test_worker.py`
- [X] T019 [P] [US3] Unit test: il worker invia lo stesso esito quando il servizio esterno di trascrizione/captioning resta indisponibile dopo i retry in `pipeline/tests/unit/test_worker.py`
- [X] T020 [P] [US3] Contract test: il payload di `PATCH` su fallimento definitivo include `pipeline_meta.reason` in `pipeline/tests/contract/test_patch_contract.py`

### Implementation for User Story 3

- [X] T021 [US3] Implementa la gestione dei fallimenti definitivi (testo segnaposto + `pipeline_meta.status`/`reason`, research.md) nel worker in `pipeline/src/worker.py` (depends on T017-T020)

**Checkpoint**: tutte e tre le user story funzionanti in isolamento

---

## Phase 6: Polish & Cross-Cutting Concerns

- [X] T022 [P] Aggiorna `pipeline/README.md` con istruzioni di setup/esecuzione, rimandando a `quickstart.md`
- [ ] T023 Esegui tutti gli scenari di `quickstart.md` end-to-end (bloccato: servono `core` in esecuzione e provider STT/captioning reali — verificato invece con 15 test automatici a servizi mockati, vedi Notes)
- [X] T024 [P] Aggiungi una riga in `CHANGELOG.md` per il modulo pipeline completato (regola della constitution sul changelog condiviso)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: nessuna dipendenza
- **Foundational (Phase 2)**: dipende da Setup — blocca tutte le user story
- **US1 (Phase 3)**: dipende da Foundational — nessuna dipendenza da US2/US3
- **US2 (Phase 4)**: dipende da Foundational — indipendente da US1, ma tocca lo stesso
  `worker.py`
- **US3 (Phase 5)**: dipende da Foundational e dal percorso di successo già presente nel worker
  (US1/US2) per aggiungere la gestione del fallimento accanto ad esso
- **Polish (Phase 6)**: dipende dalle user story che si vogliono rilasciare

### Parallel Opportunities

- T003, T004, T005 (Setup/Foundational) in parallelo — file diversi
- Tutti i test `[P]` di una stessa user story in parallelo tra loro
- `worker.py` è toccato da tutte e tre le user story: implementate in sequenza P1→P2→P3 se
  lavorate in parallelo su questo file, o coordinatevi

---

## Implementation Strategy

### MVP First

1. Setup → Foundational → US1
2. **STOP e valida**: scenari 1, 2 di `quickstart.md`
3. US1 da sola sblocca già la trascrizione — deployabile come MVP anche senza captioning

### Incremental Delivery

1. Setup + Foundational → base pronta
2. US1 (trascrizione) → valida → MVP
3. US2 (captioning) → valida
4. US3 (gestione errori) → valida
5. Polish

## Notes

- Nessun nuovo endpoint per segnalare un fallimento: si riusa `PATCH /api/events/{event_id}`
  con testo segnaposto (research.md) — coerente con `007-core-pending-events`, che considera
  "elaborato" ogni evento con `normalized_text` valorizzato, qualunque ne sia il contenuto.
- Nessuna dipendenza da `tenacity`: retry a backoff in poche righe di stdlib, stesso pattern di
  `ingestion`/`core`.
- Verificato senza servizi esterni/`core` reali: 15 test automatici (`pytest`, unit + contract)
  tutti verdi, `Config.from_env()` e caricamento di `worker.py` verificati senza errori. Manca
  la validazione end-to-end vera (T023) — da fare quando `core` e i provider STT/captioning
  reali saranno disponibili insieme.
- Commit dopo ogni task o gruppo logico, con aggiornamento di `CHANGELOG.md` per i commit
  rilevanti (regola constitution).
