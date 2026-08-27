# Implementation Plan: STT e Captioning Locali in Pipeline

**Branch**: `zimaboard` | **Date**: 2026-08-25 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/010-stt-captioning-locale/spec.md`

## Summary

Sostituire in `pipeline/src/transcription.py` e `pipeline/src/captioning.py` le chiamate HTTP ai
servizi esterni con due modelli locali eseguiti in-process: `faster-whisper` (STT) e un modello di
captioning compatto via `transformers` (BLIP-base), entrambi caricati una sola volta all'avvio del
processo worker, pesi cache su `/models` (volume `models-cache/pipeline`, già predisposto da
`008-docker-deployment`). Ogni servizio esterno resta disponibile come modalità alternativa
configurabile indipendentemente per audio e per immagini.

## Technical Context

**Language/Version**: Python 3.11+ (invariato).

**Primary Dependencies**: `faster-whisper` (STT, CTranslate2 — CPU-only per design, non porta
dipendenze CUDA come `torch`); `transformers` + `torch` (captioning, BLIP-base — stessa
precauzione CPU-only già imparata in `009-embedding-locale-core`: `torch` va installato
esplicitamente dalla build CPU prima del resto). `httpx` resta per la modalità esterna opzionale.

**Storage**: Nessun cambiamento allo schema. I pesi dei modelli vivono su `/models/stt` e
`/models/captioning` (sottocartelle del bind mount `models-cache/pipeline` già definito).

**Testing**: `pytest`, esistenti in `pipeline/tests/`. I test di `transcription.py`/`captioning.py`
che oggi mockano la chiamata HTTP vanno riscritti per i modelli locali (stesso approccio di
`test_embedding.py` in `009-embedding-locale-core`: mock a livello di libreria, nessun download
reale nei test).

**Target Platform**: Linux x86_64, container `pipeline` su ZimaBlade — CPU-only, entro i limiti
`cpus`/`mem_limit` già assegnati dal `docker-compose.yml` di `008-docker-deployment`.

**Project Type**: Servizio esistente (`pipeline`, worker senza server HTTP proprio), nessuna
nuova struttura di progetto.

**Performance Goals**: Trascrizione/captioning di un file tipico entro il budget già garantito da
`006-pipeline-transcription-captioning` (pochi minuti dalla ricezione — SC-002 di questa spec).

**Constraints**: Nessuna chiamata di rete esterna per la modalità locale (default, SC-001);
nessun contenuto di file in log verso l'esterno (SC-004); nessun ri-download dei pesi se già in
cache (SC-003); nessuna GPU assunta disponibile; entrambi i modelli locali (STT + captioning)
devono restare entro i limiti di risorse già assegnati al container `pipeline` — nessun limite
aggiuntivo introdotto da questa feature.

**Scale/Scope**: Stesso volume di `006-pipeline-transcription-captioning` (1 utente, note vocali e
immagini occasionali) — questa feature cambia solo come vengono elaborate, non la scala.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **I. Privacy-First** — PASS, rinforzato. Contenuto audio/immagine non lascia più il nodo per
  essere processato da terzi (SC-001, SC-004).
- **II. Modularità** — PASS. Cambiamento confinato a `pipeline/src/transcription.py`,
  `pipeline/src/captioning.py`, `pipeline/src/config.py`, `pipeline/src/worker.py` — nessun altro
  modulo toccato.
- **III. API testabili indipendentemente** — PASS. Nessuna API HTTP esposta da `pipeline` (è un
  worker): i contract test degli altri moduli non sono impattati. I unit test di
  `transcription.py`/`captioning.py` vanno riscritti per i nuovi meccanismi interni.
- **IV. Modelli locali preferiti per compiti CPU-compatibili** — PASS, implementazione diretta del
  principio per STT e captioning.
- **Vincoli Tecnici** — PASS. Inferenza CPU-only per entrambi i modelli (nessuna GPU assunta);
  `pipeline` ha già `cpus`/`mem_limit` da `008-docker-deployment` — nessuna modifica a quei limiti
  richiesta da questa feature, solo verificare che entrambi i modelli ci stiano dentro (task di
  validazione, non una modifica al `docker-compose.yml`).

Nessuna violazione bloccante: tabella "Complexity Tracking" non necessaria.

## Project Structure

### Documentation (this feature)

```text
specs/010-stt-captioning-locale/
├── plan.md
├── research.md
├── data-model.md
├── contracts/
└── quickstart.md
```

### Source Code (repository root)

```text
pipeline/
├── requirements.txt          # + faster-whisper, transformers, torch (CPU-only)
├── src/
│   ├── transcription.py       # riscritto: faster-whisper in-process, fallback esterno opzionale
│   ├── captioning.py          # riscritto: BLIP-base in-process, fallback esterno opzionale
│   ├── config.py              # + STT_MODE/CAPTIONING_MODE, path cache, nomi modello
│   └── worker.py               # preload() dei 2 modelli in main() prima del loop; 2 punti di
│                                #   chiamata adattati (passano config)
└── tests/
    └── unit/                   # test di transcription.py/captioning.py riscritti
```

**Structure Decision**: Nessuna nuova cartella — il cambiamento resta dentro `pipeline/`, coerente
con la modularità già esistente. Nessun impatto su `ingestion`, `core`, `graph`, `companion`.

## Complexity Tracking

> Nessuna violazione del Constitution Check: tabella vuota per questa feature.
