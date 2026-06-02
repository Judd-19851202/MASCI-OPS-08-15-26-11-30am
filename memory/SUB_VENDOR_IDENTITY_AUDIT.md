# SUB / VENDOR IDENTITY GOVERNANCE AUDIT

**OMEGA Directive · P0 audit gating Phase Alpha deployment**
**Mode:** Read-only audit · No code changes · No migrations · No deletes · No cleanup · No deployment
**Date:** 2026-06-02
**Authorization:** `AUTHORIZE SUB/VENDOR IDENTITY GOVERNANCE AUDIT`
**Headline:** 🟡 **NO sub/vendor CONTAMINATION found in `db.employees`** · 🔴 5 P0 governance violations on the parallel `db.suppliers` surface · 🔴 4 parallel "people" collections lack FK to `db.employees` · 8 cosmetic test rows in `db.employees`. **Phase Alpha deployment-safe with caveats.**

---

## 1 · Directive (operator quotation · verbatim)

> "Before deployment, perform a complete identity-governance audit to determine whether subcontractors, vendors, vendor contacts, or external workers are contaminating the employee system. Identify every route that creates: Employee · Applicant · Field Leader · Subcontractor · Vendor · Vendor Contact · External Worker. Identify every collection those routes write to. Determine whether any non-employee records exist in db.employees. Quantify contamination."

---

## 2 · Inventory of identity-creating routes (exhaustive)

Compiled by grepping `routes/`, `lib/`, and `server.py` for every `insert_one`, `insert_many`, `update_one`, `replace_one`, `delete_many` against identity-bearing collections.

### 2.1 · Employee creation routes (post-Phase-Alpha state)

| # | Route | Target | Gate | Phase Alpha closure |
|---|---|---|---|---|
| 1 | `POST /api/employees/add` | `db.employees` | PUBLIC (rate-limited) | **CLOSED · returns 410** (G-1) |
| 2 | `POST /api/field-leadership/employees` | `db.employee_requests` (was `db.employees`) | FL token | **CLOSED · enqueues, doesn't write** (G-2) |
| 3 | `POST /api/admin/employees` | `db.employees` (canonical shape) | HR-or-Admin | Phase Alpha tightened (G-3) |
| 4 | `POST /api/admin/employees/upload` | `db.employees` (append/merge) | HR-or-Admin | Phase Alpha rewritten (G-5) |
| 5 | `POST /api/hr/employees` | `db.employees` (canonical) | HR-or-Admin | Pre-Alpha · the HR Portal create |
| 6 | `POST /api/hr/employee-requests/{rid}/approve` (`kind=new_hire`) | `db.employees` + `db.employee_lifecycle_events` | HR-or-Admin | Phase Alpha new |
| 7 | `POST /api/hr/driver-qualification/import/apply` with `create_unmatched=true` | `db.employees` | HR-or-Admin | Pre-Alpha · funnels through skeleton-row constructor |
| 8 | Boot-time seed (`server.py` employee bootstrap) | `db.employees` | System | Idempotent · runs once on empty collection |
| 9 | `scripts/iter311_apply_backfill.py` | `db.employees` | Operator-run shell | One-off ops script |

### 2.2 · Applicant creation routes

| # | Route | Target collection | Gate |
|---|---|---|---|
| — | **NONE** | n/a | n/a |

**Finding:** No "Applicant" identity is modelled today. Driver-qualification import has a `create_unmatched=true` flag that can create skeleton employee rows from inbound data, but those rows enter `db.employees` directly as `lifecycle_status: "Active"` — they are NOT classified as applicants.

### 2.3 · Field Leader creation routes

| # | Route | Target collection | Gate |
|---|---|---|---|
| 1 | `seed_field_leadership_users(db)` at boot | `db.field_leadership_users` | System · idempotent |
| 2 | Admin HR-side `POST /api/hr/field-leadership-users` (if present) | `db.field_leadership_users` | HR / Admin |

**Critical observation:** `db.field_leadership_users` holds **24 rows** (foremen, field supervisors, working supervisors) with `employee_id=''` on every single row. **No FK to `db.employees` exists.** A foreman in `db.employees` and the same person in `db.field_leadership_users` are two unrelated records sharing only a name.

### 2.4 · Subcontractor creation routes

| # | Route | Target collection | Gate |
|---|---|---|---|
| 1 | `POST /api/suppliers/add` | `db.suppliers` | **PUBLIC** (rate-limited) |
| 2 | `POST /api/admin/suppliers` | `db.suppliers` | Admin-only |
| 3 | `PUT /api/admin/suppliers/{id}` | `db.suppliers` | Admin-only |
| 4 | `DELETE /api/admin/suppliers/{id}` | `db.suppliers` (soft-delete) | Admin-only |
| 5 | `POST /api/admin/suppliers/{id}/restore` | `db.suppliers` | Admin-only |
| 6 | `POST /api/admin/suppliers/upload` | `db.suppliers` (`delete_many({})` + insert_many · DESTRUCTIVE) | Admin-only |
| 7 | Boot-time seed (no-op if collection has rows) | `db.suppliers` | System |
| 8 | `scripts/legacy_imports/...` (one-off ops scripts) | `db.suppliers` | Operator-run shell |

