# Data Model: Infrastruttura di Deploy Containerizzata su ZimaBlade

Non è un modulo applicativo, quindi non ci sono entità dati nel senso tradizionale (righe di DB).
Le "entità" di questa feature sono le risorse di deploy che i cinque `docker-compose.yml`
dichiarano e condividono.

## Rete Docker condivisa

| Campo | Valore |
|---|---|
| Nome | `second-brain-net` |
| Tipo | bridge, creata una sola volta fuori da ogni compose (`external: true` in ciascun file) |
| Chi la usa | tutti e 5 i moduli |
| Come si raggiungono i moduli | DNS interno Docker per nome servizio (es. `core`, `graph`) |

## Volumi bind-mount

| Volume host | Montato in | Contenuto | Chi scrive | Chi legge |
|---|---|---|---|---|
| `/srv/second-brain/data/core` | `core:/data` | DB SQLite/Postgres eventi + preferenze | `core` | `core` |
| `/srv/second-brain/data/graph` | `graph:/data` | DB SQLite nodi + relazioni | `graph` | `graph` |
| `/srv/second-brain/models-cache/core` | `core:/models` | Pesi del modello locale di embedding | `core` (al primo avvio) | `core` |
| `/srv/second-brain/models-cache/pipeline` | `pipeline:/models` | Pesi dei modelli locali STT/captioning | `pipeline` (al primo avvio) | `pipeline` |

I path dei DB (`DB_PATH`) e dei modelli restano configurabili via variabile d'ambiente come oggi;
cambiano solo i valori di default per puntare dentro il container ai mount sopra.

## Servizi (uno per modulo)

| Servizio | Immagine base | Porta pubblicata su host | Restart policy | Limiti risorse | Volumi |
|---|---|---|---|---|---|
| `ingestion` | `python:3.12-slim` | nessuna (bot, no server) | `unless-stopped` | nessuno | nessuno |
| `pipeline` | `python:3.12-slim` | nessuna (worker) | `on-failure` | `cpus`, `mem_limit` (FR-005) | `models-cache/pipeline` |
| `core` | `python:3.12-slim` | `8000` (solo rete locale) | `unless-stopped` | nessuno | `data/core`, `models-cache/core` |
| `graph` | `python:3.12-slim` | `8001` (solo rete locale) | `unless-stopped` | nessuno | `data/graph` |
| `companion` | `python:3.12-slim` | `8002` (solo rete locale) | `unless-stopped` | nessuno | nessuno |

Nessuna porta esposta oltre la rete locale dell'host (stesso perimetro di fiducia di oggi,
Assumption della spec).
