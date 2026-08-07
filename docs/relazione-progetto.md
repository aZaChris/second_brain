# Second Brain — Relazione di Progetto

**Data**: 2026-08-07
**Repo**: [github.com/aZaChris/second_brain](https://github.com/aZaChris/second_brain)

---

## 1. Visione

Second Brain è un sistema personale di cattura, indicizzazione e ricerca di appunti/eventi.
L'utente invia pensieri (testo, audio, immagini) tramite un bot Telegram; il sistema li
trascrive/descrive se serve, li rende ricercabili per significato, individua collegamenti con
quanto già salvato in passato e li organizza in un grafo di progetti/note/idee collegate. Un
Raspberry Pi 4B fa da nodo di ingestion (e, nel setup scelto, ospita l'intero stack).

Il progetto è organizzato come **monorepo a 5 moduli indipendenti**, ciascuno con la propria
`README.md`, dipendenze isolate e test, sviluppati con il metodo Speckit
(`/speckit-constitution → /speckit-specify → /speckit-plan → /speckit-tasks → /speckit-implement`):
ogni feature ha una cartella in `specs/` con `spec.md` (cosa e perché), `plan.md`/`research.md`
(come, con le alternative scartate motivate), `tasks.md` (checklist eseguita) e `quickstart.md`
(scenari di validazione).

## 2. Principi guida (constitution v1.1.0)

Definiti in `.specify/memory/constitution.md`, hanno guidato ogni scelta tecnica:

1. **Privacy-first** — nessuno storage di dati non necessario; ogni modulo salva solo ciò che
   gli serve per il proprio compito.
2. **Modularità** — ogni modulo comunica con gli altri solo attraverso `API_CONTRACT.md`, mai
   tramite dettagli interni condivisi.
3. **API testabili indipendentemente** — ogni modulo si testa senza dover avere gli altri in
   esecuzione (servizi esterni e moduli terzi sempre mockabili).
4. **Servizi esterni preferiti a modelli locali pesanti** — LLM/STT/captioning delegati ad API
   esterne, mai modelli eseguiti localmente (in particolare sul Raspberry Pi).
5. **Regola di processo**: ogni sessione di lavoro con un coding agent termina con un
   riepilogo; ogni commit rilevante aggiorna `CHANGELOG.md`, il documento condiviso sempre
   visibile a entrambi i collaboratori.

A queste si è aggiunto un criterio pratico applicato sistematicamente nelle scelte tecniche
(pattern "ponytail"): niente coda/broker, niente ORM, niente libreria dedicata quando poche
righe di stdlib bastano — introdotti solo se il volume reale lo giustificherà.

## 3. Architettura: i 5 moduli

```
ingestion ──POST/PATCH /api/events──▶ core ──POST /api/graph/{nodes,edges}──▶ graph
                                        ▲                                      ▲
pipeline ──GET /pending, PATCH────────┘                                      │
                                                                               │
companion ──GET /api/graph/related────────────────────────────────────────────┘
companion ──GET /api/events/{search,·}────▶ core   (US1/US3 non ancora implementate)
```

Il contratto completo, con schema di request/response per ogni endpoint, è in
`API_CONTRACT.md` (8 sezioni). È stato esteso due volte durante lo sviluppo (sempre in modo
additivo, mai rompendo un endpoint esistente) quando `companion` e `pipeline` si sono rivelati
avere bisogno di endpoint di lettura che `core` non esponeva ancora.

### 3.1 `ingestion` — bot Telegram

**Cosa fa**: riceve messaggi testo/audio/immagine da utenti in whitelist, li normalizza e li
inoltra a `core`. Long polling (niente webhook pubblico, il Pi è dietro NAT). Retry a backoff
esponenziale sulle chiamate a `core`, deduplica sui doppi recapiti Telegram, notifica l'utente
se il salvataggio fallisce.

**Stack**: Python 3.11+, `python-telegram-bot`, `httpx`. Nessun database proprio.

**Stato**: ✅ completo (spec `001-ingestion-bot`), **12 test** verdi. Nota tecnica aperta: il
`media_url` per audio/immagine è oggi l'URL temporaneo servito da Telegram (scade dopo un po')
— da sostituire con un upload su storage condiviso quando il volume lo richiederà.

### 3.2 `pipeline` — trascrizione e captioning

**Cosa fa**: worker in background (nessun server HTTP proprio) che interroga periodicamente
`core` per sapere quali eventi audio/immagine aspettano ancora un testo, li scarica, li
trascrive/descrive tramite servizi esterni, e rimanda il risultato a `core`. Se il file non è
raggiungibile o il servizio esterno resta giù dopo i retry, l'evento non resta bloccato: riceve
comunque un aggiornamento con un testo segnaposto e uno stato di fallimento visibile, senza
inventare un endpoint dedicato solo per quello.

**Stack**: Python 3.11+, `httpx`. Nessun database proprio.

**Stato**: ✅ completo (spec `006-pipeline-transcription-captioning`), **15 test** verdi.
Richiede una feature dedicata su `core` (`007-core-pending-events`) per sapere cosa elaborare —
implementata prima di questa, proprio per questo.

### 3.3 `core` — motore di similarità e API principale

**Cosa fa**: è il cuore del sistema. Riceve gli eventi normalizzati, ne genera una
rappresentazione semantica (embedding, via servizio esterno), confronta ogni nuovo contenuto con
quanto già salvato e decide se segnalare un collegamento in base alle preferenze dell'utente.
Espone anche ricerca semantica e cronologia paginata dei contenuti (per `companion`) e la lista
degli eventi audio/immagine ancora da trascrivere (per `pipeline`).

**Storage**: SQLite, nessun ORM, nessun database esterno — il volume (uso personale) non lo
giustifica. Similarità calcolata in-process con `numpy` (cosine similarity), nessun vector
database dedicato.

**Endpoint esposti** (`API_CONTRACT.md`):
| Endpoint | Da chi | Cosa fa |
|---|---|---|
| `POST /api/events` | ingestion | riceve un evento, risponde subito, elabora l'embedding in background |
| `PATCH /api/events/{id}` | pipeline | riceve trascrizione/descrizione |
| `GET/PUT /api/users/{id}/preferences` | ingestion/companion | preferenze utente, con default se assenti |
| `GET /api/events/search` | companion | ricerca semantica |
| `GET /api/events` | companion | cronologia paginata (keyset pagination) |
| `GET /api/events/pending` | pipeline | eventi audio/immagine da elaborare |

**Stato**: ✅ completo su tutte le feature pianificate finora (`002`, `005`, `007`), **37 test**
verdi. Decisione tecnica degna di nota: "in attesa di elaborazione" è definito da
`normalized_text IS NULL`, non dallo stato interno di embedding — altrimenti un embedding
fallito dopo una trascrizione riuscita avrebbe fatto ritrascrivere un evento già fatto.

### 3.4 `graph` — grafo dei collegamenti

**Cosa fa**: riceve da `core` la creazione di nodi (progetto/nota/idea/persona/concetto) e
relazioni pesate tra loro, e permette di esplorare i collegamenti di un nodo fino a una
profondità data. Nodi idempotenti sull'evento di origine; relazioni verso nodi inesistenti o
verso sé stessi vengono rifiutate.

**Storage**: SQLite. Esplorazione con BFS in-process su un dizionario di adiacenza costruito al
volo — nessuna libreria di grafi dedicata (`networkx` scartata per lo stesso motivo del vector
database in `core`).

**Stato**: ✅ completo (spec `003-knowledge-graph`), **18 test** verdi — unico modulo verificato
end-to-end per intero nei test (nessuna dipendenza da servizi esterni).

### 3.5 `companion` — app di consultazione

**Cosa fa**: web app server-rendered (FastAPI + Jinja2, nessun frontend con build/JS) che
permette di esplorare i collegamenti di un contenuto nel grafo, con navigazione incrementale
cliccando sui nodi collegati.

**Stato**: 🟡 **parziale** — solo la user story di esplorazione grafo (US2) è implementata
(spec `004-companion-app`, scope volutamente limitato), **9 test** verdi. Ricerca (US1) e
cronologia (US3) hanno già il backend pronto in `core` (`005-core-search-history`) ma non sono
mai state pianificate/implementate lato `companion`.

## 4. Stato dei test

| Modulo | Test | Esito |
|---|---|---|
| ingestion | 12 | ✅ |
| pipeline | 15 | ✅ |
| core | 37 | ✅ |
| graph | 18 | ✅ |
| companion | 9 | ✅ |
| **Totale** | **91** | ✅ |

Tutti i test girano con servizi esterni (Telegram, provider di embedding/STT/captioning) e, per
`ingestion`/`pipeline`/`core`, con gli altri moduli **mockati** — nessuno di questi è mai stato
verificato con un run reale di tutto lo stack insieme (vedi §6).

## 5. Deploy

Documentato in `DEPLOY.md`: setup per far girare `ingestion` + `core` + `graph` sullo stesso
Raspberry Pi 4B, con unit `systemd` di esempio. Punto di attenzione esplicito: due filtri di
accesso diversi, con rigore diverso —

- **whitelist utenti** (`AUTHORIZED_USER_IDS` su `ingestion`): filtro di prodotto, non un
  segreto, ma va tenuto corretto;
- **token Bearer tra servizi** (`CORE_API_TOKEN`, `GRAPH_API_TOKEN`): segreti veri, da generare
  random (`secrets.token_hex`), mai committare, con enforcement `401` già implementato.

`DEPLOY.md` non è ancora stato aggiornato con le variabili d'ambiente di `pipeline` (vedi §6).

## 6. Cosa manca

- **`companion` US1 (ricerca) e US3 (cronologia)**: backend pronto in `core`, mai
  pianificato/implementato lato `companion`.
- **Validazione end-to-end reale**: nessun modulo è mai stato fatto girare insieme agli altri
  con servizi esterni veri (provider di embedding, STT, captioning) — solo test con mock.
  Diversi task nei vari `tasks.md` restano volutamente non spuntati per questo motivo (es. T026
  di `ingestion`, T031/T023 di `core`/`pipeline`).
- **`DEPLOY.md`** da aggiornare con le variabili d'ambiente di `pipeline`.
- **Provider esterni**: `EMBEDDING_API_URL`, `STT_API_URL`, `CAPTIONING_API_URL` sono oggi
  interfacce generiche (documentate nei rispettivi `research.md`) — vanno scelti i provider
  reali e adattato il parsing della risposta se il formato differisce da quello atteso.
- **`pipeline` → `graph`**: la creazione di nodi/relazioni nel grafo a partire dagli eventi
  (sezione 3 di `API_CONTRACT.md`, lato scrittura da `core`) è stata esplicitamente rimandata a
  una feature futura in `002-core-similarity-engine` — oggi `core` calcola le similarità ma non
  scrive ancora nel grafo.

## 7. Cronologia dello sviluppo

10 commit su `main`, dal setup iniziale del monorepo all'implementazione di tutti e 5 i moduli.
Dettaglio completo, sempre aggiornato, in `CHANGELOG.md`.
