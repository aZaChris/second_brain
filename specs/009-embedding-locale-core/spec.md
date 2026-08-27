# Feature Specification: Embedding Locale in Core

**Feature Branch**: `009-embedding-locale-core`

**Created**: 2026-08-25

**Status**: Draft

**Input**: User description: "Il modulo core genera l'embedding del testo di ogni evento con un
modello locale (es. sentence-transformers multilingue leggero) eseguito in-process, invece di
chiamare un servizio HTTP esterno. L'interfaccia embed(text) -> list[float] resta invariata verso
il resto del modulo (similarity.py, api.py non cambiano). Nessun dato testuale dell'utente lascia
il nodo per generare l'embedding. Il modello e i suoi pesi sono caricati una volta all'avvio del
processo core, non per singola richiesta. I pesi del modello sono cache su un volume persistente
(models-cache/core, già predisposto dalla feature Docker 008) così non si riscaricano ad ogni
riavvio del container. Questa è la ripianificazione di 002-core-similarity-engine alla luce della
migrazione da Raspberry Pi a ZimaBlade e del nuovo Principio IV della constitution (v2.0.0): il
servizio esterno di embedding resta disponibile come alternativa documentata solo se la qualità
del modello locale risultasse insufficiente."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Nessun testo personale lascia il nodo (Priority: P1)

Come utente del sistema, voglio che il testo delle mie note (spesso personali) non venga inviato a
nessun servizio esterno per calcolarne l'embedding, così la mia privacy non dipende dalla policy di
un provider terzo.

**Why this priority**: È il beneficio primario di questa feature (Principio I e IV della
constitution) — senza questa proprietà, la feature non ha motivo di esistere rispetto alla
soluzione precedente.

**Independent Test**: Inviare un evento testuale e osservare il traffico di rete in uscita dal
processo `core` durante la sua elaborazione: nessuna richiesta deve raggiungere l'endpoint del
servizio di embedding esterno precedentemente configurato.

**Acceptance Scenarios**:

1. **Given** un evento testuale ricevuto da `core`, **When** il sistema genera il suo embedding,
   **Then** nessuna chiamata di rete verso un servizio esterno di embedding viene effettuata.
2. **Given** il servizio esterno di embedding precedentemente in uso è irraggiungibile o non
   configurato, **When** un evento testuale viene elaborato, **Then** l'embedding viene comunque
   generato correttamente (nessuna dipendenza residua dal servizio esterno per il percorso
   predefinito).

---

### User Story 2 - Stessa reattività di oggi (Priority: P2)

Come utente, voglio continuare a vedere i collegamenti tra le mie note confermati rapidamente
(entro pochi secondi) anche se l'embedding ora viene calcolato localmente invece che da un servizio
esterno più potente.

**Why this priority**: Il cambiamento non deve introdurre una regressione percepibile
sull'esperienza già garantita da `002-core-similarity-engine` (SC-001: conferma entro 2s).

**Independent Test**: Inviare un evento testuale tipico (nota breve) e misurare il tempo totale
dall'invio alla disponibilità del suo embedding nel sistema.

**Acceptance Scenarios**:

1. **Given** un evento testuale di lunghezza tipica (poche centinaia di caratteri), **When** viene
   elaborato, **Then** l'embedding è disponibile entro lo stesso budget di tempo già garantito
   oggi, senza bloccare la risposta HTTP di creazione evento (elaborazione in background,
   invariata).

---

### User Story 3 - Nessun ri-download dei pesi ad ogni riavvio (Priority: P3)

Come operatore, voglio che un riavvio del processo `core` non richieda di riscaricare i pesi del
modello da internet ogni volta, così il servizio torna operativo rapidamente anche senza
connettività o con rete lenta.

**Why this priority**: Rilevante per l'affidabilità operativa quotidiana, ma non blocca il valore
primario della feature (privacy) se risolta in un secondo momento.

**Independent Test**: Riavviare il processo `core` con la cache dei pesi già popolata da un avvio
precedente e verificare che nessun download di rete avvenga durante l'avvio.

**Acceptance Scenarios**:

1. **Given** i pesi del modello già presenti nella cache persistente da un avvio precedente,
   **When** il processo `core` riparte, **Then** nessun download dei pesi avviene e il servizio
   diventa pronto a rispondere senza attese aggiuntive legate al download.

---

### Edge Cases

