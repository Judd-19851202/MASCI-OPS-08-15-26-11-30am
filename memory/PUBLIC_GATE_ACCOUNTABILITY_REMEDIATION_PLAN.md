# OMEGA · Public-Gate Accountability Remediation Plan

**Date:** 2026-06-01
**Mode:** Design decision document. No code. No implementation.
**Predecessors:** `DAILY_REPORT_OWNERSHIP_AUDIT.md` · `QAQC_OWNERSHIP_AUDIT.md` · `PUBLIC_GATE_WORKFLOW_ACCOUNTABILITY_REPORT.md` · `PUSH_NOTIFICATION_FEASIBILITY_REPORT.md` · `PUBLIC_GATE_NOTIFICATION_ARCHITECTURE.md` · `REVISION_DELIVERY_OPTIONS.md`
**Verdict:** 🟢 **Solvable. Solvable once. Solvable as a dedicated platform sprint.**

---

## TL;DR for the operator

Build one shared platform service: **Field Submitter Identity (FSI)**.

* One backend module. One collection. One config-driven UI component. One dispatcher upgrade.
* Wired into every public-gate POST as a one-line dependency.
* Solves Daily Reports, QA/QC, Site Inspections, JHA acknowledgements, Safety Meetings, Equipment inspections, **and every future public-gate workflow** with zero re-engineering.
* Recommended scheduling: **dedicated platform sprint inserted as iter452.5** (~2 weeks), positioned between iter452 and iter453.
* Without this, the iter453+ workflows ship with the same systemic gap that already invalidates iter451-452's "Definition of DONE" for the field side.

---

## 1 · Recommended authoritative identity model

### Hybrid model — three-layer identity

The operator's choice list (employee directory · supervisor email · employee ID · project ownership · hybrid) is correct in spirit, but no single layer is sufficient. The recommendation is **a three-layer hybrid** where each layer fills a different gap.

```
┌────────────────────────────────────────────────────────────┐
│ LAYER 1 — DIRECTORY ANCHOR (who they ARE)                  │
│ ────────────────────────────────────────────────────────── │
│ Required dropdown selection from a project-scoped slice    │
│ of the employees collection.                                │
│ Stored on submission row:                                   │
│   submitter_employee_id  (string · UUID FK to employees.id) │
│   submitter_name         (denormalized snapshot · audit)    │
│                                                             │
│ Source of truth: employees collection.                      │
│ Drives: accountability, reporting, Command Center, history. │
└────────────────────────────────────────────────────────────┘
                              ↓
┌────────────────────────────────────────────────────────────┐
│ LAYER 2 — CONTACT BINDING (how they are REACHED)           │
│ ────────────────────────────────────────────────────────── │
│ Per-submission contact captured at submit time, even if    │
│ the directory row has no email/phone. Operator-or-self     │
│ provided; never overwrites the directory.                   │
│ Stored on submission row:                                   │
│   submitter_email_at_submit  (string)                       │
│   submitter_phone_at_submit  (string, E.164)                │
│   submitter_device_id        (localStorage UUID)            │
│                                                             │
│ Source of truth: the submission itself.                     │
│ Drives: revision-link delivery, push fan-out, SMS.          │
└────────────────────────────────────────────────────────────┘
                              ↓
┌────────────────────────────────────────────────────────────┐
│ LAYER 3 — RESPONSIBILITY ANCHOR (who OWNS it)              │
│ ────────────────────────────────────────────────────────── │
│ Project-bound supervisor + PM chain resolved server-side   │
│ at submit time, NOT trusted from the form.                  │
│ Stored on submission row (denormalized snapshot):           │
│   resolved_pm_email                                         │
│   resolved_pm_id                                            │
│   resolved_co_pm_emails[]                                   │
│   resolved_superintendent_email                             │
│   resolved_at         (ISO-string · staleness audit)        │
│                                                             │
│ Source of truth: jobs_master + employee role assignment.    │
│ Drives: notifications, escalation, audit ownership chain.   │
└────────────────────────────────────────────────────────────┘
```

### Why each layer is non-optional

| Layer | If omitted | Consequence |
|---|---|---|
| 1 — Directory anchor | "John from concrete" cannot be told apart from any other John on any other project; accountability dashboards collapse | Phase 1A "responsible party" fails |
| 2 — Contact binding | Revision links cannot be delivered; field cannot be told of kickback | Definition-of-DONE fails (current state) |
| 3 — Responsibility anchor | Office-side notifications can be spoofed by submission free-text | PM email is wrong; CAPAs route to the wrong person |

