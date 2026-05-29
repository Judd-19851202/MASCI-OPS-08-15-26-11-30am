# M0.2 · ODR Public-Link Continuity Probe Report

_Generated 2026-05-29 · env=preview · db=masci_safety_preview._

This is the human-readable companion to the probe-generated
`/app/memory/ODR_PUBLIC_LINK_CONTINUITY_PROBE_REPORT.md` (auto-refreshed
on every probe run).

## Probe purpose

Defend the ODR Public Link Continuity contract:

> "An ODR generated today must remain accessible tomorrow, next month,
> next year, and during future audits."

## Probe surface

Eight invariants over the live Mongo (read-only):

| ID | Invariant |
|---|---|
| C1 | Unique public `link_id` across `odr_public_links` |
| C2 | Every `odr.public_access.link_id` resolves in the registry |
| C3 | Every registry row references an existing ODR |
| C4 | `doc_id` format `ODR-YYYY-NNNNN` |
| C5 | `doc_id` uniqueness across `odr` collection |
| C6 | No two ODRs share an active `link_id` |
| C7 | `odr_preload_attempts.outcome` ∈ closed enum |
| C8 | `odr_preload_attempts` count never shrinks (append-only · snapshot-anchored) |

## Live result (M0.2 ship)

```
odr_public_link_continuity_probe · env=preview · db=masci_safety_preview
  ODRs=5  links=2  with_link=2  attempts=5
  failures=0  warnings=0
  ✅ all checks passed
```

## Snapshot anchor

`/app/memory/ODR_PROBE_CONTINUITY_SNAPSHOT.json` carries the last
known-good counts. The C8 check fails if the live count drops below
the snapshot — defending against silent ledger deletions or rollback
contamination.

## Gate integration

The probe is wired into `/app/scripts/pre_deploy_check.sh` as a
hard-blocking stage:

```
run_stage "Phase V.1 · ODR public-link continuity probe" stage_odr_continuity
```

The probe runs in < 1 second over current preview data.

## Failure response (operator playbook)

| Failure | Most likely cause | Remediation |
|---|---|---|
| C1 duplicate link_id | direct Mongo mutation bypassing `mint_link` | regenerate the link via API · investigate the bypass |
| C2 orphan link on ODR | `odr_public_links` row deleted | restore from backup · re-mint |
| C3 link references missing ODR | ODR document deleted (forbidden) | restore from backup · audit hard-delete trail |
| C4 bad doc_id format | counter overflow / external import | upgrade counter handling · fix imports |
| C5 dup doc_id | counter race | enforce unique index (already in place); investigate races |
| C6 shared active link_id | direct Mongo update set link_id on two ODRs | revoke one · re-mint the other |
| C7 invalid outcome enum | code change introduced a new outcome string | update `ALLOWED_OUTCOMES` AND `PreloadAttemptOutcome` enum together |
| C8 append-only violation | someone deleted preload_attempts rows | restore from backup · investigate write path |

## Status

🟢 **GREEN.** Continuity contract intact. Probe ready for production.
