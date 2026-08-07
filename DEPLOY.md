# Deploy su Raspberry Pi 4B (tutto lo stack: ingestion + pipeline + core + graph + companion)

Girano tutti sullo stesso dispositivo, comunicano su `localhost`.

## Tre filtri di accesso diversi, da trattare diversamente

Il sistema ha tre controlli di accesso indipendenti, con scopo e rigore diversi:

- **Whitelist utenti** (`AUTHORIZED_USER_IDS` su `ingestion`): filtro di *prodotto*, decide
  quale account Telegram può scrivere al bot. Non è un segreto — è solo il tuo user id
  Telegram — ma va comunque tenuto corretto: un id sbagliato o dimenticato lascia fuori te
  stesso o lascia dentro chi non deve esserci.
- **Token Bearer tra servizi** (`CORE_API_TOKEN`, `GRAPH_API_TOKEN`): filtro di *sicurezza*
  service-to-service, protegge le API interne da chiunque riesca a raggiungere
  `localhost:8000`/`8001` sulla rete locale. Vanno generati come segreti veri (random, non
  "test-token" o simili), mai committati, e ruotati se sospetti siano trapelati. `core`/`graph`
  rispondono `401` a chi non li presenta correttamente — è già implementato, qui serve solo
  generarli bene.
- **Utente mock di `companion`** (`COMPANION_USERNAME`/`COMPANION_PASSWORD`): filtro di
  *sicurezza* ma per un umano nel browser (HTTP Basic), non tra servizi — stessa serietà dei
  token sopra (segreto vero, random, mai committato), diverso solo perché lo usi tu a mano
  quando apri `companion` invece che un altro modulo in automatico. Non è un sistema di account
  vero: una sola coppia utente/password, va bene solo finché `companion` resta sulla rete
  locale (vedi `specs/004-companion-app/spec.md`).

```bash
# genera un token/password robusto per ciascuno dei segreti sopra (tutti diversi tra loro)
python3 -c "import secrets; print(secrets.token_hex(32))"
```

## 1. Prerequisiti

```bash
python3 --version   # serve 3.11+ (Raspberry Pi OS Bookworm ce l'ha già)
git clone https://github.com/aZaChris/second_brain.git
cd second_brain
```

## 2. Setup dei cinque moduli

```bash
for m in ingestion pipeline core graph companion; do
  (cd "$m" && python3 -m venv .venv && .venv/bin/pip install -r requirements.txt)
done
```

## 3. Variabili d'ambiente

Crea un file `.env` locale per servizio (o esportale in una sessione/unit `systemd`, mai in
git — `.gitignore` esclude già `.env`).

**`core/.env`**
```bash
DB_PATH=/home/pi/second_brain/core/core.db
EMBEDDING_API_URL=<endpoint del provider di embedding scelto>
EMBEDDING_API_TOKEN=<token del provider>
CORE_API_TOKEN=<generato sopra, segreto vero>
```

**`graph/.env`**
```bash
DB_PATH=/home/pi/second_brain/graph/graph.db
GRAPH_API_TOKEN=<generato sopra, segreto vero e diverso da CORE_API_TOKEN>
```

**`ingestion/.env`**
```bash
BOT_TOKEN=<token da @BotFather>
AUTHORIZED_USER_IDS=<tuo user id Telegram, whitelist di prodotto>
CORE_EVENTS_URL=http://localhost:8000/api/events
CORE_API_TOKEN=<STESSO valore di core/.env — ingestion deve autenticarsi a core>
```

**`pipeline/.env`**
```bash
CORE_API_URL=http://localhost:8000
CORE_API_TOKEN=<STESSO valore di core/.env — pipeline deve autenticarsi a core>
STT_API_URL=<endpoint del servizio esterno di trascrizione scelto>
STT_API_TOKEN=<token del servizio>
CAPTIONING_API_URL=<endpoint del servizio esterno di captioning scelto>
CAPTIONING_API_TOKEN=<token del servizio>
POLL_INTERVAL_SECONDS=30
```

**`companion/.env`**
```bash
GRAPH_API_URL=http://localhost:8001
GRAPH_API_TOKEN=<STESSO valore di graph/.env — companion deve autenticarsi a graph>
CORE_API_URL=http://localhost:8000
CORE_API_TOKEN=<STESSO valore di core/.env — companion deve autenticarsi a core>
COMPANION_USERNAME=<scegli un nome utente>
COMPANION_PASSWORD=<generato sopra, segreto vero — è l'utente mock per il browser>
```

> Note aperte: `core/src/embedding.py`, `pipeline/src/transcription.py` e
> `pipeline/src/captioning.py` si aspettano tutti una risposta `{"text": ...}` (o
> `{"embedding": ...}` per l'embedding) dal rispettivo provider esterno. Se i provider scelti
> (es. OpenAI, Whisper) rispondono con una forma diversa, vanno adattati quei file prima del
> primo avvio reale (vedi i `research.md` di `specs/002-core-similarity-engine/` e
> `specs/006-pipeline-transcription-captioning/`).

## 4. Avvio manuale (per il primo test)

```bash
cd core      && set -a && source .env && set +a && .venv/bin/uvicorn src.main:app --port 8000 &
cd graph     && set -a && source .env && set +a && .venv/bin/uvicorn src.main:app --port 8001 &
cd companion && set -a && source .env && set +a && .venv/bin/uvicorn src.main:app --port 8002 &
cd ingestion && set -a && source .env && set +a && .venv/bin/python -m src.bot &
cd pipeline  && set -a && source .env && set +a && .venv/bin/python -m src.worker &
```

## 5. Avvio persistente con systemd (consigliato per l'uso reale)

Cinque unit separate, una per modulo, così ognuna riparte da sola dopo un riavvio o un crash.

`/etc/systemd/system/second-brain-core.service`:
```ini
[Unit]
Description=Second Brain - core
After=network.target

[Service]
User=pi
WorkingDirectory=/home/pi/second_brain/core
EnvironmentFile=/home/pi/second_brain/core/.env
ExecStart=/home/pi/second_brain/core/.venv/bin/uvicorn src.main:app --host 0.0.0.0 --port 8000
Restart=on-failure

[Install]
WantedBy=multi-user.target
```

Stessa struttura per:

- `second-brain-graph.service` (porta 8001, `WorkingDirectory` su `graph/`)
- `second-brain-companion.service` (porta 8002, `WorkingDirectory` su `companion/`)
- `second-brain-ingestion.service` (`ExecStart=.../python -m src.bot`, nessuna porta)
- `second-brain-pipeline.service` (`ExecStart=.../python -m src.worker`, nessuna porta)

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now second-brain-core second-brain-graph second-brain-companion \
  second-brain-ingestion second-brain-pipeline
sudo systemctl status second-brain-core second-brain-graph second-brain-companion \
  second-brain-ingestion second-brain-pipeline
```

`core` e `graph` vanno avviati prima degli altri in ordine logico, ma non è bloccante:
`ingestion` e `pipeline` hanno già retry con backoff (`specs/001-ingestion-bot/`,
`specs/006-pipeline-transcription-captioning/`) se `core` non è ancora su.
