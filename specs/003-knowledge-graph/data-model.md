# Data Model: Grafo di Progetti ed Eventi Collegati

## Tabella `nodes` (SQLite)

| Campo | Tipo | Note |
|---|---|---|
| `node_id` | TEXT PRIMARY KEY | generato da `graph` alla creazione |
| `node_type` | TEXT | `project` \| `note` \| `idea` \| `person` \| `concept` (da `API_CONTRACT.md`) |
| `label` | TEXT | etichetta leggibile del nodo |
| `source_event_id` | TEXT UNIQUE | riferimento all'evento originale; `UNIQUE` garantisce l'idempotenza (FR-002) |
| `embedding_ref` | TEXT NULL | riferimento opaco all'embedding in `core` (campo del contratto, non usato dalla logica di `graph`) |
| `created_at` | TEXT | ISO 8601 UTC |

## Tabella `edges` (SQLite)

| Campo | Tipo | Note |
|---|---|---|
| `edge_id` | TEXT PRIMARY KEY | generato da `graph` alla creazione |
| `from_node_id` | TEXT | FK verso `nodes.node_id`, validato in applicazione (FR-004) |
| `to_node_id` | TEXT | FK verso `nodes.node_id`, validato in applicazione (FR-004); deve differire da `from_node_id` (FR-005) |
| `relation` | TEXT | es. `deriva-da`, `collegato-a`, `usa-tecnologia-di` |
| `weight` | REAL | forza/pertinenza della relazione |
| `created_at` | TEXT | ISO 8601 UTC |

## Esplorazione (non persistita)

Risultato di `GET /api/graph/related/{node_id}?depth=N`: lista di
`{"node_id": ..., "relation": ..., "weight": ...}` per ogni nodo raggiunto entro `N` passi,
calcolata con BFS sul dizionario di adiacenza costruito da `edges` (relazioni trattate come non
orientate, vedi Assumptions in `spec.md`). Se un nodo è raggiungibile tramite più cammini, si
riporta la relazione/peso del cammino più breve trovato per primo dal BFS.
