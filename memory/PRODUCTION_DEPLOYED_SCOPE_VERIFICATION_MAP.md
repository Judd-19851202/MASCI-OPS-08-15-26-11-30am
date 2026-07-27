# PRODUCTION DEPLOYED SCOPE VERIFICATION MAP

Purpose: map the recently verified Preview/deployment work to the Production verification sweep.

---

## 1. Recently verified in Preview before deployment

### Deployment / runtime / trust surfaces

- `/api/admin/deployment-readiness` expected coherent pass posture
- `/api/admin/platform-trust/validate` expected secret-safe payload and zero unknown audit statuses
- `/api/admin/recovery/snapshot` reachable
- `/api/admin/trust-spine` reachable
- `/api/admin/integrations/truth-status` reachable
- `/api/admin/backup-verification/state` reachable
- `/api/admin/scheduler-runs` reachable

### Auth / session continuity

- Super admin login works
- Representative portal users authenticate successfully
- disabled account remains fail-closed
- admin routes require valid admin + bound directory session behavior where applicable

### Frontend/browser readiness

- Admin login and key admin routes passed
- PM / HR / Safety / Dispatch / Shop / Field Leadership logins passed in Preview
- protected-route fail-closed behavior passed
- responsive checks passed in Preview

---

## 2. Production-specific areas that must be re-verified live

These cannot be inferred from Preview alone:

- Production domain/runtime identity
- Production secrets / env parity
- Production database authority / data shape
- Production storage/R2 behavior
- Production login credentials and grants
- Production-only provider connectivity
- Production-only scheduler/runtime posture

---

## 3. PM schedule / cost-code lane truth

### Verified built in code

- Admin universal cost registry exists
- Project cost-code assignments exist
- PM project schedule exists
- rolling 14-day schedule exists
- projected finish / critical path / progress exist
- DOT schedule PDF export exists
- Monday Look-Behind surface exists

### Not yet proven as full end-to-end business closure

- structured week-prior failure review loop
- structured “why it failed” capture tied to schedule/cost-code misses
- fully computed Monday Look-Behind readiness engine
- automatic feedback from prior-week miss analysis into next rolling schedule

### Production verification objective for this lane

- verify the built surfaces are alive and usable in Production
- separate “feature exists and works” from “whole business process is fully complete”

---

## 4. Existing production-oriented artifact found in repo

There is already a production smoke script in the codebase:

- `backend/scripts/production_smoke_test.py`

It covers:

- Daily Report creation
- Excavation record creation
- DR ↔ Excavation linking
- photo upload endpoint reachability
- competent person roster
- trench box validation flag
- road plate validation flag
- reinspection request
- oversight chips

Use this as a targeted live smoke lane in addition to the broader platform checklist.
