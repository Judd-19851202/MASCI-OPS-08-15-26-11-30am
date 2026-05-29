# Daily Report · Constraint Tracking Design

_Phase V.1 · 2026-05-29 · structured delay/constraint taxonomy._

> Replaces the existing `daily_reports.schedule_delays: "Yes"/"No"`
> string with a structured, typed taxonomy that lives behind a
> single-chip selector on the foreman's screen.

---

## 1 · Data shape · `daily_reports.constraints` (new substructure)

Additive — coexists with the legacy `schedule_delays` string for
backward compat on historical rows (which are frozen anyway).

```python
class ConstraintRow(BaseModel):
    row_id: str                              # uuid · stable
    constraint_type: Literal[
        "weather",
        "utility",
        "survey_control",
        "material",
        "equipment",
        "trucking",
        "mot",                # maintenance of traffic
        "cei_inspection",     # consultant / construction engineering inspection
        "owner_engineer",
        "safety",
        "other",
    ]
    hours_lost: Optional[float] = None       # 0–24 · optional · PM backfills
    description: Optional[str] = None        # voice or text · ≤ 280 chars · optional
    affected_crew_id: Optional[str] = None   # auto from step 2 if single crew
    affected_production_row_id: Optional[str] = None  # auto from step 4 nearest row
    may_require_rfi: bool = False            # advisory flag · default false
    may_affect_schedule: bool = False        # advisory flag · default false
    resolved: bool = False                   # PM/Super edits later
    notes_at_resolution: Optional[str] = None  # PM-side · invisible to foreman
```

## 2 · UI surface · step 6 of the 9-step flow

### 2.1 Empty state (most common path)

```
┌─────────────────────────────────────────────┐
│ Issues / Delays                             │
│                                             │
│ Anything slow the crew down today?          │
│                                             │
│ [ Weather ]  [ Utility ]  [ MOT ]           │
│ [ Material ] [ Equipment ] [ Trucking ]     │
│ [ Survey ]   [ CEI ]      [ Owner ]         │
│ [ Safety ]   [ Other ]                      │
│                                             │
│ No issues today? Skip.                      │
└─────────────────────────────────────────────┘
```

One tap to skip the entire section. One tap to add a constraint.

### 2.2 Add flow (one constraint)

| Field | Input | Default |
|---|---|---|
| Constraint type | The chip the foreman just tapped | Auto-set from chip |
| Hours lost | Numeric keypad with 0.25-h step | Empty (optional) |
| Description | Voice-or-text | Empty (optional) |
| RFI flag | Checkbox "May need an RFI" | Off |
| Schedule flag | Checkbox "May affect schedule" | Off |
| Affected production row | Auto-link to nearest step-4 row | Auto |
| Affected crew | Auto from step 2 if single crew | Auto |

**Time-to-complete one constraint: ~10–15 seconds.**

### 2.3 Coaching · OGC engine reuse

Constraint type drives the OGC coaching surface (bilingual):

| Constraint type | EN coaching | ES coaching |
|---|---|---|
| `weather` | "Note ground condition before next shift." | "Anote la condición del suelo antes del próximo turno." |
| `utility` | "Log conflict location for utility tag-out." | "Registre la ubicación del conflicto para el aislamiento de servicios." |
| `mot` | "Note signage changes affecting traffic flow." | "Anote cambios en la señalización que afecten el tráfico." |
| `material` | "Record vendor + ETA so dispatch can adjust." | "Registre el proveedor + ETA para que despacho ajuste." |
| `cei_inspection` | "Note inspector name + hold-point status." | "Anote el nombre del inspector + estado del punto de retención." |
| _(others follow the same pattern)_ | | |

These are coaching prompts, not required fields. The OGC engine
already supports 14 prompt keys (M0.2A); constraints add ~6 new
prompt keys (planning-only · NOT IMPLEMENTED).

## 3 · RFI-ready flag · what it does and does NOT do

