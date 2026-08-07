# Research: Trascrizione Audio e Captioning Immagini (Pipeline)

Nessun `[NEEDS CLARIFICATION]` residuo.

## Scoperta del lavoro: polling vs push

**Decision**: `pipeline` interroga `GET /api/events/pending` a intervalli regolari (polling),
invece di ricevere un push da `core` o da `ingestion`.

**Rationale**: `007-core-pending-events` è stato progettato apposta come endpoint di lettura
per questo scopo. Un push (webhook da `core` verso `pipeline`, o coda/broker) richiederebbe
`pipeline` sempre raggiungibile e un nuovo canale non previsto da `API_CONTRACT.md` — a basso
volume (uso personale) un polling ogni N secondi è più semplice da operare e già sufficiente
per SC-001/SC-002 (trascrizione entro pochi minuti).

**Alternatives considered**: webhook da `core` a `pipeline` (scartato: richiede `pipeline`
esposta come server, complessità non necessaria per un worker); coda/broker (Redis, RabbitMQ)
— scartata per lo stesso motivo già usato in `ingestion`/`core`: nessun servizio aggiuntivo
finché il volume non lo richiede.

## Segnalazione di un fallimento definitivo

**Decision**: quando il file non è più raggiungibile (FR-006) o il servizio esterno resta
indisponibile dopo i retry (FR-007), `pipeline` invia comunque un `PATCH
/api/events/{event_id}` con un `normalized_text` segnaposto riconoscibile (es. `"[pipeline:
trascrizione non riuscita — file non raggiungibile]"`) e un `pipeline_meta` che ne registra il
motivo (`{"status": "failed", "reason": "..."}`).

**Rationale**: `API_CONTRACT.md` non prevede un endpoint dedicato per "segnalare un
fallimento" — aggiungerne uno nuovo per questo solo scopo sarebbe complessità evitabile quando
il `PATCH` già esistente basta: valorizzare `normalized_text` toglie l'evento dalla lista di
`GET /api/events/pending` (coerente con `007`, che la considera "elaborata" appena
`normalized_text` non è più nullo) e rende il fallimento visibile via `companion`
(cronologia/ricerca mostreranno il testo segnaposto), soddisfacendo SC-004 senza bloccare
l'evento indefinitamente né inventare nuova infrastruttura.

**Alternatives considered**: lasciare l'evento in sospeso indefinitamente, ritentando ad ogni
poll — scartato, viola SC-004 e martella inutilmente il servizio esterno se il problema è
persistente; aggiungere un endpoint `POST /api/events/{event_id}/fail` dedicato — scartato,
YAGNI: il `PATCH` esistente copre già il caso con un valore di testo diverso.

## Retry e backoff

**Decision**: sia il download del file (`media.py`) sia le chiamate ai servizi esterni di
STT/captioning usano lo stesso pattern già adottato in `ingestion`/`core`: un ciclo con backoff
esponenziale, max 3 tentativi, implementato in poche righe di stdlib (`time.sleep`), senza
librerie di retry dedicate.

**Rationale**: coerenza con le altre feature del monorepo (`events.py` di `ingestion`, `core`);
stessa scala di problema (blip di rete), stessa soluzione minima.

**Alternatives considered**: libreria `tenacity` — scartata per lo stesso motivo già
documentato in `001-ingestion-bot/research.md`.
