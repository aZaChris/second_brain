# Data Model: STT e Captioning Locali in Pipeline

Nessuna modifica a uno schema dati persistente (`pipeline` non ha storage proprio). Le uniche
entità nuove sono di configurazione.

## Configurazione (`pipeline/src/config.py`)

| Campo | Tipo | Default | Note |
|---|---|---|---|
| `stt_mode` | `"local" \| "external"` | `"local"` | FR-006 |
| `stt_model_name` | `str` | `"base"` | modello `faster-whisper`, usato solo se locale |
| `stt_model_cache` | `str \| None` | (obbligatorio se locale) | es. `/models/stt` |
| `stt_api_url` / `stt_api_token` | `str \| None` | `None` | obbligatori solo se `stt_mode == "external"` |
| `captioning_mode` | `"local" \| "external"` | `"local"` | FR-006, indipendente da `stt_mode` |
| `captioning_model_name` | `str` | `"Salesforce/blip-image-captioning-base"` | usato solo se locale |
| `captioning_model_cache` | `str \| None` | (obbligatorio se locale) | es. `/models/captioning` |
| `captioning_api_url` / `captioning_api_token` | `str \| None` | `None` | obbligatori solo se `captioning_mode == "external"` |

`Config.from_env()` valida solo le variabili richieste dalla combinazione di modalità
effettivamente selezionata per ciascuna delle due capacità (indipendenti tra loro).

## Modelli locali (in memoria, non persistiti)

| Modello | Libreria | Pesi (cache) | Caricato da |
|---|---|---|---|
| STT (`base`, int8) | `faster-whisper` | `/models/stt` | `preload(config)` in `worker.main()` |
| Captioning (BLIP-base) | `transformers` | `/models/captioning` | `preload(config)` in `worker.main()` |

Nessun cambiamento al formato di `normalized_text` inviato a `core` via `PATCH
/api/events/{event_id}` (`API_CONTRACT.md` invariato) — resta testo semplice, indipendentemente
da quale modalità (locale/esterna) lo ha prodotto.
