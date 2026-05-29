# ODR DATA MODEL

_Phase V.1 · Operational Daily Record · Architecture Artifact 1 of 5 · 2026-05-29_

The Operational Daily Record (ODR) is the **system of record** for
all field-day intelligence on the MASCI platform. One document per
crew per day per project. Multiple consumers, zero duplicate
reporting.

This document specifies the Pydantic / Mongo schema, the closed-set
enumerations, the audit envelope, the indexing strategy, and the
cross-consumer projection rules.

---

## 1 · Collection layout

| Mongo collection | Cardinality | Owner-write | Cross-portal-read |
|---|---|---|---|
| `odr` | 1 per (project_number, crew_id, report_date) | FL author + Super | PM · Safety · Dispatch · Shop · HR · Exec · Search · Memory |
| `odr_photos` (registry) | N per ODR | FL author | PM · Safety · Exec · PDF renderer |
| `odr_section_events` | N per ODR · append-only telemetry | system | governance only |
| `odr_consumer_index` | derived materialized view | system | per-consumer fast lookup |

Indexes (initial set · others added by usage analytics):

- `odr`: `{ project_number: 1, report_date: -1, crew_id: 1 }` (covering)
- `odr`: `{ report_date: -1 }` (global by-date scan)
- `odr`: `{ "crew_profile.crew_type": 1, report_date: -1 }` (Exec/HR rollups)
- `odr`: `{ "status": 1, report_date: -1 }` (PM Review queue)
- `odr_photos`: `{ odr_id: 1, tag: 1 }`
- `odr_section_events`: `{ odr_id: 1, ts: 1 }` (append-only — TTL not applied)

---

## 2 · Top-level envelope (Pydantic outline)

```python
class ODR(BaseModel):
    # ── Identity ──
    id: str                              # uuid4
    doc_id: str                          # ODR-YYYY-NNNNN (year-scoped sequence)
    schema_version: int                  # 1 at launch; bump on breaking change
    legacy_daily_report_id: Optional[str] # FK back to retired daily_reports row
                                          # (populated only for migrated rows)

    # ── Section 1 · Project Snapshot ──
    project: ProjectSnapshot

    # ── Section 2 · Crew Profile ──
    crew_profile: CrewProfile

    # ── Section 3 · Manpower ──
    manpower: ManpowerBlock

    # ── Section 4 · Equipment ──
    equipment: EquipmentBlock

    # ── Section 5 · Subcontractors / Vendors ──
    subcontractors: SubcontractorBlock

    # ── Section 6 · Production (polymorphic by crew_type) ──
    production: ProductionBlock

    # ── Section 7 · Delays ──
    delays: DelayBlock

    # ── Section 8 · Extra Work ──
    extra_work: ExtraWorkBlock

    # ── Section 9 · Constraints ──
    constraints: ConstraintBlock        # → operational_constraints links

    # ── Section 10 · Safety Compliance ──
    safety: SafetyBlock                 # hard-stop logic lives here

    # ── Section 11 · Weather Impact ──
    weather_impact: WeatherImpactBlock

    # ── Section 12 · Photos (tagged registry refs) ──
    photos: List[PhotoRef]              # → odr_photos by id

    # ── Section 13 · Tomorrow Plan ──
    tomorrow: TomorrowPlanBlock

    # ── Section 14 · Plan vs Actual ──
    plan_vs_actual: PlanVsActualBlock

    # ── Section 15 · Readiness Check ──
    readiness: ReadinessSnapshot        # last evaluation by readiness engine

    # ── Section 16 · PM Review (Phase 2) ──
    review: ReviewBlock                 # statuses: draft|submitted|returned|approved

    # ── Audit envelope (TRUST-TIME-1 doctrine) ──
    status: Literal["draft","submitted","returned","approved"]
    created_at: str        # UTC Z-suffixed ISO
    submitted_at: Optional[str]
    last_edited_at: str
    last_edited_by_uid: str
    submitted_by_uid: Optional[str]
    location_at_submit: Optional[GeoFix]
    location_accuracy_m: Optional[float]
    device_session_id: Optional[str]    # for IDB / offline reconciliation
    schema_violations: List[str]        # readiness engine output
    consumer_dispatch: Dict[str, str]   # per-consumer last-projected-at
```

---

## 3 · Sub-blocks (key fields only · full registry separately)

### 3.1 `ProjectSnapshot` (Section 1)

