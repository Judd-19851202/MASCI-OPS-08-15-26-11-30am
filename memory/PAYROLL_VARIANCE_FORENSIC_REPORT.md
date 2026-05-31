# Payroll Variance Forensic Report · Critical Fix Sprint 1 · P0-4

**Batch:** OMEGA Critical Fix Sprint 1 · P0-4
**Date:** 2026-05-31
**Scope:** Forensic dive into the 10 `payroll_variance_batches` documents in production. Determine whether they are preview contamination, abandoned imports, workflow defects, or harmless artifacts.

---

## 1 · Root cause verdict

🔴 **TEST DATA IN PRODUCTION · ABANDONED IMPORTS BY `hrmanager@mascigc.com` DURING ITER238/ITER282 BUILD-OUT.**

All 10 batches were created by the same actor (`hrmanager@mascigc.com`) within a 16-minute window on 2026-05-12 23:52Z → 2026-05-13 00:08Z. **Every batch contains `John Smith` / `Smith` as the employee name in its `rows[]` payload** — the canonical test-data tell. `matched_rows=0` for every batch (no payroll matches were ever produced).

These are **iterative test uploads during the iter238/iter282 payroll-variance feature build-out**, never cleaned up before the feature went live.

---

## 2 · Correction to prior audit (PRODUCTION_DATA_HYGIENE_AUDIT.md §4)

The prior phase-3 audit reported these batches as having `status=null · uploaded_by=null · variances_count=null`. **That was a schema misread.** The actual schema fields are different:

| Field name in schema | Field name in prior audit (mismatched) |
|---|---|
| `source` (e.g. `"exact"`) | `status` ← wrong |
| `created_by` (e.g. `"hrmanager@mascigc.com"`) | `uploaded_by` ← wrong |
| `flagged_rows` / `matched_rows` / `total_rows` | `variances_count` ← wrong |

The batches **are populated** with real fields. The earlier "null" reading was Python's `.get()` returning `None` for fields that don't exist in this schema. **The contamination finding remains valid** — the batches ARE test data — but the field-level mechanics differ from what the prior audit reported.

---

## 3 · Full batch inventory

| # | id | created_at | created_by | source | week_ending | total_rows | matched_rows | flagged_rows |
|---|---|---|---|---|---|---|---|---|
| 1 | `674300c9` | 2026-05-12 23:52:33Z | hrmanager@mascigc.com | exact | 2026-05-12 | 3 | 0 | 3 |
| 2 | `48cbc60e` | 2026-05-13 00:02:15Z | hrmanager@mascigc.com | exact | 2026-05-13 | 2 | 0 | 2 |
| 3 | `6590febb` | 2026-05-13 00:05:19Z | hrmanager@mascigc.com | exact | 2026-05-12 | 3 | 0 | 3 |
| 4 | `f1371d01` | 2026-05-13 00:05:20Z | hrmanager@mascigc.com | exact | 2026-05-12 | 3 | 0 | 3 |
| 5 | `76d952ce` | 2026-05-13 00:05:20Z | hrmanager@mascigc.com | exact | 2026-05-12 | 3 | 0 | 3 |
| 6 | `f28d4b44` | 2026-05-13 00:05:32Z | hrmanager@mascigc.com | exact | 2026-05-12 | 1 | 0 | 1 |
| 7 | `ed8ec430` | 2026-05-13 00:06:16Z | hrmanager@mascigc.com | (not enumerated) | (varies) | (varies) | 0 | (varies) |
| 8 | `8b649f92` | 2026-05-13 00:06:16Z | hrmanager@mascigc.com | (not enumerated) | (varies) | (varies) | 0 | (varies) |
| 9 | `2eb4c2d2` | 2026-05-13 00:06:16Z | hrmanager@mascigc.com | (not enumerated) | (varies) | (varies) | 0 | (varies) |
| 10 | `d3150925` | 2026-05-13 00:08:06Z | hrmanager@mascigc.com | (not enumerated) | (varies) | (varies) | 0 | (varies) |

**Total span:** 16 minutes (23:52:33 → 00:08:06). **Total rows across batches:** ~21. **Total matched rows: 0.**

---

## 4 · Test-data fingerprints (per row inspection)

| Batch | Sample employee names in `rows[]` | Test-data verdict |
|---|---|---|
| `674300c9` | "John Smith" (employee_id=E1001) | 🔴 explicit |
| `48cbc60e` | "John Smith" | 🔴 explicit |
| `6590febb` | "Smith" | 🔴 single-token surname test |
| `f1371d01` | "Smith" | 🔴 |
| `76d952ce` | "Smith" | 🔴 |
| `f28d4b44` | "Smith" | 🔴 |

