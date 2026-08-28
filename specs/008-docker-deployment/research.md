# Research: Infrastruttura di Deploy Containerizzata su ZimaBlade

Nessun `[NEEDS CLARIFICATION]` residuo: le decisioni sotto derivano dalla spec e dalle scelte già
confermate (compose separati per modulo, non un compose unico).

## Orchestrazione: compose separati vs unico

**Decision**: un `docker-compose.yml` indipendente per ciascun modulo, dentro la cartella del
modulo stesso.

**Rationale**: coerente con il Principio II (Modularità) già esistente — ogni modulo si
costruisce/avvia/ferma/aggiorna senza toccare gli altri (FR-001, FR-007, US1). Un compose unico
imporrebbe un unico ciclo di vita a tutti e cinque i moduli, regressione rispetto alle unit
`systemd` indipendenti di oggi.

**Alternatives considered**: un `docker-compose.yml` unico alla radice con tutti e cinque i
servizi — scartato inizialmente sull'assunto che perdesse l'indipendenza di ciclo di vita richiesta
da US1.

**Revisione post-implementazione**: assunto errato — `docker compose <cmd> <servizio>` (es. `up -d
--build core`, `stop core`, `logs -f core`) opera su un singolo servizio anche dentro un file
multi-servizio, quindi l'indipendenza di ciclo di vita (US1, FR-001, FR-007) non richiedeva file
separati. Su un deploy a nodo singolo/operatore singolo (ZimaBlade), il costo dei 5 file (rete
esterna da creare a mano, nessun `up` unico, chiavi ripetute 5 volte) non aveva contropartita.
Consolidato in un unico `docker-compose.yml` di root con 5 servizi; Dockerfile per modulo
invariati. Rete esterna sostituita dalla rete di default del progetto Compose (stesso risultato,
raggiungibilità per nome servizio, senza passo manuale). Vedi `DEPLOY.md` e
`quickstart.md` aggiornati di conseguenza.

## Comunicazione tra moduli: rete condivisa

**Decision originale (compose separati)**: una rete Docker bridge creata una sola volta fuori da
ogni compose (`docker network create second-brain-net`), referenziata in ciascun
`docker-compose.yml` come rete esterna (`external: true`) — necessaria perché con compose separati
la rete di default di ciascuno sarebbe isolata dalle altre.

**Stato attuale (dopo il consolidamento in un compose di root, vedi sopra)**: la rete di default
del progetto Compose è già condivisa da tutti e 5 i servizi dichiarati nello stesso file — nessuna
rete esterna da creare a mano. I moduli si raggiungono comunque per nome di servizio (es.
`http://core:8000`) invece che con `localhost:porta` (FR-002 invariato).

**Alternatives considered**: pubblicare le porte di ogni container sull'host e comunicare via
`localhost` come oggi — scartato, reintroduce l'accoppiamento a porte fisse sull'host che Docker
altrimenti eviterebbe, e non sfrutta il DNS interno di Docker già disponibile gratis con una rete
condivisa.

## Storage persistente: bind mount vs volumi Docker gestiti

**Decision**: bind mount su directory esplicite sotto lo storage SATA dell'host (es.
`/srv/second-brain/data/core`, `/srv/second-brain/data/graph`, `/srv/second-brain/models-cache`),
non volumi Docker gestiti (`docker volume create`).

**Rationale**: un bind mount è un percorso host ordinario — backup/ispezione con `cp`/`rsync`/`ls`
diretti, senza passare da `docker volume inspect` per trovare dove Docker l'ha messo. Per un
singolo operatore che gestisce tutto a mano, è la scelta più semplice da ragionare e da
backuppare (FR-003, SC-005).

**Alternatives considered**: volumi Docker gestiti — scartati, aggiungono un livello di
indirezione (`docker volume inspect` per trovare il path reale) senza un beneficio per un host
singolo non clusterizzato.

## Limiti di risorse sul container `pipeline`

**Decision**: limiti espressi con le chiavi top-level del Compose Spec (`cpus:`, `mem_limit:`)
nel `docker-compose.yml` di `pipeline`, non con la sezione `deploy.resources.limits`.

**Rationale**: `deploy.resources.limits` è pensato per Docker Swarm; con `docker compose up` in
modalità standalone (non swarm, il caso di un host singolo) il supporto è stato storicamente
inconsistente tra versioni del plugin Compose. `cpus:`/`mem_limit:` sono le chiavi legacy ma
supportate in modo affidabile da `docker compose up` in ogni versione recente del plugin v2,
indipendentemente da swarm — scelta più sicura per garantire che il limite sia davvero applicato
(FR-005), non solo dichiarato nel file.

**Alternatives considered**: `deploy.resources.limits` — scartato per il rischio concreto che
resti silenziosamente non applicato fuori da swarm, vanificando l'unico scopo del requisito.

## Immagine base

**Decision**: `python:3.12-slim` come immagine base per tutti e cinque i Dockerfile.

**Rationale**: tutti i moduli sono già Python 3.11+; un'unica famiglia di immagine base riduce la
superficie di manutenzione (una sola immagine da tenere aggiornata per patch di sicurezza) e la
variante `slim` mantiene le immagini piccole senza i tool di build non necessari a runtime — i
pacchetti che richiedono compilazione (es. `numpy` in `core`) restano installabili con un multi
stage Docker build senza portare in produzione il toolchain di compilazione.

**Alternatives considered**: immagine `alpine` — scartata, la libc musl introduce spesso problemi
di compatibilità con ruote precompilate di pacchetti scientifici come `numpy`, un problema
storicamente noto che non vale il risparmio di spazio per un host con storage SATA capiente.

## Restart policy per servizio

**Decision**: `restart: unless-stopped` per `ingestion`, `core`, `graph`, `companion` (processi
sempre attivi: bot/API); `restart: on-failure` per `pipeline` (worker che esegue un ciclo
poll-elabora-attendi, coerente con `worker.py` esistente).

**Rationale**: replica 1:1 il comportamento delle unit `systemd` già in uso (`Restart=on-failure`
per tutte oggi) con una sola differenza intenzionale: `unless-stopped` per i processi
sempre-attivi evita che un arresto esplicito dell'operatore (`docker compose stop`) venga
annullato da un riavvio automatico, comportamento non garantito da `on-failure` puro.

**Alternatives considered**: `restart: always` per tutti — scartato, riavvierebbe anche dopo uno
stop esplicito dell'operatore durante un aggiornamento (US1), interferendo con l'operazione
manuale che la User Story 1 richiede di poter fare in sicurezza.

## Secrets e configurazione

**Decision**: `env_file:` nel compose di ciascun modulo, puntato agli stessi file `.env` già
documentati in `DEPLOY.md` (uno per modulo, mai committati).

**Rationale**: nessun cambiamento nello schema di configurazione già esistente (`config.py` di
ciascun modulo legge da variabili d'ambiente) — Docker inietta le stesse variabili che oggi
`systemd` inietta con `EnvironmentFile=`, zero codice applicativo da toccare.

**Alternatives considered**: Docker secrets (`docker secret`) — scartato, richiede modalità swarm;
non necessario per un host singolo dove `env_file` con permessi di file ristretti offre già la
stessa garanzia pratica.
