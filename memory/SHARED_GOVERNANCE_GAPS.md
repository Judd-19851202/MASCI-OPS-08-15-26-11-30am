# SHARED_GOVERNANCE_GAPS.md
**Initiative:** Platform Governance Convergence — Phase 1
**Iteration:** iter353 · Phase 1
**Generated:** 2026-05-23
**Status:** READ-ONLY · No fixes applied. Every gap below has a Phase 2 priority + risk classification.

This document is the **prioritized backlog** for Phase 2 — Governance Convergence Plan. It enumerates every continuity gap, under-permission, over-permission, and inconsistency discovered during the Phase 1 audit.

---

## Priority key
- **P0** = blocks operational flow today (someone can't do their job)
- **P1** = consistent operational friction (workarounds in place)
- **P2** = future-readiness / architectural debt (no current operational impact)

## Risk key
- 🔴 Compliance / safety / data-integrity risk
- 🟡 Operational friction / workaround in place
- 🔵 Architectural cleanliness only

---

## GAP-001 · HR cannot create/edit safety training records
- **Priority:** P0
- **Risk:** 🔴 Compliance
- **Current:** `POST /api/safety/training-records` gated by `_require_safety_or_admin` — HR token rejected.
- **Ideal (per iter353 operator policy):** HR + Safety shared write authority on `safety_training_records`.
- **Why it matters:** HR is the operational owner of employee accountability. When Safety enters a training cert, HR is blocked from correcting employee linkage, expiration typos, or backfilling certs from external training providers — they must escalate to Safety which slows compliance continuity.
- **Phase 2 fix:** Replace `_require_safety_or_admin` with a new shared gate `require_safety_or_hr_or_admin` (already exists in `routes/safety_portal/_deps.py`, just not applied here). Single 1-line decorator change per endpoint. Audit trail already tracks `actor_role`.
- **Tests required:** HR can POST + PATCH + DELETE a training record; Safety still can; PM/Dsp/Shp still blocked.

## GAP-002 · HR cannot upload/edit safety documents
- **Priority:** P0
- **Risk:** 🔴 Compliance
- **Current:** `POST /api/safety/documents` and `PATCH /api/safety/documents/{id}` gated by safety-or-admin only.
- **Ideal:** HR shared write authority on the document library.
- **Why it matters:** OSHA certs, fit-for-duty docs, qualification certificates — HR often holds the source documents, but currently must hand them to Safety to be uploaded.
- **Phase 2 fix:** Apply `require_safety_or_hr_or_admin` to the document POST/PATCH endpoints. DELETE remains Safety-or-Admin (more conservative — operator policy explicitly listed delete as "decision needed").
- **Tests required:** HR upload + edit succeeds; HR delete returns 403 (pending policy); attribution `created_by_role` lands.

## GAP-003 · HR cannot create/edit PPE issuance + return records
- **Priority:** P1
- **Risk:** 🟡 Operational friction
- **Current:** `safety_forms.py` — equipment issuances + trainings are `_require_safety_or_admin`.
- **Ideal:** HR shared write authority.
- **Why it matters:** PPE accountability bleeds into HR's per-employee accountability profile. HR should be able to record "boots issued" when an employee onboards without routing through Safety.
- **Phase 2 fix:** New shared gate `require_safety_or_hr_or_admin` applied to `routes/safety_forms.py` write endpoints. PDF/read endpoints can remain safety-or-admin or be opened up too.

## GAP-004 · Dispatch cannot view Driver Qualification dashboard
- **Priority:** P1
- **Risk:** 🟡 Operational friction
- **Current:** `/api/hr/driver-qualification/dashboard` gated `require_hr_or_admin`.
- **Ideal:** Dispatch should view-only (read-only) the dashboard. They consume the data — they decide who can haul tonight.
- **Why it matters:** Without DQ visibility, dispatch is making assignments without knowing CDL status, expiration risk, or restrictions. They currently work from a shared paper/Excel list.
- **Phase 2 fix:** Either (a) widen the dashboard gate to `require_hr_or_admin_or_dispatch` (cleanest), OR (b) add a sibling endpoint `/api/dispatch/driver-qualification/dashboard` that proxies the same data with dispatch token + write-blocked.
- **Tests required:** Dispatch token returns dashboard data; cannot PATCH employee CDL fields.

## GAP-005 · Field Leadership cannot view DQ dashboard
- **Priority:** P1
- **Risk:** 🟡 Operational friction
- **Current:** FL token returns 403 on `/api/hr/driver-qualification/dashboard`.
- **Ideal:** FL view-only — supervisors of drivers should see their direct reports' CDL status.
- **Why it matters:** FL is the operational chain between drivers and HR. They observe expirations in real-time and route them back through the system.
- **Phase 2 fix:** Same as GAP-004 — add FL token to dashboard read gate. Scoped query to only return FL's direct reports (filter by `supervisor` field on employees collection).

## GAP-006 · PM cannot view crew CDL status
- **Priority:** P2
- **Risk:** 🔵 Architectural
- **Current:** No PM-facing CDL surface.
- **Ideal:** PM read-only filter on `/api/employees?cdl_only=true&crew=mine`.
- **Why it matters:** PMs assigning hauling tasks (tanker/dump truck/material delivery) should see CDL endorsements + status without leaving their portal.
- **Phase 2 fix:** Lower priority — most PMs route through Dispatch. Address after Dispatch/FL visibility lands.

## GAP-007 · QA/QC has NO dedicated write authority
- **Priority:** P1
- **Risk:** 🟡 Operational friction
- **Current:** QA/QC inspections gated by `require_any_portal_token` — ANY signed-in user can write QA/QC. Effectively unconstrained.
- **Ideal:** Dedicated `require_qaqc_user` for QA/QC mutations; reads remain open.
- **Why it matters:** No enforcement → no accountability for inspection authorship. Anyone could backdate or alter inspection records.
- **Phase 2 fix:** Add `db.qaqc_users` collection (mirror of `hr_users`/`safety_users` pattern). Add `require_qaqc_or_admin` gate. Apply to `routes/qaqc.py` write endpoints. Backfill existing inspections with the most recent token's actor.

## GAP-008 · Duplicated admin-gate implementations
- **Priority:** P2
- **Risk:** 🔵 Architectural drift
- **Current:** `require_admin`, `require_admin_dep`, `require_admin_async`, `require_admin_strict`, `require_admin_strict_dep` — 5 admin-gate variants, only 2 semantically distinct.
- **Ideal:** Two gates: `require_admin` and `require_admin_strict` (step-up). Everything else is an alias.
- **Why it matters:** Drift risk. Each variant currently has its own implementation that could diverge over time.
- **Phase 2 fix:** Refactor to two canonical gates + delete aliases. Tests would catch any caller-site regression.

## GAP-009 · Inline gate redefinition
- **Priority:** P2
- **Risk:** 🔵 Architectural
- **Current:** `routes/employee_lifecycle.py:760` and `routes/field_leadership_portal.py:134` both define a local `require_hr_or_admin`. Same logic, two implementations.
- **Ideal:** Single canonical `require_hr_or_admin` in `lib/rbac_gates.py` (new module), imported everywhere.
- **Why it matters:** Drift risk — if HR-or-Admin policy changes, both must be updated.
- **Phase 2 fix:** Create `lib/rbac_gates.py` with all role-combination gates as composable functions. Migrate all call sites.

## GAP-010 · Three Safety-can-touch-this gates
- **Priority:** P2
- **Risk:** 🔵 Architectural
- **Current:** `_require_safety_or_admin` (safety_forms.py), `make_require_safety_or_hr_or_admin` (safety_portal/_deps.py), `require_safety_token` (fire_ext_bulk_import.py).
- **Ideal:** One canonical `require_safety_or_admin` and one `require_safety_or_hr_or_admin`. Token-only gates for narrow public APIs.
- **Why it matters:** Same as GAP-008 — drift risk.
- **Phase 2 fix:** Consolidate into `lib/rbac_gates.py`.

## GAP-011 · `require_write` in operations.py is undocumented
- **Priority:** P2
- **Risk:** 🟡 (low) — opacity risk
- **Current:** 10 routes use `require_write` but the gate has no docstring describing which roles qualify.
- **Ideal:** Documented + role-restrictive.
- **Phase 2 fix:** Read `routes/operations.py:require_write` definition, document, and verify scope matches intent.

## GAP-012 · Field Leadership has TWO auth paths
- **Priority:** P2
- **Risk:** 🔵 Architectural
- **Current:** `db.field_leadership_users` (native FL accounts · iter348) + a shared-password "leadership token" via `field_leadership.py:_check_leadership_token` (legacy).
- **Ideal:** Native FL users only. Sunset the shared-password path.
- **Phase 2 fix:** Audit usage of shared-password token, migrate any remaining users to native accounts, then remove `_check_leadership_token`.

## GAP-013 · No HR-facing employee bulk import UI
- **Priority:** P1
- **Risk:** 🟡 Operational friction
- **Current:** `/api/exports/employees` exists (admin only) — no import. The CSV-based DQ importer (iter352) only updates driver fields on EXISTING employees.
- **Ideal:** HR-facing bulk import wizard for new-hires (same UX pattern as iter352 — preview, match-or-create, apply, audit).
- **Phase 2 fix:** Generalize the iter352 importer pattern into a reusable `lib/roster_importer.py` and instantiate it for employee onboarding.

## GAP-014 · No unified employee accountability timeline
- **Priority:** P0 (architectural)
- **Risk:** 🔴 Compliance — siloed records
- **Current:** Employee data lives in: `employees`, `safety_training_records`, `safety_documents`, `safety_equipment_issuances`, `safety_equipment_trainings`, `training_track_records`, `incidents`, `daily_reports` (refs), `tasks`, `field_leadership_records`, `driver_qualification_imports`. No unified per-employee timeline view.
- **Ideal:** One canonical `/api/hr/employees/{id}/accountability` that returns ALL accountability events chronologically. Already partially exists (iter350 `/api/hr/employee-accountability?employee=NAME`) — needs to UNION more collections.
- **Phase 2 fix:** Detailed proposal in `EMPLOYEE_ACCOUNTABILITY_ARCHITECTURE.md`.

## GAP-015 · `created_by_role` is inconsistently captured
- **Priority:** P1
- **Risk:** 🔴 Audit gap
- **Current:** Some collections capture `created_by` (email only); others capture `created_by_name`; very few capture `created_by_role`. iter352 driver_qualification_imports DOES capture role.
- **Ideal:** Every mutation records `{actor, actor_role, ts, originating_portal}`.
- **Phase 2 fix:** Add `actor_role` to all write paths via a shared `audit.write_log` helper. Backfill is impossible for historical records; mark them `actor_role: "legacy"`.

## GAP-016 · No "soft delete" policy
- **Priority:** P2
- **Risk:** 🔵 Architectural
- **Current:** Some collections have `deleted_at`, some have `is_active`, some just hard-delete (HR employees: soft via `is_active`; safety documents: hard DELETE; tasks: hard).
- **Ideal:** Unified soft-delete pattern with `deleted_at: ISO` + `deleted_by` + `deleted_by_role`. Hard-delete only via admin step-up.
- **Phase 2 fix:** Codify policy in `lib/soft_delete.py`. Migrate hard-delete sites.

## GAP-017 · No expiration-monitoring service
- **Priority:** P1 (revenue-protective)
- **Risk:** 🔴 Compliance
- **Current:** Dashboards SHOW expiring records but no daily push notification, no executive email digest, no DOT/insurance export packet.
- **Ideal:** Daily job that:
  - Finds all docs/certs/CDL/medical-card records expiring in 30/60/90 days
  - Routes alerts to record owner (HR for HR-curriculums, Safety for safety certs, Dispatch+HR for CDL)
  - Generates monthly insurance export packet
- **Phase 2 fix:** New `services/expiration_monitor.py` cron + dedicated `expiration_alerts` collection.

## GAP-018 · Production has no MFA on super-admin
- **Priority:** P1
- **Risk:** 🔴 Security
- **Current:** Super-admin can login with email+password and get all 7 portal tokens immediately. Step-up MFA exists in `admin_hardening.py` but only triggers on specific surfaces (backups, audit deletion).
- **Ideal:** MFA on every super-admin session (TOTP or magic-link).
- **Phase 2 fix:** Extend step-up to the multi-login flow itself, OR enroll super-admin in mandatory TOTP.

## GAP-019 · No portal-grant audit trail
- **Priority:** P1
- **Risk:** 🔴 Audit
- **Current:** When admin adds a Safety user, the row lands in `db.safety_users` but no entry is written to `admin_audit_log` describing the grant.
- **Ideal:** Every portal-user create/edit/delete writes to `admin_audit_log`.
- **Phase 2 fix:** Wrap `db.*_users.insert_one/update_one/delete_one` calls in `auth_directory_routes.py` with `audit.write_log` calls.

## GAP-020 · Public defect submission has no rate limit
- **Priority:** P2
- **Risk:** 🟡 Abuse
- **Current:** `POST /api/fleet/defects` accepts anonymous submissions via `require_signed_in_or_public`.
- **Ideal:** Rate-limit by IP + reCAPTCHA-style challenge.
- **Phase 2 fix:** Add rate-limit middleware on `/api/fleet/defects` only (public attack surface).

---

## Aggregate Phase 2 work breakdown

| Phase 2 work item | Gaps closed | Priority |
|---|---|---|
| iter353a — Apply `require_safety_or_hr_or_admin` to training-records, safety-documents, equipment-issuances write paths + UI | GAP-001 · GAP-002 · GAP-003 | P0 |
| iter353b — Add Dispatch + FL view-only DQ dashboard gates | GAP-004 · GAP-005 | P1 |
| iter353c — Unified employee accountability timeline endpoint + page | GAP-014 | P0 |
| iter354 — Consolidate auth gates into `lib/rbac_gates.py` | GAP-008 · GAP-009 · GAP-010 · GAP-011 · GAP-012 | P2 |
| iter355 — QA/QC dedicated auth | GAP-007 | P1 |
| iter356 — Expiration monitoring + insurance export packet | GAP-017 | P1 |
| iter357 — Super-admin MFA + portal-grant audit trail | GAP-018 · GAP-019 | P1 |
| iter358 — Soft-delete policy + audit-role consistency | GAP-015 · GAP-016 | P2 |
| iter359 — HR employee bulk import (generalize iter352 pattern) | GAP-013 | P1 |
| iter360 — PM crew CDL visibility · rate limits | GAP-006 · GAP-020 | P2 |

---

## See also
- `PLATFORM_RBAC_AUDIT.md` — route enumeration this draws from
- `PLATFORM_OWNERSHIP_MATRIX.md` — per-system grant matrix
- `EMPLOYEE_ACCOUNTABILITY_ARCHITECTURE.md` — GAP-014 deep dive
- `AUTH_AND_PORTAL_GOVERNANCE.md` — GAP-008/009/010/012/018 deep dive
