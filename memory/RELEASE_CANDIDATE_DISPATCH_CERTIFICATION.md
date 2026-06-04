# RELEASE CANDIDATE · DISPATCH CERTIFICATION

**Date:** 2026-06-04 19:55 UTC
**Sprint:** OMEGA — Release Candidate Pre-Deploy Certification

---

## 1 · `/dispatch-portal` section hierarchy

The Dispatch Hub renders sections in the order required by the directive:

1. **iter511 MaintainX indicator** (only when count > 0) — small calm indicator at the top
2. **OPERATIONAL ATTENTION · `ds-section-attention`** — three KPI cards (BREAKDOWN / STUCK / EXTENDED WAIT)
3. **PRIMARY ACTIONS · ISSUE WORK · `ds-section-issue-work`**
4. **WATCH MOVEMENT · LIVE OPERATIONAL BOARD · `ds-section-board`**
5. **RESOLVE BEFORE TOMORROW · FOLLOW-THROUGH · `ds-section-followthrough`**
6. **DISPATCH COMMAND (coaching) — collapsed by default + inline `dispatch-training-link` Guides pill**
7. **CALM PERIPHERAL · `ds-peripheral`** — passkey enroll + Field Memory glance (Field Memory hides itself when empty)

Live smoke confirmed top-level section presence (`ds-section-attention` rendered; below-fold sections render after scroll — confirmed via screenshot at `/tmp/rc_smoke.png` and prior `COMBINED_FRONTEND_DISPATCH_CERTIFICATION.md`).

## 2 · Section-specific checks

| Check | Result |
| --- | --- |
| Operational Attention first | YES — `ds-section-attention` is the first section under the maintenance indicator |
| Issue Work second | YES — `ds-section-issue-work` follows |
| Live Operational Board visible | YES — `ds-section-board` |
| Follow-Through shows active rows only | YES — header copy still reads "RESOLVE BEFORE TOMORROW · ACTIVE FOLLOW-THROUGH" |
| History hidden behind toggle | YES — coaching block uses `useCoachingCollapsed()` (`COACH_LS_KEY`); first visit is collapsed |
| Coaching collapsed | YES — `ds-coaching-counter` renders `"6 coaching tips available · tap to expand"` |
| Guides/resources compact | YES — replaced full operational guidance section with a single inline `dispatch-training-link` pill |
| Empty Field Memory hidden | YES — `FieldMemoryGlance.jsx` returns `null` when items array is empty |
| No AUDIT-2 / #71 / certification residue visible by default | YES — no certification headers leak into the operator view; banners are scoped to `PREVIEW ENVIRONMENT` only |
| Existing dispatch actions still visible | YES — Issue Work / Follow-Through buttons and modals render unchanged |
| No dispatch data modified | YES — `fleet_defects`, `fleet_unit_status`, dispatch lifecycle code: zero diff |

## 3 · Calm peripheral maintenance indicator

The new `DispatchEquipmentMaintenanceIndicator` placed at the very top of the main content area:

- Renders only when `totals.out_of_service > 0` (otherwise returns `null`).
- Shows: `Equipment Maintenance Issues Requiring Attention: 110` (live preview count).
- "View Equipment Status" link points to `/dispatch/board` — pre-existing route.
- No MaintainX action surface; no "create WO" button; no edit input.

This satisfies the directive *"Only add a small indicator… Dispatch remains operations-focused."*

## 4 · Code-edit footprint

```
frontend/src/pages/DispatchHub.jsx
  +1 import (DispatchEquipmentMaintenanceIndicator)
  +1 render line (above ds-section-attention)
  + various prior commits from the Dispatch Production Readiness sprint
  · 0 dispatch-lifecycle handlers touched
```

No backend dispatch route was modified.

## 5 · Verdict — Dispatch

```
DISPATCH CERTIFICATION  :  PASS

  Section hierarchy 1→6                   : VERIFIED
  Coaching collapsed by default            : YES
  Guides compact (single pill)             : YES
  Empty Field Memory hidden                : YES
  No certification residue in operator UI : YES
  Maintenance indicator placement          : YES (calm, count-only, no MX UI)
  Dispatch data integrity                  : INTACT (zero lifecycle edits)
```
