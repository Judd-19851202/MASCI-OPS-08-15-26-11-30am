# OPERATOR CONFIDENCE LAYER SPECIFICATION
## OCEP Phase 4 · Operational Completion Evidence Program

**Date opened**: 2026-06-02
**Authority**: OMEGA · OCEP
**Mode**: READ-ONLY · scope definition (NOT a build authorization)
**Status**: Specification only · unlock requires Phase 1 + Phase 2 evidence
**Scope**: Define what Operator Confidence is, role-by-role · define what it MUST NEVER become

---

## 0 · Doctrine

The Operator Confidence Layer is a perception surface, not a data surface. Its singular job is to let each role answer one question, with zero clicks or one click:

> **Am I good?**

If a role cannot answer that question in under 3 seconds on the device they use most, the Confidence Layer for that role has FAILED — regardless of what other beautiful data the platform exposes.

This specification is the contract for what Operator Confidence is. **No code may be written against this spec** until:
- Phase 1 (Reality Validation) produces persona interview evidence that shows the question is unanswered today, AND
- Phase 2 (Training Reality Match) confirms that no existing surface already answers it that the operators just haven't been trained on.

If a Phase 1 persona shows "Am I good?" is answered in ≤ 3 seconds on an existing platform surface → that role's Confidence Layer is ALREADY BUILT and requires no work.

---

## 1 · What Operator Confidence is

1. A **one-sentence answer** to "Am I good?" surfaced inline on every role's first screen.
2. A **roll-up** of the role's outstanding obligations, recognized failure modes, and discoverable problems.
3. A **role-scoped** view — never an executive bird's-eye view in disguise.
4. **Always tied to action**: every red / yellow indicator must lead to a specific platform surface where the operator can act, with no detour through email / phone / Jaymn.
5. **Evidence-derived**: every indicator is sourced from existing collections (`incidents`, `daily_reports`, `qaqc_inspections`, `inspections`, `payroll_variance_batches`, `jha_acknowledgements`, `safety_training_records`, `driver_qualifications`, `equipment_inspections`, `corrective_actions`, `operations_events`, `operational_constraints`). No new schema.

---

## 2 · What Operator Confidence is NOT

This list is binding. If a proposed feature falls into any of these buckets, it is **OUT OF SCOPE** for the Confidence Layer.

- ❌ A dashboard with KPIs, sparklines, heatmaps, donut charts, or vanity numbers.
- ❌ A business-intelligence report.
- ❌ An analytics surface.
- ❌ A "dashboard of dashboards."
- ❌ A trends-over-time visualisation.
- ❌ A scorecard ranking employees against each other.
- ❌ A surveillance tool that tracks individuals.
- ❌ A surface that runs in the background draining battery on field devices.
- ❌ A polling-heavy surface (must be event/snapshot based, like the existing `/admin/recovery/snapshot` cached read).
- ❌ A surface that requires a separate login.
- ❌ A surface that surfaces information the role doesn't own.
- ❌ A surface that introduces new statuses, new lifecycle states, or new collections.

If anyone proposes a confidence layer that does any of the above, it is **NOT** an Operator Confidence Layer and must be rejected.

---

## 3 · The four confidence components (per role)

Every role's Confidence Layer is composed of:

| Component | Definition | Examples (NOT new — sourced from existing collections) |
|---|---|---|
| **Confidence Inputs** | Existing fields, statuses, expirations, lifecycle states from existing collections that drive the indicator | `incidents.lifecycle_state`, `daily_reports.lifecycle_state`, `corrective_actions.due_date`, `jha_acknowledgements.acknowledged_at`, `driver_qualifications.expires_at`, `equipment_inspections.next_due_date`, `safety_training_records.expiration_date` |
| **Confidence Outputs** | The one-sentence answer + a small set of action-tied bullet items | "You are good. 2 items need attention today." → bulleted list of those 2 items, each a deep link |
| **Confidence Indicators** | Green / Yellow / Red signal per role | See §4 below |
| **Confidence Ownership** | Which role OWNS each indicator. Cross-role obligations are NEVER shown on a role whose action cannot resolve them. | A PM does not see HR's expiring W-4s. HR does not see Shop's open defects. |

---

## 4 · Per-role confidence model (8 roles)

For each role: what's GREEN, YELLOW, RED. **All conditions reference existing collections / states**.

