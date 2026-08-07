# Contract: Companion → Core (ricerca, US1)

Endpoint consumato, già definito nel contratto condiviso, non duplicato qui:

- [`API_CONTRACT.md`](../../../API_CONTRACT.md) sezione **6. Companion → Core: ricerca
  semantica** (`GET /api/events/search?q=...&limit=...`).

## Interfaccia esposta da companion (HTML per l'utente finale, non un'API tra moduli)

- **`GET /search`** — form per inserire il testo di ricerca (`q`).
- **`GET /search?q=...`** — chiama `core`, mostra i risultati (`preview`, `type`, `timestamp`,
  `score`); se `results` è vuoto, mostra "nessun risultato trovato" (FR-005 dello spec, non un
  errore).

## Utente mock

Tutte le route di `companion`, incluse quelle di US2 già esistenti, richiedono ora HTTP Basic
Auth (`COMPANION_USERNAME`/`COMPANION_PASSWORD`) — non fa parte di `API_CONTRACT.md` (è
un'interfaccia utente, non tra moduli), vedi `research.md` per la motivazione.