```python
class ProjectSnapshot(BaseModel):
    project_id: str                # FK → jobs_master
    project_number: str            # denormalized
    project_name: str              # denormalized
    contract_number: Optional[str]
    report_date: str               # YYYY-MM-DD (UTC date — local converted client-side)
    day_number: Optional[int]      # 1-based day-on-project, computed
    gps: Optional[GeoFix]
    gps_accuracy_m: Optional[float]
    time_created_local: str        # client-local for human display
    time_created_utc: str          # Z-suffixed UTC
    time_submitted_utc: Optional[str]
    foreman_uid: str
    foreman_name: str              # denormalized
    superintendent_uid: Optional[str]
    superintendent_name: Optional[str]
    pm_uid: Optional[str]
    pm_name: Optional[str]
    weather: WeatherFix            # NOAA / OpenWeather pull at create
    weather_pulled_at_utc: str
```

### 3.2 `CrewProfile` (Section 2)

```python
class CrewProfile(BaseModel):
    crew_id: str                   # FK → existing crews/foremen master
    crew_name: str                 # denormalized
    crew_type: Literal[
        "pipe","utility","grading","fine_grade","stabilization",
        "concrete","structures","curb","sidewalk","milling","paving",
        "mot","survey","airfield","electrical","other",
    ]
    primary_operation: str         # closed-set per crew_type · drives § 6 template
    secondary_operations: List[str] = []
```

### 3.3 `ManpowerBlock` (Section 3)

```python
class ManpowerRow(BaseModel):
    employee_uid: str              # FK → employees
    name: str                      # denormalized
    role: str                      # foreman/operator/laborer/etc · from employee master
    classification: Optional[str]  # craft code
    present: bool
    hours: float                   # 0.0–24.0
    overtime_hours: float          # 0.0–16.0
    absent_reason: Optional[str]
    missing_personnel_flag: bool   # set by auto-load when expected but absent

class ManpowerBlock(BaseModel):
    rows: List[ManpowerRow]
    total_hours: float             # derived
    total_overtime: float          # derived
```

### 3.4 `EquipmentBlock` (Section 4)

```python
class EquipmentRow(BaseModel):
    equipment_id: str              # FK → equipment master
    asset_tag: str                 # denormalized
    description: str
    hours: float
    idle_hours: float
    down_hours: float
    utilization_pct: float         # derived (working / total)
    maintenance_issue: Optional[MaintenanceIssue]   # if non-null → Shop visibility

class MaintenanceIssue(BaseModel):
    severity: Literal["info","warn","critical"]
    description: str
    photos: List[str]              # photo_ref ids
    auto_shop_ticket_id: Optional[str]   # set by Shop consumer projector
```

### 3.5 `SubcontractorBlock` (Section 5)

```python
class SubRow(BaseModel):
    sub_id: Optional[str]          # FK if master record exists
    name: str
    present: bool
    work_performed: str            # free-text (voice-supported)
    deliveries: List[DeliveryNote]
    issues: List[IssueNote]
```

### 3.6 `ProductionBlock` (Section 6 · polymorphic)

```python
class ProductionBlock(BaseModel):
    # Polymorphic — exactly one of the following sub-objects is populated
    # based on crew_profile.crew_type. Closed-set ensures PDF + analytics
    # can rely on shape.
    pipe: Optional[PipeProduction]
    grading: Optional[GradingProduction]
    paving: Optional[PavingProduction]
    mot: Optional[MotProduction]
    concrete: Optional[ConcreteProduction]
    structures: Optional[StructuresProduction]
    milling: Optional[MillingProduction]
    survey: Optional[SurveyProduction]
    electrical: Optional[ElectricalProduction]
    other: Optional[GenericProduction]
    # … one sub-model per crew_type · each closed-set + dropdown-first.
```

**Example: PipeProduction**

```python
class PipeRun(BaseModel):
    pipe_size_in: float
    pipe_material: Literal["RCP","HDPE","PVC","DI","CMP","other"]
    lf_installed: float
    from_structure: Optional[str]
    to_structure: Optional[str]
    backfill_type: Optional[str]
    compaction_pct: Optional[float]
    testing: List[TestRecord]

class PipeProduction(BaseModel):
    runs: List[PipeRun]
    structures_set: List[StructureSet]
    total_lf: float                # derived
    total_structures: int          # derived
```

### 3.7 `DelayBlock` (Section 7)

