# WP-15 Enterprise Governance Discovery

**Date:** 2026-07-29  
**Work Package:** WP-15 — Enterprise Governance  
**Status:** Repository discovery complete; implementation authorized to proceed  
**Execution defaults confirmed by user:** 1B, 2B, 3A, 4A, 5A

---

## 1. Discovery Scope

This discovery was performed against the certified Platform Baseline 1.0 before any WP-15 implementation.

Verified inputs:

- `/app/memory/MASCI_OPS_PLATFORM_BASELINE_1_0.md`
- `/app/backend/routes/auth_directory_routes.py`
- `/app/backend/auth.py`
- `/app/backend/pm_auth.py`
- `/app/backend/services/operations_control/registry.py`
- `/app/backend/services/operations_control/control_plane.py`
- `/app/backend/services/operations_control/case_management.py`
- `/app/backend/lib/trust_spine.py`
- `/app/backend/routes/governance.py`
- `/app/backend/routes/governance_health.py`
- `/app/backend/routes/project_identity_governance.py`
- `/app/frontend/src/pages/admin/AdminGovernance.jsx`
- `/app/frontend/src/pages/admin/AdminGovernanceTrust.jsx`
- `/app/frontend/src/pages/admin/AdminProjectIdentityGovernance.jsx`
- `/app/frontend/src/app/routing/AppRoutes.jsx`

Discovery rules used:

- only implemented functionality is treated as implemented
- existing auth remains the canonical identity owner
- existing governance-related routes are treated as adjacent governance/intelligence surfaces, not as the enterprise governance engine requested in WP-15
- unknowns are stated explicitly

---

## 2. Certified Baseline Verification

The following certified baseline elements were verified to exist before WP-15 work begins:

- Platform Baseline 1.0 exists: `/app/memory/MASCI_OPS_PLATFORM_BASELINE_1_0.md`
- Operational Registry exists: `/app/backend/services/operations_control/registry.py`
- Event Catalog exists inside the Operational Registry
- Trust Spine exists: `/app/backend/lib/trust_spine.py`
- Operations Control Plane exists: `/app/backend/services/operations_control/control_plane.py`
- Operational Case Management exists: `/app/backend/services/operations_control/case_management.py`
- OCP admin APIs exist: `/app/backend/routes/operations_control.py`

No repository conflict was found that blocks WP-15 from proceeding as a new shared governance service layered on top of the certified baseline.

---

## 3. Current Authorization Flow

### 3.1 Canonical identity / authentication owners verified

The repository already has multiple authentication surfaces and token styles. The user-approved WP-15 approach is to **reuse the existing authentication and user system as the canonical identity source**, while creating a governance identity projection for policy evaluation.

Verified auth owners:

- **Directory / multi-portal identity owner:** `/app/backend/routes/auth_directory_routes.py`
  - canonical multi-login flow
  - directory session token
  - portal token minting per eligible portal
  - admin-facing directory user management and audit
- **JWT user auth owner:** `/app/backend/auth.py`
  - `db.users`
  - JWT access + refresh for selected surfaces
- **PM auth owner:** `/app/backend/pm_auth.py`
  - per-PM credentials on `db.project_managers`
  - PM scoping helper `compute_pm_scope`

### 3.2 Current enforcement pattern

Authorization is currently **distributed** rather than centrally governed.

Patterns observed:

- route-local dependency gates such as `require_admin`, `require_admin_strict`, PM scope checks, and mixed role guards
- portal-specific token validation and scope computation
- admin-only routes enforced directly in route registration
- PM visibility constrained through `compute_pm_scope`
- some governance-like detection pages are admin-only but are not driven by a central policy engine

### 3.3 Current approval / governance posture

The platform already contains governance-related modules, but they are **not** an enterprise governance engine:

- `routes/governance.py` → compliance contradiction detection and findings management
- `routes/project_identity_governance.py` → project identity drift detection and operator queue
- `routes/governance_health.py` → governance health chip telemetry
- `services/operations_control/governance.py` → OCC governance repair operations

These modules are operational governance / integrity tools, not a centralized identity-policy-approval-delegation-authority engine.

---

## 4. Current Role System

### 4.1 Verified role sources

The repository already contains role-like constructs, but they are not unified under a single enterprise governance registry.

Examples verified:

- directory user portal access lists in `auth_directory_routes.py`
- admin/member/owner roles in `auth.py`
- PM-specific scope and admin bypass logic in `pm_auth.py`
- route-local assumptions like admin / PM / HR / Safety / Dispatch / Field Leadership

### 4.2 Discovery finding

Roles exist, but role semantics are currently spread across auth systems, route gates, and portal token issuance. This creates a clear need for:

- configurable enterprise roles
- governance registry-backed permissions
- explainable policy evaluation separate from authentication

---

## 5. Current Permission Storage / Enforcement

### Verified state

No single canonical, registry-controlled enterprise permission store was verified in the current baseline scope.

Instead, permissions appear to be enforced through:

- role checks in route dependencies
- portal eligibility lists
- PM project scoping logic
- route-specific dependency factories

### Discovery finding

The platform currently has **authorization logic**, but not a reusable **permission registry + policy engine** that every module consumes uniformly.

