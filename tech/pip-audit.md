# pip-audit

## What it is

A **vulnerability** is a known security flaw in a published version of a package. Databases list them, each with an
ID (like `PYSEC-2024-1` or `GHSA-xxxx`) and the versions that are fixed. **pip-audit** takes a list of packages and
versions, asks such a database, and reports any match.

## Why this repository uses it

The dev tools run on your machine and in CI. A pinned version stays the same, so a flaw found later would go
unnoticed without a regular check. `make audit` is that check, and CI runs it on every push.

## Where it appears

| File | What it does with this technology |
| --- | --- |
| `Makefile` `audit` | Runs `pip-audit` on `requirements-dev.lock`. |
| .github/workflows/ci.yml | Runs `make audit`. |
| `requirements-dev.lock` | The input. |

## How it works underneath

pip-audit reads each `name==version` from the file and sends the list to a public vulnerability service (by default,
the Python Packaging Advisory Database through PyPI's API). The service answers with the advisories for those
versions. pip-audit prints a table and exits non-zero if it finds any. It needs network access.

## Walkthrough of this repository's use

`Makefile`:

```make
audit: $(STAMP) ## check the locked dependencies for known vulnerabilities
	$(VENV)/bin/pip-audit --no-deps --disable-pip -r requirements-dev.lock
```

- `pip-audit`: the program, from `.venv/bin`.
- `--no-deps`: do not work out dependencies; use the list as given. This requires every line to be pinned to an exact
  version, which the lock file is.
- `--disable-pip`: do not call `pip` to resolve anything. pip-audit allows this only for hashed requirement files
  or with `--no-deps`. Here both hold.
- `-r requirements-dev.lock`: read requirements from that file.

Because the file is hash-pinned and fully resolved, the audit sees exactly what `pip` installs, and needs no
installation to run.

## Try it yourself

```bash
.venv/bin/pip-audit --version
```
Prints `pip-audit 2.10.1`.

```bash
make audit
```
With network access: two `WARNING` lines about hashing, then `No known vulnerabilities found`. Without network: an
error about reaching the service (not a pass).

```bash
.venv/bin/pip-audit --help | grep -A2 -- "--no-deps"
```
Shows the flag's explanation for the pinned version.

```bash
.venv/bin/pip-audit --no-deps --disable-pip -r requirements-dev.lock -f json | head -c 300
```
Prints the same result in machine-readable JSON.

## Mistakes people make

- **Reading "no known vulnerabilities" as "safe".** It means none are known to the database today.
- **Running it offline** and thinking the error is a pass. It is not a pass.
- **Auditing the wrong file.** The dev tools are in `requirements-dev.lock`; the runtime lock has no packages.
- **Ignoring a finding** without a written reason. If an advisory has no fix, use `--ignore-vuln ID` and record why.

## Check yourself

1. What does `--no-deps` require of the input?
   **Answer:** Every package must be pinned to an exact version.
2. Why can `--disable-pip` be used here?
   **Answer:** The requirements file is hashed and fully resolved, so pip is not needed to resolve it.
3. Does `make audit` work offline?
   **Answer:** No, it asks a vulnerability service over the network.
4. When is a new run useful even if the lock file did not change?
   **Answer:** When a new vulnerability has been published for a pinned version.
5. What does the audit not check?
   **Answer:** Our own code, or the build backend downloaded at install time.

## Further reading

- pip-audit 2.10: <https://github.com/pypa/pip-audit>
- Python Packaging Advisory Database: <https://github.com/pypa/advisory-database>
