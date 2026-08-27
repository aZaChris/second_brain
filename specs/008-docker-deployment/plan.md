# Implementation Plan: Infrastruttura di Deploy Containerizzata su ZimaBlade

**Branch**: `zimaboard` | **Date**: 2026-08-25 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/008-docker-deployment/spec.md`

## Summary

Sostituire il deploy systemd su Raspberry Pi (`DEPLOY.md`) con un deploy containerizzato su
ZimaBlade: un Dockerfile + un `docker-compose.yml` indipendente per ciascuno dei cinque moduli
(`ingestion`, `pipeline`, `core`, `graph`, `companion`), collegati a una rete Docker condivisa
creata una sola volta fuori da ogni singolo compose, con volumi bind-mount su storage SATA per i
dati persistenti e la cache dei pesi dei modelli locali, restart policy per ruolo e limiti di
CPU/RAM sul container `pipeline`.

## Technical Context

**Language/Version**: Nessun cambiamento applicativo — Python 3.11+ per tutti i moduli (invariato).
Solo Dockerfile (sintassi Docker) e file di composizione (YAML, Compose Spec v2) come nuovi
artefatti.

**Primary Dependencies**: Docker Engine + plugin Compose v2 sull'host. Nessuna nuova dipendenza
Python nei moduli per questa feature (i modelli locali di embedding/STT/captioning sono fuori
scope, arriveranno con le prossime due feature).

**Storage**: Bind mount su directory esplicite sotto lo storage SATA dell'host (non volumi Docker
gestiti): un mount per i dati persistenti di `core`/`graph` (i loro file DB), uno per la cache dei
pesi dei modelli locali che `core` e `pipeline` useranno in futuro. Bind mount invece di volumi
Docker perché più semplice da ispezionare/backuppare con strumenti standard (`cp`, `rsync`) per un
singolo operatore — stesso principio già seguito da `DB_PATH` come variabile d'ambiente esplicita.

**Testing**: Nessun framework di test automatico applicabile a un artefatto di infrastruttura;
validazione tramite `quickstart.md` (build + up di ogni modulo, verifica raggiungibilità di rete
per nome servizio, verifica persistenza dati alla ricreazione di un container, verifica dei limiti
di risorse). I contract/unit test esistenti di ciascun modulo restano invariati e continuano a
girare in-process (FastAPI `TestClient`), indipendentemente da Docker.

**Target Platform**: Linux x86_64 su host singolo ZimaBlade (Intel Celeron quad-core, fino a 16GB
RAM, storage SATA). Nessun requisito ARM da mantenere.

**Project Type**: Infrastruttura di deploy (non un modulo applicativo) — un Dockerfile + un
docker-compose.yml per ciascun modulo esistente, nessuna nuova struttura `src/`/`tests/`.

**Performance Goals**: Riavvio completo della pila entro pochi minuti dopo un riavvio host (SC-002);
i tempi di risposta di `core`/`graph`/`companion` restano entro i budget già definiti nelle loro
spec anche sotto carico sostenuto di `pipeline` (SC-004).

**Constraints**: Nessuna esposizione pubblica delle porte (stesso perimetro di fiducia di oggi);
nessun segreto nell'immagine Docker o nel repository (FR-006, SC-003); nessuna GPU assunta
disponibile (Vincoli Tecnici della constitution); limiti di CPU/RAM sul container `pipeline`
(FR-005).

**Scale/Scope**: 5 moduli, host singolo, uso personale — nessun orchestratore multi-nodo
(Swarm/Kubernetes) necessario a questo volume.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **I. Privacy-First** — PASS. Nessun nuovo storage di dati utente: i volumi bind-mount persistono
  solo ciò che i moduli già salvano oggi (DB SQLite) più la cache dei pesi dei modelli locali (non
  dati utente). Nessun segreto nell'immagine (FR-006).
- **II. Modularità** — PASS, rinforzata. Dockerfile e compose indipendenti per modulo (FR-001,
  FR-007): un modulo si costruisce/avvia/ferma senza toccare gli altri, comunicazione solo tramite
  le interfacce di `API_CONTRACT.md` attraverso la rete Docker condivisa (FR-002) — nessuna
  conoscenza dei dettagli interni altrui.
- **III. API testabili indipendentemente** — PASS. I contract/unit test di ciascun modulo restano
  eseguibili in-process con `TestClient`, senza richiedere i container Docker in esecuzione: Docker
  cambia solo come il modulo gira in produzione, non come si testa.
- **IV. Modelli locali preferiti per compiti CPU-compatibili** — N/A diretto: questa feature non
  sceglie modelli, prepara solo l'infrastruttura (volume cache dei pesi, limiti di risorse su
  `pipeline`) che le prossime due feature (embedding locale in `core`, STT/captioning locale in
  `pipeline`) useranno.
- **Vincoli Tecnici** — PASS. Containerizzazione su nodo unico ZimaBlade con limiti di CPU/RAM per
  container (FR-005), nessuna GPU assunta disponibile, retry/timeout di rete verso servizi esterni
  o altri moduli restano quelli già implementati nel codice applicativo (non toccati qui).

Nessuna violazione: tabella "Complexity Tracking" non necessaria.

## Project Structure

### Documentation (this feature)

```text
specs/008-docker-deployment/
├── plan.md              # Questo file
├── research.md          # Fase 0
├── data-model.md         # Fase 1
├── quickstart.md         # Fase 1
├── contracts/            # Fase 1
└── tasks.md              # Fase 2 (da /speckit-tasks, non da questo comando)
```

### Source Code (repository root)

```text
ingestion/
├── Dockerfile
└── docker-compose.yml

pipeline/
├── Dockerfile
└── docker-compose.yml

core/
├── Dockerfile
└── docker-compose.yml

graph/
├── Dockerfile
└── docker-compose.yml

companion/
├── Dockerfile
└── docker-compose.yml

DEPLOY.md            # Riscritto per il deploy Docker (sostituisce le istruzioni systemd)
```

**Structure Decision**: Un Dockerfile + un docker-compose.yml dentro la cartella di ciascun modulo
esistente (`ingestion/`, `pipeline/`, `core/`, `graph/`, `companion/`), coerente con la struttura
già modulare del monorepo — nessuna nuova cartella di primo livello per l'infrastruttura, ogni
modulo resta autosufficiente anche nel proprio deploy.

## Complexity Tracking

> Nessuna violazione del Constitution Check: tabella vuota per questa feature.
