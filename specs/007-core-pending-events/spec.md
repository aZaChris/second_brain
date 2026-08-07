# Feature Specification: Eventi in Attesa di Elaborazione (Core)

**Feature Branch**: `007-core-pending-events`

**Created**: 2026-08-07

**Status**: Draft

**Input**: User description: "Estensione di core con un endpoint che elenca gli eventi audio/immagine ancora privi di trascrizione/descrizione (GET /api/events/pending), secondo la nuova sezione 8 di API_CONTRACT.md, per sbloccare pipeline (006-pipeline-transcription-captioning)."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Scoperta degli eventi da elaborare (Priority: P1)

Chi si occupa di trasformare audio e immagini in testo (il modulo `pipeline`) può ottenere
l'elenco dei contenuti salvati che aspettano ancora di essere trascritti o descritti, con
abbastanza informazioni per recuperarne il file — così nessun contenuto vocale o visivo resta
"invisibile" in attesa senza che nessuno se ne accorga.

**Why this priority**: Sblocca direttamente US1/US2 di `pipeline` (006); senza questa
capacità, `pipeline` non ha modo di sapere cosa elaborare.

**Independent Test**: Salvare un evento audio e uno immagine, poi richiedere l'elenco degli
eventi in attesa e verificare che entrambi compaiano con tipo, riferimento al file e timestamp.

**Acceptance Scenarios**:

1. **Given** esistono eventi audio/immagine senza ancora una trascrizione/descrizione, **When**
   si richiede l'elenco degli eventi in attesa, **Then** vengono restituiti con tipo,
   riferimento al file e timestamp.
2. **Given** un evento ha già ricevuto una trascrizione/descrizione, **When** si richiede
   l'elenco degli eventi in attesa, **Then** quell'evento non compare più.
3. **Given** non ci sono eventi in attesa, **When** si richiede l'elenco, **Then** il risultato
   è vuoto, non un errore.

---

### User Story 2 - Filtro per tipo di contenuto (Priority: P2)

Chi elabora i contenuti può chiedere solo gli eventi audio o solo quelli immagine, per gestire
i due tipi di elaborazione separatamente se necessario.

**Why this priority**: Comodità operativa, ma l'elenco completo (US1) è già sufficiente per il
valore base della feature.

**Independent Test**: Salvare un evento audio e uno immagine, poi richiedere l'elenco filtrato
per un solo tipo e verificare che compaia solo quello richiesto.

**Acceptance Scenarios**:

1. **Given** esistono eventi in attesa sia audio sia immagine, **When** si richiede l'elenco
   filtrato per un solo tipo, **Then** compaiono solo gli eventi di quel tipo.

---

### Edge Cases

- Vengono richiesti più eventi di quanti ne siano effettivamente in attesa: il sistema
  restituisce tutti quelli disponibili, senza errore.
- Un evento di tipo testo non deve mai comparire nell'elenco, qualunque filtro venga usato.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Il sistema DEVE restituire l'elenco degli eventi di tipo audio o immagine privi
  di una trascrizione/descrizione associata.
- **FR-002**: Per ogni evento restituito, il sistema DEVE includere tipo, riferimento al file e
  timestamp.
- **FR-003**: Il sistema DEVE permettere di filtrare l'elenco per un tipo specifico (solo audio
  o solo immagine).
- **FR-004**: Un evento che ha già ricevuto una trascrizione/descrizione NON DEVE più comparire
  nell'elenco.
- **FR-005**: Se non ci sono eventi in attesa, il sistema DEVE restituire un elenco vuoto, non
  un errore.
- **FR-006**: Il sistema DEVE limitare il numero massimo di eventi restituiti in una singola
  risposta.
- **FR-007**: Gli eventi di tipo testo non devono mai comparire nell'elenco.

### Key Entities

- **Evento in attesa**: un evento audio o immagine salvato, con tipo, riferimento al file e
  timestamp, ancora privo di trascrizione/descrizione.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: L'elenco degli eventi in attesa viene restituito entro 2 secondi.
- **SC-002**: Un evento già elaborato (trascritto/descritto) non compare mai più nell'elenco,
  verificato nel 100% dei casi.
- **SC-003**: Il filtro per tipo restituisce sempre e solo eventi del tipo richiesto, verificato
  nel 100% dei casi.

## Assumptions

- Questa feature estende `core` (già specificato e implementato in
  `002-core-similarity-engine`) aggiungendo sola lettura: nessuna modifica al comportamento di
  scrittura esistente.
- Non è previsto un meccanismo di "claim"/blocco per evitare che due processi di elaborazione
  prendano lo stesso evento in parallelo: si assume un solo processo di `pipeline` attivo alla
  volta (uso personale, basso volume). Un meccanismo di lock andrebbe aggiunto solo se in
  futuro servissero più worker paralleli — fuori scope qui.
- L'autenticazione resta quella già in uso tra moduli (token condiviso di `API_CONTRACT.md`).
