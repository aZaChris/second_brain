# Deploy su Raspberry Pi 4B (tutto lo stack: ingestion + core + graph)

Girano tutti sullo stesso dispositivo, comunicano su `localhost`.

## Due filtri di accesso diversi, da trattare diversamente

Il sistema ha due controlli di accesso indipendenti, con scopo e rigore diversi:

- **Whitelist utenti** (`AUTHORIZED_USER_IDS` su `ingestion`): filtro di *prodotto*, decide
  quale account Telegram può scrivere al bot. Non è un segreto — è solo il tuo user id
  Telegram — ma va comunque tenuto corretto: un id sbagliato o dimenticato lascia fuori te
  stesso o lascia dentro chi non deve esserci.
- **Token Bearer tra servizi** (`CORE_API_TOKEN`, `GRAPH_API_TOKEN`): filtro di *sicurezza*,
  protegge le API interne da chiunque riesca a raggiungere `localhost:8000`/`8001` sulla rete
  locale. Vanno generati come segreti veri (random, non "test-token" o simili), mai committati,
  e ruotati se sospetti siano trapelati. `core`/`graph` rispondono `401` a chi non li presenta
  correttamente — è già implementato, qui serve solo generarli bene.

```bash
# genera un token robusto per CORE_API_TOKEN e uno per GRAPH_API_TOKEN (diversi tra loro)
python3 -c "import secrets; print(secrets.token_hex(32))"
```

## 1. Prerequisiti

```bash
python3 --version   # serve 3.11+ (Raspberry Pi OS Bookworm ce l'ha già)
git clone https://github.com/aZaChris/second_brain.git
cd second_brain
```

## 2. Setup dei tre moduli

```bash
for m in ingestion core graph; do
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

> Nota aperta: `core/src/embedding.py` si aspetta una risposta `{"embedding": [...]}` dal
> provider esterno. Se il provider scelto (es. OpenAI) risponde con una forma diversa, va
> adattato quel file prima del primo avvio reale (vedi `research.md` di
> `specs/002-core-similarity-engine/`).

## 4. Avvio manuale (per il primo test)

```bash
cd core   && set -a && source .env && set +a && .venv/bin/uvicorn src.main:app --port 8000 &
cd graph  && set -a && source .env && set +a && .venv/bin/uvicorn src.main:app --port 8001 &
cd ingestion && set -a && source .env && set +a && .venv/bin/python -m src.bot &
```

## 5. Avvio persistente con systemd (consigliato per l'uso reale)

Tre unit separate, una per modulo, così ognuna riparte da sola dopo un riavvio o un crash.

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

Stessa struttura per `second-brain-graph.service` (porta 8001, `WorkingDirectory` su `graph/`)
e `second-brain-ingestion.service` (`ExecStart=.../python -m src.bot`, nessuna porta).

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now second-brain-core second-brain-graph second-brain-ingestion
sudo systemctl status second-brain-core second-brain-graph second-brain-ingestion
```

`core` e `graph` vanno avviati prima di `ingestion` in ordine logico, ma non è bloccante:
`ingestion` ha già retry con backoff (`specs/001-ingestion-bot/`) se `core` non è ancora su.
