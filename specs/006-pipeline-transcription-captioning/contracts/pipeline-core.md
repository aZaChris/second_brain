# Contract: Pipeline → Core

Endpoint consumati, già definiti nel contratto condiviso, non duplicati qui:

- [`API_CONTRACT.md`](../../../API_CONTRACT.md) sezione **8. Pipeline → Core: eventi in attesa
  di elaborazione** (`GET /api/events/pending`, `007-core-pending-events`).
- [`API_CONTRACT.md`](../../../API_CONTRACT.md) sezione **2. Pipeline → Core: evento
  normalizzato** (`PATCH /api/events/{event_id}`).

## Vincoli specifici di questa feature sul contratto esistente

- `pipeline` chiama `GET /api/events/pending` con `type=audio,image` (il default) a intervalli
  regolari (research.md) — non c'è un endpoint di notifica push.
- Ogni evento elaborato, con successo o con fallimento definitivo, riceve esattamente un
  `PATCH` con `normalized_text` valorizzato (mai lasciato vuoto/nullo) — così esce sempre dalla
  lista di `GET /api/events/pending` una volta gestito, coerente con FR-004/FR-005 di
  `007-core-pending-events`.
- Su fallimento definitivo (file irraggiungibile o servizio esterno esaurito dopo i retry),
  `normalized_text` contiene un testo segnaposto riconoscibile e `pipeline_meta.status` è
  `"failed"` (research.md) — nessun nuovo endpoint introdotto per questo caso.
