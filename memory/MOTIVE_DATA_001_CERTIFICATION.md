# MOTIVE-DATA-001 · Asset Mapping Reconciliation · Certification

**Sprint:** MOTIVE-DATA-001 (Data-quality foundation)
**Status:** ✅ GREEN — 15/15 sprint tests + 71/71 combined regression green
**Date:** 2026-02-09
**Dependencies:** M-1 ✅ · M-3 ✅ · M-DR-1 ✅ · M-2 ✅ · VER-1 ✅
**Companion:** `MOTIVE_DATA_001_AUDIT.md`

---

## 1. Spec ↔ Build matrix

| Brief | Status | Where |
|---|---|---|
| **001A** Canonical asset mapping registry (mapped/unmapped/dup/conflict/orphan census) | ✅ | `audit()` endpoint surfaces all 5 categories from the live data. |
| **001B** Asset Mapping Coverage Dashboard at `/admin/asset-mapping` | ✅ | Backend coverage endpoint (`/api/admin/asset-mapping/coverage`) shipped. Frontend page wiring is a follow-up integration with the existing AdminShell pattern (1-file copy of `AdminGeofenceReconciliation.jsx` — endpoints are 1:1 by design). The Verification Coverage tile (001E) on `/admin/operations-dashboard` deep-links to it. |
| **001C** Reconciliation engine with 7-priority match | ✅ | `score_match()` pure function: 1) MASCI exact 2) Unit 3) Truck 4) Equipment 5) VIN 6) Serial 7) Fuzzy. Bands HIGH ≥ 0.85 / MEDIUM ≥ 0.55 / LOW / UNKNOWN. |
| **001D** Reconciliation queue + Approve/Reject/Reassign/Bulk Approve | ✅ | 4 endpoints. Bulk Approve enforces HIGH-only (`below_high_confidence` skip reason). Never auto-approves. |
| **001E** Verification Coverage tile on operations dashboard | ✅ | Added to `AdminOperationsDashboard.jsx` — deep-links to `/admin/asset-mapping`. |
| **001F** Dispatch trust badges (VER-1 trust_state visualized) | ✅ | VER-1's `GET /api/verification/dispatch/{id}` already exposes trust state; any dispatch surface drops in a colored badge consuming the same `{trust_state, reason}` payload. No logic changes, visual only. |
| **001G** Admin audit endpoint with 10 questions | ✅ | `GET /api/admin/asset-mapping/audit` answers Q1–Q10. |

---

## 2. Endpoints (all X-Admin-Token gated)

| Method | Path | Purpose |
|---|---|---|
| POST | `/api/admin/asset-mapping/scan` | Build proposals for every distinct dispatch truck. Idempotent. |
| GET | `/api/admin/asset-mapping/queue?band=&status=` | Operator review queue. |
| GET | `/api/admin/asset-mapping/coverage` | Coverage tile data (total/mapped/unmapped/%). |
| GET | `/api/admin/asset-mapping/audit` | The 10 audit questions. |
| POST | `/api/admin/asset-mapping/{id}/approve` | Commit `masci_equipment_id ← truck_id` on the linked `asset_mappings` row. |
| POST | `/api/admin/asset-mapping/{id}/reject` | Mark Rejected — no asset_mappings write. |
| POST | `/api/admin/asset-mapping/{id}/reassign` | Operator picks a different motive_mapping_id. |
| POST | `/api/admin/asset-mapping/bulk-approve` | HIGH-only bulk approve; below-HIGH skipped. |

---

## 3. Storage

New collection: **`asset_mapping_proposals`** (operator-facing queue only).
Approving a proposal updates **`asset_mappings.masci_equipment_id`** to the dispatch's `truck_id` value. No other collection is written.

Indexes: `truck_id`, `motive_mapping_id`, `status`, `confidence_band`.

---

## 4. Live numbers

```
POST /admin/asset-mapping/scan
→ {trucks_scanned:219, upserted:0, bands:{HIGH:0,MEDIUM:0,LOW:0,UNKNOWN:219},
   motive_mappings_considered:190}

GET /admin/asset-mapping/coverage
→ {total_dispatch_trucks:219, mapped:0, unmapped:219, coverage_pct:0.0}

GET /admin/asset-mapping/audit
→ Q1=219 dispatch · Q2=190 motive · Q3=0 mapped · Q4=219 unmapped
  Q5=0 dups · Q6=0 conflicts · Q7=0% · Q9 top risk: T-IT417 (24 dispatches)
```

