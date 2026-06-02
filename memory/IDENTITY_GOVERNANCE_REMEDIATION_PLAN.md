# IDENTITY GOVERNANCE REMEDIATION PLAN

**OMEGA Directive · Companion plan to SUB_VENDOR_IDENTITY_AUDIT.md**
**Date:** 2026-06-02
**Mode:** Plan-only · no batch authorized yet · awaits explicit operator decisions
**Sequencing:** Each phase awaits explicit "BUILD" authorization. No batch begins without operator approval.

---

## 1 · Scope of remediation (3 phases · 9 batches)

| Phase | Goal | Batches | Prerequisite |
|---|---|---|---|
| **Phase α-Sub** | Close 5 P0 violations on `db.suppliers` (Sub/Vendor parallel-Alpha) | S-1 · S-2 · S-3 · S-4 · S-5 | Employee Phase Alpha deployed and stable |
| **Phase α-Reconcile** | Add `employee_id` FK on the 5 parallel-people collections | R-1 · R-2 | Phase α-Sub complete |
| **Phase α-NewClasses** | Build Applicant + Vendor Contact + External Worker collections (if operator authorizes) | N-1 · N-2 | Phase α-Reconcile complete; identity-model decisions §1.1–1.5 of IDENTITY_MODEL_AUDIT.md confirmed |

---

## 2 · Phase α-Sub (close `db.suppliers` P0 violations)

Mirrors the Employee Phase Alpha pattern exactly. Operator must confirm sub/vendor lifecycle owner (Procurement vs PM vs Admin) before any batch ships.

### Batch S-1 · Lock `POST /api/suppliers/add`
* Change 1 endpoint (`server.py` lines ~3225–3260): replace body with HTTP 410 + structured pointer to `POST /api/supplier-requests`
* Frontend: repoint any `add to supplier roster` button to the new queue
* Tests: assert 410 + frontend toast "Submitted to Procurement Queue"
* **Size:** ~30 LOC backend · ~30 LOC frontend · 3 unit tests

### Batch S-2 · HR-OR-PROCUREMENT gate on `/api/admin/suppliers*`
* Replace `require_admin` with `_require_procurement_or_admin_for_queue` (new dependency · operator-confirmed gate)
* Mark routes with `X-Deprecated-Endpoint` header
* DELETE returns 405 with pointer to status state machine
* PUT rejects `is_active` toggle (G-4 mirror — needs Sub/Vendor lifecycle_status state machine)
* **Size:** ~70 LOC backend · 6 unit tests

### Batch S-3 · Rewrite `POST /api/admin/suppliers/upload` as append/merge
* Remove `delete_many({})` permanently
* Match by `supplier_id` then case-insensitive name; ambiguous → skipped with reason
* Empty cells DO NOT overwrite
* `lifecycle_status` · `status_history` · `created_at` · `original_engagement_date` (new) preserved
* **Size:** ~150 LOC backend · 5 unit tests

### Batch S-4 · Procurement Request Queue (`db.supplier_requests`)
* Mirror of `db.employee_requests` pattern
* Supports kinds: `new_supplier` · `vendor_type_change` · `termination`
* HR-Procurement-or-Admin review endpoints
* Audit substrate: `audit_log` on request + `status_history` on supplier + new `db.supplier_lifecycle_events`
* **Size:** ~600 LOC backend · ~500 LOC frontend Procurement Queue page · 12 unit tests · 1 frontend testing-agent pass

### Batch S-5 · Supplier lifecycle state machine
* Add `lifecycle_status` to `db.suppliers` (defaults to `Active` for existing 145 rows on first deploy)
* State machine: `Active ⇄ On Hold ⇄ Inactive → Terminated → Banned`
* `POST /api/procurement/suppliers/{id}/status` requires reason ≥5 chars
* `POST /api/procurement/suppliers/{id}/reactivate` requires reason
* Mirrors Phase Alpha employee state machine semantics
* **Size:** ~200 LOC backend · 8 unit tests

**Estimated total Phase α-Sub:** ~1100 LOC backend · ~530 LOC frontend · ~35 tests · 1 frontend cert pass · 1 testing-agent regression on suppliers

---

## 3 · Phase α-Reconcile (parallel-people FK)

### Batch R-1 · Add `employee_id` FK column to parallel collections
* Five collections affected: `field_leadership_users`, `hr_users`, `shop_users`, `dispatch_users`, `project_managers`, `user_directory`
* Add `employee_id: Optional[str]` field on each (already present on `user_directory` and `field_leadership_users`; both are NULL today)
* Backfill script: name + email heuristic match via `lib/employee_linkage.py`
* Idempotent · runs once per collection · audit row per match
* Manual HR resolution for ambiguous matches (queue UI)
* **Size:** ~200 LOC backend + 1 one-off script · ~150 LOC frontend match-reconciliation queue · 8 unit tests

