# Accountability Service Certification · Phase 1A-3

**Batch:** Pillar 1 · Phase 1A-3 · Accountability Service Surface
**Date:** 2026-05-31
**Scope:** Validate the three new read-only endpoints against the directive's certification requirements: **owner resolution · canonical status mapping · source parity · performance**, plus auth gating and no-workflow-regression sanity.
**Discipline:** OMEGA · evidence-only · zero scope drift.

---

## 1 · Executive verdict

🟢 **CERTIFIED.**

| Certification requirement | Verdict |
|---|---|
| Owner resolution (per-source · live data) | 🟢 PASS |
| Canonical status mapping (per-source · live data) | 🟢 PASS |
| Source parity (identical field set across all non-empty sections) | 🟢 PASS |
| Performance (cold ≤ 2 s · warm cache hit) | 🟢 PASS |
| Auth surface (401 unauth · 200 admin · 400/404 negative cases) | 🟢 PASS |
| No source workflow regression | 🟢 PASS |
| No Command Center / backup / recovery / health regression | 🟢 PASS |

---

## 2 · Test evidence

### 2.1 · Phase 1A-3 service suite (21 tests)

```
$ python -m pytest tests/test_accountability_service_phase_1a3.py -v
======================== 21 passed in 15.33s ==============================
```

| Section | Tests | Result |
|---|---|---|
| Auth gates (sources · snapshot · item) | 3 | 🟢 401 with bad token |
| `/sources` contract | 1 | 🟢 6 sources · async flag correct only on incidents |
| `/snapshot` contract | 9 | 🟢 phase marker · 6 sections · canonical 23-field shape · canonical statuses · escalation_level=0 invariant · timing breakdown · cache · per_source cap · roll-up arithmetic |
| `/item` contract | 4 | 🟢 live task projection · 404 unknown · 400 unsupported module · 404 virtual module |
| Source parity (success condition) | 1 | 🟢 every non-empty section's item keys identical |
| No-regression sanity | 4 | 🟢 command-center snapshot · backups state · recovery snapshot · health |

### 2.2 · Combined regression (92 tests across the Pillar)

```
$ python -m pytest tests/test_command_center_phase_a.py \
                   tests/test_accountability_projection_phase_1a2.py \
                   tests/test_accountability_service_phase_1a3.py
======================== 92 passed in 11.41s =========================
```

| Suite | Tests |
|---|---|
| `test_command_center_phase_a.py` (Pillar 2 · Phase A · Path B) | 20 |
| `test_accountability_projection_phase_1a2.py` (Phase 1A-2 unit) | 51 |
| `test_accountability_service_phase_1a3.py` (Phase 1A-3 live HTTP) | 21 |
| **Total · zero failures · zero regressions** | **92** |

---

## 3 · Owner-resolution verification (live data)

Source: preview snapshot `per_source=100`, total 277 projections.

| Source | Items | Owner verification |
|---|---|---|
| tasks | 100 | Per-row `assignee_role` resolved (e.g. `safety/Safety`, `pm/<name>`). Verified by `test_item_returns_canonical_projection_for_live_task` end-to-end. |
| safety.corrective_actions | 8 | `owner_role="safety"` · `owner_display_name = assigned_to_name` (or "Safety" fallback) |
| po.requests | 100 | **Pending POs project `owner_role="approver_per_routing"`** — the approver-not-requester correction is live. Verified across full page. |
| equipment.dvir | 50 | `owner_role="shop"`; defects with `acknowledged_by_name` surface a real shop technician name. |
| safety.incidents | 19 | `owner_role="safety"` · async CA-aware status derivation in place. |
| virtual.signals | 0 | empty section (payload-driven; no backing collection — by design) |

Auth-gated full payload exercised by `test_snapshot_every_item_has_canonical_24_field_shape` — every item satisfies the contract.

---

## 4 · Canonical status mapping verification (live data)

Roll-up from live preview snapshot (per_source=100):

```
rollup.total_items   = 277
rollup.overdue_items = 125
rollup.by_status     = {
    "open":           250,
    "in_progress":      2,
    "pending_review":   0,
    "resolved":         4,
    "closed":          16,
    "cancelled":        5
}
```

Per-source breakdown:

| Section | total | by_status (open · in_progress · pending_review · resolved · closed · cancelled) |
|---|---|---|
| tasks | 100 | 100 · 0 · 0 · 0 · 0 · 0 |
| safety.corrective_actions | 8 | 8 · 0 · 0 · 0 · 0 · 0 |
| po.requests | 100 | 91 · 0 · 0 · 4 · 0 · 5 |
| equipment.dvir | 50 | 34 · 0 · 0 · 0 · 16 · 0 |
| safety.incidents | 19 | 17 · 2 · 0 · 0 · 0 · 0 |
| virtual.signals | 0 | 0 · 0 · 0 · 0 · 0 · 0 |