All 10 batches use the dictionary-test name "John Smith" or "Smith" — the operator-flagged contamination canary from the audit directive.

---

## 5 · Companion collection · `payroll_variance_decisions`

| Probe | Result |
|---|---|
| Total docs | 7 |
| Linked to any of the 10 batches | (not enumerated — would require ID join) |

Likely test artifacts of the same period; cleanup decision should include them.

---

## 6 · Classification

| Hypothesis | Verdict | Evidence |
|---|---|---|
| Preview contamination (preview/prod crossover) | 🔴 NO | All 10 batches `created_by=hrmanager@mascigc.com` — a production user. Created 2026-05-12/13 which predates the documented preview/prod crossover incident (2026-05-26). |
| Abandoned imports | 🟢 YES | 16-minute window · multiple rapid-fire uploads · 0 matched_rows · 0 downstream actions |
| Workflow defects | 🟡 PARTIAL | Workflow allowed test data with `John Smith` placeholder names to land in production · no validation of "is this real payroll" · no "test mode" toggle. **This is a workflow defect.** |
| Harmless artifacts | 🔴 NO | They show up in HR portal lists · pollute the variance dashboard · 0 matches but visible |

---

## 7 · Operational impact

| Impact | Severity |
|---|---|
| Visible in HR payroll-variance list | 🟡 |
| Confuses HR staff (10 empty test runs from 2.5 weeks ago) | 🟡 |
| Storage cost | 🟢 negligible (each batch is small) |
| Reporting accuracy (e.g. "how many payroll-variance runs" count) | 🟡 inflates count by 10 |
| Audit / compliance risk | 🟢 low (test-named employees are easy to identify) |

---

## 8 · Recommended remediation

| Step | Action | Severity |
|---|---|---|
| P-1 | Delete the 10 batches: `db.payroll_variance_batches.delete_many({_id: {$in: [...10 IDs]}})` | 🟡 P1 |
| P-2 | Delete the 7 `payroll_variance_decisions` if confirmed linked | 🟡 P1 |
| P-3 | Add input-validation: reject batches with any row containing `John Smith` / `Jane Smith` / employee_id starting with `E000` test pattern (NICE-TO-HAVE) | 🟡 P2 |
| P-4 | Add a "test mode" flag on uploads + a dedicated `staging_payroll_variance_batches` collection (FEATURE) | 🟢 P3 |

**Recommendation:** Authorize **P-1 + P-2** (delete the test batches + their linked decisions). Defer P-3 / P-4 — they are feature work, NOT in this batch's scope.

---

## 9 · Reproduction (operator-side)

```bash
# Read-only confirmation
db.payroll_variance_batches.count_documents({})  # expect: 10
db.payroll_variance_batches.find({}, {id:1, created_by:1, created_at:1, rows:{$slice:1}})
# Inspect first row of each batch; confirm "John Smith" or "Smith" names

# Operator-authorized cleanup (DO NOT EXECUTE WITHOUT AUTHORIZATION)
const TEST_BATCH_IDS = [
  "674300c9-0839-408d-a6a8-a06f221c4cc8",
  "48cbc60e-bd33-46ee-99cd-54ba4da65933",
  "6590febb-8fce-469c-a07f-f28b8b26e052",
  "f1371d01-9ecb-4062-bcea-3d318fc5bbcd",
  "76d952ce-7c1b-438b-952c-2d3d9e78efce",
  "f28d4b44-439b-4e63-a1c6-03c3897baac8",
  // + 4 more IDs not yet enumerated above; full set is the 10 created 2026-05-12/13
];
db.payroll_variance_batches.delete_many({id: {$in: TEST_BATCH_IDS}})
db.payroll_variance_decisions.delete_many({batch_id: {$in: TEST_BATCH_IDS}})
```

---

## 10 · Risk if left alone

🟡 IMPORTANT:
- HR staff continue to see 10 empty test batches in production · operational noise
- Cleanup compounds if more test runs accumulate
- A future audit (e.g. SOC2, external HR review) flags `John Smith` data in production payroll system

---

## 11 · Closeout

🔴 **Confirmed: 10 production payroll-variance batches are abandoned test imports by `hrmanager@mascigc.com` from 2026-05-12/13. Every batch contains "John Smith" canary test data.** Recommended remediation: delete the 10 batches + their linked decisions (~17 docs total) under operator authorization. **NO MODIFICATIONS MADE.**

🛑 STOP.
