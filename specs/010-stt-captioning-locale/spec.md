# Feature Specification: STT e Captioning Locali in Pipeline

**Feature Branch**: `010-stt-captioning-locale`

**Created**: 2026-08-25

**Status**: Draft

**Input**: User description: "Il modulo pipeline trascrive audio e descrive immagini con modelli
locali leggeri (es. faster-whisper per STT, un modello di captioning compatto) eseguiti
in-process, invece di chiamare servizi HTTP esterni, mantenendo il budget di elaborazione già
definito in 006-pipeline-transcription-captioning (trascrizione entro pochi minuti dall'evento).
Le interfacce transcribe()/caption() restano compatibili verso worker.py (stesso input bytes,
stesso output testo). I pesi dei modelli sono cache su un volume persistente
(models-cache/pipeline, già predisposto dalla feature Docker 008), caricati una sola volta
all'avvio del processo, non per singola richiesta — stesso pattern già usato per l'embedding
locale in core (009-embedding-locale-core). Il container pipeline ha già limiti di CPU/RAM
(008-docker-deployment) per non affamare gli altri moduli durante l'inferenza. Questa è la
ripianificazione di 006-pipeline-transcription-captioning alla luce della migrazione da Raspberry
Pi a ZimaBlade e del Principio IV della constitution (v2.0.0): i servizi esterni di
STT/captioning restano disponibili come alternativa documentata solo se la qualità o i tempi dei
modelli locali risultassero insufficienti per un tipo di file."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Nessun file audio o immagine lascia il nodo (Priority: P1)

Come utente del sistema, voglio che i miei file audio (note vocali) e immagini (spesso personali)
non vengano inviati a nessun servizio esterno per essere trascritti o descritti, così la mia
privacy non dipende dalla policy di un provider terzo.

**Why this priority**: È il beneficio primario di questa feature (Principio I e IV della
constitution), stesso ordine di importanza già stabilito per l'embedding locale in
`009-embedding-locale-core`.

**Independent Test**: Inviare un evento audio e un evento immagine, osservare il traffico di rete
in uscita dal processo `pipeline` durante la loro elaborazione: nessuna richiesta deve raggiungere
un servizio esterno di STT/captioning precedentemente configurato.

**Acceptance Scenarios**:

1. **Given** un evento audio in attesa di trascrizione, **When** `pipeline` lo elabora, **Then**
   nessuna chiamata di rete verso un servizio esterno di STT viene effettuata.
2. **Given** un evento immagine in attesa di descrizione, **When** `pipeline` lo elabora, **Then**
   nessuna chiamata di rete verso un servizio esterno di captioning viene effettuata.
3. **Given** i servizi esterni precedentemente in uso sono irraggiungibili o non configurati,
   **When** un evento audio o immagine viene elaborato, **Then** la trascrizione/descrizione
   avviene comunque correttamente (nessuna dipendenza residua dai servizi esterni per il percorso
   predefinito).

---

### User Story 2 - Stesso tempo di elaborazione di oggi (Priority: P2)

Come utente, voglio continuare a vedere le mie note vocali trascritte e le mie immagini descritte
entro pochi minuti, come già garantito oggi, anche se l'elaborazione ora avviene localmente
invece che tramite un servizio esterno più potente.

**Why this priority**: Il cambiamento non deve introdurre una regressione percepibile
sull'esperienza già garantita da `006-pipeline-transcription-captioning`.

**Independent Test**: Inviare un evento audio (nota vocale tipica) e un evento immagine (foto
singola) e misurare il tempo dalla ricezione alla disponibilità del testo trascritto/descritto.

**Acceptance Scenarios**:

1. **Given** un evento audio di durata tipica (nota vocale personale, non una registrazione
   lunga), **When** viene elaborato, **Then** la trascrizione è disponibile entro lo stesso
   budget di tempo già garantito oggi (pochi minuti).
2. **Given** un evento immagine tipico (una foto), **When** viene elaborato, **Then** la
   descrizione è disponibile entro lo stesso budget di tempo già garantito oggi.

---

### User Story 3 - Nessun ri-download dei pesi ad ogni riavvio (Priority: P3)

Come operatore, voglio che un riavvio del processo `pipeline` non richieda di riscaricare i pesi
dei modelli di STT e captioning ogni volta, così il servizio torna operativo rapidamente anche
senza connettività o con rete lenta.

**Why this priority**: Rilevante per l'affidabilità operativa quotidiana, stesso ordine di
priorità già stabilito per l'embedding locale in `009-embedding-locale-core`.

**Independent Test**: Riavviare il processo `pipeline` con la cache dei pesi già popolata da un
avvio precedente e verificare che nessun download di rete avvenga durante l'avvio.

**Acceptance Scenarios**:

1. **Given** i pesi dei modelli già presenti nella cache persistente da un avvio precedente,
   **When** il processo `pipeline` riparte, **Then** nessun download dei pesi avviene.

---

### Edge Cases

- Cosa succede se un file audio è insolitamente lungo rispetto a una nota vocale tipica? Il tempo
  di elaborazione locale può crescere in modo significativo rispetto a un servizio esterno più
  potente — resta un'elaborazione asincrona che non blocca altri eventi in coda, ma potrebbe
  avvicinarsi o superare il budget di "pochi minuti" per quel singolo file.
- Cosa succede se la trascrizione o la descrizione locale produce un risultato vuoto (es. audio
  silenzioso, immagine non descrivibile)? Stesso comportamento già esistente: fallimento gestito
  con `PATCH` e testo segnaposto, l'evento non resta bloccato in coda (invariato da
  `006-pipeline-transcription-captioning`).
