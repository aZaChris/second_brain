# Feature Specification: Ricerca e Cronologia Eventi (Core)

**Feature Branch**: `005-core-search-history`

**Created**: 2026-08-07

**Status**: Draft

**Input**: User description: "Estensione di core con ricerca semantica tra gli eventi salvati (GET /api/events/search) e cronologia paginata degli eventi (GET /api/events), secondo le nuove sezioni 6 e 7 di API_CONTRACT.md, per sbloccare le feature di ricerca e cronologia di companion (004-companion-app)."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Ricerca tra i contenuti salvati (Priority: P1)

Chi consulta il Second Brain (tramite `companion`) può cercare con parole libere e ottenere i
contenuti salvati più pertinenti al significato della ricerca, anche se non corrispondono
esattamente alle parole usate — così ritrovare un pensiero passato non richiede di ricordarne
il testo esatto.

**Why this priority**: Sblocca direttamente US1 di `companion` (004-companion-app), la feature
di consultazione più usata.

**Independent Test**: Salvare un evento con un certo contenuto, poi cercare con parole diverse
ma legate allo stesso significato, e verificare che l'evento compaia tra i risultati.

**Acceptance Scenarios**:

1. **Given** esiste un evento salvato con una rappresentazione semantica, **When** si cerca con
   parole legate al suo significato, **Then** l'evento compare tra i risultati con anteprima,
   tipo, timestamp e punteggio di pertinenza.
2. **Given** nessun evento salvato è pertinente alla ricerca, **When** si cerca, **Then** il
   risultato è vuoto, non un errore.
3. **Given** un evento non ha ancora una rappresentazione semantica (es. media non ancora
   trascritto, o contenuto troppo generico), **When** si effettua una ricerca, **Then** quell'
   evento non compare mai tra i risultati.

---

### User Story 2 - Cronologia degli eventi salvati (Priority: P2)

Chi consulta il Second Brain può sfogliare, in ordine cronologico e a pagine, tutti gli eventi
salvati nel tempo — così può rivedere cosa ha inviato in un certo periodo, anche senza un
termine di ricerca preciso in mente.

**Why this priority**: Sblocca US3 di `companion`; utile ma meno centrale della ricerca mirata
(US1) per il valore quotidiano.

**Independent Test**: Salvare più eventi in momenti diversi, poi richiedere la cronologia e
verificare che siano restituiti in ordine cronologico corretto, sfogliabili a pagine senza
duplicati o omissioni.

**Acceptance Scenarios**:

1. **Given** più eventi salvati in momenti diversi, **When** si richiede la cronologia,
   **Then** vengono restituiti in ordine dal più recente al meno recente, con anteprima, tipo e
   timestamp.
2. **Given** più eventi di quanti ne stiano in una pagina, **When** si richiede la pagina
   successiva, **Then** si ottengono gli eventi seguenti, senza ripetizioni né omissioni.
3. **Given** nessun evento è stato ancora salvato, **When** si richiede la cronologia, **Then**
   il risultato è vuoto, non un errore.

---

### Edge Cases

- Una ricerca viene effettuata con una query vuota o troppo corta per avere significato: il
  sistema deve rispondere in modo controllato (es. nessun risultato), non con un errore.
- Viene richiesto più risultati/eventi di quanti esistano realmente: il sistema restituisce
  tutti quelli disponibili, senza errore.
- La cronologia viene richiesta su un sistema con centinaia di eventi: la paginazione deve
  restare corretta e scorrevole.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Il sistema DEVE permettere di cercare tra gli eventi salvati usando testo libero,
  restituendo quelli più pertinenti al significato della ricerca.
- **FR-002**: Per ogni risultato di ricerca, il sistema DEVE fornire anteprima del contenuto,
  tipo, timestamp e un punteggio di pertinenza.
- **FR-003**: Il sistema DEVE escludere dai risultati di ricerca gli eventi privi di una
  rappresentazione semantica (non ancora generata o scartata per contenuto troppo generico).
- **FR-004**: Se nessun evento è pertinente alla ricerca, il sistema DEVE restituire un
  risultato vuoto, non un errore.
- **FR-005**: Il sistema DEVE permettere di elencare gli eventi salvati in ordine cronologico
  decrescente, con anteprima, tipo e timestamp.
- **FR-006**: Il sistema DEVE permettere di sfogliare la cronologia a pagine, senza richiedere
  di caricare tutti gli eventi in una sola risposta.
- **FR-007**: Se non ci sono eventi salvati, il sistema DEVE restituire una cronologia vuota,
  non un errore.
- **FR-008**: Il sistema DEVE limitare il numero massimo di risultati/eventi restituiti in una
  singola risposta (ricerca e cronologia), per restare scorrevole anche con molti contenuti.

### Key Entities

- **Risultato di ricerca**: un evento salvato pertinente a una ricerca, con anteprima, tipo,
  timestamp e punteggio di pertinenza.
- **Voce di cronologia**: un evento salvato, con anteprima, tipo e timestamp, ordinato
  temporalmente.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Una ricerca restituisce i risultati entro 2 secondi dall'invio.
- **SC-002**: Nessun evento privo di rappresentazione semantica compare mai tra i risultati di
  ricerca, verificato nel 100% dei casi.
- **SC-003**: La cronologia restituisce sempre gli eventi nell'ordine cronologico corretto,
  verificato nel 100% dei casi.
- **SC-004**: Sfogliando la cronologia a pagine su un insieme di centinaia di eventi, nessun
  evento risulta duplicato o mancante tra una pagina e la successiva.

## Assumptions

- Questa feature estende `core` (già specificato e implementato in
  `002-core-similarity-engine`) aggiungendo sola lettura: nessuna modifica al comportamento di
  scrittura già esistente (`POST`/`PATCH /api/events`, preferenze utente).
- La ricerca riusa la stessa rappresentazione semantica (embedding) e lo stesso servizio
  esterno già usati per la ricerca di similarità tra eventi in `002-core-similarity-engine`.
- "Anteprima" del contenuto è un troncamento ragionevole del testo salvato (o della
  trascrizione, per audio/immagine); la lunghezza esatta è un dettaglio lasciato alla
  pianificazione tecnica.
- L'autenticazione resta quella già in uso tra moduli (token condiviso di `API_CONTRACT.md`);
  questa feature non introduce un nuovo meccanismo di autorizzazione per utente.
