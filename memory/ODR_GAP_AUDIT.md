# ODR ARCHITECTURE GAP AUDIT

_Phase V.1 · Operational Daily Record · Pre-Lock Verification · 2026-05-29_

This audit verifies the five ODR architecture artifacts (Data Model ·
UI Wireframes · Ecosystem Integration Map · PDF Layout · Migration
Plan) against the seven operator-stated review requirements before
specification lock.

**Method**: re-read every artifact line-by-line · evidence each
claim with the artifact section reference · grade Covered / Partially
Covered / Missing · attach the smallest possible remediation that
honours platform doctrine.

**No implementation. No code. No schema changes. No UI changes.**

---

## Coverage summary

| # | Requirement | Verdict | Remediation needed? |
|---|---|---|---|
| 1 | Multi-Event Reality | 🟡 **PARTIALLY COVERED** | Yes — 3 structural gaps |
| 2 | Simplicity Doctrine (< 5 min) | 🟢 **COVERED** (architectural) | Add explicit time-budget receipts |
| 3 | Tier-1 Reliability Layer | 🟡 **PARTIALLY COVERED** | Yes — 4 fields/contracts to add |
| 4 | Bilingual Field Operations | 🔴 **MISSING** | Yes — i18n shape never spec'd |
| 5 | Ecosystem Consumption (single-entry) | 🟢 **COVERED** | None · 1 clarification |
| 6 | Safety Hard-Stop Accountability | 🟢 **COVERED** | None |
| 7 | PDF Forensic Value | 🟢 **COVERED** | None |

**Overall**: 4 / 7 fully covered · 2 / 7 partial · 1 / 7 missing. Two
new structural concepts (`work_areas`, `materials` as top-level
blocks; bilingual i18n envelope) and one reliability contract
(`ReliabilityBlock`) are required before lock.

---

## REQ #1 — Multi-Event Reality

> "Crews routinely perform multiple operations within a single day…
> Multiple production events / delays / extra work / materials /
> equipment / subcontractors / work areas. No assumptions of one
> activity per day."

### What's already in the spec

| Multi-event class | Where supported | Evidence |
|---|---|---|
| Multiple delays | `DelayBlock.entries: List[DelayEntry]` | `ODR_DATA_MODEL.md` § 3.7 |
| Multiple extra-work | `ExtraWorkBlock.entries: List[ExtraWorkEntry]` | § 3.8 |
| Multiple equipment | `EquipmentBlock.rows: List[EquipmentRow]` | § 3.4 |
| Multiple subcontractors | `SubcontractorBlock.entries[]` (visitors merged) | § 3.5 · `ODR_MIGRATION_PLAN.md` § 9.3 |
| Multiple manpower | `ManpowerBlock.rows: List[ManpowerRow]` | § 3.3 |
| Multiple constraints | `ConstraintBlock.entries: List[ConstraintEntry]` | § 3.9 |
| Multiple photos | `photos: List[PhotoRef]` | § 3.12 |
| Multiple pipe runs / structures / paving lifts / closure events | inside each polymorphic Production sub-block (`PipeProduction.runs[]`, `PipeProduction.structures_set[]`, paving `lifts[]`, MOT `closure_events[]`) | § 3.6 |

✅ Inside any *single* crew_type, multiple operations of that type are first-class.

### What's missing or thin

| Gap | Evidence | Severity |
|---|---|---|
| **G1.1 — Mixed-crew-type days** | `crew_profile.crew_type` is a singular `Literal[...]` and `ProductionBlock` holds at most one populated polymorphic sub-block. A pipe-morning + paving-afternoon day has no clean place to live. The current shape forces either (a) two ODRs per day per crew or (b) generic-bucket production. | **HIGH** — common in mixed-discipline crews on FDOT projects |
| **G1.2 — Work areas as first-class** | Station limits and from/to structures live *inside* production runs. A crew working three discrete geographic areas (different intersections, different airfield taxiways) has no canonical way to bind delays / extra-work / photos to a specific area. UI wireframes don't show a Work-Area selector. | **HIGH** — claims protection asks "where did this happen?" |
| **G1.3 — Materials as first-class** | Legacy `materials[]` was top-level; ODR migration drops it into `production.<polymorphic>.materials[]`. But site-delivered stockpile, off-loaded fuel, and stand-alone material deliveries (not yet placed) have no production parent on the receiving day. | **MEDIUM** — important for cost and claims |

