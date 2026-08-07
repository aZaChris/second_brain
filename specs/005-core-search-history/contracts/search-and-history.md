# Contract: Companion → Core (ricerca e cronologia)

Endpoint già definiti nel contratto condiviso, non duplicati qui:

- [`API_CONTRACT.md`](../../../API_CONTRACT.md) sezione **6. Companion → Core: ricerca
  semantica** (`GET /api/events/search`).
- [`API_CONTRACT.md`](../../../API_CONTRACT.md) sezione **7. Companion → Core: cronologia
  eventi** (`GET /api/events`).

## Vincoli specifici di questa feature sul contratto esistente

- `GET /api/events/search` considera solo eventi con `status: embedded` (FR-003): un evento in
  attesa di trascrizione o scartato per contenuto troppo generico non compare mai nei risultati.
- `GET /api/events/search` con `q` vuota o assente risponde `200` con `"results": []`, non un
  errore (edge case dello spec).
- `GET /api/events` include tutti gli eventi salvati, indipendentemente da `status`.
- Entrambi gli endpoint applicano il `limit` massimo del contratto lato server anche se il
  chiamante ne richiede uno più alto (FR-008).
