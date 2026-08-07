# Quickstart: Ricerca e Cronologia Eventi (Core)

## Prerequisiti

- Ambiente di `core` già configurato (vedi `core/README.md`), stesso `DB_PATH` e servizio di
  embedding già in uso per `002-core-similarity-engine`.

## Esecuzione

```bash
cd core
uvicorn src.main:app --host 0.0.0.0 --port 8000
```

## Scenari di validazione (da spec.md)

1. **Ricerca pertinente (US1 / SC-001, SC-002)**: salvare un evento (`POST /api/events`) con
   testo abbastanza specifico, attendere l'embedding, poi `GET /api/events/search?q=...` con
   parole diverse ma legate allo stesso significato → l'evento compare tra i risultati con
   `preview`, `type`, `timestamp`, `score`.
2. **Nessun risultato (US1, edge case)**: `GET /api/events/search?q=...` senza eventi pertinenti
   salvati → `200` con `"results": []`.
3. **Evento non ancora embeddato escluso (US1 / SC-002)**: salvare un evento `type: audio` senza
   `PATCH` successivo (nessun testo, nessun embedding) → non deve mai comparire in nessuna
   ricerca, qualunque sia la query.
4. **Cronologia in ordine (US2 / SC-003)**: salvare 3 eventi in momenti diversi, poi
   `GET /api/events` → restituiti dal più recente al meno recente.
5. **Paginazione (US2 / SC-004)**: salvare più eventi di quanti ne stiano in una pagina (`limit`
   basso), poi usare `next_before` della prima risposta per richiedere la pagina successiva →
   nessun evento duplicato né mancante tra le due pagine.
6. **Cronologia vuota (US2, edge case)**: `GET /api/events` su un'istanza senza eventi salvati →
   `200` con `"events": []`, `"next_before": null`.

## Test automatici

```bash
pytest tests/unit         # nuove query di storage (get_embedded_events_all, get_events_page)
pytest tests/contract     # test_search_contract.py, test_history_contract.py
```
