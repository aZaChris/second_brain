"""Entrypoint per uvicorn: `uvicorn src.main:app`."""

from . import embedding
from .api import create_app
from .config import Config

_config = Config.from_env()
embedding.preload(_config)  # una sola volta all'avvio del processo, non per richiesta (FR-003)
app = create_app(_config)
