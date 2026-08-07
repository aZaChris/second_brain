# Research: Ricerca e Cronologia Eventi (Core)

Nessun `[NEEDS CLARIFICATION]` residuo.

## Ricerca semantica

**Decision**: si genera l'embedding della query con lo stesso client (`embedding.embed`) già
usato per gli eventi in `002-core-similarity-engine`, poi si calcola la cosine similarity
(`similarity.cosine_similarity`, già esistente) contro tutti gli eventi con `status: embedded`,
si ordina per punteggio decrescente e si tronca a `limit`.

**Rationale**: stesso pattern già validato per la ricerca di similarità tra eventi in
`002-core-similarity-engine` — nessuna nuova infrastruttura, solo un nuovo punto di ingresso
(endpoint) sulla logica già esistente.

**Alternatives considered**: indice di ricerca dedicato (es. full-text search di SQLite,
Elasticsearch) — scartato: la ricerca è semantica (per significato), non per parole esatte, e
il volume (migliaia di eventi) non giustifica un indice dedicato oltre al confronto in memoria
già in uso.

## Cronologia paginata

**Decision**: query SQL ordinata per `timestamp` decrescente, con `WHERE timestamp < :before`
quando `before` è fornito, e `LIMIT :limit`. Il campo `next_before` della risposta è il
`timestamp` dell'ultimo evento della pagina corrente (o `null` se la pagina ha meno elementi
del `limit` richiesto, segno che non ce ne sono altri).

**Rationale**: paginazione a cursore (keyset pagination) invece di `OFFSET`: resta corretta
anche se nel frattempo arrivano nuovi eventi, ed è già supportata nativamente da un indice su
`timestamp` in SQLite senza bisogno di una libreria di paginazione.

**Alternatives considered**: paginazione con `OFFSET`/numero di pagina — scartata: con
`OFFSET`, l'arrivo di un nuovo evento tra una richiesta di pagina e la successiva sfalsa i
risultati (rischio di eventi duplicati o saltati), cosa che la paginazione a cursore evita.

## Anteprima del contenuto

**Decision**: funzione `build_preview(event, max_length=140)` che ritorna `content` o
`normalized_text` troncato a 140 caratteri (con `...` se troncato), oppure una stringa
descrittiva (`"[audio] in attesa di trascrizione"` / `"[immagine] in attesa di trascrizione"`)
se non c'è ancora testo disponibile.

**Rationale**: 140 caratteri è una lunghezza standard per anteprime testuali (sufficiente per
riconoscere il contenuto senza appesantire la risposta); la funzione resta minima e locale a
`api.py`, nessun nuovo modulo dedicato per una singola funzione di formattazione.
