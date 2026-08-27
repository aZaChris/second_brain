---

description: "Task list for 010-stt-captioning-locale"
---

# Tasks: STT e Captioning Locali in Pipeline

**Input**: Design documents from `/specs/010-stt-captioning-locale/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md,
contracts/transcribe-caption-interface.md, quickstart.md

**Tests**: `pipeline/tests/unit/test_transcription.py` e `test_captioning.py` chiamano oggi
`transcribe()`/`caption()` con la vecchia firma (`api_url=`/`api_token=` sciolti) — vanno
**riscritti per intero**, non solo estesi (confermato dall'utente). `test_worker.py` mocka già
`src.worker.transcribe`/`caption` a livello di modulo: non richiede riscrittura, solo un aggiornamento
dei dati di test (T009).

**Organization**: Foundational riscrive il codice condiviso; le fasi per story sono soprattutto
validazione secondo `quickstart.md`, stesso schema di `009-embedding-locale-core`.

## Format: `[ID] [P?] [Story] Description`

## Path Conventions

Tutto dentro `pipeline/` — nessun altro modulo toccato (plan.md).

---

## Phase 1: Setup

- [X] T001 Aggiungere `faster-whisper` e `transformers` a `pipeline/requirements.txt`
- [X] T002 Aggiornare `pipeline/Dockerfile`: passo `RUN pip install torch --index-url
  https://download.pytorch.org/whl/cpu` prima di `pip install -r requirements.txt` (stesso fix
  di `009-embedding-locale-core`, applicato qui preventivamente — research.md)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Riscrivere `transcription.py`/`captioning.py`/`config.py`/`worker.py` per i modelli
locali, mantenendo le modalità esterne come fallback indipendenti. Blocca tutte le user story.

- [X] T003 Aggiornare `pipeline/src/config.py`: nuovi campi `stt_mode`/`captioning_mode`
  (default `"local"` ciascuno), `stt_model_name` (default `"base"`), `stt_model_cache`,
  `captioning_model_name` (default `"Salesforce/blip-image-captioning-base"`),
  `captioning_model_cache`; rendere `stt_api_url`/`stt_api_token`/`captioning_api_url`/
  `captioning_api_token` opzionali; `from_env()` valida solo le variabili richieste dalla
  combinazione di modalità effettiva (data-model.md)
- [X] T004 Riscrivere `pipeline/src/transcription.py`: `preload(config)` (carica `WhisperModel`
  di `faster-whisper` una sola volta se `stt_mode == "local"`), `transcribe(audio_bytes, *,
  config)` che smista tra `_transcribe_local` e `_transcribe_external` (stesso corpo HTTP/retry
  di oggi, invariato, letto da `config`) (contracts/transcribe-caption-interface.md)
- [X] T005 Riscrivere `pipeline/src/captioning.py`: `preload(config)` (carica la pipeline BLIP di
  `transformers` una sola volta se `captioning_mode == "local"`), `caption(image_bytes, *,
  config)` che smista tra `_caption_local` e `_caption_external` (stesso corpo HTTP/retry di
  oggi, invariato) (contracts/transcribe-caption-interface.md)
- [X] T006 Aggiornare `pipeline/src/worker.py`: chiamare `transcription.preload(config)` e
  `captioning.preload(config)` una sola volta in `main()` prima del loop `while True`; i 2 punti
  di chiamata in `process_event` passano `config=config`; **correggere `model_used`**, oggi
  hardcoded a `"stt-external"`/`"captioning-external"` a prescindere dalla modalità — derivarlo
  da `config.stt_mode`/`config.captioning_mode` (es. `f"stt-{config.stt_mode}"`)
- [X] T007 [P] Riscrivere per intero `pipeline/tests/unit/test_transcription.py`: test per
  modalità locale (`WhisperModel` mockato, nessun download reale, verifica che nessun
  `httpx.Client`/`httpx.post` venga chiamato) e per modalità esterna (stessi scenari già
  esistenti: successo, retry, errore dopo max tentativi)
- [X] T008 [P] Riscrivere per intero `pipeline/tests/unit/test_captioning.py`: stessa struttura
  di T007 per la pipeline BLIP mockata
