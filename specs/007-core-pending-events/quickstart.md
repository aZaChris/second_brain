# Quickstart: Eventi in Attesa di Elaborazione (Core)

## Prerequisiti

- Ambiente di `core` già configurato (vedi `core/README.md`).

## Esecuzione

```bash
cd core
uvicorn src.main:app --host 0.0.0.0 --port 8000
```

## Scenari di validazione (da spec.md)

1. **Elenco eventi in attesa (US1 / SC-001)**: salvare un evento `type: audio` e uno
   `type: image` (via `POST /api/events`), poi `GET /api/events/pending` → entrambi compaiono
   con `type`, `media_url`, `timestamp`.
2. **Evento già elaborato escluso (US1 / SC-002)**: fare `PATCH /api/events/{event_id}` con
   `normalized_text` su uno dei due, poi richiedere di nuovo `GET /api/events/pending` →
   quell'evento non compare più.
3. **Nessun evento in attesa (US1, edge case)**: su un'istanza senza eventi audio/immagine in
   attesa → `200` con `"events": []`.
4. **Filtro per tipo (US2 / SC-003)**: `GET /api/events/pending?type=audio` con eventi audio e
   immagine in attesa → solo gli eventi audio compaiono.

## Test automatici

```bash
pytest tests/unit         # get_pending_events
pytest tests/contract     # test_pending_contract.py
```
