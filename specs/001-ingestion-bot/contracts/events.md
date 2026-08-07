# Contract: Ingestion → Core

Il bot consuma un solo endpoint, già definito nel contratto condiviso tra moduli: non viene
duplicato qui per evitare che le due copie divergano nel tempo.

Vedi [`API_CONTRACT.md`](../../../API_CONTRACT.md), sezione **1. Ingestion → Core: invio
evento grezzo** (`POST /api/events`), per schema di request/response e codici di errore.

Vincoli specifici di questa feature sul contratto esistente:

- Il bot invia sempre `source: "telegram"`.
- `type` è sempre uno tra `text`, `audio`, `image` (mai un valore non previsto dal contratto):
  i messaggi con contenuto non supportato non vengono inoltrati (FR-009, gestiti prima di
  arrivare a questo endpoint).
- Su risposta `503` o timeout, il bot applica il retry con backoff descritto in
  [`../research.md`](../research.md) prima di considerare l'invio fallito.
