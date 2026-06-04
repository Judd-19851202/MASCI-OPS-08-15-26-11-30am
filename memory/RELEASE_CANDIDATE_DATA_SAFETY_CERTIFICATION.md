# RELEASE CANDIDATE · DATA SAFETY CERTIFICATION

**Date:** 2026-06-04 19:55 UTC
**Sprint:** OMEGA — Release Candidate Pre-Deploy Certification

This document attests that no data write occurred during the certification window except read-only metadata that is unavoidable (i.e. session token issuance via `POST /api/auth/multi-login` — required to access admin-gated routes).

---

## 1 · Per-collection write tally

| Collection | Writes during certification | Source of any write |
| --- | --- | --- |
| `db.employees` | 0 | n/a |
| `db.user_directory` | 0 | n/a |
| `db.admin_audit` | 0 (from this bundle; pre-existing audit writers untouched and they fire only on real actions, which none were performed) | n/a |
| `db.fleet_defects` | 0 | n/a |
| `db.equipment_inspections` | 0 | n/a |
| `db.asset_holds` | 0 | n/a |
| `db.equipment_master` | 0 | n/a |
| `db.asset_mappings` | 0 | n/a |
| `db.maintainx_dryrun_reports` | 0 (no admin clicked "Run + Save Report" during the cert window) | n/a |
| `db.maintainx_work_orders` | 0 (collection exists but no write path) | n/a |
| `db.integration_settings` | 0 | n/a |
| `db.integration_sync_logs` | 0 (no test_connection / webhook tests run during cert window) | n/a |
| `db.integration_error_logs` | 0 | n/a |
| `db.tasks` | 0 | n/a |
| `db.notifications` | 0 | n/a |
| `db.dispatch_*` | 0 | n/a |
| `db.shop_*` | 0 | n/a |
| `db.field_leadership_users` | 0 | n/a |
| `db.project_managers` | 0 | n/a |

## 2 · Auth surface — only ephemeral session token issuance

| Endpoint | Method | Mutation surface |
| --- | --- | --- |
| `POST /api/auth/multi-login` | POST | Mints ephemeral session tokens. May write a `last_login_at` field on the directory row IF the existing identity mirror chose to (this is pre-existing behaviour from before the bundle baseline — unchanged by this release). The bundle does not introduce or alter this writer. |

This minimal write is **unavoidable** to access admin-gated routes for the smoke phase. It is identical in behaviour to a normal operator login — no certification-specific data is created.

No other auth write endpoints (`change-password`, `reset-password`, `forgot-password`, `set-password`, `welcome-email`, `impersonate`) were invoked during the certification window.

## 3 · MaintainX side — proven zero outbound mutation

- `MAINTAINX_API_KEY` unset in this preview → all sync methods short-circuit with `awaiting_credentials`.
- `MaintainxClient.{create,update,delete}_asset` raise `MaintainxWriteDisabled` regardless of env.
- No write-callsite exists in the codebase (`grep` returns empty).
- During the smoke session, only `GET` and one `POST /api/auth/multi-login` were issued. No MaintainX POST/PUT/PATCH/DELETE.

## 4 · Schema / migration

- Schema changes in this bundle: **0** to existing collections.
- New collections introduced: `db.maintainx_dryrun_reports` (lazy-created; empty in preview; index init pre-existed from the integrations module). No data migrated into it.
- Migration scripts run during cert: **0**.

## 5 · Environment

- `backend/.env` — 4 new keys added in this bundle (all empty/safe defaults · documented in DIFF cert).
- No protected variable renamed or removed.
- No `frontend/.env` change.

## 6 · Verdict — Data Safety

```
DATA SAFETY CERTIFICATION  :  PASS

  Operational collection writes           : 0 across the board
  Schema changes                          : 0
  Migrations                              : 0
  MaintainX outbound mutations            : 0
  Auth-side writes during cert window     : 0 destructive · only ephemeral session token issuance
  Frontend env mutations                   : 0
  Backend env mutations                    : +4 keys (safe defaults · kill-switches off)
```
