"""The WSGI entry point for gunicorn: `gunicorn notes_evidence.interfaces.wsgi:app`."""

from __future__ import annotations

import os

from flask import Flask

from notes_evidence.infrastructure.logging_setup import configure_logging
from notes_evidence.infrastructure.settings import load_settings
from notes_evidence.interfaces.http_app import create_app
from notes_evidence.interfaces.wiring import build_runtime


def create() -> Flask:
    """Build the app from the environment."""
    settings = load_settings(os.environ)
    configure_logging(settings.log_level)
    runtime = build_runtime(settings)
    return create_app(runtime.service, runtime.app_db.ping)


app = create()
