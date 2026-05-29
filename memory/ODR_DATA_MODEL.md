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
