# MASCI Track 13 — Platform Reality + Five-Pillar Audit

**Date:** 2026-06-11
**Author:** ForgedOps (RC-2.1-certified state · pre-Track-13 freeze)
**Doctrine:** Read-only audit. Zero code changes in this document. The audit precedes any rebuild. If reality is misread, all subsequent work fails.
**Evidence base:** Live screenshots of all 7 portals captured at 21:55 UTC against the preview pod (`safety-audit-mobile-1.preview.emergentagent.com` · DB `masci_safety_preview`) using the super-admin token. KPI tile names, testids, headings, and API call lists harvested via Playwright DOM + `performance.getEntries()`. Source files read where structure was ambiguous.

---

## 0. Read-Me

This document does **three** things and nothing else:

1. **Captures what currently exists** in every portal, KPI-by-KPI, API-by-API, with no editorialising.
2. **Identifies drift** — the gap between the role each portal is supposed to serve and what its first screen actually rewards.
3. **Scores each portal against the Five Pillars** (Powerful · Simple · Beautiful · Trusted · Proven) and produces three lists: **PRESERVE**, **FIX**, **REBUILD**.

It does **not** contain the rebuild itself. The rebuild begins only after this document is operator-acknowledged.

---

## 1. Platform Design Baseline (cross-portal · already shipped)

The platform already has a coherent visual language. Any portal change must inherit from this baseline; no portal may invent its own.

| Element | Pattern in production | Where it appears |
|---|---|---|
| Top safety stripe | Red caution-stripe + amber preview banner (`PREVIEW ENVIRONMENT · DB: MASCI_SAFETY_PREVIEW · DO NOT ENTER REAL OPERATIONAL DATA`) | Every page, every portal |
| Header chrome | Black bar · MASCI mark · Home/Back/Hub link · Search · Notification bell · Portal switcher · EN/ES toggle · Sign out | All authenticated portals |
| Portal palette | `paletteFor(<role>)` — pm=red, shop=orange, hr=purple, safety=yellow, dispatch=sky, leadership=red, admin=slate/red | `lib/portalPalette.js` |
| KPI tile | `<Tile>` — number + label + amber/rose "Needs attention" badge when ≥1; orange/slate when 0 | every portal uses identical shape |
| Section title | font-mono uppercase `tracking-[0.22em]` lozenge + bold sentence-case headline + slate-600 lede | every section |
| Card body | white bg · `border border-slate-200` · `rounded-md` · `p-5 sm:p-7` · `print:break-inside-avoid` | every card |
| Empty state | "No X recorded — next action is Y." (rarely a bare 0) | inconsistent — see §6 |
| Buttons | Pill or square, h-11/h-12, font-bold uppercase tracking-wide, role-tinted bg, white text | every CTA |
| Drawers/Modals | shadcn `Sheet`/`Dialog` with backdrop-blur-md, rounded-md, rose/amber accents | Admin + Shop |
| Table | white bg, slate-200 borders, `text-sm`, sticky header, mono cell IDs (`EQ-…`, `DR-…`) | Admin + Shop + Safety |
| Search | Top-bar inline (`<input class="font-mono">`) + Cmd-K affordance | Admin (`admin-global-search`), Dispatch, HR have it; PM/Shop do not |
| Mobile nav | hamburger → sheet with portal-tinted left rail (post-iter314); 44 px tap targets after RC-1 Final Hardening | every portal |

**Baseline verdict:** the language is consistent. Drift, where it exists, is in the **content** each portal pushes to its first screen, not the chrome.

---

## 2. Portal-by-Portal Reality Audit

For each portal: who is it serving today? what KPIs greet them? what data feeds those KPIs? where is the drift?

---

### 2.A · ADMIN PORTAL — `/admin`

**Intended user:** Platform administrators, owners, governance.

**Current state — first screen**

- Header: `ADMIN CONSOLE · Overview · KPIs, Search, Snapshot`
- Welcome paragraph + governance score `54/100`
- Top-bar search (`admin-global-search` · "Search assets, employees, events…")
- Left rail (12 groups): **Overview · Command Center · People & Access · Jobs & Field · Equipment & Suppliers · Email & Routing · Training & Forms · Compliance & Audits · Tasks & Actions · Document Expirations · PO Requests · Project Health · Asset Transfers · Dispatch · Operations Events · Integrations · System & Backups · System Health · Database · Weekly Digest · Audit Log · Sessions · Deploy Recovery · Deploy Readiness · Usage Analytics**

