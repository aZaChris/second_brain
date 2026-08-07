# Feature Specification: Motore di Similarità e Approfondimento (Core)

**Feature Branch**: `002-core-similarity-engine`

**Created**: 2026-08-07

**Status**: Draft

**Input**: User description: "Motore (core) che riceve un evento normalizzato tramite l'endpoint POST /api/events definito in API_CONTRACT.md (chiamato da ingestion), genera un embedding del contenuto, cerca similarità con eventi/progetti già salvati, e decide se proporre un approfondimento in base alle preferenze utente salvate (GET/PUT /api/users/{user_id}/preferences). Il motore deve rispondere in modo conforme al contratto (event_id, status) e gestire il caso in cui il contenuto arrivi solo come riferimento a media (audio/immagine) non ancora normalizzato da pipeline."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Ogni nota inviata viene salvata e resa ritrovabile (Priority: P1)

Quando l'utente invia un pensiero o una nota (tramite ingestion), il sistema lo accetta, ne
genera una rappresentazione semantica e lo rende disponibile per essere confrontato con
contenuti futuri o passati — così nulla di ciò che l'utente scrive va perso o resta isolato.

**Why this priority**: Senza questo, il Second Brain è solo un archivio cieco: il valore
centrale del progetto (ritrovare e collegare pensieri) dipende da questo primo passo.

**Independent Test**: Inviare un evento con contenuto testuale e verificare che il sistema lo
accetti (risposta conforme al contratto) e che, inviando successivamente un contenuto simile,
il primo venga trovato come collegamento.

**Acceptance Scenarios**:

1. **Given** un evento normalizzato con testo, **When** il sistema lo riceve, **Then** conferma
   la ricezione e genera una rappresentazione semantica del contenuto.
2. **Given** un evento già salvato, **When** arriva un nuovo evento con contenuto simile,
   **Then** il sistema è in grado di trovare il collegamento tra i due.

---

### User Story 2 - Segnalazione di collegamenti con contenuti già salvati (Priority: P2)

Quando arriva un nuovo contenuto, il sistema lo confronta con quanto già salvato e, se trova un
collegamento pertinente con un progetto o una nota precedente, lo segnala come possibile
approfondimento — così l'utente riscopre connessioni che altrimenti dimenticherebbe.

**Why this priority**: È il valore differenziante rispetto a un semplice archivio, ma richiede
che US1 funzioni già (serve contenuto salvato con cui confrontare).

**Independent Test**: Salvare due contenuti chiaramente correlati in momenti diversi e
verificare che l'invio del secondo produca la segnalazione di un collegamento al primo.

**Acceptance Scenarios**:

1. **Given** esiste un contenuto precedente pertinente, **When** arriva un nuovo evento simile,
   **Then** il sistema segnala il collegamento trovato.
2. **Given** non esiste alcun contenuto precedente pertinente (es. primo evento in assoluto),
   **When** arriva un nuovo evento, **Then** il sistema non segnala alcun collegamento.

---

### User Story 3 - Rispetto delle preferenze dell'utente sugli approfondimenti (Priority: P3)

Il sistema decide se e quanto segnalare i collegamenti trovati in base alle preferenze salvate
dall'utente (interessi, livello di approfondimento desiderato) — così l'utente non viene
sommerso da segnalazioni che non vuole ricevere.

**Why this priority**: Migliora l'esperienza ma il sistema resta utile anche con un
comportamento di default se questa fase non è ancora rifinita (US1/US2 già coprono il valore
base).

**Independent Test**: Impostare una preferenza che richiede il minimo delle interruzioni,
inviare un evento con un collegamento pertinente disponibile, e verificare che il sistema non
generi una segnalazione.

**Acceptance Scenarios**:

1. **Given** l'utente ha impostato una preferenza di approfondimento "minimo", **When** viene
   trovato un collegamento pertinente, **Then** il sistema non lo segnala.
2. **Given** l'utente ha impostato interessi specifici, **When** il collegamento trovato
   riguarda uno di quegli interessi, **Then** il sistema lo segnala con priorità maggiore
   rispetto a un collegamento fuori interesse.
3. **Given** l'utente non ha ancora impostato alcuna preferenza, **When** viene trovato un
   collegamento pertinente, **Then** il sistema applica un comportamento di default equilibrato
   (né silenzioso né invasivo).

---

### Edge Cases

