# M-3 · Geocode Foundation · Certification

**Sprint:** M-3 (Geocode Foundation)
**Status:** ✅ GREEN — code complete, tests green, live data validated
**Date:** 2026-02-09
**Doctrine:** `MOTIVE_001_CONSTITUTIONAL_AUDIT.md` §D · §I.2 · §L
**Constitutional posture:** Read-only against Motive · No project auto-assignment · Human approves every link · Zero impact on Daily Reports / Material Movement / Dispatch

---

## 1. What shipped

### 1.1 Backend (single new module · single mount line)
- **NEW** `/app/backend/routes/operational_locations.py` — 540 LOC, zero coupling to `motive_service.py`.
- **MOUNT** `/app/backend/server.py:11375-11380` — wired alongside the existing admin lookups router.

### 1.2 Endpoints (all X-Admin-Token gated, all prefixed `/api/admin/locations`)
| Method | Path | Purpose |
|---|---|---|
| POST | `/import-geofences` | Idempotent seed of `operational_locations` from the existing `motive_geofences` collection. No Motive API call — reads from the already-synced local mirror. |
| POST | `/reconcile` | For each JOB-typed row, scores every `jobs_master` candidate and stores `proposed_project_number`, `confidence_score`, `confidence_band`. **Never** sets `project_number`. |
| GET | `/reconciliation-queue` | Operator queue. Filterable by band (`high`/`medium`/`low`) or status (`Verified`/`Rejected`). Returns sidecar counts. |
| GET | `/by-project` | M3-5 overlay map: `{verified: {project_number: row}, proposed: {project_number: [rows]}}` for the AdminJobs Location Intelligence panel. |
| POST | `/{loc_id}/approve` | Sets `project_number=proposed_project_number` + `geocode_status=Verified`. |
| POST | `/{loc_id}/reject` | Sets `geocode_status=Rejected`. Clears proposal, preserves geofence link for audit. |
| POST | `/{loc_id}/reassign` | Body `{project_number}`. Sanity-checks the project exists. Stamps `match_signal.kind="manual"`. |
| POST | `/bulk-approve` | Body `{ids: [...]}`. **Approves ONLY ids with `confidence_score >= 0.85`.** Below-threshold rows returned in `skipped`. |
| GET | `/` (list) | Generic filterable list (`location_type`, `status`). |

### 1.3 Data model — `operational_locations`
Canonical schema (per audit §D.1, all 8 location types supported):

```
id                          uuid
location_type               enum: JOB | ASPHALT_PLANT | CONCRETE_PLANT | PIT
                                  | YARD | SHOP | DISPOSAL_SITE | VENDOR
name                        str
address                     str | ""
latitude                    float | null    (polygon centroid)
longitude                   float | null
geofence_radius             int (ft)        (max corner distance, default 250)
geocode_status              enum: Not Geocoded | Imported | Matched | Verified | Rejected
motive_geofence_id          str | null      (join key to motive_geofences)
motive_category             str | ""
motive_status               str | ""
project_number              str | null      ← set ONLY by approve / reassign
proposed_project_number     str | null      ← set by reconcile
proposed_project_name       str | null
confidence_score            float [0..1]
confidence_band             enum: high (≥0.85) | medium [0.55, 0.85) | low (<0.55)
match_signal                {score, kind, evidence}
active                      bool
created_at / created_by     audit
updated_at                  audit
verified_at / verified_by   audit (set on approve/reject/reassign)
```

Indexes: `motive_geofence_id`, `project_number` (sparse), `location_type`, `geocode_status`.

### 1.4 Reconciliation engine — signals (ranked, best wins)
Pure function `_score_match(job, geofence)`. Source signals:
1. **Project number** ("24-06" / "26-08 - CP") present in fence name → **0.95**
2. **T-number** ("T5824") shared between project name + fence name → **0.92**
3. **Highway + place** ("SR 46" + "Mellonville") → **0.85**
4. **Highway only** ("SR 46") → 0.70
5. **Fuzzy fallback** (`difflib.SequenceMatcher` on normalized text) → 0..1

Bands: HIGH ≥ 0.85 · MEDIUM 0.55..0.85 · LOW < 0.55.

