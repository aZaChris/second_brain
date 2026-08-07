# Feature Specification: Trascrizione Audio e Captioning Immagini (Pipeline)

**Feature Branch**: `006-pipeline-transcription-captioning`

**Created**: 2026-08-07

**Status**: Draft

**Input**: User description: "Modulo pipeline che individua gli eventi audio/immagine salvati ancora privi di testo, trascrive i messaggi vocali e genera una descrizione delle immagini tramite servizi esterni, e invia il risultato a core secondo PATCH /api/events/{event_id} già definito in API_CONTRACT.md, gestendo file non più raggiungibili e indisponibilità temporanea dei servizi esterni."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Trascrizione dei messaggi vocali (Priority: P1)

Un messaggio vocale inviato dall'utente viene trascritto in testo, così il suo contenuto
diventa ricercabile e collegabile al resto del Second Brain esattamente come una nota scritta.

**Why this priority**: Senza trascrizione, tutto il contenuto vocale resta "cieco" per il
resto del sistema (ricerca, collegamenti) — è il caso d'uso più diretto di `pipeline`.

**Independent Test**: Salvare un evento vocale, attendere l'elaborazione, e verificare che
l'evento risulti aggiornato con una trascrizione testuale coerente col contenuto audio.

**Acceptance Scenarios**:

1. **Given** un evento vocale salvato senza ancora testo, **When** `pipeline` lo elabora,
   **Then** il testo trascritto viene associato a quell'evento.
2. **Given** un evento vocale già trascritto in precedenza, **When** `pipeline` lo incontra di
   nuovo, **Then** non lo ritrascrive una seconda volta.

---

### User Story 2 - Descrizione delle immagini (Priority: P2)

Una foto inviata dall'utente viene descritta in testo, così anche il contenuto visivo diventa
ricercabile e collegabile come il resto delle note.

**Why this priority**: Stesso valore della trascrizione ma per un tipo di contenuto meno
frequente nell'uso tipico di un Second Brain personale.

**Independent Test**: Salvare un evento immagine, attendere l'elaborazione, e verificare che
l'evento risulti aggiornato con una descrizione testuale coerente col contenuto dell'immagine.

**Acceptance Scenarios**:

1. **Given** un evento immagine salvato senza ancora testo, **When** `pipeline` lo elabora,
   **Then** una descrizione testuale viene associata a quell'evento.
2. **Given** un evento immagine già descritto in precedenza, **When** `pipeline` lo incontra di
   nuovo, **Then** non lo ridescrive una seconda volta.

---

### User Story 3 - Gestione di file non raggiungibili o servizi esterni non disponibili (Priority: P3)

Se il file audio/immagine non è più raggiungibile, o il servizio esterno di
trascrizione/captioning non risponde, l'evento non viene perso: `pipeline` segnala chiaramente
il problema o riprova, invece di far sparire silenziosamente quel contenuto.

**Why this priority**: Migliora l'affidabilità ma non blocca il valore base delle prime due
user story nelle condizioni normali.

**Independent Test**: Simulare un file non raggiungibile e un servizio esterno che non
risponde, ed verificare che in entrambi i casi l'evento resti tracciabile come "non riuscito",
non semplicemente ignorato.

**Acceptance Scenarios**:

1. **Given** il file referenziato da un evento non è più raggiungibile, **When** `pipeline`
   prova a elaborarlo, **Then** l'evento viene segnalato come non elaborabile, non perso o
   ignorato silenziosamente.
2. **Given** il servizio esterno di trascrizione/captioning non risponde temporaneamente,
   **When** `pipeline` prova a elaborare un evento, **Then** riprova prima di considerare il
   fallimento definitivo.

---

### Edge Cases

- Un evento ha un tipo diverso da audio/immagine (es. testo): `pipeline` non deve tentare di
  elaborarlo.
- Un file audio è troppo lungo o un'immagine troppo pesante per il servizio esterno usato:
  `pipeline` deve segnalarlo come non elaborabile, non bloccarsi.
- Due elaborazioni dello stesso evento partono quasi in contemporanea (es. per un riavvio):
  non devono produrre due trascrizioni/descrizioni in conflitto per lo stesso evento.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Il sistema DEVE individuare gli eventi di tipo audio o immagine ancora privi di
  una trascrizione/descrizione testuale.
- **FR-002**: Il sistema DEVE trascrivere in testo il contenuto di un evento audio.
- **FR-003**: Il sistema DEVE generare una descrizione testuale del contenuto di un evento
  immagine.
- **FR-004**: Il sistema DEVE associare il testo risultante (trascrizione o descrizione)
  all'evento originale, secondo il contratto già esistente tra `pipeline` e `core`.
- **FR-005**: Il sistema DEVE evitare di rielaborare un evento che ha già una trascrizione o
  descrizione associata.
- **FR-006**: Se il file referenziato da un evento non è più raggiungibile, il sistema DEVE
  segnalarlo come non elaborabile, senza farlo sparire silenziosamente dal sistema.
- **FR-007**: Se il servizio esterno di trascrizione/captioning non risponde temporaneamente,
  il sistema DEVE ritentare prima di considerare il fallimento definitivo.
- **FR-008**: Il sistema DEVE usare servizi esterni per trascrizione e captioning, non modelli
  pesanti eseguiti localmente.
- **FR-009**: Il sistema DEVE elaborare solo eventi di tipo audio o immagine, ignorando gli
  eventi di tipo testo.

### Key Entities

- **Evento in attesa di elaborazione**: un evento audio/immagine salvato ma ancora privo di
  trascrizione/descrizione.
- **Risultato di elaborazione**: il testo prodotto (trascrizione o descrizione), con eventuali
  metadati (es. servizio/modello usato) da associare all'evento originale.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Un messaggio vocale risulta trascritto entro pochi minuti dal salvataggio
  dell'evento, in condizioni normali.
- **SC-002**: Un'immagine risulta descritta entro pochi minuti dal salvataggio dell'evento, in
  condizioni normali.
- **SC-003**: Nessun evento viene trascritto o descritto più di una volta, verificato nel 100%
  dei casi.
- **SC-004**: Nessun evento audio/immagine resta bloccato indefinitamente senza un esito
  (trascritto/descritto, o segnalato come non elaborabile) — verificato nel 100% dei casi in
  presenza di file irraggiungibili o servizio esterno non disponibile.

## Assumptions

- Questa feature presuppone un modo per `pipeline` di scoprire gli eventi audio/immagine in
  attesa (con relativo riferimento al file) e di aggiornarne lo stato una volta elaborati.
  `API_CONTRACT.md` oggi espone solo `PATCH /api/events/{event_id}` (invio del risultato), non
  un endpoint per *scoprire* cosa è ancora da elaborare: gli endpoint di lettura già esistenti
  (`005-core-search-history`) sono pensati per `companion` e non restituiscono `media_url` né
  permettono di filtrare per "da elaborare". Sarà necessaria una feature/estensione dedicata su
  `core` (analoga a quanto fatto per sbloccare `companion`) prima che questa feature possa
  essere implementata per intero.
- Il riferimento al file (`media_url`) potrebbe avere una finestra di validità limitata (es.
  URL temporanei lato provider di messaggistica, già annotato come limite noto
  nell'implementazione di `ingestion`): questa feature tratta un file non più raggiungibile
  come edge case da segnalare (FR-006), non come garanzia di disponibilità permanente.
- Non è richiesta un'interfaccia utente diretta: `pipeline` è un processo di background,
  coordinato tramite il contratto tra moduli.
