# Data Model: Motore di Similarità e Approfondimento (Core)

## Tabella `events` (SQLite)

| Campo | Tipo | Note |
|---|---|---|
| `event_id` | TEXT PRIMARY KEY | generato da `core` alla ricezione; `UNIQUE` garantisce l'idempotenza (FR-007) |
| `source` | TEXT | da `API_CONTRACT.md` (`telegram`, ...) |
| `user_id` | TEXT | da `API_CONTRACT.md` |
| `type` | TEXT | `text` \| `audio` \| `image` |
| `content` | TEXT NULL | testo diretto, se `type == text` |
| `media_url` | TEXT NULL | riferimento al media, se `type in {audio, image}` |
| `normalized_text` | TEXT NULL | valorizzato da `PATCH /api/events/{event_id}` (da `pipeline`) per audio/immagine |
| `embedding` | TEXT NULL | JSON del vettore embedding; NULL finché non c'è testo da cui generarlo (FR-003) |
| `status` | TEXT | `received` \| `embedded` \| `skipped_low_signal` (FR-008: contenuto troppo generico) |
| `timestamp` | TEXT | timestamp originale dell'evento (ISO 8601 UTC) |
| `created_at` | TEXT | quando `core` ha accettato l'evento |

**Regola**: `embedding` viene calcolato quando è disponibile un testo (`content` se
`type == text`, altrimenti `normalized_text` dopo il `PATCH`). Se il testo risultante è troppo
corto/generico, `status` diventa `skipped_low_signal` e non si tenta il confronto (FR-008).

## Tabella `user_preferences` (SQLite)

Corrisponde al body di `GET/PUT /api/users/{user_id}/preferences` in `API_CONTRACT.md`.

| Campo | Tipo | Note |
|---|---|---|
| `user_id` | TEXT PRIMARY KEY | |
| `interests` | TEXT | JSON array di stringhe |
| `depth_level` | TEXT | `minimo` \| `equilibrato` \| `approfondito` |
| `notify_on` | TEXT | JSON array di stringhe |
| `updated_at` | TEXT | ISO 8601 UTC |

**Default in assenza di riga**: `depth_level = "equilibrato"`, `interests = []`,
`notify_on = []` — comportamento di default né invasivo né silenzioso (FR-006).

## Collegamento trovato (in-memory, non persistito come tabella separata)

Risultato del confronto per un dato evento: `{"event_id": ..., "similarity": float 0-1}`,
filtrato per soglia minima e poi passato a `insight.py` insieme alle preferenze utente per
decidere se/come segnalarlo (si veda `research.md`).