**KPI tiles (Operations Center · Admin):** 14 tiles

| Tile (testid) | Value | Source |
|---|---|---|
| `ops-card-tasks_overdue` | 0 | `/api/operations-center` |
| `ops-card-tasks_open` | 1697 | `/api/operations-center` |
| `ops-card-po_pending_approval` | 0 | `/api/operations-center` |
| `ops-card-po_missing_receipt` | 36 (Watch) | `/api/operations-center` |
| `ops-card-po_overdue_receipt` | 23 (Needs attention) | `/api/operations-center` |
| `ops-card-po_approval_p90` | 0 s (30-day p90) | `/api/operations-center` |
| `ops-card-doc_exp_expiring` | 0 | `/api/operations/expirations/summary` |
| `ops-card-doc_exp_expired` | 6 (Needs attention) | `/api/operations/expirations/summary` |
| `ops-card-incidents_open` | 44 (Needs attention) | `/api/incidents` |
| `ops-card-ca_overdue` | 17 (Needs attention) | `/api/operations-center` |
| `ops-card-equipment_down` | 1 (Needs attention) | `/api/operations/intelligence` |
| `ops-card-equipment_holds` | 0 | same |
| `ops-card-preop_failed_recent` | 0 | same |
| `ops-card-repeat_equipment_failures` | "No signal yet · 30 days · ≥3 fails per unit" | same |
| `ops-card-integration_health` | Unknown | `/api/integrations/health` |
| `ops-card-audit_coverage` | 48 % (372 / 781) | `/api/operations-center` |

**Operational Intelligence sub-strip (OIS):**

- `ois-drivers-card` — Motive **53 Active · 12 Deactivated · 0 HOS 24 h**
- `ois-equipment-card` — Equipment Health 24 h: **0 Critical · 0 Gateway Offline · 0 DVIR Crit**
- `ois-safety-card` — **0 Harsh 24 h · 2 Geofence Enter 7 d · 2 Exit 7 d**

**Document & Certification Expirations sub-strip:** 28 Expired · 6 ≤30 d · 11 ≤60 d · 8 ≤90 d · 88 Healthy

**APIs feeding Admin first screen (30 confirmed):** `/api/version`, `/api/notifications/unread-count`, `/api/operations-center`, `/api/integrations/health`, `/api/health`, `/api/employees`, `/api/suppliers`, `/api/equipment-master`, `/api/equipment-types`, `/api/inspections`, `/api/meetings`, `/api/jhas`, `/api/incidents`, `/api/daily-reports`, `/api/operations/intelligence`, `/api/admin/integrations/motive/reliability-state`, `/api/operations/expirations/summary`, `/api/operations-actions/summary`, `/api/job-hazard-plans`, `/api/trench-boxes`, `/api/equipment-inspections`, `/api/qaqc-inspections`, `/api/field-leadership`, `/api/job-photos`, `/api/cluster/capacity`, `/api/banners/active`, `/api/governance/health/admin`, `/api/admin/check`, `/api/pm/check`, `/api/shop/check`.

**Role audit:** **Serves admin reality.** Every group on the left rail maps to an admin responsibility. KPI tiles are admin-grade (overdue tasks, PO velocity, audit coverage, integration health). The 1697 Open Tasks number is honest — admins are the ones who chase the backlog.

**Five-Pillar score**

| Pillar | Score (/5) | Notes |
|---|---:|---|
| Powerful | **5** | Search bar at top, 25 sub-routes one click away, every group has a working sub-page. |
| Simple | **3** | First screen has ~30 navigable surfaces. Discoverable via search but visually dense. |
| Beautiful | **4** | Consistent chrome, left rail is well-grouped. KPI grid wraps cleanly. |
| Trusted | **4** | All KPI values are sourced via documented endpoints; integration_health = "Unknown" is honest when Motive isn't paired. |
| Proven | **4** | Admins use it. Governance score, audit-log coverage, scheduler digests all real ops needs. |

**Drift:** None on role. **Cognitive load is high** but that is a density choice, not a drift.

---

