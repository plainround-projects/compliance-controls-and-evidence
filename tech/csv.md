# CSV

## What it is

CSV (comma-separated values) is a text format for tables: one line per row, cells separated by commas. A cell with a comma or a
quote in it must be wrapped in double quotes, and quotes inside are doubled. Spreadsheets open CSV directly.

## Why this repository uses it

Control C2 (change management) needs a record that links each merged change to its approvers and to what was deployed. A
reviewer will open it in a spreadsheet, so CSV is the natural format. The program writes it, and the verifier reads it back to
find exceptions.

## Where it appears

| File | What it does with this technology |
| --- | --- |
| `src/notes_evidence/domain/changes.py` | `render_changes` writes the CSV; `exceptions_in_csv` reads it. |
| `evidence/C2-changes.csv` | The artifact. |
| `src/notes_evidence/domain/evidence.py` | Checks the header of the file. |

## How it works underneath

`csv.writer(file)` writes rows; it quotes cells as needed. `quoting=csv.QUOTE_NONNUMERIC` quotes every cell that is not a number.
`lineterminator="\n"` ends each row with a line feed. `csv.DictReader` reads the first row as column names and returns each later
row as a dictionary. `io.StringIO` is a text file that lives in memory, so the code can build the text without touching the disk.

## Walkthrough of this repository's use

`src/notes_evidence/domain/changes.py`:

```python
def render_changes(changes: list[MergedChange]) -> str:
    """The artifact as CSV: strings quoted, the number bare, approvers joined with '+'."""
    buffer = io.StringIO()
    writer = csv.writer(buffer, quoting=csv.QUOTE_NONNUMERIC, lineterminator="\n")
    writer.writerow(HEADER)
    for change in sorted(changes, key=lambda item: item.number):
        writer.writerow(
            [
                change.number,
                change.author,
                format_timestamp(change.merged_at),
                change.commit[:7],
                "+".join(change.approvers),
                change.deploy_id,
            ]
        )
    return buffer.getvalue()
```

- `io.StringIO()` is an in-memory text buffer; `buffer.getvalue()` returns everything written to it.
- `csv.writer(..., quoting=csv.QUOTE_NONNUMERIC, lineterminator="\n")` makes text cells quoted and the change number bare.
- `writer.writerow(HEADER)` writes the column names first.
- `sorted(changes, key=lambda item: item.number)` sorts by change number; `key=` takes a function that picks the sort value.
- `change.commit[:7]` is the short commit (first seven characters); `"+".join(change.approvers)` joins names like `ada+bruno`.

`evidence/C2-changes.csv`:

```
"number","author","merged_at","commit","approvers","deploy_id"
38,"bruno","2026-10-14T10:15:04Z","39f5f75","ada","deploy-2026-10-14-38"
39,"chen","2026-10-15T13:02:40Z","cc6f44b","ada+bruno","deploy-2026-10-15-39"
40,"ada","2026-10-19T08:47:19Z","ea0ceff","bruno","deploy-2026-10-19-40"
```

The result. Text cells are quoted, the number is not. An empty `approvers` or `deploy_id` cell would be an exception that the
verifier reports.

`src/notes_evidence/domain/changes.py`:

```python
def exceptions_in_csv(text: str) -> list[ChangeException]:
    """Re-derive the exceptions from a rendered artifact, so the check does not trust the collector."""
    rows = list(csv.DictReader(io.StringIO(text)))
    found: list[ChangeException] = []
    for row in rows:
        approvers = [name for name in row["approvers"].split("+") if name and name != row["author"]]
        if not approvers:
            found.append(ChangeException(int(row["number"]), "merged with no independent approver"))
        if not row["deploy_id"]:
            found.append(ChangeException(int(row["number"]), "no deployment record"))
    return found
```

`csv.DictReader(io.StringIO(text))` reads the artifact back as dictionaries, so the verifier checks the **file on disk**, not the
objects the program had in memory.

## Try it yourself

```bash
cat evidence/C2-changes.csv
```
Prints the header row and one row per merged change.

```bash
.venv/bin/python -c "import csv, io; b = io.StringIO(); w = csv.writer(b, quoting=csv.QUOTE_NONNUMERIC, lineterminator='\n'); w.writerow([38, 'bruno', 'a,b']); print(repr(b.getvalue()))"
```
Prints `'38,"bruno","a,b"\n'`: the cell with a comma is safely quoted.

```bash
.venv/bin/python -c "import csv; print(list(csv.DictReader(open('evidence/C2-changes.csv')))[0])"
```
Prints the first row as a dictionary with the column names as keys.

```bash
.venv/bin/python -c "from notes_evidence.domain.changes import HEADER; print(HEADER)"
```
Prints the six column names.

## Mistakes people make

- **Joining cells with `","`** by hand. A comma inside a cell breaks the row; use `csv`.
- **Forgetting `newline` and `lineterminator`**, which can add blank lines on Windows.
- **Trusting objects in memory** when the file is the evidence. The verifier reads the file.
- **Opening CSV in a spreadsheet and saving it**, which can change quoting and dates.

## Check yourself

1. Why use the `csv` module instead of `",".join(...)`?
   **Answer:** It quotes cells that contain commas or quotes.
2. What is `io.StringIO`?
   **Answer:** A text file kept in memory.
3. What does `QUOTE_NONNUMERIC` do?
   **Answer:** Quotes every cell that is not a number.
4. What does `DictReader` return for each row?
   **Answer:** A dictionary keyed by the column names of the first row.
5. Why does the verifier re-read the CSV file?
   **Answer:** The evidence is the file; it must be checked as stored.

## Further reading

- `csv` (Python 3.12): <https://docs.python.org/3.12/library/csv.html>
- CSV (RFC 4180): <https://www.rfc-editor.org/rfc/rfc4180>
