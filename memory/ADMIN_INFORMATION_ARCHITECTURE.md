# Admin Information Architecture — Phase IV-A

**Iteration:** iter437+ · Phase IV · 2026-02
**Status:** 🟡 GOVERNANCE MAP · NO CODE CHANGES YET
**Scope:** Document-only inventory and target topology. Implementation in subsequent phases.

---

## Current state (organic drift inventory)

The admin shell registers **29 navigation entries** pointing at **57 distinct routes** across **27 admin page components**. Functions are mixed across domains without a governing hierarchy. Sample drift:

| Symptom | Evidence |
|---|---|
| Domain mixing in nav | `system-health` (operations) sits next to `digest-config` (communications) and `audit-log` (governance) |
| Duplicate-purpose entries | `system` (backups) + `system-health` (probes) + `database` (storage) are three separate top-level entries for one domain |
| Cross-portal routes living under `/admin/` | `tasks`, `document-expirations`, `po-requests`, `project-health`, `asset-transfers`, `operational-guidance` |
| Dev-tooling mixed with operator surfaces | `deploy-recovery`, `deploy-readiness`, `legacy-imports`, `operational-inventory`, `governance` |
| Promo/marketing mixed in operational nav | `promo-assets` (cinematic clips) sits next to operational governance |

The sidebar is now 29 entries deep. Cognitive load is too high.

---

## Target state — 10 governed domains

Every admin function MUST belong to exactly one of these domains. No item appears in two domains. No new top-level domains are added without an explicit governance review.

### 1 · Identity & Access
**Purpose:** Who can do what. Authentication, authorization, sessions.
**Current routes to migrate:** `/admin/people`, `/admin/mfa`, `/admin/sessions`, `/admin/audit-log` (filtered to auth events)
**Permissions:** Super-admin · Admin
**Mobile:** Read-only for non-admin · full on iPad
**SLA:** All identity probes < 1s

### 2 · Operations
**Purpose:** Field activity surfaces — daily reports, meetings, production, oversight.
**Current routes to migrate:** `/admin/inspections`, `/admin/meetings`, `/admin/operations-events`, `/admin/project-health`, `/admin/operational-inventory`
**Permissions:** Admin · PM (scoped)
**Mobile:** Full
**SLA:** Read endpoints < 2s

### 3 · Fleet & Equipment
**Purpose:** Asset lifecycle — equipment, fleet health, pre-op, maintenance, GPS.
**Current routes to migrate:** `/admin/equipment`, `/admin/assets/:id`, `/admin/leadership-equipment`, `/admin/equipment/:id/history`, `/admin/jha-plans`, `/admin/trench-boxes`
**Permissions:** Admin · Shop · Dispatch
**Mobile:** Full
**SLA:** Equipment-status read < 1.5s

### 4 · Dispatch & Logistics
**Purpose:** Where the trucks/people are going. Routing, drivers, holds, transfers.
**Current routes to migrate:** `/admin/dispatch`, `/admin/dls/shift-qr`, `/admin/dls/day-1-debrief`, `/admin/dls/week-1-debrief`, `/asset-transfers`
**Permissions:** Admin · Dispatch
**Mobile:** Full
**SLA:** Dispatch board read < 2s · driver magic-link < 500ms

### 5 · HR & Workforce
**Purpose:** People records — time-off, onboarding, payroll, certs, terminations.
**Current routes to migrate:** `/admin/people` (HR slice), `/admin/training`, `/admin/terminations`, `/document-expirations`, `/admin/employees/:id/history`
**Permissions:** Admin · HR
**Mobile:** iPad-optimised (HR Time Verification flow)
**SLA:** Time-verification < 3s (regression-locked)

### 6 · Safety & Compliance
**Purpose:** Incidents, audits, OSHA, certifications, compliance findings.
**Current routes to migrate:** `/admin/qaqc`, `/admin/compliance`, `/admin/compliance-findings`, `/admin/photos` (when scoped to safety review), `/admin/jha-plans` (safety side)
**Permissions:** Admin · Safety
**Mobile:** Full
**SLA:** Incident query < 1.5s

### 7 · Communications
**Purpose:** All outbound platform communication. Templates, automation, rules.
**Current routes to migrate:** `/admin/email`, `/admin/digest-config`
**Permissions:** Admin
**Mobile:** Read-only on mobile · full on iPad
**SLA:** Send queue health < 1s
**Standard:** PM digest email shell becomes the universal gold standard (see `EMAIL_TEMPLATE_STANDARD.md`)

### 8 · Data & Storage
**Purpose:** Backups · restore · Atlas health · R2 · retention · contamination probes.
**Current routes to migrate:** `/admin/database`, `/admin/system` (backup slice), `/admin/deploy-recovery`, `/admin/legacy-imports`
**Permissions:** Super-admin · Admin
**Mobile:** Read-only
**SLA:** Backup probe < 2s

### 9 · System Health
**Purpose:** Live operational state — observability, regression, gates, deploy status.
**Current routes to migrate:** `/admin/system-health`, `/admin/deploy-readiness`, `/admin/operations-events` (system slice)
**Permissions:** Super-admin · Admin
**Mobile:** Read-only
**SLA:** Probe response < 1s

### 10 · Governance
**Purpose:** Lifecycle rules · audit doctrine · cleanup doctrine · deploy governance · operational standards.
**Current routes to migrate:** `/admin/governance`, `/admin/operational-language`, `/admin/guidance-coverage`, `/admin/audit-log` (governance slice), `/admin/operational-inventory` (governance slice)
**Permissions:** Super-admin only
**Mobile:** Read-only
**SLA:** Governance report < 5s

---

## Routes that move OUT of `/admin/`

These are cross-portal operational surfaces that were sitting under `/admin` for convenience but actually serve PM/Shop/HR/Safety too. They keep their existing URLs (no breaking changes) but are removed from the admin sidebar:

- `/tasks` — cross-portal task surface
- `/document-expirations` — already cross-portal
- `/po-requests` — PM/Field surface
- `/project-health` — PM surface
- `/asset-transfers` — Dispatch + Shop surface
- `/guidance` — operator training (open to all roles)
- `/admin/promo-assets` — marketing; moves under a separate `/admin/marketing` namespace later

---

## Implementation guardrails

This document is a **map only**. The corresponding code refactor follows these strict rules:

1. **No URL deletion.** Every existing `/admin/*` URL keeps responding (with a redirect or shim) for at least 90 days.
2. **No backend route changes.** This phase only restructures the frontend nav grouping + page assignments.
3. **One domain per PR.** Identity & Access first, then Operations, etc. Each PR is < 500 LOC.
4. **Regression suite must pass between every domain.**
5. **Mobile/iPad smoke test before merging each domain.**
6. **AdminShell is the only nav surface modified.** No duplicate nav systems.

See `NAVIGATION_REARCHITECTURE_PLAN.md` for the per-domain migration sequence.
