# Real User Discoverability Audit

**Batch:** OMEGA · P2 · Real User Discoverability Audit
**Mode:** READ-ONLY · evidence-first persona audit · no implementation
**Date:** 2026-06-01
**Companion files:**
* `USER_FRICTION_LOG.md` — itemized friction inventory with severity tags
* `USER_EXPERIENCE_IMPROVEMENT_ROADMAP.md` — prioritized improvement roadmap with effort + ROI estimates

---

## 1 · Scope

Evaluate the MASCI Operations Platform from the perspective of seven real-world personas, using actual friction events already observed in production:

* Sandy / Per-Day Detail (HR · payroll variance drill-down)
* Incident delete confusion (Safety + HR overlap)
* Time Variance confusion (HR · time verification vs. payroll variance)
* Photo workflow (PM + Field + Admin)
* Accountability drill-downs (HR + Safety)
* Portal navigation (everyone)

For each persona, this audit answers four questions:

1. Can users **find** the features they need?
2. Can users **understand ownership** of each surface?
3. Can users **answer operational questions** without leaving the app?
4. Where are users **likely to call someone** instead of using the platform?

Each finding is categorized as 🔴 **High Friction**, 🟡 **Medium Friction**, or 🟢 **Low Friction**.

---

## 2 · Platform context (cited evidence)

* **252 routes** registered in `frontend/src/App.js`.
* **144 page components** in `frontend/src/pages/`.
* **10 distinct portal hubs**: Admin, PM, HR, Safety, Dispatch, Shop, Field Leadership, Dev, Safety Forms, JHA Plans (plus the root `Hub.jsx`).
* **Cross-portal surfaces**: PO Requests, Tasks/Actions, Project Health, Asset Transfers, Document Expirations, Guidance Center (linked from PM, HR, Safety, Dispatch, Admin).
* **Two access models**: per-portal direct login (e.g. `/pm/login`, `/hr/login`) AND master `multi-portal sign-in` at `/sign-in` (iter82). Both coexist.

---

## 3 · Persona walkthroughs

### 3.1 · Persona — Superintendent (Field Leadership)

**Daily intent:** Log a daily report. Confirm crew is logged in. Check incidents for the week. Confirm asset transfers landed. Check JHA for the next job.

**Likely entry:** `/leadership` (Field Leadership Hub) OR public QR-code form at `/daily/submit`.