```python
DELAY_TYPE = Literal[
    "weather","utility","survey","cei","owner","faa","mot",
    "material","equipment","staffing","other",
]

class DelayEntry(BaseModel):
    delay_type: DELAY_TYPE
    hours_lost: float
    description: str               # voice-supported
    photos: List[str]
    constraint_link_id: Optional[str]  # if it traces to operational_constraints

class DelayBlock(BaseModel):
    any_delays: bool               # mandatory
    entries: List[DelayEntry]
    total_hours_lost: float        # derived
```

### 3.8 `ExtraWorkBlock` (Section 8)

```python
class ExtraWorkEntry(BaseModel):
    requested_by: str              # name + role (free-text · dropdown-first if known)
    requested_by_org: Optional[Literal["owner","cei","designer","faa","fdot","other"]]
    description: str
    potential_cost_impact_usd: Optional[float]
    potential_schedule_impact_days: Optional[float]
    photos: List[str]
    rfi_link_id: Optional[str]     # if it traces to a future RFI

class ExtraWorkBlock(BaseModel):
    any_extra_work: bool
    entries: List[ExtraWorkEntry]
```

### 3.9 `ConstraintBlock` (Section 9 · TIE-IN to V-Prelude Wave 1)

```python
class ConstraintEntry(BaseModel):
    constraint_type: Literal[
        "utility","survey","design","access","staffing","material","equipment","other",
    ]
    description: str
    auto_operational_constraint_id: Optional[str]
                                    # ← populated by Memory projector ·
                                    # FK → operational_constraints (Wave 1)

class ConstraintBlock(BaseModel):
    entries: List[ConstraintEntry]
```

### 3.10 `SafetyBlock` (Section 10 · HARD-STOP)

```python
class SafetyBlock(BaseModel):
    accident: bool
    incident: bool
    near_miss: bool
    property_damage: bool
    environmental_release: bool
    injury: bool
    any_event: bool                # derived OR of the above

    # Required only when any_event=True:
    safety_notified: Optional[bool]
    contact_name: Optional[str]
    contact_time_utc: Optional[str]
    incident_report_complete: Optional[bool]
    incident_report_link_id: Optional[str]      # FK → safety incident
                                                #   (one row, no duplicate entry)

    # Readiness engine refuses submission when any_event=True AND
    # (safety_notified is not True OR incident_report_complete is not True).
```

### 3.11 `WeatherImpactBlock` (Section 11)

```python
class WeatherImpactBlock(BaseModel):
    weather_impacted_work: bool
    hours_lost: Optional[float]
    description: Optional[str]     # voice-supported
```

### 3.12 `PhotoRef` (Section 12)

```python
PHOTO_TAG = Literal[
    "production","delay","extra_work","safety","qc","equipment","mot","weather","general",
]

class PhotoRef(BaseModel):
    photo_id: str                  # FK → odr_photos
    tag: PHOTO_TAG
    voice_caption: Optional[str]   # rendered audio → text on upload
    text_caption: Optional[str]
    captured_at_utc: str
    captured_at_local: str
    gps: Optional[GeoFix]
    section_anchor: Optional[str]  # e.g. "delays.entry[2]" for in-section thumbnail
    photo_governance_id: Optional[str]   # FK → photo_governance (Wave 1)
```

### 3.13 `TomorrowPlanBlock` (Section 13)

```python
class TomorrowPlanBlock(BaseModel):
    planned_work: str              # voice-supported
    required_resources: List[str]
    concerns: List[str]
```

### 3.14 `PlanVsActualBlock` (Section 14)

```python
class PlanVsActualBlock(BaseModel):
    completed_planned_work: bool
    variance_reason: Optional[str] # required when completed_planned_work=False
    schedule_impact_days: Optional[float]
```

### 3.15 `ReadinessSnapshot` (Section 15)

```python
class ReadinessSnapshot(BaseModel):
    evaluated_at_utc: str
    missing_required: List[str]    # field paths
    coaching_prompts: List[str]    # non-blocking, friendly suggestions
    hard_stops: List[str]          # mandatory · submission refused if non-empty
    score: Literal["draft","ready","needs_attention","blocked"]
```

### 3.16 `ReviewBlock` (Section 16 · Phase 2 surface · field present at launch)