### 1.5 Frontend
- **NEW page** `/app/frontend/src/pages/admin/AdminGeofenceReconciliation.jsx` — full reconciliation surface (counts strip, filter pills, table, bulk-approve, per-row Approve/Reject/Reassign, terminal-state read-only).
- **NEW panel** `/app/frontend/src/components/admin/LocationIntelligencePanel.jsx` — read-only Location Intelligence overlay embedded into `/admin/jobs`.
- **NEW route** `/admin/geofence-reconciliation` (admin-strict, `A(...)` wrapper) in `App.js`.
- **EDIT** `/app/frontend/src/pages/admin/AdminJobs.jsx` — embedded `<LocationIntelligencePanel />` alongside existing `<AdminJobMasterPanel />` (additive, no edits to the job CRUD logic itself).

All required `data-testid`s present:
- `geofence-recon-page`, `recon-import-btn`, `recon-run-btn`, `recon-count-{total|high|medium|low|verified|rejected}`, `recon-filter-{all|high|medium|low|verified|rejected}`, `recon-bulk-approve-btn`, `recon-table`, `recon-row-{id}`, `recon-row-select-{id}`, `recon-approve-{id}`, `recon-reject-{id}`, `recon-reassign-{id}`, `recon-reassign-input-{id}`, `recon-reassign-confirm-{id}`.
- `location-intel-panel`, `location-intel-stats`, `location-intel-open-recon`, `location-intel-row-{project_number}`.

---

## 2. Live preview verification (real data, real env)

```
POST /api/admin/locations/import-geofences   →  {imported: 67, updated: 0, total_geofences_in_motive: 67}
POST /api/admin/locations/reconcile          →  {scored: 62, bands: {high: 18, medium: 2, low: 42}, jobs_considered: 29}
GET  /api/admin/locations/reconciliation-queue → {rows: 62, counts: {total:62, high:18, medium:2, low:42, verified:0, rejected:0}}
```

Sample HIGH-confidence proposals surfaced (each matched on project_number signal at 95%):
- `25-15 - FDOT E53F1 SR 404 BREVARD CO` → `25-15` (E53F1 - SR 404, Brevard Co · Pineda)
- `21-06 - T5736 - S CENTRAL AVE YARD - THEFT` → `21-06` (T5736 Oveido)
- `25-14 - E8V62 417` → `25-14` (E8V62 Resurf Seminole Expressway / SR 417)
- `25-12 & 25-13 NSB DRAINAGE & WATERMAIN` → `25-12` (N. Atlantic Ave - Drainage)
- 14 more — operator screenshot attached to runbook.

The reconciliation UI renders 62 rows, the 4 filter bands wire correctly (HIGH narrows to 18), the bulk-approve button stays disabled until at least one HIGH row is selected, and per-row Approve/Reject/Reassign actions render with proper confidence-band coloring.

---

## 3. Test results

```
$ pytest tests/test_m3_geocode_foundation.py -v
============================ 12 passed in 37.35s =============================
```

| Test | Validates |
|---|---|
| `test_score_matches_project_number` | Signal #1 fires at 0.95 |
| `test_score_matches_t_number` | Signal #2 fires at ≥ 0.92 |
| `test_score_low_unrelated` | Unrelated text scores < 0.55 (LOW band) |
| `test_polygon_centroid_and_radius` | Centroid math + Haversine radius |
| `test_polygon_radius_defaults_when_empty` | Doctrinal default 250 ft |
| `test_import_reconcile_approve_full_flow` | Full Import → Reconcile → Bulk-Approve flow + idempotency + HIGH-only bulk restriction |
| `test_reject_and_reassign` | Reject + Reassign + unknown-project rejection + manual signal stamping + category routing (Terminal/Yard → YARD) |
| `test_admin_gate_required` | All `/admin/locations/*` endpoints return 401/403 without admin token |
| `test_no_motive_service_coupling` | Router source code contains no import of `motive_service`, no `MotiveService(`, no `httpx` — CONSTITUTIONAL guard |
| `test_no_daily_report_or_dispatch_writes` | `daily_reports`, `dispatch_assignments`, `motive_events` counts unchanged after import + reconcile |
| `test_location_types_enum_complete` | All 8 location types present |
| `test_geocode_statuses_enum_complete` | All 5 statuses present |

Lint: ✅ ruff clean (Python) · ✅ eslint clean (3 JS files).

---

## 4. Constitutional adherence checklist

