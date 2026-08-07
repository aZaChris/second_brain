# Implementation Plan: Trascrizione Audio e Captioning Immagini (Pipeline)

**Branch**: `006-pipeline-transcription-captioning` | **Date**: 2026-08-07 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/006-pipeline-transcription-captioning/spec.md`

## Summary

Processo di background (nessun server HTTP esposto, come `ingestion`) che a intervalli
regolari interroga `GET /api/events/pending` su `core` (`007-core-pending-events`), scarica il
file referenziato, lo trascrive (audio) o descrive (immagine) tramite servizi esterni, e invia
il risultato con `PATCH /api/events/{event_id}` (`API_CONTRACT.md` sezione 2). Nessun nuovo
endpoint necessario per segnalare un fallimento definitivo (file irraggiungibile o servizio
esterno esaurito dopo i retry): si usa lo stesso `PATCH` con un testo segnaposto riconoscibile,
così l'evento non resta bloccato (SC-004) senza introdurre un meccanismo nuovo nel contratto.

## Technical Context

**Language/Version**: Python 3.11+ (stesso stack degli altri moduli).

**Primary Dependencies**: `httpx` (chiamate a `core`, download del file, chiamate ai servizi
esterni di STT/captioning) — nessuna nuova dipendenza oltre a quella già usata altrove nel
monorepo.

**Storage**: N/A — `pipeline` non persiste nulla di proprio; `core` è l'unica fonte di verità su
cosa è in attesa o già elaborato (`007-core-pending-events`).

**Testing**: `pytest`, con `core`/servizi esterni mockati (stesso approccio di `ingestion`).

**Target Platform**: Linux, nessun requisito hardware specifico — nessun modello pesante
locale, la trascrizione/captioning è delegata a servizi esterni (principio IV).

**Project Type**: worker in background (loop di polling), nessuna API propria esposta — stessa
forma di `ingestion`.

**Performance Goals**: trascrizione/descrizione completata entro pochi minuti (SC-001, SC-002)
in condizioni normali — dominato dalla latenza dei servizi esterni, non da `pipeline` stessa.

**Constraints**: retry con backoff sia sul download del file sia sulle chiamate ai servizi
esterni; dopo i retry, un fallimento definitivo viene comunque comunicato a `core` (via `PATCH`
con testo segnaposto), mai lasciato in sospeso indefinitamente (SC-004).

**Scale/Scope**: basso volume, un solo processo di `pipeline` attivo alla volta (stessa
assunzione di `007-core-pending-events`).

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **I. Privacy-First** — PASS. Il file audio/immagine viene scaricato solo temporaneamente per
  l'elaborazione (in memoria, non persistito su disco da `pipeline`); solo il testo risultante
  viene inviato a `core`.
- **II. Modularità** — PASS. `pipeline` vive in `pipeline/`, comunica con `core` solo tramite
  `GET /api/events/pending` e `PATCH /api/events/{event_id}` del contratto.
- **III. API testabili indipendentemente** — PASS. Client verso `core` e verso i servizi
  esterni sono entrambi mockabili nei test, nessuna dipendenza reale richiesta per testare la
  logica di `pipeline`.
- **IV. Servizi esterni preferiti a modelli locali pesanti** — PASS. Trascrizione e captioning
  sono delegati a servizi esterni, nessun modello STT/vision eseguito localmente.
- **Vincoli Tecnici** — PASS. Nessun requisito hardware specifico; retry con backoff copre la
  connettività non garantita, sia verso `core` sia verso i servizi esterni.

Nessuna violazione: tabella "Complexity Tracking" non necessaria.

## Project Structure

### Documentation (this feature)

```text
specs/006-pipeline-transcription-captioning/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
└── tasks.md
```

### Source Code (repository root)

```text
pipeline/
├── src/
│   ├── config.py           # CORE_API_URL, CORE_API_TOKEN, STT/captioning URL+token, poll interval
│   ├── core_client.py        # get_pending(types, limit), patch_event(event_id, normalized_text, meta)
│   ├── media.py                # download_media(media_url) -> bytes, con retry/backoff
│   ├── transcription.py         # transcribe(audio_bytes) -> str, servizio esterno STT
│   ├── captioning.py             # caption(image_bytes) -> str, servizio esterno di captioning
│   └── worker.py                  # loop principale: poll -> scarica -> trascrivi/descrivi -> PATCH
└── tests/
    ├── unit/                       # media, transcription, captioning, worker (tutto mockato)
    └── contract/                    # payload PATCH conforme ad API_CONTRACT.md
```

**Structure Decision**: nuovo modulo `pipeline/`, stessa struttura piatta degli altri moduli —
worker senza server HTTP proprio, come `ingestion`.

## Complexity Tracking

> Nessuna violazione del Constitution Check: tabella vuota per questa feature.
