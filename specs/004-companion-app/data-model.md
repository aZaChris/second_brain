# Data Model: App di Consultazione (Companion) — US2, poi US1 + utente mock

Nessuna tabella propria: `companion` non persiste nulla, è un livello di presentazione sopra le
API già esistenti di `graph` e `core`.

## Vista: risultato di esplorazione (US2, non persistita)

Costruita direttamente dalla risposta di `graph`:

| Campo | Origine |
|---|---|
| `node_id` di partenza | parametro della richiesta (`?node_id=...`) |
| `related` | lista `{node_id, relation, weight}` così come restituita da `graph` |

Ogni elemento di `related` viene renderizzato anche come link `?node_id=<quel node_id>` per
continuare l'esplorazione (research.md).

## Vista: risultati di ricerca (US1, non persistita)

Costruita direttamente dalla risposta di `core` (`API_CONTRACT.md` sezione 6):

| Campo | Origine |
|---|---|
| `q` di ricerca | parametro della richiesta (`?q=...`) |
| `results` | lista `{event_id, preview, type, timestamp, score}` così come restituita da `core` |

## Utente mock (configurazione, non dato applicativo)

Non è un'entità di dominio: `COMPANION_USERNAME`/`COMPANION_PASSWORD` sono configurazione letta
da env var (vedi `config.py`), non righe in un database. Nessuna sessione persistita —
`HTTPBasic` richiede le credenziali a ogni richiesta (research.md).