Every status value across all 277 live projections is a member of `CANONICAL_STATUSES` — enforced by `test_snapshot_every_status_is_canonical`. Roll-up arithmetic verified by `test_snapshot_rollup_arithmetic_matches_sections`.

---

## 5 · Source parity (success condition)

The directive's success condition:

> "A read-only Accountability service exists and returns canonical accountability records from all six certified sources while preserving source workflow behavior."

Two assertions in the suite:

| Pytest | Asserts |
|---|---|
| `test_snapshot_every_item_has_canonical_24_field_shape` | Every item in every non-empty section has **exactly** the 23-field canonical key set |
| `test_snapshot_source_parity_all_non_empty_sections_match_field_set` | All non-empty sections share an **identical** key set (no per-source field drift) |

The 23 canonical fields verified at the network boundary:

```
{accountability_id, source_module, source_record_id, title,
 owner_role, owner_user_id, owner_employee_id, owner_display_name,
 assigned_at, assigned_by, due_at, status, priority,
 first_viewed_at, first_viewed_by,
 last_activity_at, last_activity_kind,
 escalation_level,
 resolved_at, resolved_by, resolution_notes,
 overdue, timeline_events}
```

**Pillar 1B reservation:** every item projects `escalation_level=0`. Verified by `test_snapshot_every_item_has_escalation_level_zero` (covered 277 live items in the preview environment).

---

## 6 · Auth surface verification

| Scenario | Endpoint | Expected | Observed |
|---|---|---|---|
| No token | `/sources` | 401 | 🟢 401 |
| No token | `/snapshot` | 401 | 🟢 401 |
| No token | `/item` | 401 | 🟢 401 |
| Bad token | `/sources` | 401 | 🟢 401 |
| Bad token | `/snapshot` | 401 | 🟢 401 |
| Bad token | `/item` | 401 | 🟢 401 |
| Valid admin token | `/sources` | 200 | 🟢 200 |
| Valid admin token | `/snapshot` | 200 | 🟢 200 |
| Valid admin token | `/item?source_module=tasks&source_record_id=<live>` | 200 | 🟢 200 |
| Valid admin token | `/item?source_module=tasks&source_record_id=missing` | 404 | 🟢 404 |
| Valid admin token | `/item?source_module=unknown.workflow&...` | 400 | 🟢 400 |
| Valid admin token | `/item?source_module=virtual.dr_missing&...` | 404 | 🟢 404 |

Auth is gated by `require_admin_strict` — the same gate that protects backups, recovery, Command Center. **No new auth code was written in this phase.**

---

## 7 · No-workflow-regression verification

Pytests probing pre-existing surfaces inside the same suite:

```
test_command_center_snapshot_still_returns_200    PASSED  (200 with admin token)
test_backups_scheduler_state_still_returns_200    PASSED  (200 with admin token)
test_recovery_snapshot_still_returns_200          PASSED  (200 with admin token)
test_health_still_returns_200                     PASSED  (ok=true)
```

Plus:

- Phase 1A-2 unit suite still passes (51/51 · 0.05s) → projection contract unchanged.
- Path B Command Center suite still passes (20/20) → Pulse aggregate reconciliation intact; D1/D2/D5 patches green.

**Zero source workflow file modified · zero source row mutated · zero collection created · zero notification emitted.**

---

## 8 · Out-of-scope verification

| Item | Verdict |
|---|---|
| Escalation Framework | 🛑 NOT BUILT (`escalation_level=0` enforced by `test_snapshot_every_item_has_escalation_level_zero` across 277 live items) |
| Notifications / Emails / SMS | 🛑 NOT BUILT |
| Dashboard UI | 🛑 NOT BUILT (zero frontend file changed) |
| Executive Command Center integration | 🛑 NOT BUILT (`command_center.py` md5 unchanged; the new endpoints exist but no Command Center code path consumes them) |
| ForgedOps Portal | 🛑 NOT BUILT |
| White Label Architecture | 🛑 NOT BUILT |
| Pillar 2 / 3 / 4 work | 🛑 NOT BUILT |
| Phase 1A-4 and beyond | 🛑 NOT BUILT |

---

## 9 · Phase 1A-3 closeout

🟢 **Certified.** A read-only Accountability service surface is live in preview. All seven certification requirements satisfied with pytest evidence anchored to live HTTP probes. 21/21 service tests green · 92/92 combined regression-free · zero workflow regression · zero pre-existing test regression.

🛑 **STOPPED.** No additional work without operator authorization.