**Finding:** `db.suppliers` has the SAME 5 P0 violations as `db.employees` had pre-Phase-Alpha:
- 🔴 V-SUB-1 · Public anonymous create endpoint (V-P0-1 mirror)
- 🔴 V-SUB-2 · Admin lifecycle parity (V-P0-3 mirror)
- 🔴 V-SUB-3 · Destructive `delete_many({})` upload (V-P0-5 mirror)
- 🔴 V-SUB-4 · No append/merge upload semantics (V-P0-5 mirror)
- 🔴 V-SUB-5 · No lifecycle state machine · no `lifecycle_status` · no `status_history` · `is_active` is the only signal · no audit collection

### 2.5 · Vendor creation routes

`db.suppliers` is the union of "Suppliers · Vendors · Subcontractors" — the column `vendor_type` exists but is empty (`""`) on all 145 sampled rows. No separate Vendor collection exists. All routes in §2.4 apply.

### 2.6 · Vendor Contact creation routes

| # | Route | Target collection | Gate |
|---|---|---|---|
| — | **NONE** | n/a | n/a |

**Finding:** No "Vendor Contact" identity is modelled. Vendor sign-in flows store contact emails inline on FL records (`emails_sent_to[]` on `db.field_leadership_records`) but no persistent contact identity exists.

### 2.7 · External Worker creation routes

| # | Route | Target collection | Gate |
|---|---|---|---|
| — | **NONE** | n/a | n/a |

**Finding:** No "External Worker" identity is modelled. The only audit-time reference to "external" is `db.unmapped_external_records` (a side-collection for inbound data that could not be matched to a known identity — read-only consumer surface, not a workforce roster).

---

## 3 · Identity-bearing collections (exhaustive · 9 collections)

| # | Collection | Purpose | Rows (preview) | Writers | Cross-references |
|---|---|---|---|---|---|
| 1 | `db.employees` | Workforce roster · lifecycle authority | **247** | Routes §2.1 (post-Alpha: 8 paths; pre-Alpha: 9 paths) | Referenced by name in payroll, training, JHP, safety, accountability |
| 2 | `db.suppliers` | Subcontractor + vendor master | 145 | Routes §2.4 (8 paths · 5 P0 violations) | Referenced by name in PO requests, daily reports |
| 3 | `db.users` | Legacy "owner/admin" people | 5 | (frozen / boot seed) | NOT cross-referenced to employees |
| 4 | `db.user_directory` | Multi-portal master sign-in | 49 | Admin/Super-admin · login flows | `employee_id` field exists but is `None` on ALL rows |
| 5 | `db.hr_users` | HR portal logins | 42 | HR/Admin | NOT cross-referenced to `db.employees` |
| 6 | `db.shop_users` | Shop portal logins | 3 | Admin | NOT cross-referenced |
| 7 | `db.dispatch_users` | Dispatch portal logins | 2 | Admin | NOT cross-referenced |
| 8 | `db.project_managers` | PM portal logins | 6 | Admin | NOT cross-referenced |
| 9 | `db.field_leadership_users` | FL portal logins / foremen mirror | 24 | HR/Admin via FL portal endpoint | `employee_id=''` on ALL rows |
| 10 | `db.employee_requests` | Phase Alpha queue | 27 | Per Alpha spec · HR-gated approve/reject | Cross-references `db.employees` via `resulting_employee_id` |
| 11 | `db.employee_lifecycle_events` | Phase Alpha audit ledger | 11 | HR write paths · append-only | Indexed on `employee_id` |
| 12 | `db.field_leadership_records` | FL submission records (write-ups, terminations, equipment, etc.) | 32 | FL portal | References employees by name; NOT FK |
| 13 | `db.unmapped_external_records` | Inbound-data parking lot | (varies) | Integration sync flows | Holds rows that could not match an identity |

**Total: 13 identity- or identity-adjacent collections.**

---

## 4 · Contamination scan against `db.employees`

Run against the live preview MASCI database (production-shape, 247 rows total).

### 4.1 · Sub/Vendor/Company-shaped contamination