This is the main gap WP-15 is intended to close.

---

## 6. Current Approval Workflow State

### Verified state

Approval-like workflows exist in specific modules, including:

- Daily Report lifecycle review / closeout flows
- QA/QC and site inspection lifecycle gates
- Monday briefing freeze / approval lineage
- Operational Case closure and verification workflow

### Discovery finding

These approvals are domain workflows, not a canonical reusable approval engine.

WP-15 must provide:

- reusable approval flows
- policy-driven approval requirements
- auditable approval outcomes
- integration with Operations Control Plane communications

---

## 7. Extension Points Verified

The repository already contains strong extension seams that WP-15 can use safely.

### 7.1 Trust Spine extension seam

- canonical event emission functions already exist in `/app/backend/lib/trust_spine.py`
- every governance allow / deny / delegation / override / approval should emit through the Trust Spine rather than a parallel audit system

### 7.2 Operations Control Plane extension seam

- registry-backed workflows, events, communications, and escalations already exist
- approval requests and emergency override notifications should use the existing control-plane communication-intent chain

### 7.3 Operational Case integration seam

- cases already support lifecycle, evidence, communications, and baseline linkage
- critical case closure is a natural first-class policy-enforced action under WP-15

### 7.4 Admin UI domain seam

- `/admin/governance` already exists as a governance-health style page
- dedicated `/admin/governance/*` route family is feasible and aligns with current admin route structure

---

## 8. Duplication Risks

The main duplication risks discovered are:

1. **Auth logic spread across multiple owners**  
   Directory auth, JWT auth, PM auth, and route-local gates can drift if WP-15 tries to replace them instead of projecting from them.

2. **Route-local authorization rules**  
   Many current routes encode direct authorization decisions in dependencies. If left untouched, modules could retain alternate ungoverned authorization paths.

3. **Module-specific approval logic**  
   Existing lifecycle approvals may continue to act independently unless migrated to shared policy and approval evaluation.

4. **Existing governance naming collision**  
   The repo already uses “governance” for compliance health and project identity drift tools. WP-15 must preserve those capabilities while clarifying that Enterprise Governance is the central engine.

5. **UI-only governance temptation**  
   Existing admin pages could invite superficial gating. WP-15 must keep backend enforcement authoritative.

---

## 9. Migration Strategy

### User-approved direction

WP-15 will:

- keep current authentication owners in place
- build a governance identity projection derived from the current identity owners
- centralize governance decisions in a canonical governance engine
- migrate certified core + executive/admin reporting surfaces into centralized governance enforcement in the same release scope

### Recommended migration sequence

1. build governance discovery + architecture documents
2. create governance identity projection derived from current auth / directory / PM sources
3. create governance registry for roles, permissions, policies, approval flows, delegation rules, separation rules, authority levels, emergency override types
4. create centralized governance decision engine
5. create reusable approval framework
6. integrate Trust Spine and OCP communications
7. migrate high-sensitivity certified surfaces first:
   - Operational Case closure / evidence export / baseline actions
   - OCP admin endpoints
   - executive dashboards and briefings
   - Daily Reports edit / close / review actions
   - scheduling and forecast approval actions
8. expand to remaining certified core surfaces in the same governed release
9. expose full `/admin/governance/*` administration domain
10. run regression + independent verification

### Fail-safe rule

If a route cannot yet be fully migrated, it must not retain an ungoverned alternate path by accident. WP-15 implementation must make central governance the authoritative backend decision point for the certified scope before certification is claimed.

---

## 10. Material Architectural Risks Checked

Discovery did **not** reveal any blocker that requires stopping before implementation.

No confirmed blocking evidence found for:

- unsafe auth replacement requirement
- identity-integrity impossibility
- inability to derive governance projection from existing owners
- inability to integrate with Trust Spine
- inability to integrate with Operations Control Plane communications
- risk requiring modification of Platform Baseline 1.0

### Risks to manage during implementation

- avoid creating a second identity source of truth
- avoid mixing authentication and authorization concerns
- avoid breaking current PM/admin route behavior during migration
- avoid leaving executive/admin sensitive surfaces outside the governance boundary
- avoid introducing direct email logic for approvals or overrides

---

## 11. WP-15 Implementation Determination

**Determination:** proceed directly into implementation.

WP-15 should build a new canonical Enterprise Governance Engine that:

- derives governance identity projection from existing auth owners
- centralizes policy, permission, delegation, approval, authority, separation-of-duties, and override decisions
- emits governed Trust Spine events for all governance outcomes
- uses the existing Operations Control Plane communications path for approval and override intents
- governs the certified core plus executive/admin reporting surfaces in the same release scope

---

## 12. Initial WP-15 Deliverables Required Next

1. Enterprise Governance architecture + registry foundation
2. governance identity projection model and sync strategy
3. policy decision engine with explainable allow / deny outcomes
4. configurable roles and permissions
5. approval framework
6. delegation engine
7. separation-of-duties evaluator
8. emergency override workflow with preview-safe OCP communications
9. `/admin/governance/*` UI domain
10. migration of certified core + executive/admin reporting surfaces
11. testing, independent verification, and WP-15 certification
