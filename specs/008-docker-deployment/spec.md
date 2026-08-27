# Feature Specification: Infrastruttura di Deploy Containerizzata su ZimaBlade

**Feature Branch**: `008-docker-deployment`

**Created**: 2026-08-25

**Status**: Draft

**Input**: User description: "Infrastruttura di deploy containerizzata su ZimaBlade (Intel Celeron
quad-core x86, 16GB RAM, storage SATA) a sostituzione del deploy systemd su Raspberry Pi descritto
in DEPLOY.md. Ogni modulo (ingestion, pipeline, core, graph, companion) ha il proprio Dockerfile e
il proprio docker-compose.yml indipendente, così ciascuno può essere buildato, avviato, fermato e
riavviato senza toccare gli altri. Tutti i container si collegano a una rete Docker condivisa
esterna ai singoli compose, così i moduli si raggiungono tra loro per nome di servizio invece che
con localhost:porta. Volumi persistenti su storage SATA per i database di core e graph e per la
cache dei pesi dei modelli locali. Restart policy indipendente per servizio. Limiti di risorse sul
container di pipeline per non affamare gli altri servizi sulle 4 CPU disponibili. Variabili
d'ambiente per servizio via env_file, stesso schema di segreti già definito in DEPLOY.md."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Aggiornare un modulo senza toccare gli altri (Priority: P1)

Come operatore dell'unico nodo ZimaBlade, voglio poter ricostruire e riavviare un singolo modulo
(es. `core` dopo una modifica) senza fermare o ricostruire gli altri quattro, così posso rilasciare
un aggiornamento senza un'interruzione di servizio su tutta la pila.

**Why this priority**: È il motivo principale della containerizzazione modulare: oggi (systemd)
ogni modulo è già una unit indipendente, ma senza isolamento di ambiente/dipendenze. Perdere questa
indipendenza passando a Docker sarebbe un peggioramento, non un progresso.

**Independent Test**: Con tutti e cinque i moduli in esecuzione, ricostruire e riavviare solo il
container di `core`; verificare che `ingestion`, `pipeline`, `graph`, `companion` restino attivi e
raggiungibili per tutta l'operazione.

**Acceptance Scenarios**:

1. **Given** i cinque moduli in esecuzione, **When** l'operatore ricostruisce e riavvia il
   container di un modulo, **Then** gli altri quattro container restano in esecuzione e continuano
   a rispondere senza riavvio.
2. **Given** i cinque moduli in esecuzione, **When** l'operatore ferma il container di un modulo,
   **Then** solo quel modulo risulta non raggiungibile; gli altri rilevano l'assenza tramite i
   meccanismi di retry/backoff già esistenti nel codice, senza perdere eventi in ingresso.

---

### User Story 2 - Ripartenza automatica dopo un riavvio del nodo (Priority: P2)

Come operatore, dopo un riavvio (volontario o per crash) del nodo ZimaBlade, voglio che tutti e
cinque i moduli ripartano da soli, nell'ordine corretto per quanto possibile, senza dover avviare
manualmente ciascun container.

**Why this priority**: Oggi le unit `systemd` con `Restart=on-failure` + `enable` garantiscono
questa proprietà; passare a Docker senza equivalente sarebbe una regressione operativa per un
sistema personale che deve restare disponibile senza supervisione costante.

**Independent Test**: Riavviare l'host (o simulare con `docker stop` di tutti i container seguito
da riavvio del servizio Docker) e verificare che tutti e cinque i moduli tornino attivi entro un
tempo ragionevole senza comandi manuali.

**Acceptance Scenarios**:

1. **Given** il nodo ZimaBlade si riavvia, **When** il servizio Docker riparte, **Then** tutti i
   container configurati per l'avvio automatico tornano in esecuzione senza intervento manuale.
2. **Given** `core` e `graph` non sono ancora pronti a rispondere, **When** `ingestion` o
   `pipeline` provano a contattarli, **Then** i retry con backoff già presenti nel codice
   assorbono il ritardo senza perdere eventi (comportamento già esistente, solo da preservare).

---

### User Story 3 - Un carico pesante su pipeline non degrada gli altri moduli (Priority: P3)

Come operatore, voglio che un'elaborazione intensiva in `pipeline` (trascrizione/captioning con
modelli locali) non rallenti le risposte delle API di `core`, `graph` e `companion`, che girano
sullo stesso nodo a 4 CPU.

**Why this priority**: Diventa rilevante solo quando `pipeline` userà modelli locali (feature
successiva in questa migrazione); va comunque previsto ora nell'infrastruttura perché è
un'impostazione di deploy (limiti di risorse), non di codice applicativo.

**Independent Test**: Con tutti i moduli attivi, generare un carico CPU sostenuto nel container di
`pipeline` (es. un job di lunga durata) e verificare che le risposte di `core`/`graph`/`companion`
restino entro i tempi già definiti nelle rispettive spec (`002-core-similarity-engine`,
`003-knowledge-graph`, `005-core-search-history`).

**Acceptance Scenarios**:

1. **Given** un carico CPU sostenuto nel container `pipeline`, **When** un client interroga
   `core`/`graph`/`companion`, **Then** i tempi di risposta restano entro i budget già definiti
   nelle spec di quei moduli.

