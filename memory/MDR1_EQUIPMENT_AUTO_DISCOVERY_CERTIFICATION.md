# M-DR-1 · Equipment Auto-Discovery · Certification

**Sprint:** M-DR-1 (Equipment Auto-Discovery)
**Status:** ✅ GREEN — code complete, tests green, live UI proven
**Date:** 2026-02-09
**Dependency:** M-3 Geocode Foundation (certified · `M3_GEOCODE_FOUNDATION_CERTIFICATION.md`)
**Doctrine:** Motive **SUGGESTS** · Foreman **VERIFIES** · Foreman **AUTHORS** (`MOTIVE_001_CONSTITUTIONAL_AUDIT.md` §E + §G.2)

---

## 1. What shipped

### 1.1 Backend (single new module · single mount line)
- **NEW** `/app/backend/routes/equipment_detection.py` — 270 LOC. Zero coupling to `motive_service.py` and to `daily_reports.py` (verified by `test_no_motive_service_coupling` + `test_no_daily_report_mutation`).
- **MOUNT** `/app/backend/server.py` (next to the M-3 mount).

### 1.2 Endpoint (public-read, foreman-facing)
| Method | Path | Auth | Purpose |
|---|---|---|---|
| GET | `/api/equipment-detection/{project_number}/{date}` | None (matches the Daily Report POST pattern — foreman has no admin token) | Returns Motive-observed equipment for the project on that UTC day. **No writes.** |

Response shape:
```json
{
  "ok": true,
  "project_number": "25-15",
  "date": "2026-06-09",
  "verified_geofences": 1,
  "events_considered": 4,
  "detections": [{
    "detection_key": "vehicle:1438259",
    "label": "2022 Mack Anthem",
    "asset_kind": "vehicle",
    "motive_vehicle_id": "1438259",
    "motive_asset_id": null,
    "masci_equipment_id": "TRUCK-42",
    "first_seen": "07:14",
    "last_seen":  "16:47",
    "dwell_minutes": 573,
    "confidence": "HIGH",
    "geofence": {"id": "1207777", "name": "Demo Job Site"},
    "pairs": [{"enter": "...07:14...", "exit": "...16:47...", "minutes": 573.0}],
    "source": "motive"
  }]
}
```

