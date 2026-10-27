"""The composition root: build the adapters from settings and hand them to the use cases."""

from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import timedelta
from pathlib import Path

from notes_evidence.application.notes_service import NotesService
from notes_evidence.application.ports import ChangeSource, CloudDirectory, RepositoryAccess
from notes_evidence.infrastructure.clock import SystemClock
from notes_evidence.infrastructure.passwords import ScryptHasher
from notes_evidence.infrastructure.postgres import (
    Database,
    PostgresAuditLog,
    PostgresNotes,
    PostgresProvisioner,
    PostgresRoles,
    PostgresUsers,
)
from notes_evidence.infrastructure.settings import Settings
from notes_evidence.infrastructure.sources import (
    AwsCloudDirectory,
    GithubChanges,
    GithubRepositoryAccess,
    StateCloudDirectory,
    command_json,
    file_json,
    run_command,
)
from notes_evidence.infrastructure.tokens import HmacTokens

FIXTURES = Path("fixtures")


@dataclass(frozen=True)
class Runtime:
    """Everything the programs share."""

    settings: Settings
    clock: SystemClock
    hasher: ScryptHasher
    app_db: Database
    users: PostgresUsers
    audit: PostgresAuditLog
    service: NotesService


def build_runtime(settings: Settings) -> Runtime:
    """The notes service wired to PostgreSQL as the least-privileged `app_rw` role."""
    clock, hasher = SystemClock(), ScryptHasher()
    database = Database(settings.database_url, statement_timeout_ms=settings.statement_timeout_ms)
    users, audit = PostgresUsers(database), PostgresAuditLog(database)
    tokens = HmacTokens(settings.secret, timedelta(seconds=settings.token_ttl_seconds))
    service = NotesService(users, PostgresNotes(database), audit, hasher, tokens, clock)
    return Runtime(settings, clock, hasher, database, users, audit, service)


def admin_database(settings: Settings) -> Database:
    """The administrative connection, used by the collectors and the provisioner."""
    return Database(
        settings.admin_database_url or settings.database_url, statement_timeout_ms=settings.statement_timeout_ms
    )


def provisioner(settings: Settings) -> PostgresProvisioner:
    """Creates accounts."""
    return PostgresProvisioner(admin_database(settings))


def database_roles(settings: Settings) -> PostgresRoles:
    """C1 for the database."""
    return PostgresRoles(admin_database(settings))


def repository_access(settings: Settings) -> RepositoryAccess:
    """Collaborators from a fixture file, or from `gh api` when EVIDENCE_SOURCE=live (set GITHUB_REPOSITORY)."""
    if settings.evidence_source == "live":
        repo = os.environ["GITHUB_REPOSITORY"]
        return GithubRepositoryAccess(command_json(run_command, ["gh", "api", f"repos/{repo}/collaborators"]))
    return GithubRepositoryAccess(file_json(FIXTURES / "github-collaborators.json"))


def change_source(settings: Settings) -> ChangeSource:
    """Merged pull requests and the deployment log, from fixtures or from `gh pr list`."""
    deploys = file_json(FIXTURES / "deploy-log.json")
    if settings.evidence_source == "live":
        repo = os.environ["GITHUB_REPOSITORY"]
        argv = [
            "gh",
            "pr",
            "list",
            "--repo",
            repo,
            "--state",
            "merged",
            "--limit",
            "50",
            "--json",
            "number,title,author,mergedAt,mergeCommit,reviews",
        ]
        return GithubChanges(command_json(run_command, argv), deploys)
    return GithubChanges(file_json(FIXTURES / "github-merged-prs.json"), deploys)


def cloud_directory(settings: Settings) -> CloudDirectory:
    """The cloud account: a state file seeded from a fixture, or the real account through `aws`."""
    if settings.evidence_source == "live":
        return AwsCloudDirectory()
    return StateCloudDirectory(settings.state_dir / "cloud-users.json", FIXTURES / "aws-iam-users.json")
