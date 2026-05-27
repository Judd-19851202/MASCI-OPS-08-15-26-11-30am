# Cross-Portal Operator Atlas

*Phase IV-BETA.3-P1A · iter437 · 2026-02-27*
*Status: 🟢 OPERATIONAL · printable · field-usable · audit-grade*
*Verification legend: 🟢 VERIFIED · 🟡 ASSUMED · ⚪ UNTESTED*

> A single operational reference showing where each concern lives across
> the MASCI ecosystem. **Not** marketing material. **Not** an org chart.
> This is the laminated page a foreman, an HR clerk, or a new auditor
> can keep at hand to answer the question **"where do I go?"** before
> opening any portal.

---

## I. Side-by-side domain maps (🟢 VERIFIED · matches shipping V2 sidebars)

| # | **Admin** | **PM** | **HR** |
|---|---|---|---|
| 1 | Platform Governance | Project Operations | People Operations |
| 2 | System Operations | Financials & Cost | Time & Payroll |
| 3 | Backup & Recovery | Field Coordination | Compliance & Records |
| 4 | Portal Access & Identity | Document Control | Access & Identity |
| 5 | Infrastructure Health | Compliance & Risk | Guidance |
| 6 | (— · admin-only) | System & Communications | (— · n/a) |

### Per-domain detail

| Domain | Admin contents | PM contents | HR contents |
|---|---|---|---|
| **People / Project ops** | Master employee + supplier rosters · job master | Overview · Jobs (read-only) · Daily Reports · Inspections · Meetings · Field Leadership · Job Photos | Overview · Employee Lifecycle · Employee Accountability · Field Leadership |
| **Financial / Time** | PO governance · payroll variance audit | PO Requests · Project Health · Asset Transfers | Time Verification · Payroll Variance · Time Off · PO Requests |
| **Field / Compliance** | Equipment master · Status Board · Parts catalog · Compliance Export | Equipment Fleet (read-only) · Pre-Op Checks · Suppliers (read-only) · People (read-only) | Document Expirations · Training Records · Driver Qualification · Safety Records · Daily Reports (read-only) |
| **Documents** | JHA admin · trench-box admin · poster admin | JHA Plans · Trench Boxes · Site Posters | (handled via Safety / HR docs) |
| **Access / Identity** | All user provisioning (Admin/PM/HR/Safety/Dispatch/Shop/FL) | (— · operator-level only · change password) | FL Portal Accounts · Change Password |
| **System & Comm** | Email Routing · System Health · Deploy Readiness | Change Password | (inherits Admin comm doctrine) |

---

## II. Operational purpose by portal

| Portal | Operational purpose | Primary operator type |
|---|---|---|
| **Admin** | Govern the platform itself: identities, masters, system health, comm routing, backups. | Office / executive |
| **PM** | Run a project on the ground: file daily reports, raise POs, manage crews, file incidents and JHAs, watch project health. | Project Managers (assigned scope) |
| **HR** | Govern the workforce: hire, accountability, payroll cross-check, certifications, training, FL portal access. | HR staff (office) |
| **Safety** ⚪ pending V2 | Inspect, investigate, audit, train, document safety. | Safety officers |
| **Dispatch** ⚪ pending V2 | Allocate trucks, drivers, daily schedule, driver-qual gating. | Dispatchers |
| **Field Leadership** ⚪ pending V2 | Crew-level day-of operations: pre-shift docs, attendance, incident upload from the field. | Foremen / superintendents |

---

## III. "Where should I go?" matrix (🟢 VERIFIED)

| If you need to … | Go here |
|---|---|
| File a daily production report | **PM** → Daily Reports |
| Approve a PO | **HR** (office) or **PM** (project) → PO Requests |
| Add a new employee | **HR** → Employee Lifecycle |
| Reset a PM's password | **Admin** → Project Managers |
| Reset an HR / FL / Safety / Shop / Dispatch user's password | **Admin** → that portal's user panel |
| See jobs assigned to you (as PM) | **PM** → Jobs (read-only) |
| File an incident | **PM** → Incidents (or **Safety** when V2 ships) |
| Pull a compliance export | **Admin** → Compliance Export |
| Run a payroll cross-check | **HR** → Time Verification → Payroll Variance |
| Provision a Field-Leadership login | **HR** → FL Portal Accounts |
| Take a backup / restore | **Admin** → Backup & Recovery (admin-strict) |
| Check platform health | **Admin** → Infrastructure Health |
| Manage equipment master | **Admin** → Equipment Master (PMs see read-only via PM Fleet) |
| Order parts for a unit | **Shop** → Equipment Parts → Order |
| Set up email routing rules | **Admin** → Auto-Email Routing |
| View a PM's project P&L | **Admin** → PNL (or PMs via PM Hub overview · scoped) |

---

## IV. Escalation routing (🟢 VERIFIED · matches comm doctrine A.III tiers)