```python
class ReviewEvent(BaseModel):
    actor_uid: str
    actor_role: Literal["pm","superintendent","admin"]
    action: Literal["submit","return","approve"]
    note: Optional[str]
    at_utc: str

class ReviewBlock(BaseModel):
    pm_reviewer_uid: Optional[str]
    status_history: List[ReviewEvent]
```

---

## 4 · Closed-set enumerations (single source of truth)

Stored as Python `Literal[...]` types + mirrored in `frontend/src/lib/odrEnums.js` for client-side validation. The two sources are regenerated from one YAML file (`/app/backend/data/odr_enums.yaml` · to be added in implementation phase).

| Enum | Where used | # of values |
|---|---|---|
| `CrewType` | § 2 | 16 |
| `DelayType` | § 7 | 11 |
| `ConstraintType` | § 9 | 8 |
| `PhotoTag` | § 12 | 9 |
| `PipeMaterial` | § 6 pipe | 6 |
| `ExtraWorkOrg` | § 8 | 6 |
| `ReviewStatus` | § 16 | 4 |
| `ReadinessScore` | § 15 | 4 |

---

## 5 · Audit / governance contract

- **Timestamps**: every field bearing a date is Z-suffixed UTC ISO
  (`TIMESTAMP_UTILITY_STANDARD.md` doctrine — already gated by
  `timestamp_doctrine_probe.py`).
- **Append-only sections**: `odr_section_events` records every
  field-level transition (when, by whom, from what to what).
  `OBSERVATION_LEDGER`-style integrity; never mutated, only appended.
- **Single-source for cross-portal data**: PM / Safety / Shop / HR /
  Exec read the ODR through projectors (see Artifact 3). Direct
  writes from those portals back to ODR fields are **forbidden**.
- **Schema-violation lineage**: the readiness engine writes its output
  into `schema_violations` so downstream consumers can refuse to
  surface broken records without re-evaluating.
- **Photo governance**: photo refs carry the `photo_governance_id` so
  the V-Prelude Wave 1 photo governance contract (`PHOTO_GOVERNANCE_STANDARD.md`)
  continues to apply.

---

## 6 · API surface (planned · not yet implemented)

| Verb | Path | Auth | Purpose |
|---|---|---|---|
| `POST` | `/api/odr` | FL · Super · Admin | create draft |
| `PATCH` | `/api/odr/{id}` | author + Super · Admin | partial update (field-level) |
| `POST` | `/api/odr/{id}/submit` | author + Super · Admin | run readiness engine + transition to `submitted` |
| `GET` | `/api/odr/{id}` | per-portal projector | full read |
| `GET` | `/api/odr` | per-portal projector | list with filter |
| `POST` | `/api/odr/{id}/photo` | author + Super · Admin | upload + tag |
| `POST` | `/api/odr/{id}/section-event` | system | append telemetry row |
| `POST` | `/api/odr/{id}/review` | PM · Admin | review action (Phase 2) |
| `GET` | `/api/odr/{id}/pdf` | per-portal projector | render PDF |
| `GET` | `/api/odr/dispatch/{consumer}/{id}` | consumer service | projector cached view |

All routes will live in `backend/routes/odr/` (new package; not `daily_reports.py`).

---

## 7 · Backwards compatibility

- `daily_reports` legacy collection **frozen** at migration cutover —
  no further writes. Reads remain available for 12 months as the
  archival surface.
- `legacy_daily_report_id` foreign key on ODR points back to the
  migrated row so audit trails remain end-to-end traceable.
- See `ODR_MIGRATION_PLAN.md` for the field-by-field mapping.

---

## 8 · Open architecture questions for operator review

1. Should `weather` provider be NOAA-only, or fall back to OpenWeather
   if NOAA latency exceeds a threshold? (Default proposed: NOAA primary,
   OpenWeather fallback, both stamped into `weather` block.)
2. Should `time_created_local` honor the project's site-TZ (FDOT
   projects = `America/New_York`) or the foreman's device TZ? (Default
   proposed: site-TZ, derived from `jobs_master.timezone`.)
3. Should `day_number` reset on long-paused projects, or stay
   monotonic-by-calendar-day? (Default proposed: monotonic.)
4. Should `PhotoRef.voice_caption` be transcribed server-side
   (Whisper) and the audio kept for evidentiary value? (Default
   proposed: yes — keep audio + transcript both.)
5. Should `Section 16 · PM Review` ship a field-only surface at
   launch (status field present, no UI) and turn on the review queue
   in V.1.1? (Default proposed: yes.)

Awaiting operator decisions before implementation.