- Cosa succede se nel database esistono già eventi con embedding generati dal precedente servizio
  esterno, con una dimensionalità del vettore diversa da quella del modello locale? La ricerca per
  similarità non deve confrontare vettori di dimensioni incompatibili né fallire con un errore non
  gestito.
- Cosa succede se il testo di un evento è vuoto o sotto la soglia minima già gestita oggi
  (`is_low_signal`)? Comportamento invariato: nessun embedding generato, stesso di oggi.
- Cosa succede se i pesi del modello non sono ancora presenti nella cache al primo avvio in
  assoluto (nessuna connettività di rete disponibile in quel momento)? Il processo deve segnalare
  chiaramente l'impossibilità di avviarsi, non degradare silenziosamente.
- Cosa succede se il testo è molto più lungo della media (es. una nota lunga)? Il tempo di
  generazione dell'embedding può crescere, ma resta un'elaborazione in background che non blocca
  la risposta di creazione evento (comportamento invariato).

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Il sistema DEVE generare l'embedding del testo di un evento tramite un modello
  eseguito in-process sul nodo, senza effettuare chiamate di rete verso servizi esterni per questo
  calcolo, quando configurato in modalità locale (default).
- **FR-002**: L'interfaccia di generazione dell'embedding DEVE restare compatibile con il resto del
  modulo (stesso input testuale, stesso output vettoriale) così i componenti che la usano non
  richiedono modifiche.
- **FR-003**: Il modello e i suoi pesi DEVONO essere caricati una sola volta all'avvio del
  processo, non ad ogni richiesta di embedding.
- **FR-004**: I pesi del modello DEVONO essere letti da una cache persistente tra i riavvii del
  processo; se assenti, DEVONO essere scaricati una sola volta e salvati in quella cache.
- **FR-005**: Il sistema DEVE continuare a supportare, come alternativa configurabile, un servizio
  esterno di embedding, per il caso in cui la qualità del modello locale risulti insufficiente
  (documentata, non attiva di default).
- **FR-006**: Il sistema DEVE evitare di confrontare per similarità embedding di dimensionalità
  diversa tra loro (es. generati da provider/modelli diversi in momenti diversi), senza causare
  errori non gestiti nella ricerca o nella segnalazione di collegamenti.
- **FR-007**: Il sistema DEVE continuare a non inviare il testo di un evento a nessuna
  destinazione (esterna o interna) diversa da quelle già prevista oggi per il suo funzionamento,
  quando l'embedding è generato localmente.

### Key Entities

- **Modello di embedding locale**: modello eseguito in-process, caratterizzato dai pesi (cache
  persistente) e dalla dimensionalità del vettore che produce; sostituisce la chiamata al servizio
  esterno mantenendo lo stesso ruolo nel sistema.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Il 100% delle richieste di generazione embedding non genera traffico di rete verso
  servizi esterni, verificabile osservando il traffico in uscita dal processo `core` durante
  l'elaborazione di un evento.
- **SC-002**: Il tempo di generazione dell'embedding per un testo tipico (nota breve) resta entro
  il budget già garantito oggi per la conferma dei collegamenti (entro 2s dalla ricezione
  dell'evento, elaborazione in background che non blocca la risposta HTTP).
- **SC-003**: Con i pesi già presenti in cache, un riavvio del processo `core` non genera alcun
  download di rete legato al modello.
- **SC-004**: Nessun testo di un evento utente compare in log di traffico di rete in uscita verso
  destinazioni esterne durante la generazione del suo embedding.

## Assumptions

- Il nodo ZimaBlade ha risorse sufficienti (CPU, RAM) per eseguire un modello di embedding leggero
  in-process, come già stabilito dal Principio IV della constitution (v2.0.0).
- La cache persistente dei pesi del modello (volume `models-cache/core`) è già disponibile grazie
  alla feature `008-docker-deployment`; questa feature la usa, non la crea.
- Se esistono già eventi salvati con embedding generati dal precedente servizio esterno (dimensioni
  diverse dal nuovo modello locale), la loro rigenerazione (backfill) è un'attività operativa
  separata, fuori scope per questa feature: qui si richiede solo che il sistema non fallisca in
  modo non gestito di fronte a quella situazione (FR-006).
- Il modello locale concreto (quale libreria, quali pesi) è una decisione di implementazione,
  demandata alla fase di pianificazione (`/speckit-plan`), non a questa specifica.
