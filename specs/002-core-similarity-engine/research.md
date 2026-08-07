# Research: Motore di Similarità e Approfondimento (Core)

Nessun `[NEEDS CLARIFICATION]` residuo: le decisioni sotto derivano dai vincoli della
constitution e dal volume atteso (uso personale).

## Storage

**Decision**: SQLite locale (`sqlite3` di stdlib), niente ORM.

**Rationale**: un solo utente, volume basso (ordine di migliaia di eventi nel tempo): un DB
server (Postgres) o un ORM aggiungerebbero un servizio/dipendenza da gestire senza un beneficio
misurabile a questo volume. SQLite copre transazioni, `UNIQUE` per l'idempotenza su `event_id`
e query semplici senza infrastruttura aggiuntiva.

**Alternatives considered**: Postgres (scartato, overkill per 1 utente); un ORM come SQLAlchemy
(scartato, le query necessarie sono poche e semplici — `sqlite3` di stdlib basta).

## Ricerca per similarità

**Decision**: cosine similarity calcolata in-process con `numpy` su tutti gli embedding salvati
in SQLite, caricati in memoria al momento della richiesta.

**Rationale**: a un volume di migliaia di eventi, un confronto brute-force in memoria è
dell'ordine dei millisecondi — ampiamente entro il budget di SC-001 (conferma entro 2s). Un
vector database dedicato (Qdrant, Pinecone, pgvector) introdurrebbe un servizio aggiuntivo da
gestire sul proprio hardware senza necessità a questo volume.

**Alternatives considered**: vector database dedicato (rimandato a quando/se il volume di
eventi crescerà di ordini di grandezza — annotato come possibile evoluzione, non implementato
ora).

## Servizio di embedding

**Decision**: chiamata HTTP a un servizio esterno di embedding (es. API di embedding di un
provider terzo), dietro un'interfaccia `embedding.py` con una sola funzione
`embed(text: str) -> list[float]`, cosicché il provider concreto sia sostituibile senza
toccare il resto del codice.

**Rationale**: coerente con il principio IV della constitution (servizi esterni preferiti a
modelli pesanti locali). Un'interfaccia minima disaccoppia `core` dal provider specifico, utile
se in futuro si cambia provider per costo/qualità.

**Alternatives considered**: modello di embedding locale (es. `sentence-transformers`) —
scartato: richiederebbe scaricare pesi di modello e più RAM/CPU di quanto valga per un servizio
che comunque non gira sul Raspberry Pi ma su una macchina già dimensionata per usi leggeri.

## Decisione di segnalazione (insight)

**Decision**: soglia di similarità minima configurabile (default assunto: 0.75 su cosine
similarity normalizzata 0-1) sotto la quale nessun collegamento viene proposto; la soglia
effettiva e la priorità di segnalazione vengono poi modulate dalle preferenze utente
(`depth_level`, `interests`).

**Rationale**: evita di segnalare collegamenti deboli/rumorosi (FR-008), mantenendo la logica
di decisione (`insight.py`) separata dal calcolo di similarità (`similarity.py`) per poterla
testare e tarare in isolamento.

**Alternatives considered**: nessuna soglia (segnalare sempre il match migliore) — scartato,
violerebbe FR-008 e produrrebbe rumore quando nessun contenuto è davvero pertinente.
