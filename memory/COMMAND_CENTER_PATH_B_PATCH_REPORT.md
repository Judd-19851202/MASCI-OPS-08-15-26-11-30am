# Executive Command Center · Path B Patch Report (D1 · D2 · D5)

**Batch:** Pillar 2 · Phase A · Path B · Operator-authorized
**Date:** 2026-05-31
**Scope:** Patch the three medium-severity defects identified during certification (D1 · D2 · D5) — and only those — without scope expansion, refactor, or new collections.
**Discipline:** OMEGA · code change strictly scoped to `routes/command_center.py` (helpers + 4 query call-sites) and matching pytest expansion.

---

## 1 · Defect inventory (carried from certification)

| ID | Card | Mechanism (pre-patch) | Severity | Operational impact |
|----|------|-----------------------|----------|--------------------|
| **D1** | Safety | `SAF-CRITICAL-UNRESOLVED` counted Critical/High/Serious incidents purely on age, with **no closure check**. An aged incident whose `corrected_on_site = Yes` or whose linked `corrective_actions` row was `Closed/Verified` still fired RED forever. | MEDIUM | Trust erosion: Safety card stuck RED on a known-closed event undermines dashboard credibility within first week of use. |
| **D2** | Safety | `SAF-OSHA-OPEN` issued the same age-only count. Same closure-state miss as D1 but on the OSHA-recordable subset — RED never cleared after the incident was actually resolved on site or via a verified corrective action. | MEDIUM | Regulatory-clock signal lost its meaning; operator could not tell "OSHA still owes us a closure" from "OSHA file just hasn't been formally marked closed". |
| **D5** | Approvals + Equipment | `po_requests.created_at` and `fleet_defects.created_at` may be stored as either a BSON `Date` object OR an ISO-8601 string. The pre-patch query compared each cutoff against a **single-typed** value (ISO-string for approvals; ISO-string for equipment), so the other-typed rows were silently invisible — `pending_amber` could read 0 while operationally-aged POs existed. | MEDIUM | Operational miss: approvals card silently under-reported aged POs; equipment OOS-aged windows could miss any BSON-Date defects. |

D3 / D4 / D6 / D7 (low/cosmetic) were explicitly out of scope per the Path B authorization.

---

## 2 · Source-code changes (verbatim references)

**File:** `/app/backend/routes/command_center.py` (53,507 bytes · 1,111 LOC · md5 `c6f950452e45cd48c85edbb365e79fe5`)

### 2.1 · New helpers (lines 239 – 287)

Two helper bundles added immediately after the existing `_fmt_age_hours` utility — no refactor of surrounding code:

#### D5 cross-type date helpers (lines 239 – 266)
```python
def _date_lt(field, dt):            # $or [{field: {$lt: dt}}, {field: {$lt: dt.isoformat()}}]
def _date_lte(field, dt):           # $or [{field: {$lte: dt}}, {field: {$lte: dt.isoformat()}}]
def _date_gte(field, dt):           # $or [{field: {$gte: dt}}, {field: {$gte: dt.isoformat()}}]
def _date_between_lt(field, lo, hi):# $or [{lo < field <= hi (BSON)}, {lo < field <= hi (ISO)}]
```
Each emits a `$or` that fans the same comparison out across both representations. The original semantics are preserved for either form individually; only the false negatives caused by the other form are recovered.

#### D1/D2 resolution-state helper (lines 269 – 287)
```python
async def _incident_is_resolved(db, inc) -> bool:
    if str(inc.get("corrected_on_site") or "").strip().lower() == "yes":
        return True
    inc_id = inc.get("id")
    if not inc_id:
        return False
    closed = await db.corrective_actions.find_one(
        {"$or": [{"source_id": inc_id}, {"incident_id": inc_id}],
         "status": {"$in": ["Closed", "Verified", "Completed", "Closed - Verified"]}},
        {"_id": 0, "id": 1},
    )
    return closed is not None
```

### 2.2 · D1 patch call-site — `_build_safety_card` SAF-CRITICAL-UNRESOLVED loop

Lines 466 – 470 — `await _incident_is_resolved(db, inc)` is now consulted **before** the age-bucket increment. Resolved incidents skip RED/AMBER counting entirely.

### 2.3 · D2 patch call-site — `_build_safety_card` SAF-OSHA-OPEN block

Lines 499 – 538 — the old `count_documents` was replaced with a candidate `find()` + in-loop closure check. Items list now sources from the unresolved subset, never from raw OSHA candidates.

