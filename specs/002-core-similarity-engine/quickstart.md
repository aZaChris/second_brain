# Quickstart: Motore di Similarità e Approfondimento (Core)

## Prerequisiti

- Python 3.11+
- Una chiave/URL per il servizio esterno di embedding scelto in fase di implementazione

## Setup

```bash
cd core
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt   # fastapi, uvicorn, httpx, numpy, pytest

export DB_PATH="./core.db"
export EMBEDDING_API_URL="<endpoint del servizio esterno>"
export EMBEDDING_API_TOKEN="<token del servizio esterno>"
export CORE_API_TOKEN="<token condiviso, vedi API_CONTRACT.md>"
```

## Esecuzione

```bash
uvicorn src.main:app --host 0.0.0.0 --port 8000
```

## Scenari di validazione (da spec.md)

1. **Salvataggio ed embedding (US1 / SC-001)**: `POST /api/events` con un evento `type: text` →
   risposta `201` entro 2s con `event_id`; verificare che l'evento risulti salvato con
   `status: embedded`.
2. **Collegamento trovato (US2 / SC-002)**: inviare due eventi con contenuto chiaramente
   correlato → il secondo evento deve produrre un collegamento verso il primo (verificabile
   nei log/risposta interna, secondo quanto deciso in fase di implementazione).
3. **Nessun collegamento su primo evento (US2, edge case)**: `POST /api/events` come primissimo
   evento del sistema → nessun collegamento segnalato.
4. **Rispetto preferenze "minimo" (US3 / SC-004)**: `PUT /api/users/{user_id}/preferences` con
   `depth_level: minimo`, poi inviare un evento con collegamento pertinente disponibile →
   nessuna segnalazione generata.
5. **Media senza testo (Edge case / FR-003)**: `POST /api/events` con `type: audio` e
   `media_url`, nessun `content` → risposta `201`, `status: received`, nessun embedding ancora.
   Poi `PATCH /api/events/{event_id}` con `normalized_text` → l'evento passa a
   `status: embedded`.
6. **Idempotenza (Edge case / FR-007)**: inviare due volte lo stesso `event_id` → il secondo
   invio non genera un nuovo confronto/segnalazione.

## Test automatici

```bash
pytest tests/unit         # similarity, insight decision, storage (embedding esterno mockato)
pytest tests/contract     # payload/risposte conformi ad API_CONTRACT.md (via TestClient)
```
