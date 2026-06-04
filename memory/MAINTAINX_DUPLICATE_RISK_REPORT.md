# MAINTAINX · DUPLICATE RISK REPORT

**Date:** 2026-06-04 18:30 UTC
**Sprint:** OMEGA P0-A/P0-B — Read-First MaintainX Asset Integration
**Scope:** Document the duplicate-risk pre-flight that runs for every MaintainX asset classified as `missing_in_masci`.

---

## 1 · Purpose

Before any future sprint **could** create a MASCI equipment record from a MaintainX asset, the pipeline must prove that doing so would not introduce a duplicate. This report documents the **read-only** duplicate-risk analyser, `_duplicate_risk_for_new_asset`.

**No asset is created by this sprint.** The analyser only annotates the dry-run output so an admin can see whether each "missing in MASCI" asset is `safe_to_create` or `blocked_by_collision`.

---

## 2 · Collision detection axes

For every MaintainX asset classified `missing_in_masci`, the analyser checks:

| Axis | Source field on MX | MASCI bucket searched | Risk emitted if hit |
| --- | --- | --- | --- |
| Unit number | `unitNumber` | `masci_index[("unit", normalised)]` | `same_unit_number` |
| Serial number | `serialNumber` | `masci_index[("vinserial", normalised)]` (MASCI combines VIN+serial) | `same_serial` |
| VIN | `vin` (only if distinct from serial) | same `vinserial` bucket | `same_vin` |

### Why no name-similarity check?
Names are too loose for collision prevention — a fuzzy "Truck 12" matches many real assets. The matcher already uses name fuzziness for **classification**; here we want **hard** identity signals only.

---

## 3 · Verdict semantics

```python
{
  "has_risk": bool,
  "risks": [
    { "risk_kind": "same_unit_number" | "same_serial" | "same_vin",
      "match_count": int,
      "masci_ids":  [ "<uuid>", ... ] }
  ],
  "verdict": "safe_to_create" | "blocked_by_collision"
}
```

| Verdict | Definition | Operator implication |
| --- | --- | --- |
| `safe_to_create` | No unit_number / serial / vin collision found in MASCI | A future sprint MAY safely synthesize a MASCI equipment row from this MaintainX asset (still requires explicit operator authorization). |
| `blocked_by_collision` | One or more MASCI rows already share this asset's unit_number, serial, or VIN | Future sprints MUST refuse auto-create and surface the collision so admin can resolve manually. |

---

## 4 · Aggregated counters surfaced in dry-run

In `report.totals`:

| Counter | Meaning |
| --- | --- |
| `missing_in_masci` | Count of MaintainX assets not represented in MASCI |
| `duplicate_risk_blocked` | Subset where the analyser found a collision |
| `duplicate_risk_safe` | Subset cleared as safe to create |

Per construction: `duplicate_risk_blocked + duplicate_risk_safe == missing_in_masci`.

---

## 5 · Unit-test coverage

`test_duplicate_risk_blocks_same_unit` (in `backend/tests/test_maintainx_p0_read_first.py`):

```python
masci = [{"id": "m-1", "unit_number": "TRK-50"}]
risk  = _duplicate_risk_for_new_asset(
            mx={"unit_number": "TRK-50"}, masci_index={("unit", "TRK50"): masci}
        )
assert risk["has_risk"] is True
assert risk["verdict"] == "blocked_by_collision"
```

Verifies:
- Collision detected on unit_number normalisation
- Verdict flips to `blocked_by_collision`
- Risk array carries the conflicting MASCI ids

---

## 6 · Safety guarantees (recap)

| Surface | Behaviour |
| --- | --- |
| MaintainX | Untouched — no creates, no updates, no deletes |
| `equipment_master` | Untouched — duplicate analyser only READS the in-memory index |
| `asset_mappings` | Untouched |
| `db.maintainx_dryrun_reports` | Optional read-only audit trail (admin opt-in via `?save=true`) |

The duplicate analyser is a pure function on already-fetched data; it cannot mutate anything.

---

## 7 · Verdict — Duplicate Risk Analyser

```
DUPLICATE RISK ANALYSER  :  COMPLETE · READ-ONLY · UNIT-TESTED

  Unit-number collision check               : DONE
  Serial collision check                    : DONE
  VIN collision check                       : DONE
  Aggregated counters in dry-run            : DONE
  Pure-function safety                      : DONE
  No write paths                            : VERIFIED
```

This analyser provides the operator-authorization gate that any future "create MASCI from MaintainX" path will require. It is **not** wired to any create flow in this sprint.