---

_Artifact 1 of 5 · proceed to ODR_UI_WIREFRAMES.md_

---

# Delta Integration Addendum (D1–D8) · 2026-05-29

This addendum revises the data model to incorporate the eight
operator-approved deltas and the ten newly-locked doctrine
statements (O1–O10). Original content above remains the foundational
spec; the structures defined here **supersede** the matching
sections where they differ.

## A1 · Revised top-level envelope

```python
class ODR(BaseModel):
    # ── Identity ──
    id: str
    doc_id: str                          # ODR-YYYY-NNNNN
    schema_version: int                  # bumped to 2 with D1–D8
    legacy_daily_report_id: Optional[str]

    # ── Section 1 · Project Snapshot ──
    project: ProjectSnapshot

    # ── Section 2 · Crew Profile ──
    crew_profile: CrewProfile

    # ── Section 2.5 · Work Areas (NEW · D2) ──
    work_areas: List[WorkArea]           # 0..N

    # ── Section 3 · Manpower ──
    manpower: ManpowerBlock

    # ── Section 4 · Equipment ──
    equipment: EquipmentBlock

    # ── Section 5 · Subcontractors / Vendors ──
    subcontractors: SubcontractorBlock

    # ── Section 5.5 · Materials (NEW · D3) ──
    materials: List[MaterialEvent]       # 0..N

    # ── Section 6 · Production (REVISED · D1 — now a list of segments) ──
    production_segments: List[ProductionSegment]   # 1..N (singular `production`
                                                   # field deprecated; auto-
                                                   # migrated in M1)

    # ── Section 7 · Delays ──
    delays: DelayBlock

    # ── Section 8 · Extra Work ──
    extra_work: ExtraWorkBlock

    # ── Section 9 · Constraints ──
    constraints: ConstraintBlock

    # ── Section 10 · Safety Compliance (REVISED · D7) ──
    safety: SafetyBlock                  # now carries events: List[SafetyEvent]

    # ── Section 11 · Weather Impact ──
    weather_impact: WeatherImpactBlock

    # ── Section 12 · Photos ──
    photos: List[PhotoRef]

    # ── Section 13 · Tomorrow Plan ──
    tomorrow: TomorrowPlanBlock

    # ── Section 14 · Plan vs Actual ──
    plan_vs_actual: PlanVsActualBlock

    # ── Section 15 · Readiness Check ──
    readiness: ReadinessSnapshot

    # ── Section 16 · PM Review ──
    review: ReviewBlock

    # ── Reliability envelope (NEW · D4) ──
    reliability: ReliabilityBlock

    # ── Completion telemetry (NEW · D5) ──
    completion_telemetry: CompletionTelemetry

    # ── Audit envelope ──
    status: Literal["draft","submitted","returned","approved"]
    created_at: str
    submitted_at: Optional[str]
    last_edited_at: str
    last_edited_by_uid: str
    submitted_by_uid: Optional[str]
    location_at_submit: Optional[GeoFix]
    location_accuracy_m: Optional[float]
    device_session_id: Optional[str]
    schema_violations: List[str]
    consumer_dispatch: Dict[str, str]
```

## A2 · D1 · `ProductionSegment` (multiple operations per ODR)

```python
class ProductionSegment(BaseModel):
    segment_id: str                      # uuid4
    crew_type: CrewType                  # same enum as CrewProfile.crew_type
    primary_operation: str               # closed-set per crew_type
    work_area_id: Optional[str]          # FK → ODR.work_areas[*].work_area_id
    started_at_utc: Optional[str]
    ended_at_utc: Optional[str]
    body: ProductionBlock                # the polymorphic sub-block · one shape
```

Cap: **6 segments / ODR** (proposed default · operator may override).
The polymorphic `ProductionBlock` (PipeProduction · PavingProduction ·
GradingProduction · MotProduction · ConcreteProduction · …) remains
unchanged; it now lives inside a segment.

## A3 · D2 · `WorkArea` + `work_area_id` FK pattern

```python
class WorkArea(BaseModel):
    work_area_id: str                    # uuid4
    label: LocalizedString               # e.g. "MP 12.4 SB" / "Taxiway B"
    station_from: Optional[str]
    station_to: Optional[str]
    gps_centroid: Optional[GeoFix]
    timezone: Optional[str]              # override site-TZ if rare TZ-spanning
    notes: LocalizedString
```

