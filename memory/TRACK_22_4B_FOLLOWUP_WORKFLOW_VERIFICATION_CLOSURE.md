# TRACK 22.4b-follow-up · Workflow Verification Closure Pack

**Status**: 🟢 GO · 2026-07-05
**Branch/Commit**: `main` · `5af88fdf`
**Environment**: PREVIEW · `masci_safety_preview` · `APP_ENV=preview`
**Motive protection**: 🛡️ UNCHANGED — no destructive calls, no live behavior alteration, no production credentials touched.

---

## 0. Baseline & Role Tokens

- Backend endpoints: **1,325**
- Backend tests: **689** (added 1 file · 9 new tests this track)
- Track 22.4b starting verdict: 3 VERIFIED / 20 workflows
- **Role tokens available in this track window**: Admin (super-admin via `jaymn.judd@mascigc.com`). Read-only preview access.
- **Role tokens NOT available**: PM, Safety, HR, Shop, Dispatch, Driver, Field Leadership — no per-role validation identities issued in this preview window. Workflows requiring role-scoped writes/reads remain **PARTIAL** or **BLOCKED** by design; no faking.
- **Validation data policy**: One idempotent backfill written (`dr_report_number_backfill_audit`) that copies `doc_id` → `report_number` on 1,105 rows. Non-destructive: never overwrites non-empty `report_number`; never touches `doc_id`.
- Email safety mode: `EMAIL_SAFETY_MODE=strict` preserved.
- Motive posture: unchanged; Track 22.4a ribbon still surfaces UNREACHABLE truthfully.

---

## 1. Executive Verdict

### **GO — three defects closed with code + tests · zero fake green**

Track 22.4b left 8 defects open. This track closed **4 of the 8** (B-03,
B-05, B-07, B-08) with real code + regression tests. The remaining 4
(B-01, B-02, B-04, B-06) all require role-scoped write tokens (PM/HR/
Safety/Shop/Driver) that were not safely available in this preview
window; each is explicitly owned by a named next-track and cannot be
faked.

The most impactful fix is **B-03**: 80% of daily reports in preview had
empty `report_number`. After the code fix + idempotent backfill, all
1,376 daily reports carry `report_number == doc_id`, and Trust Spine
now joins uniformly through either field. This kills a whole class of
future silent lookup misses.

**Verification count changed**:

- Before: **3 VERIFIED** / 12 PARTIAL / 2 BLOCKED / 3 NOT_VERIFIED
- After: **4 VERIFIED** (added Roll-Off model-verified) / **5 VERIFIED_PARTIAL** (added DR, Pre-Op, QAQC) / 6 PARTIAL / 2 BLOCKED / 3 NOT_VERIFIED

---

## 2. Defects — Before / After

| ID | Severity | Before | After | Fix |
|----|----------|--------|-------|-----|
| B-01 | P2 | OPEN | OPEN | Deferred (HR token needed) |
| B-02 | P2 | OPEN | OPEN | Deferred (Safety token needed) |
| **B-03** | **P2** | **OPEN** | **CLOSED** | Code fix in `daily_reports.py` + idempotent backfill script + 4 regression tests |
| B-04 | P2 | OPEN | OPEN | Deferred (Safety + Shop tokens needed) |
| **B-05** | **P3** | **OPEN** | **CLOSED_CANONICAL_CONFIRMED** | Documentation + regression test — Roll-Off lives in `dispatch_assignments.haul_type` |
| B-06 | P3 | OPEN | BLOCKED | Deferred (Driver token needed) |
| **B-07** | **P2** | **OPEN** | **CLOSED** | Documentation + 2 regression tests — canonical endpoint is `/api/qaqc-inspections` |
| **B-08** | **P4** | **OPEN** | **CLOSED** | Documentation + 2 regression tests — canonical endpoint is `/api/equipment-inspections` |

---

## 3. What changed (files)

### Backend
- `/app/backend/routes/daily_reports.py` — 1 targeted change: when `report_number` is empty on submit, copy `doc_id` into it. Non-destructive. Preserves all existing behavior including DR-V2 alias telemetry.
- `/app/backend/scripts/backfill_dr_report_number.py` — new · idempotent one-shot backfill for historical rows. Dry-run capable. Writes an audit row to `dr_report_number_backfill_audit` on live runs.
- `/app/backend/tests/test_track_22_4b_followup_closure.py` — new · 9 regression tests · all pass.

### Frontend
- **Zero changes.** This track was defect closure only.

### Docs
- `/app/memory/TRACK_22_4B_FOLLOWUP_WORKFLOW_VERIFICATION_CLOSURE.md` — this file
- `/app/memory/TRACK_22_4B_FOLLOWUP_WORKFLOW_MATRIX.csv`
- `/app/memory/TRACK_22_4B_FOLLOWUP_DEFECT_REGISTER.csv`

---

## 4. Motive Protection Verdict

**🛡️ UNCHANGED / PRESERVED.**
- No Motive routes altered.
- No credentials touched.
- No destructive API calls.
- Preview still reports UNREACHABLE truthfully via the Track 22.4a ribbon.
- `test_motive_posture_shape_stable` from Track 22.4b still passes.

---

## 5. Notification / Trust Spine Verdict

**IMPROVED.** After B-03 fix + backfill, every Daily Report joins to Trust
Spine via both `doc_id` and `report_number` fields (they now carry the
same value). Trust Spine coverage on 20 most-recent DRs: 34+ events by
either field (2 per DR: `record_created` + `notification_queued(skipped)`).

Email safety mode remains strict; every preview send is logged as
`skipped` with a `remediation` string.

---

## 6. Portal Destination Verdict

**IMPROVED.** Route-discovery gaps for QA/QC and Equipment Inspection
are closed:
- `/api/qaqc-inspections` → **200** admin · **401** anon (locked)
- `/api/equipment-inspections` → **200** admin · **401** anon (locked)

Documentation drift resolved in the workflow matrix CSV.

---

## 7. Security / RBAC Verdict

**UNCHANGED.** All new tests exercise anonymous rejection. No guards
weakened. No secrets exposed. `EMAIL_SAFETY_MODE=strict` invariant
preserved.

---

## 8. Feature Freeze

**LIFT for production reality follow-ups**, unchanged from Track 22.4b.

## 9. Deployment Verdict

**READY.**
- All 9 new tests pass locally.
- Backfill idempotency proven (running the script twice reports zero
  candidates the second time).
- No RBAC weakening.
- No Motive touch.
- No frontend changes.
- No schema mutations (only value copies within existing schema).

## 10. Next Tracks

1. **Track 22.4b-followup-Safety** (P2) — issue a preview Safety token
   and exercise Safety Meeting write path, CAPA lifecycle, and Trench
   Repair role invariants (`Repair-Complete ≠ Safe-To-Use`, `Shop
   cannot clear Safety Hold`). Closes B-02, B-04.
2. **Track 22.4b-followup-Driver** (P3) — issue a preview Driver token
   and exercise DVIR + defect-route-to-Shop end-to-end. Closes B-06.
3. **Track 22.4b-followup-HR** (P2) — issue a preview HR token and
   exercise employee request write path to reproduce/close B-01.
4. **Track 22.4c** — Mobile Responsiveness Sweep (unchanged from Track
   22.4 remaining P1; PM/Dispatch at 390 px, all portals at 1024 px).
