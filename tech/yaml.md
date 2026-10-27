# YAML

## What it is

YAML is a text format for structured data: names with values, lists, and nested groups. It uses **indentation**
(spaces, never tabs) to show what belongs to what. People like it because it is easy to read. It is also easy to break
with one wrong space.

## Why this repository uses it

GitHub Actions requires its workflow files to be YAML. This repository has exactly one YAML file.

## Where it appears

| File | What it does with this technology |
| --- | --- |
| .github/workflows/ci.yml | The workflow. |
| .editorconfig | Sets the indent to 2 spaces for `*.yml` and `*.yaml` files. |

## How it works underneath

A YAML parser reads the file line by line and builds a tree:
- `key: value` makes a **mapping** (name to value).
- A line starting with `- ` makes an item in a **list** (a sequence).
- More indentation means "inside the line above".
- `# text` is a comment.
- `"3.12"` in quotes is a string; `3.12` bare is a number; `[push, pull_request]` is a list written on one line.
GitHub's runner reads the tree and decides what to run.

## Walkthrough of this repository's use

`.github/workflows/ci.yml`:

```yaml
on: [push, pull_request]
```

A mapping key `on` whose value is a list written inline.

`.github/workflows/ci.yml`:

```yaml
jobs:
  check:
    name: Format, lint, types, import rules, unit tests with coverage, dependency audit, the scan as a build artifact (C5)
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
```

Nesting: `jobs` holds `check`; `check` holds `name`, `runs-on` and `steps`; `steps` is a list. The first step has a
single key, `uses`. The second step has two keys, `uses` and `with`, and `with` holds `python-version`.

## Try it yourself

```bash
.venv/bin/python -c "import tomllib; print('tomllib is built in')"
.venv/bin/python -c "import yaml" 2>&1 | tail -1
```
The first prints `tomllib is built in`. The second prints `ModuleNotFoundError: No module named 'yaml'`: Python has
a built-in TOML reader but no YAML reader, and this project has no use for one.

```bash
grep -c '^      - ' .github/workflows/ci.yml
```
Counts the steps (lines that start with six spaces and a dash): `12`.

```bash
sed -n 8,10p .github/workflows/ci.yml | cat -et
```
`cat -et` shows end-of-line marks (`$`) and tabs (`^I`). A YAML file must show no `^I` in the indentation.

## Mistakes people make

- **Tabs for indentation.** YAML forbids them.
- **Inconsistent indentation**, which changes the meaning rather than only looking untidy.
- **Unquoted values** that look like other types (`3.10`, `yes`, `no`, `on`).
- **Copy-pasting** a list item at the wrong depth.

## Check yourself

1. How does YAML show that one item is inside another?
   **Answer:** By indenting it further with spaces.
2. How do you write a list?
   **Answer:** One item per line starting with `- `, or inline in brackets: `[a, b]`.
3. Why is `"3.12"` quoted in `ci.yml`?
   **Answer:** To make it a string, not the number 3.12.
4. Can YAML use tab characters to indent?
   **Answer:** No.
5. What indent size does `.editorconfig` set for YAML?
   **Answer:** 2 spaces.

## Further reading

- YAML 1.2.2 specification: <https://yaml.org/spec/1.2.2/>
