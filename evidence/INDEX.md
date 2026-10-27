# Evidence pack index

Pack date: 2026-10-27T01:37:07Z. Each file below was produced by a command in this repository (`make evidence`); `manifest.json` records its hash, so a hand edit fails `make verify`.

| File | Control | Proves | Run by | Date | Period | Refreshed |
| --- | --- | --- | --- | --- | --- | --- |
| C1-access-list.txt | C1 Access control | who can do what today, in each system | ada | 2026-10-27 | point in time | weekly |
| C2-changes.csv | C2 Change management | reviewed, traceable changes, from approval to deployment | ada | 2026-10-27 | sample of recent merges | weekly |
| C3-log-sample.txt | C3 Logging and monitoring | who did what and when, without note content | ada | 2026-10-27 | sample | weekly |
| C3-alert-test.txt | C3 Logging and monitoring | the alert fires on a test event, with its timestamp beside the action | ada | 2026-10-27 | point in time | monthly |
| C4-restore-test.txt | C4 Backup and recovery | a real restore into a scratch database, verified by row count, with its duration | ada | 2026-10-27 | point in time | monthly |
| C5-scan-report.json | C5 Vulnerability management | the dependency scan of a build, with its run id and the blocking rule | ada | 2026-10-27 | every build | every build |
| C6-access-review.md | C6 Access review | a reviewer decided every access; the removed access is gone on a re-run | ada | 2026-10-27 | quarterly point in time | quarterly |

## Exceptions

- EXC-1 (C2): Pull request 43 was a hotfix merged without an approver. Follow-up: SEC-16: a retroactive review by bruno and chen was recorded the next morning.

## Tracked gaps

- C7: Backups are written unencrypted to the scratch volume; encryption at rest is a storage setting that is planned, not yet enabled. Ticket SEC-21, due 2026-12-01.

## Framework mapping

| Framework | Reference | Controls |
| --- | --- | --- |
| iso27001 | A.5.15 | C1 |
| iso27001 | A.5.18 | C1, C6 (overlap) |
| iso27001 | A.8.13 | C4 |
| iso27001 | A.8.15 | C3 |
| iso27001 | A.8.16 | C3 |
| iso27001 | A.8.2 | C1, C6 (overlap) |
| iso27001 | A.8.24 | C7 |
| iso27001 | A.8.32 | C2 |
| iso27001 | A.8.8 | C5 |
| soc2 | A1.2 | C4 |
| soc2 | A1.3 | C4 |
| soc2 | CC6.1 | C1, C7 (overlap) |
| soc2 | CC6.2 | C6 |
| soc2 | CC6.3 | C1, C6 (overlap) |
| soc2 | CC7.1 | C5 |
| soc2 | CC7.2 | C3 |
| soc2 | CC8.1 | C2 |
