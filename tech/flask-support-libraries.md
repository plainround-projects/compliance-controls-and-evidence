# Werkzeug, Jinja2, ItsDangerous, Blinker, Click and MarkupSafe

## What it is

Flask is built from smaller libraries, and `requirements.lock` pins each of them. **Werkzeug** handles HTTP details (requests,
responses, routing). **Jinja2** is a template engine for HTML pages. **MarkupSafe** escapes text so it is safe inside HTML.
**ItsDangerous** signs data (Flask uses it for session cookies). **Blinker** provides signals (events). **Click** builds command
lines (Flask's `flask` command).

## Why this repository uses it

It does not use them directly. They are installed because Flask needs them, and the lock file pins and hashes them like everything
else. This API returns JSON only, so Jinja2, MarkupSafe and ItsDangerous's cookie signing are not exercised.

## Where it appears

| File | What it does with this technology |
| --- | --- |
| `requirements.lock` | `werkzeug==3.1.9`, `jinja2==3.1.6`, `itsdangerous==2.2.0`, `blinker==1.9.0`, `click==8.5.0`, `markupsafe`. |
| `src/notes_evidence/interfaces/http_app.py` | Flask's request and response objects are Werkzeug's underneath. |
| `# via` comments in the lock file | Show which package pulled each one in. |

## How it works underneath

When Flask routes a request, Werkzeug's router matches the path against the rules (`/notes/<int:note_id>`) and converts the
digits to an integer. Werkzeug builds the `Request` and sends the `Response`. Everything else on this list is imported by Flask at
start-up but not used by this API's JSON routes.

## Walkthrough of this repository's use

`requirements.lock`:

```text
werkzeug==3.1.9 \
    --hash=sha256:55ca7c70a75689be937aa27f8ff4b018f06ff4838fc73045560bf0f5a1291060 \
    --hash=sha256:6392e50c78460ba618e5b21f08a71f59c99ce99cdc6cf6e3dd7e6ccca8754fab
    # via flask
```

Each package appears with its exact version and hashes. The comment `# via flask` says Flask asked for it.

`requirements.lock`:

```text
markupsafe==3.0.4 \
    --hash=sha256:007e1ffd9bf65bb6ee96df7b258fc632a4868dd5566037986c64781f35a36e98 \
    --hash=sha256:02fa4acbc6a3fc5c693c34d4dd8c1130b7fe99cc915181b0ddd6f72aeb296002 \
```

MarkupSafe is installed because Jinja2 needs it, and Jinja2 because Flask does. A **transitive dependency** chain like this is why
the lock file pins everything, not just the packages the project names.

`src/notes_evidence/interfaces/http_app.py`:

```python
    @app.get("/notes/<int:note_id>")
    def get_note(note_id: int) -> Response:
        return jsonify(_note_json(service.get_note(actor(), note_id)))
```

`<int:note_id>` is a Werkzeug **converter**: the router only matches digits and passes an `int`. A request for `/notes/abc` never
reaches the function; it gets a `404`, which the app's `404` handler turns into JSON.

## Try it yourself

```bash
.venv/bin/pip list 2>/dev/null | grep -iE "^(flask|werkzeug|jinja2|itsdangerous|blinker|click|markupsafe) "
```
Prints the seven packages with their versions.

```bash
.venv/bin/pip show flask | grep -E "^(Name|Version|Requires)"
```
Prints Flask's name, version and the packages it requires.

```bash
grep -B1 -A4 "^werkzeug==" requirements.lock | cut -c1-90
```
Shows the pin, the hashes and the `# via` line.

```bash
.venv/bin/python -c "from werkzeug.routing import Map, Rule; m = Map([Rule('/notes/<int:n>', endpoint='note')]).bind(''); print(m.match('/notes/7'))"
```
Prints `('note', {'n': 7})`.

## Mistakes people make

- **Importing a transitive package directly** without adding it to `pyproject.toml`. It could disappear when Flask changes.
- **Updating one of them by hand.** Regenerate the lock file instead.
- **Assuming "installed" means "used".** The API returns JSON only.

## Check yourself

1. What does Werkzeug do for Flask?
   **Answer:** HTTP details: request and response objects and URL routing.
2. Why are packages this API never calls still pinned?
   **Answer:** Flask imports them, so they are installed and must be trusted and reproducible.
3. What does `<int:note_id>` do?
   **Answer:** Matches only digits and passes an integer.
4. What does `# via flask` in the lock file mean?
   **Answer:** Flask is the reason the package is installed.
5. What is a transitive dependency?
   **Answer:** A package your dependencies need, not one you named.

## Further reading

- Werkzeug 3.1: <https://werkzeug.palletsprojects.com/en/stable/>
- Jinja 3.1: <https://jinja.palletsprojects.com/en/stable/>
- ItsDangerous 2.2: <https://itsdangerous.palletsprojects.com/en/stable/>
- Blinker 1.9: <https://blinker.readthedocs.io/en/stable/>
- Click 8: <https://click.palletsprojects.com/en/stable/>
- MarkupSafe: <https://markupsafe.palletsprojects.com/en/stable/>