### Hybrid rationale (vs. each single-layer option)

| Option considered | Rejected because |
|---|---|
| Employee directory alone | 1/261 employees have email today; directory enrichment is a separate multi-month project |
| Supervisor email alone | Same problem — and supervisor is rarely the original submitter |
| Employee ID alone | Identity without reach — knowing "who" doesn't mean we can tell them anything |
| Project ownership alone | Already works (the PM side is GREEN today); does not solve the field-side gap |
| Hybrid (recommended) | Layer 1 fixes identity; Layer 2 fixes reach in the short-term WITHOUT requiring directory enrichment; Layer 3 keeps the GREEN PM side intact |

---

## 2 · Minimum fields every public-gate workflow MUST capture

| Field | Required? | Source | Purpose |
|---|---|---|---|
| `submitter_employee_id` | ✅ Required | Dropdown (project-scoped) | Identity anchor |
| `submitter_name` | ✅ Required | Denormalized from directory | Audit-trail readability |
| `submitter_email_at_submit` | ⚠️ Soft-required (at least one of email or phone) | Text input · pre-filled from directory if available | Revision delivery |
| `submitter_phone_at_submit` | ⚠️ Soft-required (at least one of email or phone) | Text input · pre-filled from directory if available | SMS revision delivery |
| `submitter_device_id` | ✅ Auto-captured | Frontend (crewMemory.js) | Continuity across same-device submissions |
| `submitter_consent_at` | ✅ Auto-captured | Timestamp | Privacy / TCPA compliance |
| `submitter_consent_text_version` | ✅ Auto-captured | Constant | Audit of what user agreed to |
| `project_number` | ✅ Required (already today) | Dropdown | Project scope |
| `resolved_pm_email` | ✅ Auto-resolved | jobs_master | Office routing |
| `resolved_co_pm_emails` | ✅ Auto-resolved | jobs_master | Office routing |
| `resolved_superintendent_email` | 🟡 Optional (when directory has it) | employees role-filter | Field escalation |
| `resolved_at` | ✅ Auto-captured | Server timestamp | Staleness audit |

**Total new columns per workflow row: 10** (8 captured, 2 auto-resolved). All additive — no existing field renamed or removed.

The "at least one of email or phone" rule supports field crews who genuinely have neither — they fall back to the PM-relay path (Option E in `REVISION_DELIVERY_OPTIONS.md`).

---

## 3 · Affected workflows

### Currently public-gated (per the prior audit)

| Workflow | OC-* | Affected? | Notes |
|---|---|---|---|
| Daily Reports | OC-002 | ✅ Yes | Highest-volume submitter; current YELLOW classification |
| QA/QC Inspections | OC-003 | ✅ Yes | Inspector identity field absent today |
| Site Inspections | OC-004 | ✅ Yes (will be) | Same pattern — gap inherits to iter453 |
| JHA Acknowledgements | OC-005 | 🟡 Partial | Crew-acknowledgement model is distinct: per-employee row already (iter454 design) |
| Safety Meetings | — | ✅ Yes | Same pattern · not yet in Phase 1A but suffers the same gap |
| Equipment Pre-Op Inspections | — | ✅ Yes | Same pattern · Shop Manager override is independent of submitter identity |
| Incident Reports (public) | OC-001 | 🟡 Partial | Already shipped; iter451 captured `reported_by` free text · same gap |
| Vendor / Subcontractor portal submissions | — | 🟡 If/when added | Future-proofed by the same model |

### Not affected (authenticated workflows)

| Workflow | Why not affected |
|---|---|
| Payroll Variance (OC-007) | HR / Admin authenticated · no public gate |
| Incident closure transitions | Safety / Admin authenticated |
| HR Onboarding / Offboarding | HR authenticated |
| Job creation / PM management | Admin authenticated |
| Photo uploads (authenticated) | PM authenticated |
| Equipment master | Shop authenticated |

---

## 4 · Shared-service vs workflow-specific logic

### What the shared service handles

