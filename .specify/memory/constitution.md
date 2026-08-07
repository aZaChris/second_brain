<!--
Sync Impact Report
- Version change: (template) → 1.0.0 → 1.1.0
- Modified principles: n/a
- Added sections (1.0.0): Core Principles (I–IV), Vincoli Tecnici, Development Workflow, Governance
- Added sections (1.1.0): Development Workflow — regola su riepilogo di sessione e CHANGELOG.md condiviso
- Removed sections: Principle 5 slot (only 4 principles supplied, removed unused slot)
- Templates requiring updates:
  - ✅ plan-template.md (Constitution Check section is generic, references constitution file — no change needed)
  - ✅ spec-template.md (no constitution-specific references found)
  - ✅ tasks-template.md (no constitution-specific references found)
- Follow-up TODOs: none
-->

# Second Brain Constitution

## Core Principles

### I. Privacy-First
Il progetto tratta dati personali dell'utente (messaggi, audio, immagini, preferenze). Nessun
dato sensibile viene salvato oltre il necessario per il funzionamento della feature che lo
richiede; ogni storage aggiuntivo (log, cache, backup) deve avere una giustificazione esplicita
e una policy di retention. Nessun dato utente viene inviato a servizi esterni non necessari alla
feature in corso. Le credenziali (token bot, chiavi API) non vengono mai committate nel
repository.

### II. Modularità tra Ingestion, Pipeline, Core, Graph, Companion
Ogni modulo (`ingestion`, `pipeline`, `core`, `graph`, `companion`) è un'unità indipendente con
responsabilità unica: non deve contenere logica di un altro modulo, né dipendere dai suoi
dettagli interni. La comunicazione tra moduli avviene esclusivamente tramite le interfacce
definite in `API_CONTRACT.md`. Un modulo può essere sviluppato, testato e rilasciato senza che
gli altri siano implementati, purché rispetti il contratto.

### III. API Chiare e Testabili Indipendentemente
Ogni modulo espone un'API con schema di request/response esplicito e documentato in
`API_CONTRACT.md` prima dell'implementazione. Ogni endpoint deve essere testabile in isolamento
(mock/stub dei moduli a valle o a monte), senza richiedere l'intero sistema in esecuzione.
Modifiche al contratto richiedono allineamento tra i moduli coinvolti prima del merge.

### IV. Servizi Esterni Preferiti a Modelli Locali Pesanti
Il Raspberry Pi funge da nodo di ingestion e orchestrazione, non da nodo di calcolo pesante.
Per LLM, STT (speech-to-text) e captioning si usano servizi esterni (API) invece di modelli
pesanti eseguiti localmente, salvo vincoli di privacy o costo che rendano necessaria
un'alternativa locale leggera — in tal caso la scelta va documentata con la motivazione.

## Vincoli Tecnici

Il Raspberry Pi ha risorse di CPU/RAM/storage limitate: i moduli che vi girano (tipicamente
`ingestion`) devono avere footprint minimo e non assumere disponibilità di GPU. Connettività di
rete non garantita al 100%: ogni chiamata verso servizi esterni o verso altri moduli deve gestire
timeout, retry con backoff ed errori di rete senza perdere l'evento in ingresso.

## Development Workflow

Branch `main` protetto: nessun push diretto, merge solo via Pull Request. Branch di lavoro con
naming `feature/<modulo>-<descrizione>`. Ogni PR che modifica `API_CONTRACT.md` richiede review
di chi lavora sui moduli consumer/producer coinvolti prima del merge.

Ogni sessione di lavoro con un coding agent (es. Claude) termina con un riepilogo di cosa è
stato fatto. Ogni commit che introduce una modifica rilevante (nuovo modulo, endpoint, decisione
architetturale) aggiorna `CHANGELOG.md`, il documento condiviso sempre visibile a entrambi i
collaboratori, cosicché nessuno dei due debba rileggere la history di git per sapere lo stato del
progetto.

## Governance

Questa constitution ha precedenza su altre pratiche o convenzioni del progetto in caso di
conflitto. Le modifiche richiedono una PR dedicata che aggiorni il file e, se necessario, i
template dipendenti (`plan-template.md`, `spec-template.md`, `tasks-template.md`), con
motivazione esplicita nel messaggio di commit/PR. Versionamento semantico: MAJOR per rimozioni o
ridefinizioni di principi non retrocompatibili, MINOR per nuovi principi o sezioni, PATCH per
chiarimenti e correzioni non semantiche. Ogni PR deve poter essere valutata rispetto ai principi
qui definiti; scostamenti vanno giustificati esplicitamente nella sezione "Complexity Tracking"
del piano di implementazione.

**Version**: 1.1.0 | **Ratified**: 2026-08-07 | **Last Amended**: 2026-08-07
