---

description: "Task list for 009-embedding-locale-core"
---

# Tasks: Embedding Locale in Core

**Input**: Design documents from `/specs/009-embedding-locale-core/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/embed-interface.md, quickstart.md

**Tests**: I test di contratto esistenti (`core/tests/contract/`) già mockano `src.api.embed` a
livello di modulo e non vengono toccati da questa feature (verificato: i loro fixture
costruiscono `Config` con campi che restano validi). Aggiungo un solo file di unit test nuovo,
`test_embedding.py`, che oggi non esiste, perché il modulo che riscrivo non ha copertura propria.

**Organization**: Foundational riscrive il codice condiviso da tutte le user story (il default
locale copre già FR-001/FR-007 non appena Foundational è completo); le fasi per story sono
soprattutto validazione secondo `quickstart.md`.

## Format: `[ID] [P?] [Story] Description`

## Path Conventions

Tutto dentro `core/` — nessun altro modulo toccato (plan.md).

---

## Phase 1: Setup

- [X] T001 Aggiungere `sentence-transformers` a `core/requirements.txt`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Riscrivere `embedding.py`/`config.py`/`api.py`/`main.py` per il modello locale,
mantenendo la modalità esterna come fallback configurabile. Blocca tutte le user story.

- [X] T002 Aggiornare `core/src/config.py`: nuovi campi `embedding_mode` (default `"local"`),
  `embedding_model_name` (default `"paraphrase-multilingual-MiniLM-L12-v2"`),
  `embedding_model_cache`; rendere `embedding_api_url`/`embedding_api_token` opzionali;
  `from_env()` valida solo le variabili richieste dalla modalità effettiva (data-model.md)
- [X] T003 Riscrivere `core/src/embedding.py`: `preload(config)` (carica
  `SentenceTransformer` una sola volta in una variabile module-level, solo se
  `embedding_mode == "local"`), `embed(text, *, config, client=None)` che smista tra
  `_embed_local` (usa il modello precaricato, solleva `EmbeddingError` se `preload()` non è
  stato chiamato) e `_embed_external` (stesso corpo HTTP di oggi, invariato)
  (contracts/embed-interface.md)
- [X] T004 Aggiornare `core/src/main.py`: chiamare `embedding.preload(config)` prima di
  `create_app(config)` — solo nell'entrypoint di produzione, non dentro `create_app()`, così i
  test che chiamano `create_app()` direttamente non innescano un caricamento reale del modello
  (research.md: caricamento eager una sola volta all'avvio del processo)
- [X] T005 Aggiornare i 2 punti di chiamata a `embed()` in `core/src/api.py`
  (`_process_event_text`, `search_events`): passano `config=config` invece di
  `api_url=`/`api_token=` sciolti (contracts/embed-interface.md)
- [X] T006 In `core/src/api.py`, filtrare `saved_events`/`candidates` per dimensionalità del
  vettore coerente con quella appena calcolata, prima di passarli a `find_similar`/
  `cosine_similarity` in entrambi i punti (`_process_event_text`, `search_events`) — FR-006,
  senza toccare `similarity.py`
- [X] T007 [P] Creare `core/tests/unit/test_embedding.py`: mockare `SentenceTransformer` (non
  scaricare pesi reali nei test) per verificare che `preload()` + `embed()` in modalità locale
  ritornino un vettore della lunghezza attesa senza istanziare alcun `httpx.Client`; verificare
  che la modalità esterna mantenga il comportamento HTTP/retry già esistente
  (contracts/embed-interface.md "Verifica del contratto")
- [X] T008 Eseguire `core/.venv/bin/pytest core/tests` e correggere eventuali regressioni nei
  test di contratto esistenti causate dai cambi di T002-T006

**Checkpoint**: modalità locale funzionante di default, modalità esterna preservata, suite di
test esistente verde — le user story sono ora validabili.

---

## Phase 3: User Story 1 - Nessun testo personale lascia il nodo (Priority: P1) 🎯 MVP

**Goal**: nessuna chiamata di rete esterna durante la generazione dell'embedding in modalità
locale (default).

**Independent Test**: inviare un evento testuale e osservare che nessuna richiesta raggiunge un
servizio esterno di embedding.

- [X] T009 [US1] Eseguire `quickstart.md` §3-4: confermare che nessuna chiamata esterna viene
  generata durante l'elaborazione di un evento in modalità locale (SC-001, SC-004)

**Checkpoint**: User Story 1 completa — è l'MVP di questa feature (il resto è già rispettato solo
completando Foundational, dato che locale è il default).

---

## Phase 4: User Story 2 - Stessa reattività di oggi (Priority: P2)

**Goal**: generazione dell'embedding entro lo stesso budget di tempo già garantito da
`002-core-similarity-engine`.

**Independent Test**: misurare il tempo dall'invio di un evento alla disponibilità del suo
embedding.

- [X] T010 [US2] Eseguire `quickstart.md` §6: misurare il tempo di generazione embedding per una
  nota tipica, confermare che resta entro il budget (SC-002). **Risultato reale (2026-08-25,
  ambiente di sviluppo condiviso, non ZimaBlade dedicato)**: prima chiamata dopo l'avvio ~5.2s
  (cold-start CPU/thread warmup di `torch`), seconda chiamata 1.27s, evento successivo dopo
  riavvio con cache calda 2.26s dalla ricezione all'embedding completato — al limite del budget
  di 2s, non ampiamente entro come per il vecchio servizio esterno. Da riverificare su ZimaBlade
  reale (4 CPU dedicate, non condivise con il resto del sistema come in questo sandbox); se
  restasse borderline, valutare `torch.set_num_threads()` esplicito o un batch/warmup all'avvio.
- [ ] T011 [US2] Se `core` mostra contesa di CPU misurabile con `graph`/`companion` sul nodo
  condiviso (non testato qui: richiede i 5 moduli attivi insieme, non disponibile senza Docker in
  questo ambiente), aggiungere `cpus`/`mem_limit` a `core/docker-compose.yml` (nota non bloccante
  già in plan.md — condizionale, non eseguita)

**Checkpoint**: User Story 1 e 2 verificate.

---

## Phase 5: User Story 3 - Nessun ri-download dei pesi ad ogni riavvio (Priority: P3)

**Goal**: un riavvio del processo con cache già popolata non ri-scarica i pesi.

**Independent Test**: riavviare il processo con la cache già popolata, verificare assenza di
download.

- [X] T012 [US3] Eseguire `quickstart.md` §5: riavviare il processo con
  `EMBEDDING_MODEL_CACHE` già popolata, confermare nessun nuovo download (SC-003)

**Checkpoint**: tutte e 3 le user story indipendentemente verificate.

---

## Phase 6: Polish & Cross-Cutting Concerns

- [X] T013 [P] Aggiungere in `specs/002-core-similarity-engine/research.md` una nota che rimanda
  a `specs/009-embedding-locale-core/` per la decisione aggiornata sull'embedding (redirect
  esplicito invece di riscrivere il documento originale, evita contenuti duplicati che
  divergono nel tempo)
- [X] T014 [P] Aggiornare `CHANGELOG.md` con questa feature
- [X] T015 [P] Verificare che `DEPLOY.md` (già aggiornato da `008-docker-deployment`) resti
  coerente con i nomi di variabile finali scelti in T002 (`EMBEDDING_MODE`,
  `EMBEDDING_MODEL_CACHE`, `EMBEDDING_MODEL_NAME`)

---

## Dependencies & Execution Order

- **Setup (Phase 1)**: nessuna dipendenza
- **Foundational (Phase 2)**: dipende da Setup — blocca tutte le user story
- **US1/US2/US3 (Phase 3-5)**: dipendono da Foundational, indipendenti tra loro (solo
  validazione, nessun codice condiviso aggiuntivo salvo l'eccezione condizionale T011)
- **Polish (Phase 6)**: dopo le user story che si vogliono validare

### Parallel Opportunities

- T007 (nuovo file di test) è `[P]`, indipendente dagli altri task di Foundational una volta che
  l'interfaccia di `embed()`/`preload()` è definita in T003
- T013-T015 in Polish sono `[P]`: file diversi, nessuna dipendenza tra loro

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Setup + Foundational (T001-T008)
2. User Story 1 (T009) — valida il beneficio primario (privacy)
3. Già un deploy utilizzabile: l'embedding non lascia più il nodo, prima ancora di misurare
   formalmente i tempi (US2) o validare il comportamento della cache al riavvio (US3)

### Incremental Delivery

1. Setup + Foundational → embedding locale funzionante, test verdi
2. + US1 → privacy confermata (MVP)
3. + US2 → reattività confermata, eventuale tuning risorse
4. + US3 → comportamento cache al riavvio confermato
5. + Polish → documentazione e redirect coerenti
