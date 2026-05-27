# Cross-Portal Governance Alignment — Readiness Plan

*Phase IV-BETA.5 prep · iter437 follow-up · 2026-02-27*
*Status: 🟢 INVENTORY COMPLETE · IMPLEMENTATION DEFERRED*
*Scope: HR · Dispatch · Safety · Field Leadership (PM is already done)*

> **Verification legend:**
> 🟢 **VERIFIED** — confirmed via codebase grep / live API in this audit.
> 🟡 **ASSUMED** — backed by code reading but not exercised end-to-end.
> ⚪ **UNTESTED** — proposed standard, no current code applies it yet.

---

## I. Why this document exists, and what it is not

The PM portal has just completed Phase IV-BETA.0 → BETA.4: a clean
inventory, a domain-grouped V2 sidebar, a re-tiered hub, a verified
auth-boundary fix, communication-doctrine alignment, and warning-only
governance instruments wired into the deploy gate.

The same discipline must now extend to the four remaining non-Admin
portals — **HR, Dispatch, Safety, Field Leadership** — but the
operator directive is explicit:

> Prepare HR / Dispatch / Safety / Field Leadership governance
> alignment plan. **Do not implement those portals yet. Inventory
> first, same discipline as PM.**

This document is therefore an **inventory + plan**, not an
implementation. Every claim about a portal's current state is grouped
under "🟢 VERIFIED" only if it was actually checked in the codebase
this pass. Proposed changes carry "⚪ UNTESTED".

---

## II. Portal-by-portal inventory (🟢 VERIFIED · this audit)

### II.A · HR Portal

| Dimension | Current state |
|---|---|
| Shell | `components/HrPageShell.jsx` (54 LOC) |
| Pages | 17 HR-* pages under `pages/Hr*.jsx` |
| Auth | HR-token (`X-HR-Token`) via `directoryAuth` multi-login flow |
| Audited admin-endpoint leak | **None** — no HR page calls `/api/admin/*` |
| Audited shared admin panels imported into HR | **None** of the 10 audited panels (Employee/Supplier/Equipment master, Job master, StatusBoard, Routing, Compliance, Posters, TrainingStats, MasterListPanel) are imported in HR pages |
| Sidebar | Linear nav inside `HrPageShell` — NOT yet domain-grouped (V1-style) |
| Hub | `HrHub.jsx` (size unverified) — NOT yet re-tiered to V2 |
| Notable strengths | Self-contained `/api/hr/*` namespace; no cross-portal panel re-use |
| Notable gaps | No coaching sublines; no V2 domain grouping; no hub re-tiering |

**Implication:** HR is clean from the iter437 P0 perspective. The
work needed is purely UX-governance (sidebar V2 + hub re-tier +
coaching sublines), not auth fixing.

### II.B · Dispatch Portal

| Dimension | Current state |
|---|---|
| Shell | No shared shell — each Dispatch page paints its own chrome (`DispatchHub.jsx` is the central one) |
| Pages | 7 Dispatch-* pages under `pages/Dispatch*.jsx` |
| Auth | Dispatch-token via multi-login flow |
| Audited admin-endpoint leak | **None** — no Dispatch page calls `/api/admin/*` |
| Audited shared admin panels imported into Dispatch | **None** |
| Sidebar | None — Dispatch operates as a single hub with embedded sections |
| Hub | `DispatchHub.jsx` — needs inventory before re-tiering |
| Notable strengths | Tight operational surface, very few cross-cutting dependencies |
| Notable gaps | No shared shell pattern; no V2 sidebar; no domain grouping |

**Implication:** Dispatch needs a **`DispatchShell`** extraction
before any V2 work — the absence of a shell makes governance
inconsistent today. This is a larger structural change than HR's.

### II.C · Safety Portal