### Batch R-2 · Enforce FK integrity on writes
* `POST /api/hr/field-leadership-users` (and equivalents) require `employee_id` present
* Migration grace period: existing NULL rows allowed for read; new inserts must FK
* HR portal UI shows "unlinked" badge until reconciliation queue clears
* **Size:** ~120 LOC backend · ~100 LOC frontend · 4 unit tests

**Estimated total Phase α-Reconcile:** ~470 LOC + 1 ops script · 12 unit tests

---

## 4 · Phase α-NewClasses (NEW collections if authorized)

### Batch N-1 · `db.applicants` collection + HR Applicant Queue
* Schema: `{ id, name, email, phone, position_applied, source, status: pending_review|interviewing|hired|rejected|withdrawn, applied_at, resulting_employee_id?, ... }`
* Endpoints: `POST /api/applicants` (public via captcha-gated career form) · HR list/approve/reject endpoints
* On hire approval: spawns canonical `db.employees` row with `applicant_id_origin` FK
* **Size:** ~400 LOC backend · ~300 LOC frontend HR Applicant Queue · 10 unit tests
* **Operator decision required:** Build now (P1, foundational) or defer until first workflow needs Applicants?

### Batch N-2 · `db.vendor_contacts` + `db.external_workers`
* Two new collections under Procurement governance
* Endpoints: Procurement-gated CRUD + lifecycle state machine
* FK: `supplier_id` → `db.suppliers.id`
* Distinct cleanly from `db.employees` — these are NEVER on MASCI payroll
* **Size:** ~600 LOC backend · ~400 LOC frontend · 14 unit tests
* **Operator decision required:** Build now or defer? See identity-model audit §1.6–1.8.

---

## 5 · Cross-cutting concerns

| Concern | Mitigation |
|---|---|
| Operator-role ambiguity (Procurement vs PM vs Admin owns subs) | Operator picks ONE role; subagent design conforms |
| Backfill data quality (parallel-people name matches) | Heuristic + manual HR reconciliation queue (Batch R-1 includes this) |
| API surface growth | Each new endpoint follows the same Phase Alpha pattern — gates, audit, state machine, queue if needed |
| Test footprint | Each batch ships its own test file under `/app/backend/tests/test_{batch_slug}.py` |

---

## 6 · Sequencing constraint (binding)

```
Employee Phase Alpha → DEPLOY    ◄── current state (today's verdict 🟢 GO)
   │
   ├──► (optional pause for operator to authorize Sub/Vendor work)
   │
   ▼
Phase α-Sub   (S-1 → S-2 → S-3 → S-4 → S-5)
   │
   ▼
Phase α-Reconcile  (R-1 → R-2)
   │
   ▼
Phase α-NewClasses (N-1 + N-2 · operator decides scope)
   │
   ▼
Ownership Layer A  (introduces manager_employee_id FK · iter455.1)
   │
   ▼
Accountability Chain Status + Escalation Framework + White Label + Customer #2 onboarding
```

Each phase is independently shippable. Phase α-Sub does NOT block Employee Alpha deploy. But Ownership Layer A DOES block on Phase α-Reconcile (because Layer A's `manager_employee_id` FK requires the parallel-people collections to be reconcilable).

---

## 7 · Constitutional / Ownership / Reduce-Work cross-check

| Test | Verdict |
|---|---|
| Friction Rule 5 (Reduce work) | 🟢 PASS · every batch is a "Reduce" move (closes a hole) except S-4 (Procurement Queue) and N-* (new classes). Each new queue offsets one or more self-service surfaces; new classes are gated on operator necessity. |
| Friction Rule 6 (Ownership inferred) | 🟢 PASS · role-grants stay separate from identity |
| Ownership Doctrine O-1, O-3, O-7, O-15 | 🟢 PASS · per-class authority partition · no delegation surface · reopen/reactivate requires reason |
| Build/Integrate/Ignore Doctrine | 🟢 PASS · all batches are "Build" or "Integrate"; nothing is "Ignore" |
| Reduce-Work test | 🟡 Net neutral · 2 new queue surfaces (S-4, N-1) replace existing self-service surfaces; 2 new identity classes (N-2) introduce new surfaces only if operator confirms workflow need |

---

## 8 · Operator decision points (5 · pre-build)

1. **Sub/Vendor lifecycle owner** — Procurement · PM · or Admin? (binding for Phase α-Sub design)
2. **External Worker lifecycle owner** — Procurement (corporate-affiliation) or Safety (site umbrella)?
3. **Phase α-Sub authorization** — start now (before iter454/455.1) or defer?
4. **Applicant collection** — build (N-1) or defer until first workflow needs it?
5. **Vendor Contact + External Worker** — build (N-2) or defer?

---

## 9 · What this plan does NOT do

* ❌ No code changes
* ❌ No migrations
* ❌ No deployment
* ❌ No batch executed
* ❌ No iter454 / iter455.1 / Ownership Layer A / Escalation / White Label work

🛑 **Plan only. Awaiting operator decisions on §8 before any batch is authorized.**