`work_area_id: Optional[str]` is added to every event-bearing entry:

- `DelayEntry.work_area_id`
- `ExtraWorkEntry.work_area_id`
- `ConstraintEntry.work_area_id`
- `EquipmentRow.work_area_id`
- `MaterialEvent.work_area_id`
- `PhotoRef.work_area_id` (additive to existing `section_anchor`)
- `ProductionSegment.work_area_id`

Cap: **8 work_areas / ODR** (proposed default).

## A4 · D3 · `MaterialEvent` (top-level)

```python
class MaterialEvent(BaseModel):
    material_event_id: str                  # uuid4
    work_area_id: Optional[str]
    kind: Literal["delivered","consumed","staged","returned",
                  "wasted","rejected","short"]
    material_code: Optional[str]            # FK → materials master
    description: LocalizedString
    quantity: float
    uom: Literal["ton","cy","lf","sf","ea","gal","other"]
    vendor: Optional[str]
    ticket_numbers: List[str]
    photos: List[str]                       # photo_ref ids
    issue: Optional[Literal["shortage","reject","damage","wrong_material"]]
```

## A5 · D4 · Reliability envelope

```python
class ReliabilityBlock(BaseModel):
    # Autosave
    autosave_enabled: bool                   # default True
    autosave_interval_s: int                 # contract: ≤ 5
    last_autosave_at_utc: Optional[str]
    autosave_count: int

    # Draft recovery
    last_known_good_section: Optional[str]
    recovery_token: Optional[str]

    # Offline
    offline_origin: bool                     # was first save offline?
    offline_session_id: Optional[str]
    offline_photo_queue_size: int            # at submit time
    offline_photo_queue_drained_at_utc: Optional[str]

    # Sync
    sync_state: Literal["clean","pending","conflict","error"]
    last_sync_at_utc: Optional[str]
    sync_conflicts: List[SyncConflict]

    # Device
    device_fingerprint: DeviceFingerprint


class DeviceFingerprint(BaseModel):
    ua: str
    os: str
    os_version: str
    app_version: str                         # bundle build id
    is_pwa: bool
    is_secure_context: bool


class SyncConflict(BaseModel):
    section: str                             # field path
    detected_at_utc: str
    server_value_hash: str
    client_value_hash: str
    resolution: Literal["server_wins","client_wins","merged","unresolved"]
    resolved_at_utc: Optional[str]
```

## A6 · D5 · `CompletionTelemetry` envelope

```python
class CompletionTelemetry(BaseModel):
    seconds_to_submit: Optional[float]       # submitted_at - created_at
    section_visit_times: Dict[str, float]    # per-section dwell time
    auto_fill_accept_rate: Dict[str, float]  # per-section %
    voice_caption_count: int
    voice_caption_chars: int
    autosave_count: int
    language_at_entry: Literal["en","es","mixed"]
```

Admin-visible only. Per O9: not surfaced to the foreman.

## A7 · D6 · `LocalizedString` envelope (bilingual native · MANDATORY)

```python
class LocalizedString(BaseModel):
    text: str                                # canonical English at storage
    original: Optional[str]                  # original-language as entered
    original_lang: Optional[Literal["en","es"]]
    translated_by: Optional[Literal["model","operator","none"]]
    translated_at_utc: Optional[str]
    translation_model: Optional[str]         # e.g. "claude-haiku-4.5"
    translation_confidence: Optional[float]  # 0..1
```

Applied to the 10 free-text fields (see DELTA_INTEGRATION_SUMMARY § 4):

| # | Field path |
|---|---|
| 1 | `DelayEntry.description` |
| 2 | `ExtraWorkEntry.description` |
| 3 | `ConstraintEntry.description` |
| 4 | `SubRow.work_performed` |
| 5 | `PhotoRef.text_caption` |
| 6 | `PhotoRef.voice_caption` |
| 7 | `TomorrowPlanBlock.planned_work` |
| 8 | `WeatherImpactBlock.description` |
| 9 | `PlanVsActualBlock.variance_reason` |
| 10 | `MaterialEvent.description` + `WorkArea.label` + `WorkArea.notes` |

A new collection `odr_translation_events` is introduced:

```python
class TranslationEvent(BaseModel):
    odr_id: str
    field_path: str
    original_lang: Literal["en","es"]
    original_text_hash: str                  # SHA-256
    canonical_text_hash: str
    model: Optional[str]
    actor_uid: Optional[str]
    at_utc: str
```