| Concern | Where |
|---|---|
| Project-scoped employee dropdown component | Shared frontend (`<FieldSubmitterIdentityForm/>`) |
| Email validation, phone E.164 normalization | Shared frontend + shared backend validator |
| Consent timestamp + version pinning | Shared backend middleware |
| Project_number → jobs_master resolution | Existing `pm_routing.recipients_for_record_async()` — already shared |
| Device-ID generation/persistence | Existing `crewMemory.js` — already shared (extended to send to server) |
| Audit-trail event encoding | Existing `workflow_state_events` — already shared |
| Revision-link JWT issuance/validation | Shared backend (`lib/signed_revision_links.py` per the architecture doc) |
| Push/email/SMS dispatch | Shared dispatcher (per `PUBLIC_GATE_NOTIFICATION_ARCHITECTURE.md`) |
| Privacy retention (90-day TTL on contact bindings) | Shared cleanup scheduler |

**Estimate: ~90% of the work lives in the shared service.**

### What stays workflow-specific

| Concern | Why workflow-specific |
|---|---|
| Which deficiencies trigger CAPA-route | Each inspection kind has its own deficiency taxonomy |
| What "office review" means for a Daily Report vs a QA/QC inspection | Already correctly separate in iter452 |
| Which roles can transition which state | Already encoded in `workflow_state_machine.py` per-workflow |
| Workflow-specific notification copy | Per-workflow notification template (sentence templates only) |

**Estimate: ~10% of the work — copy strings, role assignments, deficiency taxonomies.**

---

## 5 · Solvable once and reused?

🟢 **Yes — provably reusable.** Three reasons:

1. **Schema reuse.** The 10 minimum fields (§2) are identical for every public-gate workflow. The schema patch is the same SQL/Mongo update for `daily_reports`, `qaqc_inspections`, `site_inspections`, `jha_acknowledgements`, `safety_meetings`, `equipment_pre_op_inspections`.

2. **Form reuse.** A single `<FieldSubmitterIdentityForm/>` React component renders the dropdown + email + phone inputs + consent text. Each workflow embeds it as 3 lines of JSX above their existing form sections.

3. **Pipeline reuse.** The submission pipeline (`POST` → validate identity → resolve PM → persist row → emit notification → dispatch revision-link) is one shared function with workflow-specific configuration injected.

Future workflows (vendor submissions, subcontractor daily certifications, etc.) gain accountability "for free" by mounting the shared form and calling the shared submit helper.

---

## 6 · Architecture recommendation — concrete

### New module — `backend/lib/field_submitter_identity.py`

Public API:

```python
async def resolve_identity(
    payload: dict,           # form submission body
    project_number: str,
    workflow_kind: str,
    db, request
) -> FieldSubmitterIdentity:
    """Validates submitter_employee_id against project-scoped employees.
    Captures contact + device + consent. Resolves PM/co-PM/supt via
    jobs_master. Returns a denormalized snapshot to embed on the row."""

async def bind_revision_channels(
    submission_id: str,
    workflow_kind: str,
    identity: FieldSubmitterIdentity,
    db
) -> None:
    """Writes to field_submitter_bindings with TTL.
    Idempotent on (workflow_kind, submission_id)."""

async def notify_field_submitter(
    submission_id: str,
    workflow_kind: str,
    event_kind: str,         # 'kickback' | 'closure' | 'capa_assigned' | ...
    message: str,
    reason: Optional[str],
    db
) -> NotificationOutcome:
    """Reads field_submitter_bindings, dispatches to the configured
    channel tier, logs delivery_log entries, returns the outcome."""
```

### New collection — `field_submitter_bindings`

(Per the architecture doc.) One row per submission. Stores contact channels and consent. 90-day TTL via Mongo `expireAfterSeconds`.

### Existing collection — `workflow_state_events`

Extended with revision-link event kinds (`revision_link_issued`, `_consumed`, `_expired`, `_replay_blocked`). Already append-only; already indexed.

### Existing collection — `notifications`

Schema unchanged. The existing `delivery = {internal, email, push, sms}` envelope becomes derived from `delivery_log[]`.

### New shared frontend component — `<FieldSubmitterIdentityForm/>`

Props: `projectNumber`, `workflowKind`, `onChange(identity)`. Embedded in every public-gate form. Renders the 4 required inputs + consent text + project-scoped employee dropdown.

### New shared backend dependency — `Depends(field_submitter_identity_gate)`

Drop-in for every public-gate `POST` route, alongside `rate_limit_public_post`. Enforces presence of the 10 minimum fields, runs identity resolution, decorates the request state.

