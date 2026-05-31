# Pillar 1 · Deployment Recommendation

**Batch:** Pillar 1 · Pre-Deployment Operational Certification
**Date:** 2026-05-31
**Verdict:** 🟡 **GO WITH KNOWN LIMITATIONS**

---

## 1 · Decision

🟡 **Approved for production deployment with explicit acknowledgement of inherited Pillar 2 Phase A limitations.**

Pillar 1 (the Accountability Engine: projection library + service router) is functionally correct, has 128/128 pytests passing, zero defects on its own surface, and zero owner mismatches across 25 sampled records. Its production deployment is **low-risk on the Pillar 1 surface itself**.

The "known limitations" refer to **how Pillar 1 is _consumed_ by Pillar 2 Phase A's Command Center** — those defects (D1, D2, D5) are already documented and certified as 🟡 CONDITIONAL GO by `EXECUTIVE_COMMAND_CENTER_CERTIFICATION.md`. Pillar 1 cannot remediate them.

---

## 2 · Three deployment paths

### Path A · Deploy Pillar 1 as-is (RECOMMENDED for fastest path)

**What ships:** `lib/accountability_projection.py` + `routes/accountability_service.py` + `routes/command_center.py` consuming the resolved projections.

**Pros:**
- Operations leadership immediately starts seeing named individuals on resolved owner paths (CAs with assignees, incidents with linked-CA assignees, POs once jobs_master gets PM links).
- Zero code change required.
- 128/128 pytests already green.
- Lower-blast-radius deploy: source workflows untouched, no notification path activated, no escalation path activated, frontend untouched.

**Cons / known limitations being deployed:**
- D1 (SAF-CRITICAL-UNRESOLVED no resolution-state check) carries forward.
- D2 (SAF-OSHA-OPEN no resolution-state check) carries forward.
- D5 (Approvals & Equipment OOS sub-count silently zeros) carries forward.
- JOBS-ISSUE-NO-OWNER predicate/implementation mismatch (only queries CAs not incidents) carries forward.
- 6% TEST_iter pollution in approvals card (preview seed artifact — should disappear on production data).

**Pre-deploy checklist (operator-confirmable):**
1. Confirm `command_center_thresholds` doc exists in production DB and matches version=3 (or accept default-on-first-load).
2. Confirm `command_center_calendar` doc exists in production DB.
3. Confirm frontend `AdminCommandCenter.jsx` md5 matches preview (`4cb825b428e0a4afc1a5cb7eb5b14ec1`).
4. Confirm production DB has the same source collections present in preview: `tasks`, `corrective_actions`, `po_requests`, `fleet_defects`, `incidents`, `jobs_master`.

### Path B · Deploy Pillar 1 + remediate inherited Pillar 2 Phase A D1/D2/D5

**What ships:** Path A + a ~45 LOC patch on `command_center.py` per the Pillar 2 `EXECUTIVE_COMMAND_CENTER_DEPLOYMENT_RECOMMENDATION.md` Path B.

**Pros:**
- Approvals card stops silently zeroing.
- Equipment OOS sub-count starts reporting honestly.
- SAF-CRITICAL/OSHA no longer fires forever on resolved aged incidents.
- FP rate drops from ~22% to ~8% (per Phase A FP review).

**Cons:**
- Requires a separate **explicit Phase 1A-X authorization batch** with the 5 mandatory pillar inputs — _NOT in scope of this read-only certification_.
- ~45 LOC of new code requires fresh pytest authoring + recertification.
- Adds 1-2 days to the deployment timeline.

### Path C · Defer Pillar 1 production deployment until Phase 1A-6 (Dashboard) ships

**What ships:** Nothing yet.

**Pros:**
- A purpose-built Accountability Dashboard could expose the projection layer to operators without going through the Command Center's known defects.
- Lets operators evaluate Pillar 1 in isolation before binding it to Pillar 2's RAG aggregator.

