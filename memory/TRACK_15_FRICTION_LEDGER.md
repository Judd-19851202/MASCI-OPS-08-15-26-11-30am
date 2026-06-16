# TRACK 15.0 · FRICTION LEDGER

**Phase 18 deliverable. Every friction point discovered during operational reality certification. Categorized by severity and operational impact.**

## P0 — Blocks daily operations

| # | Role | Workflow | Step | Issue | Safe fix applied | Remaining issue | Impact |
|---|------|----------|------|-------|------------------|-----------------|--------|
| — | — | — | — | **None found.** | n/a | n/a | n/a |

🟢 **Zero P0 friction discovered.**

## P1 — Significant friction

| # | Role | Workflow | Step | Issue | Safe fix applied | Remaining issue | Impact |
|---|------|----------|------|-------|------------------|-----------------|--------|
| — | — | — | — | **None found.** | n/a | n/a | n/a |

🟢 **Zero P1 friction discovered.**

## P2 — Mild annoyance · documented

| # | Role | Workflow | Step | Issue | Safe fix applied | Remaining issue | Impact |
|---|------|----------|------|-------|------------------|-----------------|--------|
| F-1 | Safety | Daily Report cross-reference during incident investigation | Safety has to ask PM for daily report by email/chat | Documented in `SAFETY_DAILY_REPORTS_PERMISSION_REVIEW.md`. D-A3 deferred per hard rules (permission redesign). | YES — Safety must work around | Low-medium: requires a 5-min cross-team conversation per investigation. Acceptable for now per documented audit (Option C or D path forward when track opens). |
| F-2 | Admin (V2 audit) | V2 sidebar lacks Command Center · Asset Administration · Operational Records | V2 is feature-flagged OFF in production — does not impact daily use today | None (audit-only) | YES — V2 would need parity work before promoted to default | Zero impact today. Will matter if V2 promotion track opens. |
| F-3 | Admin / dev hygiene | 4 pre-existing pytest files have import errors (`test_equipment_inspections`, `test_iter138_typeahead_bindings`, `test_iter139_master_lookup_filters`, `test_sprint1c_incident_delete`) | Tests don't COLLECT — orthogonal regression noise, not a runtime defect | None (out-of-scope per hard rules — pre-existing, not Track-15-introduced) | YES — should clean up in a future test-hygiene pass | Zero impact on runtime; minor CI noise. |

## P3 — Cosmetic / future polish

| # | Role | Workflow | Step | Issue | Safe fix applied | Remaining issue | Impact |
|---|------|----------|------|-------|------------------|-----------------|--------|
| F-4 | PM | Trench Safety nested badges re-use Safety component library (cyan icons inside red PM chrome) | Top chrome is unambiguously PM red; only deep-nested badges/icons are cyan | None — visual identification confirmed unambiguous in runtime | YES — could be styled with stronger semantic class isolation later | Cosmetic. No user confusion reported. |

## Categorization

| Type | Count |
|------|-------|
| Broken workflow | 0 |
| Confusing workflow | 0 |
| Slow workflow | 0 |
| Hidden workflow | 0 (after this session's fixes) |
| Permission issue (deferred per hard rules) | 1 (D-A3) |
| Training issue | 0 |
| Future enhancement | 3 (V2 parity, test hygiene, badge styling) |

## Session fix-as-you-go inventory

Fixes applied INLINE during Track 15 (additive, low-risk):
- **G4** — Added `/odr/center` (Operational Daily Records) to Admin V1 sidebar so V1 has feature parity with V2 on this surface. Single line in `AdminShell.jsx`. No permission change.

Fixes applied earlier in this session that closed defects which would have surfaced as Track-15 friction:
- D-A11 (Spanish synonyms) — bilingual operator vocabulary
- D-A12 (PM sidebar parity) — Command Center / Holds / Due Today / Project Staffing / Trench Safety
- D-A13 (PM Trench Safety) — PmShell wrap, no shell hop
- D-A15 (Operational Records + Operations Actions in Admin V1)
- D-A16 (FL Portal Leadership submissions launcher card)
- D-A20 (HR Document Expirations canonical link)
- D-DA12-EXT — Overloaded Crew visibility on Project Staffing

## Verdict

🟢 **No P0 or P1 friction remains.** Track 15 closes as **OPERATIONALLY CERTIFIED.**