---

## 7 · Migration strategy

### Phase R1 — Foundations (week 1)

* Create `field_submitter_bindings` collection + indexes + TTL
* Implement `lib/field_submitter_identity.py` (resolve, bind)
* Add `Depends(field_submitter_identity_gate)` dep
* Generate VAPID keys; create `REVISION_LINK_SECRET`; add env vars
* Implement `lib/signed_revision_links.py` (JWT issuer/validator)
* Add audit-event kinds to `workflow_state_events`

### Phase R2 — Tier-1 channel: email revision (week 1.5)

* Implement email dispatcher (uses existing `schedule_auto_email` infra)
* Implement `/revise/<jwt>` route on backend + frontend rendering shell
* Wire the kickback transition in `daily_report_lifecycle.py` to call `notify_field_submitter`
* Add Playwright happy-path test

### Phase R3 — UI shared component (week 1.5 in parallel with R2)

* Build `<FieldSubmitterIdentityForm/>` React component
* Project-scoped employees endpoint (`GET /api/projects/<num>/team`) — already exists in some form; verify and re-use
* Add `data-testid` set for the testing agent

### Phase R4 — Workflow rollout (week 2)

Rollout order (lowest risk first):

1. **Daily Reports** — already in iter452 scope; touches `ViewDailyReport`, `NewDailyReport`, `daily_report_lifecycle`
2. **QA/QC** — will land in iter453 anyway; aligns with operator's roadmap
3. **Site Inspections** — iter453 scope
4. **Incident Reports (public)** — retrofit iter451's `reported_by` to populate `submitter_*`
5. **JHA Acknowledgement Ledger** — iter454; per-employee row already (lighter retrofit)
6. **Safety Meetings, Equipment Pre-Op** — not in Phase 1A; opt-in retrofit

Each workflow retrofit is ≈ 1-2 hours: import the shared form, accept the new fields in the Pydantic model, call `resolve_identity` in the POST handler.

### Phase R5 — Backfill policy

* Pre-iter452.5 submissions remain free-text only; they are read through a shim (`coerce_submitter_identity`) that returns `null` for the new fields.
* No retroactive identity assignment. Audit history is unchanged.
* Reports flag pre-iter452.5 rows as "legacy submitter — identity not enforced" in the UI for transparency.

### Phase R6 — Tier-2 / Tier-3 channels (optional, weeks 3-4)

* SMS dispatcher (Twilio integration)
* Push dispatcher (VAPID + service worker)
* These are independent of the identity model. Tier-1 (email) closes ~70% of the gap; the remaining tiers are upside.

---

## 8 · Estimated effort

| Phase | Scope | Best-case | Realistic | Buffered |
|---|---|---:|---:|---:|
| R1 — Foundations | Collection + lib + JWT + env | 3 days | 4 days | 5 days |
| R2 — Email Tier-1 | Dispatcher + `/revise/<jwt>` + first wire-up | 3 days | 4 days | 5 days |
| R3 — Shared UI form | React + tests | 2 days | 3 days | 4 days |
| R4 — Workflow rollout (6 workflows) | Retrofit × 6 @ ~2 hrs each | 1.5 days | 2 days | 3 days |
| R5 — Backfill policy & legacy shim | Shim + legacy badge | 1 day | 1.5 days | 2 days |
| **R1–R5 cumulative (Tier-1 stack)** | | **10.5 days** | **14.5 days** | **19 days** |
| R6a — SMS Tier-2 | Twilio dispatcher + consent flow | 3 days | 4 days | 5 days |
| R6b — Push Tier-3 | VAPID + SW + iOS PWA install flow | 5 days | 7 days | 9 days |
| **Full stack (R1–R6)** | | **18.5 days** | **25.5 days** | **33 days** |

**Recommendation: scope iter452.5 to Phases R1–R5 only (~14.5 realistic days ≈ 3 weeks).** This closes the systemic gap for the email-reachable submitter — the 70% case — with the lowest risk. Tiers 2-3 are independent follow-ons that can ship in Phase 1A.5 or Phase 2 without re-engineering.

---

## 9 · Recommended phase placement

