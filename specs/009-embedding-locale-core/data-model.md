# Data Model: Embedding Locale in Core

Nessuna modifica allo schema SQLite (`storage.py` invariato). L'unica entità nuova è di
configurazione, non di dati persistenti applicativi.

## Configurazione (`core/src/config.py`)

| Campo | Tipo | Default | Note |
|---|---|---|---|
| `embedding_mode` | `"local" \| "external"` | `"local"` | FR-005 |
| `embedding_model_name` | `str` | `"paraphrase-multilingual-MiniLM-L12-v2"` | usato solo se `embedding_mode == "local"` |
| `embedding_model_cache` | `str` | (obbligatorio se locale) | path della cache pesi, es. `/models` |
| `embedding_api_url` | `str \| None` | `None` | obbligatorio solo se `embedding_mode == "external"` |
| `embedding_api_token` | `str \| None` | `None` | obbligatorio solo se `embedding_mode == "external"` |

`Config.from_env()` valida solo le variabili richieste dalla modalità effettivamente selezionata
(non richiede più `EMBEDDING_API_URL`/`EMBEDDING_API_TOKEN` quando `EMBEDDING_MODE=local`, che è
il default).

## Vettore di embedding (invariato nello storage)

Nessun cambio di schema: la colonna `events.embedding` (SQLite, testo JSON) continua a contenere
una lista di float. Cambia solo la dimensionalità tipica del vettore prodotto (384, dal modello
locale) rispetto a quella del provider esterno precedente — gestito da FR-006 (esclusione dal
confronto se dimensioni diverse, non un cambio di schema).
