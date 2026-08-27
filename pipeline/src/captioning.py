"""Descrive un'immagine: modello locale in-process di default (Principio IV della
constitution v2.0.0), servizio esterno HTTP come alternativa configurabile.
"""

from __future__ import annotations

import io
import time

import httpx

from .config import Config

_local_processor = None  # caricato una volta da preload(), mai per singola richiesta (FR-004)
_local_model = None


class CaptioningError(RuntimeError):
    pass


def _load_processor(model_name: str, cache_dir: str | None):
    from transformers import BlipProcessor  # import pesante: solo se serve

    return BlipProcessor.from_pretrained(model_name, cache_dir=cache_dir)


def _load_model(model_name: str, cache_dir: str | None):
    from transformers import BlipForConditionalGeneration  # import pesante: solo se serve

    return BlipForConditionalGeneration.from_pretrained(model_name, cache_dir=cache_dir)


def preload(config: Config) -> None:
    """Carica il modello locale in memoria una sola volta, se in modalità locale.
    Va chiamato una sola volta all'avvio del processo (worker.main()), non per richiesta.

    Usa le classi BLIP dedicate (`BlipProcessor`/`BlipForConditionalGeneration`, tramite
    `_load_processor`/`_load_model`) invece dell'astrazione generica `transformers.pipeline`: il
    nome del task generico ("image-to-text") non è stabile tra versioni di `transformers`
    (rimosso/rinominato in versioni recenti), le classi specifiche del modello sì.
    `_load_processor`/`_load_model` sono funzioni separate (invece di chiamare `transformers`
    direttamente qui) così i test possono sostituirle senza dipendere dai dettagli di caching
    interni del modulo `transformers`."""
    global _local_processor, _local_model
    if config.captioning_mode != "local" or _local_model is not None:
        return

    _local_processor = _load_processor(config.captioning_model_name, config.captioning_model_cache)
    _local_model = _load_model(config.captioning_model_name, config.captioning_model_cache)


def caption(image_bytes: bytes, *, config: Config) -> str:
    if config.captioning_mode == "local":
        return _caption_local(image_bytes)
    return _caption_external(
        image_bytes,
        api_url=config.captioning_api_url,
        api_token=config.captioning_api_token,
        max_retries=config.max_retries,
        backoff_seconds=config.retry_backoff_seconds,
    )


def _caption_local(image_bytes: bytes) -> str:
    if _local_model is None or _local_processor is None:
        raise CaptioningError("modello locale non caricato: preload(config) non è stato chiamato all'avvio")

    try:
        from PIL import Image

        image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        inputs = _local_processor(image, return_tensors="pt")
        output_ids = _local_model.generate(**inputs, max_new_tokens=50)
        text = _local_processor.decode(output_ids[0], skip_special_tokens=True).strip()
    except Exception as exc:  # formato non supportato, file corrotto, ecc. (FR-007)
        raise CaptioningError(f"captioning locale fallito: {exc}") from exc

    if not text:
        raise CaptioningError("captioning locale ha prodotto un risultato vuoto")
    return text


def _caption_external(
    image_bytes: bytes,
    *,
    api_url: str,
    api_token: str,
    max_retries: int = 3,
    backoff_seconds: float = 1.0,
) -> str:
    last_error: Exception | None = None
    for attempt in range(max_retries):
        try:
            response = httpx.post(
                api_url,
                content=image_bytes,
                headers={"Authorization": f"Bearer {api_token}", "Content-Type": "application/octet-stream"},
                timeout=60.0,
            )
        except httpx.RequestError as exc:
            last_error = exc
        else:
            if response.status_code == 200:
                text = response.json().get("text")
                if text:
                    return text
                last_error = CaptioningError("risposta del servizio di captioning senza campo 'text'")
            else:
                last_error = CaptioningError(f"servizio di captioning ha risposto {response.status_code}")

        if attempt < max_retries - 1:
            time.sleep(backoff_seconds * (2**attempt))

    raise CaptioningError(f"captioning fallito dopo {max_retries} tentativi: {last_error}") from last_error