### 1.3 Detection algorithm (MDR1-1, MDR1-4)
1. **Project attribution gate:** ONLY `operational_locations` rows with `geocode_status == "Verified"` for the given `project_number` are accepted (uses M-3's join key `motive_geofence_id`). No verified link → empty result with `no_detection_reason="no_verified_geofence"`.
2. **Event window:** `motive_events` where `event_at` in `[date 00:00 UTC, date+1 00:00 UTC)` AND `event_family ∈ {geofence_enter, geofence_exit, asset_geofence_enter, asset_geofence_exit}` AND `raw.geofence.id ∈ {verified gids}`.
3. **Actor grouping:** by `vehicle:<motive_vehicle_id>` or `equipment:<motive_asset_id>`. Enters paired with the next-following exits; unpaired enters treated as "still on site" up to "now".
4. **Confidence banding (MDR1-4):**
   - **HIGH** — inside a Verified project geofence AND total dwell ≥ 5 minutes
   - **MEDIUM** — inside a Verified project geofence AND total dwell < 5 minutes (drive-through suspect; surfaced but visually downgraded)
   - **LOW** — never surfaced (audit §E.4: proximity heuristics are LOW and stay out of the foreman's UI). Test `test_no_low_band_is_ever_surfaced` enforces this.
5. **Label resolution:** lookup `asset_mappings` → `motive.year motive.make motive.model` for vehicles, or `motive.name` for equipment. Fallback to event payload `raw.asset.name`, finally fallback to `detection_key`.
6. **Sort:** HIGH first, then by first-seen ascending.

### 1.4 Frontend
- **NEW** `/app/frontend/src/components/daily-report/EquipmentDetectedToday.jsx` — full pane: counts strip, per-row Accept/Remove/Ignore, dwell + geofence display, "Detected by Motive" tagline (MDR1-5), empty-state with helpful reason hint, error-state with manual-entry fallback.
- **EDIT** `/app/frontend/src/pages/NewDailyReport.jsx` — embeds `<EquipmentDetectedToday>` above the Equipment Log `<RepeatBlock>`. `onAccept` calls `eq.add({...})` (the form's existing equipment helper), appending a new equipment row with `description`, `time_delivered`, `time_removed`, and a `notes` string that records the Motive provenance.

All required `data-testid`s present:
- `equipment-detected-today` (root), `equipment-detected-counts`, `equipment-detected-row-{key}`, `equipment-detected-accept-{key}`, `equipment-detected-remove-{key}`, `equipment-detected-ignore-{key}`, `equipment-detected-empty`, `equipment-detected-error`, `equipment-detected-diagnostics`.

### 1.5 Decision model (MDR1-3)
- **Accept** → ephemerally appends a row to `data.equipment` (the foreman's Daily Report state). The component marks the detection as accepted; the foreman can still edit / delete the row in the Equipment Log table below.
- **Remove** → ephemerally hides the row (no DB write — there is no decisions collection by design).
- **Ignore** → ephemerally greys the row (no DB write).

All decisions are component-local. On reload of the form, fresh suggestions are recomputed from server-side telemetry. This avoids creating a new write path purely for UI state, matches the OMEGA "minimal surface" principle, and prevents stale decisions from affecting tomorrow's report.

---

## 2. Live preview verification (real backend, seeded fixture, real UI)

```
$ curl http://127.0.0.1:8001/api/equipment-detection/MDR1-DEMO/2026-06-09
→ 4 detections: 3 HIGH (Mack Anthem 573 min · CAT 320 EX-4 565 min · Peterbilt 567 477 min)
  + 1 MEDIUM (drive-through 3 min) — LOW confidence NEVER surfaces.
```

Screenshot of `/daily/new` with project_number=MDR1-DEMO + Equipment Log expanded:
- Counts strip: HIGH 3 · MEDIUM 1 · ACCEPTED 0 · IGNORED 0
- Row 1: HIGH · 2022 Mack Anthem · 07:14 → 16:47 · 573 min · Demo Job Site · Accept/Remove/Ignore
- Row 2: HIGH · CAT 320 EX-4 · 07:30 → 16:55 · 565 min
- Row 3: HIGH · 2019 Peterbilt 567 · 08:03 → 16:00 · 477 min
- Row 4: MEDIUM · Vehicle Mdr1-Demo-Veh-3 · 09:21 → 09:24 · 3 min (correctly downgraded)

The "Detected by Motive · You confirm what was on site" sub-label is visible per MDR1-5.

---

## 3. Test results

```
$ pytest tests/test_mdr1_equipment_detection.py tests/test_m3_geocode_foundation.py -v
======================== 23 passed in ~26s =========================
  • test_mdr1_equipment_detection.py        11 / 11
  • test_m3_geocode_foundation.py (regression)  12 / 12
```

| Test | Required by | Validates |
|---|---|---|
| `test_high_confidence_long_dwell` | MDR1-4 HIGH | 573 min dwell → HIGH, label resolution via asset_mappings, geofence.id attribution |
| `test_medium_confidence_drive_through` | MDR1-4 MEDIUM | 3-minute dwell → MEDIUM |
| `test_project_attribution_via_verified_geofence_only` | MDR1-1 | Flipping the op-locations row to Rejected → zero detections, reason="no_verified_geofence" |
| `test_unknown_project_returns_empty` | safety | Unknown project_number → empty result, no crash |
| `test_invalid_date_format_rejected` | safety | "2026-13-99" → 400 Bad Request |
| `test_no_low_band_is_ever_surfaced` | MDR1-4 LOW | Zero-dwell pair stays MEDIUM (inside fence); LOW never appears in response |
| `test_no_daily_report_mutation` | constitutional | `daily_reports`, `dispatch_assignments`, `motive_events`, `asset_mappings`, `operational_locations` counts unchanged after 3 calls |
| `test_no_motive_service_coupling` | constitutional | Router source has no `motive_service`/`MotiveService`/`httpx` reference |
| `test_constants_match_doctrine` | MDR1-4 | `HIGH_DWELL_MIN==5` · `PRESENCE_EVENTS=={4 expected}` |
| `test_m3_collection_untouched` | M-3 regression | All seeded op_locations keys preserved byte-for-byte after the endpoint runs |
| `test_endpoint_does_not_require_admin_token` | MDR1-5 | Foreman-facing → public-read, no auth required |
| **M-3 regression** | — | 12 of 12 M-3 tests still green (no regression) |

Lint: ✅ ruff clean (Python) · ✅ eslint clean (JS).

---

## 4. Constitutional adherence — what we did NOT do

| Forbidden behavior | How we ensured it didn't happen | Verified by |
|---|---|---|
| ❌ Auto-add equipment to a Daily Report | The endpoint never writes; the JSX panel only appends to `data.equipment` if the foreman taps Accept | `test_no_daily_report_mutation` |
| ❌ Auto-submit a Daily Report | This sprint doesn't touch `/api/daily-reports` POST at all | endpoint mount review |
| ❌ Auto-create equipment rows | Only the foreman's tap → `eq.add(...)` triggers any row insertion (and that's into form-local state, not DB) | source review |
| ❌ Auto-create production | We never touch `production[]` | grep |
| ❌ Auto-create material movement | We never touch `dispatch_assignments` / `outbound_materials` | `test_no_daily_report_mutation` |
| ❌ Auto-close verification gaps | M-3 verification queue remains operator-driven | `test_m3_collection_untouched` |
| ❌ Generate OA events | No `workflow_state_events` write | source review |
| ❌ Notify users | No email / SMS / push code path | source review |
| ❌ Surveil drivers | The endpoint surfaces detections per *project*, not per *driver*. `driver_id` is intentionally not part of the response shape. | source review |
| ❌ Push to Motive | Router has zero outbound HTTP. No `httpx`, no `MotiveService`. | `test_no_motive_service_coupling` |

---

## 5. Required test checklist (per brief MDR1)

| # | Requirement | Status | Evidence |
|---|---|---|---|
| 1 | Correct project attribution | ✅ | `test_project_attribution_via_verified_geofence_only` — only Verified op-locations attribute |
| 2 | HIGH confidence detection | ✅ | `test_high_confidence_long_dwell` (573 min → HIGH) |
| 3 | MEDIUM confidence detection | ✅ | `test_medium_confidence_drive_through` (3 min → MEDIUM) |
| 4 | Foreman acceptance | ✅ | `onAccept` callback appends to `data.equipment`; live UI screenshot |
| 5 | Foreman removal | ✅ | `decisions[key]="remove"` hides row in `visible` memo |
| 6 | Foreman ignore | ✅ | `decisions[key]="ignore"` greys row, keeps visible |
| 7 | No auto-authoring | ✅ | `test_no_daily_report_mutation` |
| 8 | No DR mutation without approval | ✅ | Same test; no endpoint writes to daily_reports |
| 9 | Geofence linkage works | ✅ | Live data shows correct geofence.id + name attribution |
| 10 | No regression to M-3 | ✅ | 12/12 M-3 tests still pass; `test_m3_collection_untouched` confirms zero drift |
| Regression suite | ✅ | 23/23 combined M-3 + M-DR-1 pass |
| Lint | ✅ | ruff + eslint clean |
| Screenshots | ✅ | `/tmp/mdr1_final3.jpg` with 3 HIGH + 1 MEDIUM in real Daily Report |

---

## 6. Success criterion (per brief)

> A superintendent can open a Daily Report and immediately see "Equipment Detected Today" with trustworthy suggestions that reduce typing while preserving human accountability.

**Met.** The screenshot proves: open `/daily/new`, type the project number, expand the Equipment Log card → the foreman sees 3 HIGH suggestions with timestamps + dwell time + geofence, plus a MEDIUM drive-through row that's clearly visually flagged. One tap on **Accept** auto-populates a new equipment row in the existing Equipment Log table with the Motive provenance recorded in `notes`. No DR is modified without that tap. No driver names are surfaced. No surveillance.

---

## 7. What is explicitly NOT in this sprint (per brief)

- ❌ M-2 Event Router — not built
- ❌ Verification Layer — not built
- ❌ Dispatch automation — not built
- ❌ Daily Report mutations beyond the Accept tap — none
- ❌ Production / material movement automation — none
- ❌ OA events / notifications — none
- ❌ Pushes to Motive — none

🛑 **STOP. Awaiting explicit authorization for M-2 Event Router.**
