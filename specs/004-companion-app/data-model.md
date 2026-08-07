# Data Model: App di Consultazione (Companion) — solo US2

Nessuna tabella propria: `companion` non persiste nulla, è un livello di presentazione sopra
`GET /api/graph/related/{node_id}` di `graph` (vedi `003-knowledge-graph/data-model.md` per
l'origine dei dati).

## Vista: risultato di esplorazione (non persistita)

Costruita direttamente dalla risposta di `graph`:

| Campo | Origine |
|---|---|
| `node_id` di partenza | parametro della richiesta (`?node_id=...`) |
| `related` | lista `{node_id, relation, weight}` così come restituita da `graph` |

Ogni elemento di `related` viene renderizzato anche come link `?node_id=<quel node_id>` per
continuare l'esplorazione (research.md).
