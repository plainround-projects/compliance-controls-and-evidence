"""Integration tests need the PostgreSQL of docker-compose.yml (make up); they skip, saying why, without it."""

from __future__ import annotations

import os

import pytest

from notes_evidence.infrastructure.postgres import Database
from notes_evidence.infrastructure.settings import Settings, load_settings


@pytest.fixture(scope="session")
def settings() -> Settings:
    if not os.environ.get("DATABASE_URL") or not os.environ.get("ADMIN_DATABASE_URL"):
        pytest.skip("DATABASE_URL and ADMIN_DATABASE_URL are not set: run `make up` and use `make test-integration`")
    return load_settings(os.environ)


@pytest.fixture(scope="session")
def admin(settings: Settings) -> Database:
    return Database(settings.admin_database_url)


@pytest.fixture(scope="session")
def app_db(settings: Settings) -> Database:
    return Database(settings.database_url)
