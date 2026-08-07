# Implementation Plan: App di Consultazione (Companion) — US1 + utente mock

**Branch**: `004-companion-app` | **Date**: 2026-08-07 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/004-companion-app/spec.md`

**Scope di questo piano**: **User Story 1 — Ricerca tra i contenuti salvati**, più un
ritocco trasversale: un gate di autenticazione con un **utente mock** (una sola coppia
utente/password da variabili d'ambiente, non un sistema utenti) applicato a tutte le route di
`companion`, per colmare il gap su FR-006 notato durante la revisione della spec (vedi
`checklists/requirements.md`). US2 (esplorazione grafo) è già implementata — qui riceve solo il
gate di autenticazione. US3 (cronologia) resta fuori, pianificata a parte in seguito.

## Summary

Aggiunge a `companion` (già FastAPI + Jinja2 server-rendered) una pagina di ricerca che chiama
`GET /api/events/search` su `core` (`005-core-search-history`) e mostra i risultati con
anteprima, tipo, data e punteggio. Aggiunge inoltre un gate di autenticazione HTTP Basic con
un'unica coppia utente/password configurata via env var — non un sistema di account, solo un
modo per non lasciare `companion` completamente aperto ora che espone anche la ricerca (che
rende interrogabile tutto il contenuto personale salvato).

## Technical Context

**Language/Version**: Python 3.11+ (stesso stack degli altri moduli/di `companion` US2).

**Primary Dependencies**: nessuna nuova dipendenza — `fastapi.security.HTTPBasic` è già incluso
in FastAPI, nessun pacchetto aggiuntivo per l'autenticazione.

**Storage**: N/A — invariato rispetto a US2.

**Testing**: `pytest` con `TestClient`; client verso `core` mockato per i test (stesso pattern
di `graph_client` in US2).

**Target Platform**: stesso host/rete privata di US2 (vedi `DEPLOY.md`).

**Project Type**: web app server-rendered (invariato).

**Performance Goals**: ricerca visualizzata entro 2s (coerente con SC-001 di `spec.md`, che
`core` già rispetta da `005-core-search-history`).

**Constraints**: l'utente mock non è un sistema di autenticazione vero (nessun hashing con
salt/bcrypt, nessuna sessione, nessun account multiplo) — è un gate minimo con confronto in
tempo costante (`secrets.compare_digest`) su una coppia utente/password fissa da env var, per
tenere `companion` non completamente aperto senza costruire infrastruttura non necessaria a un
solo utente. Va sostituito con autenticazione vera se `companion` verrà mai esposta oltre la
rete locale (nota già in `spec.md`).

**Scale/Scope**: singolo utente, invariato.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **I. Privacy-First** — PASS. Nessun nuovo dato salvato; il gate di autenticazione riduce,
  non aumenta, l'esposizione di dati personali tramite ricerca.
- **II. Modularità** — PASS. Nuovo punto di contatto solo verso `core`
  (`GET /api/events/search`), già definito nel contratto condiviso.
- **III. API testabili indipendentemente** — PASS. Client verso `core` mockabile, gate di
  autenticazione testabile senza credenziali reali (env var di test).
- **IV. Servizi esterni preferiti a modelli locali pesanti** — N/A per questa user story.
- **Vincoli Tecnici** — PASS. Nessuna dipendenza nuova, nessun requisito hardware.

Nessuna violazione: tabella "Complexity Tracking" non necessaria.

## Project Structure

### Documentation (this feature)

```text
specs/004-companion-app/
├── plan.md               # questo file, aggiornato per l'incremento US1 + auth
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
└── tasks.md
```

### Source Code (repository root)

```text
companion/
├── src/
│   ├── api.py             # + GET /search, + dependency di autenticazione su tutte le route
│   ├── auth.py              # NUOVO: gate HTTP Basic, utente mock da env var
│   ├── core_client.py        # NUOVO: chiamata GET /api/events/search a core
│   ├── graph_client.py        # invariato (US2)
│   ├── config.py               # + COMPANION_USERNAME, COMPANION_PASSWORD, CORE_API_URL, CORE_API_TOKEN
│   └── templates/
│       ├── explore_form.html    # invariato
│       ├── related_results.html  # invariato
│       └── search_results.html    # NUOVO
└── tests/
    ├── unit/                       # + test_auth.py, + test_core_client.py
    └── contract/                    # + test_search_contract.py; test_explore_contract.py aggiornato per l'auth
```

**Structure Decision**: estende il modulo `companion/` già esistente (creato per US2), stessa
struttura piatta. Nessuna cartella nuova.

## Complexity Tracking

> Nessuna violazione del Constitution Check: tabella vuota per questa feature.
