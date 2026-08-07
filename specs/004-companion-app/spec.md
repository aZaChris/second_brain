# Feature Specification: App di Consultazione (Companion)

**Feature Branch**: `004-companion-app`

**Created**: 2026-08-07

**Status**: Draft

**Input**: User description: "App di consultazione del Second Brain: ricerca semantica tra i contenuti salvati, esplorazione del grafo delle connessioni a partire da un contenuto, e cronologia dei contenuti inviati nel tempo — così l'utente può ritrovare e riscoprire ciò che ha scritto/salvato."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Ricerca tra i contenuti salvati (Priority: P1)

L'utente cerca, con parole libere, qualcosa che ricorda di aver scritto o salvato in passato, e
ottiene i contenuti più pertinenti, anche se non usa esattamente le stesse parole dell'originale
— così ritrovare un pensiero passato non richiede di ricordarne il testo esatto.

**Why this priority**: È il modo più diretto e frequente con cui l'utente torna a usare ciò che
ha accumulato nel Second Brain; senza ricerca, il valore di tutto il resto resta inaccessibile.

**Independent Test**: Cercare un termine legato a un contenuto salvato in precedenza e
verificare che compaia tra i primi risultati, con abbastanza contesto da riconoscerlo.

**Acceptance Scenarios**:

1. **Given** esiste un contenuto salvato pertinente, **When** l'utente cerca con parole
   collegate al suo significato, **Then** il contenuto compare tra i risultati con anteprima,
   data e tipo.
2. **Given** nessun contenuto salvato è pertinente alla ricerca, **When** l'utente cerca,
   **Then** il sistema indica chiaramente che non ci sono risultati, senza errore.

---

### User Story 2 - Esplorazione dei collegamenti di un contenuto (Priority: P2)

A partire da un contenuto specifico (una nota, un progetto, un'idea), l'utente vede quali altri
contenuti gli sono collegati, e può continuare a esplorare da lì — così riscopre connessioni tra
pensieri fatti in momenti diversi.

**Why this priority**: Arricchisce la ricerca ma presuppone che l'utente sia già arrivato a un
contenuto (tramite ricerca o cronologia, US1/US3).

**Independent Test**: Aprire un contenuto con collegamenti noti e verificare che vengano
mostrati tutti i contenuti collegati, con il tipo di relazione.

**Acceptance Scenarios**:

1. **Given** un contenuto con collegamenti esistenti, **When** l'utente ne esplora i
   collegamenti, **Then** vede i contenuti collegati con il tipo di relazione tra loro.
2. **Given** un contenuto senza collegamenti, **When** l'utente ne esplora i collegamenti,
   **Then** il sistema indica che non ce ne sono, senza errore.

---

### User Story 3 - Cronologia dei contenuti inviati (Priority: P3)

L'utente scorre in ordine cronologico ciò che ha inviato al Second Brain, per rivedere cosa ha
scritto in un certo periodo, anche senza un termine di ricerca preciso in mente.

**Why this priority**: Utile per rivedere/riflettere sul proprio percorso, ma meno centrale
della ricerca mirata (US1) e dell'esplorazione (US2) per il valore quotidiano dell'app.

**Independent Test**: Consultare la cronologia e verificare che i contenuti compaiano in ordine
cronologico corretto, con anteprima e tipo.

**Acceptance Scenarios**:

1. **Given** l'utente ha inviato più contenuti nel tempo, **When** consulta la cronologia,
   **Then** li vede in ordine cronologico, con anteprima, data e tipo.
2. **Given** non è ancora stato inviato nulla, **When** l'utente consulta la cronologia,
   **Then** il sistema indica che è vuota, senza errore.

---

### Edge Cases

- La ricerca produce moltissimi risultati pertinenti: l'utente deve poter vedere i più
  pertinenti senza essere sommerso da tutti in una volta.
- L'utente prova a esplorare i collegamenti di un contenuto che non esiste (mai stato salvato o
  rimosso): il sistema deve dirlo chiaramente, non fallire silenziosamente.
