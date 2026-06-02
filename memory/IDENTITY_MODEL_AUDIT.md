# IDENTITY MODEL AUDIT · Canonical Identity Classes

**OMEGA Directive · Identity Model design (no code)**
**Date:** 2026-06-02
**Mode:** Design-only · companion to `SUB_VENDOR_IDENTITY_AUDIT.md`

---

## 1 · Canonical identity classes (proposed · 7 classes)

Each class defined by **source of truth · lifecycle owner · creation authority · modification authority · deletion authority**.

### 1.1 · Employee

* **Definition:** A natural person on MASCI's W-2 payroll. Active or temporarily inactive (`On Leave`, `Pending Hire`). Subject to MASCI's HR policies, accountability framework, and training requirements.
* **Source of truth:** `db.employees`
* **Lifecycle owner:** **HR** (per Phase Alpha)
* **Creation authority:** HR (via `POST /api/hr/employees`, queue approval, driver-qual import, canonical bulk upload)
* **Modification authority:** HR (via `PATCH /api/hr/employees/{id}`, status state machine)
* **Deletion authority:** **NONE via API** — terminations transition `lifecycle_status` only. Console-only physical delete for compliance scrubs (super-admin).

### 1.2 · Former Employee

* **Definition:** A person whose Employee lifecycle has terminated (`Terminated`, `Resigned`, `Retired`). May be rehired by HR (transitions back to Employee).
* **Source of truth:** `db.employees` with `lifecycle_status ∈ {Terminated, Resigned, Retired}` · `is_active=false` · `termination_date` set
* **Lifecycle owner:** HR
* **Creation authority:** HR (via status transition from Employee · never created directly)
* **Modification authority:** HR (most fields write-once after termination; `rehire_eligibility` and `rehire_eligibility_reason` HR-editable)
* **Deletion authority:** NONE via API. Retain indefinitely (audit + rehire-eligibility chain depends on history).

### 1.3 · Applicant (NEW · not yet modelled)

* **Definition:** A natural person who has SUBMITTED interest in working at MASCI but has not yet been hired. NOT on payroll. NOT subject to training requirements. NOT visible on safety/PM/dispatch rosters.
* **Source of truth:** **(NEW) `db.applicants`** (proposed — does not exist today)
* **Lifecycle owner:** HR
* **Creation authority:** HR (via canonical create) OR public via captcha-gated career form (rate-limited · always lands as `pending_review`)
* **Modification authority:** HR (move to `hired` → spawns `db.employees` row · or move to `rejected` / `withdrawn`)
* **Deletion authority:** HR after retention period (e.g. 12 months for unhired applicants per EEOC norms)
* **Transition to Employee:** HR explicit promote action only. Once promoted, the applicant row is preserved as the audit trail; the new `db.employees` row carries `applicant_id_origin` FK for traceability.

### 1.4 · Field Leader (CURRENT state · needs reconciliation)

* **Definition:** A natural person with elevated field authority (Foreman · Field Supervisor · Working Supervisor · Superintendent). Today modelled as a portal-login mirror in `db.field_leadership_users` AND (separately) as a row in `db.employees`.
* **Source of truth (TODAY):** **AMBIGUOUS** — `db.field_leadership_users` has 24 FL rows with `employee_id=''` (no FK to employees).
* **Source of truth (PROPOSED):** `db.employees` is the canonical identity; `db.field_leadership_users` is a *role grant* on top of that identity, indexed by `employee_id` FK.
* **Lifecycle owner:** HR (employee identity) · Admin (FL role grant) — proposed split
* **Creation authority:** Admin grants FL role; cannot create the underlying employee
* **Modification authority:** HR (employee fields) · Admin (FL role attributes: portal access, role label)
* **Deletion authority:** Admin (revoke FL role) · HR (terminate underlying employee · cascades to FL role)

### 1.5 · Subcontractor (current `db.suppliers`)

* **Definition:** A **company** (legal entity) contracted by MASCI to perform work. NOT a natural person. Multiple individual workers may belong to a subcontractor.
* **Source of truth:** `db.suppliers` (today is the union of Subcontractors + Vendors · `vendor_type` field exists but unused)
* **Lifecycle owner (PROPOSED):** **Procurement / PM** (NOT HR — HR governs natural persons; subs are corporate entities)
* **Creation authority (PROPOSED):** Procurement-or-PM via canonical create endpoint (mirrored Phase Alpha pattern)
* **Modification authority:** Procurement-or-PM
* **Deletion authority:** NONE via API · lifecycle transition (`Active` → `Inactive` / `Terminated`)
* **TODAY:** PUBLIC `/api/suppliers/add` + admin destructive upload (5 P0 violations · see audit §2.4)

### 1.6 · Vendor (current `db.suppliers` with `vendor_type="vendor"`)

* **Definition:** A **company** that supplies goods/materials but does NOT perform field labor under MASCI's safety umbrella.
* **Source of truth (PROPOSED):** Same `db.suppliers` collection with `vendor_type="vendor"` to disambiguate from `vendor_type="subcontractor"`.
* **Lifecycle owner:** Procurement
* **Creation authority:** Procurement
* **Modification authority:** Procurement
* **Deletion authority:** NONE via API · lifecycle transition only

### 1.7 · Vendor Contact (NEW · not yet modelled)

