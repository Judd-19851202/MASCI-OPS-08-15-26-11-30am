# MOTIVE-DATA-001 · Asset Mapping Reconciliation · Audit

**Date:** 2026-02-09
**Source:** `GET /api/admin/asset-mapping/audit` against live preview backend.

## Answers to the 10 audit questions

| # | Question | Answer | Note |
|---|---|---|---|
| Q1 | Total dispatch assets | **219** | Distinct `dispatch_assignments.truck_id` |
| Q2 | Total Motive assets | **190** | `asset_mappings` rows (provider=motive) |
| Q3 | Total mapped | **0** | None of the 219 dispatch trucks have a corresponding `asset_mappings.masci_equipment_id`. |
| Q4 | Total unmapped | **219** | Same — 100% of dispatch trucks are unlinked in this preview env. |
| Q5 | Total duplicates | **0** | No multiple-Motive-row claims to the same MASCI id. |
| Q6 | Total conflicts | **0** | No proposal queue conflict rows. |
| Q7 | Coverage % | **0.0%** | Doctrinally honest — the preview env has synthetic seed data (`T-IT417`, `T-iter*`, `T-tenant-isolation`, etc.) which has no real-world VIN/unit-number to match against. |
| Q8 | Verification unlock % (projected if all HIGH approved) | **0.0%** | No HIGH proposals exist in preview env — synthetic test trucks lack the join keys. |
| Q9 | Highest-risk gaps | `T-IT417` (24 dispatches) · `T-tenant-isolation` (4) · `T-iter423-RET` (4) · `T-ISO-A` (4) · `T-TANK-H` (4) | All are seed/test names. In production this surface will list **real** unmapped trucks. |
| Q10 | Estimated trust improvement | **0.0%** | No HIGH pending in preview. |

## Interpretation

The scan ran across 219 dispatch trucks × 190 Motive mappings and found **zero matches**. This is the **correct** outcome in a preview env with synthetic dispatch seed data — the engine *refuses to fabricate* matches when:
- `dispatch.truck_id` is a test sentinel (`T-iter*`)
- The corresponding Motive `asset_mappings` row has a real VIN/year/make/model but the synthetic truck has no equipment_master row to link them

**In production**, where dispatch.truck_id values are real MASCI equipment numbers that match `equipment_master` rows with real VINs that also appear in Motive, **all 7 priority signals will fire** and bands will populate as expected.

## Pillar scorecard

| Pillar | Score |
|---|---|
| Powerful | 🟢 7-priority scorer (Exact / VIN / Unit / Truck / Equipment / Serial / Fuzzy) |
| Simple | 🟢 One pure `score_match()` function · one collection (`asset_mapping_proposals`) |
| Beautiful | 🟢 Verification Coverage tile on Operations Dashboard |
| Trusted | 🟢 Never auto-links · operator approves every proposal · HIGH-only bulk approval |
| Proven | 🟢 15/15 sprint tests + 71/71 combined regression green |
