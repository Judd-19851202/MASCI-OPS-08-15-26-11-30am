# User Friction Log

**Batch:** OMEGA · P2 · Real User Discoverability Audit
**Companion:** `REAL_USER_DISCOVERABILITY_AUDIT.md` · `USER_EXPERIENCE_IMPROVEMENT_ROADMAP.md`
**Date:** 2026-06-01

> Itemized friction inventory. Each row contains: ID · journey · persona(s) · severity · friction · impact · evidence anchor.

---

## 🔴 High Friction

### F-001 · Sandy / Per-Day Detail — no drill-through from variance row to time-verification

| Field | Value |
|---|---|
| **User journey** | Sandy uploads weekly payroll CSV → variance grid shows 14 flagged rows → for each row she wants to see the per-day timecard that produced that variance |
| **Persona(s)** | HR, Payroll · Sandy Lohrey + any HR backup |
| **Current behaviour** | `HrPayrollVariance.jsx` shows the flagged row with a `FLAG_META` chip. The row is not linkable. Sandy must open a new tab, navigate to `/hr/time-verification`, type the employee name, set the same week-ending date, then visually scan |
| **Friction** | 4+ clicks per row · context switch · re-typing of filters · employee-name typos cause empty results |
| **Impact** | Sandy spends ~20-30 min per Monday on payroll triage that should take ~5 min. Pulls Sandy off other reconciliation work. Erodes trust in the platform |
| **Evidence** | Operator-reported; `HrPayrollVariance.jsx` (no `<Link>` to `/hr/time-verification`) · `HrTimeVerification.jsx` (no inbound deep-link contract) |

### F-002 · Time Verification vs. Payroll Variance — two parallel HR tiles with overlapping copy

| Field | Value |
|---|---|
| **User journey** | HR user lands on HrHub. Sees two tiles: "Time Verification" and "Payroll Variance". Both have generic subtitles. Has to learn the difference by trial |
| **Persona(s)** | HR, Payroll · everyone except long-tenured users |
| **Current behaviour** | HrHub.jsx exposes two tiles side-by-side: `timeVerification: "/hr/time-verification"` and `payrollVariance: "/hr/payroll-variance"` with similar one-liners |
| **Friction** | Conceptual ambiguity. New HR hires routinely use the wrong tool first |
| **Impact** | Training overhead. Wrong-tool data entry (e.g. pasting payroll CSV into the time-verification page produces an empty board, looks broken) |
| **Evidence** | `HrHub.jsx` (lines listing `timeVerification`, `payrollVariance`); operator-reported confusion |

### F-003 · No in-app PO digest replay

| Field | Value |
|---|---|
| **User journey** | PM gets Monday digest email. Wednesday afternoon, PM remembers something in it but the email is buried. PM wants to re-read inside the platform |
| **Persona(s)** | PM (8), HR (3), Executive (3) |
| **Current behaviour** | No surface in `/po-requests`, `/pm` hub, or anywhere else lets a user view the digest content that was sent. The `po_digest_runs` audit collection does not exist (`PO_DIGEST_FORENSIC_REPORT.md`) |
| **Friction** | Users must search inbox; if the email was deleted they cannot recover the same view |
| **Impact** | PMs work in email instead of the platform · weakens platform stickiness · also blocks the operator from auditing "what did the system tell so-and-so last Monday?" |
| **Evidence** | `routes/po_digest_admin.py` exposes `/preview` (dry-run) but no persistent history |

### F-004 · Superintendent cannot find JHA from /leadership

| Field | Value |
|---|---|
| **User journey** | Superintendent on site needs the JHA for "trench shoring above 5'". Opens phone → /leadership |
| **Persona(s)** | Superintendent, Foreman |
| **Current behaviour** | `FieldLeadershipHub.jsx` does not link to `/jha`. Super must remember the route or go back to `/` (Hub) |
| **Friction** | Friction-on-friction: on-site, hands-busy, signal-poor; route memorisation is unrealistic |
| **Impact** | Crews call the office instead. Office passes the call to PM. PM screenshots the JHA. This eats ~10 min of two senior employees' time |
| **Evidence** | `FieldLeadershipHub.jsx` tile list does not include `/jha` |