Append-only · protected by extended `trendline_integrity_probe.py`.

## A8 · D7 · `SafetyBlock` per-event refactor

```python
SAFETY_EVENT_KIND = Literal[
    "accident","incident","near_miss",
    "property_damage","environmental_release","injury",
]

class SafetyEvent(BaseModel):
    event_id: str                            # uuid4
    event_kind: SAFETY_EVENT_KIND
    notified_safety: bool
    contact_name: Optional[str]
    contact_time_utc: Optional[str]
    incident_report_complete: bool
    incident_report_link_id: Optional[str]
    work_area_id: Optional[str]              # ties event to a WorkArea
    photos: List[str]


class SafetyBlock(BaseModel):
    # Six booleans retained for fast filtering / dashboards:
    accident: bool
    incident: bool
    near_miss: bool
    property_damage: bool
    environmental_release: bool
    injury: bool
    any_event: bool                          # derived OR
    # Per-event accountability lineage:
    events: List[SafetyEvent]                # 1..N when any_event=True
```

Hard-stop contract (unchanged): readiness engine refuses submission
when **any** event in `events` has `notified_safety=False` OR
`incident_report_complete=False`.

## A9 · Updated index strategy

Indexes added to support the new shape:

- `odr`: `{ "work_areas.work_area_id": 1, report_date: -1 }`
- `odr`: `{ "production_segments.crew_type": 1, report_date: -1 }`
- `odr`: `{ "materials.kind": 1, report_date: -1 }`
- `odr`: `{ "safety.any_event": 1, report_date: -1 }`
- `odr_translation_events`: `{ odr_id: 1, at_utc: 1 }`

## A10 · D6 collection inventory (post-revision)

| Collection | Purpose | Append-only? |
|---|---|---|
| `odr` | system of record | no — drafts mutable |
| `odr_photos` | photo registry | no — caption mutable |
| `odr_section_events` | field-level transitions | yes (probe-protected) |
| `odr_translation_events` | bilingual audit trail (D6) | yes (probe-protected) |
| `odr_consumer_index` | derived projector views | refreshed |

## A11 · Doctrine anchors (O1–O10 → spec)

| Doctrine | Anchor in this artifact |
|---|---|
| O1 | A1 envelope shape + A6 telemetry |
| O2 | A2 + A3 + A4 + A8 + existing lists |
| O3 | A6 measurable budget |
| O4 | A7 LocalizedString voice support + closed-set enums § 4 |
| O5 | ECOSYSTEM projector contracts (see that artifact) |
| O6 | ECOSYSTEM § 1–2 (see that artifact) |
| O7 | A7 LocalizedString + odr_translation_events |
| O8 | A5 ReliabilityBlock |
| O9 | A8 SafetyBlock hard-stop + ReadinessSnapshot |
| O10 | PDF_LAYOUT artifact |

_End of Delta Integration Addendum (D1–D8) · DATA_MODEL._

---

# Public-Link Device Continuity Addendum · 2026-05-29

This addendum revises the ODR envelope to absorb the
Public-Link Device Continuity Doctrine (O11–O20). Read alongside
`ODR_PUBLIC_LINK_DEVICE_CONTINUITY_ADDENDUM.md`. Sections here
**supersede** the matching parts of the earlier spec.

## P1 · Revised ODR envelope (additions only)

```python
class ODR(BaseModel):
    ...  # (everything from earlier addenda)

    # ── Public-link access envelope (NEW · O11–O20) ──
    public_access: PublicAccessBlock
```

## P2 · `PublicAccessBlock`

```python
class PublicAccessBlock(BaseModel):
    link_id: str                              # opaque · per-project + per-crew
    link_scope: Literal["project", "project_crew"]
    link_created_at_utc: str
    link_created_by_uid: str                  # PM / Admin
    link_revoked_at_utc: Optional[str]

    device_tokens: List[DeviceToken]          # 0..N trusted devices

    continuity: DeviceContinuityBlock         # last-evaluated continuity result
                                              # for the device that authored / submitted
                                              # this ODR
```

## P3 · `DeviceToken`

```python
class DeviceToken(BaseModel):
    token_id: str                             # uuid4 (server-issued)
    token_hash: str                           # SHA-256 of the opaque token
    issued_at_utc: str
    last_seen_at_utc: str
    expires_at_utc: str                       # default issued + 90d
    issued_to_fingerprint: DeviceFingerprint  # bound at issue time
    issued_via: Literal["foreman_first_use","admin_override","pm_override"]
    issuer_uid: Optional[str]                 # set when issued_via != foreman_first_use
    note: Optional[str]
    revoked_at_utc: Optional[str]
```

