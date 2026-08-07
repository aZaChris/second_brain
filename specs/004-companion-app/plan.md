# Implementation Plan: App di Consultazione (Companion) — solo US2

**Branch**: `004-companion-app` | **Date**: 2026-08-07 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/004-companion-app/spec.md`

**Scope di questo piano**: solo **User Story 2 — Esplorazione dei collegamenti di un
contenuto**. US1 (ricerca) e US3 (cronologia) restano fuori da questo piano per scelta
esplicita, anche se `core` li supporta già da `005-core-search-history` — verranno pianificate
a parte in un secondo momento.

## Summary

Piccola web app server-rendered (FastAPI + Jinja2, nessun frontend build/JS framework) che
permette di inserire un `node_id` e una profondità, chiama `GET /api/graph/related/{node_id}`
su `graph` (già implementato in `003-knowledge-graph`) e mostra i nodi collegati con tipo di
relazione e peso, con la possibilità di continuare l'esplorazione cliccando su un nodo
collegato.

## Technical Context

**Language/Version**: Python 3.11+ (stesso stack degli altri moduli).

**Primary Dependencies**: FastAPI, Jinja2 (HTML server-rendered — nessuna build frontend,
nessun framework JS: per una pagina di consultazione a uso personale è complessità non
giustificata), `httpx` (chiamata a `graph`).

**Storage**: N/A — `companion` non persiste nulla di proprio, è un livello di presentazione
sopra le API già esistenti.

**Testing**: `pytest` con `TestClient` di FastAPI; client verso `graph` mockato per i test.

**Target Platform**: stesso host degli altri moduli (es. lo stesso Raspberry Pi, vedi
`DEPLOY.md`), accesso via browser sulla rete locale.

**Project Type**: web app server-rendered.

**Performance Goals**: la pagina di esplorazione si carica entro 1s (coerente con SC-004 di
`003-knowledge-graph`, che `graph` già rispetta).

**Constraints**: nessuna autenticazione utente in questa v1 — assumption: l'app gira su rete
privata/locale, non esposta su internet pubblico (da rivedere se questo cambia). La chiamata
`companion` → `graph` resta comunque autenticata con `GRAPH_API_TOKEN`, come da
`API_CONTRACT.md`.

**Scale/Scope**: singolo utente, stesso ordine di grandezza degli altri moduli.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **I. Privacy-First** — PASS. `companion` non salva nulla: fa solo da presentazione sopra
  l'API di `graph`, nessun nuovo storage di dati personali.
- **II. Modularità** — PASS. `companion` vive in `companion/`, l'unico punto di contatto è
  `GET /api/graph/related/{node_id}` come da `API_CONTRACT.md`.
- **III. API testabili indipendentemente** — PASS. `TestClient` + client verso `graph`
  mockabile permettono di testare `companion` senza `graph` in esecuzione.
- **IV. Servizi esterni preferiti a modelli locali pesanti** — N/A: nessun LLM/STT coinvolto in
  questa user story.
- **Vincoli Tecnici** — PASS. Nessuna build frontend, nessun requisito hardware specifico;
  leggero quanto gli altri moduli.

Nessuna violazione: tabella "Complexity Tracking" non necessaria.

## Project Structure

### Documentation (this feature)

```text
specs/004-companion-app/
├── plan.md
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
│   ├── api.py            # route FastAPI: form di esplorazione + rendering risultati
│   ├── graph_client.py     # chiamata GET /api/graph/related/{node_id} a graph
│   ├── config.py            # GRAPH_API_URL, GRAPH_API_TOKEN
│   └── templates/
│       ├── explore_form.html
│       └── related_results.html
└── tests/
    ├── unit/                  # graph_client (mockato)
    └── contract/               # TestClient sulle route HTML
```

**Structure Decision**: nuovo modulo `companion/`, stessa struttura piatta degli altri moduli
del monorepo. Solo le route/i template per US2 in questo piano; US1 (ricerca) e US3
(cronologia) aggiungeranno rispettivamente route/template propri in un piano successivo, senza
impatto su questa struttura.

## Complexity Tracking

> Nessuna violazione del Constitution Check: tabella vuota per questa feature.
