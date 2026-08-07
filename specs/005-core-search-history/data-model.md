# Data Model: Ricerca e Cronologia Eventi (Core)

Nessuna nuova tabella: questa feature legge la tabella `events` già definita in
`002-core-similarity-engine/data-model.md`. Nuove query, non nuovi campi.

## Query: eventi con embedding (per la ricerca)

`get_embedded_events_all(conn) -> list[{event_id, content, normalized_text, type, timestamp, embedding}]`

Seleziona tutti gli eventi con `status = 'embedded'` — riusa lo stesso filtro già presente in
`get_embedded_events` (che oggi esclude anche un `event_id`, usato durante l'elaborazione di un
nuovo evento); questa nuova funzione non esclude nulla, serve tutta la ricerca.

## Query: pagina di cronologia

`get_events_page(conn, before: str | None, limit: int) -> list[{event_id, content, normalized_text, type, timestamp}]`

Seleziona gli eventi con `timestamp < before` (o tutti se `before` è assente), ordinati per
`timestamp` decrescente, limitati a `limit` righe. Nessun filtro su `status`: la cronologia
mostra tutti gli eventi salvati, anche quelli senza ancora una rappresentazione semantica.

## Risposta: risultato di ricerca (non persistito)

`{"event_id": ..., "preview": ..., "type": ..., "timestamp": ..., "score": float 0-1}` — vedi
`API_CONTRACT.md` sezione 6.

## Risposta: voce di cronologia (non persistita)

`{"event_id": ..., "preview": ..., "type": ..., "timestamp": ...}` — vedi `API_CONTRACT.md`
sezione 7.
