# Deploy su ZimaBlade (Intel Celeron quad-core x86, 16GB RAM, storage SATA)

Ogni modulo (`ingestion`, `pipeline`, `core`, `graph`, `companion`) gira nel proprio container
Docker, con il proprio `Dockerfile` e il proprio `docker-compose.yml` indipendente dentro la
cartella del modulo — nessun compose unico: ogni modulo si costruisce, avvia, ferma e aggiorna
senza toccare gli altri (`specs/008-docker-deployment/`). I moduli comunicano tra loro per nome di
servizio su una rete Docker condivisa, non più via `localhost:porta`.

## Tre filtri di accesso diversi, da trattare diversamente

Il sistema ha tre controlli di accesso indipendenti, con scopo e rigore diversi (invariato rispetto
al deploy precedente):

- **Whitelist utenti** (`AUTHORIZED_USER_IDS` su `ingestion`): filtro di *prodotto*, decide
  quale account Telegram può scrivere al bot. Non è un segreto — è solo il tuo user id
  Telegram — ma va comunque tenuto corretto: un id sbagliato o dimenticato lascia fuori te
  stesso o lascia dentro chi non deve esserci.
- **Token Bearer tra servizi** (`CORE_API_TOKEN`, `GRAPH_API_TOKEN`): filtro di *sicurezza*
  service-to-service, protegge le API interne da chiunque riesca a raggiungere i container sulla
  rete Docker condivisa o sulla rete locale. Vanno generati come segreti veri (random, non
  "test-token" o simili), mai committati, e ruotati se sospetti siano trapelati.
- **Utente mock di `companion`** (`COMPANION_USERNAME`/`COMPANION_PASSWORD`): filtro di
  *sicurezza* ma per un umano nel browser (HTTP Basic), stessa serietà dei token sopra (segreto
  vero, random, mai committato). Non è un sistema di account vero: una sola coppia
  utente/password, va bene solo finché `companion` resta sulla rete locale.

```bash
# genera un token/password robusto per ciascuno dei segreti sopra (tutti diversi tra loro)
python3 -c "import secrets; print(secrets.token_hex(32))"
```

## 1. Prerequisiti

```bash
docker --version         # Docker Engine
docker compose version   # plugin Compose v2
git clone https://github.com/aZaChris/second_brain.git
cd second_brain
```

## 2. Storage persistente su SATA

Creata una sola volta, fuori da ogni compose (`specs/008-docker-deployment/data-model.md`):

```bash
mkdir -p /srv/second-brain/data/core /srv/second-brain/data/graph \
         /srv/second-brain/models-cache/core /srv/second-brain/models-cache/pipeline
```

## 3. Rete Docker condivisa

Creata una sola volta, fuori da ogni compose — è così che i moduli si raggiungono per nome
servizio invece che con `localhost:porta`:

```bash
docker network create second-brain-net
```

## 4. Variabili d'ambiente

Un file `.env` per modulo, dentro la cartella del modulo (letto da `env_file:` nel suo
`docker-compose.yml`), mai in git — `.gitignore` esclude già `.env`.

**`core/.env`**
```bash
DB_PATH=/data/core.db
EMBEDDING_MODEL_CACHE=/models
CORE_API_TOKEN=<generato sopra, segreto vero>
```

**`graph/.env`**
```bash
DB_PATH=/data/graph.db
GRAPH_API_TOKEN=<generato sopra, segreto vero e diverso da CORE_API_TOKEN>
```

**`ingestion/.env`**
```bash
BOT_TOKEN=<token da @BotFather>
AUTHORIZED_USER_IDS=<tuo user id Telegram, whitelist di prodotto>
CORE_EVENTS_URL=http://core:8000/api/events
CORE_API_TOKEN=<STESSO valore di core/.env — ingestion deve autenticarsi a core>
```