### 2.4 · D5 patch call-sites

| Card | Rule | Lines | Cutoff(s) wrapped |
|------|------|-------|-------------------|
| Safety | SAF-OSHA-OPEN | 509 | `_date_lt("created_at", cutoff_osha_dt)` |
| Equipment | EQP-OOS-OLD red | 624 – 628 | `_date_lt("created_at", cutoff_red_dt)` |
| Equipment | EQP-OOS-OLD amber bucket | 629 – 633 | `_date_between_lt("created_at", cutoff_red_dt, cutoff_amber_dt)` |
| Equipment | EQP-OOS-NEW | 670 – 675 | `_date_gte("created_at", cutoff_amber_dt)` |
| Approvals | APP-AMBER | 814 – 819 | `_date_between_lt("created_at", cutoff_amber_start_dt, cutoff_amber_end_dt)` |
| Approvals | APP-RED | 820 – 825 | `_date_lte("created_at", cutoff_red_dt)` |
| Approvals | APP-WEEK | 826 – 831 | `_date_lte("created_at", cutoff_week_dt)` |

Every existing rule’s arithmetic, threshold name, message string, and warning shape is preserved byte-for-byte. **No behavioral change for collections that store only one date form.**

### 2.5 · What was NOT touched

- `_build_jobs_card` (no defects raised in this batch)
- `_build_accountability_card` (no defects raised in this batch)
- All threshold defaults, rule IDs, expected_resolution strings
- The factory `build_command_center_router`, cache TTL, audit-log emits, drilldown endpoint
- Frontend `AdminCommandCenter.jsx` (zero changes)
- `server.py` wiring · sidebar registration · `App.jsx` route
- Every other backend module

### 2.6 · git evidence

```
commit 22f40ff (2026-05-31 04:01 UTC) — Phase A initial implementation
  backend/routes/command_center.py             | 1031 ++++++++ NEW
  backend/tests/test_command_center_phase_a.py |  298 ++++++ NEW
commit 1820fe9 — Path B patch (D1/D2/D5)
  backend/routes/command_center.py             +80 / -25
  backend/tests/test_command_center_phase_a.py +105 / 0
```

`git diff 22f40ff 1820fe9 -- backend/routes/command_center.py backend/tests/test_command_center_phase_a.py` is the exact change set above.

---

## 3 · Pytest expansion

**File:** `/app/backend/tests/test_command_center_phase_a.py` (14,981 bytes · 403 LOC · md5 `5815a7762fa46d989cae35d94575bc0c`)

Six new test cases added · zero existing case mutated:

| Test | Defect | What it asserts |
|------|--------|-----------------|
| `test_d1_critical_incident_corrected_on_site_does_not_fire_red` | D1 | Aged Critical incident with `corrected_on_site=Yes` produces 0 RED warning. |
| `test_d1_critical_incident_with_closed_ca_does_not_fire_red` | D1 | Aged Critical incident with linked `corrective_actions.status=Closed` produces 0 RED warning. |
| `test_d2_osha_recordable_corrected_on_site_does_not_fire_red` | D2 | Aged OSHA-recordable incident with `corrected_on_site=Yes` produces 0 RED warning. |
| `test_d2_osha_recordable_with_verified_ca_does_not_fire_red` | D2 | Aged OSHA-recordable incident with linked CA `status=Verified` produces 0 RED warning. |
| `test_d5_approvals_red_with_bson_datetime_created_at` | D5 | PO row stored with BSON `datetime` `created_at` 6 days old is counted as RED (was 0 pre-patch). |
| `test_d5_equipment_red_with_bson_datetime_created_at` | D5 | Fleet defect stored with BSON `datetime` `created_at` 80 hours old is counted as OOS red (was 0 pre-patch). |

### 3.1 · Final run (fresh)

