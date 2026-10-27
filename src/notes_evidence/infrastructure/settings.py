"""Settings from the environment, validated once at start-up (twelve-factor). Secrets come only from here."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path


class SettingsError(ValueError):
    """An environment variable is missing or holds a value the program cannot use."""


@dataclass(frozen=True)
class Settings:
    """Everything the programs read from the environment."""

    database_url: str
    admin_database_url: str
    secret: str
    token_ttl_seconds: int
    retention_days: int
    statement_timeout_ms: int
    evidence_dir: Path
    controls_file: Path
    evidence_source: str
    run_by: str
    state_dir: Path
    log_level: str
    http_port: int
    db_exec_prefix: tuple[str, ...]
    postgres_user: str
    postgres_db: str


def _required(env: Mapping[str, str], name: str) -> str:
    value = env.get(name, "")
    if not value:
        raise SettingsError(f"{name} is required")
    return value


def _positive_int(env: Mapping[str, str], name: str, default: int) -> int:
    raw = env.get(name, str(default))
    try:
        value = int(raw)
    except ValueError:
        raise SettingsError(f"{name} must be a whole number, got {raw!r}") from None
    if value <= 0:
        raise SettingsError(f"{name} must be positive, got {value}")
    return value


def load_settings(env: Mapping[str, str]) -> Settings:
    """Validate and collect the settings. A signing secret shorter than 32 characters is refused."""
    secret = _required(env, "NOTES_SECRET")
    if len(secret) < 32:
        raise SettingsError("NOTES_SECRET must be at least 32 characters")
    source = env.get("EVIDENCE_SOURCE", "fixture")
    if source not in ("fixture", "live"):
        raise SettingsError(f"EVIDENCE_SOURCE must be fixture or live, got {source!r}")
    level = env.get("LOG_LEVEL", "INFO").upper()
    if level not in ("DEBUG", "INFO", "WARNING", "ERROR"):
        raise SettingsError(f"LOG_LEVEL must be DEBUG, INFO, WARNING or ERROR, got {level!r}")
    return Settings(
        database_url=_required(env, "DATABASE_URL"),
        admin_database_url=env.get("ADMIN_DATABASE_URL", ""),
        secret=secret,
        token_ttl_seconds=_positive_int(env, "TOKEN_TTL_SECONDS", 900),
        retention_days=_positive_int(env, "AUDIT_RETENTION_DAYS", 365),
        statement_timeout_ms=_positive_int(env, "DB_STATEMENT_TIMEOUT_MS", 30_000),
        evidence_dir=Path(env.get("EVIDENCE_DIR", "evidence")),
        controls_file=Path(env.get("CONTROLS_FILE", "controls/controls.toml")),
        evidence_source=source,
        run_by=env.get("EVIDENCE_RUN_BY", "ada"),
        state_dir=Path(env.get("STATE_DIR", "state")),
        log_level=level,
        http_port=_positive_int(env, "HTTP_PORT", 8080),
        db_exec_prefix=tuple(env.get("DB_EXEC_PREFIX", "docker compose exec -T db").split()),
        postgres_user=env.get("POSTGRES_USER", "postgres"),
        postgres_db=env.get("POSTGRES_DB", "notes"),
    )