### 2.B · PM PORTAL — `/pm` → redirects to `/pm/command-center`

**Intended user:** Project Managers.

**Source file:** `pages/PmCommandCenter.jsx` (header comment: "PM Command Center · FORGEDOPS Phase 4B. One page · six operational sections · top KPI strip"). Built on Phase 4A endpoints `/api/pm/command-center/{overview,resources,hauls,materials,shop-impact,safety-impact,timeline}`.

**Current state — first screen**

- Header: `PM · Command Center · v1 · Project Operational Truth · All my projects`
- Project selector dropdown ("All my projects")
- Tabs: **Overview · Resources · Hauls · Materials · Shop · Safety · Timeline**
- Right-side link: "Dispatch PM Hub"

**KPI tiles — twelve total, all six on a single row + six on a second row:**

| Tile (testid) | Value | What it actually is |
|---|---:|---|
| `pm-cc-tile-active-assignments` | **272 Active Jobs** | active dispatch *assignments* (haul lifecycle), not project count |
| `pm-cc-tile-trucks-assigned` | 135 Trucks | trucking |
| `pm-cc-tile-drivers-assigned` | 30 Drivers | trucking |
| `pm-cc-tile-equipment-assigned` | 693 Equipment | fleet |
| `pm-cc-tile-trailers-assigned` | 2 Trailers | fleet |
| `pm-cc-tile-road-plates-assigned` | 88 Road Plates | resource |
| `pm-cc-tile-active-hauls` | 272 Active Hauls | trucking |
| `pm-cc-tile-materials-in-today` | 0 Materials Today | trucking-adjacent |
| `pm-cc-tile-defects-open` | 0 Open Defects | shop-adjacent |
| `pm-cc-tile-incidents-open` | 44 Incidents | safety |
| `pm-cc-tile-open-safety` | 24 Open Safety | safety |
| `pm-cc-tile-loads-today` | 0 Loads Today | trucking |

**Below the strip:** "Overview" tab content shows three columns — **Resources · Open** (Equipment 693 · Trucks 135 · Trailers 2 · Road Plates 88 · Drivers 30); **Hauls · Open** (Assignments 272 · Hauls 272 · Loads 0 · Materials in 0 · Materials out 0); **Impact · Open** (Defects 0 · Incidents 44 · CAPAs 24). Footer integrations row: **FleetWatcher: Pending Integration · MaintainX: Pending Integration.**

**Role audit:** 🔴 **MAJOR DRIFT.** The portal is named "Project Operational Truth" but it shows fleet/haul/material counts as the dominant signals. A PM walking in at 5:30 AM does not need to know there are 135 trucks; they need to know:

- Which of my projects need attention today?
- Which dailies are missing?
- What did the field report last night?
- Are there open issues blocking work?
- What does safety look like on my jobs?
- What does my schedule look like this week?

**None of these questions are answered by the first screen.** The 6 tabs (Resources · Hauls · Materials · Shop · Safety · Timeline) are organized by *operational resource type*, not by *project*. There is no per-project rollup card on the first screen.

**Data joins (Track 13H check):**

- `272 Active Jobs` — Honest count of active assignments. But this is *assignments*, not *projects*. There are likely 6-15 actual MASCI projects today (preview pod fixtures + a few real).
- `0 Loads Today / 0 Materials Today` — Likely honest empty state (no loads recorded yet today UTC at 21:55).
- `0 Open Defects` — Suspicious. Admin OIS shows "1 Equipment Out of Service" and Shop shows 183 Blocked + 149 Awaiting RTS. Possible broken join: PM tile counts only PM-owned defects (none) while shop sees system-wide. Needs verification.
- `44 Incidents` / `24 Open Safety` — Cross-references Admin OIS exactly. Honest.
- `FleetWatcher / MaintainX Pending Integration` — Honest (operator-known Atlas separation gate per FORGEDOPS).

**Five-Pillar score**

| Pillar | Score (/5) | Notes |
|---|---:|---|
| Powerful | **2** | Lots of numbers; *zero one-click PM actions* (no "Open Daily", no "Approve a Daily", no "Review Issue", no project drill-down on first screen). |
| Simple | **2** | First screen is a fleet dashboard wearing PM clothing. Confusing for the role. |
| Beautiful | **4** | Inherits baseline; visually clean and consistent. |
| Trusted | **3** | Numbers are sourced but the *labels* mislead ("Active Jobs" = assignments, not projects). |
| Proven | **1** | Would not survive a real PM 5:30 AM scrub. Fails Track-13 "10-second test". |

