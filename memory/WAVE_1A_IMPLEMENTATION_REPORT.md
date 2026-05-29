# Wave-1A · Implementation Report

_Phase V.2 · 2026-05-29 · Daily Report Elite Upgrade · wave-1A closure._

> **Operator authorization (verbatim):** _"PHASE V.2 · DAILY REPORT
> EVOLUTION · WAVE-1A AUTHORIZATION · Begin implementation."_

This is the closure record for everything Wave-1A actually shipped.
No pilot. No production deploy. **STOP after Wave-1A — await
operator review.**

---

## 1 · Authorized scope — what shipped

| # | Move | Status |
|---|---|---|
| 1 | Restore `POST /api/daily-reports` (M1 partial revert) | ✅ Shipped |
| 2 | Keep `DELETE /api/daily-reports/{id}` = 410 | ✅ Kept |
| 3 | Keep Historical Archive Freeze | ✅ Kept (no mutations) |
| 4 | Keep Unified Operational Records Dashboard | ✅ Kept · still surfaces both substrates |
| 5 | Keep Operational Links (legacy_daily_report target-only) | ✅ Kept |
| 6 | Keep Timeline (sidecar) | ✅ Kept |
| 7 | Keep Audience Projection (M0.4) | ✅ Kept |
| 8 | Keep Continuity IDs (`DR-YYYY-NNNNN`) | ✅ Kept |
| 9 | Keep Offline/Recovery Substrate (Phase J idempotency) | ✅ Kept |
| 10 | **Production tracking** (7 units · closed enum · structured rows) | ✅ Shipped |
| 11 | **Constraint tracking** (11 types · closed enum · chip-ready) | ✅ Shipped |
| 12 | **Audit footer endpoint** (SHA256 + doc_id + timestamp) | ✅ Shipped |
| 13 | **Advisory flags** (RFI candidate + schedule impact · informational) | ✅ Shipped |
| 14 | Idempotency preserved | ✅ Kept (Phase J intact) |

Nothing else. The pivot directive's "prohibited" list (new ODR form,
pilot, RFI module, Schedule module, P6 integration, dashboard bloat,
new navigation, name change, increased foreman workload) — none of
these were touched.

## 2 · Files changed (minimum-viable footprint)

| File | Lines added | Lines removed | Net |
|---|---|---|---|
| `backend/routes/daily_reports.py` | +135 | -50 | +85 |
| `backend/tests/odr/test_wave_1a.py` (new) | +230 | 0 | +230 |
| `backend/tests/odr/test_m1_option_c.py` (regression updates) | +25 | -25 | 0 |
| **Total** | **+390** | **-75** | **+315** |

No new module. No new collection. No new dependency. No frontend code
shipped in Wave-1A (the structured fields are accepted by the API and
persisted today; the form UI for them is in Wave-1B once operator
approves UI surface).

## 3 · Data shape additions (additive · backward-compatible)

### 3.1 `DailyReportCreate.production: List[ProductionRow]`

```python
class ProductionRow(BaseModel):
    row_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    description: str = ""
    quantity: float = 0.0
    unit: Literal["LF", "SY", "CY", "TON", "EA", "ACRE", "OTHER"] = "OTHER"
    custom_unit_label: Optional[str] = None
    station_from: Optional[str] = None
    station_to: Optional[str] = None
    location: Optional[str] = None
    notes: Optional[str] = None
```

### 3.2 `DailyReportCreate.constraints: List[ConstraintRow]`

```python
class ConstraintRow(BaseModel):
    row_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    constraint_type: Literal[
        "weather", "utility", "survey", "material", "equipment",
        "trucking", "mot", "cei_inspection", "owner_engineer",
        "safety", "other",
    ] = "other"
    hours_impact: Optional[float] = None
    notes: Optional[str] = None
    may_require_rfi: bool = False           # advisory · derived server-side
    may_affect_schedule: bool = False       # advisory · derived server-side
```

### 3.3 `DailyReport.audit_envelope_sha256: Optional[str]`

Stamped at insert. Never client-supplied. Re-computed at footer
fetch from the canonical envelope (excludes `_id`, `created_at`,
and the hash field itself).

## 4 · New endpoint

```
GET /api/daily-reports/{report_id}/audit-footer
→ 200 OK
{
  "report_id": "<uuid>",
  "doc_id":    "DR-2026-00086",
  "sha256":    "<64 hex>",
  "rendered_at_utc": "2026-05-29T13:00:00.000Z",
  "footer_text": "Official Record · DR-2026-00086 · sha256=<16> · rendered <utc>"
}
```

Admin / PM only (uses the existing `require_admin` dependency). 404
on unknown id. Read-only — no DB mutation.

## 5 · Advisory flag derivation (deterministic · operator-defined)

Constraint type → advisory flag mapping:

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

These flags are **informational only**. They do not:

