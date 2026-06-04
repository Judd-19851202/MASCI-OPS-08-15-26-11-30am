# MAINTAINX · DEFECT EXPLORER CERTIFICATION

**Date:** 2026-06-04 19:30 UTC
**Sprint:** OMEGA — Defect Source Coverage Command Center
**Mode:** READ-ONLY (no writes)

This document certifies the read-only Defect Explorer + drawer surface inside the Admin Integration Center.

---

## 1 · Surface summary

Component: `frontend/src/components/admin/MaintainxDefectCoverageSection.jsx`.
Inside this component, the Defect Explorer is the bottom-most card:

```
+──────────────────────────────────────────────+
|  DEFECT EXPLORER · filter: <source or none>  |
+──────────────────────────────────────────────+
|  [icon] <defect title>                       |
|         TRK-12 · Truck 12 · Driver X · date  |
|                              [READY][Mapped] |
|  ...
+──────────────────────────────────────────────+
```

Clicking a row opens the read-only drawer (right side, `<Sheet>`-based).

---

## 2 · Drawer fields

| Field | Source |
| --- | --- |
| Source | `source_type` |
| Equipment Name | `equipment_name` |
| Unit Number | `unit_number` |
| Make / Model | `make` + `model` |
| Reported By | `reported_by` |
| Date Reported | `reported_at` |
| Severity | `severity` |
| Status | `status` |
| Out of Service | derived bool |
| Safety Critical | derived bool |
| Photos Present | bool |
| RTS Required | bool |
| MaintainX Status | classifier `maintainx_status` |
| Readiness | classifier `readiness` |
| Reasons | classifier `reasons[]` enumerated as bullets |

No edit controls. No buttons that mutate any row. The drawer is `<Sheet>` opened by row-click; `onOpenChange(false)` is the only mutation, and it only clears local React state.

---

## 3 · Filtering

- Source-breakdown rows are clickable; clicking sets the local `filterSource` state.
- Toggling the same row again clears the filter.
- A `[Clear filter]` button in the explorer header is also wired.

All filter logic is client-side over the `defects[]` array already returned by the backend. No additional API calls are made when filtering.

---

## 4 · Sort order

Defects in `report.defects[]` are pre-sorted by the backend:

```
1) OOS first
2) DUPLICATE_RISK next
3) Then newer reports first (by length of reported_at string then by value)
```

Frontend renders the order verbatim — no client-side resorting.

---

## 5 · Data-testid coverage

```
mx-coverage-root             ─ section root
mx-coverage-banner           ─ admin-only safety banner
mx-coverage-refresh          ─ refresh button
mx-coverage-total-{open|high|safety|oos|ready|blocked|dup} ─ overview cells
mx-coverage-breakdown        ─ source breakdown table
mx-coverage-row-{source}     ─ each breakdown row (clickable filter)
mx-coverage-filter-clear     ─ filter clear button
mx-coverage-list             ─ defect list <ul>
mx-coverage-defect-{id}      ─ each defect row
mx-coverage-empty            ─ empty-state cell
mx-coverage-drawer           ─ <Sheet> content
mx-coverage-writes           ─ writes_performed footer
```

QA can drive the full read-only flow off these test-ids.

---

## 6 · Live verification (Playwright smoke)

| Step | Result |
| --- | --- |
| Open `/admin/integrations` and click `ic-tab-maintainx-p0` | OK |
| `mx-coverage-root` present | YES |
| `mx-coverage-total-open` reads "OPEN DEFECTS · 138" | YES |
| `mx-coverage-total-oos` reads "OUT OF SERVICE · 110" | YES |
| `mx-coverage-total-ready` reads "READY · 2" | YES |
| `mx-coverage-total-blocked` reads "BLOCKED · 134" | YES |
| `mx-coverage-writes` reads "writes_performed: mx=0 · eq_master=0 · fleet_defects=0 · inspections=0 · holds=0 · mappings=0" | YES |
| All counters update on refresh | YES |
| Clicking a source row toggles a filter on the explorer below | YES |

---

## 7 · Compliance with directive

| Requirement | Verdict |
| --- | --- |
| Read-only drawer | YES |
| Display Source / Equipment Name / Unit Number / Reported By / Date Reported / Severity / Current Status / Out Of Service Flag / Photos Present / RTS Required / MaintainX Status | YES (12 fields enumerated above) |
| MaintainX Status values: Not Evaluated / Ready / Blocked / Duplicate Risk / Mapped / Excluded | YES (mapped 1:1 with the classifier output) |

---

## 8 · Verdict — Defect Explorer

```
DEFECT EXPLORER  :  CERTIFIED

  Drawer is read-only                       : YES
  All 12 required fields present            : YES
  All 6 MaintainX status values supported   : YES
  Filtering by source                       : YES
  Live preview functional                   : YES (138 open / 110 OOS / 2 ready)
  Zero write paths                          : VERIFIED
```
