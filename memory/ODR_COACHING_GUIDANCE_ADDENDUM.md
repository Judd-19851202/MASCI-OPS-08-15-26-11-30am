# ODR · COACHING / TRAINING / GUIDANCE ADDENDUM

_Phase V.1 · Operational Daily Record · Pre-Lock Final Doctrine · 2026-05-29_

This addendum is the **final architecture revision** before spec
lock. It establishes the ODR as an **operational coaching system
that simultaneously captures operational intelligence** — not
merely a reporting form.

**No implementation. No code. No routes. No collections. No UI build.**

---

## 1 · Doctrine statements (O36–O50 · new)

These extend the locked operator doctrine (O1–O35) and complete
the **50-doctrine lock** for V.1.

| # | Statement |
|---|---|
| O36 | The ODR is **not merely a reporting system**. It is an operational coaching system that simultaneously captures operational intelligence. |
| O37 | The platform shall **teach users while they work**. |
| O38 | The **primary quality-control mechanism is coaching**. Rejection / return workflows are secondary. |
| O39 | The system shall guide users toward high-quality reports through contextual coaching, examples, crew-specific guidance, readiness suggestions, and embedded best practices. |
| O40 | The foreman must **never be required to memorize reporting requirements**. The platform carries that load. |
| O41 | ODR shall integrate directly with the **Operational Guidance Center**. Every major ODR section shall support: Learn More · Example Entries · Crew-Specific Guidance · Best Practices. |
| O42 | Guidance must be available **without leaving workflow context** — inline drawers, never destructive navigation. |
| O43 | Guidance content shall be **fully mirrored EN ↔ ES** from a single source of truth. No separate disconnected guidance systems. |
| O44 | ODR coaching shall **adapt based on Crew Type, Primary Operation, and Work Category**. Pipe / Paving / MOT / Survey / Airfield / Electrical / Concrete / Structures / etc. each receive crew-specific examples. |
| O45 | Readiness indicators **coach**. They never **punish**. They surface "Suggested additions" — never "Missing fields you failed to enter." |
| O46 | First-time-user onboarding shall be **optional, ≤ 2 minutes, and dismissible**. Once dismissed, it never reappears unless the foreman opens it from the help menu or guidance center. |
| O47 | Field Leadership Portal shall expose an **ODR Training** surface: best practices, examples, quality guidance, and coaching metrics (aggregated · never per-foreman scoring). |
| O48 | PM Portal shall display **completion trends · coaching opportunity trends · common missing information** — aggregated · for training opportunity identification, **not** disciplinary scoring. |
| O49 | Coaching telemetry shall be **append-only**, integrity-anchored, and operator-strict on the raw-per-foreman dimension. Only **aggregated** views ever leave the admin / governance surfaces. |
| O50 | The coaching system shall **never be used as performance review evidence**. Per O9 + O27 + O45 — coach, never punish; this is a hard cultural contract anchored in the spec. |

---

## 2 · The four guidance touchpoints (O41 inventory)

Each major ODR section gains four guidance surfaces. Surfaces are
inline · context-preserving · dismissible · bilingual.

| Touchpoint | What it shows | UI affordance |
|---|---|---|
| **Learn More** | one-paragraph explanation of what this section is for, in operator vocabulary (no jargon) | small `ⓘ` icon next to the section title — opens a slide-in drawer |
| **Example Entries** | 2–4 realistic worked examples drawn from the operator's own historical data (anonymized) where possible · else from doctrine-curated samples | small `✎` "Show example" link beneath the section header |
| **Crew-Specific Guidance** | a 4–6 bullet list of tips for the current `crew_profile.crew_type` + `primary_operation` (pipe / paving / MOT / etc.) | a calm pill at the top of the section: `Tips for pipe crews` — opens a drawer |
| **Best Practices** | the doctrine reference for this section, linked to `Operational Guidance Center` | a small "Best practices" footer link — opens a drawer with deep link to the Guidance Center entry |

All four touchpoints are **opt-in** taps. None block entry. None
pre-open by default after first dismissal.

---

## 3 · Sections that gain guidance touchpoints (12 total)

The four touchpoints are **architecturally available** on every
ODR section, but the V.1 launch exposes them on these 12 sections
where coaching value is highest:

