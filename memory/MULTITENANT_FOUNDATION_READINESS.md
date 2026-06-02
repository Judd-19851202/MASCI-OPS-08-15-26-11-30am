# MULTITENANT FOUNDATION READINESS

**Authority**: FOCP MASTER PROGRAM · Phase 14
**Mode**: READ-ONLY · source-direct assessment of tenancy-leakage surface area
**Date verified**: 2026-06-02

---

## Five leak surfaces

The five questions from the directive map to five concrete leak surfaces. For each, I assessed the current codebase against today's single-tenant deployment AND projected forward to a notional Customer #2 + White Label state.

### 1 · Can DATA leak between tenants?

**Today**: **N/A · single-tenant**. The `masci_safety_preview` / `masci_safety` (production) database holds only MASCI data; there is no `customer_id` partition because there is no second customer.

**If multi-tenancy were attempted today**: **YES · DATA WOULD LEAK** — no collection carries a `customer_id` field; no query carries a `customer_id` filter; the auth layer issues tokens with no tenant scope.

**Blockers**:
* Every collection insert site needs `customer_id` injection
* Every query needs `customer_id` filter at the boundary
* Every aggregate / pipeline / report needs tenant-scoped joins

**Estimated effort**: 4 weeks (per Customer #2 Blockers doc) for the partition foundation; further 2 weeks for verification.

### 2 · Can PERMISSIONS leak between tenants?

**Today**: **N/A · single-tenant**.

**If multi-tenancy were attempted today**: **YES** — RBAC is identity-scoped, not tenant-scoped. A user with HR role in tenant A would inherit HR role on collections belonging to tenant B if no `customer_id` filter was applied.

**Blockers**:
* Token claims need `customer_id`
* Role resolution needs `customer_id`
* `RequireSafety` / `RequireHr` / etc. need tenant-aware variants

### 3 · Can OWNERSHIP leak between tenants?

**Today**: **N/A · single-tenant**.

**If multi-tenancy were attempted today**: **YES** — `owner_id`, `assigned_to`, `created_by`, `responsible_employee_id` reference the `employee_master` collection, which is itself unpartitioned. An "owned by" lookup would return employees from any tenant.

**Blockers**:
* `employee_master` needs `customer_id`
* All FK lookups need tenant-scoped joins
* User search needs tenant-scoped filter

### 4 · Can WORKFLOWS leak between tenants?

**Today**: **N/A · single-tenant**.

**If multi-tenancy were attempted today**: **YES** — workflows are not parameterized by tenant. Project lookup, JHP application, JHA-applies-to, dispatch crew assignment all assume a single tenant scope.

**Blockers**:
* Project picker needs tenant filter
* Asset / equipment lookup needs tenant filter
* Cross-workflow signals (e.g., DR completes → notify PM) need tenant boundaries

### 5 · Can AUDIT TRAILS leak between tenants?

**Today**: **N/A · single-tenant**.

**If multi-tenancy were attempted today**: **YES** — `operations_events`, `state_events`, `audit_log` collections are shared and unpartitioned. An admin audit query would see events from any tenant.

**Blockers**:
* All event-stream collections need `customer_id`
* Audit-log query API needs tenant filter (or a fully separate per-tenant audit stream)

## Composite readiness

| Question | Today (1-tenant) | If multi-tenancy attempted now | Effort to fix |
|---|:-:|:-:|---|
| Data leak | n/a | 🔴 YES | 4 weeks |
| Permissions leak | n/a | 🔴 YES | 1 week (depends on data partition) |
| Ownership leak | n/a | 🔴 YES | 1 week (depends on data partition) |
| Workflow leak | n/a | 🔴 YES | 1 week (depends on data partition) |
| Audit leak | n/a | 🔴 YES | 1 week (depends on data partition) |

**Multi-Tenant Foundation Readiness: ~ 15 %** (auth layer carries the most groundwork; data layer requires the most lift).

The 15 % is concentrated in:

* Auth token claims have a stable shape; adding `customer_id` is mechanical
* Audit-log conventions are consistent; adding a partition field is mechanical
* Most collection-write sites flow through a small set of helpers; adding `customer_id` injection at those helpers cascades naturally

The other 85 % is:

* Reading every backend query and ensuring tenant filter
* Reading every aggregation / pipeline / report
* Building tenant-config substrate (SLAs, branding, vocabulary)
* Building tenant onboarding flow
* Building tenant-scoped scheduler
* Auditing every i18n / email / PDF template for tenant cleanliness

## Recommendation

Per `ITER501_CUSTOMER2_BLOCKERS.md` and `ITER501_WHITELABEL_BLOCKERS.md`:

* **Do not** start multi-tenancy work until FOCP Phases 1–13 close.
* **Make explicit Shape A vs Shape B decision** before any multi-tenancy code (Shape A = shared deployment + customer_id partition; Shape B = per-tenant pod).
* Estimated total path to multi-tenant 95 % ready: **~ 9 weeks** of focused engineering AFTER Shape decision AND AFTER FOCP completes.

## Dependency map

```
FOCP Phases 1–13 close
        ↓
Operator Shape A vs Shape B decision
        ↓
Phase 14 multi-tenancy build (~ 9 weeks)
        ↓
Customer #2 pilot ready
        ↓
White Label brand-extension (~ 5 weeks)
        ↓
First White Label tenant pitch
```

---

End of Multi-Tenant Foundation Readiness assessment.
