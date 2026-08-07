# Contract: Ingestion/Pipeline → Core, Companion → Core

Endpoint consumati/esposti da questa feature — già definiti nel contratto condiviso, non
duplicati qui per evitare divergenze:

- [`API_CONTRACT.md`](../../../API_CONTRACT.md) sezione **1. Ingestion → Core**
  (`POST /api/events`).
- [`API_CONTRACT.md`](../../../API_CONTRACT.md) sezione **2. Pipeline → Core**
  (`PATCH /api/events/{event_id}`).
- [`API_CONTRACT.md`](../../../API_CONTRACT.md) sezione **5. Preferenze utente**
  (`GET/PUT /api/users/{user_id}/preferences`).

Fuori scope per questa feature (vedi Assumptions in `spec.md`): sezione 3
(`Core → Graph`) e sezione 4 (`Companion → Core: progetti/task`) — rimandate a feature
successive.

## Vincoli specifici di questa feature sul contratto esistente

- `POST /api/events` risponde `201` con `event_id` non appena l'evento è persistito in SQLite,
  **prima** di aver generato l'embedding (SC-001: conferma entro 2s) — la generazione
  dell'embedding e il confronto per similarità avvengono subito dopo, in modo sincrono ma senza
  bloccare la risposta oltre il tempo di scrittura su SQLite.
- `PATCH /api/events/{event_id}` su un evento con `type` `audio`/`image` innesca la generazione
  dell'embedding (prima assente per mancanza di testo, FR-003) usando `normalized_text`.
- `GET /api/users/{user_id}/preferences` su un utente senza preferenze salvate risponde con i
  default descritti in `data-model.md` (FR-006), non con `404`.