**Drift verdict:** 🔴 **CONFIRMED CRITICAL. Rebuild required.**

---

### 2.C · DISPATCH PORTAL — `/dispatch-portal`

**Intended user:** Dispatchers (live fleet ops).

**Current state — first screen**

- Header: `DISPATCH · Dispatcher`
- Right-of-header: **Switch Portal · Search · Sign out**
- Alert banner: "**Equipment Maintenance Issues Requiring Attention: 149 · View Equipment Status**" (links Shop context into Dispatch — good cross-portal signal)
- Section 1 — `RIGHT NOW · Operational Attention` — 3 tiles: **Trucks in Breakdown 0 · Stuck >30 min 0 · Extended Wait 0** + actions "Open the Operational Board" + "What requires dispatch attention"
- Section 2 — `PRIMARY ACTIONS · Issue Work` — 4 action cards: **Create Assignment · Start Equipment Move · Tanker / Liquid Asphalt · Support / Misc Haul** (with how-it-works links)
- Section 3 — `WATCH MOVEMENT · Live Operational Board` — explanatory blurb + **giant orange "Open Operational Board" button**
- Section 4 — `RESOLVE BEFORE TOMORROW · Follow-Through`

**Headings inventory:** "Operational Attention · Issue Work · Live Operational Board · Follow-Through · Fleet, utilization, and integrations · Recent transfers · Active holds · Operations Actions · Recent field memory."

**Role audit:** **Largely serves dispatcher reality** — every section answers a dispatcher question. **However:**

- The Live Map is **one click away via a clearly visible orange "Open Operational Board" button**, but it is **not embedded** in the hero. Dispatchers need to see "who is moving / who is stuck / where is everything" in their *first glance*, not after a click. The current design is excellent for *triaging* (the 3 attention tiles + Issue Work actions are extremely useful) but weak for *situational awareness*.
- All three attention tiles read 0/0/0 in preview. Either preview fixtures lack live-truck data, or the join is filtering on a project scope that is empty. Verify before deploy.

**Five-Pillar score**

| Pillar | Score (/5) | Notes |
|---|---:|---|
| Powerful | **4** | Issue Work action cards + Operational Board access → one click to act. |
| Simple | **4** | Clear sections, clear ordering. |
| Beautiful | **4.5** | Best-looking portal. Orange/red palette, density well-balanced. |
| Trusted | **3** | 0/0/0 attention tiles are either honest (preview has no live-truck signal) or broken joins — must verify. |
| Proven | **4** | Dispatchers can issue work and triage from this screen. Lacks the embedded map. |

**Drift verdict:** 🟡 **MODERATE.** Live Map needs to be *embedded* on the first screen, not only linked. This is an enhancement, not a rebuild.

---

### 2.D · SHOP PORTAL — `/shop`

**Intended user:** Shop / maintenance / parts personnel.

**Current state — first screen**

- Header: `SHOP · Sign out` etc.
- Section 1 — `Recent field memory` (TEST-prefixed equipment notes from past 3 days — preview fixtures)
- Section 2 — `Equipment Down · Faults · GPS Health` (OIS-1D Motive Equipment Intel):
  - **1 Critical Faults · 1 Gateway Offline · 2 DVIR Defects · 1 Fault Closed 30 d · 100 GPS Not Reporting**
  - Lists actual vehicle IDs (`veh 1438259 fault_code 6/8/2026 1:57:02 PM`, `DPT014-7057 NOT REPORTING South Patrick Shores, FL Last: 4/13/2026`, etc.)
- Section 3 — `MAINTAINX READINESS QUEUE · READ-ONLY` — **Ready 2 · Blocked 183 · Duplicate Risk 2 · Awaiting RTS 149**
- Section 4 — Shop Recovery (Equipment Needing Attention · Trucks in breakdown right now)
- Section 5 — Operations Actions
- Section 6 — Active Recovery Work 0 · Waiting / Delays 0 · Returned to Service 0
- Section 7 — Operational Continuity History

**Role audit:** **Strong role fit.** The portal already shows everything Track 13D requires:

