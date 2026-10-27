# pathlib and file access

## What it is

`pathlib.Path` is the standard Python way to work with file and folder names. A `Path` object knows how to join
names with `/`, ask whether something exists, read and write text, and list a folder. It works the same on macOS,
Linux and Windows.

## Why this repository uses it

The program reads the repository's documents and writes a report. All file access goes through one small class
(`FileSystemStore`), which also refuses paths that escape the root folder.

## Where it appears

| File | What it does with this technology |
| --- | --- |
| `src/notes_evidence/infrastructure/evidence_store.py` | `FileEvidenceStore`: the only code that writes the evidence folder. |
| `src/notes_evidence/infrastructure/alerting.py` | `FileAlertSink` appends alerts to a file. |
| `src/notes_evidence/infrastructure/sources.py` | Reads the fixture JSON files; `StateCloudDirectory` keeps a state file. |
| `src/notes_evidence/infrastructure/settings.py` | Turns folder settings into `Path` values. |
| `tests/**` | `tmp_path` for a throwaway evidence folder. |

## How it works underneath

- A `Path` is only a name until you use it. `Path("docs") / "adr"` builds `docs/adr` without touching the disk.
- `.read_text(encoding="utf-8")` opens the file, reads all of it as text using that encoding, and closes it.
- `.resolve()` makes a path absolute and follows `..` and symbolic links. Comparing resolved paths is the safe way to
  test "is this inside that folder".
- `.parents` is the chain of containing folders.

## Walkthrough of this repository's use

`src/notes_evidence/infrastructure/evidence_store.py`:

```python
class FileEvidenceStore:
    """Files under one folder. Names may not leave it."""

    def __init__(self, directory: Path) -> None:
        self._dir = directory.resolve()

    def _path(self, name: str) -> Path:
        path = (self._dir / name).resolve()
```

- `directory.resolve()` stores the absolute folder.
- `(self._dir / name).resolve()` joins and normalizes; `path.parent != self._dir` rejects any name that is not directly inside
  the evidence folder (`../x`, `sub/x` or an absolute path), so a collector can never write outside it.

`src/notes_evidence/infrastructure/evidence_store.py`:

```python
    def write(self, name: str, text: str, control: str, produced_at: datetime, run_by: str, source: str) -> None:
        """Write the file and record it in the manifest (the index itself is recorded under control '-')."""
        self._dir.mkdir(parents=True, exist_ok=True)
        self._path(name).write_text(text, encoding="utf-8")
        entries = self._load()
        entries[name] = {
            "control": control,
            "produced_at": produced_at.astimezone(UTC).strftime(_TIME),
            "run_by": run_by,
            "source": source,
            "sha256": digest(text),
        }
        self._path(MANIFEST).write_text(json.dumps(entries, indent=2, sort_keys=True) + "\n", encoding="utf-8")
```

- `self._dir.mkdir(parents=True, exist_ok=True)` creates the folder if needed.
- `write_text(text, encoding="utf-8")` writes the file.
- `produced_at.astimezone(UTC).strftime(_TIME)` formats the time in UTC as `2026-10-27T01:34:10Z`.
- The manifest is rewritten each time, as sorted JSON (see `json.md`). The SHA-256 of the text is recorded (see
  `hashing-and-signing.md`).

`src/notes_evidence/infrastructure/evidence_store.py`:

```python
    def read_all(self) -> dict[str, str]:
        """Every file in the folder."""
        if not self._dir.is_dir():
            return {}
        return {path.name: path.read_text(encoding="utf-8") for path in sorted(self._dir.iterdir()) if path.is_file()}
```

`self._dir.iterdir()` lists the folder, `sorted(...)` makes the order stable, `path.is_file()` skips folders, and a dictionary
comprehension reads each file. The verifier uses it to find files that no control claims.

`src/notes_evidence/infrastructure/alerting.py`:

```python
    def send(self, message: str) -> None:
        """Deliver one alert."""
        self._path.parent.mkdir(parents=True, exist_ok=True)
        with self._path.open("a", encoding="utf-8") as stream:
            stream.write(message + "\n")
```

`self._path.open("a", encoding="utf-8")` opens the file for **appending**: each alert is added at the end.

## Try it yourself

```bash
ls evidence
```
Lists the pack: `C1-access-list.txt`, `C2-changes.csv`, `C3-alert-test.txt`, `C3-log-sample.txt`, `C4-restore-test.txt`,
`C5-scan-report.json`, `C6-access-review.md`, `INDEX.md`, `manifest.json`.

```bash
.venv/bin/python -c "from pathlib import Path; p = Path('evidence') / 'C2-changes.csv'; print(p, p.exists(), p.suffix, p.parent)"
```
Prints `evidence/C2-changes.csv True .csv evidence`.

```bash
.venv/bin/python -c "from pathlib import Path; from notes_evidence.infrastructure.evidence_store import FileEvidenceStore; FileEvidenceStore(Path('evidence')).read('../x')" 2>&1 | tail -1
```
Prints `ValueError: evidence files live directly in evidence: ../x`.

```bash
.venv/bin/python -c "from pathlib import Path; from notes_evidence.infrastructure.evidence_store import FileEvidenceStore; print(sorted(FileEvidenceStore(Path('evidence')).manifest()))"
```
Prints the names recorded in the manifest.

## Mistakes people make

- **Joining paths with `+`** and a slash character. Use `/`.
- **Forgetting the encoding** on Windows, where the default is not UTF-8.
- **Comparing unresolved paths**, so `docs/../x` looks like it is inside `docs`.
- **Letting user-supplied names reach the disk unchecked.** The store checks every path.

## Check yourself

1. Why does `_path` compare `path.parent` with the evidence folder?
   **Answer:** To refuse any name that would leave the folder.
2. What does opening a file with mode `"a"` do?
   **Answer:** Appends to the end instead of replacing the file.
3. What does `Path.resolve()` do?
   **Answer:** Makes the path absolute and removes `..` and links.
4. Why is `iterdir()` wrapped in `sorted()`?
   **Answer:** So the order is the same on every machine.
5. What does `mkdir(parents=True, exist_ok=True)` do?
   **Answer:** Creates the folder and missing parents; no error if it exists.

## Further reading

- `pathlib` (Python 3.12): <https://docs.python.org/3.12/library/pathlib.html>
