# Changelog

Documento condiviso sempre visibile ad entrambi i collaboratori. Ogni commit rilevante
(nuovo modulo, endpoint, decisione architetturale) aggiunge una riga qui, così nessuno dei
due deve rileggere la history di git per sapere lo stato del progetto.

Formato: [Keep a Changelog](https://keepachangelog.com/it/1.1.0/).

## [Unreleased]

### Added
- Struttura moduli (`ingestion`, `pipeline`, `core`, `graph`, `companion`) con README stub.
- `API_CONTRACT.md`: contratto REST tra tutti i moduli (eventi, normalizzazione, grafo,
  progetti/task, preferenze utente).
- Scaffolding Speckit (`.specify/`) e `constitution.md` v1.1.0: privacy-first, modularità,
  API testabili indipendentemente, preferenza servizi esterni su modelli locali pesanti;
  regola su riepilogo di sessione e changelog condiviso.
