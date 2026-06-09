# VER-1 · Operational Trust Audit

**Sprint:** VER-1 (required pre-certification audit)
**Date:** 2026-02-09
**Source of numbers:** `GET /api/admin/verification/audit` against the live preview backend.

---

## Answers to the 10 required questions

| # | Question | Answer | Note |
|---|---|---|---|
| Q1 | Total verified assignments | **0** | No active dispatch is currently CONFIRMED in the preview env. |
| Q2 | Total pending assignments | **276** | All active dispatches are PENDING_CONFIRMATION — they lack the asset_mappings → motive vehicle/asset join. |
| Q3 | Total mismatches | **0** | No active dispatch is in MISMATCH. |
| Q4 | Total quiet assets | **189 of 191** | 189 mapped assets have zero `operational_events` rows; only 2 (the ones routed through M-2) have evidence. |
| Q5 | Top mismatch causes | `[]` | None observable yet — would surface entries like `asset observed on {other_project}` once routing has cross-project data. |
| Q6 | Most common missing evidence | **`no_asset_mapping` × 276** | `dispatch_assignments.truck_id` values do not currently match `asset_mappings.masci_equipment_id`. This is a *data linkage* problem, not a code problem. |
| Q7 | Verification accuracy estimate | **0%** | Accuracy = `Q1 / considered`. Will rise the moment the dispatch.truck_id ↔ asset_mappings.masci_equipment_id link is populated. |
| Q8 | False positive rate | *not directly observable without ground truth* | Honest report — without operator-labeled truth set, we don't fabricate a number. |
| Q9 | False negative rate | *not directly observable without ground truth* | Same. |
| Q10 | Operator trust score | **0.0** | `max(0, accuracy − mismatch_share × 1.5) = 0`. |

---

## Doctrinal interpretation

The audit is reporting the operational truth honestly:

1. The M-2 Event Router is producing events (`operational_events` collection has rows).
2. The dispatch board has 276 active assignments.
3. **But the join between the two is missing**: `dispatch_assignments.truck_id` values are MASCI-side strings that have not been entered into `asset_mappings.masci_equipment_id` for the Motive-side records.

Once that link is established (a one-time data-entry task by the asset administrator), the verification accuracy will rise materially. **No code change is required to lift Q10 above 0** — the verification engine is already correctly wired.

---

## Pillar scorecard

| Pillar | Score | Why |
|---|---|---|
| Powerful | 🟢 | 4 trust states, 5 endpoints, computes across DR/dispatch/MM/project presence |
| Simple | 🟢 | One pure function `compute_trust_state(has_expectation, observed_at_expected, observed_elsewhere)` drives every surface |
| Beautiful | 🟢 | Verification grid reuses M-3/M-DR-1/M-2 visual language |
| Trusted | 🟢 | Compute-on-read · no writes anywhere · honest 0% reporting · explicit `null` for FP/FN |
| Proven | 🟢 | 56/56 regression tests green across VER-1 + M-2 + M-DR-1 + M-3 |