## P4 · `DeviceContinuityBlock`

```python
class DeviceContinuityBlock(BaseModel):
    # The seven signals at the moment of evaluation:
    signals: ContinuitySignals

    # Aggregate result:
    outcome: Literal[
        "allowed",
        "denied_device_mismatch",
        "denied_missing_token",
        "denied_expired_context",
        "denied_wrong_project",
        "denied_wrong_link",
        "denied_date_out_of_window",
        "denied_gps_conflict",
        "denied_no_prior",
    ]
    evaluated_at_utc: str
    prior_odr_id: Optional[str]               # the prior ODR considered, if any

class ContinuitySignals(BaseModel):
    fingerprint_match: bool                   # signal 1
    token_match: bool                         # signal 2
    project_match: bool                       # signal 3
    link_match: bool                          # signal 4
    date_in_window: bool                      # signal 5
    gps_proximity_ok: Optional[bool]          # signal 6 · None if unmeasurable
    prior_identity_match: Optional[bool]      # signal 7 · None if no prior identity
    explicit_conflict: bool                   # any signal explicitly conflicted
```

## P5 · `PreloadAttempt` (per-attempt audit row)

```python
class PreloadAttempt(BaseModel):
    attempt_id: str                            # uuid4
    requested_at_utc: str
    public_link_id: str
    project_id: str
    target_report_date: str                    # YYYY-MM-DD
    prior_odr_id: Optional[str]

    outcome: Literal[
        "allowed",
        "denied_device_mismatch",
        "denied_missing_token",
        "denied_expired_context",
        "denied_wrong_project",
        "denied_wrong_link",
        "denied_date_out_of_window",
        "denied_gps_conflict",
        "denied_no_prior",
        "override_used",
    ]
    signals_matched: List[str]
    signals_failed: List[str]

    override_actor_uid: Optional[str]          # set when outcome="override_used"
    override_portal: Optional[Literal["pm","admin"]]
    notes: Optional[str]

    device_fingerprint_at_request: DeviceFingerprint
    gps_at_request: Optional[GeoFix]
```

## P6 · New collection · `odr_preload_attempts`

| Property | Value |
|---|---|
| Append-only? | **yes** (probe-protected · `trendline_integrity_probe.py` extended) |
| Indexes | `{ project_id: 1, requested_at_utc: -1 }` · `{ public_link_id: 1, requested_at_utc: -1 }` · `{ outcome: 1, requested_at_utc: -1 }` |
| Read access | admin-strict + PM-token for own-project · NEVER public |
| Write access | only the public-link continuity engine and admin override route |
| Retention | append-only · never purged · doctrine-anchored |

## P7 · Two additional ODR convenience flags

```python
class ODR(BaseModel):
    ...
    prior_report_preload_allowed: bool        # convenience flag · True if
                                              # this ODR was created via an
                                              # allowed preload
    preload_denial_reason: Optional[str]      # set when a preload was denied
                                              # but the foreman chose "start blank"
                                              # · same enum as PreloadAttempt.outcome
```

These two flags make it cheap for the projector layer to know
whether this ODR carries inherited seed data or is a true blank.

## P8 · Updated index list

Adds to the index list from the earlier D1–D8 addendum (§ A9):

- `odr`: `{ "public_access.link_id": 1, "project.report_date": -1 }`
- `odr_preload_attempts`: `{ project_id: 1, requested_at_utc: -1 }`
- `odr_preload_attempts`: `{ outcome: 1, requested_at_utc: -1 }`

## P9 · Doctrine anchors (O11–O20 → DATA_MODEL)

| Doctrine | Anchor |
|---|---|
| O11 public scope | `PublicAccessBlock` · `link_scope` |
| O12–O14 continuity-gated preload | `DeviceContinuityBlock` + `prior_report_preload_allowed` |
| O15 no leak | only `allowed`-outcome preloads return prior data (enforced at route layer) |
| O17 override authenticated only | `DeviceToken.issued_via in {admin_override, pm_override}` requires `issuer_uid` |
| O18 append-only log | `odr_preload_attempts` collection |

_End of Public-Link Device Continuity Addendum · DATA_MODEL._
