# LIVE PRODUCTION · ADMIN CERTIFICATION
## OMEGA Directive · Phase 7 of 10

**Date**: 2026-06-03
**Target**: https://mascidocs.com (production)

---

## 🟡 PHASE 7 VERDICT — OPERATOR WALKTHROUGH REQUIRED

Admin surfaces (HR, Dispatch, Assets, Payroll Variance, Admin Tools) are auth-gated. External probes confirm gating and SPA route loading; full admin functionality requires operator credentials.

---

## 1 · What the agent verified externally

| Probe | Result |
|---|:-:|
| `GET /admin` (SPA fallback) | 🟢 200 |
| `GET /hr-login` (SPA fallback) | 🟢 200 |
| `GET /dispatch-portal` (SPA fallback) | 🟢 200 |
| `GET /api/projects` (anon) | 🟢 401 — correctly gated |
| `GET /api/users` (anon) | 🟢 401 — correctly gated |
| `GET /api/workflow/undo/feed` (anon) | 🟢 404 — not exposed to anon |
| `GET /api/payroll-variance/batches` (anon) | 🟢 404 — not exposed to anon |
| `GET /api/employees` (anon) | ⚠️ 200 with 247-record roster — see `LIVE_PRODUCTION_STABILITY_REVIEW.md` §2 (HIGH, pre-existing, NOT from OKCP deploy) |

---

## 2 · Operator walkthrough checklist (required to complete Phase 7)

Execute on https://mascidocs.com using Tier-1 admin credentials.

### 2.1 · HR
- [ ] Log in to HR portal
- [ ] Employee Lifecycle: open an active employee, verify lifecycle events render
- [ ] Status update: change an employee's status (active → on-leave or equivalent), confirm event logged
- [ ] Visibility: confirm HR-only fields visible to HR, hidden to non-HR

### 2.2 · Dispatch
- [ ] Log in to Dispatch portal
- [ ] Verify dispatch board loads
- [ ] Verify available actions (assign, reassign, cancel) work
- [ ] Confirm shift-start QR flow still functional
- [ ] Confirm fleet RTS visibility for the dispatcher role (per the OKCP scope correction, dispatch role gets fleet.rts coaching)

### 2.3 · Assets / Equipment
- [ ] Open Assets surface
- [ ] Transfer an asset between projects
- [ ] Confirm transfer logged
- [ ] Confirm visibility correct for asset owner role

### 2.4 · Payroll Variance
- [ ] Log in as HR or Admin
- [ ] Open Payroll Variance dashboard
- [ ] Verify batches visible, status transitions visible
- [ ] Open one batch
- [ ] Confirm the 3-attestation gate (HR + Admin + Final) is enforced; no auto-finalize
- [ ] Try to finalize as a non-authorized role → confirm refusal
- [ ] Confirm Payroll Variance coaching tips visible (per OKCP scope: `hr/admin`)

### 2.5 · Admin Tools
- [ ] Admin → Integration Center loads (note pre-existing ESLint warning, not a runtime error)
- [ ] Admin → Operations Events loads
- [ ] Admin → Operational Language (glossary) loads with new terms from OER
- [ ] Admin → Recovery Stream loads
- [ ] Admin → Audit Trail loads with recent events
- [ ] Admin → Asset Profile loads

### 2.6 · Permission boundary checks
- [ ] Log in as HR-only → confirm Dispatch portal route refuses access
- [ ] Log in as Dispatch-only → confirm HR portal route refuses access
- [ ] Log in as Field Leadership → confirm Admin route refuses access

---

## 3 · Acceptance

- All admin surfaces load without 500s.
- Permission boundaries are enforced at the route level AND the data level.
- No admin tool produces a white screen.
- No data leaks across role boundaries.

---

## 4 · Phase 7 outcome

🟡 **OPERATOR WALKTHROUGH REQUIRED** — admin gating confirmed at the network edge; full surface verification requires operator.