### 4.1 · LABORER
- **Inputs**: `jha_acknowledgements` (today's job), `equipment_inspections` (assigned equipment), `safety_training_records` (their expirations)
- **GREEN**: Today's JHP for assigned job acknowledged · assigned equipment has current pre-shift · no expired training
- **YELLOW**: Training expires within 7 days · pre-shift pending
- **RED**: Today's JHP NOT acknowledged · training expired today · assigned equipment has open Red-severity defect
- **One-sentence**: "You're good for today." (GREEN) / "Sign today's JHP." (RED)
- **Ownership**: laborer · cannot show items HR / Safety / Dispatch must act on

### 4.2 · FOREMAN
- **Inputs**: `daily_reports` (today's, status), `jha_acknowledgements` (entire crew on today's job), `equipment_inspections` (assigned units), `incidents` (open on their job)
- **GREEN**: Today's DR not yet due OR in OPEN/PENDING_REVIEW · all crew acknowledged today's JHP · no open incidents > 24h on this job
- **YELLOW**: DR bounced back by office (`PENDING_REVIEW → OPEN` with reason) · 1+ crew member missing JHP ack · open incident 12–24h
- **RED**: DR overdue for submission · ≥ 2 crew missing JHP ack · open incident > 24h
- **One-sentence**: "Crew is good. Submit today's DR by 5pm." (GREEN)
- **Ownership**: foreman · this is the only Confidence view that aggregates over a CREW

### 4.3 · SUPERINTENDENT
- **Inputs**: `daily_reports` (all jobs they cover), `incidents` (open across all their jobs), `equipment_inspections` (cross-job), `operational_constraints` (open across their jobs)
- **GREEN**: 0 stuck DRs · 0 incidents > 24h · 0 critical constraints unresolved
- **YELLOW**: Any DR in PENDING_REVIEW > 48h · any incident in OPEN > 12h · any constraint > 72h
- **RED**: Any DR in PENDING_REVIEW > 72h · any incident OPEN > 24h · constraint blocking production
- **One-sentence**: "All 4 jobs are good." (GREEN) / "3 items blocking — tap to clear." (RED)
- **Ownership**: super · aggregates Foreman-level Reds but does NOT show PM-only obligations

### 4.4 · PROJECT MANAGER (PM)
- **Inputs**: `corrective_actions` (owned), `incidents` (on their jobs), `daily_reports` (closed status), `jha_acknowledgements` (project-level compliance), `operational_constraints` (their jobs)
- **GREEN**: 0 CAPAs overdue · all DRs closing on schedule · JHP coverage ≥ 90% per project
- **YELLOW**: 1+ CAPA due within 3 days · DR closure rate < 90% · JHP coverage 70–89%
- **RED**: 1+ CAPA overdue · 1+ DR stuck in CLOSED-back-to-PENDING_REVIEW loop · JHP coverage < 70%
- **One-sentence**: "All 3 jobs healthy." (GREEN) / "1 overdue CAPA on Job 2024-101." (RED)
- **Ownership**: PM · cross-job

### 4.5 · SAFETY MANAGER
- **Inputs**: `incidents` (cross-platform), `qaqc_inspections`, `inspections`, `corrective_actions` (CAPA), `jha_acknowledgements` (compliance roll-up), `safety_training_records` (expirations)
- **GREEN**: 0 OSHA-recordables in OPEN/UNDER_INVESTIGATION > 24h · 0 deficiencies overdue · 0 unauthorised closures (Amendment 001 violations are now impossible by code)
- **YELLOW**: Incident in UNDER_INVESTIGATION 12–24h · deficiency in PENDING_RE_INSPECTION > 7 days · JHP roster gap on a mobilising job
- **RED**: OSHA recordable in OPEN > 24h · deficiency overdue (post-Amendment 001 thresholds) · training expirations ignored for > 30 days
- **One-sentence**: "Safety posture is good." (GREEN) / "1 OSHA recordable needs investigation." (RED)
- **Ownership**: Safety · this is the only role whose RED auto-escalates to Executive

### 4.6 · DISPATCH
- **Inputs**: `dispatch_assignments` (today + tomorrow), `driver_qualifications` (CDL / medical expirations), `equipment_inspections` (offline equipment), `incidents` (driver-involved)
- **GREEN**: Tomorrow's board complete · 0 drivers with expirations < 30 days · 0 equipment offline overnight without backup
- **YELLOW**: Tomorrow's board < 90% complete by 3pm today · driver expiration 8–30 days · equipment offline overnight with backup
- **RED**: Tomorrow's board < 70% by EOD · driver expiration < 7 days · equipment offline with no backup
- **One-sentence**: "Tomorrow is set." (GREEN) / "2 drivers expire next week — confirm or reroute." (YELLOW)
- **Ownership**: Dispatch

### 4.7 · HR
- **Inputs**: `employees.lifecycle_status`, `payroll_variance_batches` (lifecycle_state), `employee_requests` (queue), `driver_qualifications` (HR-side records), `safety_training_records` (HR-owned)
- **GREEN**: Last week's payroll variance FINALIZED · 0 employee requests > 5 days · 0 training expiring < 7 days
- **YELLOW**: PV in APPROVED but not FINALIZED > 24h · employee request 3–5 days · training expiring 7–14 days
- **RED**: PV stuck > 7 days · employee request > 7 days · expired training still active
- **One-sentence**: "HR is good through Friday." (GREEN) / "Finalize last week's variance." (RED)
- **Ownership**: HR

### 4.8 · EXECUTIVE
- **Inputs**: roll-up of Safety RED + PM RED + HR RED + Dispatch RED + Shop RED · `backup_health` posture (existing Recovery Dashboard) · `system_health`
- **GREEN**: 0 ROLE-LEVEL reds across the platform · last successful backup within RPO target · scheduler alive
- **YELLOW**: 1–2 role-level reds, not safety
- **RED**: ANY safety RED · OR ≥ 3 role-level reds simultaneously · OR backup posture RED · OR scheduler dead
- **One-sentence**: "Everything is good." (GREEN) / "1 safety RED needs your attention." (RED)
- **Ownership**: Executive · roll-up only · cannot drill into individual operator activity
- **Hard rule**: Executive view NEVER shows individual employee records by name. It shows aggregated counts and links into the responsible role's surface (Safety / PM / HR / Dispatch / Shop). This preserves the "coaching, not policing" doctrine.

---

## 5 · Confidence Layer interaction model

| Property | Rule |
|---|---|
| Surface | A single inline strip at the top of the role's primary hub page. NOT a separate page. |
| Tap target | Each indicator is itself the link to the action surface. |
| Latency | ≤ 500ms p95 first render. Server-side cached snapshot (`/api/admin/recovery/snapshot` is the architectural pattern: 15s TTL, single round-trip). |
| Personalisation | Identity-scoped: HR token sees HR view, PM token sees PM view, etc. Not switchable from one role's session. |
| Internationalisation | Bilingual (EN/ES) for Laborer + Foreman ONLY. Other roles are English-canonical. |
| Print | Hidden in print. |
| Polling | None. Refresh on navigation or user pull-to-refresh. |
| Empty state | When the role has no data yet, the strip shows the doctrine: "Nothing requires your attention." NOT a marketing welcome. |
| Failure mode | If the snapshot endpoint errors, the strip degrades to a quiet text fallback. NEVER blocks the role's hub from rendering. |

---

## 6 · Confidence Layer governance gates

Before any code is written:

| Gate | Evidence required |
|---|---|
| G1 | Phase 1 interviews for the role show the role cannot currently answer "Am I good?" in ≤ 3 seconds on existing surfaces |
| G2 | Phase 2 audit confirms no existing training teaches the role that there's an existing surface they're ignoring |
| G3 | The 7 OCEP tests pass for the proposal |
| G4 | The 4 OCEP proofs pass for the proposal |
| G5 | The proposal is sourced from EXISTING collections only · no schema change |
| G6 | The proposal does not violate §2 (what it MUST NEVER become) |

All 6 gates must pass per role. If any role passes, that role's Confidence Layer can advance to design — but ONLY that role's, ONLY when re-authorized.

---

## 7 · Refusal conditions

The AI agent MUST refuse to:
- Build the Confidence Layer for any role without all 6 gates documented as passed
- Build a "platform-wide" Confidence Layer in a single iteration (it is intentionally role-by-role)
- Add ANY indicator to a Confidence Layer that does not derive from an existing collection
- Add an analytics / trend / over-time view to the Confidence Layer
- Treat "Operator Confidence" as a feature pitch; it is a doctrine

---

## 8 · Out-of-scope work that masquerades as Confidence Layer

These are common drift patterns. If a future directive uses any of these terms, the AI agent should pause and confirm whether what's actually being asked is a Confidence Layer addition or a different (build-class) feature:

- "Executive dashboard" → likely BI / out-of-scope under FOCP
- "Real-time alerts" → likely a notification surface, not a Confidence Layer
- "Trend analysis" → analytics, out-of-scope
- "Compare jobs side-by-side" → BI, out-of-scope
- "AI-generated insights" → out-of-scope
- "Weekly digest" → already exists (`operator_digest`); not a new surface
- "Custom views per user" → personalisation; not a Confidence Layer

---

**End of OPERATOR CONFIDENCE LAYER SPECIFICATION · OCEP Phase 4**
