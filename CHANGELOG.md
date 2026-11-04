# Changelog

All notable changes to this project are recorded here. The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and the project uses [Semantic Versioning](https://semver.org/).

## [Unreleased]

### Added

- Drawn architecture and flow figures in `docs/diagrams/`, light and dark, shown in the README.

## [0.1.0] - 2026-10-27

### Added

- The notes API (login, notes, role grants) with three roles, scrypt password hashes, signed expiring tokens, an audit trail that never holds note text, and a health endpoint.
- PostgreSQL schema with least-privilege grants and an append-only audit log enforced by triggers, a retention role, 12,400 seeded notes, the controls' queries.
- Collectors for the six controls (access list, change record, log sample and alert test, restore test, dependency scan, access review), a manifest of hashes, an index, and `verify` with the rules EVD001 to EVD009 and ARV001 to ARV003.
- The control matrix (ISO/IEC 27001:2022 Annex A and SOC 2 references), a recorded exception, a tracked gap (backup encryption), made-up people and a reviewer's decisions.
- Fixtures shaped like `gh` and `aws` output with live adapters behind the same parsers, a Dockerfile and compose file, unit, integration and end-to-end tests, ruff, mypy strict, hash-pinned lock files, and CI workflows including a weekly evidence run.
