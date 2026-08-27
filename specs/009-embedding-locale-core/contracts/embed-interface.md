# Contratto: `core/src/embedding.py`

Interfaccia interna che il resto di `core` usa per ottenere l'embedding di un testo. Non è
un'API HTTP esposta all'esterno (quella resta invariata, vedi `API_CONTRACT.md`) — è il contratto
tra `embedding.py` e i suoi due chiamanti in `api.py`.

## Firma

```python
def embed(text: str, *, config: Config, client: httpx.Client | None = None) -> list[float]:
    ...
```

- **Input**: `text` non vuoto (i chiamanti già filtrano con `is_low_signal` prima di chiamare
  `embed`, invariato); `config` per leggere `embedding_mode` e i parametri della modalità attiva.
- **Output**: `list[float]`, lunghezza pari alla dimensionalità del modello attivo (384 per
  `paraphrase-multilingual-MiniLM-L12-v2` in modalità locale).
- **Errori**: `EmbeddingError` (invariato) se la modalità esterna fallisce dopo i retry, o se il
  modello locale non riesce a produrre un vettore (caso limite, es. testo non processabile).

## Cosa NON cambia

- `similarity.py` (`cosine_similarity`, `find_similar`, `is_low_signal`) — nessun riferimento a
  `embed()`, nessuna modifica.
- `insight.py` — nessun riferimento a `embed()`, nessuna modifica.
- Lo schema di richiesta/risposta delle route HTTP di `core` in `API_CONTRACT.md` — invariato,
  questo è un cambiamento interno.

## Cosa cambia in `api.py`

I 2 punti di chiamata (`_process_event_text` in background, `search_events`) passano `config`
invece dei singoli `api_url`/`api_token`:

```python
# prima
vector = embed(text, api_url=config.embedding_api_url, api_token=config.embedding_api_token)

# dopo
vector = embed(text, config=config)
```

## Verifica del contratto

Test unitari di `embedding.py`:
- Con `embedding_mode="local"`: `embed()` ritorna un vettore di lunghezza 384, nessun client HTTP
  istanziato (verificabile mockando `httpx.Client` e asserendo che non viene chiamato).
- Con `embedding_mode="external"`: comportamento invariato rispetto ai test già esistenti prima
  di questa feature (chiamata HTTP, retry, `EmbeddingError` sugli stessi casi di oggi).