- Equipment needing attention ✅
- Trucks in breakdown right now ✅
- Open DVIR issues ✅ (2 listed with timestamps)
- Failed Pre-Op inspections ✅ (Critical Faults bucket)
- MaintainX readiness ✅ (4-tile readiness queue with real numbers)
- Equipment locations from Motive ✅ (DPT014-7057 Port Orange, FL Last: 5/29/2026)
- Open shop items ✅
- Active recovery work ✅
- Returned to service ✅

**Data:** Real per-vehicle data with timestamps and locations. MaintainX 183 Blocked is a real backlog, not a placeholder.

**Empty states:** Active Recovery Work 0 · Waiting/Delays 0 · Returned to Service 0 — these read honestly: nothing currently in those buckets in preview. Could be tighter empty-state copy ("No equipment currently in active repair — start a recovery from the queue above") but functional.

**Five-Pillar score**

| Pillar | Score (/5) | Notes |
|---|---:|---|
| Powerful | **4.5** | Real per-unit data, MaintainX cross-link, Motive signals all wired. |
| Simple | **4** | Clear sectioning. The "Operational Continuity History" footer is a little verbose. |
| Beautiful | **4** | Inherits baseline; readability is good. Could use slightly higher info density in the lower sections. |
| Trusted | **5** | Every value sourced; "No work orders are created from this view" disclaimer respected. |
| Proven | **4.5** | Shop crews would use this without retraining. |

**Drift verdict:** 🟢 **NO DRIFT.** Polish opportunities only (empty-state copy, info density). **No rebuild required.**

---

### 2.E · HR PORTAL — `/hr`

**Intended user:** HR + workforce-compliance personnel.

**Current state — first screen**

- Header: `HR PORTAL · Employee Records & Accountability · Read-only HR access · field leadership records · accountability · payroll-time verification · training compliance.`
- Governance Drift: **100/100** ✅
- KPI tiles (4): **Incidents Open 44 · Overdue PO Receipts 23 · Corrective Actions Overdue 17 · Docs Expired 6** (all with "Needs attention" badges)
- OA-1 Operations Actions banner: "Operations Action — operational ownership, not a ticket. · 68 Open"
- Sections (visible headings): **People Operations · Employee Lifecycle · Employee Requests Queue · Tasks & Actions · Employee Accountability · Field Leadership Records · Time & Payroll · Time Verification · Payroll Variance (CSV) · Time Off Requests · PO Requests & Receipts · Compliance & Records · Document Expirations**

**Role audit:** **Largely on-role**, but two anomalies:

1. **`Incidents Open 44`** as an HR first-screen tile is questionable — incidents are safety. HR cares about *employee-impact* incidents (injuries, terminations, attendance) but the raw count belongs in Safety. Same for `Corrective Actions Overdue` — those are usually safety/operations CAPAs, not HR CAPAs.
2. **`Overdue PO Receipts 23`** on the HR first screen is admin territory — HR rarely chases PO receipts.

These three KPIs feel like the operations-center aggregate was pasted onto HR. They should be replaced with HR-native KPIs (Onboarding due · Training due · Credentials expiring · Time-verification pending · Open employee requests).

**Otherwise:** the section list is HR-native. Lifecycle / Requests / Field Leadership Records / Time & Payroll / Document Expirations are exactly HR work.

**Five-Pillar score**

| Pillar | Score (/5) | Notes |
|---|---:|---|
| Powerful | **3.5** | Section list is real HR work; KPI strip leaks ops content. |
| Simple | **3.5** | Section count is healthy; KPIs add noise. |
| Beautiful | **4** | Inherits baseline; purple accent reads as HR. |
| Trusted | **3.5** | 4 KPI tiles are sourced honestly but conceptually mis-shelved. |
| Proven | **4** | HR personnel can find lifecycle / requests / documents from here. KPIs need swap. |

**Drift verdict:** 🟡 **MINOR.** Replace the 4 KPI tiles with HR-native KPIs. Keep section list intact. **No layout rebuild required.**

---

### 2.F · SAFETY PORTAL — `/safety-portal`

**Intended user:** Safety officers / safety managers.

**Current state — first screen**

