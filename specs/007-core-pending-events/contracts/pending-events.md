# Contract: Pipeline → Core (scoperta eventi da elaborare)

Endpoint già definito nel contratto condiviso, non duplicato qui:

- [`API_CONTRACT.md`](../../../API_CONTRACT.md) sezione **8. Pipeline → Core: eventi in attesa
  di elaborazione** (`GET /api/events/pending`).

## Vincoli specifici di questa feature sul contratto esistente

- Un evento compare nell'elenco finché non riceve un `PATCH /api/events/{event_id}` con
  `normalized_text` (research.md) — indipendentemente dall'esito dell'embedding fatto da `core`
  dopo il `PATCH`.
- Gli eventi sono ordinati per `timestamp` crescente (i più vecchi prima), non decrescente come
  la cronologia di `companion` (sezione 7).
- `type` non valido nel filtro (diverso da `audio`/`image`) viene ignorato silenziosamente
  (comportamento di default: nessun filtro invalido causa errore, semplicemente non produce
  risultati per quel valore).
