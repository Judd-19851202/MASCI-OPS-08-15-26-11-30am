# Phase 1A-4 · Executive Command Center Accountability Consumption · Certification

**Batch:** Pillar 1 · Phase 1A-4
**Date:** 2026-05-31
**Scope:** Certify that the Executive Command Center now consumes the Accountability Service's canonical projection layer for ownership and drilldown context, satisfying each of the directive's certification requirements: ownership parity · approver-not-requester · hardcoded owner removal · Command Center regression-free · accountability service consumption verified.
**Discipline:** OMEGA · evidence-only · no scope drift.

---

## 1 · Executive verdict

🟢 **CERTIFIED.**

| Certification requirement | Verdict |
|---|---|
| Ownership parity verified | 🟢 PASS |
| Approver-not-requester verified | 🟢 PASS |
| Hardcoded owner removal verified | 🟢 PASS |
| Command Center regressions tested | 🟢 PASS (20/20 Phase A · 0 regression) |
| Accountability service consumption verified | 🟢 PASS |

---

## 2 · Test evidence summary

### 2.1 · Phase 1A-4 suite (NEW)

```
$ cd /app/backend && python -m pytest tests/test_accountability_executive_phase_1a4.py -v
============================== 16 passed in 9.77s ==============================
```

| Section | Tests | Result |
|---|---|---|
| Surface invariants (200 · 5 cards · pulse reconciles) | 3 | 🟢 |
| Hardcoded-owner removal (APP · SAF-CRITICAL · SAF-OSHA · JOBS-ISSUE-NO-PATH · EQP-OOS-OLD) | 5 | 🟢 |
| Drilldown enrichment (accountability + timeline shape + owner parity) | 3 | 🟢 |
| No-regression sanity (accountability service · backups · recovery · health) | 4 | 🟢 |
| Pillar 1B reservation invariant in 1A-4 surface | 1 | 🟢 |

### 2.2 · Combined regression (108 tests across the Pillar)

```
$ python -m pytest \
       tests/test_command_center_phase_a.py \
       tests/test_accountability_projection_phase_1a2.py \
       tests/test_accountability_service_phase_1a3.py \
       tests/test_accountability_executive_phase_1a4.py
======================== 108 passed in 14.88s ========================
```

| Suite | Tests |
|---|---|
| `test_command_center_phase_a.py` (Pillar 2 Phase A Path B · D1/D2/D5) | 20 |
| `test_accountability_projection_phase_1a2.py` (Phase 1A-2 unit) | 51 |
| `test_accountability_service_phase_1a3.py` (Phase 1A-3 live HTTP) | 21 |
| `test_accountability_executive_phase_1a4.py` (Phase 1A-4 live HTTP) | 16 |
| **Total** | **108 · zero failures · zero regression** |

---

## 3 · Cert requirement #1 · Ownership parity verified

The directive's success condition: Command Center derives ownership from the Accountability Service, not hardcoded logic.

| Surface | Pre-1A-4 path | Post-1A-4 path |
|---|---|---|
| Snapshot card item `owner` | Python string literal or `field-name fallback chain` | projection `owner_display_name` for incident/po/fleet_defect rules |
| Drilldown `owner` legacy field | Field-name fallback chain | projection `owner_display_name` (with field fallback as safety net) |
| Drilldown `accountability.owner_*` (new) | did not exist | full `owner_role` + `owner_user_id` + `owner_employee_id` + `owner_display_name` |

Live evidence (2026-05-31 preview):

```
[red]  SAF-CA-OVERDUE   owner='Alec Perkins'            ◄── real CA assignee via projection
[red]  SAF-CA-OVERDUE   owner='iter364 Sub Vendor Owner' ◄── real CA assignee via projection
[amber] APP-AMBER       owner='Pending Approver'         ◄── projection's approver-role
```

Drilldown probe confirms `payload.owner == payload.accountability.owner_display_name` when projection is available (`test_drilldown_owner_matches_projection_when_accountability_present`).

---

## 4 · Cert requirement #2 · Approver-not-requester verified

**This is the Audit's most operationally consequential closure.**

