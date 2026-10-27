# EditorConfig

## What it is

EditorConfig is a tiny file format and a convention. A file called `.editorconfig` states the basic text rules for
a project: character encoding, end-of-line style, indent style and size. Most editors read it (some need a plug-in)
and apply it to every file you save.

## Why this repository uses it

Different editors and operating systems save files differently (Windows line endings, tabs, no final newline). That
creates noisy diffs. A common file keeps the files uniform, and keeps real tab characters in the Makefile.

## Where it appears

| File | What it does with this technology |
| --- | --- |
| .editorconfig | The settings. |
| `Makefile` | Needs tabs; the file forces them. |
| `*.py`, `*.md`, `*.toml`, `*.yml` | Covered by the rules. |

## How it works underneath

The editor looks for `.editorconfig` in the file's folder and each parent folder, up to one marked `root = true`.
Sections in square brackets are **globs** (patterns that match file names). Later sections override earlier ones for
matching files. The editor applies the settings when it opens and saves. EditorConfig does not check files by
itself; it only configures editors.

## Walkthrough of this repository's use

`.editorconfig`:

```ini
root = true

[*]
charset = utf-8
end_of_line = lf
insert_final_newline = true
trim_trailing_whitespace = true
indent_style = space
indent_size = 4
```

- `root = true`: stop looking in parent folders.
- `[*]`: every file.
  - `charset = utf-8`: save as UTF-8, the standard text encoding.
  - `end_of_line = lf`: lines end with a line-feed (Unix style), not carriage-return plus line-feed (Windows).
  - `insert_final_newline = true`: end every file with a newline.
  - `trim_trailing_whitespace = true`: remove spaces at the end of lines.
  - `indent_style = space` and `indent_size = 4`: indent with four spaces (the Python convention).
- `[*.{yml,yaml,json,toml}]` with `indent_size = 2`: these formats use two spaces. The braces in the glob mean "any of
  these endings".

`.editorconfig`:

```ini
[Makefile]
indent_style = tab
```

Make's recipes must start with a tab, so this section overrides the space rule for the Makefile.

`.editorconfig`:

```ini
[*.md]
trim_trailing_whitespace = false
```

In Markdown, two trailing spaces can mean a line break, so trimming is turned off for `*.md`.

## Try it yourself

```bash
cat .editorconfig
```
Prints the file.

```bash
grep -c "$(printf '\t')" Makefile
```
Prints a number above zero: the Makefile's recipe lines begin with tab characters.

```bash
tail -c1 README.md | xxd | head -1
```
The last byte is `0a`, a newline: `insert_final_newline` at work.

```bash
file README.md
```
Shows `ASCII text` (plain English text is valid UTF-8 too) and no mention of `CRLF`, which `file` would add for Windows
line endings.

## Mistakes people make

- **Thinking it enforces anything.** It only tells editors what to do; `ruff format` enforces Python style.
- **Using spaces in the Makefile** because the editor ignored the file.
- **Trimming whitespace in Markdown** when it is meaningful. This file turns trimming off for `*.md`.
- **Forgetting `root = true`**, so settings from a parent folder leak in.

## Check yourself

1. What does `end_of_line = lf` mean?
   **Answer:** Lines end with a single line-feed character, the Unix style.
2. Why does `[Makefile]` set `indent_style = tab`?
   **Answer:** Make recipes must begin with a tab.
3. Does EditorConfig check files in CI?
   **Answer:** No, it only configures editors.
4. What does `root = true` do?
   **Answer:** It stops the editor from reading `.editorconfig` files in parent folders.
5. Why is trailing-whitespace trimming off for Markdown?
   **Answer:** Two trailing spaces can mean a line break there.

## Further reading

- EditorConfig specification and property list: <https://spec.editorconfig.org/>
- Editors and plug-ins: <https://editorconfig.org/>
