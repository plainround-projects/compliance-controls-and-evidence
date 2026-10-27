# Regular expressions (the re module)

## What it is

A **regular expression** (regex) is a short pattern that describes a set of strings, like `^## (.+)$` for "a line
that starts with `## `". Python's standard `re` module compiles a pattern into an object you can use to **match** a
string, **search** inside it, **find all** matches or **split** it. Parentheses in a pattern make **groups** whose text
you can read back.

## Why this repository uses it

The documents are Markdown text with simple conventions (`## Heading`, `Label: text`, `Phase 3: name`). The
program recognizes them with a handful of regexes and turns them into typed values. The patterns are compiled once, as
module-level constants with a leading underscore.

## Where it appears

| File | What it does with this technology |
| --- | --- |
| `src/notes_evidence/domain/notes.py` | `USERNAME`: the shape of a user name. |
| `src/notes_evidence/domain/evidence.py` | `LOG_LINE`, `TIMESTAMP` and searches that verify the evidence files. |
| `sql/001_schema.sql` | The same user-name rule as a `CHECK` using PostgreSQL's `~` operator. |

## How it works underneath

`re.compile(pattern)` turns the pattern into a small program for matching. `pattern.match(line)` tries to match from
the **start** of the string and returns a match object or `None`. `pattern.search(text)` looks anywhere. A match
object's `.group(1)` is the text of the first parenthesized part. The symbols used here:

| Symbol | Meaning |
| --- | --- |
| `^` and `$` | start and end of the text |
| `.` | any one character |
| `+`, `*`, `?` | one or more, zero or more, optional |
| `+?`, `.*?` | the same but **lazy**: as few characters as possible |
| `\d`, `\s` | a digit, a whitespace character |
| `[A-Z0-9]` | one character from a set |
| `( ... )` | a group to capture |
| `a|b` | a or b |
| `(?<=x)`, `(?=x)` | look-behind and look-ahead: x must come before or after, but is not part of the match |
| `\.` | a literal dot (a backslash cancels a symbol's meaning) |

A string written `r"..."` is a **raw string**: backslashes are kept as they are, which is what patterns need.

## Walkthrough of this repository's use

`src/notes_evidence/domain/notes.py`:

```python
USERNAME = re.compile(r"^[a-z][a-z0-9_-]{1,31}$")
```

`USERNAME` accepts a user name: `^` start, `[a-z]` one lower-case letter first, `[a-z0-9_-]{1,31}` between 1 and 31 more
letters, digits, underscores or hyphens (`{1,31}` is a count), `$` end. So `ada` and `chen-2` pass; `Ada`, `1ada` and `a` do not.
The database checks the same rule (`CHECK (username ~ '^[a-z][a-z0-9_-]{1,31}$')` in `sql/001_schema.sql`, where `~` is
PostgreSQL's regex match), so a name that gets past the code is still refused by the table.

`src/notes_evidence/domain/evidence.py`:

```python
LOG_LINE = re.compile(
    r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z user=\S+ id=\S+ action=[a-z_]+ note=\S+ outcome=[a-z]+( \w+=\S+)*$"
)
TIMESTAMP = re.compile(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z")
```

`LOG_LINE` describes a valid line of the C3 log sample: a timestamp (`\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z`), then
`user=` and a value without spaces (`\S+`), `id=`, `action=` and lower-case letters or underscores, `note=`, `outcome=`, and any
number of further `key=value` pairs (`( \w+=\S+)*`). `\S` means "not whitespace", `\w` means "letter, digit or underscore".
The verifier uses it to prove that every line of the sample carries a user, an id and an action.

`src/notes_evidence/domain/evidence.py`:

```python
    action = re.search(r"test action at (" + TIMESTAMP.pattern + ")", text)
    alert = re.search(r"ALERT \[[a-z-]+\] (" + TIMESTAMP.pattern + ")", text)
```

Patterns built from other patterns: `TIMESTAMP.pattern` is pasted inside a bigger pattern, and the parentheses capture the
timestamp. The check finds the time of the **test action** and the time of the **alert**, then compares them (the alert must
follow the action).

`src/notes_evidence/domain/evidence.py`:

```python
        removed = re.findall(r"^Removed: (.+)\.$", review, re.MULTILINE)
```

`re.findall` returns every match. `^Removed: (.+)\.$` with `re.MULTILINE` finds the lines of the access review that say what was
removed. `.+` is greedy and `\.` is a literal full stop.

## Try it yourself

```bash
.venv/bin/python -c "from notes_evidence.domain.notes import USERNAME; print([bool(USERNAME.match(n)) for n in ('ada', 'chen-2', 'Ada', '1ada', 'a')])"
```
Prints `[True, True, False, False, False]`.

```bash
.venv/bin/python -c "from notes_evidence.domain.evidence import LOG_LINE; print(bool(LOG_LINE.match('2026-10-27T01:33:59Z user=bruno id=2 action=note_created note=12401 outcome=ok')))"
```
Prints `True`.

```bash
.venv/bin/python -c "from notes_evidence.domain.evidence import TIMESTAMP; print(TIMESTAMP.findall('from 2026-10-27T01:33:59Z to 2026-10-27T01:34:10Z'))"
```
Prints the two timestamps as a list.

```bash
grep -c LOG_LINE.match src/notes_evidence/domain/evidence.py; head -2 evidence/C3-log-sample.txt
```
Shows that the sample's first lines have the shape the pattern requires.

## Mistakes people make

- **Forgetting `r` before the string**, so `\d` is read as a plain `d` with a warning.
- **Greedy matching** that grabs too much: `.+` versus `.+?`.
- **Using `match` when `search` is needed** (`match` only matches at the start).
- **Parsing nested structure with a regex.** Here the patterns recognize single lines, and the code groups lines itself.
- **Not escaping user text** when it is placed inside a pattern. `re.escape` does that (used in the field parser).

## Check yourself

1. What does `{1,31}` mean in the user-name pattern?
   **Answer:** Between 1 and 31 repetitions of the item before it.
2. What is the difference between `\S` and `\w`?
   **Answer:** `\S` is any character that is not whitespace; `\w` is a letter, digit or underscore.
3. Why does the database repeat the user-name rule?
   **Answer:** So a name that got past the code is still refused by the table.
4. What does `re.findall(..., re.MULTILINE)` return?
   **Answer:** A list of every match, with `^` and `$` working on each line.
5. How is a bigger pattern built from `TIMESTAMP`?
   **Answer:** The `.pattern` text is joined into the new pattern string.

## Further reading

- `re` (Python 3.12): <https://docs.python.org/3.12/library/re.html>
- Regular Expression HOWTO: <https://docs.python.org/3.12/howto/regex.html>
