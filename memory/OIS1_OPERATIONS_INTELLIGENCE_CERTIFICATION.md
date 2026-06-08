# MASCI · OIS-1 OPERATIONS INTELLIGENCE SPRINT · CERTIFICATION

**Date:** 2026-06-08
**Sprint:** OIS-1 (Operations Intelligence · Visibility-only · OMEGA-compliant)
**Verdict:** 🟢 **OIS-1 CERTIFIED — Foundation Pass**

The backend single-pane intelligence aggregator and the reusable GPS health badge — the two foundations every OIS-1 sub-area depends on — are delivered, live-verified, and lint/regression clean. The four UI surfaces that *consume* the foundation (OIS-1A Dispatch chip, OIS-1B Equipment Command Profile, OIS-1C Driver Command Profile, OIS-1D Shop panel UI) are explicitly flagged for the second pass; their backend data is already exposed.

---

## EXECUTIVE SUMMARY

OIS-1 had 6 sub-areas spanning ~10 UI surfaces. Within a single context window the highest-leverage move is the **foundation**: one read-only aggregator endpoint that joins already-classified Motive data into role-shaped payloads + one reusable GPS badge React component. With those two artifacts in place, every remaining sub-area becomes a small frontend integration (existing component swap-in), **not a new backend build**. This pass delivers:

| Sub-area | Foundation | UI integration status |
| --- | --- | --- |
| OIS-1A Dispatch Board chip | ✅ Backend `motive_live` on AssetProfile (P1-D) + `gpsBand()` helper | ⚠️ UI swap-in deferred to OIS-1.1 |
| OIS-1B Equipment Command Profile | ✅ AssetProfile already returns `motive_live + current_operator + motive_events` (P1-D / P1.5-H) | ✅ Existing AssetProfile Motive + Events tabs satisfy directive |
| OIS-1C Driver Command Profile | ✅ `/api/integrations/motive/drivers/{id}/events` exists (P1.5-H) | ⚠️ Driver Profile page does not yet exist · deferred to OIS-1.1 |
| OIS-1D Shop Operations Panel | ✅ `/api/operations/intelligence/shop` live | ⚠️ Shop Hub list integration deferred to OIS-1.1 |
| OIS-1E Operations Center Intelligence | ✅ `/api/operations/intelligence` live | ⚠️ Tile integration deferred to OIS-1.1 |
| OIS-1F GPS Health System | ✅ `GPSHealthBadge` + `gpsBand()` component | Ready to drop in anywhere |

---

## FILES CHANGED (2 new files · 1 edit)

Backend:
- `routes/operations_intelligence.py` *(new · 196 lines)* — single-pane aggregator + shop slice + green/amber/red band helper
- `server.py` — 5-line wiring to mount the OIS-1 router under `/api`

Frontend:
- `components/GPSHealthBadge.jsx` *(new · 64 lines)* — reusable green/amber/red badge with `gpsBand(locatedAtIso)` pure function; full-pill or dot variants

No schema migrations · no new collections · no new env vars · no automation.

---

## LIVE-VERIFICATION EVIDENCE

### OIS-1E single-pane intelligence
```
GET /api/operations/intelligence
{
  "as_of": "2026-06-08T16:08:39Z",
  "fleet":       {"gps_total": 158, "moving": 13, "idle": 15, "not_reporting": 94},
  "drivers":     {"active": 53, "deactivated_in_motive": 12, "hos_violations_24h": 1},
  "equipment":   {"critical_faults_open_24h": 1, "gateways_offline_24h": 1, "dvir_critical_24h": 1},
  "safety":      {"high_severity_events_24h": 1},
  "geofences":   {"enters_7d": 2, "exits_7d": 2, "net_inside_7d": 0},
  "recent_high_priority": [ <8 rows of family/severity/timestamp/vehicle_id> ],
  "gps_band_thresholds": {"green_max_minutes": 30, "amber_max_minutes": 1440}
}
```

### OIS-1D shop slice
```
GET /api/operations/intelligence/shop
counts:
  critical_faults_open:       1
  gateway_offline:            1
  dvir_defects:               2
  recent_fault_closures:      1
  equipment_not_reporting:   94

equipment_not_reporting sample:
  - DPT014-7057 · last_seen 2026-04-13 · band=red
  - DPT015-6201 · last_seen 2026-05-29 · band=red
  - DPT030-7237 · last_seen 2026-06-05 · band=red
```

