# FORGEDOPS · P0-D · TRUTH GAP ANALYSIS

**Date:** 2026-02-10 · **Verdict:** 🟡 **MIXED — production-vs-preview gaps documented; severities assigned; remediation priorities set.**

---

## 1 · Headline gaps (highest severity first)

### 🔴 CRITICAL — Asset Spine ↔ Motive coverage = ZERO
- Production Motive-mapped: **0** of 596 assets (0%)
- Preview Motive-mapped: **0** of 693 assets (0%)
- **Impact:** Without Motive ↔ Asset Spine mapping, the Live Operations Map will have NO real GPS data to render. Every row will classify `UNKNOWN` confidence.
- **Severity:** **CRITICAL** — blocks Phase 5B map UI by itself, independent of the credential issue.
- **Remediation:** Wire Motive vehicle IDs into `equipment_master.motive_truck_id` for fleet assets (Phase 1 of Motive activation).

### 🔴 CRITICAL — preview pod credential = cluster-wide
- Documented exhaustively in `ATLAS_CLUSTER_SPLIT_RECONCILIATION.md` + `ATLAS_USER_ISOLATION_CERTIFICATION.md`.
- **Severity:** **CRITICAL**.
- **Remediation:** Operator executes Atlas user separation runbook.

### 🟡 HIGH — Production has 0 road plates; preview shows 88
- Preview fixtures inflated specialty_assets total by ~10% with phantom road plates.
- **Severity:** **HIGH** (taxonomy / UI labeling, not data corruption — Phase 4C correction was specifically designed to keep road plates as ONE family member, not privileged).
- **Remediation:** Production UI counts will naturally show 0 road plates when wired to `/api/operations-map/contract`; no code change needed. Any text claiming "MASCI has X road plates" must be removed from PRDs / certifications (already done in Data Truth Correction).

### 🟡 HIGH — Production has 0 active dispatches today
- Preview had 272 fixture dispatches.
- **Severity:** **HIGH** for Live Operations Map (no haul rows to render today).
- **Remediation:** None — this is operational reality. Map will render honest empty states.

### 🟡 MEDIUM — Production has 0 CAPAs and 0 open defects
- Preview had 24 CAPAs, 0 defects.
- **Severity:** **MEDIUM** — Operations Center safety + shop sections will be calm-empty in production.
- **Remediation:** None — operational reality.

### 🟡 MEDIUM — `drivers_in_employees` query returns 0 in both envs
- The query filters by `role=driver` OR `position` regex-match `driver`. Returns 0.
- **Severity:** **MEDIUM** — data-shape unknown for driver classification.
- **Remediation:** Confirm how MASCI tags drivers in `employees` (is it a separate `roles[]` array? a `driver_license_*` field?). Update the classifier.

### 🟢 LOW — Trench box count differs (7 prod vs 16 preview)
- Production has fewer trench boxes than preview fixture. This is honest reality.
- **Severity:** **LOW** — operational expectation, not a defect.

### 🟢 LOW — `traffic_control` family has zero rows in production
- Confirms what preview audit also showed.
- **Severity:** **LOW**.
- **Remediation:** None — classifier ready for when MASCI starts tracking arrow boards/message boards/signals.

---

## 2 · Severity-counted summary

| Severity | Count |
|---|---|
| 🔴 CRITICAL | 2 (motive coverage = 0% · credential cluster-wide) |
| 🟡 HIGH | 2 (phantom road plates · 0 active dispatches) |
| 🟡 MEDIUM | 2 (CAPAs/defects empty · driver classification) |
| 🟢 LOW | 2 (trench box delta · traffic_control empty) |

---

## 3 · Missing / duplicate / orphaned / mismatched / unknown / unmapped

| Category | Finding |
|---|---|
| **Missing assets** (in production, not preview) | Net production has 97 *fewer* active assets than preview (596 vs 693). All 97 are fixture-only preview rows. |
| **Duplicate assets** | Not detected in this audit (no `unit_number` collision pass — added to follow-up backlog). |
| **Orphaned assets** | Per `equipment_master`, no asset is missing a `unit_number` or `id`. |
| **Mismatched assets** | None at the count level; per-row reconciliation deferred to follow-up. |
| **Unknown kinds** | preview 0 · production 0 (classifier handles every observed `type` value). |
| **Unmapped to Motive** | preview 693/693 · production 596/596 — 100% unmapped both envs. |

---

## 4 · Verbatim machine-readable output

`/app/memory/p0_audit_truth_gap.json` — full bucket-by-bucket delta JSON.

## 5 · Deliverable
- This analysis
- `/app/memory/p0_audit_truth_gap.json`

---
