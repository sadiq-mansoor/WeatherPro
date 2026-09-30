"""Vercel Python Function entrypoint for the Flask API."""

from __future__ import annotations

import os
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"
sys.path.insert(0, str(BACKEND))

# Vercel functions have a read-only deployment filesystem. The Flask app uses
# /tmp for its rolling window, history, and logs when VERCEL=1.
os.environ.setdefault("VERCEL", "1")

from app import app as _flask_app  # noqa: E402


def app(environ, start_response):
    """Expose Flask and provide a health alias for the API namespace."""
    path = environ.get("PATH_INFO", "")
    if path == "/api":
        environ["PATH_INFO"] = "/"
    elif path == "/api/health":
        environ["PATH_INFO"] = "/health"
    return _flask_app(environ, start_response)