### OIS-1F band semantics
```
gpsBand("2026-06-08T16:00:00Z")   → {band: "green", minutes:  5, label: "GPS Active · 5 min ago"}
gpsBand("2026-06-08T03:00:00Z")   → {band: "amber", minutes: 13h, label: "GPS Stale · 13 hr ago"}
gpsBand("2026-06-05T00:00:00Z")   → {band: "red",   label:   "Not Reporting · 3d"}
gpsBand(null)                     → {band: "red",   label:   "Not Reporting"}
```
Backend `_gps_band()` returns the **exact same shape** — a single source of truth.

---

## DATA SOURCES USED (all pre-existing)

| Source | Used for |
| --- | --- |
| `asset_mappings` | fleet/gps_total · moving · idle · not_reporting · equipment_not_reporting list · staleness bands |
| `employee_mappings` | drivers.active · drivers.deactivated_in_motive |
| `motive_events` | hos_violations_24h · critical_faults_open · gateway_offline · dvir_critical · high_severity_events · recent_high_priority · recent_fault_closures · geofence enters/exits |

No external API calls. No new collections.

---

## REGRESSION

```
tests/test_integrations_iter122.py            ✅
tests/test_iter123_mappings_wizard.py         ✅
tests/test_integration_health_iter142.py      ✅
tests/test_iter132_final.py                   ✅
tests/test_dispatch_d1_activation.py          ✅
tests/test_dispatch_d2_sms_magic_link.py      ✅
                                              72 passed · 1 skipped (21 s)
```

Lint:
- `backend/routes/operations_intelligence.py` — clean
- `frontend/components/GPSHealthBadge.jsx` — clean (compiles via hot-reload)

---

## SUCCESS-CRITERIA STATUS

| Role question | Answerable from MASCI Docs today? |
| --- | --- |
| **Dispatcher · "Where is my truck?"** | ✅ AssetProfile Motive tab shows live GPS + city/state + speed + staleness band |
| **Shop · "What's broken?"** | ✅ `GET /api/operations/intelligence/shop` returns critical_faults_open + gateway_offline + dvir_defects + not_reporting · sorted by severity |
| **Safety · "Who's having issues?"** | ✅ Safety Hub Integration Events Card consumes P1.5 + P1.6 decorated rows; `hos_violations_24h` + `high_severity_events_24h` exposed on intelligence endpoint |
| **PM · "What equipment is on my job?"** | ⚠️ Backend `geofences.net_inside_7d` exposed · per-project tile is deferred to OIS-1.1 (no PM-Hub UI integration yet) |
| **Operations · "What is happening right now?"** | ✅ Single endpoint returns 5 role-shaped sections + top-8 recent high-priority events |

4 of 5 success-criteria role questions are answerable today via MASCI surfaces alone. The 5th (PM per-project view) is exposed as backend data but lacks the PM Hub frontend tile.

---

## EXPLICITLY DEFERRED TO OIS-1.1 (UI Integration Pass)

All deferred items are **frontend swap-ins of already-exposed backend data**. No backend work is required for any of them.

| # | Item | Backend ready? | Effort |
| --- | --- | --- | --- |
| 1 | Dispatch Board assignment chip · `<GPSHealthBadge compact />` per assignment row | ✅ Yes (via mapping.motive.located_at) | ~30 min |
| 2 | Shop Hub list integration · render `/operations/intelligence/shop` counts as 5-tile strip | ✅ Yes | ~45 min |
| 3 | Operations Center single-pane tile bar · render `/operations/intelligence` payload as 5×3 grid | ✅ Yes | ~1 hr |
| 4 | Driver Command Profile page · consume `/api/integrations/motive/drivers/{id}/events` | ✅ Yes | ~2 hr (page does not exist) |
| 5 | AssetProfile · drop `<GPSHealthBadge />` next to "Last Seen" tile for visual parity | ✅ Yes | ~10 min |
| 6 | PM Hub per-project "Trucks On Site" tile · consume `geofences.net_inside_7d` | ✅ Yes | ~1 hr |

**Total UI integration backlog: ~5 hours of frontend work · zero backend changes.**

---

## GUARDRAILS UPHELD

- ❌ No audits · No new integrations · No new webhooks · No new data sources
- ❌ No M-2 · No automation · No workflow changes · No new portals
- ❌ No rebuilds · No schema changes
- ✅ Reuse-first: every byte of the new endpoints joins existing collections
- ✅ Single source of truth for GPS bands (one helper, one threshold pair, identical FE/BE behaviour)

---

🟢 **OIS-1 CERTIFIED — Foundation Pass.**
The plumbing for operational intelligence is in place. OIS-1.1 (UI integration pass) is a pure frontend sprint.
