# Implementation Plan: Embedding Locale in Core

**Branch**: `zimaboard` | **Date**: 2026-08-25 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/009-embedding-locale-core/spec.md`

## Summary

Sostituire in `core/src/embedding.py` la chiamata HTTP al servizio esterno di embedding con un
modello `sentence-transformers` multilingue leggero eseguito in-process, caricato una sola volta
all'avvio del processo, con i pesi cache su `/models` (volume `models-cache/core` già predisposto
da `008-docker-deployment`). Il servizio esterno resta disponibile come modalità alternativa
configurabile (`EMBEDDING_MODE`), non attiva di default.

## Technical Context

**Language/Version**: Python 3.11+ (invariato).

**Primary Dependencies**: `sentence-transformers` (nuova, porta con sé `torch` CPU e
`transformers`) per l'inferenza locale; `httpx` resta per la modalità esterna opzionale (FR-005).

**Storage**: Nessun cambiamento allo schema SQLite. I pesi del modello (non dati applicativi)
vivono su `/models`, bind mount già definito da `008-docker-deployment`.

**Testing**: `pytest`, esistenti in `core/tests/`. I test di `embedding.py` che oggi mockano la
chiamata HTTP vanno riscritti per il modello locale (nessuna chiamata di rete da mockare più; si
verifica invece forma/dimensionalità del vettore prodotto e che nessun client HTTP venga
istanziato in modalità locale).

**Target Platform**: Linux x86_64, container `core` su ZimaBlade (Celeron quad-core, CPU-only,
nessuna GPU assunta — Vincoli Tecnici della constitution).

**Project Type**: Servizio web singolo esistente (`core`), nessuna nuova struttura di progetto.

**Performance Goals**: Generazione embedding di un testo tipico entro il budget già garantito da
`002-core-similarity-engine` (conferma collegamenti entro 2s, elaborazione in background — SC-002
di questa spec).

**Constraints**: Nessuna chiamata di rete esterna per la modalità locale (default, SC-001);
nessun testo utente in log verso l'esterno (SC-004); nessun ri-download dei pesi se già in cache
(SC-003); nessuna GPU assunta disponibile.

**Scale/Scope**: Stesso volume di `002-core-similarity-engine` (1 utente, migliaia di eventi) —
questa feature cambia solo come l'embedding viene calcolato, non la scala del sistema.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **I. Privacy-First** — PASS, rinforzato. Il testo dell'evento non lascia più il nodo per essere
  processato da terzi (SC-001, SC-004).
- **II. Modularità** — PASS. Cambiamento confinato a `core/src/embedding.py` +
  `core/src/config.py`; `similarity.py`/`insight.py` non richiedono modifiche (FR-002). I punti di
  chiamata in `api.py` richiedono un adattamento meccanico minimo (passare `config` invece dei
  singoli `api_url`/`api_token`) per supportare la modalità configurabile di FR-005 — non tocca
  altri moduli.
- **III. API testabili indipendentemente** — PASS. I contract test delle route HTTP di `core`
  restano invariati (stesso comportamento esterno); solo i unit test di `embedding.py` vanno
  riscritti per il nuovo meccanismo interno.
- **IV. Modelli locali preferiti per compiti CPU-compatibili** — PASS, questa feature è
  l'implementazione diretta del principio per l'embedding.
- **Vincoli Tecnici** — PASS. Inferenza CPU-only (nessuna GPU assunta). Nota non bloccante:
  l'inferenza locale consuma CPU sul nodo condiviso — `core` non ha oggi limiti di risorse propri
  (solo `pipeline` li ha, da `008-docker-deployment`); se la validazione di SC-002 mostrasse
  contesa di CPU con `graph`/`companion`, aggiungere `cpus`/`mem_limit` a
  `core/docker-compose.yml` è un follow-up naturale, non una violazione di questa feature.

Nessuna violazione bloccante: tabella "Complexity Tracking" non necessaria.

## Project Structure

### Documentation (this feature)

```text
specs/009-embedding-locale-core/
├── plan.md
├── research.md
├── data-model.md
├── contracts/
└── quickstart.md
```

### Source Code (repository root)

```text
core/
├── requirements.txt      # + sentence-transformers
├── src/
│   ├── embedding.py       # riscritto: modello locale in-process, fallback esterno opzionale
│   ├── config.py          # + EMBEDDING_MODE, EMBEDDING_MODEL_CACHE, EMBEDDING_MODEL_NAME
│   └── api.py              # 2 punti di chiamata a embed() adattati (passa config, non più
│                            #   api_url/api_token sciolti)
└── tests/
    └── unit/               # test di embedding.py riscritti per il modello locale
```

**Structure Decision**: Nessuna nuova cartella — il cambiamento resta dentro `core/`, coerente con
la modularità già esistente. Nessun impatto su `ingestion`, `pipeline`, `graph`, `companion`.

## Complexity Tracking

> Nessuna violazione del Constitution Check: tabella vuota per questa feature.
