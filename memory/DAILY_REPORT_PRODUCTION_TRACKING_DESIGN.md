# Daily Report · Production Tracking Design

_Phase V.1 · 2026-05-29 · structured production quantities + activity inference._

> Adds typed production tracking to the existing Daily Report
> WITHOUT making the foreman experience harder. Activity tracking
> is derived from production rows + crew + equipment; foremen never
> author activities separately.

---

## 1 · Data shape · `daily_reports.production` (new substructure)

Additive — does not modify existing fields. Lives under
`daily_reports.production` (new) alongside the existing `activities`,
`materials`, `masci_crews` fields.

```python
class ProductionRow(BaseModel):
    row_id: str                          # uuid · stable
    unit: Literal[
        "LF_pipe",           # linear feet of pipe (utility)
        "CY_concrete",       # cubic yards of concrete (structures / curb / sw)
        "tons_asphalt",      # tons of asphalt (paving / milling)
        "SY_grading",        # square yards of grading
        "SY_milling",        # square yards of milling
        "LF_curb",           # linear feet of curb & gutter
        "custom",            # operator-supplied unit (notes field carries label)
    ]
    quantity: float                      # required; > 0
    station_from: Optional[str] = None   # e.g., "12+50" — free text, no parser
    station_to: Optional[str] = None     # e.g., "13+00"
    work_area_id: Optional[str] = None   # FK to operational_links work_area (future)
    activity_status: Literal[            # inferred from form context, foreman can override
        "started",
        "continued",
        "completed",
    ] = "continued"
    affected_crew_id: Optional[str] = None   # derived from masci_crews[].id if exactly one
    affected_equipment_ids: List[str] = []   # derived from equipment[] picks
    custom_unit_label: Optional[str] = None  # only set when unit == "custom"
    notes: Optional[str] = None              # voice or text · ≤ 240 chars
    coaching_acknowledged: bool = False      # OGC engine: did foreman see the unit-specific prompt?
```

The closed enum protects ODR-style taxonomy without forcing the foreman
to learn one. The substrate values themselves are simple words a
foreman already says aloud on site ("we did 600 LF of pipe").

## 2 · UI surface · step 4 of the 9-step flow

### 2.1 Empty state (most common path)

```
┌─────────────────────────────────────────────┐
│ Production                                  │
│                                             │
│ [+ Add production]                          │
│                                             │
│ Skip if no production today.                │
└─────────────────────────────────────────────┘
```

One tap to skip the entire section. The default "no rows" state is
operationally valid (e.g., rain day, demo-only crew).

### 2.2 Add flow (one row)

| Field | Input | Default |
|---|---|---|
| Unit | Chip selector (6 units + "custom") | Last-used unit pre-selected |
| Quantity | Numeric keypad | Empty (focus on open) |
| Station range | Free text · "12+50 → 13+00" | Empty (optional) |
| Activity status | Chip: started / continued / completed | "continued" |
| Affected crew | Auto from step 2 if exactly one crew | Auto |
| Affected equipment | Auto from step 3 if exactly one set | Auto |
| Notes | Voice-or-text | Empty |

**Time-to-complete one row: ~15–20 seconds.** Typical DR has 1–3
production rows.

### 2.3 Coaching · OGC engine reuse

When the foreman picks `unit = LF_pipe`, the OGC engine
(`guidance_catalog.py`, M0.2A) surfaces the bilingual coaching
tied to the `utility` / `pipe` crew type:

> EN: "Confirm bedding compaction probe before backfill."
> ES: "Confirme la prueba de compactación de cama antes del relleno."

Same engine. Same 14 prompt keys. Different surface — now under the
Daily Report form instead of the ODR form.

## 3 · Activity tracking · INFERRED, not authored

Per the Field Simplicity Certification, foremen do NOT author
activities separately. Activities are derived deterministically:

| Inferred field | Derivation |
|---|---|
| `work_activity` | Implied by `unit` (e.g., `LF_pipe` → "Pipe install") |
| `station/location` | `station_from` / `station_to` |
| `status` | `activity_status` enum on the row |
| `affected crew` | `affected_crew_id` (auto from step 2) |
| `affected equipment` | `affected_equipment_ids` (auto from step 3) |

The activity record is generated at submit time by the substrate
layer — never authored manually. This:

- Holds the 9-step contract (no separate activity step)
- Eliminates ~32 of the ~150-decision manual-classification queue
  identified in the M1 pre-authorization review
- Produces ODR-style structured activities behind the scenes
  without the foreman experiencing any of the ODR shape

## 4 · Substrate reuse map (cross-link to `ODR_SUBSTRATE_REUSE_MAP.md`)

| Source asset | Reused for |
|---|---|
| ODR `production_segments[]` | Backend shape for the new `daily_reports.production[]` |
| ODR `crew_type` closed enum | Activity status enum + unit→crew_type inference |
| OGC guidance catalog | Unit-specific coaching prompts |
| Photo governance | Photo → production_row_id linkage |
| `operational_links` | Production row ↔ photo / constraint / activity |
| Audience projection | External PDFs render quantities only · no foreman_uid / no GPS |

## 5 · External PDF redaction (audience projection reused)

When a Daily Report PDF is generated for the `external` audience:

| Field | External PDF |
|---|---|
| Unit | ✅ Visible |
| Quantity | ✅ Visible |
| Station range | ✅ Visible |
| Activity status | ✅ Visible (started / continued / completed) |
| Affected crew (UID) | ❌ Stripped |
| Affected equipment ids | ❌ Stripped (counts only) |
| Notes (free text) | ✅ Visible (regex-redacted per M0.4 caption rules) |
| Coaching acknowledged | ❌ Stripped (internal telemetry) |

The same M0.4 audience-projection codepath governs this — no new
projection engine, just a new envelope shape inside the existing
projection.

## 6 · Validation gates

| Gate | Rule |
|---|---|
| `unit` required when row added | yes |
| `quantity` > 0 | yes |
| `quantity` upper bound | warn at 10× project-to-date avg (advisory · never blocks submit) |
| `unit == custom` requires `custom_unit_label` | yes |
| `station_from <= station_to` (lex sort) | warn · never block |
| At least one production row | NO · empty is valid |

## 7 · Migration impact (none)

Existing daily_reports rows have no `production` field. New rows get
`production: []` by default. Historical rows are not mutated (per
M1 freeze · `LEGACY_RECORD_FREEZE_CERTIFICATION.md`).

## 8 · Wave 1 build scope · this design's footprint

| Layer | Lines · new | Lines · modified |
|---|---|---|
| Backend model | ~40 | ~10 |
| Backend submit validator | ~25 | ~5 |
| Backend PDF renderer (production section) | ~60 | ~15 |
| Frontend step 4 component | ~180 | ~0 |
| Frontend OGC coaching hook | ~30 | ~5 |
| Backend tests | ~120 | ~0 |
| **Estimate** | **~455 lines new** | **~35 modified** |

Estimated dev-day: **1.5–2 days** for production tracking alone (no
RFI, no schedule, no P6).

---

_End of DAILY_REPORT_PRODUCTION_TRACKING_DESIGN.md._