| Dimension | Current state |
|---|---|
| Shell | `components/SafetyShell.jsx` (95 LOC) |
| Pages | 23 Safety-* pages under `pages/Safety*.jsx` |
| Auth | Safety-token via multi-login flow |
| Audited admin-endpoint leak | **None** — no Safety page calls `/api/admin/*` |
| Audited shared admin panels imported into Safety | **None** |
| Sidebar | Linear nav inside `SafetyShell` (similar to HR) |
| Hub | `SafetyHub.jsx` — needs re-tier |
| Notable strengths | Large but well-named surface; strong RBAC isolation |
| Notable gaps | Same as HR: no coaching sublines; no V2 domain grouping; no hub re-tier |

**Implication:** Safety is the largest non-Admin portal by page count
(23 pages). V2 sidebar work will require the most thoughtful domain
grouping — this is the portal that most needs the "calmer cockpit"
treatment.

### II.D · Field Leadership Portals (HUB and PORTAL — TWO surfaces)

| Dimension | Current state |
|---|---|
| Surface A (Internal) | `FieldLeadershipHub.jsx` (lives under `/field-leadership`) — admin/HR-internal field-leadership management surface |
| Surface B (External) | `FieldLeadershipPortalDashboard.jsx` (lives under `/field-leadership/portal/*`) — the actual field-leadership user portal |
| Shell | No shared shell — Surface A and Surface B use different chrome |
| Auth | FL-portal token for Surface B; staff tokens (HR/Admin) for Surface A |
| Audited admin-endpoint leak | **None** — no FL page calls `/api/admin/*` |
| Audited shared admin panels imported into FL | **None** |
| Sidebar | None on either surface |
| Hub | `FieldLeadershipPortalDashboard.jsx` is the primary FL-user landing |
| Notable strengths | Strict scope on `/api/field-leadership/portal/*` |
| Notable gaps | Two parallel surfaces with diverging chrome; no V2; no coaching sublines |

**Implication:** FL has a structural decision to make BEFORE V2
work — should Surface A and Surface B share a shell, or stay
intentionally separate? This is a governance question, not a
visual one, and the operator will need to make the call.

---

## III. Cross-portal posture (🟢 VERIFIED · this audit)

| Question | Answer |
|---|---|
| Does any non-PM, non-Admin page call `/api/admin/*`? | **No** (grep confirms zero hits across HR / Safety / Dispatch / FL `pages/*.jsx`) |
| Does any non-PM, non-Admin page import a shared admin panel known to hardcode `/api/admin/*`? | **No** |
| Are HR / Safety / Dispatch / FL at risk of the regression that hit PM? | **No** — they were never wired into the offending shared panels |
| Are there other admin-token leak vectors that PM didn't have? | Not detected. Each portal has a clean `/api/{portal}/*` namespace. |

**Net:** The auth-routing P0 was specific to PM. HR / Dispatch /
Safety / FL are clean on that axis today. The governance work
remaining is UX-only.

---

## IV. Proposed alignment work order (⚪ UNTESTED · plan only)

When authorised, the cleanest sequence is:

### IV.1 · HR (smallest blast radius)

1. Inventory `HrHub.jsx` (tile count, current grouping).
2. Author `HR_PORTAL_CURRENT_STATE_AUDIT.md`.
3. Author the 8 HR governance docs mirroring the PM set
   (operational verbiage, hub re-tiering plan, sidebar V2 plan,
   coaching subline matrix, visual loudness baseline, cross-portal
   coaching standard delta, V2 certification template, mobile-scroll
   certification template).
4. Implement HR Sidebar V2 behind `?hrSidebarV2=1` flag.
5. Implement HR Hub V2 re-tier behind the same flag.
6. Wire `verify_coaching_sublines.py` to include HR routes (currently
   only PM is governed).
7. Run Playwright regression + manual review.
8. Promote out of flag.

### IV.2 · Safety (largest portal — most careful pass)

Same eight-step pattern as HR. The Safety hub has 23 pages so the
domain grouping is the critical artifact. Expected domains:
- Documents & Training
- Incidents & Investigations
- Audits & Inspections
- Records & Profiles
- System (login, password, etc.)

