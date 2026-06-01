# Phase 1A · Deployment Plan

**Program:** OMEGA · PCP · Phase 1A · Final Build Package
**Pattern:** Mirrors iter446 production-deploy pattern (preview → preview-cert → operator deploys via Emergent button → production-cert)
**Date:** 2026-06-01

---

## 1 · Deployment phases

| Phase | Owner | Duration |
|---|---|---|
| 1. Build + unit tests pass | Agent (during Sprint B1-B5) | ~12.5 days |
| 2. Preview deploy (supervisor restart) | Agent · auto on code change | seconds |
| 3. Preview certification battery | Agent | ~10 min |
| 4. `PHASE1A_PREVIEW_CERTIFICATION.md` produced | Agent | ~5 min |
| 5. Operator review + GO/NO-GO | **Operator** | varies |
| 6. Production deploy (Emergent button) | **Operator** | ~5-8 min |
| 7. Production certification battery | Agent | ~10 min |
| 8. `PHASE1A_PRODUCTION_CERTIFICATION.md` produced | Agent | ~5 min |
| 9. Operator monitors first 24h | **Operator** | passive |

---

## 2 · Pre-deploy gates (mandatory)

Before requesting operator production-deploy authorization:

| Gate | Required outcome |
|---|---|
| All unit tests pass (≥95% coverage on new code) | ✅ |
| All integration tests pass | ✅ |
| All backwards-compat regression tests pass (~225 tests · 0 failures) | ✅ |
| Migration dry-run on production-mirror DB · 0 errors | ✅ |
| Lint clean (ruff + eslint) | ✅ |
| Frontend smoke test of all 7 modified pages | ✅ |
| Audit collection indexes created on backend startup | ✅ |
| Preview-cert probe battery (14 probes) all green | ✅ |

If any gate fails, operator is NOT asked to deploy.

---

## 3 · Preview deployment

### 3.1 · Deploy mechanism

Backend hot-reloads on file save. Supervisor restart needed only if:
* `.env` changes (no `.env` changes planned for Phase 1A)
* New Python packages installed (no new packages for Phase 1A · `motor`, `pydantic`, `fastapi` only)

Frontend hot-reloads on file save.

No supervisor restart required for code-only changes. ~zero downtime.

### 3.2 · Preview environment

* URL: `REACT_APP_BACKEND_URL` (preview pod)
* MongoDB: preview DB (separate from production)
* Migration: runs at first backend boot post-deploy · idempotent

### 3.3 · Preview cert probes (14 total)

Reuses the inventory from `PHASE1A_CERTIFICATION_PLAN.md` §4:

1. `POST /api/incidents/{id}/transition {to_state: "IN_PROGRESS"}` → 200
2. Same with HR token → 403
3. Same with invalid to_state → 422
4. Same rapidly twice → 409
5. Frontend: state pill renders correctly
6. Frontend: reopen button gating
7. `/api/admin/workflow-state-events` returns paginated history
8. Migration: every incident has `lifecycle_state` post-startup
9. OSHA-recordable closure without attestation → 422
10. Super-Admin override path → 200 with audit marker
11. DR return-to-field triggers notification row
12. Accountability projection envelope unchanged (regression)
13. Command Center cards still render (regression)
14. Photo Viewer raw endpoint unchanged (regression)

Plus 6 OC-005-specific probes:

15. `POST /api/jhas/{jha_id}/acknowledgements` (FL token, signature) → 200
16. Coverage dashboard returns expected envelope
17. Public token submission works
18. Duplicate ack from same crew member rejected
19. Soft-delete with reason works · audit row written
20. Super-Admin restore works

**Total: 20 preview probes. All must pass before operator deploy authorization.**

---

## 4 · Production deployment

### 4.1 · Authorization protocol

Per iter446 pattern:
1. Agent submits `PHASE1A_PREVIEW_CERTIFICATION.md` with all 20 probes green
2. Operator reviews
3. Operator clicks "Deploy" button in Emergent platform
4. Deploy takes ~5-8 minutes
5. Agent re-probes `/api/version` for new `source_hash`
6. Agent runs production probe battery

### 4.2 · Deploy artifact verification

Post-deploy verification matrix (mirrors iter446 §6):

| Artifact | Expected |
|---|---|
| Backend `source_hash` | new value · different from pre-deploy |
| `/api/admin/workflow-state-events` (authed) | 200 with envelope |
| `/api/jha-acknowledgements/coverage` (authed) | 200 with envelope |
| `/api/incidents/{id}/transition` route registered | 401 unauthed · proves route exists |
| `/api/jhas/{id}/acknowledgements` route registered | 401 unauthed |
| Sanity: unknown admin route | 404 |
| Frontend main bundle | contains new test-ids: `lifecycle-panel-incident` · `lifecycle-btn-*` · `jha-ack-modal` · `admin-tile-jha-coverage` |
| Migration: production incidents all have `lifecycle_state` | sample query |
| Accountability snapshot envelope | unchanged shape |
| Command Center cards | render |

### 4.3 · Production cert probes

Same 20 probes as preview-cert, executed against `https://mascidocs.com`.

### 4.4 · Production deploy timing

Per `PHASE1A_CERTIFICATION_PLAN.md` recommended window:
* **Tue-Wed daytime ET** (≥48h from any high-volume operational event)
* Avoid Friday afternoon (no weekend availability for issue triage)
* Avoid within 24h of Monday digest fire (cushion for any unrelated regression)

---

## 5 · Post-deploy monitoring (first 24h)

| Hour | Action |
|---|---|
| 0-2 | Operator monitors `/admin/workflow-state-events` for any unexpected rows · checks Sentry for new errors · validates first few production transitions |
| 2-6 | Spot-check 3 incidents in production: confirm `lifecycle_state` populated + per-doc history endpoint working |
| 6-24 | First real user transitions (Safety closes an incident · PM reviews a DR · Sandy decides payroll rows · FL acknowledges a JHA) |
| 24h | Operator declares Phase 1A 🟢 ACCEPTED or 🟡 ISSUES FOUND |

---

## 6 · Communication template

After successful production cert, agent produces:
* `PHASE1A_PRODUCTION_CERTIFICATION.md` (operator one-pager)
* Executive operator summary with:
  * What was deployed (6 workflows · 19 new endpoints · 2 new collections)
  * What users will notice (LifecyclePanel everywhere · JHA acknowledgement flow)
  * What's now possible (Sandy can close payroll batches · Safety can close incidents · etc.)
  * What's still gated for Phase 1B+ (vocab canonicalization · placeholders)

---

## 7 · OMEGA discipline

🟢 Deployment pattern documented · mirrors iter446 · 20 preview cert probes · 20 production cert probes · operator-owned deploy authorization · post-deploy monitoring schedule.

🛑 Continue to `PHASE1A_ROLLBACK_PLAN.md`.
