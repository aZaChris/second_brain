# Feature Specification: Bot Telegram di Ingestion

**Feature Branch**: `001-ingestion-bot`

**Created**: 2026-08-07

**Status**: Draft

**Input**: User description: "Bot Telegram che riceve messaggi testo, audio, immagini da un utente autorizzato e li inoltra come evento normalizzato (tipo, contenuto, timestamp, utente) a un endpoint interno del backend (core), secondo il contratto POST /api/events definito in API_CONTRACT.md, gestendo errori di rete (retry con backoff) e conferma di ricezione all'utente."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Invio messaggio di testo (Priority: P1)

L'utente autorizzato scrive un messaggio di testo al bot Telegram. Il messaggio viene
normalizzato e inoltrato al backend; l'utente riceve conferma che è stato salvato.

**Why this priority**: È il flusso più semplice e più frequente d'uso: senza questo, il bot
non ha valore.

**Independent Test**: Inviare un messaggio di testo al bot e verificare che l'utente riceva
una risposta di conferma e che l'evento risulti ricevuto dal backend (`POST /api/events`
restituisce `201`).

**Acceptance Scenarios**:

1. **Given** l'utente è nella whitelist degli autorizzati, **When** invia un messaggio di
   testo, **Then** il bot inoltra un evento con `type: text` e conferma la ricezione
   all'utente.
2. **Given** il backend è raggiungibile, **When** l'evento viene inoltrato con successo,
   **Then** l'utente vede la conferma entro pochi secondi.

---

### User Story 2 - Invio messaggio audio o immagine (Priority: P2)

L'utente autorizzato invia un messaggio vocale o una foto. Il bot riconosce il tipo, salva un
riferimento al file e inoltra l'evento normalizzato, senza dover trascrivere o interpretare il
contenuto (compito di un altro modulo).

**Why this priority**: Valore aggiunto rispetto al solo testo, ma il sistema è già utile senza,
quindi priorità inferiore al flusso testo.

**Independent Test**: Inviare un messaggio audio (o una foto) al bot e verificare che l'evento
inoltrato abbia `type: audio` (o `image`) e un riferimento al file, non il contenuto binario
nel corpo della richiesta.

**Acceptance Scenarios**:

1. **Given** l'utente è autorizzato, **When** invia un messaggio vocale, **Then** il bot
   inoltra un evento con `type: audio` e `media_url` valorizzato, e conferma la ricezione.
2. **Given** l'utente è autorizzato, **When** invia una foto, **Then** il bot inoltra un evento
   con `type: image` e `media_url` valorizzato, e conferma la ricezione.

---

### User Story 3 - Gestione errori di rete verso il backend (Priority: P3)

Il backend (`core`) è temporaneamente irraggiungibile quando l'utente invia un messaggio. Il
bot riprova l'invio automaticamente; se fallisce definitivamente, avvisa l'utente che il
messaggio non è stato salvato, senza perderlo silenziosamente.

**Why this priority**: Migliora l'affidabilità ma non blocca l'uso base del bot nelle
condizioni normali (P1/P2 già coperte).

**Independent Test**: Simulare l'indisponibilità del backend, inviare un messaggio e verificare
che il bot ritenti con backoff e, in caso di fallimento persistente, notifichi l'utente.

**Acceptance Scenarios**:

1. **Given** il backend non risponde (timeout o `503`), **When** il bot inoltra l'evento,
   **Then** riprova con backoff fino a un numero massimo di tentativi prima di considerare il
   fallimento definitivo.
2. **Given** tutti i tentativi falliscono, **When** il fallimento è definitivo, **Then**
   l'utente riceve un messaggio che lo informa che l'invio non è andato a buon fine.

---

### Edge Cases

- Un utente non presente nella whitelist scrive al bot: il messaggio non deve essere inoltrato
  al backend.
- Il messaggio Telegram non ha contenuto riconoscibile (es. sticker, video, documento non
  supportato): il bot deve rispondere indicando che il tipo non è supportato, senza inoltrarlo
  come evento.
