# PHASE 29 · Stability Governance
## iter431 · 2026-05-25

## Protected collections (NEVER touched by stability governance)
| Collection                          | Why                                            |
|-------------------------------------|------------------------------------------------|
| `dispatch_assignments`              | Operational truth · audit-trail                |
| `dispatch_continuity_events`        | Operational memory · doctrine-locked           |
| `operational_attachments`           | Append-only evidence proof                     |
| `legacy_imports` + `_audit`         | Accountability records                         |
| `backup_runs` + `_drift_watch`      | Survivability records                          |
| `users_*`, `user_passkeys`, `roles` | Identity / access truth                        |
| `safety_*`, `hr_*`, `pm_*` records  | Compliance / employment data                   |
| `tenants`, `projects`, `equipment`  | Operational catalogue                          |

## Transient collections (eligible for sweep)
| Collection                          | Retention                                  | Mechanism            |
|-------------------------------------|--------------------------------------------|----------------------|
| `dispatch_driver_sessions`          | Revoked OR older than 14 days              | sweep                |
| `webauthn_challenges`               | Older than 24 hours                        | TTL index + sweep    |
| `temp_upload_chunks`                | Older than 24 hours                        | TTL index + sweep    |
| `offline_replay_records`            | `state=replayed` AND older than 7 days     | sweep                |

## Module
`backend/lib/stability_governance.py`
- `ensure_stability_ttls(db)` — idempotent TTL index ensures on every
  startup. Skipped lines never overwrite an existing TTL config.
- `sweep_driver_sessions(db, dry_run=...)` — revoked-OR-aged rule
- `sweep_webauthn_challenges(db, dry_run=...)`
- `sweep_temp_upload_chunks(db, dry_run=...)`
- `sweep_offline_replay_records(db, dry_run=...)` — `state=replayed`
  AND `created_at < cutoff` (unreplayed records never touched)
- `run_stability_sweep(db, dry_run=True)` — orchestrator

## API
`POST /api/admin-strict/stability/sweep?dry_run={bool}`
- Admin-strict only · JSON only · NO UI.
- DRY-RUN BY DEFAULT. Operator must pass `?dry_run=false` to delete.
- Returns per-collection counts so the operator sees exactly what
  was (or would be) removed.

## Cadence
- TTL ensures: every backend startup (cheap, idempotent).
- Sweep: operator-triggered only this phase. Auto-cron deferred to a
  future phase once we have a week of dry-run data to verify nothing
  surprising shows up.

## Retention doctrine
1. **Operational truth is permanent**. Assignments, attachments,
   continuity events, audit rows — NEVER deleted by governance.
2. **Identity is permanent**. Users, passkeys, roles, tenants — NEVER
   deleted by governance.
3. **Transient artifacts have explicit lifetimes**. Sessions, WebAuthn
   challenges, temp chunks, replayed offline records — explicit grace
   windows enforced via TTL and/or sweep.
4. **Dry-run before apply, always**. Every sweep API call defaults to
   `dry_run=true`. The apply path requires explicit operator action.

## Orphan protection
The sweepers DELIBERATELY do NOT delete:
- attachments whose host assignment is gone (might still be operational
  proof for litigation)
- continuity events whose assignment is gone (same)
- legacy_imports rows in any state (accountability)

Orphan cleanup, if ever needed, is a separate, deliberate, operator-
approved operation — never a default sweep.

## Verification
`tests/test_iter431_phase29.py` covers:
- dry-run honours the no-delete contract
- offline_replay sweep PROTECTS unreplayed rows even when old
- aggregate sweep returns per-collection counts