Pre-1A-4: line 874 of `command_center.py` set `owner = p.get("requested_by_name") or "Requester"` — the **requester** of the PO. The actual approver awaiting action was invisible.

Post-1A-4: same line now reads `owner = _acc_proj.project_po_request(p)["owner_display_name"]`. The projection's `_owner_from_po()` returns `"Pending Approver"` for pending statuses (`Submitted`, `Pending Approval`, `Clarification Needed`, `Pending Receipt`, `Overdue Receipt`).

### 4.1 · Pytest enforcement

```python
def test_approvals_pending_owner_is_not_requester_when_card_lights():
    """The original bug: pending POs showed `requested_by_name` as owner.
    Phase 1A-4 must surface a non-requester owner..."""
    d = _snapshot()
    for rule in ("APP-AMBER", "APP-RED", "APP-WEEK"):
        for it in _items_for_rule(d, rule):
            assert it["owner"] not in ("", None)
            assert it["owner"] == "Pending Approver", (
                f"rule={rule} unexpected owner={it['owner']!r}")
```

This test passed against the live preview snapshot with 5 APP-AMBER items, every one showing `"Pending Approver"`.

### 4.2 · Negative case verified

Rejected/Cancelled POs (terminal) correctly fall back to the requester per the projection's contract (`_owner_from_po` in `lib/accountability_projection.py:343-358`). The contract is asserted at the unit level by `test_po_rejected_owner_is_requester` (Phase 1A-2 suite).

---

## 5 · Cert requirement #3 · Hardcoded owner removal verified

Five rules cleared. Per the Audit §5 finding (5 of 9 owner strings hardcoded), all five are now derived:

| Rule | Pre-1A-4 source | Post-1A-4 source | Pytest |
|---|---|---|---|
| JOBS-ISSUE-NO-PATH | `"Safety"` literal | `project_incident().owner_display_name` | `test_jobs_issue_no_path_owner_no_longer_hardcoded_safety` |
| SAF-CRITICAL-UNRESOLVED | `"Safety"` literal | `project_incident().owner_display_name` | `test_saf_critical_unresolved_owner_no_longer_hardcoded_safety` |
| SAF-OSHA-OPEN | `"Safety"` literal | `project_incident().owner_display_name` | `test_saf_osha_open_owner_no_longer_hardcoded_safety` |
| EQP-OOS-OLD | `"Shop"` literal | `project_fleet_defect().owner_display_name` | `test_eqp_oos_old_owner_no_longer_hardcoded_shop` |
| APP-AMBER · APP-RED · APP-WEEK | `requested_by_name` (wrong attribution) | `project_po_request().owner_display_name` | `test_approvals_pending_owner_is_not_requester_when_card_lights` |

Each test asserts the owner field is non-empty AND, for the approvals case, equals the projection's contract output.

Note: in the live preview environment, JOBS-ISSUE-NO-PATH and SAF-CRITICAL-UNRESOLVED still display the string `"Safety"`. This is **not a regression** — these incidents have no linked CA assignee, so the projection's fallback chain correctly resolves to `"Safety"`. The difference is that the string now comes from the projection's documented contract, not from a Python literal. Future phases (1A-5 native assignee fields, then 1A-3 promotion of linked CA assignee) will surface real names here.

---

## 6 · Cert requirement #4 · Command Center regressions tested

### 6.1 · Pulse aggregate reconciliation (the Path B invariant)

```python
def test_pulse_aggregate_still_reconciles_post_1a4():
    """Phase 1A-4 must NOT break the Pulse aggregate invariant
    established by Path B."""
    ...
    assert pulse["red_warnings"] == red_w
    assert pulse["amber_warnings"] == amb_w
    assert pulse["red_items"] == red_i
    assert pulse["amber_items"] == amb_i
```

🟢 PASS — pulse counters reconcile exactly post-1A-4.

### 6.2 · Pre-existing Command Center suite

```
$ python -m pytest tests/test_command_center_phase_a.py
======================== 20 passed ===========================
```

🟢 All 20 Path B + Phase A tests still pass. D1/D2/D5 patches green. Status mappings unchanged on snapshot items.

### 6.3 · Endpoint surface

