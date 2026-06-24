# TRACK 15.75 · Phase 12 — Production Data Remediation Plan

Evidence: `/api/admin/pm-email-coverage`, Track 15.73Q audit.

**Hard rule:** No production DB writes by E1 / agent. Operator
performs each action via the admin UI. Plan is the artifact.

## Remediation #1 — Active jobs missing PM email (7)

| Row # | `project_number` | `project_name` | Recent DR count | Authoritative source | Operator action | Confidence | Risk if unchanged |
|---|---|---|---|---|---|---|---|
| 1 | `20-07` | T5686 SR 15/SR600 (SANFORD, 17/92, LAKE MARY) | **53** (last 2026-06-19) | `/admin → Project Managers` directory | `/admin → Active Jobs Master → 20-07 → PM cell → assign` | high (active project) | DRs continue routing to dead-letter (visible, not silent). Co-PM `pm.demo@mascigc.com` still CC'd. |
| 2 | `26-07` | University High Parent Loop Ext | **16** (last 2026-06-22) | same | same | high | DRs dead-letter; **no co-PM either** — only `safety@mascigc.com` notified. |
| 3 | `21-06` | T5736 Oveido (426, BROADWAY) | 0 | same | same | medium (no recent DR) | low immediate impact |
| 4 | `22-08` | T5749 SR 436 (ALTAMONTE SPRINGS) | 0 | same | same | medium | low |
| 5 | `24-08` | E57B2 - SR 46 (MELLONVILLE AVE) | 0 | same | same | medium | low |
| 6 | `26-04` | E58F7 - SR 5 | 0 | same | same | medium | low |
| 7 | `SD-6909db` | SD test | 0 | unclear (looks synthetic — verify with operator) | possible delete or mark `active=false` | low | none |

**Recommended order:** 1, 2 first (high impact). 3-6 next. 7 verify
intent — may be deletable.

## Remediation #2 — Active jobs with co-PM email only (2)

These are subsets of the table above (20-07 and 21-06).

After Remediation #1, the routing for these projects will become
DIRECT_PM with co-PM in CC.

## Remediation #3 — Legacy equipment_master rows missing `unit_number` (247 / 705)

* Already documented in Track 15.73 Slice 4.
* Picker guardrails (Track 15.73 Slice 3) ensure new equipment
  inspections **cannot** be submitted without a `unit_number` for
  the selected asset.
* These 247 records are small gear (pumps, generators, hand tools)
  classified under `display_label` only — no operational impact
  unless one of them is inspected.
* **Operator action:** spreadsheet export from `/admin → Equipment`,
  backfill `unit_number` in bulk, re-import. **Optional, non-blocking.**

## Remediation #4 — `employees.employee_id` empty on 388 / 396 rows

* The current code uses `id` (UUID) and `email` as the canonical
  employee identity (verified Phase 5 + Track 15.73 Slice 2
  attendee normalization).
* `employee_id` is a vestigial field used only by external HR-side
  imports.
* **Operator action:** Defer. Not on the critical path.

## Remediation #5 — Yard incidents / QAQC without project_number (17 + 10)

* All affected rows are test harness fixtures
  (`project_name="iter363-…"`, `"iter364-QAQC-…"`).
* **Operator action:** None required — these are fixtures from
  prior track runs. If desired, an admin-side cleanup script can
  remove them; otherwise harmless.

## No prod DB writes performed

All Track 15.75 evidence collection ran read-only against
`masci_safety_preview`. No `update_one`, `insert_one`,
`replace_one`, or `delete_*` was executed by E1.
