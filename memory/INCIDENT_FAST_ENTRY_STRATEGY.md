# Incident Fast Entry Strategy (Tiered)

**Source schema:** `/app/frontend/src/lib/incidentSchema.js` · 193 LOC, ~54 fields.
**Current UI:** `/app/frontend/src/pages/NewIncident.jsx` · 1,088 LOC.
**Goal:** Capture a Near Miss in ≤60 seconds. Capture a serious incident with full OSHA-grade detail in a stress-aware flow that respects field reality.

---

## The problem in one sentence

Today, a stressed supervisor who just witnessed a Near Miss is presented with the **same 54-field form** as the supervisor documenting a lost-time injury. That's wrong.

---

## Tiered model

### Tier 1 · Fast Entry (≤60s target)

**Always visible on initial submission.** These 8 fields cover the critical accountability + downstream notification triggers.

| Field | Why Tier 1 |
|---|---|
| `project_number` | Required for governance + PM routing |
| `location` | Where on site (one-liner) |
| `incident_date` / `incident_time` | Default = now (auto) |
| `person_name` | Who was involved (free text or master-lookup) |
| `incident_type` | 9-option pill selector (current schema) |
| `severity` | 6-option pill selector with color (current schema) |
| `description` | Single textarea — "What happened?" |
| `immediate_actions_taken` | Single textarea — "What did you do right away?" |
| `photos` | Upload/take photo (no minimum at Tier 1 — encourage but don't block) |

**Auto-captured (invisible to operator):**
- `gps_lat` / `gps_lng` / `gps_accuracy`
- `reported_date` / `reported_by` (current logged-in user)
- `incident_report_id` / status (`tier_1_only`)

**Tier 1 = 8 visible inputs.** All other 46 fields default to empty/unspecified and remain present in the data model.

### Tier 2 · Follow-Up Enrichment

**NOT in the initial submit flow.** Triggered automatically:
- **Reporter:** notification appears in their portal after submit: *"Add follow-up details to incident INC-20260224-001"*
- **Safety:** receives the Tier 1 record immediately via existing fan-out + can prompt the reporter for Tier 2 completion via the incident detail page

**Tier 2 fields (the remaining 46):**

| Block | Fields |
|---|---|
| Person detail | `person_role`, `person_employer`, `person_years_experience`, `employee_master_id`, `employee_master_label` |
| Injury detail | `body_part`, `injury_nature`, `treatment_provided`, `medical_facility`, `sent_home` |
| Cause | `immediate_cause`, `contributing_factors`, `root_causes{}` (11 checkboxes), `root_cause_notes` |
| Compliance | `osha_recordable`, `work_stopped`, `equipment_master_id`, `equipment_master_label` |
| Reporting | `supervisor_name`, `corrective_actions`, `responsible_party`, `target_completion_date` |
| Witnesses | `witnesses[]` (array) |
| Notifications | `notified_safety_manager`, `notified_pm`, `notified_gc`, `notified_owner`, `notified_osha`, `notified_other` |
| Distribution | `distribution_list[]` |
| Sign-off | `reporter_signature`, `supervisor_signature` |

**Tier 2 = the rest.** Completed in the existing incident detail edit page (same record, no re-create).

### Tier 1 → Tier 2 transition

```
┌─ Submit Tier 1 ─┐
│ POST /incidents │  ← creates record · status="tier_1_only"
└────────┬────────┘
         │
         ├─→ Fan-out: notification to Safety
         ├─→ Fan-out: notification to PM
         ├─→ Fan-out: auto-email to safety_contacts
         │
         └─→ Toast to reporter:
             "Incident submitted ✓ Safety notified.
              Tap here within 24h to add follow-up details."
                    │
                    ▼
            ┌─ Tier 2 edit ─────┐
            │ PATCH /incidents/X│ ← appends Tier 2 fields
            │ status="complete" │
            └───────────────────┘
```

**Backend reality check:** the `routes/safety.py` incidents API **already supports `POST` (create) and `PATCH` (update)**. No backend change required to enable tiered entry — the model already accepts partial-then-full updates. We're using existing capabilities.

---

## Auto-escalation safety net

**Rule:** If the operator selects `severity ∈ {medical, restricted, lost_time, fatality}`, **Tier 2 fields auto-surface within the same submission page**. The Near Miss tier shortcut does NOT apply to serious events.

This prevents the failure mode where a supervisor under-classifies severity to avoid the longer form. The form expands the moment severity rises, and the additional fields are required before submit.

| Severity selected | Tier 2 auto-expansion |
|---|---|
| `near_miss` | None — Tier 1 only |
| `first_aid` | Injury detail block only |
| `medical` | Injury detail + cause + medical_facility required |
| `restricted` | All Tier 2 required except witnesses (optional) |
| `lost_time` (DART) | All Tier 2 required including OSHA fields |
| `fatality` | All Tier 2 + immediate auto-page to Safety + OSHA flag locked to Yes |

---

## Mobile-first ordering of Tier 1 inputs

```
┌─ New Incident · INC-20260224-001 ─────────────────────────────────┐
│                                                                    │
│  ▶  Tap your severity                                              │
│    [Near Miss] [First Aid] [Medical] [Restricted] [DART] [Fatal]  │
│                                                                    │
│  ▶  What happened?                                                 │
│    [_______________________________________________________]      │
│    [_______________________________________________________]      │
│                                                                    │
│  ▶  Where?                                                         │
│    Project: [auto-selected ▼]  Location: [____________________]   │
│                                                                    │
│  ▶  Who?                                                           │
│    [Type or pick from master roster ▼]                            │
│                                                                    │
│  ▶  What did you do right away?                                    │
│    [_______________________________________________________]      │
│                                                                    │
│  ▶  Photos                                                         │
│    [📷 Take]  [📁 Upload]   ⊕ optional but encouraged             │
│                                                                    │
│  ▶  GPS captured · Time auto-set · 14:32 today                    │
│                                                                    │
│  ⚠  Safety has been notified automatically when you submit.        │
│                                                                    │
│  [           SUBMIT (Near Miss · 8 fields)            ]          │
└────────────────────────────────────────────────────────────────────┘
```

If severity ≥ medical, the form auto-expands the relevant Tier 2 sections below the Tier 1 block (no separate page).

---

## Coaching pairing (`LifecycleGuide`)

A compact LifecycleGuide block at the top of the Tier 1 page:

```
┌─ Lifecycle Guide ─────────────────────────────────────────────────┐
│ Incident reporting flow                                            │
│ ─────────────────                                                  │
│ • Submit now (8 fields) → Safety is notified immediately           │
│ • Add follow-up details within 24 hours from the incident detail   │
│ • Serious events (Medical/DART/Fatality) require full detail now   │
└────────────────────────────────────────────────────────────────────┘
```

Existing LifecycleGuide component (`/app/frontend/src/components/LifecycleGuide.jsx`) supports this exactly — dismissible per-user, mobile-collapsible, indigo accent. No new component needed.

---

## Trust + accountability preservation

| Concern | How it's preserved |
|---|---|
| Safety notified on Tier 1 submit | Fan-out already fires on POST /incidents — unchanged |
| OSHA recordable detection | `osha_recordable` field still present; Tier 2 auto-required when severity≥medical |
| Witness statements not lost | Tier 2 follow-up captures within 24h; reminder notifications fire if not completed |
| Audit trail | Same record, PATCHed not re-POSTed — full history retained |
| Severity downgrade avoidance | Auto-expansion gate prevents undeclaring serious events |
| Distribution list | Preserved in Tier 2; falls back to org-default if not specified |
| Signatures | Preserved in Tier 2 |

---

## What this strategy explicitly forbids

| ❌ Not allowed | Why |
|---|---|
| Skip Tier 2 entirely for `near_miss` | Even Near Misses sometimes warrant follow-up; the reminder notification stays |
| Allow Tier 2 submit without severity | Severity is the gate that decides if more is required |
| Default `severity` to anything but Near Miss | Defaulting to a higher tier would lock users into a longer form unnecessarily |
| Change the fan-out routing | Same Safety/PM/GC notification logic on Tier 1 submit |
| Reduce photo upload capability | Photos still uploadable at Tier 1; required count enforced at Tier 2 for serious events |

---

## Estimated reduction

| Metric | Current | Tier 1 | Δ |
|---|---|---|---|
| Visible inputs (Near Miss) | 54 | 8 | −85% |
| Taps to complete Near Miss | ~40 | ~9 | −78% |
| Estimated time (Near Miss) | 5–8 min | <60s | −85% |
| Visible inputs (Lost Time) | 54 | 30 | −44% (still compressed via grouping) |
| Estimated time (Lost Time) | 8–12 min | 4–6 min | −50% |

**Caveat:** estimates pending field shadow. The Lost Time numbers may need re-validation — that tier should not feel "fast", it should feel **thorough**, just less chaotic.

---

## Implementation footprint

**Files touched:** 1 (`NewIncident.jsx`)
**Backend touched:** 0 — POST and PATCH already exist
**LOC added/changed:** ~200 (state machine for tier, conditional sections, auto-expand logic)
**Risk:** MEDIUM. Stress-driven UX is harder to get right than routine UX. Demands field validation.
**Rollback:** Single state flag (`tier=2` default) restores current behavior.

---

## Closing principle

A Near Miss must be **trivial to report** so that supervisors actually report them. A Fatality must be **impossible to under-document** so that the platform protects the company. The tiered model serves both, simultaneously, without forcing one to compromise the other.