| Trigger | First responder | Email tier | Subject prefix |
|---|---|---|---|
| Severe incident | Site Safety → PM → HR | severe | `🚨 SEVERE INCIDENT` |
| Equipment pre-op fail | Shop Manager → PM | severe | `⚠ EQUIPMENT FAIL` |
| Platform outage | Admin (on-call) | severe | `🚨 PLATFORM OUTAGE` |
| System health failure | Admin (on-call) | severe | `🚨 HEALTH FAIL` |
| Backup verification failure | Admin | severe | `🚨 BACKUP VERIFICATION FAILED` |
| PO awaiting approval | PM / HR | action-required | `[MASCI · PO]` |
| Daily report submitted | PM (+CC scope) | routine | `[MASCI · DAILY]` |
| Inspection submitted | PM (+CC scope) | routine | `[MASCI · INSP]` |
| Welcome / password reset | the affected user | routine (account) | `[MASCI · ACCESS]` |
| Parts order | Shop Manager + warehouse | routine | `[MASCI · PARTS]` |
| Weekly PO digest | PMs + HR | routine | `[MASCI · PO] · YYYY-MM-DD` |
| Weekly backup verification | Admin | routine (pass) / severe (fail) | `[MASCI · BACKUP]` / `🚨 …` |

---

## V. Portal-boundary doctrine (🟢 VERIFIED · iter180 + iter437)

| Token | Allowed namespace | Forbidden namespace |
|---|---|---|
| `X-Admin-Token` | every `/api/...` | (nothing) |
| `X-PM-Token` | `/api/pm/*` · `/api/<public>/*` · `/api/<shop-or-admin>/*` | `/api/admin/*` |
| `X-HR-Token` | `/api/hr/*` · `/api/<public>/*` | `/api/admin/*` |
| `X-Safety-Token` | `/api/safety-portal/*` · `/api/<public>/*` | `/api/admin/*` |
| `X-Dispatch-Token` | `/api/dispatch/*` · `/api/<public>/*` | `/api/admin/*` |
| `X-Shop-Token` | `/api/<shop-or-admin>/*` · `/api/<public>/*` | `/api/admin/*` |
| `X-FL-Token` | `/api/field-leadership/portal/*` | `/api/admin/*` |

**One rule, no exceptions:** `/api/admin/*` is strict-admin. No
per-portal bypass. The frontend never points a non-Admin token at
`/api/admin/*` — this is enforced by `test_portal_token_routing.py`
and rewatch by `pre_deploy_check.sh stage_portal_auth_routing`.

---

## VI. "What DOES NOT belong here" (🟢 explicit anti-pattern matrix)

| Portal | Does NOT belong |
|---|---|
| **Admin** | Day-to-day project work (use PM). Operational reports filed by field crews (those land in PM via public submit). |
| **PM** | Master-list edits (Admin only). Email routing rule edits (Admin only). Backup / restore (Admin-strict only). Compliance exports (Admin only). Per-account password rotation of other users (Admin only). |
| **HR** | Project work (PM). Daily Report edits (read-only in HR). Safety investigation primary ownership (Safety). Dispatch board work (Dispatch). Admin-namespace anything. |
| **Safety** ⚪ | Project ownership (PM). Payroll (HR). Admin-namespace anything. |
| **Dispatch** ⚪ | Project ownership (PM). Payroll (HR). Driver-qualification edits (HR). |
| **FL Portal** ⚪ | Admin work. Master edits. HR-payroll work. Other operators' records. |

If a tile, button, or panel surfaces in a portal it doesn't belong to,
treat it as a regression and route to the iter437 fix pattern
(`PORTAL_AUTH_TOKEN_AUDIT.md` §3).

---

## VII. Onboarding quick-reference

**Day-1 PM:** sign in at `/pm/login` → land on `/pm` overview → check
"Jobs Assigned to You" first → file your first daily report via `/pm/daily`.

**Day-1 HR clerk:** sign in at `/hr/login` → land on `/hr` hub → start
the day at "Document Expirations" (top of Compliance & Records) →
weekly cycle: Time Verification → Payroll Variance → PO Requests.

**Day-1 Admin:** sign in at `/admin/login` → land on Admin hub →
review "Infrastructure Health" first → spend ≤5 minutes on
"Deploy Readiness" before clicking anything in the masters.

**New auditor:** read **§I** + **§V** of this Atlas before opening
any portal. Most "where is …?" questions are answered there.

---

## VIII. Mobile considerations (🟢 VERIFIED)

| Surface | Mobile pattern |
|---|---|
| Admin V2 sidebar | Collapses to hamburger; routes scroll-locked above iOS safe area |
| PM V2 sidebar | Same pattern — verified by `test_pm_mobile_nav_scroll_v2.py` |
| **HR V2 sidebar** | Hidden at `<lg` widths; tile-grid retained for narrow viewports (intentional — sidebar is desktop optimisation) |
| All hubs | 1-column grid `<sm` · 2-column `sm+` · controls collapse via `hidden sm:flex` |
| Severe-tier emails | Body bodies render readable on iOS Mail at 375px width (PM gold standard preserved) |

---

## IX. Doctrine reaffirmed

- ✅ Atlas is a **reference**, not a redesign. No surface was changed
  for this document.
- ✅ Every surface mentioned has a verified 🟢 source (sidebar map,
  audit doc, certification doc, or shipping code).
- ✅ Items marked ⚪ are pending portals (Safety / Dispatch / FL).
- ✅ Printable as one double-sided page (recommended pre-flight check
  for new office staff and new field foremen).