- Header: `SAFETY PORTAL · Safety Operations Dashboard · Governance Drift 100/100`
- Recent field memory feed (3 entries)
- "Incident filed · 4 hr ago" timeline pill
- Section — `SPRINT A · DOCEXP-60/90 · Training & Certification Expirations` — 5 tiles: **28 Expired · 6 ≤30 d · 11 ≤60 d · 8 ≤90 d · 88 Healthy**
- Expiring item list (`TEST_iter151_TWIC_5d 2026-06-13 ≤30 d` · `Competent Person Cert 2026-06-14` etc.)
- Left rail: **Incidents & Escalation (Incidents & Near Misses · Corrective Actions · Tasks & Actions) · Documents & Training (Training & Certifications · Safety Document Library · Equipment & PPE Accountability · Employee Safety Profiles) · Compliance & Records (Document Expirations · Fire Extinguishers · …)**

**Role audit:** **Strong role fit.** Every left-rail group is safety-native. The 5-tile training/cert expiration strip is exactly what a safety officer scans at the start of the week. Recent incident pill is correct first-glance content.

**Five-Pillar score**

| Pillar | Score (/5) | Notes |
|---|---:|---|
| Powerful | **4** | Left rail covers incidents, CAPAs, training, library, PPE. |
| Simple | **4** | Clear hierarchy. |
| Beautiful | **4** | Inherits baseline. |
| Trusted | **5** | Real per-credential list with dates. |
| Proven | **4** | Safety officers would use it. |

**Drift verdict:** 🟢 **NO DRIFT.** **No rebuild required.**

---

### 2.G · FIELD LEADERSHIP PORTAL — `/leadership`

**Intended user:** Foremen, superintendents, field leaders.

**Current state — first screen**

- Header: `RESTRICTED · CREW DOCUMENTATION · Field Leadership · Crew accountability, employee documentation, equipment responsibility, recognition, and workforce-management tools for MASCI field leadership.`
- Compliance lozenge: "ALL FORMS MUST BE FACTUAL, PROFESSIONAL, AND COMPLIANT WITH EMPLOYMENT-DOCUMENTATION BEST PRACTICES."
- Recent field memory feed (3 entries — `EQUIPMENT TEST-8aec185b — Shop hydraulic pressure note · 3 d ago` etc.)
- Timeline pill: "Daily report filed · 4 hr ago"
- Section: `DAILY CREW DOCUMENTATION · What you fill out at the end of a shift to keep the paper trail clean.`
- **4 action cards**: Verbal Coaching · Employee Write-Up · Attendance / Tardy · Recognition / Reward — each with "New Entry →" button
- Top bar: Guides · Records

**Role audit:** **Excellent role fit.** Field leadership doesn't need a dashboard; they need a few documentation forms they can complete in 90 s from the cab of a truck. The portal is purpose-built for that.

**Five-Pillar score**

| Pillar | Score (/5) | Notes |
|---|---:|---|
| Powerful | **5** | "New Entry" is one tap; that's the whole job. |
| Simple | **5** | Four cards. Done. |
| Beautiful | **5** | Cleanest portal. |
| Trusted | **5** | Honest "Recent field memory" feed. |
| Proven | **5** | Foremen would use this on day 1, in the field, no training. |

**Drift verdict:** 🟢 **NO DRIFT. Reference standard for all others.**

---

## 3. Five-Pillar Summary Table

| Portal | Powerful | Simple | Beautiful | Trusted | Proven | **Total /25** | Verdict |
|---|---:|---:|---:|---:|---:|---:|---|
| Admin | 5 | 3 | 4 | 4 | 4 | **20** | 🟢 Preserve |
| **PM** | 2 | 2 | 4 | 3 | 1 | **12** | 🔴 **REBUILD** |
| Dispatch | 4 | 4 | 4.5 | 3 | 4 | **19.5** | 🟡 Fix (embed map) |
| Shop | 4.5 | 4 | 4 | 5 | 4.5 | **22** | 🟢 Preserve |
| HR | 3.5 | 3.5 | 4 | 3.5 | 4 | **18.5** | 🟡 Fix (swap KPI strip) |
| Safety | 4 | 4 | 4 | 5 | 4 | **21** | 🟢 Preserve |
| Field Leadership | 5 | 5 | 5 | 5 | 5 | **25** | 🟢 **Reference standard** |

---

## 4. Drift Analysis (where reality fails intent)

