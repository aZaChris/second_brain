"""Entrypoint per uvicorn: `uvicorn src.main:app`."""

from .api import create_app
from .config import Config

app = create_app(Config.from_env())
