# Research: App di Consultazione (Companion) — solo US2

Nessun `[NEEDS CLARIFICATION]` residuo.

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

## Autenticazione utente su companion

**Decision**: nessuna autenticazione utente sull'interfaccia di `companion` in questa v1;
assunta rete privata/locale (stesso host degli altri moduli, vedi `DEPLOY.md`).

**Rationale**: `companion` è per un solo utente proprietario del Second Brain; aggiungere
login/sessioni ora sarebbe complessità non giustificata finché l'app non è esposta oltre la
rete locale. La chiamata verso `graph` resta comunque autenticata con `GRAPH_API_TOKEN`
(sicurezza service-to-service, diversa da quella utente — stessa distinzione già fatta in
`DEPLOY.md` tra whitelist di prodotto e token di servizio).

**Alternatives considered**: autenticazione utente (login/password, token) — rimandata a
quando/se `companion` verrà esposta fuori dalla rete locale.

## Esplorazione incrementale

**Decision**: ogni nodo collegato mostrato nei risultati è anche un link che rilancia la stessa
pagina con quel `node_id` come nuovo punto di partenza (`GET /explore?node_id=...`).

**Rationale**: permette di "seguire" i collegamenti passo dopo passo (come richiesto
dall'Acceptance Scenario di US2) senza JavaScript: un link HTML che ricarica la pagina con un
altro parametro basta.
