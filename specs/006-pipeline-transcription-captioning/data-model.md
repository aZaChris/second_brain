# Data Model: Trascrizione Audio e Captioning Immagini (Pipeline)

Nessuno storage proprio (privacy-first, coerente con `plan.md`): le entità sotto sono
rappresentazioni in memoria durante l'elaborazione di un singolo evento.

## PendingEvent (letto da `core`)

Corrisponde 1:1 a un elemento di `GET /api/events/pending` (`API_CONTRACT.md` sezione 8):

| Campo | Tipo | Note |
|---|---|---|
| `event_id` | str | usato per il successivo `PATCH` |
| `type` | `audio` \| `image` | decide se chiamare `transcription.py` o `captioning.py` |
| `media_url` | str | riferimento al file da scaricare |
| `timestamp` | str | non usato operativamente, solo per ordinamento già garantito da `core` |

## ProcessingResult (inviato a `core`)

Corrisponde al body di `PATCH /api/events/{event_id}` (`API_CONTRACT.md` sezione 2):

| Campo | Valore |
|---|---|
| `normalized_text` | testo trascritto/descritto, oppure testo segnaposto su fallimento definitivo (research.md) |
| `pipeline_meta.model_used` | identificativo del servizio esterno usato |
| `pipeline_meta.status` | `"ok"` \| `"failed"` |
| `pipeline_meta.reason` | presente solo se `status: failed` (es. `"file_unreachable"`, `"service_unavailable"`) |
