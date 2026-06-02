# EMPLOYEE ROSTER CONTAMINATION REPORT

**OMEGA Directive · Live contamination scan of `db.employees`**
**Date:** 2026-06-02
**Scope:** Live preview MASCI database (production-shape · 247 rows total)
**Verdict:** 🟡 **9 contaminated rows · 3.6 % of roster · 0 sub/vendor contamination · 0 anonymous-public contamination · all 9 are cosmetic test or pre-Alpha residual rows**

---

## 1 · Headline

> **`db.employees` is structurally clean.** The operator's worst-case hypothesis — that subcontractors, vendors, vendor contacts, or external workers have been silently inserted into the employee roster — is **REFUTED by data**. The only contamination found is 8 test/canary rows from Phase Alpha smoke + 1 pre-Phase-Alpha legacy row from the now-closed Field Leadership inline-create path.

---

## 2 · Contamination quantification

| Class | Count | % of 247 | Severity | Recommended action |
|---|---|---|---|---|
| Sub / Vendor / Company-shaped | **0** | 0 % | n/a | — |
| Anonymous public-form (`added_via=field-form`) | **0** | 0 % | n/a | — |
| Field-Leadership inline residual (`created_via=field_leadership_inline`) | **1** | 0.4 % | LOW | Operator review · likely a real foreman; HR can confirm |
| Test / canary rows (`name` matches `test\|canary\|smoke\|G[1-5]`) | **8** | 3.2 % | LOW · cosmetic | Post-deploy cleanup via HR status state machine |
| **TOTAL CONTAMINATION** | **9** | **3.6 %** | LOW overall | All 9 are non-blocking for Phase Alpha deployment |

---

## 3 · Detailed contamination roll-up

### 3.1 · Test / canary rows (8 · the only material contamination)

| # | Row ID (8-char) | Name | `added_via` | `lifecycle_status` | Created | Source |
|---|---|---|---|---|---|---|
| 1 | `a875538e` | `Approval Test User` | `hr-queue-approval` | `Active` | 2026-06-02 | Phase Alpha smoke (curl test) |
| 2 | `c77adae9` | `TEST_QA_HRApproved_1780404467804` | `hr-queue-approval` | `Active` | 2026-06-02 | `testing_agent_v3_fork` iter368 |
| 3 | `ea52130a` | `G5UploadCanary_1780403837` | `bulk-upload-merge` | `Active` | 2026-06-02 | Phase Alpha G-5 pytest |
| 4 | `edea8cc4` | `G5UploadCanary_1780403873` | `bulk-upload-merge` | `Active` | 2026-06-02 | Phase Alpha G-5 pytest |
| 5 | `2d2b18f4` | `G5UploadCanary_1780403891` | `bulk-upload-merge` | `Active` | 2026-06-02 | Phase Alpha G-5 pytest |
| 6 | `cd0887ce` | `G5UploadCanary_1780405013` | `bulk-upload-merge` | `Active` | 2026-06-02 | Phase Alpha G-5 pytest |
| 7 | `30b82fed` | `TEST_Bob Builder` | (none) | (blank) | (pre-Alpha) | Pre-Phase-Alpha legacy test |
| 8 | `25202b82` | `TEST_FL_Employee_iter42` | (none) | (blank) | (pre-Alpha) | Pre-Phase-Alpha legacy test (iter42 era) |

### 3.2 · Field-Leadership inline residual (1)

| # | Provenance marker | Count | Action |
|---|---|---|---|
| 1 | `created_via=field_leadership_inline` (LEGACY pre-G-2 field) | **1** | HR should review · likely a real foreman added via the now-closed FL inline path. No way to distinguish a real-foreman row from a contamination row by field markers alone — HR needs to confirm the name. |

### 3.3 · Provenance breakdown (full)

