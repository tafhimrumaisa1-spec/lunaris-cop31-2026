"""ASGI entrypoint: `uvicorn lunaris_api.main:app` (or `--factory lunaris_api.app:create_app`)."""
from .app import create_app

app = create_app()