* **Definition:** A natural person who is a point-of-contact at a Vendor or Subcontractor. NOT a MASCI employee. May receive emails, sign documents on behalf of their company, etc.
* **Source of truth:** **(NEW) `db.vendor_contacts`** (proposed — does not exist today)
* **Lifecycle owner:** Procurement
* **Creation authority:** Procurement (via canonical create)
* **Modification authority:** Procurement
* **Deletion authority:** Procurement (soft-delete with retention)
* **FK:** `supplier_id` FK to `db.suppliers.id`. One vendor may have many contacts. A contact may move between vendors over time (HR-style history).

### 1.8 · External Worker (NEW · not yet modelled)

* **Definition:** A natural person employed by a Subcontractor who is on a MASCI job site. NOT on MASCI payroll. NOT subject to MASCI training requirements (their subcontractor governs training). MAY be subject to MASCI's safety umbrella (site-wide JHP acknowledgement, safety briefings).
* **Source of truth:** **(NEW) `db.external_workers`** (proposed — does not exist today)
* **Lifecycle owner:** Procurement OR Safety (operator decision required)
* **Creation authority:** Procurement-or-Safety (via canonical create)
* **Modification authority:** Procurement-or-Safety
* **Deletion authority:** Procurement-or-Safety (soft-delete)
* **FK:** `supplier_id` FK to `db.suppliers.id`. One subcontractor has many external workers.

---

## 2 · Authority matrix (consolidated)

| Class | Source of Truth | Lifecycle Owner | Create | Modify | Delete |
|---|---|---|---|---|---|
| **Employee** | `db.employees` | HR | HR | HR | NONE (status only) |
| **Former Employee** | `db.employees` (terminated states) | HR | HR (via transition) | HR (limited fields) | NONE |
| **Applicant** | `db.applicants` (NEW) | HR | HR or public career-form | HR | HR (post-retention) |
| **Field Leader** | `db.employees` + `db.field_leadership_users` role-grant | HR (identity) + Admin (role) | Admin grants on existing employee | HR (identity) + Admin (role) | Admin (revoke role); HR (terminate person) |
| **Subcontractor** | `db.suppliers` (`vendor_type="subcontractor"`) | Procurement / PM | Procurement / PM | Procurement / PM | NONE (status only) |
| **Vendor** | `db.suppliers` (`vendor_type="vendor"`) | Procurement | Procurement | Procurement | NONE (status only) |
| **Vendor Contact** | `db.vendor_contacts` (NEW) | Procurement | Procurement | Procurement | Procurement (soft) |
| **External Worker** | `db.external_workers` (NEW) | Procurement-or-Safety | Procurement-or-Safety | Procurement-or-Safety | Procurement-or-Safety (soft) |

---

## 3 · Cross-class relationships (proposed FK schema)

```
db.employees ─────────────────────────────────────────────────┐
   id (uuid, primary)                                          │
   manager_employee_id  ──► db.employees.id  (Ownership Layer A)
   applicant_id_origin  ──► db.applicants.id (audit trail)
                                                                │
db.applicants                                                   │
   id, status: pending_review|hired|rejected|withdrawn          │
   resulting_employee_id ──► db.employees.id (on hire)          │
                                                                │
db.field_leadership_users                                       │
   employee_id  ──► db.employees.id  (NEW · required FK)        │
   role: Foreman|Field Supervisor|Working Supervisor|Superintendent
                                                                │
db.user_directory + db.hr_users + db.shop_users + db.dispatch_users + db.project_managers
   employee_id (Optional) ──► db.employees.id                   │
   (NULL for external auth principals like admin-only accounts) │
                                                                │
db.suppliers                                                     ◄──┐
   id (uuid, primary)                                              │
   vendor_type: subcontractor | vendor | both                      │
   lifecycle_status, status_history, etc. (mirrored from employee) │
                                                                   │
db.vendor_contacts                                                 │
   id, supplier_id  ──► db.suppliers.id                            │
                                                                   │
db.external_workers                                                │
   id, supplier_id  ──► db.suppliers.id                          ──┘
```

---

## 4 · Decision points for operator (5)

1. **Subcontractor lifecycle owner** — HR (single-source-of-truth pure) or Procurement/PM (correct domain expertise)?
2. **External Worker lifecycle owner** — Procurement (corporate-affiliation FK) or Safety (because they're under the safety umbrella)?
3. **Applicant collection** — build now (P1, foundational for clean hiring) or defer until first workflow needs it?
4. **Vendor Contact collection** — build now (P1) or defer?
5. **Phase Beta sequencing** — close suppliers governance (Sub/Vendor Phase Alpha) BEFORE or AFTER reconciling parallel people collections?

---

## 5 · Constitutional fit

| Test | Verdict |
|---|---|
| Single source of truth per identity class | ✅ Each class has exactly one canonical collection |
| Authority cleanly partitioned | ✅ HR governs natural persons employed by MASCI; Procurement governs companies + external persons; Safety governs site umbrella |
| No silent state-machine bypass | ✅ Every class has explicit `lifecycle_status` + `status_history` + audit ledger (mirrored from Phase Alpha pattern) |
| Reduce-work-vs-create-work | ✅ Each class has at most one canonical create surface · no parallel self-service paths |
| Friction Rule 6 (Ownership inferred) | ✅ Role-grants (FL portal access, HR role) are inferred from base identity, not field-stamped on the identity itself |
| Build/Integrate/Ignore Doctrine | ✅ Classes are minimum-viable · no speculative classes added |

🛑 **Audit / design only. STOP for operator decisions.**