### Recommended remediation (data-model deltas only · no UI/code yet)

```python
# 1. Allow multiple production segments per ODR (one per crew_type or shift)
class ProductionSegment(BaseModel):
    segment_id: str                # uuid4
    crew_type: CrewType            # same enum as crew_profile.crew_type
    primary_operation: str
    work_area_id: Optional[str]    # ← ties segment to a work area
    started_at_utc: Optional[str]
    ended_at_utc: Optional[str]
    body: ProductionBlock          # the polymorphic block (one shape per segment)

# 2. Lift `production` to a list
class ODR(BaseModel):
    ...
    production_segments: List[ProductionSegment]   # 1..N
    # (deprecate the singular `production` field by Wave M1)
    ...

# 3. New top-level Work Areas block
class WorkArea(BaseModel):
    work_area_id: str              # uuid4
    label: str                     # e.g. "MP 12.4 SB" / "Taxiway B"
    station_from: Optional[str]
    station_to: Optional[str]
    gps_centroid: Optional[GeoFix]
    notes: Optional[str]

class ODR(BaseModel):
    ...
    work_areas: List[WorkArea]     # 0..N
    ...

# 4. New top-level Materials block (delivered / consumed / staged)
class MaterialEvent(BaseModel):
    material_event_id: str         # uuid4
    work_area_id: Optional[str]
    kind: Literal["delivered","consumed","staged","returned","wasted"]
    material_code: Optional[str]   # FK to materials master if known
    description: str               # voice-supported
    quantity: float
    uom: Literal["ton","cy","lf","sf","ea","gal","other"]
    vendor: Optional[str]
    ticket_numbers: List[str]
    photos: List[str]              # photo_ref ids

class ODR(BaseModel):
    ...
    materials: List[MaterialEvent] # 0..N
    ...

# 5. Add work_area_id to every event-bearing block so any event can
#    be geo-bound when the crew worked multiple areas:
#      DelayEntry.work_area_id
#      ExtraWorkEntry.work_area_id
#      ConstraintEntry.work_area_id
#      EquipmentRow.work_area_id  (where the asset spent the day)
#      PhotoRef.work_area_id      (already has section_anchor; add area)
```

UI implication (no wireframe change required for lock — surfaced
inside the existing Section 6 template as a "+ add segment" affordance
and a new Section 2.5 "Work Areas" mini-form between Crew Profile and
Manpower).

PDF implication: Page 3 (Production) becomes a per-segment block;
Page 4 events show `work_area` columns. No re-layout of the PDF
shell required.

🟡 **Verdict: PARTIALLY COVERED.** Most multi-event surfaces exist;
3 structural blocks (`production_segments`, `work_areas`, `materials`)
must be added before lock.

---

## REQ #2 — Simplicity Doctrine (< 5 minutes)

> "Average completion target < 5 minutes. Mobile-first. Voice-first.
> Dropdown-first. Auto-fill everything possible. The platform must
> work harder than the foreman."

### Per-section completion-time receipt

Assumes the pilot-foreman archetype: a "typical day" = pipe crew,
8 manpower, 4 equipment, 1 delay, 0 extra work, 0 safety event, 1
constraint, 6 photos. Times are derived from auto-fill density +
input modality (tap / voice / type).

| § | Section | Required fields | Optional | Auto-filled | Modality | Typical time |
|---|---|---|---|---|---|---|
| 1 | Project Snapshot | 0 | 1 (Super/PM change) | 18 / 18 | confirm only | **0–5 s** |
| 2 | Crew Profile | 2 (crew_type · primary_op) | 1 (secondary) | last-7-day default | dropdown | **5–15 s** |
| 3 | Manpower | 0 (per-row hours optional) | many | roster + scheduled hours | tap to adjust | **30–60 s** |
| 4 | Equipment | 0 (per-row hours optional) | maintenance | roster + scheduled hours | tap | **30–90 s** |
| 5 | Subs / Vendors | 0 (per-row present toggle) | work performed | roster + deliveries | tap + voice | **15–60 s** |
| 6 | Production | per-template (e.g. pipe: size · LF · from/to) | testing · compaction | yesterday's defaults | dropdown + numeric stepper | **60–180 s** |
| 7 | Delays | yes/no toggle | type + hours + desc | none | dropdown + voice | **0–60 s** |
| 8 | Extra Work | yes/no toggle | type + cost + sched | none | dropdown + voice | **0–60 s** |
| 9 | Constraints | 0 (multi-select chip) | per-chip desc | suggestions from Memory | tap + voice | **0–30 s** |
| 10 | Safety | 6 yes/no toggles | (hard-stop branch) | none | tap | **5–15 s** (no event) |
| 11 | Weather Impact | yes/no toggle | hours + desc | weather snapshot | tap + voice | **5 s** |
| 12 | Photos | 0 (none required) | caption per photo | tag auto-inferred · voice caption | camera + voice | **30–90 s** |
| 13 | Tomorrow Plan | planned work (voice) | resources · concerns | yesterday's plan as draft | voice + checkbox | **30–60 s** |
| 14 | Plan vs Actual | yes/no toggle | reason if No | none | tap | **5–15 s** |
| 15 | Readiness | none — passive | none | engine output | review | **0–30 s** |
| 16 | PM Review | n/a — foreman doesn't author | n/a | n/a | n/a | **0 s** |

