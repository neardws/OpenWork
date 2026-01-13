"""Server module - FastAPI backend for OpenWork."""

from openwork.server.app import create_app
from openwork.server.websocket import ConnectionManager

__all__ = ["create_app", "ConnectionManager"]
