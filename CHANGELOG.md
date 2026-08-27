# Changelog

Documento condiviso sempre visibile ad entrambi i collaboratori. Ogni commit rilevante
(nuovo modulo, endpoint, decisione architetturale) aggiunge una riga qui, così nessuno dei
due deve rileggere la history di git per sapere lo stato del progetto.

Formato: [Keep a Changelog](https://keepachangelog.com/it/1.1.0/).

## [Unreleased]

### Added
- Modulo `pipeline`: worker in background (nessun server HTTP proprio, come `ingestion`) che
  interroga `GET /api/events/pending`, scarica il file, trascrive audio o descrive immagini
  tramite servizi esterni, invia il risultato con `PATCH /api/events/{event_id}`. Su file
  irraggiungibile o servizio esterno esaurito dopo i retry, invia comunque un `PATCH` con testo
  segnaposto e `pipeline_meta.status: "failed"` — nessun nuovo endpoint per segnalare un
  fallimento, l'evento non resta mai bloccato in coda. Implementato secondo
  `specs/006-pipeline-transcription-captioning/`. 15 test automatici (unit + contract).
- Modulo `ingestion`: bot Telegram (Python, long polling) con whitelist utenti, normalizzazione
  testo/audio/immagine in evento, invio a `core` con retry a backoff esponenziale, notifica di
  fallimento all'utente, deduplica su `message_id`. Implementato secondo
  `specs/001-ingestion-bot/` (spec, plan, tasks). 12 test automatici (unit + contract).
- Modulo `core`: API FastAPI (`POST`/`PATCH /api/events`, `GET`/`PUT /api/users/{id}/preferences`)
  su storage SQLite. Genera embedding (servizio esterno) in background dopo la risposta, cerca
  collegamenti per similarità (cosine, numpy) tra eventi salvati, decide se segnalarli in base
  alle preferenze utente (con default se assenti). Implementato secondo
  `specs/002-core-similarity-engine/`. 20 test automatici (unit + contract).
- Modulo `graph`: API FastAPI (`POST /api/graph/nodes`, `POST /api/graph/edges`,
  `GET /api/graph/related/{node_id}`) su storage SQLite. Nodi idempotenti su `source_event_id`,
  relazioni validate (nodi esistenti, no self-loop), esplorazione con BFS in-process fino a una
  profondità data. Implementato secondo `specs/003-knowledge-graph/`. 18 test automatici (unit +
  contract).
- Struttura moduli (`ingestion`, `pipeline`, `core`, `graph`, `companion`) con README stub.
- `API_CONTRACT.md`: contratto REST tra tutti i moduli (eventi, normalizzazione, grafo,
  progetti/task, preferenze utente).
- `API_CONTRACT.md`: aggiunte sezioni 6-7 (`GET /api/events/search`, `GET /api/events`) per
  sbloccare ricerca e cronologia di `companion` — nessun endpoint esistente modificato. Spec
  della relativa estensione di `core` in `specs/005-core-search-history/`.
- Modulo `core`: aggiunti `GET /api/events/search` (ricerca semantica, riusa embedding/cosine
  similarity già esistenti) e `GET /api/events` (cronologia paginata con keyset pagination su
  `timestamp`), sblocca `companion` US1 e US3. Implementato secondo
  `specs/005-core-search-history/`. 9 nuovi test automatici (29 totali su `core`).
- `DEPLOY.md`: guida per far girare ingestion+core+graph tutti sul Raspberry Pi 4B (setup,
  variabili d'ambiente, unit `systemd`). Distingue esplicitamente la whitelist utenti di
  `ingestion` (filtro di prodotto) dai token Bearer tra servizi `core`/`graph` (segreti veri,
  da generare random e mai committare) — due controlli diversi, enforcement diverso.
- `API_CONTRACT.md`: aggiunta sezione 8 (`GET /api/events/pending`) per sbloccare la scoperta
  di eventi audio/immagine da elaborare per `pipeline` — additivo, nessun endpoint esistente
  modificato. Spec della relativa estensione di `core` in `specs/007-core-pending-events/`.
- Modulo `core`: aggiunto `GET /api/events/pending` (elenco eventi audio/immagine da
  trascrivere/descrivere, filtro per tipo, FIFO). L'idea chiave: il filtro si basa su
  `normalized_text IS NULL`, non sul campo `status` interno, per non far ricomparire eventi già
  trascritti se l'embedding fallisce dopo il `PATCH`. Sblocca `pipeline` US1/US2. Implementato
  secondo `specs/007-core-pending-events/`. 8 nuovi test automatici (37 totali su `core`).
- Modulo `companion` (US2): web app server-rendered (FastAPI + Jinja2, nessun frontend
  build) con `GET /explore` per navigare i collegamenti di un nodo su `graph`, esplorazione
  incrementale via link. Implementato secondo `specs/004-companion-app/` (scope US2). 9 test
  automatici (unit + contract). US1 (ricerca) e US3 (cronologia) restano da
  pianificare/implementare, anche se `core` le supporta già.
- `DEPLOY.md`: aggiunte le variabili d'ambiente e le unit `systemd` di `pipeline` e
  `companion` (mancavano dalla prima stesura, scritta solo per ingestion+core+graph).
  Aggiunto un terzo filtro di accesso alla sezione già esistente: l'utente mock di
  `companion` (`COMPANION_USERNAME`/`PASSWORD`), trattato come segreto vero al pari dei
  token tra servizi, non come la whitelist di prodotto.
- Modulo `companion` (US1 + utente mock): aggiunto `GET /search` (ricerca semantica via
  `core`). Aggiunto anche un gate di autenticazione HTTP Basic ("utente mock": una sola coppia
  utente/password da env var, `secrets.compare_digest`, nessun sistema di account) applicato a
  **tutte** le route, incluso `/explore` (retrofit su US2) — colma il gap su FR-006 notato in
  `spec.md`, resta un compromesso da rivedere se `companion` uscirà dalla rete locale.
  Implementato secondo `specs/004-companion-app/`. 12 nuovi test (21 totali su `companion`).
  US3 (cronologia) resta da pianificare/implementare.
- Scaffolding Speckit (`.specify/`) e `constitution.md` v1.1.0: privacy-first, modularità,
  API testabili indipendentemente, preferenza servizi esterni su modelli locali pesanti;
  regola su riepilogo di sessione e changelog condiviso.
- `constitution.md` v2.0.0: migrazione infrastrutturale da Raspberry Pi a ZimaBlade (Intel
  Celeron quad-core x86, 16GB RAM, storage SATA). Principio IV ridefinito da "servizi esterni
  preferiti" a "modelli locali preferiti per compiti CPU-compatibili" (embedding, STT,
  captioning) — ridefinizione non retrocompatibile (MAJOR bump). Vincoli Tecnici aggiornati:
  limiti di CPU/RAM per container su nodo unico invece di footprint minimo legato al Pi.
- Infrastruttura di deploy containerizzata (`008-docker-deployment`): un `Dockerfile` +
  `docker-compose.yml` indipendente per ciascun modulo (`ingestion`, `pipeline`, `core`,
  `graph`, `companion`), a sostituzione delle unit `systemd` su Raspberry Pi. Rete Docker
  condivisa esterna ai singoli compose (i moduli si raggiungono per nome servizio, non più
  `localhost:porta`), volumi bind-mount su storage SATA per i database e la cache dei pesi dei
  modelli locali, restart policy per ruolo (`unless-stopped` per API/bot, `on-failure` per il
  worker `pipeline`), limiti `cpus`/`mem_limit` sul container `pipeline` per non affamare gli
  altri moduli sulle 4 CPU condivise (preferite a `deploy.resources.limits`, non affidabile
  fuori da swarm). `DEPLOY.md` riscritto di conseguenza. Implementato secondo
  `specs/008-docker-deployment/`. Nessun test automatico (feature di infrastruttura, validata
  tramite `quickstart.md`); validazione end-to-end sui container non ancora eseguita in questa
  sessione — richiede un host Docker reale (non disponibile nell'ambiente di sviluppo usato per
  scrivere questa feature).