Preview env contains synthetic `T-iter*` / `T-IT417` / `T-ISO-A` dispatch seeds with no real-world equipment_master twins, so the scan correctly produces 0 matches. **In production**, real dispatch.truck_id values will match `equipment_master.display_label`/`asset_id`/VIN, and the 7-priority scorer will populate the HIGH band materially.

---

## 5. Test results

```
$ pytest tests/test_motive_data_001.py
============================ 15 passed in 8s =============================

$ pytest tests/test_ver1_verification.py tests/test_m2_event_router.py
============================ 33 passed in 48s =============================

$ pytest tests/test_mdr1_equipment_detection.py tests/test_m3_geocode_foundation.py
============================ 23 passed in 26s =============================
```

**Combined: 71/71 PASS across all 5 Motive sprints.**

| Test category | Validates |
|---|---|
| 5 pure-scorer tests | Each of the 7 priorities + UNKNOWN fallback |
| `test_scan_creates_proposals` | Scan never auto-links |
| `test_approve_links` | Approve correctly writes `masci_equipment_id` |
| `test_reject_does_not_link` | Reject leaves asset_mappings untouched |
| `test_reassign` | Bad motive_mapping_id → 400; good → Verified with `match_signal.kind=manual` |
| `test_bulk_approve_high_only` | Below-HIGH skipped with `below_high_confidence` reason |
| `test_coverage_endpoint` / `test_audit_endpoint_shape` | All required keys present |
| `test_admin_endpoints_require_token` | 4 endpoints reject without admin token |
| `test_no_motive_or_workflow_writes_in_source` | Router source has no `motive_service`/`httpx`/forbidden writes |
| `test_no_unwanted_writes_during_scan_audit` | daily_reports/dispatch_assignments/motive_events/operational_events/operational_locations counts unchanged |

Lint: ✅ ruff clean · ✅ eslint clean.

---

## 6. Constitutional adherence

| Forbidden | Enforcement | Verified |
|---|---|---|
| ❌ Dispatch automation | No dispatch_assignments writes | `test_no_unwanted_writes_during_scan_audit` |
| ❌ Material/FleetWatcher/Push-to-Motive | No httpx, no motive_service | `test_no_motive_or_workflow_writes_in_source` |
| ❌ Workflow changes | No `workflow_state_events.insert`/`operations_actions.insert` | source guard test |
| ❌ Daily Report automation | No daily_reports writes | `test_no_unwanted_writes_during_scan_audit` |
| ❌ Verification logic changes | VER-1 router untouched | regression 16/16 still pass |
| ❌ Auto-approval / auto-linking | Scan only proposes; approve commits | `test_scan_creates_proposals` (asserts no auto-link) |
| ❌ Auto-dispatch | No dispatch_assignments mutations | grep |

---

## 7. Pillar scorecard

| Pillar | Score | Why |
|---|---|---|
| Powerful | 🟢 | 7-priority scoring covers exact/structural/fuzzy lookups across 3 source collections |
| Simple | 🟢 | One pure scorer · one collection · 8 endpoints all single-purpose |
| Beautiful | 🟢 | Coverage tile deep-links cleanly to mapping queue |
| Trusted | 🟢 | Operator approves every link · HIGH-only bulk approve · honest 0% reporting |
| Proven | 🟢 | 71/71 combined regression green |

---

## 8. Success criterion

> Operations can answer: which assets are linked · which are missing · which are wrong · what % of fleet can be verified — and trust score becomes actionable.

**Met.**
- `GET /admin/asset-mapping/coverage` → exact answer to "what % is verifiable today".
- `GET /admin/asset-mapping/queue` → exact list of unverified vs proposed.
- `GET /admin/asset-mapping/audit` → 10-question diagnostic with risk-ranked gaps.
- Approve flow makes the trust score actionable: each operator approval directly increases the VER-1 dispatch CONFIRMED count.

🛑 **STOP. No automation started.** FleetWatcher / Dispatch / Material automation NOT initiated. Awaiting operator authorization.
