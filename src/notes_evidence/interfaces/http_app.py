"""The notes API over HTTP. Turns requests into service calls and errors into status codes; no rules of its own."""

from __future__ import annotations

import logging
import time
from collections.abc import Callable
from typing import Any

from flask import Flask, Response, g, jsonify, request

from notes_evidence.application.notes_service import NotesService
from notes_evidence.domain.errors import (
    InvalidCredentialsError,
    NotAllowedError,
    NotAuthenticatedError,
    NotFoundError,
    ValidationError,
)
from notes_evidence.domain.notes import Note, User
from notes_evidence.domain.roles import Role

logger = logging.getLogger("notes.http")
MAX_BODY_BYTES = 64 * 1024


def _note_json(note: Note) -> dict[str, Any]:
    return {
        "id": note.id,
        "owner_id": note.owner_id,
        "title": note.title,
        "body": note.body,
        "created_at": note.created_at.isoformat(),
        "updated_at": note.updated_at.isoformat(),
    }


def _payload() -> dict[str, Any]:
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        raise ValidationError("body", "a JSON object is required")
    return data


def create_app(service: NotesService, ping: Callable[[], bool]) -> Flask:
    """Build the Flask app around a service and a database ping."""
    app = Flask(__name__)
    app.config["MAX_CONTENT_LENGTH"] = MAX_BODY_BYTES

    def actor() -> User:
        header = request.headers.get("Authorization", "")
        if not header.startswith("Bearer "):
            raise NotAuthenticatedError("bearer token required")
        return service.authenticate(header.removeprefix("Bearer ").strip())

    @app.before_request
    def start_timer() -> None:
        g.started = time.monotonic()

    @app.after_request
    def finish(response: Response) -> Response:
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Cache-Control"] = "no-store"
        logger.info(
            "request",
            extra={
                "method": request.method,
                "path": request.path,
                "status": response.status_code,
                "duration_ms": int((time.monotonic() - g.get("started", time.monotonic())) * 1000),
            },
        )
        return response

    @app.get("/healthz")
    def healthz() -> tuple[Response, int]:
        healthy = ping()
        return jsonify(status="ok" if healthy else "database unavailable"), 200 if healthy else 503

    @app.post("/login")
    def login() -> Response:
        data = _payload()
        return jsonify(token=service.login(data.get("username", ""), data.get("password", "")))

    @app.get("/notes")
    def list_notes() -> Response:
        return jsonify(notes=[_note_json(note) for note in service.list_notes(actor())])

    @app.post("/notes")
    def create_note() -> tuple[Response, int]:
        data = _payload()
        return jsonify(_note_json(service.create_note(actor(), data.get("title"), data.get("body")))), 201

    @app.get("/notes/<int:note_id>")
    def get_note(note_id: int) -> Response:
        return jsonify(_note_json(service.get_note(actor(), note_id)))

    @app.put("/notes/<int:note_id>")
    def update_note(note_id: int) -> Response:
        data = _payload()
        return jsonify(_note_json(service.update_note(actor(), note_id, data.get("title"), data.get("body"))))

    @app.delete("/notes/<int:note_id>")
    def delete_note(note_id: int) -> tuple[str, int]:
        service.delete_note(actor(), note_id)
        return "", 204

    @app.put("/users/<username>/role")
    def grant_role(username: str) -> Response:
        data = _payload()
        try:
            role = Role(data.get("role"))
        except ValueError:
            raise ValidationError("role", "one of admin, member, readonly") from None
        user = service.grant_role(actor(), username, role)
        return jsonify(username=user.username, role=user.role.value)

    _register_errors(app)
    return app


def _register_errors(app: Flask) -> None:
    def answer(status: int, message: str) -> tuple[Response, int]:
        return jsonify(error=message), status

    @app.errorhandler(ValidationError)
    def invalid(problem: ValidationError) -> tuple[Response, int]:
        return answer(400, str(problem))

    @app.errorhandler(InvalidCredentialsError)
    @app.errorhandler(NotAuthenticatedError)
    def unauthenticated(problem: Exception) -> tuple[Response, int]:
        return answer(401, str(problem))

    @app.errorhandler(NotAllowedError)
    def forbidden(problem: NotAllowedError) -> tuple[Response, int]:
        return answer(403, str(problem))

    @app.errorhandler(NotFoundError)
    def missing(problem: NotFoundError) -> tuple[Response, int]:
        return answer(404, str(problem))

    @app.errorhandler(404)
    def no_route(_: Exception) -> tuple[Response, int]:
        return answer(404, "not found")

    @app.errorhandler(413)
    def too_large(_: Exception) -> tuple[Response, int]:
        return answer(413, "request too large")

    @app.errorhandler(Exception)
    def unexpected(problem: Exception) -> tuple[Response, int]:
        logger.error("unhandled %s", type(problem).__name__)
        return answer(500, "internal error")
