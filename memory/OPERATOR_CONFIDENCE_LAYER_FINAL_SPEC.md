# OPERATOR CONFIDENCE LAYER · FINAL SPECIFICATION
## OCEP Operational Completion Sprint · Phase 4

**Date**: 2026-06-02
**Authority**: OMEGA · OPERATIONAL COMPLETION SPRINT
**Mode**: READ-ONLY · operational specification (NOT a build authorization)
**Status**: FINAL · supersedes prior `OPERATOR_CONFIDENCE_LAYER_SPECIFICATION.md` as the canonical reference
**Scope**: Define operator confidence per role · evidence-anchored · doctrine-bound

---

## 0 · Doctrine

> Every role must be able to answer: **Am I good?**
> In ≤ 3 seconds. On the device they actually use.
> With one click — at most — to act on whatever isn't good.

That is the entire job of the Operator Confidence Layer. Nothing else.

If the platform already answers "Am I good?" for a role through existing surfaces (Hubs, inline alerts, status pills, recovery stream, lifecycle panels), then **NO BUILD IS REQUIRED** for that role. The Confidence Layer is **role-conditional**, not universal.

---

## 1 · What Operator Confidence IS

| Property | Specification |
|---|---|
| One sentence answer | A single line at top of role's primary hub: "You're good." / "X needs attention." / "Y is blocking." |
| Role-scoped | HR token → HR view · PM token → PM view · etc. Never aggregated across roles in a single render. |
| Action-tied | Every red/yellow indicator is itself a tappable link to the surface where the action is taken. |
| Evidence-derived | Every indicator derives from EXISTING collections. Zero new schema, zero new statuses. |
| Latency | ≤ 500ms p95 first render (single round-trip · cached server-side · pattern: `/api/admin/recovery/snapshot` 15s TTL) |
| Polling | None. Refresh on navigation or pull-to-refresh. |
| Personalization | Identity-scoped by token; not switchable per session. |
| Internationalization | Bilingual for **Laborer + Foreman ONLY**. Other roles English-canonical. |
| Print | Hidden in print views. |
| Surface | Inline strip at top of role's hub page. NOT a separate page. |
| Empty state | "Nothing requires your attention." (Quiet · NOT a marketing welcome.) |
| Failure mode | Quiet text fallback; never blocks hub render. |

---

## 2 · What Operator Confidence MUST NEVER BECOME

Binding list. If a future proposal falls under any of these, it is **OUT OF SCOPE** by definition and must be refused.

- ❌ A dashboard with KPIs, sparklines, heatmaps, donut charts, or vanity numbers
- ❌ Business intelligence
- ❌ Analytics
- ❌ A "dashboard of dashboards"
- ❌ Trends over time
- ❌ Employee leaderboard / scorecards comparing operators
- ❌ Surveillance — tracking individual operator activity
- ❌ Background-polling surface that drains field device battery
- ❌ A separate login / app
- ❌ A surface that surfaces information the role doesn't own
- ❌ Anything introducing new statuses, lifecycle states, or collections
- ❌ A "build everywhere because it would be nice" universal layer (must be role-conditional)
- ❌ A surface that requires AI inference to render
- ❌ A surface whose primary purpose is presentation, not action

If a future directive uses any of these terms, the AI agent pauses and re-confirms what's actually being requested:
- "Executive dashboard" → BI · out of scope
- "Real-time alerts" → notification surface · different feature
- "Custom views per user" → personalization · different feature
- "AI-generated insights" → out of scope
- "Weekly digest" → already exists (`operator_digest` cron)

---

## 3 · The four confidence components (per role)