### F-005 · Superintendent cannot see asset transfers from /leadership

| Field | Value |
|---|---|
| **User journey** | Super at job site expects a roller to arrive at 09:00. By 10:00 it's not there. Wants to know if the transfer is still in transit |
| **Persona(s)** | Superintendent, Foreman, Dispatcher |
| **Current behaviour** | `/asset-transfers` is linked from PmHub but not FieldLeadershipHub. Supers either ask dispatch or call the equipment yard |
| **Friction** | Cross-portal information silo |
| **Impact** | 5-15 min phone tag per missed delivery · escalates to a PM if dispatch is on another call |
| **Evidence** | `FieldLeadershipHub.jsx` (no `/asset-transfers` tile) vs `PmHub.jsx` (has it) |

### F-006 · Duplicate PO digest emails

| Field | Value |
|---|---|
| **User journey** | PM opens Outlook Monday morning. Two identical PO digest emails arrive within 60s |
| **Persona(s)** | PM, HR, Executive — all PO digest recipients |
| **Current behaviour** | Singleton scheduler race produces orphan + new scheduler both firing at same slot. Documented in `PO_DIGEST_ROOT_CAUSE.md` |
| **Friction** | Inbox clutter · trust erosion |
| **Impact** | Operator reports indicate this happens repeatedly. Up to ~22 emails per affected Monday · adjacent risk that safety + operator digests do the same |
| **Evidence** | `PO_DIGEST_FORENSIC_REPORT.md` (in this same batch) |

---

## 🟡 Medium Friction

### F-007 · Two parallel training-records surfaces (`/safety/training-records` vs `/hr/training-records`)

| Field | Value |
|---|---|
| **Persona(s)** | Safety, HR |
| **Current behaviour** | Both surfaces exist. Both are wired to similar APIs. Safety officers don't know which is canonical |
| **Friction** | Cognitive overhead · risk of stale data if HR adds a record only to one |
| **Impact** | Training record discrepancies during audits |

### F-008 · Two parallel dispatch surfaces (`/dispatch-portal` vs `/admin/dispatch`)

| Field | Value |
|---|---|
| **Persona(s)** | Dispatcher, Admin |
| **Current behaviour** | The Dispatch portal has DispatchBoard. The Admin portal has AdminDispatch with different controls. Cross-pollination is not documented |
| **Friction** | Dispatchers ask admins for help with controls that don't exist in their portal |
| **Impact** | Adoption pain for dispatchers |

### F-009 · PmProjectDetail entry path buried

| Field | Value |
|---|---|
| **Persona(s)** | PM, Executive |
| **Current behaviour** | The cross-domain timeline view is one of the platform's strongest surfaces, but reaching it requires clicking through `/pm/{sub-page}` first then selecting a project. Not a top-level PmHub tile |
| **Friction** | Users don't know it exists |
| **Impact** | The most valuable view in the PM portal is under-used |

### F-010 · Project Health tile copy underpromises

| Field | Value |
|---|---|
| **Persona(s)** | PM, Executive |
| **Current behaviour** | PmHub tile says "Operational friction by job". PMs expect a P&L / cost-to-complete view |
| **Friction** | Misaligned expectation |
| **Impact** | Tile under-clicked despite useful data |

### F-011 · Daily-report submission has two near-identical URLs (`/daily/new` vs `/daily/submit`)

| Field | Value |
|---|---|
| **Persona(s)** | Superintendent, Foreman, Office sharing the URL via SMS |
| **Current behaviour** | `/daily/submit` is `publicMode={true}` (no login). `/daily/new` requires auth. Both render `NewDailyReport.jsx` |
| **Friction** | Ambiguous which to share |
| **Impact** | Auth'd users land on `/submit` and lose features. Public users land on `/new` and bounce |

### F-012 · Manual safety digest fire is admin-only

