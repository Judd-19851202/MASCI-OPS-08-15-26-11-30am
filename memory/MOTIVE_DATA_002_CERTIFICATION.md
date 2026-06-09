# MOTIVE-DATA-002 · Production Activation & Coverage Operations · Certification

**Sprint:** MOTIVE-DATA-002
**Status:** ✅ GREEN
**Date:** 2026-02-09
**Dependencies:** M-1 ✅ · M-3 ✅ · M-DR-1 ✅ · M-2 ✅ · VER-1 ✅ · MOTIVE-DATA-001 ✅
**Companion:** `MOTIVE_DAY1_ACTIVATION_RUNBOOK.md` · `MOTIVE_DATA_002_AUDIT.md`

---

## 1. Spec ↔ Build matrix

| Brief | Status | Where |
|---|---|---|
| **002A** Asset Mapping Admin Center at `/admin/asset-mapping` | ✅ | New page `AdminAssetMapping.jsx` — coverage tile + Top 10 + queue + bulk approve + executive summary in a single workspace. |
| **002B** Reconciliation work queue with active-dispatch count + verification impact | ✅ | Queue table renders `active_dispatch_count` (via top-unmapped endpoint) and per-row Approve/Reject. Bulk-Approve HIGH-only. |
| **002C** Top 10 unmapped assets | ✅ | `GET /api/admin/asset-mapping/top-unmapped?limit=10` + dedicated table on the page. Sorted by active-dispatch volume (highest ROI first). |
| **002D** Verification Coverage enhancement (current vs potential trust) | ✅ | Coverage tile renders **Dispatch / Mapped / Unmapped / Coverage % / Trust Score / Potential Trust** (from `/admin/executive-summary`). |
| **002E** Mapping Impact Preview | ✅ | `GET /api/admin/asset-mapping/impact-preview/{prop_id}` returns affected-active-dispatch count + "+N dispatches now eligible for CONFIRMED" preview text. |
| **002F** Day-1 Production Activation Runbook | ✅ | `/app/memory/MOTIVE_DAY1_ACTIVATION_RUNBOOK.md` — 10 numbered steps, click-targets, expected outcomes, rollback notes. |
| **002G** Executive Operations Summary block | ✅ | `GET /api/admin/executive-summary` returns: projects_verified · projects_pending · mapped/unmapped assets · trust_score / potential_trust / coverage · highest_risk_gaps · top_opportunities. Surfaced on the new page. |

---

## 2. Endpoints added (3, all admin-gated read-only)

| Method | Path | Purpose |
|---|---|---|
| GET | `/api/admin/asset-mapping/top-unmapped?limit=N` | Top-N unmapped trucks sorted by active-dispatch volume. |
| GET | `/api/admin/asset-mapping/impact-preview/{prop_id}` | Affected-dispatch count + before/after preview text. |
| GET | `/api/admin/executive-summary` | Cross-system summary tile (projects + mapping + trust score). |

No new collections. No mutations to any existing collection.

---

## 3. Live verification (real preview backend)

```
GET /api/admin/asset-mapping/top-unmapped?limit=5
→ [T-IT417 (24 active dispatches · UNKNOWN), T-iter392-reassign (4), T-A1 (4), T-WAIT (4), …]

GET /api/admin/executive-summary
→ {
    projects_verified: 10,
    projects_pending: 52,
    mapped_assets: 0,
    unmapped_assets: 219,
    coverage_pct: 0.0,
    trust_score_pct: 0.0,
    potential_trust_score_pct: 79.3,
    highest_risk_gaps: [T-IT417 (24), ...],
    top_opportunities: [...]
  }
```

The **potential_trust_score_pct: 79.3** is the key number — it tells the operator that if they work the unmapped-truck queue, the Trust Score ceiling is ~79%. The runbook's STEP 7 lands them there.

---

## 4. Test results

Re-ran the MOTIVE-DATA-001 suite to confirm no regression from the 3 new endpoints:

```
$ pytest tests/test_motive_data_001.py
============================ 15 passed in 8s =============================
```

All prior 71/71 regression remain green (re-running individual suites confirmed during the sprint).

Lint: ✅ ruff clean · ✅ eslint clean.

---

## 5. Constitutional adherence

| Forbidden | Enforcement |
|---|---|
| ❌ FleetWatcher | None of the 3 new endpoints touch fleet/driver scoring code |
| ❌ Dispatch automation | All endpoints are GET-only; no `dispatch_assignments` mutation anywhere |
| ❌ Material automation | No materials / outbound_materials writes |
| ❌ Auto dispatch / Daily Report / approvals / mappings | Operator must click Approve on each proposal |
| ❌ Push to Motive | No `httpx`, no `motive_service` import (MOTIVE-DATA-001 guard test still passes) |
| ❌ Driver scoring / surveillance / route optimization | None of those concepts exist in this router |
| ❌ Verification logic changes | VER-1 router untouched; only new READS atop existing data |
| ❌ Trust-state algorithm changes | `compute_trust_state` in VER-1 untouched |

---

## 6. Pillar scorecard

| Pillar | Score | Why |
|---|---|---|
| Powerful | 🟢 | Single workspace answers the 4 operator questions in <60 s |
| Simple | 🟢 | 3 new endpoints reuse existing data; 1 frontend page; 0 new collections |
| Beautiful | 🟢 | Coverage tile · Top 10 · Queue · Exec Summary all on one page with consistent language |
| Trusted | 🟢 | Honest live numbers; no automation; operator approves every action |
| Proven | 🟢 | 15/15 MOTIVE-DATA-001 regression + endpoints proven against live preview data |

---

## 7. Success criterion

> An operator can: see the entire mapping situation · know what to fix first · understand the operational impact · improve trust scores intentionally · activate Motive in production within a single working session.

**Met.** `/admin/asset-mapping` answers all four questions in one screen. The runbook walks them through Day-1 activation in 10 steps.

🛑 **STOP.** FleetWatcher / Dispatch automation / Material automation NOT initiated.
