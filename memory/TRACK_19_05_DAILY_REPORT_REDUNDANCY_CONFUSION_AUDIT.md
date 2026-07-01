# Track 19.05 · Daily Report Redundancy / Confusion Audit

Deep look at duplicate concepts and confusing pairs. No merging in this track — audit only.

## Confusing pairs

### 1. Activity Log vs Production Log vs Notes

| Field | What it stores | Route to PDF/PM/email | Recommendation |
| --- | --- | --- | --- |
| `activities[]` | Free-text `{description, notes}` rows (legacy pre-Wave-1A) | Yes | Retain schema; UI can hide behind "Add unstructured note" fallback |
| `production[]` | Structured `{description, quantity, unit, station_from, station_to, location, notes}` | Yes (Wave-1A + advisory) | **Primary** in redesign |
| `general_notes` | Single free-text catch-all | Yes | Retain; low usage; consider hiding until user opens "Additional notes" |
| `narrative_sections{}` | 6-prompt guided narrative | Yes | Merge with general_notes UI or expose one prompt at a time |

**Redesign candidate**: consolidate the UI into `Production Log` (structured, primary) + `Notes` (optional). `activities[]` remains persisted schema for legacy but hidden from the redesigned surface.

### 2. Delay vs Extra Work vs Weather Delay

| Signal | Where it lives | Redundancy |
| --- | --- | --- |
| `schedule_delays = Yes` + `schedule_delays_notes` | Section 03 (safety triggers) | Overlaps with `constraints[]` |
| `constraints[]` with `constraint_type=weather/material/…` | Section 10 structured (Wave-1A) | Preferred |
| `weather_impact = Yes` + `weather_impact_notes` | Section 02 | Overlaps with `constraints[]` weather type |
| "Extra work" | Not a distinct field — captured in narrative or activities | Confusion source (users expect a field) |

**Redesign candidate**: single "Delays & Constraints" section powered by `constraints[]`. Weather/schedule triggers become auto-derived from constraint rows.

### 3. Injury vs Accident vs Safety Incident

| Trigger | Reveals | Redundancy |
| --- | --- | --- |
| `safety_incidents_today = Yes` | incident_notes | Broadest term |
| `injuries_reported = Yes` | safety_notified cascade | Subset of incident |
| "Accident" | Not a distinct field | Users may enter into incident_notes |

**Redesign candidate**: one Yes/No "Did anything on-site require safety review today?" with sub-type radio (Incident / Injury / Near Miss / Property Damage). Persisted schema keeps both `safety_incidents_today` and `injuries_reported` for legacy PDF.

### 4. Materials Delivered vs Materials Used

Currently `materials[]` = inbound deliveries only (MM-001B-F1 doctrine). "Materials Used" is captured via `production[]` quantity (heavy civil pattern). This is CORRECT but foremen conflate "delivered" with "used" — UI clarity needed.

### 5. Materials Exported vs Hauling

`outbound_materials[]` (MM-ENTRY-002 K-MM-1) is the singular field. UI labels it "Outbound Materials / Hauled Off" — CORRECT and consistent.

### 6. Visitors vs Subcontractors

Distinct:
* `subcontractors[]` = performing work on-site.
* `visitors[]` = present but not performing work.

Fine as-is; UI should just clarify with helper text.

### 7. Equipment On Site vs Equipment Used

`equipment[]` currently combines both (description + hours_used + time_delivered/removed). No dedicated "On-site inventory" concept. Fine as-is for heavy civil — hours = 0 means "on-site not used today".

### 8. Attachments vs Photos

Post-Track-19.04:
* `photos[]` = image files (min 6, embedded in PDF).
* `attachments[]` = PDF/XLSX/XLS/CSV.

Clear separation, both grouped in PM detail by category. NOT confusing.

### 9. PM notes vs General notes

Only `general_notes` exists (there is no distinct `pm_notes` field). No redundancy.

## Redundancy risk matrix

| Pair | Store different data? | Route differently? | Merge risk? | Recommendation |
| --- | --- | --- | --- | --- |
| activities vs production | Yes (structure) | Same PDF section | LOW schema risk, HIGH UX benefit | UI-merge into "Production Log" |
| schedule_delays vs constraints | Yes (structured) | Same advisory flags | MED — both feed exposure signals | UI-merge, keep both persisted |
| weather_impact vs constraints(type=weather) | Yes | Same | MED | UI-merge, auto-populate constraint from weather Yes |
| incidents vs injuries | Yes (severity) | Different email routing | HIGH — safety/insurance implications | KEEP separate |
| materials vs outbound | Direction | Different PDF sections | HIGH | KEEP separate |
| visitors vs subcontractors | Role | Different sections | HIGH | KEEP separate |
| photos vs attachments | Type | Different R2 prefix | HIGH | KEEP separate |
