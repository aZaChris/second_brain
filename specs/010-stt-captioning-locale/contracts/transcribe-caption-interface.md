# Contratto: `pipeline/src/transcription.py` e `pipeline/src/captioning.py`

Interfacce interne che `worker.py` usa per ottenere testo da un file audio o immagine. Non sono
API HTTP esposte all'esterno — `pipeline` non ha un server proprio (`API_CONTRACT.md` non cambia).

## Firme

```python
# transcription.py
def transcribe(audio_bytes: bytes, *, config: Config) -> str: ...

# captioning.py
def caption(image_bytes: bytes, *, config: Config) -> str: ...
```

- **Input**: bytes grezzi del file (invariato rispetto a oggi); `config` per leggere
  `stt_mode`/`captioning_mode` e i parametri della modalità attiva per ciascuna.
- **Output**: `str` non vuota.
- **Errori**: `TranscriptionError`/`CaptioningError` (nomi invariati) se il risultato è vuoto, il
  formato non è supportato, o (in modalità esterna) la chiamata fallisce dopo i retry — stesso
  comportamento a valle in `worker.py` (`_patch_failure`, FR-007).

## Cosa NON cambia

- `worker.py::process_event` — stessa struttura (try/except attorno a `transcribe`/`caption`,
  stesso `_patch_failure` su errore), cambia solo come vengono chiamate (vedi sotto).
- `core_client.py`, `media.py` — nessun riferimento a `transcribe`/`caption`, nessuna modifica.
- Il formato di `PATCH /api/events/{event_id}` inviato a `core` — invariato.

## Cosa cambia in `worker.py`

I 2 punti di chiamata passano `config` invece dei parametri sciolti:

```python
# prima
text = transcribe(media_bytes, api_url=config.stt_api_url, api_token=config.stt_api_token,
                   max_retries=config.max_retries, backoff_seconds=config.retry_backoff_seconds)

# dopo
text = transcribe(media_bytes, config=config)
```

```python
# prima
text = caption(media_bytes, api_url=config.captioning_api_url, api_token=config.captioning_api_token,
               max_retries=config.max_retries, backoff_seconds=config.retry_backoff_seconds)

# dopo
text = caption(media_bytes, config=config)
```

`max_retries`/`backoff_seconds` restano usati internamente da `_transcribe_external`/
`_caption_external`, letti da `config` (già presenti in `Config` oggi), non più passati esplicitamente
dal chiamante.

## Verifica del contratto

Test unitari:
- Con `stt_mode="local"`/`captioning_mode="local"`: `transcribe()`/`caption()` ritornano una
  stringa non vuota data una libreria mockata (nessun download reale, nessun client HTTP
  istanziato).
- Con modalità `"external"`: comportamento HTTP/retry invariato rispetto ai test già esistenti
  prima di questa feature.
- Fallimento (risultato vuoto/eccezione del modello locale): `TranscriptionError`/
  `CaptioningError` sollevata, stesso comportamento a valle in `worker.py` già coperto dai test
  esistenti di `test_worker.py` (se presente) o equivalente.