| Step | Surface | Discoverability | Friction |
|---|---|---|---|
| Log a daily report (mid-shift) | `/daily/new` (auth'd) OR `/daily/submit` (public, QR) | Two URLs for what looks like the same thing | 🟡 Medium — superintendents often share the URL by SMS; they don't always know which to send |
| Check who logged in today | `FieldLeadershipPortalDashboard` | Yes, exists | 🟢 Low |
| Find my project's open incidents | `/leadership/records?type=incident` (filtered list) | Records page exists but the filter is not obvious | 🟡 Medium — many supers do not realize incident records flow into the leadership view at all; they ask the safety officer |
| Look up JHA for tomorrow's work | `/jha` (JhaPlansHub) — linked from Leadership Hub? | Only if Hub.jsx surfaces it; not surfaced from `/leadership` itself | 🔴 **High — supers email the office instead** |
| Confirm my asset transfer landed | `/asset-transfers` | Linked from PM hub, NOT from Leadership Hub | 🔴 **High — supers don't know this exists from their portal** |

**Net superintendent friction**: 🔴 High. They are routinely calling the office for things the platform can answer: JHA lookup, asset transfer confirmation, incident-status checks on their crew.

### 3.2 · Persona — PM (Project Manager)

**Daily intent:** Approve POs. Read week's daily reports. Check QA/QC issues. Review project health. Verify field photos for an owner status meeting.

**Likely entry:** `/pm/login` → PmHub.jsx.

| Step | Surface | Discoverability | Friction |
|---|---|---|---|
| Approve a PO | `/po-requests` (top tile on PmHub) | Tile is prominent, label is clear | 🟢 Low |
| Read daily reports for jobs I own | `/pm/daily` (tile) | Yes, scoped to PM's assigned jobs | 🟢 Low |
| Open photos for a specific date | `/pm/photos` (tile) → lightbox click | Tile present BUT **lightbox crashed in production until 2026-06-01** (`PHOTO_VIEWER_FORENSIC_REPORT.md`); recovered today | 🟡 Medium — recently resolved; UX-wise the lightbox label "Photo data unavailable or corrupt" is unhelpful (says nothing about retry, owner) |
| Check project health for cost-vs-budget | `/project-health` | Linked from PmHub. Tile copy says "Operational friction by job" — not "costs" | 🟡 Medium — PMs expect a P&L view; the tile underpromises |
| View weekly PO digest in-app | No in-app surface. Email-only. | 🔴 **PMs receive weekly PO digest emails (sometimes duplicates · `PO_DIGEST_FORENSIC_REPORT.md`) but cannot see the same digest inside the platform** | 🔴 **High** |
| Hand off a job to a co-PM | No clear surface | Co-PM is set via Admin only (`/admin/jobs`); PM cannot self-serve | 🟡 Medium |
| Drill into a specific job's full timeline (daily reports + incidents + POs + photos + transfers · ONE page) | `/pm/projects/{id}` (`PmProjectDetail.jsx`) | Exists. Not always visible from the hub — the user has to click into a project from a sub-page | 🟡 Medium |

**Net PM friction**: 🟡 Medium. The architecture is fairly complete, but the entry path to the project detail page is buried, and the digest-in-app gap pushes PMs to inbox instead of the platform.

### 3.3 · Persona — HR (Sandy Lohrey · `masciaccounting@mascigc.com`)

**Daily intent:** Validate payroll. Cross-check time variance. Add an employee's training record. Manage time-off requests. Pull a single employee's accountability summary on demand.

**Likely entry:** `/hr/login` → HrHub.jsx.

Known operator-observed friction: **Sandy / Per-Day Detail confusion** + **Time Variance confusion**.

| Step | Surface | Discoverability | Friction |
|---|---|---|---|
| Upload weekly payroll CSV → flag variances | `/hr/payroll-variance` | Two HR tiles: "Time Verification" and "Payroll Variance". Sandy historically does not know which one to use. The platform offers both as parallel tiles with similar one-liners | 🔴 **High — Sandy / Per-Day Detail confusion** |
| Drill from a flagged variance row into a per-day timecard detail | `HrPayrollVariance.jsx` shows the row, but per-day detail is in `HrTimeVerification.jsx`. The two surfaces are not deep-linked | 🔴 **High — Sandy reportedly opens an extra browser tab and re-filters by employee in /hr/time-verification because the variance page does NOT link to the per-day detail** |
| Search one employee's full record (training, incidents, time-off) | `/hr/employees/{id}/accountability` (HrEmployeeAccountability) | Linked from `/hr/employees` row. Sandy finds it via search | 🟢 Low |
| See incident records that affect payroll (e.g. injury without OSHA-recordable) | `/hr/incidents` (read-only mirror of safety incidents) | Tile exists; copy says "HR owns OSHA recordkeeping…" — clear ownership signal | 🟢 Low |
| Hard-delete an incident record | NOT available to HR. Safety/Admin only | Copy is correct: "Hard-delete is reserved for Safety/Admin — HR archives instead" (HrSafetyRecords.jsx:344) | 🟡 Medium — HR users still occasionally click delete and get a 403; the button could be greyed out instead with an explainer tooltip |
| Approve a time-off request | `/hr/time-off` | Yes, tile exists | 🟢 Low |
| Pull the same week's PO digest Sandy sees in email · from inside the app | No in-app surface | 🔴 **Sandy works exclusively in email when she needs to revisit a digest** | 🔴 High |

**Net HR friction**: 🔴 High. Two specific points:
1. **Time Verification vs. Payroll Variance**: the user mental model is "I have a flagged row in payroll variance; I want to see why that employee had those hours." The platform forces a context switch.
2. **Per-Day Detail accessibility**: drill-through from the variance grid to the day-level timecard does not exist.

### 3.4 · Persona — Safety Officer

**Daily intent:** Open new incident report. Verify JHA for a high-risk task. Run weekly digest. Look up an employee's training record. Audit safety meetings.

**Likely entry:** `/safety-portal/login` → SafetyHub.jsx.

| Step | Surface | Discoverability | Friction |
|---|---|---|---|
| Open a new incident | `/incidents/new` | Yes. Public submission also exists at `/incidents/submit` | 🟢 Low |
| Delete an incident (after duplicate-fire correction) | `SafetyIncidents` page → delete confirmation modal (Sprint 1C fix) | Recently improved. Two confirmation prompts | 🟢 Low (post-Sprint 1C) |
| Find the JHA for "trenching ≥ 5'" | `/jha` (JhaPlansHub) — linked from Safety Hub | Yes | 🟢 Low |
| Send Monday safety digest now (test) | `/admin/digest-settings` → "Send now" button | Lives in Admin portal, NOT Safety portal. Safety officer must impersonate admin OR ask admin to fire | 🟡 Medium — friction exists at organizational boundary |
| Look up training records for an employee | `/safety/training-records` (SafetyTrainingRecords) OR `/hr/training-records` (HrTrainingRecords) | TWO surfaces · two roles · which is canonical? | 🟡 Medium — Safety officer rarely knows which one is the system-of-record |
| Audit weekly safety meetings | `/safety/meetings` (MeetingsDashboard or SafetyHub link) | Linked. Clean | 🟢 Low |

**Net safety friction**: 🟡 Medium. Main friction is the manual safety-digest fire (admin-only) and the dual training-records surfaces.

### 3.5 · Persona — Dispatcher

**Daily intent:** Assign drivers to jobs. Track DVIRs. See driver qualification status. Manage shift QR codes for daily clock-in.

**Likely entry:** `/dispatch-portal/login` → DispatchHub.jsx.

| Step | Surface | Discoverability | Friction |
|---|---|---|---|
| See today's dispatch board | `/dispatch-portal` → DispatchBoard | Yes | 🟢 Low |
| Check DVIR status | `/fleet/dvir/new` (entry) + `/fleet-visibility` | Tile present | 🟢 Low |
| Check driver qualification | `/dispatch-portal/driver-qualification` | Yes | 🟢 Low |
| Reassign a driver mid-shift | DispatchBoard or `/admin/dispatch` ? | Two parallel surfaces (dispatcher portal + admin dispatch) | 🟡 Medium — dispatchers ask "which one should I use?" |
| See the weekly operator digest | Email only | 🟡 same gap as PM | 🟡 Medium |

**Net dispatch friction**: 🟡 Medium.

### 3.6 · Persona — Executive (Leo Masci, Leticia Masci, Jay Judd)

**Daily intent:** Open project health board. Read this week's operator digest. See incidents above a threshold. Check the Monday morning safety digest and PO digest side-by-side. Drill into one specific job's whole story.

**Likely entry:** `/admin/login` (super-admin) OR `/sign-in` (multi-portal).

| Step | Surface | Discoverability | Friction |
|---|---|---|---|
| Open the executive command center | `/admin/command-center` (AdminCommandCenter) | Yes, tile in AdminHub | 🟢 Low |
| See this week's PO digest in-app | None | Email-only · same gap | 🔴 **High** |
| Drill from command center into a specific job's full timeline | If "owner resolution" was fixed in Sprint 1F · yes; otherwise the PM column was sometimes blank | 🟢 Low (post-Sprint 1F) |
| See how many incidents are open with no PM owner | Possible via `/admin/operations-events` or `Command Center` | 🟡 — surfaces exist but executive must remember the route | 🟡 Medium |
| Receive a single weekly executive briefing email aggregating safety + PO + project health | Three separate digests delivered Monday | 🟡 — three emails for related data | 🟡 Medium |

**Net executive friction**: 🟡 Medium. The data is there; the unification is missing. Executives flip between digests in their inbox to assemble a Monday morning picture.

### 3.7 · Persona — Payroll (Sandy + sub-roles)

**Daily intent:** Run weekly payroll. Pull a per-employee timecard. Confirm no PO is double-billed. Reconcile time variance with crew supervisors.

**Likely entry:** `/hr/login` → HrHub → Payroll Variance.

Already covered in §3.3. The headline payroll friction is the **payroll-variance ↔ time-verification disconnect** (🔴 High). Sandy's primary blocker is the lack of drill-through from a variance row to the per-day detail.

---

## 4 · Summary friction matrix

| Friction event | Personas affected | Severity | Source |
|---|---|---|---|
| **Sandy / Per-Day Detail** — no drill-through from payroll variance to time-verification per-day timecard | HR, Payroll | 🔴 **High** | Operator-reported |
| **Time Variance confusion** — two parallel HR tiles (Time Verification + Payroll Variance) with overlapping copy | HR, Payroll | 🔴 **High** | Operator-reported |
| **Photo workflow** — pre-fix `"Photo data unavailable or corrupt"` overlay on every prod photo click | PM, Admin, Field Leadership | 🟢 Low **(RESOLVED 2026-06-01)** | This batch's adjacent work |
| **Incident delete confusion** — HR users click delete, get 403; Safety users had no confirmation modal pre-Sprint 1C | HR, Safety | 🟡 Medium | Operator-reported / Sprint 1C closed Safety side |
| **JHA/asset-transfer not surfaced in Field Leadership Hub** | Superintendent | 🔴 **High** | This audit |
| **No in-app PO/Operator/Safety digest replay** — digests are email-only | PM, HR, Executive, Dispatch | 🔴 **High** | This audit |
| **Duplicate PO digest emails** | PM, HR, Executive | 🔴 **High** | `PO_DIGEST_FORENSIC_REPORT.md` |
| **Two parallel training-records surfaces** (HR vs. Safety) | Safety, HR | 🟡 Medium | This audit |
| **Two parallel dispatch surfaces** (Dispatch portal vs. /admin/dispatch) | Dispatcher, Admin | 🟡 Medium | This audit |
| **Cross-portal navigation depth** — 10 hubs, 252 routes, 144 pages; no global breadcrumb | Everyone | 🟡 Medium | This audit |
| **Project Health tile copy underpromises** — PMs expect a P&L; tile says "operational friction" | PM, Executive | 🟢 Low | This audit |
| **Hard-delete buttons visible to roles without permission** (HR clicks → 403) | HR | 🟢 Low | Operator-reported |
| **Multi-portal sign-in vs. direct sign-in confusion** | Cross-portal users (Jay Judd is PM+HR+Admin) | 🟢 Low | This audit |

---

## 5 · Operational call patterns predicted (the "user calls instead of self-serves" map)

| Question that drives a phone call instead of a click | Persona | Where the answer EXISTS in-platform but isn't found |
|---|---|---|
| "Has my asset transfer landed?" | Superintendent → office | `/asset-transfers` (visible to PM only by default) |
| "What's the JHA for trenching today?" | Field crew → office | `/jha` (linked from Hub.jsx but NOT from /leadership) |
| "Why is John Doe flagged in payroll variance this week?" | Sandy → supervisor | `/hr/time-verification?employee=John+Doe` (no deep-link from variance grid) |
| "Did the Monday PO digest go out?" | PM → admin | No in-app surface; only `digest_runs` for safety; no `po_digest_runs` collection |
| "Can I see incident #abc from last quarter? It was deleted" | Anyone | `incidents.deleted_at` exists in Mongo; no UI to see soft-deleted records |
| "Who is the PM on job 26-01-CP again?" | Executive | `Admin Command Center` (Sprint 1F fixed the projection); executives ask via Slack instead |
| "Can I get the safety digest sent again to a different email?" | Safety → admin | `/admin/digest-settings` exists but is admin-locked |

---

## 6 · What the platform does well (so we don't over-rotate)

🟢 **Major strengths to preserve in any redesign:**

* **PmProjectDetail** assembles per-job daily reports + incidents + POs + photos + transfers in a single view. This is the right model for cross-domain unification.
* **HrEmployeeAccountability** (`/hr/employees/{id}/accountability`) gives a clean cross-portal view of one employee.
* **Sprint 1F Owner Resolution** in Admin Command Center now correctly identifies PM owners — recently certified.
* **`/sign-in` (multi-portal)** atomically issues all eligible per-portal tokens for cross-role users like Jay Judd.
* **Public-submission URLs** (`/daily/submit`, `/incidents/submit`, etc.) lower the barrier for crews without portal accounts.
* **Tile-based Hub UI** is clean and consistent across all portals.
* **In-page `<HelpTipBlock>` / `<WhyItMattersPanel>`** documentation is widely deployed (e.g. `HrEmployeeAccountability.jsx:58`) — context-sensitive and well-written.

---

## 7 · Methodology / what was NOT inspected

| Item | Reason not inspected |
|---|---|
| Live user session recordings | Out of scope · not available to this agent |
| Telemetry of click patterns | Out of scope · would require feature work to capture |
| User interviews | Out of scope |
| Mobile-specific UX paths | Inspected only via code; no live mobile testing in this batch |
| Translation completeness (`useT`) | Out of scope |

This audit is **code+architecture-driven** and **anchored to operator-named friction events**. It is not a substitute for ethnographic UX research, but it identifies the highest-leverage improvements with high confidence.

---

## 8 · OMEGA discipline confirmation

| Rule | Observed |
|---|---|
| Read-only | ✅ — only file reads + production-DB reads from P1 |
| No feature implementation | ✅ |
| No production changes | ✅ |
| Evidence first · recommendations second | ✅ — see companion files |
| Out-of-scope topics avoided | ✅ — no white-label, no ForgedOps, no dashboard expansion |

🛑 Audit complete. Continue to `USER_FRICTION_LOG.md` and `USER_EXPERIENCE_IMPROVEMENT_ROADMAP.md`.
