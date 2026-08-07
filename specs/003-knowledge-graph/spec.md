# Feature Specification: Grafo di Progetti ed Eventi Collegati

**Feature Branch**: `003-knowledge-graph`

**Created**: 2026-08-07

**Status**: Draft

**Input**: User description: "Grafo (graph) che riceve da core la creazione di nodi (progetto, nota, idea, persona, concetto) tramite POST /api/graph/nodes e di archi/relazioni pesate tra nodi tramite POST /api/graph/edges, secondo API_CONTRACT.md. Deve permettere di interrogare i nodi collegati a un nodo dato fino a una certa profondità tramite GET /api/graph/related/{node_id}, così che l'utente possa esplorare come le proprie note/progetti/idee sono collegati tra loro nel tempo. Ogni nodo mantiene un riferimento all'evento originale che lo ha generato."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Ogni contenuto salvato diventa un nodo esplorabile (Priority: P1)

Quando un contenuto rilevante (nota, progetto, idea, persona, concetto) viene individuato dal
resto del sistema, il grafo lo registra come nodo, mantenendo un riferimento a cosa lo ha
generato — così ogni pensiero dell'utente ha un posto stabile nel grafo, pronto per essere
collegato ad altri.

**Why this priority**: Senza nodi non c'è grafo: è la base su cui si costruisce tutto il resto.

**Independent Test**: Creare un nodo con tipo, etichetta e riferimento a un evento, poi
verificare che il nodo esista e mantenga quel riferimento.

**Acceptance Scenarios**:

1. **Given** un contenuto rilevante identificato altrove nel sistema, **When** viene richiesta
   la creazione di un nodo per quel contenuto, **Then** il grafo lo registra con il suo tipo,
   etichetta e riferimento all'evento originale.
2. **Given** un nodo è già stato creato per un certo evento originale, **When** viene richiesta
   di nuovo la creazione di un nodo per lo stesso evento, **Then** il grafo non crea un
   duplicato.

---

### User Story 2 - Le relazioni tra contenuti vengono registrate (Priority: P2)

Quando viene individuato un collegamento tra due contenuti già presenti nel grafo, questo viene
registrato come relazione pesata tra i due nodi corrispondenti — così le connessioni tra le
cose che l'utente ha scritto nel tempo non vanno perse.

**Why this priority**: Ha senso solo se esistono già nodi (US1); è il passo che rende il grafo
più di un semplice elenco.

**Independent Test**: Creare due nodi, poi creare una relazione tra loro con un tipo e un peso,
e verificare che la relazione risulti registrata in entrambe le direzioni della query di
esplorazione.

**Acceptance Scenarios**:

1. **Given** due nodi esistenti, **When** viene richiesta la creazione di una relazione tra
   loro con un tipo e un peso, **Then** il grafo la registra.
2. **Given** viene richiesta una relazione che coinvolge un nodo inesistente, **When** la
   richiesta arriva, **Then** il grafo la rifiuta con un errore chiaro, senza creare nulla.

---

### User Story 3 - Esplorazione dei collegamenti a partire da un nodo (Priority: P3)

L'utente (tramite l'app di consultazione) può partire da un nodo e vedere quali altri nodi gli
sono collegati, fino a una certa distanza — così può riscoprire come le proprie note, progetti
e idee si intrecciano nel tempo, anche collegamenti che non ricordava.

**Why this priority**: È il valore finale del grafo per l'utente, ma richiede che nodi e
relazioni esistano già (US1/US2).

**Independent Test**: A partire da un nodo con relazioni note fino a due passi di distanza,
interrogare i nodi collegati con profondità 1 e con profondità 2 e verificare che i risultati
corrispondano esattamente ai nodi attesi a ciascuna distanza.

**Acceptance Scenarios**:

1. **Given** un nodo con relazioni dirette verso altri nodi, **When** si interrogano i
   collegamenti con profondità 1, **Then** il grafo restituisce esattamente i nodi collegati
   direttamente, con tipo di relazione e peso.