| Constitutional rule | Enforced where | Verified by |
|---|---|---|
| Motive is NOT source of truth | Router never sets `project_number` on import/reconcile; only `approve`/`reassign` does (operator action) | `test_import_reconcile_approve_full_flow` lines asserting `not loc.get("project_number")` after import + reconcile |
| No pushes to Motive | Router does not import `motive_service`, does not use `httpx` | `test_no_motive_service_coupling` |
| Human always approves | `bulk-approve` rejects below-HIGH, `reassign` requires real project, no auto-acceptance path | `test_import_reconcile_approve_full_flow` (below-HIGH skip) + `test_reject_and_reassign` (unknown-project 400) |
| No automatic project assignment | `confidence_score >= HIGH` does not auto-flip status to Verified — only `Matched` until operator approves | Manual: read `reconcile` endpoint code lines 305–325 |
| No automatic job creation | Router never inserts into `jobs_master` (only reads via `find`) | Source review |
| No automatic geofence creation | Router never inserts into `motive_geofences` (only reads via `find`) | Source review |
| No impact on Daily Reports / Material Movement / Dispatch | Router writes only to `operational_locations` | `test_no_daily_report_or_dispatch_writes` (counts unchanged) |
| Verified is the trusted state | `geocode_status="Verified"` is the only state surfaced as authoritative in `/by-project` | M3-5 panel filters strictly on `Verified` |

---

## 5. Required testing checklist (per brief)

| Required test | Status | Evidence |
|---|---|---|
| 1. Import of existing geofences | ✅ | 67 imported live · idempotent on re-run |
| 2. Matching engine | ✅ | 62 scored (5 non-JOB-categorized rows skip JOB scoring) |
| 3. High confidence routing | ✅ | 18 HIGH band, all visible at `recon-filter-high` |
| 4. Medium confidence routing | ✅ | 2 MEDIUM band |
| 5. Unmatched routing | ✅ | 42 LOW band (operator review needed) |
| 6. Approval workflow | ✅ | Approve / Reject / Reassign / Bulk-Approve all wired + unit-tested |
| 7. Jobs Master display | ✅ | `LocationIntelligencePanel` embedded in `/admin/jobs` |
| 8. No Motive writes | ✅ | `test_no_motive_service_coupling` |
| 9. No Daily Report impact | ✅ | `test_no_daily_report_or_dispatch_writes` |
| 10. No schema regressions | ✅ | Existing collections untouched; new collection is additive |
| Regression suite | ✅ | 12/12 pass |
| Lint | ✅ | Clean across Python + JS |
| Screenshots | ✅ | `/tmp/m3_loaded.jpg` shows live HIGH-band rows with 95% confidence chips |

---

## 6. Success criteria from the operator brief

> Operator can answer:
> * Which geofence belongs to which project?
> * Which projects are geocoded?
> * Which projects are not?
> * Which Motive events belong to which job?
> without opening Motive.

| Question | Answered by | Where |
|---|---|---|
| Which geofence belongs to which project? | Reconciliation Queue table | `/admin/geofence-reconciliation` |
| Which projects are geocoded? | Location Intelligence stats (Verified column) | `/admin/jobs` → Location Intelligence panel |
| Which projects are not? | Same panel — "No proposal" tile (red dot) and per-row badge | `/admin/jobs` |
| Which Motive events belong to which job? | Once an `operational_locations` row is Verified, `project_number` is now joinable to `motive_events.raw.geofence.id` via `motive_geofence_id`. **Wiring this join is M-2's job (deferred).** | Foundation laid; consumption is M-2 |

The fourth question's *foundation* is shipped — the join key now exists. Actually surfacing geofence-tagged Motive events on operator-facing screens is **explicitly out of scope** for M-3 (it belongs to the M-2 Event Router).

---

## 7. What is explicitly NOT in this sprint (per brief)

- ❌ M-DR-1 Equipment Auto-Discovery — not built
- ❌ M-2 Event Router — not built
- ❌ Verification Layer — not built
- ❌ Dispatch automation — not built
- ❌ Daily Report modifications — none
- ❌ Material Movement modifications — none
- ❌ Push to Motive — none
- ❌ OA events / notifications — none

🛑 **STOP. AWAITING EXPLICIT AUTHORIZATION FOR M-DR-1.**