- Lo stesso messaggio viene recapitato due volte da Telegram (retry lato Telegram): il backend
  non deve creare due eventi duplicati per lo stesso messaggio originale.
- Il file audio/immagine supera una dimensione massima gestibile: il bot deve avvisare l'utente
  invece di tentare comunque l'inoltro.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Il sistema DEVE accettare messaggi solo da utenti presenti in una whitelist di
  utenti autorizzati e ignorare (o rifiutare esplicitamente) i messaggi di chiunque altro.
- **FR-002**: Il sistema DEVE riconoscere il tipo di ogni messaggio in arrivo tra testo, audio o
  immagine.
- **FR-003**: Il sistema DEVE normalizzare ogni messaggio riconosciuto in un evento con: fonte,
  utente, tipo, contenuto (testo) o riferimento al media (audio/immagine), timestamp.
- **FR-004**: Il sistema DEVE inoltrare ogni evento normalizzato all'endpoint interno del
  backend secondo il contratto `POST /api/events` definito in `API_CONTRACT.md`.
- **FR-005**: Il sistema DEVE confermare all'utente, nella chat Telegram, l'avvenuta ricezione e
  presa in carico del messaggio.
- **FR-006**: In caso di errore di rete o di indisponibilità del backend, il sistema DEVE
  ritentare l'invio dell'evento con backoff, fino a un numero massimo di tentativi, prima di
  considerare l'invio fallito.
- **FR-007**: Se l'invio fallisce in modo definitivo dopo i tentativi previsti, il sistema DEVE
  informare l'utente che il messaggio non è stato salvato, così che l'utente sappia di doverlo
  eventualmente reinviare.
- **FR-008**: Il sistema DEVE evitare di creare eventi duplicati quando Telegram recapita lo
  stesso messaggio più di una volta (idempotenza sull'identificativo del messaggio originale).
- **FR-009**: Il sistema DEVE rispondere all'utente con un messaggio chiaro quando riceve un
  tipo di contenuto non supportato (es. sticker, video, documenti generici), senza inoltrarlo
  come evento.

### Key Entities

- **Messaggio Telegram in ingresso**: messaggio grezzo ricevuto dal bot — utente mittente, tipo
  di contenuto, testo o riferimento al file, identificativo del messaggio Telegram, timestamp
  di arrivo.
- **Evento normalizzato**: rappresentazione unificata inoltrata al backend — sorgente
  (`telegram`), utente, tipo (`text`/`audio`/`image`), contenuto o `media_url`, timestamp,
  secondo lo schema di `API_CONTRACT.md`.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Un utente autorizzato riceve conferma di ricezione entro 5 secondi dall'invio di
  un messaggio di testo, in condizioni di rete normali.
- **SC-002**: Il 100% dei messaggi provenienti da utenti non autorizzati viene bloccato e non
  genera alcun evento verso il backend.
- **SC-003**: In caso di indisponibilità del backend più breve di 1 minuto, almeno il 95% degli
  eventi viene recapitato automaticamente tramite retry, senza intervento manuale dell'utente.
- **SC-004**: Nessun evento va perso silenziosamente: ogni fallimento definitivo di invio
  produce una notifica visibile all'utente entro la stessa sessione di chat.

## Assumptions

- Esiste un solo utente autorizzato (uso personale del Second Brain) o una whitelist statica di
  pochi utenti, configurata tramite variabile d'ambiente — non è richiesto un sistema di
  registrazione/autenticazione multi-utente.
- Il canale coperto da questa feature è Telegram; l'integrazione con WhatsApp (citata nella
  visione generale del progetto) è fuori scope e sarà una feature separata.
- Per audio e immagini, il bot carica il file su uno storage raggiungibile da `core`/`pipeline`
  e ne passa solo il riferimento (`media_url`), come previsto da `API_CONTRACT.md`; il dettaglio
  di dove risieda questo storage è una decisione implementativa lasciata al piano.
- Retry con backoff esponenziale e un numero massimo di 3 tentativi è lo standard adottato,
  salvo diversa indicazione in fase di pianificazione tecnica.
