# DOT / FAA RFI Template Standard
## Phase V.0 · Architecture & Governance · 2026-05-27

> Agency-specific RFI template doctrine. Templates are operational
> presets, not hard-coded forms. Doctrine-locked.

---

## 1 · Why Templates

DOT, FAA, and Owner-Reps each carry their own conventions for what an
RFI must contain. MASCI Ops should not force superintendents and PMs
to remember those conventions — the platform should embed them as
selectable templates.

A template is a **preset** that pre-fills:

- Field labels (terminology)
- Required-field whitelist
- Default priority interpretation
- Default response window
- Distribution defaults
- PDF section ordering toggles
- Coaching sublines

It does NOT change the underlying RFI schema. Every RFI carries every
field defined in `RFI_SYSTEM_DOCTRINE.md`. Templates simply present a
filtered, agency-aligned view.

---

## 2 · Approved Templates (V.0 design · build in V.1)

### 2.1 — FDOT (Florida DOT · roadway / bridge / utility)

| Property | Value |
|---|---|
| Distribution defaults | CEI · Engineer of Record |
| Required fields | Station/Offset · Plan Sheet # · Pay Item # · Spec Section |
| Default priority | Action Required |
| Response window | 5 business days (override-able) |
| PDF emphasis | Plan/Spec references · Pay-item linkage · MOT impact |
| Coaching subline | "FDOT field condition · CEI response required" |

### 2.2 — TxDOT (Texas DOT · roadway / bridge)

| Property | Value |
|---|---|
| Distribution defaults | Area Engineer · CEI |
| Required fields | Station/Offset · Sheet # · Item Number · Special Provision ref |
| Default priority | Action Required |
| Response window | 5 business days |
| PDF emphasis | Plan/Spec references · Special Provisions · MOT |
| Coaching subline | "TxDOT field condition · Area Engineer response required" |

### 2.3 — FAA · Airfield (taxiway / runway / apron)

| Property | Value |
|---|---|
| Distribution defaults | Resident Engineer · Airport Ops · Owner |
| Required fields | Pavement section · Coordinates (lat/long) · Closure window · NOTAM ref · FAA operational impact |
| Default priority | Critical Path Impact (airfield default) |
| Response window | 2 business days (default) · 24h if closure-window driven |
| PDF emphasis | NOTAM ref · Closure window · FAA operational impact · Photos with coordinates |
| Coaching subline | "FAA operational impact · response inside closure window" |

### 2.4 — Heavy-Civil Owner (Municipal / County / Authority)

| Property | Value |
|---|---|
| Distribution defaults | Owner · Engineer of Record |
| Required fields | Plan Sheet # · Spec Section · Cost impact estimate |
| Default priority | Action Required |
| Response window | 10 business days |
| PDF emphasis | Plan/Spec refs · Cost impact · Schedule impact |
| Coaching subline | "Owner clarification · field condition documented" |

### 2.5 — Utility Coordination

| Property | Value |
|---|---|
| Distribution defaults | Utility company contact · Engineer of Record |
| Required fields | Utility ID · Conflict description · Coordinates · Plan sheet |
| Default priority | Critical Path Impact (utility default) |
| Response window | 5 business days |
| PDF emphasis | Conflict photo · Coordinates · Schedule impact |
| Coaching subline | "Utility conflict · coordination response required" |

### 2.6 — Generic (fallback)

| Property | Value |
|---|---|
| Distribution defaults | (none · PM picks) |
| Required fields | Project · Contract · Field condition · Question |
| Default priority | Routine |
| Response window | 10 business days |
| PDF emphasis | Full schema |
| Coaching subline | "Field condition documented · response requested" |

---

## 3 · Template Selection

Templates are selected by **project**, not per RFI. Each project carries
a default `rfi_template` resolved from:

1. Contract type (when the project meta carries `agency = fdot|txdot|faa|owner|utility|generic`).
2. PM override (PM can set per project).
3. Superintendent draft choice (last-mile override, audited).

If no template matches, **Generic** applies.

---

## 4 · Template Definition Format

Templates are stored as JSON in `/app/memory/rfi_templates/` and loaded
by the backend at startup:

```json
{
  "id": "fdot",
  "label": "FDOT (Florida DOT)",
  "agency_kind": "state_dot",
  "distribution_defaults": ["cei", "engineer"],
  "required_fields": ["station_offset", "plan_sheet", "pay_item", "spec_section"],
  "default_priority": "action_required",
  "response_window_business_days": 5,
  "pdf_emphasis": ["plan_spec_refs", "pay_item", "mot_impact"],
  "coaching_subline": "FDOT field condition · CEI response required",
  "terminology_overrides": {
    "engineer_role_label": "Engineer of Record",
    "review_role_label": "CEI"
  }
}
```

This format is **declarative** so audits can verify the active template
without reading code. Doctrine reaffirmation: governance > velocity.

---

## 5 · Template Versioning

Templates carry a `version`. When a template is revised, existing RFIs
that referenced the prior version **continue to reference that prior
version forever** (immutable). New RFIs use the new version. The PDF
footer reports the template id + version used.

---

## 6 · Adding a New Template (operator workflow)

1. PM or Admin proposes a new template (e.g., `caltrans`).
2. Doctrine review: terminology, required fields, response window.
3. New file under `/app/memory/rfi_templates/<id>.json`.
4. Coaching subline reviewed against `RFI_COACHING_TERMINOLOGY_STANDARD.md`.
5. Regression test asserts the new template loads cleanly.
6. Rolled into production via the existing deploy flow.

No template is added without a doctrine pass. Random "let's add a
field" requests are rejected — they reach the template review board
first.

---

## 7 · Out-of-Scope Templates

Phase V.0 explicitly defers:

- International agencies (Mexico SCT, Canadian MTO) — until operational demand justifies.
- Private rail / port authorities — same gate.
- City-specific micro-templates (e.g., "City of Tampa stormwater") —
  use Generic + manual reference fields.

---

## 8 · Sign-off

- **Author:** E1 · Phase V.0 architecture authoring pass
- **Status:** 🟢 Doctrine-grade
- **Implementation gate:** Template engine lands in V.1. Initial templates ship with FDOT + Generic; the rest land as projects of that agency type appear.