| Field | Value |
|---|---|
| **Persona(s)** | Safety officer |
| **Current behaviour** | `/admin/digest-settings/send-now` is `Depends(require_admin)`. Safety officers must request from an admin |
| **Friction** | Cross-team handoff |
| **Impact** | Slow turnaround for ad-hoc safety bulletins (e.g. "fire the digest now after I corrected last week's incident count") |

### F-013 · Soft-deleted incidents are not visible to anyone in-app

| Field | Value |
|---|---|
| **Persona(s)** | Safety, HR, Admin |
| **Current behaviour** | `incidents.deleted_at` is set by the Sprint 1C delete flow, but there is no UI to view the soft-deleted set. Audit-only via Mongo |
| **Friction** | Asking "what happened to incident #abc" requires admin DB access |
| **Impact** | Trust erosion when records appear to "vanish" |

### F-014 · Hard-delete buttons visible to roles without permission

| Field | Value |
|---|---|
| **Persona(s)** | HR (clicks delete on safety records) |
| **Current behaviour** | HrSafetyRecords.jsx surfaces a delete button. The backend rejects with 403. HR sees the click "do nothing" or shows a toast |
| **Friction** | Buttons visible that produce no action |
| **Impact** | Mild · already documented in copy ("Hard-delete is reserved for Safety/Admin") · but the button should be greyed out, not present and inert |

### F-015 · Cross-portal navigation lacks a global breadcrumb

| Field | Value |
|---|---|
| **Persona(s)** | Everyone, especially multi-portal users |
| **Current behaviour** | Each hub has "Home" and "Back" buttons. No breadcrumb showing "Hub > HR > Payroll Variance > Drill #12" |
| **Friction** | Deep navigation feels stack-less |
| **Impact** | Users sometimes lose where they are; refresh-then-back loop |

### F-016 · Executive briefing fragmented across 3 Monday emails

| Field | Value |
|---|---|
| **Persona(s)** | Executive (Leo, Leticia, Jay) |
| **Current behaviour** | Three separate Monday digests: PO, Safety, Operator |
| **Friction** | Three emails for related data |
| **Impact** | Executives copy/paste figures into a single status doc; risk of stale or mismatched numbers |

---

## 🟢 Low Friction (recently resolved or minor cosmetic)

### F-017 · Photo viewer "Photo data unavailable or corrupt" overlay (RESOLVED 2026-06-01)

| Field | Value |
|---|---|
| **Persona(s)** | PM, Admin, Field Leadership |
| **Status** | 🟢 RESOLVED · `PHOTO_VIEWER_PRODUCTION_CERTIFICATION.md` |
| **Lingering UX gap** | The error string "Photo data unavailable or corrupt" is unhelpful; a future cosmetic pass should replace it with "Photo could not be loaded. Retry?" with a retry button |

### F-018 · Multi-portal sign-in vs direct sign-in

| Field | Value |
|---|---|
| **Persona(s)** | Cross-portal users (Jay Judd: PM + HR + Admin + Safety) |
| **Current behaviour** | `/sign-in` mints all tokens atomically; `/pm/login` mints only PM. Both work. Cross-portal users sometimes use the direct route and wonder why they don't have HR access in the same tab |
| **Friction** | Low — comment in `SignIn.jsx` documents the design choice |
| **Impact** | Minor |

### F-019 · "Send to a different email" for safety digest

| Field | Value |
|---|---|
| **Persona(s)** | Safety officer who needs to forward digest to a regional manager |
| **Current behaviour** | `/admin/digest-settings` lets admin edit recipients globally. No per-fire override |
| **Friction** | Low frequency |
| **Impact** | Minor — workaround = manually forward the email |

---

## Summary counts

| Severity | Count |
|---|---|
| 🔴 High | 6 (F-001 to F-006) |
| 🟡 Medium | 10 (F-007 to F-016) |
| 🟢 Low | 3 (F-017 to F-019) |

🔴 6 high-friction items concentrated in three buckets:
1. **HR payroll drill-through** (F-001, F-002)
2. **Field Leadership Hub completeness** (F-004, F-005)
3. **Digest replay + duplicate** (F-003, F-006)

🛑 Friction log complete. Continue to `USER_EXPERIENCE_IMPROVEMENT_ROADMAP.md`.