- [X] T009 Aggiornare `pipeline/tests/unit/test_worker.py::make_config()`: aggiungere
  `stt_mode="external"`, `captioning_mode="external"` esplicitamente, così le asserzioni
  esistenti su `model_used == "stt-external"`/`"captioning-external"` restano valide dopo la
  correzione di T006 (lo scenario di quel file testa il percorso esterno, non va riscritto per il
  locale)
- [X] T010 Eseguire `pipeline/.venv/bin/pytest pipeline/tests` e correggere eventuali
  regressioni nei test di contratto (`test_patch_contract.py`) causate dai cambi di T003-T006

**Checkpoint**: modalità locale funzionante di default per STT e captioning indipendentemente,
modalità esterne preservate, suite di test esistente verde.

---

## Phase 3: User Story 1 - Nessun file audio o immagine lascia il nodo (Priority: P1) 🎯 MVP

**Independent Test**: inviare un evento audio e un evento immagine, osservare che nessuna
richiesta raggiunge un servizio esterno.

- [ ] T011 [US1] Eseguire `quickstart.md` §3-4: confermare che nessuna chiamata esterna viene
  generata durante l'elaborazione di eventi audio/immagine in modalità locale (SC-001, SC-004)

**Checkpoint**: User Story 1 completa — è l'MVP di questa feature.

---

## Phase 4: User Story 2 - Stesso tempo di elaborazione di oggi (Priority: P2)

**Independent Test**: misurare il tempo dalla ricezione di un evento audio/immagine alla sua
elaborazione.

- [ ] T012 [US2] Eseguire `quickstart.md` §6: misurare i tempi di trascrizione e captioning per
  file tipici, confermare che restano entro il budget (SC-002)

**Checkpoint**: User Story 1 e 2 verificate.

---

## Phase 5: User Story 3 - Nessun ri-download dei pesi ad ogni riavvio (Priority: P3)

**Independent Test**: riavviare il processo con la cache già popolata, verificare assenza di
download.

- [ ] T013 [US3] Eseguire `quickstart.md` §5: riavviare il processo con `STT_MODEL_CACHE`/
  `CAPTIONING_MODEL_CACHE` già popolate, confermare nessun nuovo download (SC-003)

**Checkpoint**: tutte e 3 le user story indipendentemente verificate.

---

## Phase 6: Polish & Cross-Cutting Concerns

- [X] T014 [P] Aggiungere in `specs/006-pipeline-transcription-captioning/research.md` una nota
  che rimanda a `specs/010-stt-captioning-locale/` per la decisione aggiornata su STT/captioning
  (stesso pattern di redirect già usato in `002-core-similarity-engine`)
- [X] T015 [P] Aggiornare `CHANGELOG.md` con questa feature
- [X] T016 [P] Verificare che `DEPLOY.md` resti coerente con i nomi di variabile finali scelti in
  T003 (`STT_MODE`, `STT_MODEL_CACHE`, `STT_MODEL_NAME`, `CAPTIONING_MODE`,
  `CAPTIONING_MODEL_CACHE`, `CAPTIONING_MODEL_NAME`)

---

## Dependencies & Execution Order

- **Setup (Phase 1)**: nessuna dipendenza
- **Foundational (Phase 2)**: dipende da Setup — blocca tutte le user story
- **US1/US2/US3 (Phase 3-5)**: dipendono da Foundational, indipendenti tra loro
- **Polish (Phase 6)**: dopo le user story che si vogliono validare

### Parallel Opportunities

- T007/T008 (file di test diversi) sono `[P]` una volta che T004/T005 definiscono l'interfaccia
- T014-T016 in Polish sono `[P]`: file diversi

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Setup + Foundational (T001-T010)
2. User Story 1 (T011) — valida il beneficio primario (privacy)

### Incremental Delivery

1. Setup + Foundational → STT/captioning locali funzionanti, test verdi
2. + US1 → privacy confermata (MVP)
3. + US2 → tempi confermati
4. + US3 → comportamento cache al riavvio confermato
5. + Polish → documentazione coerente
