# API Contract — Second Brain

Contratto tra i moduli: Ingestion, Pipeline, Core, Graph, Companion. Ogni modulo espone/consuma solo queste interfacce — implementazione interna libera, purché rispetti schema e comportamento qui descritti.

Formato: REST + JSON. Auth: header `Authorization: Bearer <token>` su tutte le chiamate interne (token condiviso tra moduli, non esposto all'esterno). Timestamp sempre ISO 8601 UTC.

---

## 1. Ingestion → Core: invio evento grezzo

**POST /api/events**

Chiamata dal bot Telegram/WhatsApp ogni volta che arriva un messaggio dall'utente.

Request:
```json
{
  "source": "telegram",
  "user_id": "tg_123456",
  "type": "text | audio | image",
  "content": "testo diretto oppure null",
  "media_url": "url o path del file audio/immagine, null se type=text",
  "timestamp": "2026-08-07T10:32:00Z"
}
```

Response `201 Created`:
```json
{
  "event_id": "evt_9f2a",
  "status": "received"
}
```

Errori: `400` payload invalido, `401` token mancante/errato, `503` core non raggiungibile (il bot deve fare retry con backoff e avvisare l'utente se fallisce).

---

## 2. Pipeline → Core: evento normalizzato

Dopo trascrizione/captioning, la pipeline aggiorna l'evento con il testo normalizzato.

**PATCH /api/events/{event_id}**

Request:
```json
{
  "normalized_text": "testo trascritto o descrizione immagine",
  "pipeline_meta": {
    "model_used": "whisper-api",
    "confidence": 0.94
  }
}
```

Response `200 OK`:
```json
{
  "event_id": "evt_9f2a",
  "status": "normalized"
}
```

Se `type: text`, questo step è saltato: Core tratta `content` come già normalizzato.

---

## 3. Core → Graph: creazione/aggiornamento nodi e relazioni

**POST /api/graph/nodes**

Request:
```json
{
  "node_type": "project | note | idea | person | concept",
  "label": "Second Brain - modulo ingestion",
  "source_event_id": "evt_9f2a",
  "embedding_ref": "vec_id_interno"
}
```

Response `201 Created`:
```json
{ "node_id": "node_44a1" }
```

**POST /api/graph/edges**

Request:
```json
{
  "from_node_id": "node_44a1",
  "to_node_id": "node_12bc",
  "relation": "deriva-da | collegato-a | usa-tecnologia-di",
  "weight": 0.82
}
```

Response `201 Created`: `{ "edge_id": "edge_77z" }`

**GET /api/graph/related/{node_id}?depth=1**

Response `200 OK`:
```json
{
  "node_id": "node_44a1",
  "related": [
    { "node_id": "node_12bc", "relation": "collegato-a", "weight": 0.82 }
  ]
}
```

---

## 4. Companion → Core: lettura progetti e task

**GET /api/projects**

Response `200 OK`:
```json
[
  { "project_id": "proj_1", "name": "Kinect", "status": "active" },
  { "project_id": "proj_2", "name": "Second Brain", "status": "active" }
]
```

**GET /api/projects/{project_id}/tasks**

Response `200 OK`:
```json
[
  {
    "task_id": "task_5",
    "title": "Approfondire libreria STT offline",
    "origin_event_id": "evt_9f2a",
    "estimated_effort": "medium",
    "status": "todo"
  }
]
```

---

## 5. Preferenze utente

**GET /api/users/{user_id}/preferences**

Response `200 OK`:
```json
{
  "interests": ["robotica", "AI", "domotica"],
  "depth_level": "approfondito",
  "notify_on": ["nuova_idea", "collegamento_trovato"]
}
```

**PUT /api/users/{user_id}/preferences** — stesso body, aggiorna le preferenze.

---

## Convenzioni comuni

Tutti gli errori seguono il formato:
```json
{ "error": "codice_errore", "message": "descrizione leggibile" }
```

Codici HTTP standard: `200/201` successo, `400` input invalido, `401` non autorizzato, `404` risorsa non trovata, `503` servizio a valle non disponibile.

Ogni modulo logga `event_id` in ogni operazione derivata, per tracciabilità end-to-end (da messaggio Telegram fino al nodo nel grafo).
