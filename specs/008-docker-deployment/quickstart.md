# Quickstart: validare il deploy Docker su ZimaBlade

Guida per verificare che l'infrastruttura containerizzata funzioni end-to-end, secondo i criteri
di successo di `spec.md`. Presuppone Docker Engine + plugin Compose v2 già installati sull'host
(fuori scope, vedi Assumptions).

## 0. Prerequisiti

```bash
docker --version
docker compose version
mkdir -p /srv/second-brain/data/core /srv/second-brain/data/graph \
         /srv/second-brain/models-cache/core /srv/second-brain/models-cache/pipeline
```

## 1. Rete condivisa (una sola volta)

```bash
docker network create second-brain-net
```

## 2. File `.env` per modulo

Stesso contenuto già documentato in `DEPLOY.md` (whitelist utenti, token Bearer tra servizi,
utente mock di `companion`) — un file `.env` dentro ciascuna cartella modulo, mai committato.

## 3. Build + avvio, un modulo alla volta

```bash
cd core      && docker compose up -d --build
cd ../graph  && docker compose up -d --build
cd ../ingestion && docker compose up -d --build
cd ../pipeline  && docker compose up -d --build
cd ../companion && docker compose up -d --build
```

**Atteso**: ogni comando riguarda solo quel modulo; gli altri, se già avviati, non vengono toccati
(valida US1 / SC-001).

## 4. Raggiungibilità per nome servizio (FR-002)

```bash
docker exec second-brain-companion sh -c "wget -qO- http://core:8000/openapi.json | head -c 40"
docker exec second-brain-companion sh -c "wget -qO- http://graph:8001/openapi.json | head -c 40"
```

**Atteso**: risposta valida da entrambi, senza usare `localhost` né IP hardcoded.

## 5. Aggiornare un solo modulo senza fermare gli altri (US1)

```bash
# modifica core/src/..., poi:
cd core && docker compose up -d --build
docker ps --filter "name=second-brain-" --format "{{.Names}}: {{.Status}}"
```

**Atteso**: `second-brain-core` si ricrea; `ingestion`, `pipeline`, `graph`, `companion` restano
`Up` per tutta l'operazione, uptime non azzerato.

## 6. Persistenza dati alla ricreazione del container (SC-005)

```bash
docker compose -f core/docker-compose.yml down
docker compose -f core/docker-compose.yml up -d
curl -s -H "Authorization: Bearer $CORE_API_TOKEN" http://localhost:8000/api/events?limit=1
```

**Atteso**: gli eventi salvati prima del `down` sono ancora presenti dopo l'`up` (il bind mount su
`/srv/second-brain/data/core` sopravvive alla rimozione del container).

## 7. Limiti di risorse su `pipeline` (FR-005)

```bash
docker inspect second-brain-pipeline --format '{{.HostConfig.NanoCpus}} {{.HostConfig.Memory}}'
```

**Atteso**: valori diversi da `0`, coerenti con quanto dichiarato in `pipeline/docker-compose.yml`.

## 8. Ripartenza dopo riavvio Docker (US2 / SC-002)

```bash
sudo systemctl restart docker
sleep 60
docker ps --filter "name=second-brain-" --format "{{.Names}}: {{.Status}}"
```

**Atteso**: tutti e cinque i container tornano `Up` senza comandi manuali oltre l'attesa.

## 9. Nessun segreto nell'immagine (SC-003)

```bash
docker history second-brain-core-core --no-trunc | grep -i -E "token|password|secret" || echo "OK: nessun match"
```

**Atteso**: `OK: nessun match` per ciascuna delle cinque immagini.
