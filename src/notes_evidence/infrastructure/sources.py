"""Where C1 and C2 read from: the hosting platform and the cloud account, as files or as `gh` and `aws` commands.

Both modes parse the same JSON shapes, so the parsers are tested against recorded output of the real tools and the
live adapters only add the command.
"""

from __future__ import annotations

import json
import subprocess
from collections.abc import Callable
from datetime import datetime
from pathlib import Path
from typing import Any

from notes_evidence.domain.access import CLOUD, REPOSITORY, AccessEntry
from notes_evidence.domain.changes import MergedChange

JsonLoader = Callable[[], Any]
Runner = Callable[[list[str]], str]


class SourceError(RuntimeError):
    """A source did not give what the parser needs."""


def run_command(argv: list[str]) -> str:
    """Run a command with a timeout and return its standard output; a failure is a SourceError."""
    try:
        done = subprocess.run(argv, capture_output=True, text=True, timeout=60, check=False)
    except (OSError, subprocess.TimeoutExpired) as problem:
        raise SourceError(f"{argv[0]}: {problem}") from None
    if done.returncode != 0:
        raise SourceError(f"{argv[0]} exited {done.returncode}: {done.stderr.strip()[:200]}")
    return done.stdout


def file_json(path: Path) -> JsonLoader:
    """Load JSON from a file."""
    return lambda: json.loads(path.read_text(encoding="utf-8"))


def command_json(runner: Runner, argv: list[str]) -> JsonLoader:
    """Load JSON from a command's output."""
    return lambda: json.loads(runner(argv))


def parse_collaborators(data: Any) -> list[AccessEntry]:
    """`gh api repos/OWNER/REPO/collaborators`: login and role_name."""
    return [AccessEntry(REPOSITORY, item["login"], item["role_name"]) for item in data]


def parse_iam_users(data: Any) -> list[AccessEntry]:
    """`aws iam list-users`: the user names."""
    return [AccessEntry(CLOUD, item["UserName"]) for item in data["Users"]]


def parse_merged_prs(prs: Any, deploys: Any) -> list[MergedChange]:
    """`gh pr list --state merged --json ...`, joined to the deployment log by the short commit."""
    deploy_by_commit = {item["commit"]: item["deploy_id"] for item in deploys}
    changes = []
    for pr in prs:
        commit = pr["mergeCommit"]["oid"]
        approvers = tuple(
            sorted({review["author"]["login"] for review in pr["reviews"] if review["state"] == "APPROVED"})
        )
        merged_at = datetime.fromisoformat(pr["mergedAt"].replace("Z", "+00:00"))
        changes.append(
            MergedChange(
                pr["number"], pr["author"]["login"], merged_at, commit, approvers, deploy_by_commit.get(commit[:7], "")
            )
        )
    return changes


class GithubRepositoryAccess:
    """Collaborators from whichever loader it is given."""

    def __init__(self, load: JsonLoader) -> None:
        self._load = load

    def collaborators(self) -> list[AccessEntry]:
        """Collaborators and their permission."""
        return parse_collaborators(self._load())


class GithubChanges:
    """Merged pull requests joined with the deployment log."""

    def __init__(self, load_prs: JsonLoader, load_deploys: JsonLoader) -> None:
        self._prs = load_prs
        self._deploys = load_deploys

    def merged_changes(self) -> list[MergedChange]:
        """Merged changes with their approvers and deploy ids."""
        return parse_merged_prs(self._prs(), self._deploys())


class StateCloudDirectory:
    """The cloud account stand-in for fixture mode: a JSON file shaped like `aws iam list-users`, seeded from a fixture.

    `remove_user` rewrites the file, which is what `aws iam delete-user` does to the account.
    """

    def __init__(self, state_file: Path, seed_file: Path) -> None:
        self._state = state_file
        self._seed = seed_file

    def users(self) -> list[AccessEntry]:
        """Users currently in the account."""
        if not self._state.is_file():
            self._state.parent.mkdir(parents=True, exist_ok=True)
            self._state.write_text(self._seed.read_text(encoding="utf-8"), encoding="utf-8")
        return parse_iam_users(json.loads(self._state.read_text(encoding="utf-8")))

    def remove_user(self, name: str) -> None:
        """Delete one user from the account."""
        data = json.loads(self._state.read_text(encoding="utf-8"))
        data["Users"] = [user for user in data["Users"] if user["UserName"] != name]
        self._state.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


class AwsCloudDirectory:
    """The real account through the `aws` command line."""

    def __init__(self, runner: Runner = run_command) -> None:
        self._runner = runner

    def users(self) -> list[AccessEntry]:
        """`aws iam list-users`."""
        return parse_iam_users(json.loads(self._runner(["aws", "iam", "list-users", "--output", "json"])))

    def remove_user(self, name: str) -> None:
        """`aws iam delete-user`. The user must have no keys or policies left; AWS refuses otherwise."""
        self._runner(["aws", "iam", "delete-user", "--user-name", name])