**Cons:**
- Loses the immediate ownership-fidelity uplift on the Command Center's Approvals + Safety cards on production.
- Phase 1A-6 has not yet been scoped or authorized.
- Production already runs Pillar 2 Phase A without Pillar 1; deferring leaves the legacy hardcoded `"Safety"` / `"Pending Approver"` strings live in production drilldowns until the Dashboard ships.

---

## 3 · Recommended path

🟢 **PATH A · Deploy Pillar 1 as-is, with the Pillar 2 Phase A D1/D2/D5 patch deferred to its own authorized batch.**

Rationale:
- Pillar 1 is fully certified standalone.
- Path A delivers immediate operator value: named CA assignees, named PMs (once data populates), named acknowledgers — all without code change.
- D1/D2/D5 are existing production behavior; deploying Pillar 1 does NOT _introduce_ them, it merely surfaces existing data through a more accurate ownership layer.
- Path B work belongs to a Pillar 2 batch, not a Pillar 1 batch — keeps OMEGA batch boundaries clean.
- Path C delays a working improvement for a future product that has not been scoped.

---

## 4 · Post-deploy verification gates (Path A)

If the operator authorizes a future deployment batch on Path A, the gates that must be green before flipping production:

| Gate | Verifiable via | Expected |
|---|---|---|
| `GET /api/admin/accountability/sources` returns 6 sources | `curl -H "X-Admin-Token: …"` against prod | 200 · 6 entries |
| `GET /api/admin/accountability/snapshot?per_source=10` returns projections | same | 200 · projections present · `escalation_level=0` on every row |
| `GET /api/admin/command-center/snapshot` returns 5 cards | same | 200 · 5 cards · pulse reconciles |
| `GET /api/admin/command-center/drilldown/safety/{incident_id}` includes `accountability.owner_*` (4 fields) | same | 200 · accountability sub-doc populated |
| Frontend `/admin/command-center` page renders 5 cards | browser check (Path B recertification pattern) | RAG pills visible · zero JS console errors |
| `AdminCommandCenter.jsx` md5 unchanged | `md5sum` against prod build | `4cb825b428e0a4afc1a5cb7eb5b14ec1` |
| No new collections created | `db.listCollectionNames()` diff | zero new collections |
| Backup scheduler unaffected | `GET /api/admin/backups-scheduler-state` | `alive=true · last_tick < 120s ago` |

---

## 5 · Rollback plan (Path A)

| Trigger | Action | RTO |
|---|---|---|
| Snapshot 500s due to projection bug | revert `routes/command_center.py` to pre-Pillar-1 commit | ~2 min |
| Snapshot 200s but card payload regresses | same | ~2 min |
| Service router endpoint 500s | unmount router from `server.py` (1-line change) | ~2 min |
| Threshold doc corrupted | `command_center_thresholds` falls back to `DEFAULT_THRESHOLDS` in code automatically — no action needed | 0 min |
| Calendar doc corrupted | `command_center_calendar` falls back to defaults — no action needed | 0 min |
| Backup architecture inadvertently touched | covered by Pillar 2 frozen-inventory list — NOT POSSIBLE in this code path | n/a |

---

## 6 · What this verdict is NOT

- ❌ Not authorization to deploy. Operator must issue an explicit Phase 1A-7 (Production Deployment) batch with the 5 mandatory pillar inputs.
- ❌ Not a recommendation to remediate Pillar 2 Phase A defects inside this batch.
- ❌ Not a recommendation to start Phase 1A-6 (Accountability Dashboard).
- ❌ Not a recommendation to start white-label remediation (Pillar 1 modules are already clean; the remaining work belongs to Customer #2 onboarding).

---

## 7 · Closeout

🟡 **GO WITH KNOWN LIMITATIONS · Path A recommended.** Awaiting operator authorization for Phase 1A-7 (Production Deployment) — and explicit acknowledgement of the inherited Pillar 2 Phase A D1/D2/D5 limitations — before any deployment action. **STOP.**