2. **Given** un nodo senza alcuna relazione, **When** si interrogano i suoi collegamenti,
   **Then** il grafo restituisce un risultato vuoto, non un errore.
3. **Given** una profondità richiesta maggiore dell'estensione reale del grafo attorno al nodo,
   **When** si interroga, **Then** il grafo risponde comunque correttamente e in tempo utile,
   senza bloccarsi.

---

### Edge Cases

- Viene richiesta la creazione di una relazione che collega un nodo a sé stesso: non ha valore
  semantico in questo dominio e va rifiutata come una relazione verso un nodo inesistente.
- Arrivano richieste di creazione dello stesso nodo o della stessa relazione quasi
  contemporaneamente (doppio invio): non devono generare duplicati.
- Un nodo ha un numero molto alto di relazioni dirette: l'esplorazione a bassa profondità (1-2)
  deve restare rapida anche in questo caso.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Il sistema DEVE accettare la creazione di un nodo con tipo (progetto, nota, idea,
  persona, concetto), etichetta e riferimento all'evento originale che lo ha generato.
- **FR-002**: Il sistema DEVE evitare di creare più di un nodo per lo stesso evento originale
  (idempotenza sulla creazione dei nodi).
- **FR-003**: Il sistema DEVE accettare la creazione di una relazione pesata tra due nodi
  esistenti, con un tipo di relazione.
- **FR-004**: Il sistema DEVE rifiutare la creazione di una relazione se uno dei due nodi
  indicati non esiste, senza creare nulla.
- **FR-005**: Il sistema DEVE rifiutare la creazione di una relazione che collega un nodo a sé
  stesso.
- **FR-006**: Il sistema DEVE permettere di interrogare i nodi collegati a un nodo dato, fino a
  una profondità specificata nella richiesta.
- **FR-007**: Se un nodo non ha collegamenti (diretti o entro la profondità richiesta), il
  sistema DEVE restituire un risultato vuoto, non un errore.
- **FR-008**: Per ogni nodo collegato restituito, il sistema DEVE indicare il tipo di relazione
  e il peso rispetto al nodo di partenza.
- **FR-009**: Il sistema DEVE rispondere alle interrogazioni di esplorazione in un tempo utile
  anche quando la profondità richiesta eccede l'estensione reale del grafo attorno al nodo.

### Key Entities

- **Nodo**: rappresenta un progetto, nota, idea, persona o concetto — ha un tipo, un'etichetta
  e un riferimento all'evento originale che lo ha generato.
- **Relazione**: collega due nodi esistenti, con un tipo (es. "deriva da", "collegato a", "usa
  tecnologia di") e un peso che ne indica la forza/pertinenza.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: La creazione di un nodo o di una relazione viene confermata entro 1 secondo.
- **SC-002**: Interrogare i nodi collegati a un nodo con profondità 1 restituisce
  esattamente i nodi attesi (nessuno mancante, nessuno spurio) nel 100% dei casi verificati.
- **SC-003**: Nessun nodo duplicato viene creato per lo stesso evento originale, anche se la
  richiesta di creazione arriva più di una volta.
- **SC-004**: Le interrogazioni di esplorazione restano sotto 1 secondo di risposta anche su un
  grafo di alcune migliaia di nodi e relazioni.

## Assumptions

- Questa feature copre solo la costruzione e l'interrogazione del grafo (creazione di nodi/
  relazioni, esplorazione dei collegamenti). La decisione di *quali* nodi e relazioni creare a
  partire dai contenuti dell'utente è responsabilità di `core` (già specificata in una feature
  separata), non di questa.
- Non è richiesta un'interfaccia utente diretta qui: il grafo è consumato da altri moduli
  (`core` come scrittore, `companion` come lettore) tramite il contratto in `API_CONTRACT.md`.
- In questa fase non è richiesta la modifica o cancellazione di nodi/relazioni già creati: solo
  creazione e interrogazione.
- Le relazioni sono trattate come non orientate ai fini dell'esplorazione (FR-006): un
  collegamento creato da A verso B è visibile esplorando sia da A sia da B.
