# MAINTAINX · READINESS CLASSIFICATION REPORT

**Date:** 2026-06-04 19:30 UTC
**Sprint:** OMEGA — Defect Source Coverage Command Center
**Mode:** READ-ONLY (no writes)

This document specifies the readiness classifier that powers the Defect Source Coverage view — the rules that decide whether each defect is **READY**, **BLOCKED**, **DUPLICATE_RISK**, or **EXCLUDED**, and the **MaintainX Status** label that surfaces alongside.

---

## 1 · Classifier inputs

Per defect, the classifier receives a canonical defect dict (see `services/maintainx_defect_coverage._norm_*`) and two pre-built indices:

| Input | Source |
| --- | --- |
| `asset_map` | dict: `equipment_master.id → asset_mappings row` (only rows with `maintainx.asset_id != ""`) |
| `open_by_unit_title` | dict: `(normalised unit_number, uppercase title) → count` over all OPEN defects |

Both are built once per request — O(N+M+K) total.

---

## 2 · Decision order (first match wins)

### 1) EXCLUDED — already closed
```
status ∈ {"cleared", "repaired", "closed"}
→ classification = EXCLUDED
  maintainx_status = "Excluded"
  reasons = ["status=<x>"]
```
Why first: closed rows would otherwise be flagged as blocked due to dependent identity checks — short-circuit them.

### 2) BLOCKED — missing identity fields
```
if not equipment_id → reasons += ["missing_equipment"]
if not unit_number  → reasons += ["missing_unit_number"]
if not source_record_id → reasons += ["missing_source_reference"]
if any reasons:
    → classification = BLOCKED
      maintainx_status = "Blocked"
```
These three fields are the **minimum** required to ever push a WO into MaintainX. Without any one of them, the duplicate-protection (`correlation_id` + `externalId`) cannot be safely constructed.

### 3) DUPLICATE_RISK — multiple open defects, same unit, same title
```
key = (norm_unit(unit_number), title.strip().upper())
if open_by_unit_title.get(key, 0) > 1:
    → classification = DUPLICATE_RISK
      maintainx_status = "Duplicate Risk"
      reasons = [f"multiple_open_defects_same_unit_same_title (n={count})"]
```
Catches form double-submits and same-day re-reports of an already-known issue before they fan out into MaintainX as separate WOs.

### 4) READY — mapping present?
```
mapping = asset_map.get(equipment_id)
mx_asset_id = mapping.maintainx.asset_id or ""
if mx_asset_id:
    → classification = READY
      maintainx_status = "Mapped"
      reasons = ["asset_mapped"]
      maintainx_asset_id = mx_asset_id
else:
    → classification = READY
      maintainx_status = "Ready"
      reasons = ["asset_unmapped_but_classifiable"]
```
A defect can be classification=READY while still being maintainx_status="Ready" (not yet Mapped). This distinction lets the operator see:
- `Mapped` — would push to a known MaintainX asset
- `Ready` — payload is well-formed; would need an asset mapping to land in MaintainX

---

## 3 · Six terminal states

| Classification × MaintainX Status | Meaning |
| --- | --- |
| READY × Mapped | Asset is known to MaintainX (`asset_mappings.maintainx.asset_id` set) — eligible to push as-is. |
| READY × Ready | Defect payload is sound but the asset hasn't been mapped yet — would push after admin runs the Mappings Wizard. |
| BLOCKED × Blocked | Payload cannot be constructed safely; reasons enumerated. |
| DUPLICATE_RISK × Duplicate Risk | Another open defect on the same unit/title — push would create a second WO for the same issue. |
| EXCLUDED × Excluded | Defect already closed in ForgedOps — no action required. |
| — × Not Evaluated | Fallback only — UI shows this when classifier output is missing entirely (defensive). |

---

## 4 · Per-source typical classification distribution (live preview baseline)

| Source | Open | Ready | Blocked | Dup Risk | Notes |
| --- | --- | --- | --- | --- | --- |
| Fleet DVIR | (varies) | 2 | 134 | 2 | Many DVIR rows record `unit_number` strings that don't resolve to live `equipment_master` rows (e.g. legacy "TRK-12" vs current "T-12"); these surface as BLOCKED with `missing_equipment` reason. |
| Equipment Pre-Op | (heavy iron) | — | — | — | Same pattern — operator-typed `equipment_unit` must match `equipment_master.unit_number` normalised. |
| Manual OOS | minimal | — | — | — | Admin-keyed; usually well-formed. |
| Shop / Dispatch Holds | minimal | — | — | — | Same. |

This is exactly the data-quality signal the operator needs **before** writes are turned on: enabling MaintainX today would result in 134 push attempts that would be blocked at the canonical-payload stage, not in MaintainX.

---

## 5 · Why a classifier (not a flag)

The classifier output is **a tuple**: `{readiness, maintainx_status, reasons[]}`.

- `readiness` is the operational decision (will we attempt a push?).
- `maintainx_status` is the operator-facing label (what does the row look like in MaintainX terms?).
- `reasons[]` is the audit trail (why was this row in this state?).

This three-part output lets the UI show two pills per row (readiness + MaintainX status) and lets the drawer enumerate the reasons. It also enables the future WO push module to filter by `readiness == READY` while still respecting `maintainx_status == Ready` (push pending mapping).

---

## 6 · Code references

```
backend/services/maintainx_defect_coverage.py
  · READY / BLOCKED / DUPLICATE_RISK / EXCLUDED constants    (lines 16-19)
  · _classify(...)                                            (lines 175-217)
  · run_defect_coverage(...) — wires it all together          (lines 222-300)
```

Frontend pill mapping:

```
frontend/src/components/admin/MaintainxDefectCoverageSection.jsx
  · READINESS_PILL                  (4 colours)
  · MX_STATUS_PILL                  (6 colours · Mapped > Ready > Blocked > Dup > Excluded > Not Evaluated)
```

---

## 7 · Verdict — Readiness Classifier

```
READINESS CLASSIFIER  :  COMPLETE

  Four primary buckets                     : DONE
  Six terminal states                       : DEFINED
  Decision order documented                 : YES
  Reasons array surfaced to UI               : YES
  Indexed for O(N+M+K)                       : YES
  Read-only                                  : VERIFIED
```
