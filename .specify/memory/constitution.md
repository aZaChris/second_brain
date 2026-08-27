<!--
Sync Impact Report
- Version change: 1.1.0 → 2.0.0
- Modified principles:
  - IV. "Servizi Esterni Preferiti a Modelli Locali Pesanti" → "Modelli Locali Preferiti per
    Compiti CPU-Compatibili, Servizi Esterni per il Resto" (ridefinizione non retrocompatibile:
    la preferenza di default si inverte, motivata dalla migrazione infrastrutturale da
    Raspberry Pi a ZimaBlade)
- Modified sections:
  - Vincoli Tecnici: rimosso il riferimento a footprint minimo legato al Raspberry Pi e a
    "tipicamente ingestion"; sostituito con vincoli di CPU/RAM per container su nodo unico
    ZimaBlade, mantenuto il vincolo "nessuna GPU assunta disponibile" e la gestione di rete
    non garantita
- Added sections: n/a
- Removed sections: n/a
- Templates requiring updates:
  - ✅ plan-template.md (Constitution Check section è generica, nessun riferimento hardcoded a
    Raspberry Pi o al Principio IV — nessuna modifica necessaria)
  - ✅ spec-template.md (nessun riferimento specifico alla constitution — nessuna modifica
    necessaria)
  - ✅ tasks-template.md (nessun riferimento specifico alla constitution — nessuna modifica
    necessaria)
  - ⚠ README.md (riga "Preferenza per servizi esterni (LLM/STT) rispetto a modelli pesanti
    locali sul Raspberry Pi" riflette ancora il Principio IV precedente — da aggiornare in un
    passo successivo, non incluso in questo comando)
- Follow-up TODOs:
  - specs/002-core-similarity-engine e specs/006-pipeline-transcription-captioning hanno
    research.md/plan.md che documentano la vecchia decisione (servizio esterno di
    embedding/STT/captioning) coerente con il Principio IV precedente — da rifare secondo il
    Principio IV attuale (pianificato come passi successivi della migrazione ZimaBlade)
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

### IV. Modelli Locali Preferiti per Compiti CPU-Compatibili, Servizi Esterni per il Resto
L'infrastruttura gira su uno ZimaBlade (Intel Celeron quad-core x86, fino a 16GB RAM, storage
SATA), nodo unico per tutti i moduli, inclusi i carichi di calcolo leggeri — non più un
Raspberry Pi limitato a ingestion e orchestrazione. Per compiti compatibili con l'esecuzione su
CPU (embedding, STT, captioning con modelli leggeri) si preferisce un modello locale a un
servizio esterno: nessun dato personale lascia il nodo (rafforza il Principio I) e il costo
marginale resta nullo. In concreto: l'embedding usa un modello locale leggero (es.
sentence-transformers multilingue); STT e captioning usano un modello locale leggero (es.
faster-whisper, captioning compatto) finché il tempo di elaborazione resta entro il budget
definito nelle spec di ciascuna feature (dell'ordine di pochi minuti per evento). Un servizio
esterno resta l'alternativa legittima quando la qualità richiesta supera quanto un modello
leggero offre, o quando il tempo di elaborazione locale eccede il budget — in tal caso la scelta
va documentata con la motivazione.

## Vincoli Tecnici

Tutti i moduli girano containerizzati su un unico nodo ZimaBlade, con limiti di CPU/RAM
assegnati per container: nessun modulo deve assumere disponibilità di GPU. Connettività di rete
non garantita al 100% verso servizi esterni (quando usati per le eccezioni del Principio IV) o
verso altri moduli: ogni chiamata deve gestire timeout, retry con backoff ed errori di rete senza
perdere l'evento in ingresso.

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

**Version**: 2.0.0 | **Ratified**: 2026-08-07 | **Last Amended**: 2026-08-25
