# Implementation Plan: Bot Telegram di Ingestion

**Branch**: `001-ingestion-bot` | **Date**: 2026-08-07 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/001-ingestion-bot/spec.md`

## Summary

Bot Telegram che riceve messaggi testo/audio/immagine da utenti in whitelist, li normalizza in
un evento (`API_CONTRACT.md` → `POST /api/events`) e li inoltra sincronamente a `core` con retry
a backoff esponenziale, confermando la ricezione all'utente. Nessuno storage locale persistente
dei messaggi (privacy-first). Long polling verso l'API Telegram: evita di esporre un endpoint
pubblico dal Raspberry Pi dietro NAT.

## Technical Context

**Language/Version**: Python 3.11+

**Primary Dependencies**: `python-telegram-bot` (integrazione Telegram, long polling),
`httpx` (chiamata sincrona a `core`) — nessun broker/coda: volume basso, un solo bot; si
introduce una coda solo se il volume lo richiederà in futuro.

**Storage**: N/A — nessun dato persistito localmente oltre la durata dell'inoltro (principio
privacy-first della constitution).

**Testing**: `pytest`, con client HTTP verso `core` mockato per testare whitelist,
normalizzazione e retry in isolamento (principio "API testabili indipendentemente").

**Target Platform**: Linux (Raspberry Pi OS, ARM) in produzione; qualunque Linux/macOS in
sviluppo — nessuna dipendenza da GPU o hardware specifico.

**Project Type**: Servizio singolo, processo long-running (es. via systemd), non un progetto
web frontend+backend.

**Performance Goals**: Basso volume (uso personale/piccola whitelist, ordine di decine di
messaggi al giorno) — non è richiesto throughput elevato; conferma di ricezione entro 5s
(SC-001 dello spec).

**Constraints**: Footprint di CPU/RAM minimo per girare su Raspberry Pi; connettività di rete
non garantita al 100% → ogni chiamata verso `core` gestisce timeout e retry senza perdere
l'evento (vincolo tecnico della constitution).

**Scale/Scope**: 1–pochi utenti autorizzati (whitelist statica), nessuna scalabilità
multi-tenant richiesta in questa fase.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **I. Privacy-First** — PASS. Nessuno storage locale persistente dei messaggi; il contenuto
  vive solo in memoria per il tempo dell'inoltro. Nessun dato inviato a servizi esterni non
  necessari: l'unica destinazione è l'endpoint interno di `core`.
- **II. Modularità** — PASS. Il codice vive interamente in `ingestion/`; l'unico punto di
  contatto con altri moduli è `POST /api/events` come da `API_CONTRACT.md`.
- **III. API testabili indipendentemente** — PASS. Whitelist, normalizzazione e logica di
  retry sono testabili senza `core` in esecuzione, mockando il client HTTP.
- **IV. Servizi esterni preferiti a modelli locali pesanti** — N/A per questa feature: il bot
  non esegue LLM/STT, si limita a inoltrare; nessuna violazione.
- **Vincoli Tecnici** — PASS. Long polling invece di webhook pubblico (adatto a Raspberry Pi
  dietro NAT); retry con backoff copre la connettività non garantita; nessuna libreria pesante
  o GPU richiesta.

Nessuna violazione: tabella "Complexity Tracking" non necessaria.

## Project Structure

### Documentation (this feature)

```text
specs/001-ingestion-bot/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md         # Phase 1 output
├── quickstart.md         # Phase 1 output
├── contracts/            # Phase 1 output
└── tasks.md              # Phase 2 output (/speckit-tasks — not created here)
```

### Source Code (repository root)

```text
ingestion/
├── src/
│   ├── bot.py          # entrypoint: avvia il bot in long polling, registra gli handler
│   ├── auth.py         # controllo whitelist utenti autorizzati
│   ├── events.py       # normalizzazione messaggio -> evento + invio a core con retry/backoff
│   └── config.py       # lettura variabili d'ambiente (token, whitelist, URL core, retry)
└── tests/
    ├── unit/            # whitelist, normalizzazione, backoff, idempotenza
    └── contract/        # verifica che il payload inviato rispetti API_CONTRACT.md
```

**Structure Decision**: Opzione "single project" dentro il modulo `ingestion/` già esistente
nel monorepo — coerente con la modularità della constitution, nessun bisogno di una struttura
frontend/backend separata per questa feature.

## Complexity Tracking

> Nessuna violazione del Constitution Check: tabella vuota per questa feature.
