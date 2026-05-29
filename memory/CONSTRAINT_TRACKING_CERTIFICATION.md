# Constraint Tracking · Certification

_Phase V.2 · Wave-1A · 2026-05-29._

> Structured constraint rows added to Daily Reports. **11-type closed
> enum · chip-ready · advisory-flag derivation server-side.**

---

## 1 · Data contract

```python
class ConstraintRow(BaseModel):
    row_id: str                              # uuid · auto-generated
    constraint_type: Literal[
        "weather", "utility", "survey", "material", "equipment",
        "trucking", "mot", "cei_inspection", "owner_engineer",
        "safety", "other",
    ] = "other"
    hours_impact: Optional[float] = None     # 0–24 typical · optional
    notes: Optional[str] = None              # ≤ 280 chars
    may_require_rfi: bool = False            # advisory · derived server-side
    may_affect_schedule: bool = False        # advisory · derived server-side
```

Lives at `daily_reports.constraints: List[ConstraintRow]`. Coexists
with the legacy `schedule_delays: "Yes"/"No"` string (untouched).

## 2 · Closed enum · 11 constraint types (operator-approved)

| Type | Common cause |
|---|---|
| `weather` | rain / wind / lightning / heat / freeze |
| `utility` | undocumented FPL, gas, water, comm conflict |
| `survey` | missing control, busted layout, datum drift |
| `material` | late delivery, wrong mix, short load |
| `equipment` | breakdown, hydraulic, tire, attachment |
| `trucking` | shortage, late dispatch, blown route |
| `mot` | maintenance of traffic — signage change, escort delay |
| `cei_inspection` | consultant / construction engineering inspection hold |
| `owner_engineer` | owner pause, engineer direction, design change |
| `safety` | near-miss stand-down, JHA refresh, environmental hold |
| `other` | catch-all · foreman supplies context in notes |

Invalid types rejected at POST with HTTP 422 (test 7).

## 3 · Advisory flag derivation (operator-defined heuristic)

Constraint type → advisory flag mapping (server-side · deterministic):

| constraint_type | may_require_rfi | may_affect_schedule |
|---|---|---|
| `weather` | ❌ | ✅ |
| `utility` | ✅ | ✅ |
| `survey` | ✅ | ❌ |
| `material` | ❌ | ✅ |
| `equipment` | ❌ | ✅ |
| `trucking` | ❌ | ❌ |
| `mot` | ❌ | ✅ |
| `cei_inspection` | ✅ | ❌ |
| `owner_engineer` | ✅ | ❌ |
| `safety` | ❌ | ❌ |
| `other` | ❌ | ❌ |

Rationale documented in `ADVISORY_FLAG_CERTIFICATION.md`. These are
**informational signals only** — they do NOT create RFIs, modify
schedules, or notify anyone.

## 4 · Persistence rules

| Aspect | Rule |
|---|---|
| Insert | New rows accepted at `POST /api/daily-reports` |
| Update | New rows accepted at `PUT /api/daily-reports/{id}` |
| Delete | Forbidden (DELETE remains 410) |
| `row_id` | uuid auto-generated · preserved across updates |
| Advisory flags | Server overwrites at insert · operator can override on subsequent updates by re-asserting; Wave-1B will add the explicit lock semantic if needed |

## 5 · Backward compatibility

Every existing `daily_reports` row WITHOUT a `constraints` field
renders with `constraints: []` in API responses. No row mutated.
The legacy `schedule_delays: "Yes"/"No"` string still works; it is
preserved alongside the structured collection so legacy CSV exports
and reports keep functioning.

## 6 · Mobile-friendly hints (for Wave-1B UI design)

- **11-chip grid** in step 6 of the foreman flow
- **Zero-tap default** when no issues today ("No issues today · skip")
- **Single-tap to add** a constraint (chip click + optional hours
  keypad + optional voice notes)
- **Advisory flag previews** rendered inline in PM panel · invisible
  to foreman
- **Auto-save** at every change (≤ 2 s debounce)

## 7 · Validation gates

| Gate | Rule |
|---|---|
| `constraint_type` ∈ 11 closed enum | Pydantic enforced |
| `hours_impact` 0–24 if provided | Soft (typed as float) — no upper-bound enforcement in v1 |
| `notes` ≤ 280 chars | Soft (typed as str) — UI enforces |
| Empty `constraints[]` | Valid (no issues today) |

## 8 · API surface

| Endpoint | Behavior |
|---|---|
| `POST /api/daily-reports` | Accepts `constraints[]` · validates types · derives advisory flags · persists rows |
| `GET /api/daily-reports/{id}` | Returns the stored `constraints[]` including advisory flags |
| `PUT /api/daily-reports/{id}` | Replaces `constraints[]` if provided |
| `GET /api/daily-reports` (list) | Constraints not in summary projection (Wave-1A · narrow path) |
| `GET /api/daily-reports.csv` | Constraints not in v1 CSV (operator may add later) |

## 9 · External PDF audience projection (forward compatibility)

When the DR PDF renderer is extended (Wave-1C), the external audience
projection of `constraints[]` will:

| Field | External PDF |
|---|---|
| `constraint_type` | ✅ Visible |
| `hours_impact` | ✅ Visible |
| `notes` | ✅ Visible (regex-redacted per M0.4 caption rules) |
| `may_require_rfi` | ❌ Stripped (internal operator metadata) |
| `may_affect_schedule` | ❌ Stripped (internal operator metadata) |
| `row_id` | ❌ Stripped (uuid · internal) |

## 10 · Test coverage

3 dedicated cases in `test_wave_1a.py`:

- `test_constraints_persisted` — 3 typed constraints survive a round trip
- `test_constraint_type_closed_enum_rejected` — `wormhole` → 422
- `test_advisory_flags_derived` — utility=RFI+sched · weather=sched · other=neither

All 🟢.

## 11 · Field simplicity verdict (Doctrine Lock #1)

| Test | Answer |
|---|---|
| Can a foreman complete this in mud/gloves/5:30 PM? | **YES** (when UI lands · chip + keypad · ~10 s per constraint) |
| Time-to-complete impact | +10–15 s per constraint · 0–1 typical · still inside 5-min target |
| Forbidden patterns introduced | None |
| 9-step contract preserved | YES (constraint entry sits inside step 6, "Issues/Delays") |

PASS · constraint tracking ships.

---

_End of CONSTRAINT_TRACKING_CERTIFICATION.md._