```
$ cd /app/backend && python -m pytest tests/test_command_center_phase_a.py -v
============================= test session starts ==============================
platform linux -- Python 3.11.15, pytest-9.0.3
collected 20 items

tests/test_command_center_phase_a.py::test_worst_pill_priority PASSED                                  [  5%]
tests/test_command_center_phase_a.py::test_default_thresholds_have_all_required_rules PASSED          [ 10%]
tests/test_command_center_phase_a.py::test_jobs_card_green_when_all_active_jobs_have_dr PASSED        [ 15%]
tests/test_command_center_phase_a.py::test_jobs_card_red_when_many_jobs_missing_dr PASSED             [ 20%]
tests/test_command_center_phase_a.py::test_jobs_card_red_when_unowned_corrective_action PASSED        [ 25%]
tests/test_command_center_phase_a.py::test_safety_card_red_when_critical_incident_unresolved_48h PASSED [ 30%]
tests/test_command_center_phase_a.py::test_safety_card_amber_when_critical_incident_24h_only PASSED   [ 35%]
tests/test_command_center_phase_a.py::test_safety_card_red_on_osha_open_24h PASSED                    [ 40%]
tests/test_command_center_phase_a.py::test_equipment_card_red_when_oos_72h PASSED                     [ 45%]
tests/test_command_center_phase_a.py::test_equipment_card_red_on_backlog PASSED                       [ 50%]
tests/test_command_center_phase_a.py::test_accountability_red_when_many_high_overdue PASSED           [ 55%]
tests/test_command_center_phase_a.py::test_accountability_green_when_no_overdue PASSED                [ 60%]
tests/test_command_center_phase_a.py::test_approvals_red_when_po_aged_5_days PASSED                   [ 65%]
tests/test_command_center_phase_a.py::test_approvals_amber_when_po_aged_3_days PASSED                 [ 70%]
tests/test_command_center_phase_a.py::test_d1_critical_incident_corrected_on_site_does_not_fire_red PASSED [ 75%]
tests/test_command_center_phase_a.py::test_d1_critical_incident_with_closed_ca_does_not_fire_red PASSED [ 80%]
tests/test_command_center_phase_a.py::test_d2_osha_recordable_corrected_on_site_does_not_fire_red PASSED [ 85%]
tests/test_command_center_phase_a.py::test_d2_osha_recordable_with_verified_ca_does_not_fire_red PASSED [ 90%]
tests/test_command_center_phase_a.py::test_d5_approvals_red_with_bson_datetime_created_at PASSED      [ 95%]
tests/test_command_center_phase_a.py::test_d5_equipment_red_with_bson_datetime_created_at PASSED      [100%]

======================== 20 passed, 1 warning in 0.27s =========================
```

**Result: 20/20 PASS · 0 FAIL · 0 SKIP · 0 ERROR · 0.27 s.**

Pre-patch had 14 tests; the 6 new D1/D2/D5 cases would have failed against the pre-patch source. Existing 14 cases still pass — no regression.

---

## 4 · OMEGA discipline check

| Discipline rule | Verdict |
|---|---|
| Code change confined to `/app/backend/routes/command_center.py` + matching pytest | 🟢 PASS |
| No new collections introduced | 🟢 PASS (still only `command_center_thresholds`, `command_center_calendar`) |
| No notification / email / fan-out emission added | 🟢 PASS |
| No frontend code changed | 🟢 PASS (`AdminCommandCenter.jsx` unchanged · md5 `4cb825b4830871d1d407d206d4ae5519`) |
| No threshold default changed | 🟢 PASS |
| No surrounding code refactored | 🟢 PASS |
| Production source untouched | 🟢 PASS (deploy is a separate operator decision) |

---

## 5 · Risk assessment of this patch

| Risk class | Likelihood | Severity | Mitigation evidence |
|---|---|---|---|
| Closure-state helper false-positive (incident marked resolved when really open) | LOW | LOW | `_incident_is_resolved` only treats `corrected_on_site=Yes` OR linked CA in **explicit closure states** as resolved. No fuzzy matching. Existing 14 tests still pass. |
| Cross-type date helper miscompares Date vs string | NEGLIGIBLE | LOW | `$or` fans out; each branch is a typed comparison MongoDB already supports natively. Test `test_d5_*` covers both storage forms. |
| Performance regression from extra `find_one` per critical incident | LOW | LOW | Bounded by `.limit(50)` upstream and the `corrected_on_site=Yes` short-circuit; in preview snapshot only 2 RED critical incidents currently surface → at most 2 extra `find_one` per refresh, cached 15 sec. |
| Cache invalidation drift | NONE | — | Cache key is unchanged; patch is read-only logic. |

---

## 6 · What this batch did NOT do

- ❌ No production deployment (operator authorizes separately)
- ❌ No D3/D4/D6/D7 work (out of Path B scope)
- ❌ No frontend changes
- ❌ No Phase B / Pillar 1 / Pillar 3 / Pillar 4 scope expansion
- ❌ No refactor of unrelated code

Patch is intentionally narrow, evidence-backed, and reversible.
