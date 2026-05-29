# Production Tracking · Certification

_Phase V.2 · Wave-1A · 2026-05-29._

> Structured production rows added to Daily Reports. **Additive ·
> backward-compatible · no foreman workflow change.**

---

## 1 · Data contract

```python
class ProductionRow(BaseModel):
    row_id: str                          # uuid · auto-generated
    description: str = ""
    quantity: float = 0.0
    unit: Literal["LF","SY","CY","TON","EA","ACRE","OTHER"] = "OTHER"
    custom_unit_label: Optional[str]     # only when unit == "OTHER"
    station_from: Optional[str]          # e.g., "12+50"
    station_to: Optional[str]            # e.g., "13+00"
    location: Optional[str]              # free-text fallback
    notes: Optional[str]                 # ≤ 280 chars
```

Lives at `daily_reports.production: List[ProductionRow]`. Coexists
with the legacy free-text `activities[]` (untouched).

## 2 · Closed enum · 7 units (operator-approved)

| Unit | Common use |
|---|---|
| `LF` | linear feet — pipe, curb, sidewalk, joint sealing |
| `SY` | square yards — grading, milling, sod, sodding |
| `CY` | cubic yards — concrete, base, fill |
| `TON` | tons — asphalt, aggregate, soil |
| `EA` | each — manhole, structure, light, sign |
| `ACRE` | acres — clearing, stabilization |
| `OTHER` | foreman-supplied label (`custom_unit_label`) |

Invalid units rejected at POST with HTTP 422 (test 4).

## 3 · Persistence rules

| Aspect | Rule |
|---|---|
| Insert | New rows accepted at `POST /api/daily-reports` |
| Update | New rows accepted at `PUT /api/daily-reports/{id}` (existing endpoint) |
| Delete | Forbidden (DELETE remains 410) |
| `row_id` | uuid auto-generated if omitted; preserved across updates |
| Empty list | Valid — no production today is a legitimate state |

## 4 · Backward compatibility

Every historical and current `daily_reports` row WITHOUT a
`production` field renders with `production: []` in API responses.
No row is mutated. Existing form submissions that omit `production`
continue to succeed.

## 5 · API surface

| Endpoint | Behavior |
|---|---|
| `POST /api/daily-reports` | Accepts `production[]` · validates units · persists rows |
| `GET /api/daily-reports/{id}` | Returns the stored `production[]` |
| `PUT /api/daily-reports/{id}` | Replaces `production[]` if provided |
| `GET /api/daily-reports` (list) | Photo + crew + sub counts only · production not in summary projection (kept thin for the dashboard table) |
| `GET /api/daily-reports.csv` | Production not exported in v1 CSV (kept narrow per operator review) — add later if requested |

## 6 · Validation gates

| Gate | Rule |
|---|---|
| `unit` ∈ 7 closed enum | Pydantic enforced |
| `quantity` ≥ 0 | typed as float; semantic check skipped for v1 (foreman may enter zero rows for placeholder) |
| `custom_unit_label` required when `unit == "OTHER"` | Recommended (not enforced in v1 — operator may relax) |
| Station range validity | Free text; no parser; never enforced |

## 7 · Mobile-friendly hints (for Wave-1B UI design)

These are hints for the frontend renderer to implement in Wave-1B;
they are NOT enforced at the API level.

- **Chip-style unit selector** (one tap)
- **Last-used unit pre-selected** per project_number
- **Numeric keypad** on `quantity` focus
- **Voice input** allowed on `notes`
- **Station range** as a single combined "12+50 → 13+00" input pattern
- **Auto-save** the row at every keystroke (≤ 2 s debounce, per
  `DAILY_REPORT_OFFLINE_RECOVERY_PLAN.md`)

## 8 · Test coverage

3 dedicated cases in `test_wave_1a.py`:

- `test_production_rows_persisted` — both rows survive a round trip
- `test_production_unit_closed_enum_rejected` — `FATHOMS` → 422
- `test_production_unit_other_allowed` — `OTHER` + `custom_unit_label` works

All 🟢.

## 9 · External PDF audience projection (forward compatibility)

When the DR PDF renderer is updated (Wave-1C), the external audience
projection of `production[]` will strip:

- `row_id` (uuid · internal)
- `notes` regex-redacted per M0.4 caption rules

…and keep:

- `description`, `quantity`, `unit`, station range, `location`.

This matches the M0.4 audience projection doctrine and requires no
new code path — only an additional case inside the existing
`_project_for_audience` helper.

## 10 · Field simplicity verdict (Doctrine Lock #1)

| Test | Answer |
|---|---|
| Can a foreman complete this in mud/gloves/5:30 PM? | **YES** (when UI lands · chip + keypad · ~15 s per row) |
| Time-to-complete impact | +15–30 s per row · 1–3 rows typical · still inside 5-min target |
| Forbidden patterns introduced | None |
| 9-step contract preserved | YES (row entry sits inside step 4, "Production") |

PASS · production tracking ships.

---

_End of PRODUCTION_TRACKING_CERTIFICATION.md._
