# MASCI Portal Target State Matrix

**Track 13.5C · Per-Portal Target State**
**Mode:** Architecture only — no implementation.
**Generated:** 2026-06-12 (UTC)

> Defines, per portal: Purpose · Primary operator · First-screen objective · Above-the-fold content · What belongs here · What does not belong · KPI expectations · Workflow expectations · Five-Pillar target score. Citations link back to the reality matrices.

---

## 1. Admin Portal

| Field | Target |
| --- | --- |
| **Purpose** | Configure the platform · seed data · supervise platform health · admit operators · audit security |
| **Primary operator** | Super-admin · Admin (limited) |
| **First-screen objective** | "Is the platform healthy and is anyone locked out who shouldn't be?" |
| **Above the fold** | One Platform-Health card (rolling 4-page collapse into sub-tabs — H-5) · Recent admin actions feed · 2 primary actions max (`New Operator` / `Open Operations Center`) |
| **Belongs here** | Job CRUD · operator CRUD · MFA + recovery · integrations · backup health · scheduler audit · compliance roll-up · legacy import · training-video catalog · QA/QC inventory · asset mapping · termination orchestration · deploy readiness gate |
| **Does NOT belong here** | Operator workflows (Daily Report submission · Incident reporting · Dispatch assignment); these belong to the role portals. Coaching authoring (belongs in renamed Guidance surface). |
| **KPI expectations** | Backups (R2) · scheduler last-run · MFA enrollment % · open compliance findings · pending operator approvals · platform feed_status |
| **Workflow expectations** | Admin verifies platform state and admits operators; never operates field workflows |
| **Five-Pillar target** | Powerful 10 · Simple 9 · Beautiful 9 · Trusted 10 · Proven 9 |

---

## 2. Dispatch Portal

| Field | Target |
| --- | --- |
| **Purpose** | Place crews and equipment on jobs with real-time visibility |
| **Primary operator** | Dispatcher · Super-admin (oversight) |
| **First-screen objective** | "Where is every crew right now, and what needs me in the next hour?" |
| **Above the fold** | Live fleet map at ≥ 60% viewport height (iPad landscape verified by 13.4A guardrail) · Assignment board collapsed pulse (3 cards: open assignments · stale feeds · safety holds) · 2 primary actions max (`New Assignment` / `Drivers`) |
| **Belongs here** | Live map · assignment board · driver profile + qualification · ELD/HOS read · stale-feed surfacing · severity-coded alerts |
| **Does NOT belong here** | PM-level project drill · safety form authoring · HR onboarding · admin scheduler |
| **KPI expectations** | Crews in field (live count) · stale-position assets (D-03 / D-06) · ELD violations (live) · open assignments · feed health (D-01 visible per source) |
| **Workflow expectations** | Operator can re-assign equipment to a crew in < 30 s; can drill from a stale chip to the underlying asset in 1 click |
| **Five-Pillar target** | Powerful 10 · Simple 9 · Beautiful 9 · Trusted 10 · Proven 10 |

---

## 3. PM Portal

| Field | Target |
| --- | --- |
| **Purpose** | Run the project book: surface holds, verify field work, escalate cleanly |
| **Primary operator** | Project Manager |
| **First-screen objective** | "What's at risk on my projects today, and what needs my signature?" |
| **Above the fold** | 4-card pulse (Active Projects · Crews in Field · **Open Holds** · Due Today) · Project list (top 5 by health severity) · 2 primary actions (`New RFI` deferred to backlog · `Open Command Center`) |
| **Belongs here** | Project list (scoped via `co_pm_emails`) · per-project health drill · Daily Reports verify · Incidents read + verify · **PM-scoped CAPA list** (closes U-01) · Photos · crew compliance · field-leadership read · fleet read · holds aggregation |
| **Does NOT belong here** | Job CRUD (Admin) · dispatcher's live map (referenced but not duplicated) · HR termination flow · safety-forms authoring · ODR issuance (Operator) |
| **KPI expectations** | Active project count · crews in field · open holds (unified across engines — H-8) · due today · daily-report verification queue depth |
| **Workflow expectations** | One-click drill from any pulse card to the underlying record; verify-or-revise on a Daily Report in ≤ 3 clicks |
| **Five-Pillar target** | Powerful 10 · Simple 9 · Beautiful 9 · Trusted 10 · Proven 9 |