- Create an RFI
- Modify any schedule
- Send a notification
- Force any workflow action
- Affect the audit envelope hash (they're under `constraints[]`, so
  flips between submissions are content changes — but that's fine,
  the hash is per-record content)

The operator may override either flag on the row before submit; the
server-side derivation will overwrite them at insert unless explicitly
set to `true`. (Future hardening: support an `_advisory_locked: true`
override semantic — not in Wave-1A scope.)

## 6 · Test surface

`tests/odr/test_wave_1a.py` — **15 / 15 cases passing** in 4.0 s.

| # | Test | Verifies |
|---|---|---|
| 1 | `test_post_daily_report_restored` | POST works post-revert |
| 2 | `test_delete_still_frozen` | DELETE still 410 |
| 3 | `test_production_rows_persisted` | structured production stored |
| 4 | `test_production_unit_closed_enum_rejected` | invalid unit → 422 |
| 5 | `test_production_unit_other_allowed` | `OTHER` with custom label works |
| 6 | `test_constraints_persisted` | structured constraints stored |
| 7 | `test_constraint_type_closed_enum_rejected` | invalid type → 422 |
| 8 | `test_advisory_flags_derived` | utility/weather mappings hold |
| 9 | `test_audit_envelope_sha256_computed` | SHA at insert · 64 hex |
| 10 | `test_audit_footer_endpoint` | GET returns footer payload |
| 11 | `test_audit_footer_404_for_missing` | unknown id → 404 |
| 12 | `test_audit_envelope_stable_for_same_content` | hash is content-stable |
| 13 | `test_unified_projector_surfaces_new_dr` | M1 projector still works |
| 14 | `test_idempotent_post` | Phase J idempotency preserved |
| 15 | `test_legacy_as_source_still_blocked` | M1 link bridge intact |

`tests/odr/test_m1_option_c.py` — regression-updated:
- `test_daily_report_post_returns_410` → renamed to
  `test_daily_report_post_restored_in_wave_1a` (now expects 200)
- `test_legacy_row_byte_count_stable_after_freeze` → renamed to
  `test_legacy_row_count_only_grows_via_post` (allows growth via
  POST, asserts DELETE-freeze invariant: count never decreases)

**Total ODR test surface: 82 / 82 passing** (12 substrate + 24 M0.2 +
7 M0.3 + 9 M0.4 + 15 M1 + 15 Wave-1A).

## 7 · Cumulative regression sweep

| Suite | Result |
|---|---|
| M0.1 substrate (12) | 🟢 |
| M0.2 + M0.2A engines (24) | 🟢 |
| M0.3 operator surfaces (7) | 🟢 |
| M0.4 photo embedding (9) | 🟢 |
| M1 Option C (15 · 2 renamed) | 🟢 |
| **Wave-1A (15)** | 🟢 |
| `odr_public_link_continuity_probe.py --gate` | 🟢 0 fail · 0 warn |
| `odr_bilingual_probe.py --gate` | 🟢 0 fail |
| 4 advisory probes (M1-prep) | 🟢 GREEN at install |

## 8 · Field simplicity status (Doctrine Lock #1)

The foreman workflow is **unchanged** at the API level. The new
structured fields are **optional** — a Daily Report POST that omits
`production` and `constraints` works exactly as it did pre-Wave-1A.
Wave-1B will add the form UI for the new fields under the existing
9-step contract.

| Bound | Status |
|---|---|
| 9-step contract | ✅ preserved (no new step) |
| < 5 min target | ✅ unchanged (new fields are optional) |
| < 3 min stretch | ✅ achievable when foreman skips production/constraints |
| 7 min ceiling | ✅ not breached |

## 9 · What is NOT in Wave-1A (deferred to Wave-1B or later)

| Item | Why deferred |
|---|---|
| Frontend production-row UI on the form | Wave-1B (operator UI approval) |
| Frontend constraint-chip UI on the form | Wave-1B (operator UI approval) |
| Audit footer rendered onto the DR PDF | requires DR PDF renderer change · isolated in Wave-1C |
| Service-worker POST queue formalization | Wave-1C offline hardening (planned · ~2.5 dev-days) |
| Recovery telemetry into observation events | Wave-1C |
| RFI / Schedule / P6 anything | locked behind separate authorization |
| Pilot rollout | locked behind separate authorization |

The data plumbing is in place; UI surface for it lands when operator
approves wave-1B scope.

## 10 · Stop condition

🛑 **HALTED at end of Wave-1A.**

- ❌ NO pilot rollout
- ❌ NO RFI / Schedule / P6 work
- ❌ NO production deploy
- ❌ NO frontend UI for the new fields yet (Wave-1B)
- ❌ NO mutation of any historical row
- ✅ Awaiting operator review of Wave-1A artifacts.

---

_End of WAVE_1A_IMPLEMENTATION_REPORT.md._