- Un evento arriva con solo un riferimento a un file audio/immagine, senza testo (perché
  `pipeline` non lo ha ancora trascritto/descritto): il sistema deve accettare comunque
  l'evento e rimandare la generazione della rappresentazione semantica a quando il testo
  diventerà disponibile.
- Lo stesso evento (stesso identificativo) viene ricevuto più di una volta: non deve essere
  elaborato due volte né generare due segnalazioni.
- Il contenuto è troppo corto o generico per produrre un confronto significativo (es. "ok",
  "ciao"): il sistema non deve forzare una segnalazione di collegamento poco utile.
- Le preferenze dell'utente cambiano tra l'invio di un evento e l'elaborazione dell'evento
  successivo: si applicano sempre le preferenze più recenti disponibili al momento della
  decisione.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Il sistema DEVE accettare un evento normalizzato in arrivo e confermarne la
  ricezione in modo conforme al contratto (`event_id`, stato di ricezione).
- **FR-002**: Il sistema DEVE generare una rappresentazione semantica del contenuto testuale di
  un evento, quando il testo è disponibile.
- **FR-003**: Se l'evento contiene solo un riferimento a media senza testo, il sistema DEVE
  accettare comunque l'evento e rimandare la generazione della rappresentazione semantica al
  momento in cui il contenuto testuale diventa disponibile.
- **FR-004**: Il sistema DEVE confrontare un nuovo contenuto con gli eventi e i progetti già
  salvati per individuare collegamenti pertinenti.
- **FR-005**: Il sistema DEVE decidere, sulla base delle preferenze salvate dell'utente, se e
  con quale priorità segnalare un collegamento trovato.
- **FR-006**: Se l'utente non ha preferenze salvate, il sistema DEVE applicare un comportamento
  di default che non sommerge l'utente di segnalazioni né le sopprime del tutto.
- **FR-007**: Il sistema DEVE evitare di elaborare due volte lo stesso evento se ricevuto più di
  una volta (idempotenza sull'identificativo dell'evento).
- **FR-008**: Il sistema DEVE evitare di segnalare un collegamento quando il contenuto è troppo
  generico o corto per produrre un confronto significativo.
- **FR-009**: Il sistema DEVE poter aggiornare la rappresentazione semantica di un evento già
  accettato quando arriva successivamente il testo derivato da audio/immagine.

### Key Entities

- **Evento salvato**: un evento normalizzato accettato dal sistema, con la sua rappresentazione
  semantica (quando disponibile) — usato come base per i confronti futuri.
- **Preferenze utente**: interessi, livello di approfondimento desiderato, che governano se e
  come vengono segnalati i collegamenti trovati.
- **Collegamento trovato**: un evento o progetto già salvato ritenuto pertinente rispetto a un
  nuovo contenuto, con un grado di pertinenza che ne determina la priorità di segnalazione.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Il sistema conferma la ricezione di un evento entro 2 secondi dall'arrivo, così
  da non far scattare i retry del modulo che lo invia.
- **SC-002**: Quando esiste un contenuto precedente chiaramente pertinente, il sistema lo trova
  e lo segnala in almeno l'80% dei casi verificati.
- **SC-003**: Nessun evento genera più di una segnalazione di collegamento per lo stesso evento,
  anche se ricevuto più volte.
- **SC-004**: Con una preferenza di approfondimento "minimo" impostata, il sistema non genera
  alcuna segnalazione nel 100% dei casi verificati.

## Assumptions

- Il testo su cui basare il confronto può arrivare subito (evento di tipo testo) o in un
  secondo momento tramite un aggiornamento da `pipeline` (audio/immagine); fino ad allora
  l'evento resta "in attesa" prima di poter essere confrontato semanticamente.
- Questa feature copre solo il flusso ingestion → core (ricezione, rappresentazione semantica,
  confronto, decisione di segnalazione). La costruzione del grafo di progetti/eventi collegati
  e il canale con cui la segnalazione arriva effettivamente all'utente sono responsabilità di
  feature successive (`graph`, `companion`), non di questa.
- Non è richiesta un'interfaccia utente diretta per questa feature: `core` è consumato da altri
  moduli tramite il contratto già definito in `API_CONTRACT.md`.
- Una soglia di pertinenza minima (sotto la quale un collegamento non viene proposto) è un
  dettaglio di calibrazione lasciato alla fase di pianificazione tecnica, non alla spec.
