# 1. Evidence is produced by commands and recorded with a hash

Status: accepted, 2026-10-26

## Context

An auditor asks "show me". A hand-made list proves only that someone typed it, and a screenshot cannot be produced again. The lesson asks for artifacts a system produced, dated, and repeatable.

## Decision

Every artifact is written by a collector (`controls-evidence <step>`) that reads the system itself. The collector also writes `evidence/manifest.json` with the control, the time, who ran it, the source mode (fixture or live) and the SHA-256 of the file. `verify` recomputes each hash, so a file edited by hand fails (EVD003).

## Alternatives considered

- **Files only, no manifest.** The pack looks the same, but nothing says who made a file or when, and an edit is invisible.
- **Sign each file with a key.** Stronger against a malicious editor, but it needs key management the lesson does not scope in; the manifest is in the same repository, so a person who can edit the file can edit the manifest. The hash catches mistakes and casual edits, not an attacker (ARCHITECTURE.md, limits).
- **Store the evidence outside the repository.** Better in production (write-once storage); here the committed pack is a sample for the reader.

## Consequences

- `make verify` is a real check: it fails on a missing file, an empty one, an unclaimed one, a hash mismatch and content that does not say what the control needs.
- Re-running `make run` rewrites the pack with new timestamps, so the sample in `evidence/` shows a diff on every run.