- La cronologia viene consultata su un periodo molto ampio con centinaia di contenuti: deve
  restare scorrevole, non bloccarsi o rallentare vistosamente.
- Solo l'utente autorizzato proprietario del Second Brain può accedere a ricerca, esplorazione
  e cronologia — nessun altro utente deve poter vedere questi contenuti.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Il sistema DEVE permettere all'utente di cercare tra i propri contenuti salvati
  usando testo libero, restituendo i risultati più pertinenti al significato della ricerca (non
  solo corrispondenza esatta delle parole).
- **FR-002**: Il sistema DEVE mostrare, per ogni risultato di ricerca, anteprima del contenuto,
  data e tipo, così da poterlo riconoscere senza doverlo aprire.
- **FR-003**: Il sistema DEVE permettere di esplorare i collegamenti diretti di un contenuto
  specifico, mostrando i contenuti collegati e il tipo di relazione.
- **FR-004**: Il sistema DEVE permettere di consultare la cronologia dei contenuti inviati, in
  ordine cronologico, con anteprima, data e tipo.
- **FR-005**: Il sistema DEVE indicare chiaramente quando una ricerca, un'esplorazione o la
  cronologia non producono risultati, distinguendolo da una condizione di errore.
- **FR-006**: Il sistema DEVE restringere l'accesso a ricerca, esplorazione e cronologia al solo
  utente autorizzato proprietario del Second Brain.
- **FR-007**: Il sistema DEVE gestire senza errori bloccanti le richieste su un contenuto
  inesistente o su una cronologia vuota.
- **FR-008**: Il sistema DEVE limitare il numero di risultati mostrati in una volta (ricerca e
  cronologia), permettendo di vederne altri su richiesta, quando i risultati pertinenti sono
  molti.

### Key Entities

- **Risultato di ricerca**: un contenuto salvato ritenuto pertinente a una ricerca, con
  anteprima, data, tipo e grado di pertinenza.
- **Contenuto esplorato**: un contenuto e l'elenco dei contenuti ad esso collegati, ciascuno con
  il tipo di relazione.
- **Voce di cronologia**: un contenuto inviato in un dato momento, con anteprima, data e tipo.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Una ricerca restituisce i risultati entro 2 secondi dall'invio.
- **SC-002**: Cercando un contenuto salvato in precedenza con parole diverse da quelle
  originali, l'utente lo trova tra i primi risultati in almeno il 90% dei tentativi verificati.
- **SC-003**: L'esplorazione dei collegamenti di un contenuto mostra tutti e soli i collegamenti
  diretti attesi nel 100% dei casi verificati.
- **SC-004**: La cronologia resta scorrevole (nessun rallentamento percepibile) anche con
  centinaia di contenuti salvati.

## Assumptions

- `companion` è ad uso del singolo utente autorizzato del Second Brain (lo stesso di
  `ingestion`), non un'app multi-utente.
- Ricerca semantica e cronologia richiedono endpoint di lettura in `core` che oggi non esistono
  (`core`, come specificato e implementato in `002-core-similarity-engine`, espone solo
  scrittura di eventi e lettura/scrittura preferenze). Sarà necessaria una feature dedicata su
  `core` (o un'estensione di `API_CONTRACT.md`) prima che questa feature possa essere
  implementata per intero — questa spec descrive il comportamento atteso lato utente,
  indipendentemente da quando quegli endpoint saranno disponibili.
- L'esplorazione dei collegamenti si appoggia agli endpoint già esistenti in `graph`
  (`GET /api/graph/related/{node_id}`, già implementato in `003-knowledge-graph`).
- In questa fase non è richiesta la possibilità di modificare o cancellare contenuti dall'app:
  solo consultazione (ricerca, esplorazione, cronologia).
