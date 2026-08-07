# Contract: Core → Graph, Companion → Graph

Endpoint già definiti nel contratto condiviso, non duplicati qui:

- [`API_CONTRACT.md`](../../../API_CONTRACT.md) sezione **3. Core → Graph** —
  `POST /api/graph/nodes`, `POST /api/graph/edges`, `GET /api/graph/related/{node_id}?depth=1`.

## Vincoli specifici di questa feature sul contratto esistente

- `POST /api/graph/nodes` con lo stesso `source_event_id` già usato per un nodo esistente
  risponde `201` con il `node_id` del nodo già esistente (FR-002), non un errore né un
  duplicato.
- `POST /api/graph/edges` risponde `400` se `from_node_id` o `to_node_id` non esistono, o se
  coincidono tra loro (FR-004, FR-005).
- `GET /api/graph/related/{node_id}?depth=N`: `depth` di default è `1` se assente (come da
  esempio in `API_CONTRACT.md`); valori di `depth` maggiori dell'estensione reale del grafo
  attorno al nodo restituiscono comunque una risposta in tempo utile (FR-009), non un errore.