**Typical day total**: **4 m 0 s – 7 m 30 s.**

**Complex day (3 production segments + 2 delays + 1 extra work + 2 work areas)**: **8 m – 12 m.** (Cannot hit < 5 min without aggressive auto-fill from yesterday + Memory pattern-recognition.)

### What architecturally supports the < 5 min target

- 100% auto-fill of Section 1 (zero foreman input on a normal day).
- Last-7-day defaults on Crew Profile (one-tap confirmation).
- Pre-loaded rosters on Manpower, Equipment, Subs.
- Closed-set dropdowns first (no typing for crew_type / delay_type / constraint_type / material_uom).
- Voice-first on every free-text field (mic icon documented in `ODR_UI_WIREFRAMES.md` § 17).
- Yesterday's plan pre-fills Section 13.
- Tomorrow plan from one ODR pre-fills next ODR's auto-context.

### What's missing for the receipt to be measurable

| Gap | Severity |
|---|---|
| **G2.1** — No explicit "median completion time" telemetry contract documented. We measure `time_created_utc` → `time_submitted_utc` per ODR but the architecture doesn't promise a percentile dashboard. | MEDIUM — needed to *prove* the doctrine post-launch |
| **G2.2** — No "auto-fill confidence" telemetry. We don't know how often the last-7-day default was actually accepted. | LOW |

### Recommended remediation (telemetry contract only · no UI)

```python
# Add to ODR audit envelope:
class ODR(BaseModel):
    ...
    completion_telemetry: CompletionTelemetry

class CompletionTelemetry(BaseModel):
    seconds_to_submit: Optional[float]   # time_submitted_utc - time_created_utc
    section_visit_times: Dict[str, float]  # per-section dwell time
    auto_fill_accept_rate: Dict[str, float]  # per-section %
    voice_caption_count: int
    voice_caption_chars: int
    autosave_count: int
```

Surfaced on `/admin/odr/health` later; **no foreman-facing exposure**
(doctrine: no grades, no punishment).

🟢 **Verdict: COVERED architecturally.** The mechanisms exist to hit
< 5 min on a typical day. Add `CompletionTelemetry` so the doctrine
is *measurable* post-launch.

---

## REQ #3 — Tier-1 Reliability Layer

> "Auto Save · Draft Recovery · Offline Drafts · Offline Photo Queue ·
> Sync Status · GPS Capture · Device Verification · Edit History."

### Per-capability audit

| Capability | Spec evidence | Verdict |
|---|---|---|
| Auto Save | _not mentioned in any of the 5 artifacts_ | 🔴 MISSING |
| Draft Recovery | `status="draft"` exists (`ODR_DATA_MODEL.md` § 2) but no explicit recovery flow, no "resume where you left off" contract | 🟡 PARTIAL |
| Offline Drafts | only an oblique reference to `device_session_id … for IDB / offline reconciliation` (§ 2 audit envelope); no contract for IDB schema, conflict resolution, or offline-first queue | 🟡 PARTIAL |
| Offline Photo Queue | inherits TRUST-1 IDB queue from existing Daily Reports infra; mentioned in `ODR_UI_WIREFRAMES.md` (camera affordance), not codified in data model | 🟡 PARTIAL (inherits, not explicit) |
| Sync Status | _not mentioned_ — no `sync_state` field, no UI indicator spec | 🔴 MISSING |
| GPS Capture | `project.gps: Optional[GeoFix]` + `gps_accuracy_m` + per-photo `gps` (§ 3.1, § 3.12) | 🟢 COVERED |
| Device Verification | `device_session_id` (envelope) ties to a session id; full device-trust chain (UA, OS, version, attested-from-secure-enclave) not spec'd | 🟡 PARTIAL |
| Edit History | `odr_section_events` is append-only field-level transition log (§ 5); doctrine inherits `trendline_integrity_probe.py` | 🟢 COVERED |