---

### Edge Cases

- Cosa succede se la rete Docker condivisa non esiste ancora quando si avvia il primo modulo? Deve
  esserci un passo di bootstrap esplicito e documentato (una sola volta, non per modulo).
- Cosa succede se il percorso SATA per i volumi persistenti non è ancora montato all'avvio del
  container? Il container non deve scrivere silenziosamente su storage temporaneo del container
  stesso (perdita dati al ricreare il container).
- Cosa succede se due moduli vengono avviati in ordine diverso da quello logico (es. `companion`
  prima di `graph`)? Deve restare non bloccante, coperto dai retry già presenti nel codice.
- Cosa succede se un segreto manca dall'`env_file` di un modulo all'avvio? Il modulo deve fallire
  in modo esplicito all'avvio (comportamento già esistente in ciascun `config.py`), non partire con
  valori di default silenziosi.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Ogni modulo (`ingestion`, `pipeline`, `core`, `graph`, `companion`) DEVE avere un
  proprio Dockerfile e un proprio file di composizione indipendente, costruibile e avviabile senza
  richiedere la ricostruzione o il riavvio degli altri moduli.
- **FR-002**: I moduli DEVONO potersi raggiungere tra loro tramite nome di servizio su una rete
  Docker condivisa, non tramite `localhost` o indirizzi IP hardcoded.
- **FR-003**: I dati che devono sopravvivere alla ricreazione di un container (database di `core` e
  `graph`, cache dei pesi dei modelli locali) DEVONO essere su volumi persistenti mappati su
  storage SATA, non sul filesystem effimero del container.
- **FR-004**: Ogni servizio DEVE avere una restart policy indipendente e appropriata al proprio
  ruolo (riavvio automatico per le API sempre attive e per il bot di ingestion; riavvio solo su
  fallimento per il worker `pipeline`).
- **FR-005**: Il container di `pipeline` DEVE avere limiti di CPU e memoria configurati, così un
  carico di elaborazione locale intensivo non riduce le risorse disponibili agli altri moduli sul
  nodo condiviso.
- **FR-006**: Ogni modulo DEVE ricevere segreti e configurazione tramite file di variabili
  d'ambiente esterno all'immagine, mai incluso nell'immagine stessa o nel repository.
- **FR-007**: L'operatore DEVE poter avviare, fermare o ricostruire un singolo modulo con un
  comando che coinvolge solo quel modulo, senza dover orchestrare l'intera pila in un unico
  comando.

### Key Entities

- **Rete Docker condivisa**: rete a cui tutti i container dei cinque moduli si collegano per
  comunicare tra loro per nome di servizio; creata una sola volta, indipendente dai singoli file di
  composizione.
- **Volume dati persistenti**: storage su SATA per i database SQLite/Postgres di `core` e `graph`,
  sopravvive alla ricreazione dei container.
- **Volume cache modelli**: storage su SATA per i pesi dei modelli locali (embedding in `core`,
  STT/captioning in `pipeline`), evita di riscaricarli ad ogni ricostruzione dell'immagine.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Un operatore può ricostruire e riavviare un singolo modulo mantenendo gli altri
  quattro disponibili per tutta l'operazione, senza alcuna interruzione osservabile dall'esterno
  sugli altri moduli.
- **SC-002**: Dopo un riavvio del nodo, tutti e cinque i moduli tornano operativi senza alcun
  comando manuale, entro pochi minuti (stesso ordine di grandezza già tollerato oggi dai retry con
  backoff tra moduli).
- **SC-003**: Nessun segreto (token, credenziali) compare nell'immagine Docker di alcun modulo né
  nel repository, verificabile ispezionando i layer dell'immagine.
- **SC-004**: Un carico sostenuto di elaborazione locale in `pipeline` non fa superare ai tempi di
  risposta di `core`, `graph` e `companion` i budget già definiti nelle rispettive spec.
- **SC-005**: I dati di `core` e `graph` sopravvivono alla rimozione e ricreazione di un container
  (es. dopo un aggiornamento immagine), verificabile ricreando il container e ritrovando gli stessi
  dati.

## Assumptions

- Docker Engine e il plugin Compose (v2) sono già installati sul nodo ZimaBlade; l'installazione
  del runtime Docker stesso è fuori scope per questa feature.
- Un solo host Docker (nessun orchestratore multi-nodo tipo Swarm/Kubernetes): coerente con "nodo
  unico" della constitution aggiornata.
- La scelta dei modelli locali concreti per embedding/STT/captioning (quali pesi, quale libreria)
  è fuori scope qui: questa feature fornisce solo l'infrastruttura (volume cache, limiti di
  risorse) che quelle feature successive useranno.
- Nessuna esposizione pubblica dei servizi: stesso modello di fiducia già documentato oggi (accesso
  solo da rete locale), la containerizzazione non cambia questo perimetro.
- Il file `DEPLOY.md` verrà riscritto per riflettere il nuovo deploy Docker, ma la sua riscrittura
  è parte dell'implementazione di questa feature, non uno use case separato.
