# dataclasses

## What it is

A **dataclass** is a class that mainly holds data. You list the fields with their types, and Python writes the
boring methods for you: `__init__` (to create the object), `__repr__` (to print it) and `__eq__` (to compare two
objects by their fields). The decorator `@dataclass` does the work. `frozen=True` makes the object read-only after it
is created.

## Why this repository uses it

Everything the program passes around is a value: a finding, a report, a parsed record, a set of settings. Frozen
values cannot be changed behind your back, are easy to compare in tests, and print readably when a test fails.

## Where it appears

| File | What it does with this technology |
| --- | --- |
| `src/notes_evidence/domain/findings.py` | `Finding`, `Report`. |
| `src/notes_evidence/domain/notes.py`, `audit.py` | `User`, `Note`, `AuditEvent`. |
| `src/notes_evidence/domain/evidence.py`, `controls.py`, `changes.py`, `restore.py`, `scan.py` | `ManifestEntry`, `Control`, `EvidenceSpec`, `MergedChange`, `RestoreResult`, `ScanReport`. |
| `src/notes_evidence/infrastructure/settings.py` | `Settings`: twenty settings, read once. |
| `src/notes_evidence/interfaces/wiring.py` | `Runtime`: the adapters the programs share. |

## How it works underneath

At import time, `@dataclass` looks at the class's annotated fields and **generates source code** for `__init__`,
`__repr__` and `__eq__` and attaches it to the class. With `frozen=True` it also generates `__setattr__` and
`__delattr__` methods that raise `FrozenInstanceError`, and a `__hash__`, so frozen objects can be dictionary keys or
set members. The fields are stored in the object like ordinary attributes.

## Walkthrough of this repository's use

`src/notes_evidence/domain/findings.py`:

```python
@dataclass(frozen=True)
class Finding:
    """One rule violation. The code names the rule so a test and a reader can point at it."""

    code: str
    severity: Severity
    subject: str
    message: str
```

- `@dataclass(frozen=True)` writes `__init__`, `__repr__` and `__eq__` and forbids changing fields afterwards.
- `code: str` and the three lines below are **fields**: a name, a colon, a type.

`src/notes_evidence/domain/findings.py`:

```python
@dataclass(frozen=True)
class Report:
    """Every finding from one run, plus the subjects that were checked."""

    subjects: tuple[str, ...]
    findings: tuple[Finding, ...]
```

`tuple[str, ...]` fields hold immutable sequences, so the whole report stays unchangeable.

`src/notes_evidence/domain/audit.py`:

```python
@dataclass(frozen=True)
class AuditEvent:
    """One line of the audit trail. `detail` holds short facts such as the role granted, never a caller's free text."""

    at: datetime
    user_id: int | None
    username: str
    action: AuditAction
    note_id: int | None
    outcome: str
    detail: dict[str, str] = field(default_factory=dict)


def format_timestamp(moment: datetime) -> str:
```

`AuditEvent` has a `detail` dictionary with a default. Dataclasses refuse a mutable default such as `{}` written directly; the
`field(default_factory=dict)` form (the import line shows `field`) creates a new dictionary for every event.

`src/notes_evidence/domain/evidence.py`:

```python
@dataclass(frozen=True)
class ManifestEntry:
    """What a collector recorded about the file it wrote."""

    file: str
    control: str
    produced_at: datetime
    run_by: str
    source: str
```

The manifest entry is the record of one evidence file: control, time, who ran the collector, where the data came from and its
SHA-256. A frozen object cannot be edited after it is made, which suits evidence.

`src/notes_evidence/infrastructure/settings.py`:

```python
@dataclass(frozen=True)
class Settings:
    """Everything the programs read from the environment."""

    database_url: str
    admin_database_url: str
    secret: str
    token_ttl_seconds: int
    retention_days: int
    statement_timeout_ms: int
    evidence_dir: Path
    controls_file: Path
    evidence_source: str
    run_by: str
    state_dir: Path
    log_level: str
    http_port: int
    db_exec_prefix: tuple[str, ...]
    postgres_user: str
    postgres_db: str
```

`Settings` is long but plain: every field a program may need, typed, built once by `load_settings` and never changed. Two
settings are tuples (`db_exec_prefix: tuple[str, ...]`), because a list could be changed by accident.

## Try it yourself

```bash
.venv/bin/python - <<'EOF'
from notes_evidence.domain.findings import Finding, Severity
f = Finding("X1", Severity.ERROR, "a.md", "oops")
print(f == Finding("X1", Severity.ERROR, "a.md", "oops"))
try:
    f.code = "Y"
except Exception as e:
    print(type(e).__name__)
EOF
```
Prints `True` and then `FrozenInstanceError`.

```bash
.venv/bin/python -c "from dataclasses import fields; from notes_evidence.domain.findings import Finding; print([x.name for x in fields(Finding)])"
```
Prints `['code', 'severity', 'subject', 'message']`.

```bash
.venv/bin/python -c "from dataclasses import replace; from notes_evidence.domain.findings import Finding, Severity; f = Finding('A', Severity.ERROR, 's', 'm'); print(replace(f, code='B').code, f.code)"
```
Prints `B A`: a changed copy, the original untouched.

```bash
grep -rn "@dataclass" src | wc -l
```
Counts the dataclasses in the code.

## Mistakes people make

- **A mutable default** such as `items: list = []`. Dataclasses reject it; use `field(default_factory=list)` or an
  immutable tuple.
- **Forgetting `frozen=True`** and letting values change by accident.
- **Assuming frozen means deeply frozen.** A frozen dataclass holding a list can still have the list changed. These
  classes hold tuples.
- **Comparing floats by `==`** in a dataclass field. Use a tolerance in tests.

## Check yourself

1. What does `@dataclass` write for you?
   **Answer:** `__init__`, `__repr__` and `__eq__` (and more, with options).
2. What does `frozen=True` do?
   **Answer:** It makes assigning to a field after creation raise `FrozenInstanceError`.
3. How do you change one field of a frozen object?
   **Answer:** Make a copy with `dataclasses.replace(obj, field=value)`.
4. Why use `tuple[str, ...]` rather than `list[str]` in a frozen class?
   **Answer:** A tuple cannot be changed, so the object stays unchangeable.
5. When does `__post_init__` run?
   **Answer:** Right after the generated `__init__`, to validate the fields.

## Further reading

- `dataclasses` (Python 3.12): <https://docs.python.org/3.12/library/dataclasses.html>