---

## 4. Safety Portal

| Field | Target |
| --- | --- |
| **Purpose** | Operate the safety system: forms, JHA, posters, trench safety, training |
| **Primary operator** | Safety Manager · field operators (forms only) |
| **First-screen objective** | "What unsafe conditions are open right now, and what training/forms are due?" |
| **Above the fold** | Open Safety Holds + open Equipment-Out-of-Service · Today's training due · Recent QR / public surface usage |
| **Belongs here** | Safety form hub (EN/ES) · JHA plans · trench-safety module · field safety cards · public QR landings · posters · safety-meeting registry · training-by-discipline |
| **Does NOT belong here** | Job CRUD · dispatcher's map · termination flow · ODR issuance |
| **KPI expectations** | Open safety holds · CAPA aging · training currency by crew · ES-translation completeness (T-01..T-07 currency) |
| **Workflow expectations** | Safety Manager can lift a hold in ≤ 5 clicks; field operator can submit Equipment Issuance in ≤ 90 s on phone |
| **Five-Pillar target** | Powerful 10 · Simple 10 · Beautiful 10 · Trusted 10 · Proven 10 (Trench Safety is the reference benchmark) |

---

## 5. Shop Portal

| Field | Target |
| --- | --- |
| **Purpose** | Run equipment maintenance · respond to repair requests · manage parts/service holds |
| **Primary operator** | Shop Mechanic · Shop Lead |
| **First-screen objective** | "What broke, what's down, what do I work on next?" |
| **Above the fold** | Equipment down (count + worst-severity card) · Open repair queue · Today's scheduled service |
| **Belongs here** | Repair queue · equipment-maintenance log · parts inventory link · maintenance-hold lifecycle |
| **Does NOT belong here** | Job CRUD · PM project drill · termination flow · safety-forms authoring |
| **KPI expectations** | Equipment in maintenance · average down-time · open repair tickets · backlog age |
| **Workflow expectations** | Mechanic can move a repair from Submitted → Verified in ≤ 4 clicks |
| **Five-Pillar target** | Powerful 9 · Simple 10 · Beautiful 9 · Trusted 10 · Proven 9 |

---

## 6. HR Portal

| Field | Target |
| --- | --- |
| **Purpose** | Onboard · offboard · manage personnel · monitor field health · respect privacy |
| **Primary operator** | HR Manager · HR Coordinator |
| **First-screen objective** | "Who is starting, who is leaving, and what crew-health flags need follow-up?" |
| **Above the fold** | This week's onboards · this week's offboards · open HR-relevant incidents (read-only) · pending compliance training |
| **Belongs here** | Onboarding · terminations · personnel CRUD · daily-report read · incidents read (HR view) · digest config · MFA |
| **Does NOT belong here** | Operator workflows (Daily Report submit · Incident submit) · dispatcher map · job CRUD |
| **KPI expectations** | Onboards/week · offboards/week · open termination tasks · compliance-training currency |
| **Workflow expectations** | HR can initiate an offboard packet in ≤ 5 clicks; can read but never edit field engine records |
| **Five-Pillar target** | Powerful 10 · Simple 10 · Beautiful 10 · Trusted 10 · Proven 10 (HR is the second reference benchmark) |

---

## 7. Field Leadership Portal

