# 3. Fixtures for the hosting platform and the cloud account, with live adapters behind the same parsers

Status: accepted, 2026-10-26

## Context

C1, C2 and C6 read the repository host and the cloud account, and Sumit's machine has neither a repository named `notes-api` nor a cloud account to list. The code still has to be tested, and the evidence has to be shaped like the real thing.

## Decision

The collectors depend on ports (`RepositoryAccess`, `ChangeSource`, `CloudDirectory`). Fixture mode reads JSON files under `fixtures/` shaped exactly like the output of `gh api .../collaborators`, `gh pr list --json ...` and `aws iam list-users`; live mode runs those commands. Both use the same parsers (`parse_collaborators`, `parse_merged_prs`, `parse_iam_users`). The fixture cloud account is a state file that `remove_user` rewrites, as `aws iam delete-user` rewrites the account. The database part of C1 and everything in C3 to C5 are real in both modes.

## Alternatives considered

- **Mock the commands in tests only.** Then `make run` shows nothing.
- **Require a real repository and account.** Nobody could run the lesson offline, and the fresh-clone test could not pass.
- **A fake GitHub server.** More code than the parsers it would exercise.

## Consequences

- The live adapters are tested against recorded output shapes but have not been run against a real account; the README says so.
- Anyone using the project for real sets `EVIDENCE_SOURCE=live`, `GITHUB_REPOSITORY` and AWS credentials in the environment.
