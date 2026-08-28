# KB: README di `core`/`pipeline` proponevano variabili che avrebbero fatto crashare l'app

## Sintomo

`core/README.md` e `pipeline/README.md` mostravano nel blocco `## Setup` queste variabili come
se fossero necessarie:

- `core`: `EMBEDDING_API_URL`, `EMBEDDING_API_TOKEN`
- `pipeline`: `STT_API_URL`/`STT_API_TOKEN`, `CAPTIONING_API_URL`/`CAPTIONING_API_TOKEN`

Seguendo il README alla lettera, `Config.from_env()` avrebbe sollevato
`MissingConfigError: Variabile d'ambiente mancante: EMBEDDING_MODEL_CACHE` (e equivalenti per
`pipeline`) — non trovato eseguendo l'app, ma rileggendo `core/src/config.py`/
`pipeline/src/config.py` insieme ai README durante una revisione.

## Causa radice

`009-embedding-locale-core` e `010-stt-captioning-locale` hanno cambiato il **default** di
`EMBEDDING_MODE`/`STT_MODE`/`CAPTIONING_MODE` da `external` a `local` (Principio IV della
constitution v2.0.0, migrazione ZimaBlade). In modalità locale, `from_env()` richiede
`EMBEDDING_MODEL_CACHE`/`STT_MODEL_CACHE`/`CAPTIONING_MODEL_CACHE` e **non** richiede più le
variabili del servizio esterno. I README dei moduli erano stati scritti per l'architettura
pre-migrazione e non sono mai stati toccati quando 009/010 hanno cambiato il default — `DEPLOY.md`
sì (era già stato aggiornato), i README per-modulo no.

## Come l'abbiamo confermata

Letto `core/src/config.py`:

```python
if embedding_mode == "local":
    embedding_model_cache = _require_env("EMBEDDING_MODEL_CACHE")
    ...
else:
    embedding_api_url = _require_env("EMBEDDING_API_URL")
    ...
```

`embedding_mode` di default è `"local"` — il README invece proponeva solo le variabili del ramo
`else`.

## Risoluzione

Riscritti i blocchi `## Setup` per mostrare la modalità locale come default (variabile
`*_MODEL_CACHE`), con una nota esplicita subito dopo su come passare a `*_MODE=external` +
`*_API_URL`/`*_API_TOKEN` per chi vuole ancora un servizio esterno.

## Lezione per il futuro

Quando una feature cambia il **default** di una configurazione (non solo aggiunge un'opzione),
va cercato ogni punto della documentazione che mostra un esempio di configurazione — non solo
`DEPLOY.md`. I README per-modulo sono "istruzioni di setup" a tutti gli effetti, ma non sono
coperti da nessun test automatico: restano stantii in silenzio finché qualcuno non li rilegge o
non li segue alla lettera e si scontra con l'errore.

## Riferimenti

- `core/src/config.py`, `pipeline/src/config.py` (`from_env()`)
- `specs/009-embedding-locale-core/`, `specs/010-stt-captioning-locale/` (cambio di default)
- `DEPLOY.md` (era già coerente, unico documento non stantio)