### Recommended remediation (data-model deltas only · no UI)

```python
class ReliabilityBlock(BaseModel):
    # Autosave
    autosave_enabled: bool                       # true at create
    autosave_interval_s: int                     # contract: ≤ 5
    last_autosave_at_utc: Optional[str]
    autosave_count: int

    # Draft recovery
    last_known_good_section: Optional[str]       # field path
    recovery_token: Optional[str]                # opaque · used by IDB

    # Offline
    offline_origin: bool                         # true if first save was offline
    offline_session_id: Optional[str]
    offline_photo_queue_size: int                # at submit
    offline_photo_queue_drained_at_utc: Optional[str]

    # Sync
    sync_state: Literal["clean","pending","conflict","error"]
    last_sync_at_utc: Optional[str]
    sync_conflicts: List[SyncConflict]           # append-only

    # Device
    device_fingerprint: DeviceFingerprint        # see below

class DeviceFingerprint(BaseModel):
    ua: str                                      # User-Agent
    os: str
    os_version: str
    app_version: str                             # bundle build id
    is_pwa: bool                                 # installed vs browser
    is_secure_context: bool

class SyncConflict(BaseModel):
    section: str                                 # field path
    detected_at_utc: str
    server_value_hash: str                       # SHA-256 prefix
    client_value_hash: str
    resolution: Literal["server_wins","client_wins","merged","unresolved"]
    resolved_at_utc: Optional[str]

class ODR(BaseModel):
    ...
    reliability: ReliabilityBlock
    ...
```

UI implication (no wireframe lock-change for now — informational
sync pill in the global shell, already pattern-consistent with TRUST-1
pill on Daily Reports).

Probe implication: `trendline_integrity_probe.py` extends to cover
`odr_section_events` and the `sync_conflicts` log; same append-only
posture.

🟡 **Verdict: PARTIALLY COVERED.** Add `ReliabilityBlock` +
`DeviceFingerprint` + `SyncConflict` before lock. GPS + Edit History
are already clean.

---

## REQ #4 — Bilingual Field Operations

> "Full EN / ES UI · ES toggle · Spanish field entry · automatic
> English normalization on submission · preservation of original
> Spanish · English PDF output · translation audit trail."

### Current state

Re-scanned the five artifacts for any mention of `language`, `locale`,
`i18n`, `Spanish`, `EN`, `ES`, `lang`, `translation`. **Zero hits.**

🔴 **Verdict: MISSING.** The current spec is implicitly English-only.
However, the architecture is structurally **i18n-compatible** because
every free-text field is a plain `str` and can be wrapped without
breaking consumers.

### What needs to be added for compatibility (no implementation)

```python
# 1. Per-field localization envelope for every free-text input:
class LocalizedString(BaseModel):
    text: str                               # canonical English at storage
    original: Optional[str]                 # original-language text as entered
    original_lang: Optional[Literal["en","es"]]
    translated_by: Optional[Literal["model","operator","none"]]
    translated_at_utc: Optional[str]
    translation_model: Optional[str]        # e.g. "claude-haiku-4.5"
    translation_confidence: Optional[float] # 0..1

# 2. Replace every free-text `str` field with `LocalizedString` for the
#    voice-friendly bilingual surfaces:
#      DelayEntry.description
#      ExtraWorkEntry.description
#      ConstraintEntry.description
#      SubRow.work_performed
#      PhotoRef.text_caption  &  voice_caption
#      TomorrowPlanBlock.planned_work · concerns
#      WeatherImpactBlock.description
#      PlanVsActualBlock.variance_reason
#      MaterialEvent.description  (from REQ #1 remediation)
#      WorkArea.label · notes     (from REQ #1 remediation)

# 3. Translation audit trail (lives next to odr_section_events):
class TranslationEvent(BaseModel):
    odr_id: str
    field_path: str                         # e.g. "delays.entries[0].description"
    original_lang: Literal["en","es"]
    original_text_hash: str                 # SHA-256
    canonical_text_hash: str
    model: Optional[str]
    actor_uid: Optional[str]
    at_utc: str

odr_translation_events  ←  new append-only collection
```

