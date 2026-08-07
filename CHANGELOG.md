# Changelog

Documento condiviso sempre visibile ad entrambi i collaboratori. Ogni commit rilevante
(nuovo modulo, endpoint, decisione architetturale) aggiunge una riga qui, così nessuno dei
due deve rileggere la history di git per sapere lo stato del progetto.

Formato: [Keep a Changelog](https://keepachangelog.com/it/1.1.0/).

## [Unreleased]

### Added
- Modulo `ingestion`: bot Telegram (Python, long polling) con whitelist utenti, normalizzazione
  testo/audio/immagine in evento, invio a `core` con retry a backoff esponenziale, notifica di
  fallimento all'utente, deduplica su `message_id`. Implementato secondo
  `specs/001-ingestion-bot/` (spec, plan, tasks). 12 test automatici (unit + contract).
- Modulo `core`: API FastAPI (`POST`/`PATCH /api/events`, `GET`/`PUT /api/users/{id}/preferences`)
  su storage SQLite. Genera embedding (servizio esterno) in background dopo la risposta, cerca
  collegamenti per similarità (cosine, numpy) tra eventi salvati, decide se segnalarli in base
  alle preferenze utente (con default se assenti). Implementato secondo
  `specs/002-core-similarity-engine/`. 20 test automatici (unit + contract).
- Struttura moduli (`ingestion`, `pipeline`, `core`, `graph`, `companion`) con README stub.
- `API_CONTRACT.md`: contratto REST tra tutti i moduli (eventi, normalizzazione, grafo,
  progetti/task, preferenze utente).
- Scaffolding Speckit (`.specify/`) e `constitution.md` v1.1.0: privacy-first, modularità,
  API testabili indipendentemente, preferenza servizi esterni su modelli locali pesanti;
  regola su riepilogo di sessione e changelog condiviso.