### IV.3 · Dispatch (needs structural shell extraction first)

1. Extract `DispatchShell.jsx` from `DispatchHub.jsx`.
2. Then follow the HR/Safety eight-step pattern.

### IV.4 · Field Leadership (operator decision required)

1. **Decision**: keep Surface A and Surface B separate, or
   unify under a shared shell?
2. After decision, follow the HR/Safety pattern for whichever
   surface(s) remain.

---

## V. Governance script extension plan (⚪ UNTESTED · plan only)

The three governance instruments today govern PM and Admin only:

| Script | Today's scope | Cross-portal extension |
|---|---|---|
| `verify_coaching_sublines.py` | PM Sidebar V2 + Admin Sidebar V2 governed sublines | Extend `GOVERNED_FILES` to include HR/Safety/Dispatch/FL sidebars once V2 ships per portal |
| `verify_admin_copy.py` | Whole frontend (already cross-portal) | No change needed — already scans all of `frontend/src/` |
| `measure_visual_loudness.py` | Routes passed as `--routes` | Extend the `pre_deploy_check.sh` invocation to add `/hr /safety /dispatch /field-leadership/portal` as V2 ships per portal |

**No script source changes are needed today.** The scripts already
generalize; what's required is wider invocation when each portal V2
lands.

---

## VI. Communication doctrine extension plan (⚪ UNTESTED · plan only)

Per `COMMUNICATION_UNIFICATION_DOCTRINE.md` addendum A.VII, six email
sites have subject-line drift. Of those:

| Drift site | Owning portal |
|---|---|
| `routes/shop_parts.py:323` (Parts order subject) | Shop (out of HR/Safety/Dispatch/FL scope but PM-adjacent) |
| `routes/pm_admin.py:333` (PM admin notif) | PM (will be handled in PM IV-BETA.3-impl) |
| `po_digest.py:321` (PO/cost digest) | PM/HR (shared) |
| `outage_alerts.py:115` (Sentry outage) | Platform-wide |
| `health_monitor.py:113` (Backend health) | Platform-wide |
| `backup_verification.py:498` (Backup) | Admin |

None of these are *exclusively* HR / Dispatch / Safety / FL. The
communication unification work is therefore largely orthogonal to the
cross-portal sidebar/hub alignment plan above, and can proceed in
parallel.

---

## VII. Estimated effort (⚪ UNTESTED · planning estimate, not a commitment)

| Portal | Effort tier | Notes |
|---|---|---|
| HR | **S** (small) | No shell extraction, no auth fix — pure UX governance |
| Safety | **M** (medium) | 23 pages, careful domain grouping |
| Dispatch | **M-L** (medium-large) | Shell extraction first, then UX governance |
| Field Leadership | **L** (large) | Surface-strategy decision + double-surface alignment |

---

## VIII. Constraints reaffirmed

- ✅ Preview only — no production touches
- ✅ No backend rewrite required (cross-portal auth boundaries are
  already clean; iter437 confirmed HR/Safety/Dispatch/FL never had the
  PM-specific leak)
- ✅ No destructive data action
- ✅ Every artifact distinguishes 🟢 VERIFIED / 🟡 ASSUMED / ⚪ UNTESTED
- ✅ Every implementation pass when authorised must be regression-locked
  with a portal-specific Playwright test mirroring the PM precedent
- ✅ Each portal's V2 sidebar ships behind a single feature flag (e.g.,
  `?hrSidebarV2=1`) before promotion, matching the PM playbook

---

## IX. Stop point — handoff to operator

This document **does not authorise** any of the work in §IV–§VI. It is
the planning artifact requested by the operator at the end of the
iter437 follow-up batch. Implementation begins only when the operator
selects a portal (probably HR, since it is the smallest) and authorises
the eight-step pattern in §IV.1.
