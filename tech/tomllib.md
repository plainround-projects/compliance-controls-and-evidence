# tomllib (reading the control matrix)

## What it is

`tomllib` is the standard Python module that reads TOML text (see `toml.md`). `tomllib.loads(text)` returns nested dictionaries and
lists. It can only read TOML, not write it.

## Why this repository uses it

The control matrix is **data**: which control needs which evidence, which framework clauses it answers, which gaps and
exceptions are known. Keeping it in TOML lets the verifier compare it with the real evidence folder and fail when they disagree.

## Where it appears

| File | What it does with this technology |
| --- | --- |
| `src/notes_evidence/infrastructure/catalog.py` | `TomlCatalog`: one method per file. |
| `controls/controls.toml` | The controls and their evidence specs. |
| `controls/exceptions.toml`, `gaps.toml`, `people.toml`, `access-review.toml` | Known deviations, tracked gaps, people, the reviewer's decisions. |

## How it works underneath

`tomllib.loads` parses the text into dictionaries. `[[control]]` blocks make a list under the key `control`; a nested
`[[control.evidence]]` adds to the list of the control just above it. Bad syntax raises `tomllib.TOMLDecodeError`. TOML checks
syntax only, so the catalog checks meaning.

## Walkthrough of this repository's use

`src/notes_evidence/infrastructure/catalog.py`:

```python
def _load(path: Path) -> dict[str, Any]:
    try:
        return tomllib.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        raise CatalogError(f"{path} does not exist") from None
    except tomllib.TOMLDecodeError as problem:
        raise CatalogError(f"{path} is not valid TOML: {problem}") from None
```

A missing file and a syntax error each become a `CatalogError` with a clear message. `from None` hides the library's traceback.

`src/notes_evidence/infrastructure/catalog.py`:

```python
    def controls(self) -> list[Control]:
        """The controls with their evidence specs; an unknown evidence kind is an error."""
        found: list[Control] = []
        for item in _load(self._controls_file).get("control", []):
            try:
                specs = tuple(
                    EvidenceSpec(e["file"], e["kind"], e["proves"], e["period"], int(e["refresh_days"]), e["refreshed"])
                    for e in item.get("evidence", [])
                )
                if bad := [spec.kind for spec in specs if spec.kind not in KINDS]:
                    raise CatalogError(f"{item['id']}: unknown evidence kind {bad[0]!r}")
                found.append(
                    Control(
                        item["id"],
                        item["name"],
                        item["requires"],
                        item["where"],
                        {name: tuple(item.get(name, ())) for name in FRAMEWORKS},
                        specs,
                    )
                )
            except KeyError as missing:
                raise CatalogError(f"{self._controls_file}: control is missing {missing}") from None
        return found
```

- `_load(...).get("control", [])` is the list of control tables, or an empty list.
- A **generator expression** builds one `EvidenceSpec` per `[[control.evidence]]` item; `int(e["refresh_days"])` converts the
  number.
- The **walrus** `bad := [...]` collects unknown evidence kinds and tests them in one step; an unknown kind raises
  `CatalogError`.
- `{name: tuple(item.get(name, ())) for name in FRAMEWORKS}` reads each framework's list (`iso27001`, `soc2`), or an empty tuple.
- A missing required key raises `KeyError`, caught as `control is missing 'key'`.

`src/notes_evidence/infrastructure/catalog.py`:

```python
def _date(raw: object) -> date | None:
    return raw if isinstance(raw, date) else None
```

TOML has its own date type; `tomllib` returns a Python `date` for `due = 2026-12-01`, so the helper accepts only that.

## Try it yourself

```bash
.venv/bin/python -c "import tomllib; d = tomllib.load(open('controls/controls.toml','rb')); print([c['id'] for c in d['control']], d['control'][0]['evidence'][0]['file'])"
```
Prints the control ids and `C1-access-list.txt`.

```bash
make verify
```
Reads the catalog and the evidence folder and prints `OK: 9 files checked, 0 errors, 0 warnings`.

```bash
.venv/bin/python -c "import tomllib; print(tomllib.loads('due = 2026-12-01'))"
```
Prints `{'due': datetime.date(2026, 12, 1)}`.

```bash
.venv/bin/python -c "import tomllib; tomllib.loads('x = ')" 2>&1 | tail -1
```
Prints a `TOMLDecodeError`.

## Mistakes people make

- **Opening the file in text mode** for `tomllib.load`: it needs binary. This code uses `loads` on text.
- **Trusting parsed values.** The catalog rejects unknown evidence kinds and missing keys.
- **Letting the matrix drift from the evidence.** `make verify` fails when it does.

## Check yourself

1. What does a nested `[[control.evidence]]` belong to?
   **Answer:** The control defined just above it.
2. What type does TOML give a date like `2026-12-01`?
   **Answer:** A Python `date`.
3. Why wrap errors in `CatalogError`?
   **Answer:** The command line turns it into one message and exit code 2.
4. What does `make verify` compare?
   **Answer:** The control matrix with the files in the evidence folder and their manifest.
5. What does the walrus `:=` do in `if bad := [...]`?
   **Answer:** Assigns the list and tests it in one step.

## Further reading

- `tomllib` (Python 3.12): <https://docs.python.org/3.12/library/tomllib.html>
- TOML 1.0.0: <https://toml.io/en/v1.0.0>
