# HTTP, REST and curl

## What it is

**HTTP** is the way programs ask each other for things over a network. A **client** sends a **request** (a method such as `GET`, a
path such as `/notes`, headers, sometimes a body); a **server** sends back a **response** (a **status code**, headers, a body).
A **REST API** uses the method and path to say what to do with a thing: `GET /notes` lists, `POST /notes` creates,
`DELETE /notes/3` deletes. `curl` is a command-line client.

## Why this repository uses it

The service whose controls are being proved is a notes API. Its behavior (who may read which note, what is refused, what is
logged) is exactly what the evidence shows, so the API must be small and clear.

## Where it appears

| File | What it does with this technology |
| --- | --- |
| `src/notes_evidence/interfaces/http_app.py` | The routes and the error-to-status mapping. |
| `src/notes_evidence/interfaces/health.py` | A client: asks `/healthz`. |
| `Makefile` `smoke` | `curl -fsS http://127.0.0.1:$(HTTP_PORT)/healthz`. |
| `docker-compose.yml` | Publishes the API port on `127.0.0.1` only. |

## How it works underneath

A request is text on a TCP connection: a first line (`GET /healthz HTTP/1.1`), headers (`Authorization: Bearer <token>`), a blank
line, and a body. The status code says how it went: **2xx** success (200 OK, 201 Created, 204 No Content), **4xx** the caller's
fault (400 bad input, 401 not logged in, 403 not allowed, 404 not found, 413 too large), **5xx** the server's fault (500, 503).
A **bearer token** is a secret string the client sends in the `Authorization` header to prove who it is.

## Walkthrough of this repository's use

`src/notes_evidence/interfaces/http_app.py`:

```python
    def actor() -> User:
        header = request.headers.get("Authorization", "")
        if not header.startswith("Bearer "):
            raise NotAuthenticatedError("bearer token required")
        return service.authenticate(header.removeprefix("Bearer ").strip())
```

Every protected route calls `actor()`. It reads the header, insists on the form `Bearer <token>`, and asks the service who the
token belongs to; no header means `NotAuthenticatedError`, which becomes `401`.

`src/notes_evidence/interfaces/http_app.py`:

```python
    @app.post("/login")
    def login() -> Response:
        data = _payload()
        return jsonify(token=service.login(data.get("username", ""), data.get("password", "")))
```

`src/notes_evidence/interfaces/http_app.py`:

```python
    @app.get("/notes/<int:note_id>")
    def get_note(note_id: int) -> Response:
        return jsonify(_note_json(service.get_note(actor(), note_id)))
```

`src/notes_evidence/interfaces/http_app.py`:

```python
    @app.delete("/notes/<int:note_id>")
    def delete_note(note_id: int) -> tuple[str, int]:
        service.delete_note(actor(), note_id)
        return "", 204
```

Routes: `POST /login` returns a token; `GET /notes/<int:note_id>` reads one note (`<int:note_id>` accepts only digits and passes an
integer); `DELETE` answers `204` with no body. `PUT /users/<username>/role` grants a role.

`src/notes_evidence/interfaces/http_app.py`:

```python
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
```

Domain errors become status codes in one place: validation to `400`, bad or missing credentials to `401`, a role that lacks a
permission to `403`, a missing note to `404`. The routes contain no `try` blocks.

`Makefile`:

```make
smoke: ## the API container answers /healthz
	curl -fsS http://127.0.0.1:$(HTTP_PORT)/healthz
```

`curl -fsS URL`: `-f` makes curl fail (exit code 22) on an HTTP error status; `-s` hides the progress meter; `-S` still shows an
error message when it does fail.

## Try it yourself

Not run while this note was written: the machine was out of capacity, so no container was started. The expected output comes from the repository's own verified runs (the README and `evidence/`).

```bash
make api-up && make smoke
```
Builds and starts the API beside the database; `smoke` prints `{"status":"ok"}`.

```bash
curl -s -X POST http://127.0.0.1:8080/login -H 'Content-Type: application/json' -d '{"username":"ada","password":"wrong"}'; echo
```
Prints `{"error":"invalid username or password"}` (HTTP 401).

```bash
curl -s -o /dev/null -w "%{http_code}\n" http://127.0.0.1:8080/notes
```
Prints `401`: no bearer token.

```bash
curl -s -o /dev/null -w "%{http_code}\n" http://127.0.0.1:8080/nothing
```
Prints `404`.

```bash
make down
```
Stops the containers and deletes the database volume.

## Mistakes people make

- **Returning 200 for everything** and hiding the error in the body. Status codes are part of the contract.
- **Telling an attacker too much** (`unknown user` versus `wrong password`). Login failures say the same thing.
- **Logging the bearer token.** Only whitelisted fields are logged.
- **Publishing a port on all interfaces.** Compose binds to `127.0.0.1`.
- **Unbounded request bodies.** `MAX_CONTENT_LENGTH` is 64 KiB; larger gets `413`.

## Check yourself

1. What does `401` mean and how is it different from `403`?
   **Answer:** 401: the caller is not logged in; 403: the caller is known but not allowed.
2. What is a bearer token?
   **Answer:** A secret string sent in the `Authorization` header to prove who you are.
3. What does `curl -f` do?
   **Answer:** Fails with a non-zero exit code on an HTTP error status.
4. Why does `DELETE` answer `204`?
   **Answer:** It succeeded and there is no body to return.
5. Where are domain errors turned into status codes?
   **Answer:** In `_register_errors`, in one place.

## Further reading

- HTTP semantics (RFC 9110): <https://www.rfc-editor.org/rfc/rfc9110>
- curl documentation: <https://curl.se/docs/>
- MDN, HTTP status codes: <https://developer.mozilla.org/en-US/docs/Web/HTTP/Status>
