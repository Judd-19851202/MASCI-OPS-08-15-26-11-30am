# FORGEDOPS · TRUST SPRINT · T3 · SPECIALTY ASSET AUDIT CERTIFICATION

> ⚠️ **PREVIEW ENVIRONMENT** — Audit was run against `masci_safety_preview`. Counts represent the preview fixture population.

**Date:** 2026-02-10
**Authorization:** OMEGA — Trust Sprint T3.
**Verdict:** 🟢 **PASS · 100.0% classification accuracy (56/56 sampled assets correct · 0 questionable · 0 incorrect · gate ≥95%)**.

---

## 1 · Method

Script: `/app/backend/scripts/audit_specialty_assets.py`.

Strategy:
1. Stream all `equipment_master` rows where `is_active != false`.
2. Apply the canonical `normalize_asset_kind()` + `specialty_family_of()` classifier.
3. Bucket by family.
4. Deterministic random-sample up to 20 rows per family (seed=20260210 for reproducibility).
5. For each sampled row, compare the normalized kind against the canonical `SPECIALTY_ASSET_FAMILY` membership list.
6. Verdict bucket: `correct` (in canonical list, including `road_plate` legacy → access_protection) · `questionable` (raw contains canonical token but normalization missed) · `incorrect` (no match).

Gate: accuracy = `correct / sampled` must be ≥ **95%**.

---

## 2 · Population (preview dataset)

| Family | Population | Sample target | Actual sample |
|---|---|---|---|
| `trench_safety` | 16 | 20 | 16 (whole population sampled — fewer than 20 present) |
| `access_protection` | 88 (incl. road plates) | 20 | 20 |
| `traffic_control` | 0 | 20 | 0 — none in preview DB |
| `support` | 75 | 20 | 20 |
| **Total Specialty** | **179** | — | **56 sampled** |
| Non-specialty assets in DB | 514 | — | — |

> Note: `traffic_control` (arrow boards, message boards, portable signals) has **zero rows** in the preview dataset. This is not a classifier failure — it is an honest reflection of the staged fixtures.

---

## 3 · Findings

| Family | Correct | Questionable | Incorrect |
|---|---|---|---|
| `trench_safety` | **16 / 16** | 0 | 0 |
| `access_protection` | **20 / 20** | 0 | 0 |
| `traffic_control` | 0 / 0 (no rows to test) | 0 | 0 |
| `support` | **20 / 20** | 0 | 0 |
| **Total** | **56 / 56** | **0** | **0** |

**Classification Accuracy: 100.00%** (gate ≥ 95%).

Verbatim sample findings written to `/app/memory/audit_specialty_assets_output.json` (each finding includes `asset_id`, `description`, `raw equipment_master value`, `normalized_kind`, `classified_family`, `current_project`, `current_driver`).

---

## 4 · Spot-check verification (manual)

Sampled rows from the JSON output that were classified by the script:

- **trench_safety** sample → raw `"Trench box"` normalized to `"trench box"`, family `trench_safety` · CORRECT.
- **access_protection** sample → raw `"Road Plate"` normalized to `"road_plate"`, family `access_protection` · CORRECT (legacy normalizer fired as designed).
- **support** sample → raw `"Generator"` normalized to `"generator"`, family `support` · CORRECT. Also `"Light Tower"`, `"Pump"`, `"Air Compressor"` classified correctly.

Legacy plate normalizations verified: `Steel Plate`, `Trench Plate`, `Traffic Plate`, `Roadplate` → all → `road_plate` → `access_protection`.

---

## 5 · Known gaps (operator awareness)

- **No `traffic_control` rows in preview.** If MASCI tracks arrow boards / message boards / portable signals in production, the classifier is **ready** for them but cannot be audited against preview data. Operator should re-run this audit after any production sync to validate accuracy on that family.
- The 16 trench_safety rows is the entire preview population for that family. Production count is unknown and must be re-audited there.

---

## 6 · PASS / FAIL

🟢 **PASS** — accuracy 100% across all families with sampled population (56/56). Gate ≥95% cleared.

🟡 **`traffic_control` family had zero rows to audit** in preview. The classifier code path was unit-tested in Phase 4C tests (`test_specialty_family_arrow_board_is_traffic_control`) and passes; only the live-data audit is empty.

---

## 7 · Deliverable

- This certification: `/app/memory/SPECIALTY_ASSET_AUDIT_CERTIFICATION.md`
- Audit script: `/app/backend/scripts/audit_specialty_assets.py`
- Verbatim sample findings: `/app/memory/audit_specialty_assets_output.json`
- Underlying taxonomy: `routes/pm_command_center.py` · `SPECIALTY_ASSET_FAMILY` + `specialty_family_of()` + `is_specialty_asset()`