1. Crew Profile · Section 2
2. Work Areas · Section 2.5
3. Manpower · Section 3
4. Equipment · Section 4
5. Subcontractors / Vendors · Section 5
6. Materials · Section 5.5
7. Production · Section 6 (template-specific)
8. Delays · Section 7
9. Extra Work · Section 8
10. Constraints · Section 9
11. Safety · Section 10
12. Photos · Section 12 + Tomorrow Plan · Section 13

Remaining sections (Project Snapshot · Manpower autoload · Weather
Impact · Plan vs Actual · Readiness · PM Review) ship without
touchpoints by default — their content is auto-filled or trivial.

---

## 4 · Crew-specific guidance content map (O44)

A `guidance_catalog` (read from `frontend/src/lib/guidance/*` plus
backend canonical text) provides crew-specific bullets. The catalog
is **planned · architecture-only**, not yet authored.

| Crew Type | Examples that ship in V.1 | Sample tips |
|---|---|---|
| Pipe | pipe sizes, structure types, utility-conflict patterns | "Record bedding type per run · separate runs by station break · capture compaction percent + test method" |
| Paving | mix codes, lift sequence, temperature ranges | "Record mix temperature at lay-down · separate by lift · capture station limits per lift" |
| Grading / Fine Grade | proof-roll, density, blue-tops | "Note proof-roll witness · capture failing stations · proof-roll photo helps claims" |
| Stabilization | depth, mix design, moisture | "Cite mix design number · note moisture variance" |
| Concrete | mix code, slump, air content | "Record mix design + slump + air at point of pour · ticket per truck" |
| Structures | structure type, station, depth | "Capture as-built deviation · photo of completed structure with stationing visible" |
| Curb / Sidewalk | LF type, joint count, ADA features | "Capture ADA ramp details · note joint spacing" |
| Milling | depth, station limits, surface condition | "Note depth per pass · capture surface condition before re-paving" |
| Paving (continued) | see above | — |
| MOT | closure type, hours active, deviations | "Document closure setup time · note any plan deviations · TMP reference helps claims" |
| Survey | control issues, staking activity, errors | "Note benchmark conflicts · staking error photos for claims" |
| Airfield | FAA escort, runway closures, security | "Cite FAA Form 7460 reference · note escort sign-in · operational restriction time windows" |
| Electrical | conduit, pull-boxes, energization | "Note as-built deviations · capture as-built conduit count" |
| Other | freeform guidance | "Describe operation in 1 sentence at start of report" |

Catalog is bilingual EN ↔ ES from day one (O43). Source of truth:
`Operational Guidance Center` rows; ODR pulls per `(crew_type,
primary_operation, lang)` triple.

---

## 5 · Readiness coaching vocabulary contract (O45)

The readiness engine (`ReadinessSnapshot` from DATA_MODEL § 3.15)
emits two kinds of items:

- `hard_stops: List[str]` — **rare** (Safety compliance only · O9)
- `coaching_prompts: List[str]` — **the default mode**

Vocabulary is governed:

| Allowed phrasing | Forbidden phrasing |
|---|---|
| "Add production quantities for stronger claims protection" | ❌ "Production quantities are missing" |
| "Tomorrow's plan helps the next crew" | ❌ "You didn't fill out tomorrow's plan" |
| "A photo here strengthens the record" | ❌ "Required: photo" |
| "Consider noting compaction percent" | ❌ "Compaction percent is incomplete" |
| "Crew-specific tip: …" | ❌ "Error: …" |

The vocabulary list is enforced by `verify_coaching_sublines.py`
(existing warning-only probe) which is extended to cover the
readiness output strings.

---

## 6 · First-time-user onboarding (O46)

Architecture (no UI build yet):

| Property | Value |
|---|---|
| When shown | first open of an ODR creation link, per `(device_fingerprint, project_id)` tuple |
| Length | target **≤ 2 minutes** of foreman time |
| Format | 4-card slide-show within the ODR shell (no full-screen takeover) |
| Cards | 1) "Welcome — this is your daily report" · 2) "Sections fill themselves where they can" · 3) "Tap ⓘ for tips on any section" · 4) "Submit when ready — you have 24h to edit after" |
| Dismissal | "Got it" button on card 4 + a "Skip for now" link visible on every card |
| State | stored in localStorage keyed to `(fingerprint, project_id)` · admin can reset for a project from Admin portal |
| Bilingual | EN + ES (O43) |
| Mandatory? | **never** — fully optional |

