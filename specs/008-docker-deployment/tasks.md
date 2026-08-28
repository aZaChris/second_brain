---

description: "Task list for 008-docker-deployment"
---

# Tasks: Infrastruttura di Deploy Containerizzata su ZimaBlade

**Input**: Design documents from `/specs/008-docker-deployment/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/compose-schema.md, quickstart.md

**Tests**: Nessun task di test automatico — la spec valida questa feature tramite gli scenari
manuali di `quickstart.md` (infrastruttura di deploy, non codice applicativo con test unitari).

**Stato implementazione (2026-08-25)**: tutti i task che producono codice/config (Dockerfile,
docker-compose.yml, DEPLOY.md, CHANGELOG.md) sono completati e marcati `[X]`. I task che
richiedono un daemon Docker in esecuzione (T001-T002, T013, T017-T019, T022, T024-T027) restano
`[ ]`: l'ambiente di sviluppo usato per scrivere questa feature non ha Docker disponibile (WSL
senza integrazione Docker Desktop attiva) — vanno eseguiti sul nodo ZimaBlade reale (o in un
ambiente con Docker funzionante) seguendo `quickstart.md`.

**Organization**: Le fasi Setup e Foundational producono l'infrastruttura Docker di base comune a
tutti i moduli; le fasi successive sono organizzate per user story (spec.md), ciascuna aggiunge
solo ciò che serve a quella storia specifica sopra la base comune.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Può girare in parallelo (file diversi, nessuna dipendenza da task non completati)
- **[Story]**: A quale user story appartiene (US1, US2, US3)

## Path Conventions

Un Dockerfile + un docker-compose.yml dentro la cartella di ciascun modulo esistente
(`ingestion/`, `pipeline/`, `core/`, `graph/`, `companion/`), come da `plan.md`.

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Predisporre sull'host ZimaBlade le risorse condivise da tutti i moduli, fuori da
ogni singolo compose.

- [ ] T001 Creare le directory di storage persistente su SATA sull'host:
  `/srv/second-brain/data/core`, `/srv/second-brain/data/graph`,
  `/srv/second-brain/models-cache/core`, `/srv/second-brain/models-cache/pipeline`
  (data-model.md)
- [X] ~~T002 [P] Creare la rete Docker condivisa `second-brain-net`~~ — obsoleto: dopo il
  consolidamento in un `docker-compose.yml` di root (research.md), la rete di default del progetto
  Compose copre lo stesso bisogno, nessun passo manuale richiesto

**Checkpoint**: Rete e directory pronte — i moduli possono ora essere containerizzati.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Dockerfile e scheletro compose minimo per ciascuno dei 5 moduli, comune a tutte le
user story (build indipendente, env_file, riferimento alla rete condivisa) — senza ancora volumi,
restart policy o limiti di risorse, che sono specifici delle singole user story sotto.

**⚠️ CRITICAL**: Nessuna user story può essere validata prima che questa fase sia completa.

- [X] T003 [P] Creare `ingestion/Dockerfile` (base `python:3.12-slim`, install
  `requirements.txt`, entrypoint `python -m src.bot`)
- [X] T004 [P] Creare `pipeline/Dockerfile` (base `python:3.12-slim`, install
  `requirements.txt`, entrypoint `python -m src.worker`)
- [X] T005 [P] Creare `core/Dockerfile` (base `python:3.12-slim`, multi-stage per compilare
  `numpy`, entrypoint `uvicorn src.main:app --host 0.0.0.0 --port 8000`)
- [X] T006 [P] Creare `graph/Dockerfile` (base `python:3.12-slim`, entrypoint
  `uvicorn src.main:app --host 0.0.0.0 --port 8001`)
- [X] T007 [P] Creare `companion/Dockerfile` (base `python:3.12-slim`, entrypoint
  `uvicorn src.main:app --host 0.0.0.0 --port 8002`)
- [X] T008 [P] Creare `ingestion/docker-compose.yml` minimo (build, container_name, env_file,
  rete esterna `second-brain-net`, nessuna porta) secondo `contracts/compose-schema.md`
- [X] T009 [P] Creare `pipeline/docker-compose.yml` minimo (stesse chiavi di T008, nessuna porta)
- [X] T010 [P] Creare `core/docker-compose.yml` minimo (stesse chiavi di T008 + porta `8000`)
- [X] T011 [P] Creare `graph/docker-compose.yml` minimo (stesse chiavi di T008 + porta `8001`)
- [X] T012 [P] Creare `companion/docker-compose.yml` minimo (stesse chiavi di T008 + porta `8002`)
- [ ] T013 Validare staticamente i 5 file con `docker compose config` (nessun errore di sintassi,
  contracts/compose-schema.md)

**Checkpoint**: Ogni modulo è containerizzabile e collegabile alla rete condivisa — le user story
possono ora procedere.

---

## Phase 3: User Story 1 - Aggiornare un modulo senza toccare gli altri (Priority: P1) 🎯 MVP

**Goal**: Ricostruire/riavviare un singolo modulo senza fermare gli altri quattro.

**Independent Test**: Con tutti e 5 i moduli attivi, ricostruire solo `core` e verificare che gli
altri restino `Up` e raggiungibili per tutta l'operazione.

### Implementation for User Story 1

- [X] T014 [US1] Aggiungere i bind mount di `core/docker-compose.yml` verso
  `/srv/second-brain/data/core` e `/srv/second-brain/models-cache/core` (data-model.md)
- [X] T015 [US1] Aggiungere il bind mount di `graph/docker-compose.yml` verso
  `/srv/second-brain/data/graph` (data-model.md)
- [X] T016 [US1] Aggiungere il bind mount di `pipeline/docker-compose.yml` verso
  `/srv/second-brain/models-cache/pipeline` (data-model.md)
- [ ] T017 [US1] Avviare i 5 moduli con `docker compose up -d --build`, uno alla volta, secondo
  `quickstart.md` §1-3
- [ ] T018 [US1] Verificare la raggiungibilità reciproca per nome servizio da `companion` verso
  `core` e `graph` (`quickstart.md` §4, FR-002)
- [ ] T019 [US1] Validare l'aggiornamento indipendente: ricostruire solo `core` e confermare che
  `ingestion`/`pipeline`/`graph`/`companion` restano `Up` senza riavvio (`quickstart.md` §5, SC-001)

**Checkpoint**: User Story 1 completa e verificabile in isolamento — è l'MVP di questa feature.

---

## Phase 4: User Story 2 - Ripartenza automatica dopo un riavvio del nodo (Priority: P2)

**Goal**: Tutti e 5 i moduli ripartono da soli dopo un riavvio del nodo/di Docker.

**Independent Test**: Riavviare il servizio Docker e verificare che tutti i container tornino
attivi senza comandi manuali.

### Implementation for User Story 2

- [X] T020 [P] [US2] Impostare `restart: unless-stopped` in `ingestion/docker-compose.yml`,
  `core/docker-compose.yml`, `graph/docker-compose.yml`, `companion/docker-compose.yml`
  (research.md)
- [X] T021 [US2] Impostare `restart: on-failure` in `pipeline/docker-compose.yml` (research.md)
- [ ] T022 [US2] Validare la ripartenza automatica: `sudo systemctl restart docker`, attendere,
  verificare tutti e 5 i container `Up` senza intervento manuale (`quickstart.md` §8, SC-002)

**Checkpoint**: User Story 1 e 2 funzionano entrambe in modo indipendente.

---

## Phase 5: User Story 3 - Un carico pesante su pipeline non degrada gli altri moduli (Priority: P3)

**Goal**: Limiti di CPU/RAM sul container `pipeline` impediscono che un carico di elaborazione
locale affami `core`/`graph`/`companion` sulle 4 CPU condivise.

**Independent Test**: Generare un carico CPU sostenuto in `pipeline` e verificare che i tempi di
risposta di `core`/`graph`/`companion` restino entro i budget già definiti nelle loro spec.

### Implementation for User Story 3

- [X] T023 [US3] Aggiungere `cpus:` e `mem_limit:` a `pipeline/docker-compose.yml` (research.md:
  non `deploy.resources.limits`, non affidabile fuori da swarm)
- [ ] T024 [US3] Verificare i limiti applicati con
  `docker inspect second-brain-pipeline --format '{{.HostConfig.NanoCpus}} {{.HostConfig.Memory}}'`
  (`quickstart.md` §7, FR-005)
- [ ] T025 [US3] Validare che un carico sostenuto in `pipeline` non faccia superare a
  `core`/`graph`/`companion` i budget di risposta già definiti nelle rispettive spec
  (`quickstart.md` §7, SC-004)

**Checkpoint**: Tutte e 3 le user story sono ora indipendentemente funzionanti.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Verifiche finali trasversali e aggiornamento della documentazione operativa.

- [ ] T026 [P] Verificare l'assenza di segreti in ciascuna delle 5 immagini con `docker history`
  (`quickstart.md` §9, SC-003)
- [ ] T027 [P] Validare la persistenza dei dati di `core` e `graph` ricreando i container
  (`quickstart.md` §6, SC-005)
- [X] T028 Riscrivere `DEPLOY.md` per descrivere il deploy Docker (sostituisce le istruzioni
  systemd su Raspberry Pi)
- [X] T029 Aggiornare `CHANGELOG.md` con la feature di deploy containerizzato

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: nessuna dipendenza — può iniziare subito
- **Foundational (Phase 2)**: dipende dal completamento di Setup — blocca tutte le user story
- **User Story 1 (Phase 3)**: dipende dal completamento di Foundational — nessuna dipendenza dalle
  altre story
- **User Story 2 (Phase 4)**: dipende da Foundational; indipendente da US1 (può girare in
  parallelo se si lavora su più moduli contemporaneamente)
- **User Story 3 (Phase 5)**: dipende da Foundational; indipendente da US1/US2
- **Polish (Phase 6)**: dipende dal completamento delle user story che si vogliono validare

### Parallel Opportunities

- Tutti i Dockerfile (T003-T007) e tutti i compose minimi (T008-T012) sono `[P]`: file diversi,
  nessuna dipendenza tra loro
- T020 (restart policy sui 4 moduli sempre attivi) è `[P]`: 4 file diversi
- T026/T027 in Polish sono `[P]`: verifiche indipendenti

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Completare Setup (Phase 1) + Foundational (Phase 2)
2. Completare User Story 1 (Phase 3)
3. **STOP e VALIDARE**: aggiornare `core` da solo, confermare che gli altri restano `Up`
4. Questo è già un deploy utilizzabile: sostituisce `DEPLOY.md`/systemd con lo stesso livello di
   indipendenza tra moduli, anche prima di aggiungere restart automatico e limiti di risorse

### Incremental Delivery

1. Setup + Foundational → i 5 moduli sono containerizzabili
2. + User Story 1 → aggiornamento indipendente per modulo (MVP)
3. + User Story 2 → ripartenza automatica dopo riavvio
4. + User Story 3 → isolamento di risorse sotto carico
5. + Polish → documentazione operativa aggiornata (`DEPLOY.md`, `CHANGELOG.md`)

---

## Notes

- Nessun task di test automatico: la validazione è tramite gli scenari manuali di
  `quickstart.md`, richiamati da ogni task di validazione sopra.
- I task T001/T002/T022/T024/T025 presuppongono l'host ZimaBlade reale (o un ambiente Docker
  equivalente) — non eseguibili a scopo di sola scrittura codice.
- Fermarsi al checkpoint di ogni fase per validare la story indipendentemente prima di procedere.
