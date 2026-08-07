# Contract: Companion → Graph (esplorazione, US2)

Endpoint consumato, già definito nel contratto condiviso, non duplicato qui:

- [`API_CONTRACT.md`](../../../API_CONTRACT.md) sezione **3. Core → Graph**,
  `GET /api/graph/related/{node_id}?depth=1` (lo stesso endpoint, qui chiamato da `companion`
  invece che da `core`).

## Interfaccia esposta da companion (non fa parte di API_CONTRACT.md — è HTML per l'utente finale, non un'API tra moduli)

- **`GET /explore`** — form per inserire `node_id` (obbligatorio) e `depth` (opzionale, default
  `1`).
- **`GET /explore?node_id=...&depth=...`** — esegue la chiamata a `graph` e mostra i risultati;
  se `node_id` non esiste (graph risponde `404`), mostra un messaggio chiaro invece di un errore
  generico; se `related` è vuoto, mostra "nessun collegamento trovato" (FR-007 dello spec).
