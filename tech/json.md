# JSON

## What it is

JSON (JavaScript Object Notation) is a text format for data made of objects (`{"key": value}`), arrays (`[1, 2]`), text in double
quotes, numbers, `true`, `false` and `null`. Every language can read it. `json.dumps` turns Python values into JSON text;
`json.loads` turns it back.

## Why this repository uses it

JSON is the common language between the pieces: the Flask API reads and answers JSON, the fixtures copy the shape of what the
`gh` and `aws` tools print, the manifest records each evidence file, the logs are one JSON object per line, and the database
stores an event's `detail` as JSON (`jsonb`).

## Where it appears

| File | What it does with this technology |
| --- | --- |
| `fixtures/*.json` | Made-up output of `gh` and `aws` for fixture mode. |
| `evidence/manifest.json` | Who produced each file, when, and its SHA-256. |
| `evidence/C5-scan-report.json` | The pip-audit scan with a run id. |
| `src/notes_evidence/infrastructure/logging_setup.py` | One JSON object per log line. |
| `src/notes_evidence/interfaces/http_app.py` | `jsonify` for every API answer. |
| `sql/001_schema.sql` | `detail jsonb` in the audit log. |

## How it works underneath

JSON text is parsed into Python `dict`, `list`, `str`, `int`, `float`, `bool` and `None`. `sort_keys=True` writes the keys in
alphabetical order, so two runs produce identical text and the same hash. `indent=2` adds line breaks for people. A value that
JSON cannot hold (a `datetime`) must be turned into text first (here with `.isoformat()` or `strftime`).

## Walkthrough of this repository's use

`fixtures/github-merged-prs.json`:

```json
[
  {
    "number": 38,
    "title": "Change 38",
    "author": {
      "login": "bruno"
    },
    "mergedAt": "2026-10-14T10:15:04Z",
    "mergeCommit": {
      "oid": "39f5f753633ed25f14992533aa82e522c3311423"
    },
    "reviews": [
      {
        "state": "APPROVED",
```

The fixture has the same shape as `gh pr list --json ...` prints, so the same parser works on a file and on the real command
(see `subprocess.md`). The parser reads `pr["mergeCommit"]["oid"]` and the reviews.

`src/notes_evidence/infrastructure/sources.py`:

```python
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
```

- `{item["commit"]: item["deploy_id"] for item in deploys}` is a **dictionary comprehension**: commit to deploy id.
- `sorted({review["author"]["login"] for ... if review["state"] == "APPROVED"})` builds a **set comprehension** (no duplicates)
  of the logins that approved, then sorts it.
- `datetime.fromisoformat(pr["mergedAt"].replace("Z", "+00:00"))` turns `2026-10-14T10:15:04Z` into a timezone-aware time.

`src/notes_evidence/infrastructure/evidence_store.py`:

```python
        entries[name] = {
            "control": control,
            "produced_at": produced_at.astimezone(UTC).strftime(_TIME),
            "run_by": run_by,
            "source": source,
            "sha256": digest(text),
        }
        self._path(MANIFEST).write_text(json.dumps(entries, indent=2, sort_keys=True) + "\n", encoding="utf-8")
```

`src/notes_evidence/infrastructure/evidence_store.py`:

```python
        self._path(MANIFEST).write_text(json.dumps(entries, indent=2, sort_keys=True) + "\n", encoding="utf-8")
```

The manifest is a JSON object keyed by file name. `json.dumps(entries, indent=2, sort_keys=True) + "\n"` writes sorted, indented
JSON with a final newline, so the file is stable and diffs are small.

`evidence/manifest.json`:

```json
{
  "C1-access-list.txt": {
    "control": "C1",
    "produced_at": "2026-10-27T01:37:07Z",
    "run_by": "ada",
    "sha256": "ba099eb7874505e0ef36f1988b63bab3a7df1baf0f48b497054929427bb9b84e",
    "source": "fixture"
  },
```

One entry as it is stored. The verifier recomputes the SHA-256 of the file and compares it with `sha256`; an edited file is caught.

`src/notes_evidence/infrastructure/logging_setup.py`:

```python
class JsonFormatter(logging.Formatter):
    """One JSON object per line."""

    def format(self, record: logging.LogRecord) -> str:
        """Render a record; only the whitelisted extra fields are included."""
        document = {
            "time": datetime.fromtimestamp(record.created, UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        document.update({name: getattr(record, name) for name in _SAFE_FIELDS if hasattr(record, name)})
        return json.dumps(document)
```

A log formatter that writes one JSON object per line: time, level, logger, message, plus only the **whitelisted** extra fields
(`method`, `path`, `status`, `user_id`, `duration_ms`). Nothing else can leak into a log line, so a password or a note body never
appears. See `logging.md`.

`src/notes_evidence/interfaces/http_app.py`:

```python
def _payload() -> dict[str, Any]:
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        raise ValidationError("body", "a JSON object is required")
    return data
```

`request.get_json(silent=True)` returns the parsed body, or `None` for bad JSON; anything that is not an object is refused with
`400`.

## Try it yourself

```bash
head -8 evidence/manifest.json
```
Shows the first manifest entry: `control`, `produced_at`, `run_by`, `sha256`, `source`.

```bash
.venv/bin/python -m json.tool fixtures/aws-iam-users.json | head -8
```
Pretty-prints a fixture with Python's built-in tool.

```bash
.venv/bin/python -c "import json; print(json.dumps({'b': 1, 'a': [None, True]}, sort_keys=True), json.loads('[1, 2, 3]'))"
```
Prints `{"a": [null, true], "b": 1}` and `[1, 2, 3]`.

```bash
.venv/bin/python -c "import json; json.loads('{bad')" 2>&1 | tail -1
```
Prints `json.decoder.JSONDecodeError: Expecting property name enclosed in double quotes: ...`.

```bash
.venv/bin/python -c "import json, hashlib; t = open('evidence/C1-access-list.txt').read(); m = json.load(open('evidence/manifest.json')); print(hashlib.sha256(t.encode()).hexdigest() == m['C1-access-list.txt']['sha256'])"
```
Prints `True`: the file still matches its manifest entry.

## Mistakes people make

- **Single quotes or trailing commas** in JSON.
- **Putting secrets or note text into logs.** The formatter writes only whitelisted fields.
- **Unsorted keys** when a hash of the text is needed; `sort_keys=True` makes the text stable.
- **Parsing a request body without checking its shape.** `_payload` insists on an object.

## Check yourself

1. What does `sort_keys=True` buy here?
   **Answer:** The same data always gives the same text, so the same hash and small diffs.
2. What is a set comprehension?
   **Answer:** `{x for x in items if ...}`: a set built by a loop, with no duplicates.
3. Why are log fields whitelisted?
   **Answer:** So nothing unexpected, such as a secret, can end up in a log line.
4. What does `get_json(silent=True)` return for invalid JSON?
   **Answer:** `None`, instead of raising an error.
5. Why do the fixtures copy the shape of the real tools' output?
   **Answer:** So the same parser serves both fixture and live mode.

## Further reading

- `json` (Python 3.12): <https://docs.python.org/3.12/library/json.html>
- JSON (RFC 8259): <https://www.rfc-editor.org/rfc/rfc8259>
