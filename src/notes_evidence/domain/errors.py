"""Named errors of the notes service. The interfaces layer maps each to an HTTP status."""

from __future__ import annotations


class DomainError(Exception):
    """Base of every expected failure."""


class ValidationError(DomainError):
    """An input is not acceptable; `field` says which."""

    def __init__(self, field: str, message: str) -> None:
        super().__init__(f"{field}: {message}")
        self.field = field
        self.message = message


class InvalidCredentialsError(DomainError):
    """The username or password is wrong, or the account is inactive. The message never says which."""


class NotAuthenticatedError(DomainError):
    """A request carries no valid token."""


class NotAllowedError(DomainError):
    """The role may not do this."""


class NotFoundError(DomainError):
    """The note does not exist, or the caller may not know that it does."""