- Cosa succede se entrambi i modelli locali (STT e captioning) sono caricati in memoria
  contemporaneamente nello stesso processo? Devono restare entro i limiti di CPU/RAM già
  assegnati al container `pipeline` (`008-docker-deployment`).
- Cosa succede se il file audio o immagine è in un formato non supportato dal modello locale?
  Deve essere trattato come un fallimento gestito (stesso pattern del punto sopra), non un errore
  non gestito che blocca il worker.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Il sistema DEVE trascrivere un file audio tramite un modello eseguito in-process sul
  nodo, senza effettuare chiamate di rete verso servizi esterni, quando configurato in modalità
  locale (default).
- **FR-002**: Il sistema DEVE descrivere un'immagine tramite un modello eseguito in-process sul
  nodo, senza effettuare chiamate di rete verso servizi esterni, quando configurato in modalità
  locale (default).
- **FR-003**: Le interfacce di trascrizione e di descrizione immagine DEVONO restare compatibili
  con il resto del modulo (stesso input binario, stesso output testuale) così i componenti che le
  usano non richiedono modifiche.
- **FR-004**: I modelli locali (STT e captioning) DEVONO essere caricati una sola volta all'avvio
  del processo, non ad ogni richiesta di trascrizione/descrizione.
- **FR-005**: I pesi dei modelli locali DEVONO essere letti da una cache persistente tra i
  riavvii del processo; se assenti, DEVONO essere scaricati una sola volta e salvati in quella
  cache.
- **FR-006**: Il sistema DEVE continuare a supportare, indipendentemente per audio e per
  immagini, un servizio esterno come alternativa configurabile, per il caso in cui la qualità o i
  tempi del modello locale corrispondente risultino insufficienti.
- **FR-007**: Un fallimento nella trascrizione o descrizione locale (risultato vuoto, formato non
  supportato, errore del modello) DEVE seguire lo stesso comportamento di gestione fallimenti già
  esistente (segnalazione tramite il meccanismo già in uso, l'evento non resta bloccato
  indefinitamente in coda).
- **FR-008**: Il sistema NON DEVE inviare il contenuto di un file audio o immagine a nessuna
  destinazione diversa da quelle già previste oggi per il suo funzionamento, quando l'elaborazione
  è locale.

### Key Entities

- **Modello locale di trascrizione (STT)**: modello eseguito in-process, caratterizzato dai pesi
  (cache persistente) e dai formati audio supportati; sostituisce la chiamata al servizio esterno
  mantenendo lo stesso ruolo nel sistema.
- **Modello locale di captioning**: modello eseguito in-process, caratterizzato dai pesi (cache
  persistente) e dai formati immagine supportati; sostituisce la chiamata al servizio esterno
  mantenendo lo stesso ruolo nel sistema.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Il 100% delle trascrizioni e delle descrizioni immagine non genera traffico di rete
  verso servizi esterni, verificabile osservando il traffico in uscita dal processo `pipeline`
  durante l'elaborazione.
- **SC-002**: Il tempo di elaborazione per un file audio o immagine tipico resta entro lo stesso
  budget già garantito oggi (pochi minuti dalla ricezione dell'evento).
- **SC-003**: Con i pesi già presenti in cache, un riavvio del processo `pipeline` non genera
  alcun download di rete legato ai modelli.
- **SC-004**: Nessun contenuto di file audio o immagine utente compare in log di traffico di rete
  in uscita verso destinazioni esterne durante l'elaborazione locale.

## Assumptions

- Il nodo ZimaBlade ha risorse sufficienti (CPU, RAM) per eseguire entrambi i modelli locali (STT
  e captioning) in-process nello stesso processo `pipeline`, entro i limiti di CPU/RAM già
  assegnati al container (`008-docker-deployment`), come già stabilito dal Principio IV della
  constitution (v2.0.0).
- La cache persistente dei pesi dei modelli (volume `models-cache/pipeline`) è già disponibile
  grazie alla feature `008-docker-deployment`; questa feature la usa, non la crea.
- Il volume e la tipologia di file (note vocali brevi, singole immagini, uso personale) restano
  gli stessi già assunti da `006-pipeline-transcription-captioning` — questa feature cambia come
  vengono elaborati, non la scala del sistema.
- I modelli locali concreti (quali librerie, quali pesi, per STT e per captioning
  indipendentemente) sono una decisione di implementazione, demandata alla fase di pianificazione
  (`/speckit-plan`), non a questa specifica.
