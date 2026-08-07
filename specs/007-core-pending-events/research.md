# Research: Eventi in Attesa di Elaborazione (Core)

Nessun `[NEEDS CLARIFICATION]` residuo.

## Cosa rende un evento "in attesa"

**Decision**: un evento è "in attesa" per `pipeline` se `type` è `audio`/`image` e
`normalized_text IS NULL` — non in base al campo `status` (`received`/`embedded`/
`skipped_low_signal`) già usato internamente da `core` per l'embedding.

**Rationale**: `status` riflette l'esito dell'embedding (fatto da `core` dopo il `PATCH`), non
se `pipeline` ha già trascritto/descritto l'evento. Se il servizio esterno di embedding fallisce
temporaneamente dopo un `PATCH` riuscito, l'evento resta con `status: received` pur avendo già
`normalized_text` valorizzato — filtrare per `status` lo farebbe ricomparire come "da
trascrivere" e `pipeline` lo rielaborerebbe inutilmente, violando FR-004. Filtrare su
`normalized_text IS NULL` (più `content IS NULL`, dato che gli eventi audio/immagine hanno
sempre `content` nullo) è il segnale corretto e indipendente dallo stato di embedding di `core`.

**Alternatives considered**: filtrare per `status = 'received'` — scartato per il motivo sopra;
aggiungere un nuovo campo di stato dedicato (es. `pipeline_status`) — scartato, ridondante:
`normalized_text IS NULL` è già un segnale sufficiente e già presente nello schema.

## Ordinamento della coda

**Decision**: eventi in attesa ordinati per `timestamp` crescente (i più vecchi prima) — FIFO.

**Rationale**: per una coda di lavoro ha senso elaborare prima ciò che aspetta da più tempo,
al contrario della cronologia per `companion` (`005`) che mostra i più recenti prima.

**Alternatives considered**: nessun ordinamento esplicito — scartato, un ordine deterministico
rende il comportamento prevedibile e testabile.