| Behavior | RFI flag |
|---|---|
| Records `may_require_rfi: true` on the row | ✅ YES |
| Surfaces in the PM panel "exposures" tile | ✅ YES (future) |
| Creates an RFI record | ❌ NO (forbidden until M2 authorization) |
| Notifies the owner/engineer | ❌ NO |
| Affects the schedule | ❌ NO |
| Affects the PDF audience projection | ❌ NO (it is operator metadata, not external) |

The flag is **pure signal**. It tells the PM "the foreman thinks this
might need an RFI" — nothing more.

## 4 · Schedule-impact flag · what it does and does NOT do

| Behavior | Schedule flag |
|---|---|
| Records `may_affect_schedule: true` on the row | ✅ YES |
| Surfaces in the PM panel "schedule risk" tile | ✅ YES (future) |
| Modifies any schedule | ❌ NO (forbidden until schedule integration authorization) |
| Posts to P6 | ❌ NO |
| Notifies anyone | ❌ NO |
| Affects PDF audience projection | ❌ NO |

Pure signal again. The PM decides what to do with it.

## 5 · Substrate reuse map (cross-link to `ODR_SUBSTRATE_REUSE_MAP.md`)

| Source asset | Reused for |
|---|---|
| ODR `delays.entries[]` shape (closed `delay_type` enum) | Backend `daily_reports.constraints[]` |
| ODR `operational_links` `chronology_anchor` + `addresses` | Constraint ↔ production row linkage |
| OGC guidance catalog | Constraint-type-specific coaching prompts |
| Photo governance | Photo → constraint_row_id linkage |
| Audience projection (external) | External PDFs strip foreman uid / device, render constraint type + hours + description |
| Audit footer (SHA256) | DR PDF rendering gains the audit footer |

## 6 · External PDF redaction

| Field | External PDF |
|---|---|
| Constraint type | ✅ Visible |
| Hours lost | ✅ Visible |
| Description | ✅ Visible (regex-redacted per M0.4) |
| `may_require_rfi` | ❌ Stripped (internal operator metadata) |
| `may_affect_schedule` | ❌ Stripped (internal operator metadata) |
| `resolved` | ❌ Stripped (PM telemetry) |
| `notes_at_resolution` | ❌ Stripped (PM-only) |
| Affected production_row_id | ❌ Stripped (uuid · internal) |
| Affected crew uid | ❌ Stripped |

## 7 · Validation gates

| Gate | Rule |
|---|---|
| `constraint_type` required when row added | yes |
| `hours_lost` ≥ 0 if provided | yes |
| `hours_lost` ≤ 24 | yes |
| `description` ≤ 280 chars | yes |
| At least one constraint when `schedule_delays == "Yes"` (legacy compat) | warn · never blocks |
| Self-link to production row valid | optional |

## 8 · Migration impact (none)

Historical daily_reports rows have no `constraints[]` field. New rows
get `constraints: []` by default. Historical rows are not mutated.

## 9 · Wave 1 build scope · this design's footprint

| Layer | Lines · new | Lines · modified |
|---|---|---|
| Backend model | ~45 | ~5 |
| Backend submit validator | ~20 | ~5 |
| Backend PDF renderer (constraints section) | ~50 | ~10 |
| Frontend step 6 component | ~160 | ~20 (replaces the Y/N control) |
| Frontend OGC coaching hook | ~20 | ~5 |
| Backend tests | ~100 | ~0 |
| **Estimate** | **~395 lines new** | **~45 modified** |

Estimated dev-day: **1–1.5 days** for constraint tracking alone.

## 10 · Combined wave-1 estimate (production + constraint)

| | Production | Constraints | Combined |
|---|---|---|---|
| New lines | ~455 | ~395 | ~850 |
| Modified lines | ~35 | ~45 | ~80 |
| Dev-days | 1.5–2 | 1–1.5 | **3–4 dev-days** (parallelizable to ~2.5) |

---

_End of DAILY_REPORT_CONSTRAINT_TRACKING_DESIGN.md._