| Test | Result |
|---|---|
| Rows where `name` matches `\b(LLC\|INC\|CO\.\|CORP\|COMPANY\|CONSTRUCTION\|SUPPLY\|TRUCKING)\b` | **0** |
| Rows where `role` matches `sub\|vendor\|contractor\|external\|guest\|temp\|applicant` | **0** |
| Rows where `trade` matches `sub\|vendor\|contractor\|external\|guest\|temp\|applicant` | **0** |
| Rows where `crew` matches `sub\|vendor\|contractor\|external\|guest\|temp\|applicant` | **0** |

🟢 **`db.employees` is CLEAN of subcontractor / vendor / external-worker contamination.** No company-shaped rows exist.

### 4.2 · Test / canary contamination

| Row ID prefix | Name | `added_via` | `lifecycle_status` | Action recommended |
|---|---|---|---|---|
| `a875538e` | `Approval Test User` | `hr-queue-approval` | `Active` | Operator clean (Phase Alpha smoke) |
| `ea52130a` | `G5UploadCanary_1780403837` | `bulk-upload-merge` | `Active` | Operator clean (Phase Alpha G-5 test) |
| `edea8cc4` | `G5UploadCanary_1780403873` | `bulk-upload-merge` | `Active` | Operator clean |
| `2d2b18f4` | `G5UploadCanary_1780403891` | `bulk-upload-merge` | `Active` | Operator clean |
| `cd0887ce` | `G5UploadCanary_1780405013` | `bulk-upload-merge` | `Active` | Operator clean |
| `30b82fed` | `TEST_Bob Builder` | (none) | (blank) | Pre-Alpha legacy test row |
| `25202b82` | `TEST_FL_Employee_iter42` | (none) | (blank) | Pre-Alpha legacy test row |
| `c77adae9` | `TEST_QA_HRApproved_1780404467804` | `hr-queue-approval` | `Active` | testing_agent_v3_fork iter368 leftover |

**Total: 8 test rows · 3.2 % of the 247-row roster.** All cosmetic. None impact production governance. None are sub/vendor/external. Recommend post-deployment HR-side cleanup via standard `POST /api/hr/employees/{id}/status` (target: Inactive or Terminated with reason "audit cleanup").

### 4.3 · Provenance distribution

| `added_via` value | Count | Provenance |
|---|---|---|
| (none — legacy seed / pre-iter71) | 236 | Original MASCI roster · boot-time bulk import · clean by manual inspection |
| `hr-queue-approval` | 7 | Phase Alpha approval flow + smoke tests |
| `bulk-upload-merge` | 4 | Phase Alpha G-5 test uploads |
| `field-form` | 0 | 🟢 Public anonymous endpoint (V-P0-1) was NEVER abused before closure |
| `field_leadership_inline` | 0 | 🟢 (post-Alpha) — but see §4.4 below |
| `admin-panel-deprecated` | 0 | Phase Alpha admin-create endpoint not used yet |

### 4.4 · Pre-Phase-Alpha residual

| Provenance | Count | Notes |
|---|---|---|
| `created_via=field_leadership_inline` (the LEGACY pre-G-2 field) | **1** | One historical row inserted via the pre-Alpha FL inline create. Now the FL inline path enqueues to HR Queue instead. The historical row is still on the roster but is structurally indistinguishable from a normal employee. HR should review and either confirm or terminate. |

---

## 5 · Quantified contamination summary

| Contamination class | Count | Severity | Blocks Phase Alpha deploy? |
|---|---|---|---|
| Sub/Vendor contamination in `db.employees` | **0** | 🟢 NONE | No |
| Anonymous public-form contamination | **0** | 🟢 NONE | No |
| Operations (FL) self-service residual (`created_via`) | **1** | 🟡 LOW | No |
| Test/canary rows | **8** | 🟡 LOW · cosmetic | No (recommend post-deploy cleanup) |
| Parallel-collection governance gap (suppliers) | **5 P0 violations** | 🔴 P0 | Yes — but only for sub/vendor governance · Phase Alpha is employee-only |
| Parallel-people-collection FK gap (FL users, HR users, etc.) | **5 collections · 0 FKs to employees** | 🔴 STRUCTURAL | No · existing-state, unchanged by Alpha |

---

## 6 · Impact on downstream systems

