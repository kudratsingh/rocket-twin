"""Compose local draft routes ahead of the unchanged frozen inspection API.

The base catalog and its source/asset equivalence pins stay unchanged. Its CORS
middleware and documentation apply to its own mounted routes; the draft router
has its separate exact-origin request boundary, including PATCH/OPTIONS.
"""

from pathlib import Path

from fastapi import FastAPI

from src.api.app import CATALOG, ROOT, CatalogEntry
from src.api.app import create_app as create_inspection_app
from src.api.design_drafts import create_router
from src.api.draft_intents import create_router as create_intent_router
from src.api.reference_parts import create_router as create_reference_router


def create_app(root: Path = ROOT, catalog: tuple[CatalogEntry, ...] = CATALOG) -> FastAPI:
    """Create the loopback workbench app; create no draft on startup."""
    app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None)
    app.include_router(create_reference_router(root))
    app.include_router(create_intent_router(root))
    app.include_router(create_router(root))
    app.mount("/", create_inspection_app(root, catalog))
    return app