**`pipeline/.env`**
```bash
CORE_API_URL=http://core:8000
CORE_API_TOKEN=<STESSO valore di core/.env — pipeline deve autenticarsi a core>
STT_MODEL_CACHE=/models/stt
CAPTIONING_MODEL_CACHE=/models/captioning
POLL_INTERVAL_SECONDS=30
```

**`companion/.env`**
```bash
GRAPH_API_URL=http://graph:8001
GRAPH_API_TOKEN=<STESSO valore di graph/.env — companion deve autenticarsi a graph>
CORE_API_URL=http://core:8000
CORE_API_TOKEN=<STESSO valore di core/.env — companion deve autenticarsi a core>
COMPANION_USERNAME=<scegli un nome utente>
COMPANION_PASSWORD=<generato sopra, segreto vero — è l'utente mock per il browser>
```

> Nota: `EMBEDDING_MODEL_CACHE` è il path dei pesi del modello locale di embedding
> (`009-embedding-locale-core`, implementata — `EMBEDDING_MODE=local` è il default, non serve
> impostarla esplicitamente; `EMBEDDING_MODEL_NAME` ha anch'essa un default sensato). Per tornare
> al servizio esterno: `EMBEDDING_MODE=external` + `EMBEDDING_API_URL`/`EMBEDDING_API_TOKEN` in
> `core/.env` (FR-005 di `009-embedding-locale-core`). Stesso schema per `pipeline`
> (`010-stt-captioning-locale`, implementata): `STT_MODE`/`CAPTIONING_MODE=local` sono il default
> (non serve impostarle), pesi cache in due sottocartelle dello stesso volume
> (`STT_MODEL_CACHE=/models/stt`, `CAPTIONING_MODEL_CACHE=/models/captioning`); per tornare a un
> servizio esterno, indipendentemente per audio o immagini: `STT_MODE=external` +
> `STT_API_URL`/`STT_API_TOKEN`, oppure `CAPTIONING_MODE=external` +
> `CAPTIONING_API_URL`/`CAPTIONING_API_TOKEN`, in `pipeline/.env` (FR-006 di
> `010-stt-captioning-locale`).

## 5. Build e avvio, un modulo alla volta

Nessun ordine bloccante: `ingestion` e `pipeline` hanno già retry con backoff se `core` non è
ancora su.

```bash
cd core      && docker compose up -d --build
cd ../graph  && docker compose up -d --build
cd ../ingestion && docker compose up -d --build
cd ../pipeline  && docker compose up -d --build
cd ../companion && docker compose up -d --build
```

## 6. Operazioni comuni

Aggiornare un singolo modulo (gli altri restano `Up`, invariati):

```bash
cd core && docker compose up -d --build
```

Fermare un singolo modulo:

```bash
cd core && docker compose stop
```

Log di un modulo:

```bash
cd core && docker compose logs -f
```

Stato di tutti i moduli:

```bash
docker ps --filter "name=second-brain-" --format "table {{.Names}}\t{{.Status}}"
```

## 7. Ripartenza automatica

`restart: unless-stopped` (API sempre attive e bot `ingestion`) e `restart: on-failure`
(worker `pipeline`) sono già nei rispettivi `docker-compose.yml` — dopo un riavvio del nodo o del
servizio Docker, tutti i moduli ripartono da soli senza intervento manuale, a meno che tu li abbia
fermati esplicitamente con `docker compose stop`.

## 8. Limiti di risorse

`pipeline` (unico carico CPU-bound pesante, inferenza dei modelli locali di STT/captioning) ha
`cpus`/`mem_limit` nel proprio `docker-compose.yml`, così un'elaborazione intensiva non riduce le
risorse disponibili a `core`/`graph`/`companion` sulle 4 CPU condivise del nodo. Valori di
partenza, da tarare con il carico reale (vedi commento nel file).

## 9. Validazione end-to-end

Guida passo-passo con i comandi esatti per verificare rete, persistenza dati, limiti di risorse e
ripartenza automatica: `specs/008-docker-deployment/quickstart.md`.