| Component | Definition | Source rule |
|---|---|---|
| **Inputs** | Existing fields / statuses / expirations from existing collections that drive the indicator | NO new schema. Every input must be a citable existing field. |
| **Outputs** | The one-sentence answer + a small set of action-tied bullet items | At most 3 bullets per role. Each bullet is a tappable deep link. |
| **Indicators** | GREEN / YELLOW / RED per role | Defined per role in §4. |
| **Ownership** | Which role OWNS each indicator. Cross-role obligations NEVER shown on a role whose action cannot resolve them. | A PM does not see HR's expiring W-4s. HR does not see Shop's open defects. |
| **Escalation** | The pre-defined path from RED on one role to the role that can resolve it | Defined per role in §5. |
| **Thresholds** | Numeric definitions of GREEN/YELLOW/RED boundaries | Defined per role in §4. |

---

## 4 · Per-role confidence model (8 roles · final)

### 4.1 · LABORER
| Field | Specification |
|---|---|
| **Inputs (existing)** | `jha_acknowledgements` (today's job) · `equipment_inspections` (assigned equipment) · `safety_training_records` (their expirations) |
| **Outputs** | One sentence + up to 2 bullets |
| **GREEN** | Today's JHP for assigned job acknowledged · pre-shift complete on assigned equipment · no expired training |
| **YELLOW** | Training expires within 7 days · pre-shift pending |
| **RED** | Today's JHP NOT acknowledged OR training expired today OR assigned equipment has open Red-severity defect |
| **One-sentence** | GREEN: "You're good for today." · RED: "Sign today's JHP." |
| **Ownership** | Laborer · their own attestations only |
| **Escalation** | If JHP roster gap → Foreman (Foreman sees the gap, Laborer sees their own missing ack) |
| **Bilingual** | YES (EN + ES) |

### 4.2 · FOREMAN
| Field | Specification |
|---|---|
| **Inputs** | `daily_reports` (today's, status) · `jha_acknowledgements` (entire crew on today's job) · `equipment_inspections` (assigned units) · `incidents` (open on their job) |
| **GREEN** | Today's DR not yet due OR in OPEN/PENDING_REVIEW · all crew acknowledged today's JHP · no open incidents > 24h on this job |
| **YELLOW** | DR bounced back (PENDING_REVIEW → OPEN with reason) · ≥ 1 crew member missing JHP ack · open incident 12–24h |
| **RED** | DR overdue · ≥ 2 crew missing JHP ack · open incident > 24h |
| **One-sentence** | GREEN: "Crew is good. Submit today's DR by 5pm." |
| **Ownership** | Foreman · only role that aggregates over a CREW |
| **Escalation** | RED → Superintendent (super sees foreman's REDs as their yellows) |
| **Bilingual** | YES |

### 4.3 · SUPERINTENDENT
| Field | Specification |
|---|---|
| **Inputs** | `daily_reports` (all jobs they cover) · `incidents` (open across all jobs) · `equipment_inspections` (cross-job) · `operational_constraints` (open across their jobs) |
| **GREEN** | 0 stuck DRs · 0 incidents > 24h · 0 critical constraints unresolved |
| **YELLOW** | Any DR PENDING_REVIEW > 48h · any incident OPEN > 12h · any constraint > 72h |
| **RED** | Any DR PENDING_REVIEW > 72h · any incident OPEN > 24h · constraint blocking production |
| **One-sentence** | GREEN: "All 4 jobs are good." · RED: "3 items blocking — tap to clear." |
| **Ownership** | Super · aggregates Foreman-level REDs · does NOT show PM-only obligations |
| **Escalation** | Super RED → PM (PM sees super's REDs as escalations on PM's jobs) |
| **Bilingual** | NO (English-canonical) |

### 4.4 · PROJECT MANAGER
| Field | Specification |
|---|---|
| **Inputs** | `corrective_actions` (owned) · `incidents` (on their jobs) · `daily_reports` (closed status) · `jha_acknowledgements` (project-level compliance) · `operational_constraints` (their jobs) |
| **GREEN** | 0 CAPAs overdue · all DRs closing on schedule · JHP coverage ≥ 90% per project |
| **YELLOW** | ≥ 1 CAPA due ≤ 3 days · DR closure rate < 90% · JHP coverage 70–89% |
| **RED** | ≥ 1 CAPA overdue · ≥ 1 DR stuck in CLOSED-back-to-PENDING_REVIEW loop · JHP coverage < 70% |
| **One-sentence** | GREEN: "All 3 jobs healthy." · RED: "1 overdue CAPA on Job 2024-101." |
| **Ownership** | PM · cross-job |
| **Escalation** | PM RED → Safety (for safety-class CAPAs) OR Executive (for production-class) |
| **Bilingual** | NO |

### 4.5 · SAFETY MANAGER
| Field | Specification |
|---|---|
| **Inputs** | `incidents` (cross-platform) · `qaqc_inspections` · `inspections` · `corrective_actions` · `jha_acknowledgements` (compliance roll-up) · `safety_training_records` (expirations) |
| **GREEN** | 0 OSHA recordables OPEN/UNDER_INVESTIGATION > 24h · 0 deficiencies overdue · 0 unauthorised closures (Amendment 001 violations are code-impossible) |
| **YELLOW** | Incident UNDER_INVESTIGATION 12–24h · deficiency PENDING_RE_INSPECTION > 7 days · JHP roster gap on mobilising job |
| **RED** | OSHA recordable OPEN > 24h · deficiency overdue (Amendment 001 thresholds) · training expirations ignored > 30 days |
| **One-sentence** | GREEN: "Safety posture is good." · RED: "1 OSHA recordable needs investigation." |
| **Ownership** | Safety · this is the ONLY role whose RED auto-escalates to Executive |
| **Escalation** | Safety RED → Executive AND PM (whichever job is affected) |
| **Bilingual** | NO |

### 4.6 · DISPATCH
| Field | Specification |
|---|---|
| **Inputs** | `dispatch_assignments` (today + tomorrow) · `driver_qualifications` (CDL / medical expirations) · `equipment_inspections` (offline) · `incidents` (driver-involved) |
| **GREEN** | Tomorrow's board complete · 0 drivers with expirations < 30 days · 0 equipment offline overnight without backup |
| **YELLOW** | Tomorrow's board < 90% complete by 3pm · driver expiration 8–30 days · equipment offline overnight with backup |
| **RED** | Tomorrow's board < 70% by EOD · driver expiration < 7 days · equipment offline with no backup |
| **One-sentence** | GREEN: "Tomorrow is set." · YELLOW: "2 drivers expire next week — confirm or reroute." |
| **Ownership** | Dispatch |
| **Escalation** | Dispatch RED on driver qualification → HR (HR owns the qualification record); Dispatch RED on equipment → Shop |
| **Bilingual** | NO |

### 4.7 · HR
| Field | Specification |
|---|---|
| **Inputs** | `employees.lifecycle_status` · `payroll_variance_batches` (lifecycle_state) · `employee_requests` (queue) · `driver_qualifications` (HR-side records) · `safety_training_records` (HR-owned) |
| **GREEN** | Last week's payroll variance FINALIZED · 0 employee requests > 5 days · 0 training expiring < 7 days |
| **YELLOW** | PV APPROVED but not FINALIZED > 24h · employee request 3–5 days · training expiring 7–14 days |
| **RED** | PV stuck > 7 days · employee request > 7 days · expired training still active |
| **One-sentence** | GREEN: "HR is good through Friday." · RED: "Finalize last week's variance." |
| **Ownership** | HR |
| **Escalation** | HR RED on PV stuck > 7 days → Admin (Admin finalizes per `_PV_ROLES` `FINALIZE` lane) |
| **Bilingual** | NO |

### 4.8 · EXECUTIVE
| Field | Specification |
|---|---|
| **Inputs** | Roll-up of Safety RED + PM RED + HR RED + Dispatch RED + Shop RED · `backup_health` posture · scheduler liveness |
| **GREEN** | 0 role-level REDs across the platform · last backup within RPO · scheduler alive |
| **YELLOW** | 1–2 role-level REDs, none safety |
| **RED** | ANY safety RED OR ≥ 3 role-level REDs simultaneously OR backup posture RED OR scheduler dead |
| **One-sentence** | GREEN: "Everything is good." · RED: "1 safety RED needs your attention." |
| **Ownership** | Executive · roll-up only · cannot drill into individual operator activity |
| **Escalation** | N/A · Executive is the top |
| **Hard rule** | Executive view NEVER shows individual employee records by name. Aggregated counts + links into responsible role's surface. Preserves the "coaching, not policing" doctrine. |
| **Bilingual** | NO |

---

## 5 · Escalation matrix (cross-role)

| FROM (role with RED) | TO (role with the resolution authority) | Mechanism |
|---|---|---|
| Laborer | Foreman | Foreman's roster check surfaces the gap |
| Foreman | Superintendent | Super's cross-job view surfaces foreman REDs as super's YELLOWs |
| Superintendent | PM | PM's job-level view surfaces super REDs as PM's reds-on-that-job |
| PM | Safety / Executive | Safety-class CAPAs → Safety · production-class → Executive |
| Safety | Executive + affected PM | Auto-escalate · the ONLY role whose RED auto-escalates two ways |
| Dispatch | HR (qualifications) + Shop (equipment) | Domain-specific |
| HR | Admin (PV finalize) + PM (RTW return-to-work) | Domain-specific |
| Executive | — | Top of escalation |

No escalation introduces new statuses or new collections; all escalations are already representable in existing audit events (`workflow_state_events`).

---

## 6 · Authorization gates (6 · all must pass per-role before any build)

| Gate | Evidence required (per role) |
|---|---|
| G1 | Phase 1 interview shows the role cannot answer "Am I good?" in ≤ 3 seconds on existing surfaces |
| G2 | Phase 2 audit confirms no existing surface ALREADY answers it that operators are simply not trained on |
| G3 | Proposal passes all 7 OCEP acceptance tests |
| G4 | Proposal passes all 4 FOCP pre-authorization proofs (does not exist · users need it · simplifies operations · will be used) |
| G5 | Proposal derives ONLY from existing collections — no new schema, no new statuses |
| G6 | Proposal does not violate §2 (the MUST-NEVER-BECOME list) |

All 6 gates must pass per role. Roles pass independently. A passing role moves to design (NOT build) authorization. Building requires a separate explicit operator directive.

---

## 7 · Implementation reference architecture (READ-ONLY guidance · NOT a build authorization)

If/when an authorized role advances to design, the canonical pattern is:

| Layer | Existing parallel | Notes |
|---|---|---|
| Cached snapshot read | `/api/admin/recovery/snapshot` (15s TTL) | Same pattern: cached at server, single round-trip, role-scoped |
| Audit derivation | `workflow_state_events` reads | Re-uses Phase 1A audit substrate |
| Inline strip render | Pattern of `<HelpTipBlock>` (collapsible, mobile-first) | Component-shape reference only |
| Bilingual surfacing | i18n.js with `useT()` | Existing pattern |
| Identity scoping | `require_admin` / `require_pm` / `require_safety_or_hr_or_admin` | Existing dependency injectors |

No new infrastructure. All four layers exist today.

---

## 8 · Refusal conditions

The AI agent MUST refuse to:
- Build the Confidence Layer for any role without all 6 gates documented as passed
- Build a "platform-wide" Confidence Layer in a single iteration (intentionally role-by-role)
- Add ANY indicator that doesn't derive from an existing collection
- Add an analytics / trends-over-time / leaderboard view to the Confidence Layer
- Treat "Operator Confidence" as a feature pitch · it is a doctrine

---

**End of OPERATOR CONFIDENCE LAYER · FINAL SPECIFICATION · OCEP Phase 4**