| System | Risk from contamination | Risk from parallel collections |
|---|---|---|
| **Payroll** | 🟢 None (no sub/vendor in employees) | 🟡 Payroll variance joins by name not FK — fragile but functional |
| **HR roster** | 🟡 8 test rows visible | 🟡 4 parallel people collections (HR portal + FL portal + portal logins) — HR sees one roster only |
| **Training** | 🟢 None | 🟡 Training records reference `db.employees` by name only |
| **JHP acknowledgements** | 🟢 None today (OC-005 not yet built) | 🟡 Future OC-005 must FK to `db.employees`, not name-match across FL/HR users |
| **Safety** | 🟢 None | 🟢 Safety reads `db.employees` only |
| **Accountability** | 🟢 None | 🔴 `manager_employee_id` doesn't exist; FL supervisor relationship lives in a free-text `supervisor` string |
| **Command Center** | 🟢 None | 🟡 Command center widgets read `db.employees` and `db.field_leadership_users` separately |
| **Notifications** | 🟢 None | 🟡 Recipient lookups by name; legitimate-actor identification ambiguous when name appears in multiple collections |
| **Ownership Layer A** | 🟢 None | 🔴 **CRITICAL** — Ownership Layer A must FK `manager_employee_id` to `db.employees.id`. Today the structural reporting chain is a free-text `supervisor` string with no FK. The 24 FL users are NOT cross-referenced to the 247 employees. Layer A cannot ship until this is reconciled. |

---

## 7 · Findings (consolidated)

### 7.1 · The good news (Phase Alpha deploy-safe)

🟢 **`db.employees` is structurally clean of sub/vendor/external-worker contamination.**
🟢 **The G-1 public create endpoint was never abused before closure** — 0 rows with `added_via=field-form`.
🟢 **The G-2 FL inline path inserted only 1 row before closure** (still on the roster as a structurally normal employee; HR can review).
🟢 **Phase Alpha closures hold:** post-Alpha provenance markers (`hr-queue-approval`, `bulk-upload-merge`) are the only fresh inserts.
🟢 **No applicant, external-worker, or vendor-contact contamination exists** because those identity classes are NOT modelled today and no rows were ever shoehorned into employees.

### 7.2 · The bad news (P0 gaps that exist independently of Phase Alpha)

🔴 **`db.suppliers` mirrors the pre-Alpha employee governance violations** verbatim:
   - Public anonymous create
   - Admin-only CRUD with destructive replace-all upload
   - No queue · no lifecycle state machine · no audit ledger

🔴 **4 parallel "people" collections have NO FK to `db.employees`:**
   - `field_leadership_users` (24 foremen) · `employee_id` is `''` everywhere
   - `hr_users` (42) · `shop_users` (3) · `dispatch_users` (2) · `project_managers` (6) · all lack FK
   - `user_directory` (49) has `employee_id` field but it is `None` on every row

🔴 **`db.users` is a legacy "owner/admin" 5-row collection** that nobody writes to anymore but nobody deletes either. Source-of-truth ambiguity for the 5 MASCI principals.

🟡 **No identity classes modelled for:** Applicant · External Worker · Vendor Contact · Subcontractor Employee. If any future workflow needs these (e.g. JHP acknowledgement by a sub's foreman), new collections + governance must be designed.

### 7.3 · Phase Alpha deployment impact

🟢 **Phase Alpha is deployment-safe for employee governance.** The audit confirms that:
1. The 5 P0 closures correctly intercept all employee-create write paths.
2. No contamination from sub/vendor/external workers exists in `db.employees` that could be unmasked by tighter governance.
3. The 8 test rows + 1 pre-Alpha FL row are cosmetic and can be cleaned post-deploy.
4. Phase Alpha does NOT introduce any regression in supplier or parallel-collection governance — those gaps existed pre-Alpha and remain.

🔴 **Phase Alpha is NOT a complete identity-governance solution.** The supplier surface and the parallel people collections remain ungoverned. Phase Beta (or a new Sub/Vendor Phase Alpha) is required before iter454/iter455.1/Ownership Layer A can ship safely.

---

## 8 · Recommendations (informational · no code authorized)

1. **Deploy Phase Alpha as planned.** Employee-side governance is complete and contamination-free. The 5 LOW risks from the prior Risk Report stand.
2. **Authorize an analogous "Sub/Vendor Governance Phase Alpha"** to close the 5 V-SUB violations on `db.suppliers`. Same shape as employee Alpha: public-create lock-down + admin-deprecation + destructive-upload rewrite + queue + audit ledger.
3. **Authorize a "Parallel-People Reconciliation"** batch to introduce the `employee_id` FK from `field_leadership_users`, `hr_users`, `shop_users`, `dispatch_users`, `project_managers`, `user_directory` back to `db.employees`. This is the foundation for Ownership Layer A's `manager_employee_id`.
4. **Authorize cleanup of the 8 test rows** post-deploy via the HR Queue or the canonical HR status state machine.
5. **Decide on identity-class modelling** for Applicant · External Worker · Vendor Contact · Subcontractor Employee before any workflow requires them.

---

## 9 · What this audit did NOT do (scope discipline)

* ❌ No code changes
* ❌ No migrations
* ❌ No deletes
* ❌ No cleanup
* ❌ No deployment
* ❌ No Phase Beta / Ownership Layer A / Accountability Chain / Escalation Framework work

🛑 **Audit complete. Deployment decision deferred to operator per directive.**
