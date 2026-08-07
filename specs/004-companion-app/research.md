# Research: App di Consultazione (Companion) — US2, poi US1 + utente mock

Nessun `[NEEDS CLARIFICATION]` residuo. Le sezioni sotto sono cumulative: quelle scritte per
US2 restano valide; le ultime due sono dell'incremento US1 + autenticazione.

## Tipo di interfaccia

**Decision**: web app server-rendered con FastAPI + Jinja2, HTML semplice, nessun framework
JS/build step.

**Rationale**: scelta esplicita dell'utente (tra CLI, comandi Telegram su `ingestion`, o web
app) — coerente con la visione originale di `companion` come app separata. Server-rendered
evita la complessità di un frontend con build/bundler per una pagina di consultazione a uso
personale: un form e una lista di risultati non hanno bisogno di React/Vue o di un'API
JSON separata dal rendering.

**Alternatives considered**: CLI (scartata, l'utente vuole una web app); SPA con frontend
separato (scartata per questa scala — nessun bisogno di interattività client-side complessa
per mostrare una lista di nodi collegati).

## Autenticazione utente su companion (US2, superata dalla decisione sotto)

**Decision originale**: nessuna autenticazione utente sull'interfaccia di `companion`;
assunta rete privata/locale (stesso host degli altri moduli, vedi `DEPLOY.md`).

**Perché è stata rivista**: aggiungendo la ricerca (US1), `companion` rende interrogabile
tutto il contenuto personale salvato — l'assenza totale di gate è stata giudicata un rischio
maggiore rispetto alla sola esplorazione del grafo di US2. Vedi la decisione "Utente mock"
sotto per il nuovo comportamento.

## Utente mock (autenticazione minima, US1)

**Decision**: gate HTTP Basic Auth su tutte le route di `companion` (incluso `/explore` di
US2), verificato contro un'unica coppia utente/password letta da variabili d'ambiente
(`COMPANION_USERNAME`, `COMPANION_PASSWORD`), confrontata con `secrets.compare_digest` per
evitare timing attack banali. Nessun database utenti, nessuna sessione, nessun hashing con
salt: un solo "utente mock" fisso.

**Rationale**: `companion` è per un solo utente proprietario del Second Brain — un vero sistema
di account (registrazione, hashing con salt, sessioni/cookie di sessione, recovery password)
sarebbe complessità ingiustificata per un'unica persona. `HTTPBasic` è già incluso in FastAPI
(nessuna nuova dipendenza), supportato nativamente da ogni browser (prompt di login integrato,
niente form/JS da scrivere), e sufficiente a non lasciare la ricerca completamente aperta su
rete locale. Resta un compromesso esplicito (vedi `plan.md` → Constraints e la nota su FR-006 in
`spec.md`): va sostituito con autenticazione vera solo se/quando `companion` uscirà dalla rete
locale.

**Alternatives considered**: sistema di account completo con login form + sessioni — scartato,
YAGNI per un solo utente; nessun gate (status quo di US2) — scartato ora che la ricerca aumenta
la sensibilità di ciò che `companion` espone; token in query string — scartato, finirebbe nei
log/history del browser, `HTTPBasic` (header) non ha questo problema.

## Ricerca (US1)

**Decision**: nuovo `core_client.py` in `companion`, simmetrico a `graph_client.py` di US2:
chiama `GET /api/events/search?q=...&limit=...` su `core`, propaga il parametro `q` dal form di
ricerca, mostra i risultati (`event_id`, `preview`, `type`, `timestamp`, `score`) in un nuovo
template `search_results.html`, riusando lo stesso stile "form + risultati" già adottato in
`explore_form.html`.

**Rationale**: `005-core-search-history` ha già fatto tutto il lavoro di ricerca semantica lato
`core`; `companion` deve solo chiamarlo e presentare i risultati — stesso pattern già validato
per `graph_client.py`, nessuna nuova idea architetturale necessaria.

**Alternatives considered**: nessuna — il contratto e il pattern client esistono già,
l'implementazione è diretta.

## Esplorazione incrementale

**Decision**: ogni nodo collegato mostrato nei risultati è anche un link che rilancia la stessa
pagina con quel `node_id` come nuovo punto di partenza (`GET /explore?node_id=...`).

**Rationale**: permette di "seguire" i collegamenti passo dopo passo (come richiesto
dall'Acceptance Scenario di US2) senza JavaScript: un link HTML che ricarica la pagina con un
altro parametro basta.