Re-access: top-right help menu → "Quick start" launches the same
4-card sequence; Operational Guidance Center carries an evergreen
copy.

---

## 7 · Field Leadership Training Center (O47)

A new sub-surface under `/field-leadership/portal/training`. Read-
only for all FL roles. Sections:

- **Best Practices** — doctrine references organized by ODR section
- **Examples** — anonymized real-day examples by crew type
- **Quality Guidance** — what makes an ODR claims-defensible
- **Coaching Metrics** (aggregated · never per-foreman):
  - % of submitted ODRs with all photos for production runs
  - % of submitted ODRs with tomorrow plan filled
  - % of submitted ODRs with at least one delay categorized
  - % of submitted ODRs with non-zero materials
  - Distribution of coaching prompts per section (which sections
    most often trigger coaching)

Source data: `odr_section_events` + `ReadinessSnapshot` history.
**No individual foreman ever appears in this surface.**

The Training Center is the **Superintendent-facing analog** of the
Operational Guidance Center (which is the platform-wide canonical
doctrine). FL Training surfaces curate guidance Center content for
field-team consumption.

---

## 8 · PM Portal coaching consumption surface (O48)

Added to the read-only PM ODR consumption panel
(`ODR_FINAL_GOVERNANCE_ADDENDUM.md § 5` + `ODR_UI_WIREFRAMES.md § G5`):

- **Completion trends** — aggregated by project · week-over-week ·
  per-section
- **Coaching opportunity trends** — same shape · which sections
  most often trigger coaching prompts on this project
- **Common missing information** — top 5 most frequently coached
  fields on this project

These three views surface **training opportunities**, not
disciplinary leads. The PM panel never lists per-foreman counts,
per-foreman names, or per-foreman scores.

Per O22 + O50, PM may **act** on these trends only by:

- Requesting Field Leadership scheduling of training topics
- Adding doctrine references to the Operational Guidance Center
  (via authenticated admin)

PM cannot escalate a coaching trend into a foreman performance
review through the platform.

---

## 9 · Single-source-of-truth guidance content layer (O43)

```
                   Operational Guidance Center
                   (canonical doctrine · bilingual)
                            │
            ┌───────────────┼───────────────┐
            ▼               ▼               ▼
   ODR inline drawers   FL Training      PM coaching
   (Learn More /         Center           consumption
    Examples /           (Super+)         (read-only)
    Crew Tips /
    Best Practices)
            │
            └─→ first-time onboarding (4 cards)
            └─→ help menu "Quick start"
            └─→ Spanish parity via shared i18n string tables
```

There is **one canonical store** for guidance content
(`guidance_catalog` · backend + i18n string tables). Every surface
listed above reads from it. There is **no second guidance system,
no per-portal duplication**, and no risk of EN/ES divergence
without `odr_bilingual_probe.py` (D8) failing the deploy.

---

## 10 · Architecture deltas (lightweight · architecture-only)

The coaching layer **does not introduce any new ODR collection**.
It introduces:

| New artefact | Type | Owner |
|---|---|---|
| `guidance_catalog` (planned) | backend module + i18n string tables | Operational Guidance Center editors (admin role) |
| `coaching_metrics_view` (planned) | derived rollup over `odr_section_events` + `ReadinessSnapshot` history | system (materialized · refreshed nightly + incremental) |
| `onboarding_state` (planned) | localStorage entry keyed to `(fingerprint, project_id)` | client-only |

The existing collections (`odr · odr_section_events · odr_amendments
· odr_translation_events · odr_preload_attempts · odr_attachments
· odr_photos · odr_consumer_index`) are **unchanged**.

Per-section guidance content is referenced from inside the
`ReadinessSnapshot.coaching_prompts` via a `prompt_key` (planned ·
opaque slug) so prompts and their guidance content stay coupled
across language versions.

---

## 11 · Probe extensions (planned · architecture-only)

`verify_coaching_sublines.py` (existing warning-only probe) extends
to cover:

1. Every `coaching_prompts[]` string in shipping code is from the
   approved vocabulary list (§ 5 above).
2. No coaching string uses "Error", "Required", "Missing",
   "Failed", "Incomplete", or other punitive language.