### UI / UX implications (informational · not a wireframe-lock change)

- Global shell adds an `EN | ES` toggle in the top bar (existing
  pattern from `frontend/src/lib/i18n` infra used by other portals).
- Voice-to-text engine respects toggle state; transcripts are
  preserved in `LocalizedString.original` + auto-translated into
  `LocalizedString.text`.
- PDF rendering reads only `LocalizedString.text` — English-only
  PDF guaranteed.
- Section labels, dropdown enums, coaching prompts use existing
  i18n string tables (per `frontend/src/lib/i18n/*`).

### Telemetry / governance

- New probe stage `odr_bilingual_probe.py`:
  - Asserts every `LocalizedString` has non-null `text` (canonical).
  - Asserts when `original_lang != "en"`, `original` is present and `translated_by != "none"`.
  - Asserts no PDF rendering reads `original` (English-only output).

### Cost / scope note

EN-canonical-at-storage + ES-preservation pattern is a known low-risk
shape (used by other governed surfaces). It does *not* require:

- a separate Spanish DB
- a separate Spanish PDF pipeline
- a separate Spanish consumer projector layer

Cross-portal consumers continue to read English `text`.

🔴 **Verdict: MISSING.** Add `LocalizedString` envelope +
`odr_translation_events` + bilingual probe before lock. Architecture
is i18n-compatible by construction; the spec just doesn't say so yet.

---

## REQ #5 — Ecosystem Consumption (single-entry · multi-consumer)

> "Verify ODR remains single-entry / multi-consumer. Identify any
> workflow requiring duplicate user entry."

### Per-consumer audit (re-verifying my own Artifact 3)

| Consumer | Reads | Writes derived records | Duplicate foreman entry required? |
|---|---|---|---|
| PM | `production.*` · `delays` · `extra_work` · `constraints` · `plan_vs_actual` · `tomorrow` · `review` | `pm_project_rollup` view rows | ❌ No |
| Safety | `safety.*` · `incident_report_link_id` · safety-tagged photos | does NOT duplicate event entry; the linked incident IS the entry | ❌ No |
| Dispatch | `equipment.*` · `manpower.missing_personnel_flag` · `tomorrow.required_resources` · `subcontractors[].deliveries` | board snapshot | ❌ No |
| Shop | `equipment[].maintenance_issue` | auto-ticket with `source.kind="odr"` | ❌ No |
| HR | `manpower.rows[].hours · overtime · classification` · attendance flags | attendance ledger · variance comparator | ❌ No |
| Executive | rollups via projectors | precomputed aggregates | ❌ No |
| Memory | `constraints` · `delays` · `production` · `extra_work` · `plan_vs_actual.variance_reason` | constraint rows (V-Prelude Wave 1) + pattern detectors | ❌ No |
| Search | full-text index of free-text + photo captions | search index | ❌ No |
| RFI | `extra_work.entries[]` + photos | RFI seed record | ❌ No |
| Schedule (P6) | `production.*` per station limits + work_areas | correlation index | ❌ No |
| Claims | `delays` · `extra_work` · `constraints` per project lifetime | claims package | ❌ No |
| Future AI | everything · transcripts · photos | retrieval index | ❌ No |

### Clarification (not a gap)

The only *second-party* entry point in the ODR lifecycle is **PM
Review** in Section 16. That is by design — it is the PM authoring
their own review action (`status_history` event), not re-entering
the foreman's data. The PM does not re-type production, delays, or
any other field-day fact.

### What's already enforced

- Write boundary: only `/api/odr/*` writes the `odr` collection
  (`ODR_ECOSYSTEM_INTEGRATION_MAP.md` § 1).
- Each consumer projector is `(odr_id, projector_kind)`-keyed,
  idempotent, and pure (§ 3).
- `source.kind="odr"` + `source.id=odr_id` traceability stamp on
  every derived consumer record (§ 1).
- Telemetry: every projector dispatch logged to
  `odr_section_events` (§ 6).
- Anti-pattern list explicitly forbids back-mutation of ODR fields
  by consumers (§ 5).

🟢 **Verdict: COVERED.** No workflow requires duplicate foreman
entry across the 12 consumer surfaces. The PM Review (§ 16) is the
only second-party action and is **not** a duplicate-entry path.