| Field | Target |
| --- | --- |
| **Purpose** | Supervise crews from the field; submit / verify field records on phone or iPad |
| **Primary operator** | Superintendent · General Foreman |
| **First-screen objective** | "What is my crew submitting today, what needs my verify, and is there a safety flag?" |
| **Above the fold** | Today's daily-report status (per crew) · open safety items · 2 primary actions (`New Daily Report` / `New Incident`) |
| **Belongs here** | Daily Reports · Site Inspections · Incidents · QA/QC submissions · trench-safety field forms · equipment issuance / return · crew composition · field safety cards |
| **Does NOT belong here** | Admin · job CRUD · PM project drill (read-only allowed) · HR data |
| **KPI expectations** | Daily reports per crew today · open incidents · open QA/QC · safety holds on my crews |
| **Workflow expectations** | Phone-first; offline-capable for Daily Report + Equipment Issuance (queued sync ≤ 30 s) |
| **Five-Pillar target** | Powerful 9 · Simple 10 · Beautiful 9 · Trusted 10 · Proven 9 |

---

## 8. Leadership Portal (Executive)

| Field | Target |
| --- | --- |
| **Purpose** | Read-only weekly + monthly executive view of operational reality |
| **Primary operator** | C-suite · operations director |
| **First-screen objective** | "Is the company operating safely and profitably this week?" |
| **Above the fold** | One safety chart (incidents · holds) · one operations chart (jobs in motion · crew utilization) · one trust chart (verification queue depth · stale feeds) |
| **Belongs here** | Roll-up dashboards · weekly KPI · monthly trend · safety performance · operational reality summary |
| **Does NOT belong here** | Any operator workflow · job CRUD · personnel detail · raw engine data |
| **KPI expectations** | Trailing 7-day and 30-day rollups only. No real-time live charts (executive doesn't need 1-Hz refresh) |
| **Workflow expectations** | Zero writes. Read-only with export to PDF/Excel (locale-aware per T-08/T-10) |
| **Five-Pillar target** | Powerful 9 · Simple 10 · Beautiful 10 · Trusted 10 · Proven 9 |

---

## 9. Driver Portal

| Field | Target |
| --- | --- |
| **Purpose** | Driver self-service: shift, qualification, time, simple submissions |
| **Primary operator** | Driver |
| **First-screen objective** | "What's my shift today, am I qualified for it, and how do I clock in?" |
| **Above the fold** | Today's shift card (truck, route, start time) · Qualification chip · Single primary action (`Start Shift`) |
| **Belongs here** | DriverHub landing (closes V-15 / R-13) · DriverShift · ShiftStart · DriverQualification self-view · magic-link sign-in path |
| **Does NOT belong here** | PM data · admin data · safety form authoring · job CRUD |
| **KPI expectations** | Personal-only: my next shift · my qualification expiry · my recent submissions |
| **Workflow expectations** | Phone-only is acceptable. Magic-link sign-in is preferred. Start Shift in ≤ 2 taps |
| **Five-Pillar target** | Powerful 9 · Simple 10 · Beautiful 9 · Trusted 10 · Proven 9 |

---

## 10. Cross-portal alignment summary

| Portal | Today's avg score (13.5B) | Target avg score (13.5C) | Gap to close |
| --- | :-: | :-: | :-: |
| Trench Safety module | 8.8 | 10.0 | 1.2 |
| HR | 8.4 | 10.0 | 1.6 |
| Dispatch | 7.8 | 9.6 | 1.8 |
| PM | 7.2 | 9.6 | 2.4 |
| Safety (forms hub) | 7.2 | 10.0 | 2.8 |
| Shop | 6.8 | 9.4 | 2.6 |
| Admin | 6.8 | 9.4 | 2.6 |
| Field Leadership | 6.2 | 9.4 | 3.2 |
| Driver | 5.2 | 9.4 | 4.2 |

**Platform target average: ~9.6 / 10** (some 10/10 ceilings, some 9-10 honest targets where regulatory / external constraints prevent perfection).

---

## 11. Standing rules

No deploy. No GitHub save. No merge. This matrix is the **destination**, not the journey. The journey is sequenced by `MASCI_REALITY_GAP_PRIORITY_LIST.md` and authorized one phase at a time.