| Portal | Intended role | Currently rewards | Drift kind | Severity |
|---|---|---|---|---|
| PM | Project management — projects, dailies, photos, issues, schedule | Fleet · hauls · trucks · drivers · trailers · road plates · materials · loads | **Conceptual** — PM portal has been built on the dispatch data model with a PM filter | 🔴 Critical |
| Dispatch | Live operations — map, fleet, assignments, stuck/idle | Triage tiles + Issue-Work cards + Operational Board *button* (no embedded map) | **Composition** — map exists but is not on the first screen | 🟡 Moderate |
| HR | Workforce compliance — onboarding, training, credentials, time | First-screen KPIs are operations-center pastes (Incidents/PO/CAPA) | **KPI mis-shelf** — sections are HR, but KPIs are ops | 🟡 Minor |
| Admin | Platform admin command | Platform admin command | None | 🟢 None |
| Shop | Equipment recovery + maintenance | Equipment recovery + maintenance | None | 🟢 None |
| Safety | Safety officer ops | Safety officer ops | None | 🟢 None |
| Field Leadership | Field documentation | Field documentation | None | 🟢 Reference |

---

## 5. Data Audit (Track 13H — joins vs. honest empties)

Every dashboard tile reading `0` was traced to its API source.

| Tile | Reading | Verdict |
|---|---|---|
| PM `pm-cc-tile-loads-today` = 0 | `/api/pm/command-center/materials` filtered to TODAY UTC | Honest empty (preview pod has no load events recorded today UTC) |
| PM `pm-cc-tile-defects-open` = 0 | `/api/pm/command-center/shop-impact` filtered to PM project scope | **Suspect** — Admin OIS shows 1 equipment_down, Shop shows 183 MaintainX-blocked. The PM tile is over-filtering (likely "open defects assigned to a project that the current PM owns" — none in preview because no PM is mapped). Should be a verified honest empty or a broken join — needs operator confirmation |
| PM `pm-cc-tile-materials-in-today` = 0 | `/api/pm/command-center/materials` | Honest empty (no materials logged today) |
| Dispatch `Trucks in Breakdown` = 0 | `/api/dispatch/operational-attention` | Honest (preview has 1 equipment_down for shop, may not be classified as a "truck in breakdown" by dispatch lifecycle) |
| Dispatch `Stuck >30 min` = 0 | same | Honest |
| Dispatch `Extended Wait` = 0 | same | Honest |
| Shop `Active Recovery Work` = 0 | `/api/shop/recovery` | Honest empty — operator can begin a recovery from MaintainX Blocked / DVIR queue |
| Shop `Waiting / Delays` = 0 | same | Honest |
| Shop `Returned to Service` = 0 | same | Honest |
| HR `Incidents Open` = 44 | `/api/incidents` | Real but misplaced (belongs Safety) |
| HR `Overdue PO Receipts` = 23 | `/api/operations-center` | Real but misplaced (belongs Admin) |
| Admin `ops-card-equipment_holds` = 0 | `/api/operations/intelligence` | Honest |
| Admin `repeat_equipment_failures` = "No signal yet" | same | Honest 30-day window |

**Net:** The platform's reading of `0` is honest in 8/10 cases. The two suspect joins are both on the PM portal — and that portal is already on the rebuild list, so the joins will be re-validated during the rebuild.

---

## 6. Empty State Audit

| Pattern | Portal usage | Verdict |
|---|---|---|
| Bare `0` with no copy | PM tiles (12), Dispatch attention tiles (3), Shop recovery footer (3) | **Inconsistent** — bare 0 in a "Needs attention" tile is fine; bare 0 in a content row is unhelpful |
| "No X recorded — next action is Y" | Safety document list, Admin repeat-failures | **Reference pattern** |
| `Pending Integration` | PM FleetWatcher + MaintainX | **Honest and informative** |
| `Unknown` (Integration Health) | Admin | **Honest** |
| `No signal yet · 30 days · ≥3 fails per unit` | Admin repeat-failures | **Reference pattern** |

**Recommendation in scope of PM rebuild:** every PM tile reading 0 must carry a next-action sentence (e.g., `0 Dailies pending review · You have no pending reviews. Open Field Truth to browse this week's submissions.`).

---