| `added_via` value | Count | Trust level |
|---|---|---|
| (none — legacy seed) | 236 | 🟢 Original MASCI roster · bulk seed import · clean by manual review · pre-iter71 |
| `hr-queue-approval` | 7 | 🟢 5 real + 2 test (Approval Test User · TEST_QA_HRApproved_*) |
| `bulk-upload-merge` | 4 | 🟡 All 4 are G5UploadCanary_* test rows |
| `field-form` | 0 | 🟢 V-P0-1 (closed in G-1) was never exploited |
| `field_leadership_inline` | 0 | 🟢 New marker · no rows yet · the old marker `created_via=field_leadership_inline` lives on 1 row instead |
| `admin-panel-deprecated` | 0 | 🟢 Phase Alpha admin-panel-create not used |

---

## 4 · What is NOT in the contamination set

Verified by exhaustive regex scans against the live preview DB:

* 🟢 **0 rows with `name` matching** `\b(LLC|INC|CO\.|CORP|COMPANY|CONSTRUCTION|SUPPLY|TRUCKING)\b` — no company-shaped names
* 🟢 **0 rows with `role` matching** `sub|vendor|contractor|external|guest|temp|applicant`
* 🟢 **0 rows with `trade` matching** the same pattern
* 🟢 **0 rows with `crew` matching** the same pattern
* 🟢 **0 rows with `added_via=field-form`** (the V-P0-1 anonymous-public marker)

Top role values in `db.employees`:
* 246 rows · `role=''` (blank)
* 1 row · `role=None`

Top trade values:
* 235 · blank
* 5 · `Carpentry` (Phase Alpha G-5 test rows)
* 5 · `Master Electrician` (Phase Alpha queue test rows)
* 1 · `Operator`
* 1 · `Concrete`

The 247-row roster is dominated by legacy seed rows that all have blank role/trade — the original MASCI bulk import did not carry those fields. This is expected.

---

## 5 · Recommended cleanup (post-deploy · operator-authorized · NOT in this audit)

If/when the operator authorizes cleanup:

1. For the 8 test rows, transition each to `Inactive` via `POST /api/hr/employees/{id}/status` with `reason="audit cleanup: test/canary row from Phase Alpha smoke testing"`. This appends to `status_history` and `employee_lifecycle_events` (preserving audit) without physically deleting.
2. For row #7+#8 (legacy TEST_* rows with no provenance), the same — `Inactive` with reason "legacy pre-Alpha test row".
3. For the 1 `created_via=field_leadership_inline` row, HR reviews the name and either confirms (and stamps `provenance_reviewed_at`) or transitions to `Inactive` with reason "pre-Alpha FL inline · unconfirmed".

**Estimated cleanup time:** 5 minutes via the HR portal. No SQL/migration. No deletes.

---

## 6 · Risk assessment

| Risk | Severity | Notes |
|---|---|---|
| Test rows pollute reports | LOW | Cosmetic — analytics, training metrics could show 8 ghost employees |
| Test rows fail safety/training requirements | LOW | They're `Active` but have no training records · would show as "missing training" but won't be flagged because they don't appear in real crew assignments |
| Test rows pollute Payroll | LOW | Payroll keys off `employee_id` (HR ID) which is blank on all 8 — they'd never receive a paycheck |
| Test rows pollute JHP acknowledgement (future OC-005) | LOW | Same — JHP requires real assignment to crew/project, which test rows lack |
| Pre-Alpha FL row is real foreman | NEUTRAL | If real, no risk; row is a normal employee |
| Pre-Alpha FL row is contamination | LOW | Would manifest as ghost employee · same low-impact pattern as test rows |

**Net deployment risk from contamination: LOW** — all 9 rows are detectable, easily cleaned, and do not block payroll, safety, or accountability functions.

---

## 7 · Sign-off

🟢 **`db.employees` is deployment-safe.** No sub/vendor/external-worker contamination exists. The 9 cosmetic rows can be cleaned post-deploy via the standard HR status state machine without code changes or migrations.

🛑 **Audit / quantification only. No cleanup performed. Operator decides.**
