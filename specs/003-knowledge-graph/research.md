# Research: Grafo di Progetti ed Eventi Collegati

Nessun `[NEEDS CLARIFICATION]` residuo.

## Storage

**Decision**: SQLite (stdlib `sqlite3`), tabelle `nodes` ed `edges`, coerente con la scelta già
fatta per `core`.

**Rationale**: stesso volume/uso personale di `core`: un DB a grafo dedicato (Neo4j, ecc.)
aggiungerebbe un servizio da gestire senza beneficio misurabile a questo volume.

**Alternatives considered**: Neo4j o altro DB a grafo (scartato, overkill per un utente
singolo e poche migliaia di nodi); Postgres con estensione grafo (stesso motivo).

## Esplorazione dei collegamenti

**Decision**: BFS (breadth-first search) in-process: si caricano le relazioni rilevanti da
SQLite in un dizionario di adiacenza e si esplora fino alla profondità richiesta con una coda,
trattando le relazioni come non orientate (assumption dello spec).

**Rationale**: a poche migliaia di nodi/relazioni, un BFS in memoria è dell'ordine dei
millisecondi — ampiamente entro SC-004. Una libreria di grafi come `networkx` aggiungerebbe una
dipendenza per un algoritmo che qui è poche righe di stdlib (coda, set di visitati).

**Alternatives considered**: `networkx` (scartato per lo stesso principio YAGNI applicato in
`core` per il vector database: non c'è bisogno finché il volume non lo giustifica).

## Idempotenza sui nodi

**Decision**: `UNIQUE` su `source_event_id` nella tabella `nodes`: un secondo tentativo di
creare un nodo per lo stesso evento originale viene ignorato (FR-002), ritornando il nodo già
esistente.

**Rationale**: stesso pattern già usato in `core` per l'idempotenza su `event_id` — coerenza
tra moduli, un solo modo di risolvere lo stesso problema nel monorepo.

## Validazione delle relazioni

**Decision**: prima di inserire una relazione, si verifica in un'unica transazione che entrambi
i nodi esistano (FR-004) e che non siano lo stesso nodo (FR-005, self-loop rifiutato).

**Rationale**: evita relazioni orfane o senza senso semantico nel dominio, con un controllo
applicativo semplice invece di vincoli SQLite più complessi da mantenere.