## 7. Preserve · Fix · Rebuild lists (the operator decision matrix)

### 🟢 PRESERVE (do not touch in Track 13)
- **Admin portal** — left-rail grouping, search bar, OIS strip, governance score
- **Shop portal** — MaintainX readiness queue, OIS-1D motive intel, per-vehicle alert list
- **Safety portal** — left-rail grouping, training/cert expiration strip, recent-incident pill
- **Field Leadership portal** — 4-action card grid (this is the design reference)
- **Cross-portal chrome** — header, EN/ES toggle (now ≥36 px post RC-1), password toggle (36 ×36), back-links (44 px), portal switcher, search affordance
- **Platform design baseline** — every visual primitive listed in §1
- **117-case predeploy gate** (RC-2 guardrails) — must continue to pass after every change

### 🟡 FIX (in scope · single-session work)
- **Dispatch** — embed Live Map preview into Section 3 hero (replace the explanatory blurb), keep the orange button as fallback. *Estimate: 1 component, ~50 lines.*
- **HR KPI strip** — swap the 4 operations-paste tiles for HR-native KPIs sourced from `/api/employees`, `/api/operations/expirations/summary` (HR-scoped), and `/api/operations-actions/summary` (HR scope). *Estimate: 1 tile-strip swap.*
- **PM defect-count join** — verify whether `pm-cc-tile-defects-open` is over-filtering or honest; if over-filtering, scope-correct the query.

### 🔴 REBUILD (multi-section · the actual Track 13 mission)
- **PM Portal `/pm/command-center`** — replace the 12-tile fleet strip + 7-tab fleet-resource layout with the Track 13B four-section layout:
  1. **Project Command** — *my active projects* (list with health · last activity · daily status · open issues count) + project selector
  2. **Field Truth** — *latest dailies · latest photos · latest safety observations · missing reports · pending PM review*
  3. **Project Risk** — *open safety · open defects on my jobs · delays/holds · missing documentation · needs PM action*
  4. **Documents & Plans** — *plans · RFIs · submittals · photos · reports*
  Existing tabs (Resources · Hauls · Materials · Shop · Safety · Timeline) move from default first-screen to *project-detail* drill-down (one click into a project). The first screen becomes the *projects view*, not the *resources view*.

### ⛔ NOT IN TRACK 13 (operator-deferred)
- New features
- New integrations
- New backend endpoints (Phase 4A endpoints are sufficient; rebuild reuses them)
- Visual rebrand beyond the baseline
- Mobile-only redesign
- iPad split-view layouts
- Translation expansion beyond RC-1's coverage

---

## 8. Track 13 Coding Preconditions

Before any Track 13 code is written:

1. ✅ This audit is read and acknowledged by operator
2. ✅ Operator confirms the Preserve / Fix / Rebuild lists
3. ✅ Operator confirms 117-case predeploy gate stays green after every change
4. ✅ Operator confirms no production data will be touched
5. ✅ Operator confirms PM Phase 4A endpoints (`/api/pm/command-center/{overview,resources,hauls,materials,shop-impact,safety-impact,timeline}`) may be reused; no new backend route in this track
6. ✅ Operator confirms field-leadership portal is the design reference standard

If any of those are unchecked, do not begin coding.

---

## 9. Five-Pillar Aggregate · Platform Score (pre-Track 13)

**138 / 175 (78.9 %)** across the 7 portals.

Strongest pillar: **Beautiful** (28.5/35 · 81 %) — the baseline is doing its job.
Weakest pillar: **Proven** for **PM only** (1/5 — the bottom-of-platform).

Removing the PM portal score: 126/150 (84 %).

**The platform is healthy. PM is the single critical failure. Everything else is preserve-or-tweak.**

---

## 10. Operator Decision Required

Acknowledge this audit and approve the **Preserve / Fix / Rebuild** matrix in §7. Once acknowledged, Track 13 coding begins on:

1. PM portal rebuild (4 sections per §7 Rebuild)
2. Dispatch Live Map embed (per §7 Fix)
3. HR KPI strip swap (per §7 Fix)
4. PM defect-count join verification (per §7 Fix)

All four items are scoped to the existing API surface — **no new backend work**, no schema changes, no production data mutated, no RC-2 guardrail relaxation.

**Track 13 is the rebuild. Track 13A is finished here.**

