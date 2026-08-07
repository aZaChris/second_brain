"""App FastAPI: pagina di esplorazione del grafo (US2 di 004-companion-app)."""

from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from . import graph_client
from .config import Config

TEMPLATES_DIR = Path(__file__).parent / "templates"


def create_app(config: Config) -> FastAPI:
    app = FastAPI()
    templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

    @app.get("/explore", response_class=HTMLResponse)
    async def explore(request: Request, node_id: str | None = None, depth: int = 1):
        context = {"node_id": node_id, "depth": depth}

        if node_id:
            try:
                result = graph_client.get_related(
                    node_id, depth, api_url=config.graph_api_url, api_token=config.graph_api_token
                )
            except graph_client.GraphUnavailableError as exc:
                context["error"] = f"Impossibile raggiungere il grafo: {exc}"
            else:
                if result is None:
                    context["error"] = f"Nodo non trovato: {node_id}"
                else:
                    context["related"] = result["related"]

        return templates.TemplateResponse(request, "explore_form.html", context)

    return app