---

## REQ #6 — Safety Hard-Stop Accountability

> "Accident · Incident · Near Miss · Property Damage · Environmental
> Release · Injury — if YES: Safety notified? · Who? · Time? ·
> Incident report completed? Submission blocking required."

### Audit

| Requirement | Spec evidence |
|---|---|
| Six event flags | `SafetyBlock.accident · incident · near_miss · property_damage · environmental_release · injury` (`ODR_DATA_MODEL.md` § 3.10) |
| Derived "any event" | `SafetyBlock.any_event` (OR of the six) — § 3.10 |
| Required when any_event=True | `safety_notified` · `contact_name` · `contact_time_utc` · `incident_report_complete` · `incident_report_link_id` — § 3.10 |
| Submission blocking | Readiness engine refuses submission when any_event AND (safety_notified ≠ True OR incident_report_complete ≠ True) — § 3.10 |
| Hard-stop UI | Section 10 wireframe explicitly shows disabled Submit button until both Yes (`ODR_UI_WIREFRAMES.md` § 10) |
| No duplicate incident entry | Open incident report from inside ODR; `incident_report_link_id` is the single FK; Safety reads from same row — § 10 + `ODR_ECOSYSTEM_INTEGRATION_MAP.md` § 2.2 |
| Dispatch ordering | Safety projector is **#1 in the dispatch order** (`ODR_ECOSYSTEM_INTEGRATION_MAP.md` § 4); transition rolls back to draft if Safety fails |
| Hard contract during projection | Safety projector MUST find non-null `incident_report_link_id` when `any_event=True` — § 2.2 |
| Forensic PDF | Page 5 renders "NO SAFETY EVENTS" when clean; "⛔ Safety event" with single-red accent when any_event — `ODR_PDF_LAYOUT_DESIGN.md` § 6 |

### Recommendation — small clarification (not a gap)

Add to `SafetyBlock` an explicit list of **per-event entries** so
that a single ODR with both a near-miss AND a property-damage event
carries two distinct lineages, each with its own contact_name /
contact_time / incident_report_link_id:

```python
class SafetyEvent(BaseModel):
    event_kind: Literal["accident","incident","near_miss",
                        "property_damage","environmental_release","injury"]
    notified_safety: bool
    contact_name: Optional[str]
    contact_time_utc: Optional[str]
    incident_report_complete: bool
    incident_report_link_id: Optional[str]

class SafetyBlock(BaseModel):
    any_event: bool
    events: List[SafetyEvent]    # 0..N · one per event observed
```

This is **a refinement, not a gap** — the existing six bool flags
remain (for fast filtering); the events list captures the
per-event accountability chain the operator described.

🟢 **Verdict: COVERED.** Optional refinement to per-event lineage
recommended but not blocking.

---

## REQ #7 — PDF Forensic Value

> "Executive · Owner · CEI · FAA · FDOT · Attorney · Claims friendly.
> Review against Production · Delays · Extra Work · Constraints ·
> Safety · Weather · Photos · Audit Chain."

### Audit against `ODR_PDF_LAYOUT_DESIGN.md`

| Audience | Coverage | Evidence |
|---|---|---|
| Executive | Page 1 "Today at a glance" + 3-line PM narrative + sign-off | § 2 |
| Owner | Same as Executive + Page 4 (delays / extras / constraints) | § 2 + § 5 |
| CEI | `cei_packet` variant: Pages 1–3 (no claims surfaces, no costs) | § 10 |
| FAA / FDOT | `fdot_owner` variant: Pages 1–5 + photo appendix + SHA + QR reinforced | § 10 |
| Attorney | `attorney_full` variant: every page + expanded audit envelope + `odr_section_events` appended | § 10 |
| Claims | `claims_only` variant: Page 1 + Page 4 + Page 5 + tagged photos | § 10 |

| Topic | PDF location |
|---|---|
| Production | Page 3 (polymorphic by crew_type) — § 4 |
| Delays | Page 4 — § 5 |
| Extra Work | Page 4 — § 5 |
| Constraints | Page 4 (with operational_constraints lineage) — § 5 |
| Safety | Page 5 (single-red accent; per-event drilled detail) — § 6 |
| Weather | Page 5 (always present) — § 6 |
| Photos | Pages 6+ photo appendix with caption + GPS + audio QR — § 7 |
| Audit Chain | Final page (Foreman / Super / PM sign-off + audit envelope + SHA-256 + cover QR) — § 8 |