| Option | Pros | Cons | Recommendation |
|---|---|---|---|
| **iter453** | Co-located with OC-003/OC-004 build · they need the model anyway | Conflates "build workflow" with "build platform" · iter453 scope doubles | ❌ Avoid |
| **iter454** | Co-located with JHA which is already partly-directory-anchored | Daily Reports + QA/QC ship with the gap and need retrofit | ❌ Avoid |
| **iter455** | Bundled with the Phase 1A integration certification | Field-side gap remains open for the entirety of Phase 1A build | ❌ Avoid |
| **Phase 1B** | Aligns with the status-vocab canonicalization sprint | Field-side gap remains open through 4 more iterations · Definition-of-DONE for OC-001..-004 fails for 2-3 months | ❌ Reject — moves the systemic gap too far right |
| **Dedicated platform sprint (iter452.5)** | Shared service ships before OC-003/-004 build; they inherit it cleanly · field-side gap closes ASAP · architecturally cleaner | Delays iter453 BUILD by ~3 weeks | ✅ **Strongly recommended** |

### Why iter452.5 is the right answer

1. **Cost compounds.** Every iter453+ workflow built without the shared service must be retrofitted later — duplicate work.
2. **Risk compounds.** Each iteration that ships with the YELLOW classification accumulates audit debt and customer-visible accountability gaps.
3. **Mental model alignment.** "Build the platform, then build the workflows" is the correct sequencing per the Operator's OMEGA discipline; doing it in reverse is the anti-pattern.
4. **Definition-of-DONE convergence.** iter452.5 transforms iter451 (incidents) + iter452 (DR + PV) from 🟡 YELLOW field-side to 🟢 GREEN field-side immediately on completion, with a one-day per-workflow retrofit. The closure of the systemic gap happens once, not six times.

---

## 10 · Deployment order

```
Today
  ↓
─── iter452 deploy authorization (separate decision, can proceed independently)
  ↓
─── iter452.5 PLATFORM SPRINT (3 weeks)
       Week 1   : R1 Foundations + R2 Tier-1 email scaffolding
       Week 2   : R3 shared UI + R4 rollout to OC-001/OC-002
       Week 3   : R4 rollout to OC-003/OC-004 placeholders +
                  R5 legacy shim + final certification
  ↓
─── iter452.5 production deploy + ops cert
  ↓
─── iter453 BUILD (OC-003 + OC-004) — inherits the shared service for free
  ↓
─── iter454 BUILD (OC-005 JHA Ledger) — inherits shared service
  ↓
─── iter455 INTEGRATION CERTIFICATION
       Includes optional R6a/R6b channel-tier authorization decision
```

**Critical sequencing constraint:** iter452.5 MUST land before iter453 BUILD begins. Reversing the order forces a costly retrofit of OC-003/OC-004 inside iter453 or iter455.

---

## 11 · Open operator decisions required

The plan is decision-complete except for these explicit operator choices:

| Decision | Operator must choose | Default if not specified |
|---|---|---|
| Authorize iter452.5 platform sprint | Yes / No / Defer | (no default — operator-only) |
| Sprint timing relative to iter452 production deploy | Before · After · Parallel | After |
| Tier-1 channel choice | Email-only · Email+SMS · Email+Push · All three | Email-only (lowest risk) |
| Privacy retention window for `field_submitter_bindings` | 30d · 60d · **90d** · 180d | 90d (matches OSHA secondary retention) |
| Consent text wording | Operator-authored · Legal-reviewed · Platform-default | Platform-default with legal-review-recommended flag |
| Legacy backfill | None · Best-effort retro · None-with-flag | None-with-flag (recommended) |
| iOS PWA mandatory install messaging | "Recommended" · "Required" · "Not surfaced" | "Recommended" (avoids hard blocking) |

---

## 12 · Verdict

🟢 **The systemic gap is solvable, solvable once, and solvable in a single dedicated platform sprint.**

* **Identity model:** Three-layer hybrid (directory anchor + per-submit contact + project-resolved responsibility).
* **Architecture:** One shared lib + one shared collection + one shared form + one dispatcher upgrade.
* **Effort:** ~14.5 realistic engineering days (3 weeks buffered) for Tier-1; ~25.5 days for the full Tier-1/2/3 stack.
* **Phase placement:** **iter452.5 dedicated platform sprint**, positioned between iter452 production deploy and iter453 BUILD.
* **Rollout:** 6 workflows retrofit at ~2 hours each. Future workflows inherit by importing one form + one dependency.

**Awaiting operator authorization for the iter452.5 platform sprint.** No code. No implementation. Design decision delivered.
