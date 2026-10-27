"""Roles and what each may do: least privilege as a table that tests can read."""

from __future__ import annotations

from enum import Enum


class Role(Enum):
    """member writes their own notes; readonly reads every note and writes none; admin does everything."""

    ADMIN = "admin"
    MEMBER = "member"
    READONLY = "readonly"


class Permission(Enum):
    """What a request needs."""

    READ_OWN = "read_own"
    WRITE_OWN = "write_own"
    READ_ANY = "read_any"
    WRITE_ANY = "write_any"
    GRANT_ROLE = "grant_role"


GRANTS: dict[Role, frozenset[Permission]] = {
    Role.ADMIN: frozenset(Permission),
    Role.MEMBER: frozenset({Permission.READ_OWN, Permission.WRITE_OWN}),
    Role.READONLY: frozenset({Permission.READ_OWN, Permission.READ_ANY}),
}


def allowed(role: Role, permission: Permission) -> bool:
    """True when the role holds the permission."""
    return permission in GRANTS[role]