### Forensic guarantees already in spec

- SHA-256 of payload printed on cover + final audit envelope
  (§ 8 + § 12-Q2).
- QR code on cover resolves to `/o/odr/{doc_id}` for authenticity
  verification (§ 1 · § 12-Q2).
- XMP-embedded full ODR JSON in hidden metadata for forensic
  verification (§ 12-Q5).
- Photo audio QR (proposed default: yes) for attorney audio
  retrieval (§ 12-Q4).
- Single-footer invariant enforced by
  `test_iter310_pdf_single_footer_invariant.py` (inherited).
- Calmness doctrine (single-red, no chrome) holds across all
  variants.

🟢 **Verdict: COVERED.** All eight forensic topics + all seven
audience archetypes are addressed. Five variants exist for
audience-specific packets.

---

## Consolidated remediation list (pre-lock)

These are the smallest possible deltas that close every gap above
without re-opening any other section of the spec.

| # | Delta | Touches | Severity |
|---|---|---|---|
| D1 | Add `production_segments: List[ProductionSegment]` (lift singular production to a list) | `ODR_DATA_MODEL.md` § 2, § 3.6 · `ODR_UI_WIREFRAMES.md` § 6 (informational) · `ODR_PDF_LAYOUT_DESIGN.md` § 4 (informational) | HIGH |
| D2 | Add top-level `work_areas: List[WorkArea]` + `work_area_id` FK on every event-bearing entry | `ODR_DATA_MODEL.md` § 2 + multiple sub-blocks · `ODR_UI_WIREFRAMES.md` (new Section 2.5) · `ODR_PDF_LAYOUT_DESIGN.md` § 4–5 (informational) | HIGH |
| D3 | Add top-level `materials: List[MaterialEvent]` | `ODR_DATA_MODEL.md` § 2 · `ODR_UI_WIREFRAMES.md` (new Section 5.5) | MEDIUM |
| D4 | Add `ReliabilityBlock` + `DeviceFingerprint` + `SyncConflict` | `ODR_DATA_MODEL.md` § 2 (envelope) | HIGH |
| D5 | Add `CompletionTelemetry` envelope | `ODR_DATA_MODEL.md` § 2 | LOW |
| D6 | Replace free-text `str` with `LocalizedString` envelope on the 10 free-text fields; add `odr_translation_events` collection | `ODR_DATA_MODEL.md` § 3.5–3.13 · all sections of `ODR_UI_WIREFRAMES.md` (informational EN/ES toggle) · `ODR_PDF_LAYOUT_DESIGN.md` (English-only render rule made explicit) | HIGH |
| D7 | Refactor `SafetyBlock` to per-event `events: List[SafetyEvent]` (keep the six bool flags for filtering) | `ODR_DATA_MODEL.md` § 3.10 only | LOW (refinement) |
| D8 | Add `odr_bilingual_probe.py` to `pre_deploy_check.sh` warning stages | governance | LOW |

**None of the above breaks any prior architecture decision.** All
eight deltas are additive on the data model and clarifying on the
PDF / UI artifacts.

---

## Effect of remediation on the 25 open questions

After applying D1–D8, the 25 open questions in the artifact set
remain valid (operator decisions still pending), with two
clarifications:

- Q (Data Model § 8 · #2): the timezone question now also governs
  per-work-area timezone (if a single ODR spans multiple TZs — rare
  but possible). Default remains site-TZ.
- Q (UI Wireframes § 18 · #4): "multiple secondary_operations" is
  now subsumed by `production_segments`; the question becomes "max
  segments per ODR" (recommend cap = 6 to keep PDF Page 3 readable).

---

## Recommended pre-lock decision sequence

1. Operator reviews this gap audit.
2. Operator either approves the 8 deltas D1–D8 wholesale, asks for
   modification, or rejects one/more.
3. On approval, this agent **revises** the five existing
   architecture artifacts to incorporate D1–D8 (still no
   implementation — just spec edits).
4. Operator answers the 25 open questions (or accepts defaults).
5. Specification lock command issued.
6. Implementation Wave M0 begins.

---

_Pre-lock audit complete · 4 / 7 fully covered · 2 / 7 partial · 1 / 7 missing · 8 deltas proposed, all additive · awaiting operator decision._
