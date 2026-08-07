# Data Model: Eventi in Attesa di Elaborazione (Core)

Nessuna nuova tabella: legge la tabella `events` già definita in
`002-core-similarity-engine/data-model.md`. Nuova query, non nuovi campi.

## Query: eventi in attesa

`get_pending_events(conn, types: list[str], limit: int) -> list[{event_id, type, media_url, timestamp}]`

```sql
SELECT event_id, type, media_url, timestamp FROM events
WHERE type IN (...) AND normalized_text IS NULL
ORDER BY timestamp ASC LIMIT ?
```

`types` di default `["audio", "image"]` (FR-007: gli eventi `text` non hanno mai
`normalized_text IS NULL` in modo rilevante qui — comunque esclusi esplicitamente dal filtro
`type IN (...)`, coerente con research.md).

## Risposta (non persistita)

`{"events": [{"event_id": ..., "type": ..., "media_url": ..., "timestamp": ...}]}` — vedi
`API_CONTRACT.md` sezione 8.
