"""C1: who has which access, in which system. Generated from the systems, never typed."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from notes_evidence.domain.audit import format_timestamp

REPOSITORY = "repository (permission per person)"
DATABASE = "database roles"
CLOUD = "cloud account users"
SYSTEMS = (REPOSITORY, DATABASE, CLOUD)


@dataclass(frozen=True)
class AccessEntry:
    """One principal in one system. `level` is empty where the system has only members (cloud users)."""

    system: str
    principal: str
    level: str = ""


@dataclass(frozen=True)
class AccessList:
    """Every entry of every system, with the moment it was generated."""

    generated_at: datetime
    entries: tuple[AccessEntry, ...]

    def in_system(self, system: str) -> tuple[AccessEntry, ...]:
        """The entries of one system, in the order the system returned them."""
        return tuple(entry for entry in self.entries if entry.system == system)

    def counts(self) -> dict[str, int]:
        """Entries per system."""
        return {system: len(self.in_system(system)) for system in SYSTEMS}

    def without(self, system: str, principal: str) -> AccessList:
        """The same list with one principal removed from one system."""
        kept = tuple(entry for entry in self.entries if not (entry.system == system and entry.principal == principal))
        return AccessList(self.generated_at, kept)


def render_access_list(access: AccessList) -> str:
    """The artifact: a dated header and one block per system, `principal<TAB>level` per line."""
    lines = [f"# access list, generated {format_timestamp(access.generated_at)}"]
    for system in SYSTEMS:
        lines.append(f"## {system}")
        for entry in access.in_system(system):
            lines.append(f"{entry.principal}\t{entry.level}" if entry.level else entry.principal)
    return "\n".join(lines) + "\n"


def parse_access_list(text: str) -> dict[str, list[str]]:
    """Principals per system from a rendered list; empty when the text is not an access list."""
    blocks: dict[str, list[str]] = {}
    current: str | None = None
    for line in text.splitlines():
        if line.startswith("## "):
            current = line[3:].strip()
            blocks[current] = []
        elif current is not None and line.strip() and not line.startswith("#"):
            blocks[current].append(line.split("\t")[0].strip())
    return blocks