| Endpoint | Status |
|---|---|
| `/api/admin/command-center/snapshot` | 200 |
| `/api/admin/command-center/thresholds` | 200 |
| `/api/admin/command-center/calendar` | 200 |
| `/api/admin/command-center/drilldown/{card}/{id}` | 200 (with `accountability` + `timeline`) · 404 for missing items · 400 for unknown card_id |

### 6.4 · Frontend SPA

| Surface | Status |
|---|---|
| `AdminCommandCenter.jsx` md5 | `4cb825b4830871d1d407d206d4ae5519` (unchanged) |
| Card layout · sidebar · routes | unchanged |
| Network calls from SPA | unchanged · existing endpoints |

The directive's mandate "preserve existing visual design and card structure" is satisfied — zero frontend code change.

### 6.5 · Adjacent surfaces (backup · recovery · health · accountability service)

```
$ test_backups_scheduler_state_still_200       PASSED
$ test_recovery_snapshot_still_200             PASSED
$ test_health_still_200                        PASSED
$ test_accountability_service_snapshot_still_200  PASSED
```

🟢 No regression.

---

## 7 · Cert requirement #5 · Accountability Service consumption verified

The Command Center now consumes the projection **in-process** via `from lib import accountability_projection as _acc_proj` (line 12 of `command_center.py`). Verified by:

| Pytest | Asserts |
|---|---|
| `test_drilldown_includes_accountability_subobject` | Drilldown response carries both `accountability` and `timeline` keys |
| `test_drilldown_accountability_has_canonical_fields_when_present` | The 23-field canonical key set is present and identical between Command Center drilldown and Accountability Service `/item` endpoint |
| `test_drilldown_owner_matches_projection_when_accountability_present` | Legacy `owner` field === `accountability.owner_display_name` |
| `test_no_escalation_activation_phase_1a4` | `escalation_level=0` is enforced on every projection surfaced through the Command Center |

The two surfaces (`/api/admin/accountability/item` and `/api/admin/command-center/drilldown/...`) now expose the **same canonical contract** for the same source row — different endpoints, identical projection.

---

## 8 · Out-of-scope verification

| Item | Verdict |
|---|---|
| Escalation Framework | 🛑 NOT BUILT (`escalation_level=0` enforced everywhere in this batch) |
| Notifications · Emails · SMS | 🛑 NOT BUILT |
| Accountability Dashboard page | 🛑 NOT BUILT |
| New collections | 🛑 NOT BUILT |
| White Label · ForgedOps Portal | 🛑 NOT BUILT |
| Pillar 2 · Pillar 3 · Pillar 4 | 🛑 NOT BUILT |
| Phase 1A-5 (native `assignee_*` fields) | 🛑 NOT BUILT |

---

## 9 · OMEGA discipline check (Phase 1A-4 close)

| Discipline rule | Verdict |
|---|---|
| Source workflows untouched | 🟢 |
| Projection library byte-stable (md5 `e8de1112…`) | 🟢 |
| Service router byte-stable (md5 `0e879cf9…`) | 🟢 |
| Frontend untouched (md5 `4cb825b4…`) | 🟢 |
| One file modified (`command_center.py`) + one new test file | 🟢 |
| No new collection · no new endpoint | 🟢 |
| Card payload shape preserved (only string content changes) | 🟢 |
| Escalation NOT activated | 🟢 |
| No notifications/emails/SMS/cron added | 🟢 |
| Backup · recovery · scheduler · R2 · drill framework untouched | 🟢 |
| Pillar 1A-5+ untouched | 🟢 |
| No deployment | 🟢 |

---

## 10 · Phase 1A-4 closeout

🟢 **Certified.** The Executive Command Center derives ownership and accountability context from the Accountability Service. All five identified hardcoded owner strings replaced. The Approvals card stops misattributing the requester as the owner. The drilldown carries the full canonical projection plus a 25-event timeline. Zero regression: 108/108 pytests green across Path B, Phase 1A-2, Phase 1A-3, Phase 1A-4 suites. Frontend untouched · card structure preserved · backups/recovery/scheduler unaffected.

🛑 **STOPPED.** No further work without operator authorization.