3. Every `prompt_key` referenced has both EN and ES guidance
   content in the catalog (overlap check with
   `odr_bilingual_probe.py`).
4. Every crew_type has at least 4 crew-specific guidance bullets
   in the catalog.
5. The Training Center coaching-metrics queries never expose a
   per-foreman row (grep-level + integration-test check).
6. The PM coaching consumption surface never exposes a per-foreman
   row.

Mode: **WARN** for vocabulary drift (existing posture) ·
**HARD** for missing EN/ES parity (O43 hard contract).

---

## 12 · Doctrine anchors (O36–O50 → spec)

| Doctrine | Anchor |
|---|---|
| O36 ODR = coaching + intelligence | this addendum + UI guidance touchpoints |
| O37 teach while working | § 2 four touchpoints + inline drawers |
| O38 coaching primary · rejection secondary | readiness engine emits coaching by default; hard-stop only for Safety (O9) |
| O39 multiple guidance modes | § 2 four touchpoints |
| O40 platform > foreman memory | § 2 + § 4 + § 6 onboarding |
| O41 Operational Guidance Center integration | § 9 single source diagram |
| O42 context-preserving guidance | inline drawers · no destructive navigation |
| O43 EN ↔ ES mirrored | § 9 i18n string tables + § 11 probe |
| O44 crew-specific | § 4 catalog map |
| O45 readiness coaches | § 5 vocabulary contract |
| O46 first-time onboarding | § 6 properties |
| O47 FL Training Center | § 7 surface |
| O48 PM coaching consumption | § 8 surface |
| O49 telemetry append-only · operator-strict on raw | existing append-only audit substrate covers it; aggregations are derived |
| O50 never performance-review evidence | hard contract anchored in § 7 + § 8 (no per-foreman rows) |

---

## 13 · How this addendum lands in each artifact

| Artifact | Update |
|---|---|
| `ODR_DATA_MODEL.md` | Adds `prompt_key` field to coaching items in `ReadinessSnapshot`; references `guidance_catalog` (no new collection) |
| `ODR_UI_WIREFRAMES.md` | Adds four guidance touchpoints to 12 sections · first-time onboarding 4-card flow · FL Training Center surface · PM coaching consumption surface · top-right help menu "Quick start" |
| `ODR_ECOSYSTEM_INTEGRATION_MAP.md` | Adds `guidance_catalog` as a shared cross-portal asset · coaching telemetry contract (append-only · aggregated-only consumer reads) · O50 anti-pattern (no per-foreman in PM/FL Training views) |
| `ODR_MIGRATION_PLAN.md` | Adds M0 step: ship `guidance_catalog` seed (12 sections × EN+ES) · staged crew-specific catalog rollout through M1–M2 · acceptance criterion: probe green |
| `ODR_SPEC_LOCK_READINESS_REVIEW.md` | Adds 8 new certifications (one per item in operator's 8-point checklist below) |
| `_INDEX.md` | Row for this addendum + the coaching certification |

Each artifact carries a short "Coaching / Guidance Addendum"
section at the end.

---

## 14 · Operator's 8-point pre-lock checklist (anchored)

| # | Required certification | Verdict | Anchor |
|---|---|---|---|
| 1 | Operational Guidance Center integration defined | ✅ | § 9 single-source diagram |
| 2 | English guidance path defined | ✅ | § 9 + § 4 (EN bullets) |
| 3 | Spanish guidance path defined | ✅ | § 9 + § 4 (ES bullets) + O43 |
| 4 | Crew-specific coaching defined | ✅ | § 4 catalog map (14 crew types) |
| 5 | Readiness coaching defined | ✅ | § 5 vocabulary contract |
| 6 | First-time onboarding defined | ✅ | § 6 properties |
| 7 | Field Leadership training architecture defined | ✅ | § 7 Training Center |
| 8 | PM visibility architecture defined | ✅ | § 8 coaching consumption surface |

8 / 8 ✅

---

## 15 · Stop condition honoured

- ✅ No implementation
- ✅ No code · no routes · no collections · no UI · no probe code
- ✅ Wave M0 NOT begun
- ✅ Architecture-only revision
- ✅ V-Prelude Observation Freeze on broader platform still intact

Awaiting operator spec-lock authorization.

_End of Coaching / Training / Guidance Addendum._
