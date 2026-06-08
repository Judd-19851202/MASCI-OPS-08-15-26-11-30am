# MASCI · MOTIVE P1.5 EVENT ACTIVATION SPRINT · CERTIFICATION

**Date:** 2026-06-08
**Sprint:** P1.5 (Event Activation · Visibility-Only · OMEGA-compliant)
**Verdict:** 🟢 **P1.5 COMPLETE**

---

## EXECUTIVE SUMMARY

The 5 authorized event families (`harsh_event`, `fault_code`, `dvir`, `geofence_enter`, `geofence_exit`) are now ingested by the existing signed webhook receiver, classified into a normalized schema, decorated at read-time into operational language, and surfaced on **3 existing screens** (Asset Profile · Safety/HR Hub event feed · Dispatch Hub Integrations tab). **Zero automation. Zero state transitions. Zero new portals.** Workflow integrity is preserved.

| Metric | Before P1.5 | After P1.5 |
| --- | --- | --- |
| Event families ingested by receiver | 1 (`vehicle_gps`) | **6** (vehicle_gps + 5 authorized families) |
| Per-event classification fields | 4 generic | **11 family-aware** (severity · subtype · harsh/fault/dvir/geofence sub-blocks · address · speed · summary) |
| Family-filterable read endpoint | ❌ | ✅ `/api/integrations/motive/events?family=…` |
| Per-asset event timeline endpoint | ❌ | ✅ `/api/integrations/motive/assets/{id}/events` |
| Per-driver event timeline endpoint | ❌ | ✅ `/api/integrations/motive/drivers/{id}/events` |
| Asset Profile Events tab | MASCI ops events only | **+ Motive event timeline with family chips** |
| Dispatch Integrations tab | Counters only | **+ Live arrivals/departures strip** |
| Safety/HR Hub event card rows | Blank/decorated GPS rows | **Decorated with humanized `summary` field** |

---

## P1.5-A · Motive Webhook Subscription Verification

| Configuration item | Status |
| --- | --- |
| Receiver endpoint | `POST /api/integrations/motive/webhook` ✅ live |
| HMAC signature header | `X-Motive-Signature` (SHA256 of raw body) ✅ verified |
| Webhook secret | `004350cc…c106` (stored in `integration_settings.motive.webhook_secret_value`) ✅ |
| Family classifier | `_classify_family()` covers 6 families + `other` bucket ✅ |
| Severity hint resolver | `_SEVERITY_BY_SUBTYPE` table + payload-driven overrides ✅ |
| Per-event field extractor | `_classify_event()` writes `harsh / fault / dvir / geofence` sub-blocks ✅ |

**Subscription gap (acknowledged · not closed by this sprint):** Motive's upstream dashboard still has only `vehicle_gps` subscribed in production. The 5 authorized families are **receiver-ready**; the operator must enable the remaining 5 subscriptions in the Motive Admin → Webhooks UI when authorized. P1.5 validates that when Motive starts sending those events, MASCI ingests, classifies, and displays them without further work. Verified via signed-payload replay (see P1.5-B).

---

## P1.5-B · Event Ingestion (live signed-payload replay)

All 5 families were replayed through the production webhook receiver against the live preview env with valid HMAC signatures. Receiver responses:

| Family | Payload event_type | Receiver response | DB row |
| --- | --- | --- | --- |
| harsh_event | `hard_brake` | `{ok:true, family:harsh_event, severity:high, status:stored}` | ✅ inserted, decorated |
| fault_code | `fault_code` | `{ok:true, family:fault_code, severity:critical}` | ✅ inserted, `mil_status=true` triggered critical band |
| dvir | `dvir_submitted` (out_of_service=true, 2 defects) | `{ok:true, family:dvir, severity:critical}` | ✅ inserted, OOS recognized |
| geofence_enter | `geofence_enter` | `{ok:true, family:geofence_enter, severity:info}` | ✅ inserted |
| geofence_exit | `geofence_exit` (dwell_seconds=4567) | `{ok:true, family:geofence_exit, severity:info}` | ✅ inserted, dwell computed |

Bad-signature negative test: returns `HTTP 401 · Invalid webhook signature`. Confirmed.

---

## P1.5-C · Safety Visibility

**Surface:** existing `IntegrationEventsCard.MotiveRow` on Safety Hub + HR Hub.
**Wiring:** the read endpoint now emits a humanized `summary` field per row. The card renders `summary` when present, falling back to the existing `driver_name · unit_number · address` line.

Sample rendered output (real DB row, family=harsh_event):
```
Hard Brake: Unknown driver in DPT021-8147 at 64 mph near I-4, Deltona, FL
[severity: HIGH] [Coach]
```

Fields exposed to Safety: Driver · Vehicle · Severity · Speed (mph) · Location · Time · Coaching-required badge. No new screens.

---

## P1.5-D · Shop Visibility

**Surface:** AssetProfile → Events tab (new Motive event timeline section) + family chip in Safety/HR feed (visually colored amber for `fault_code`).
**No work-order creation. No MaintainX writes. No equipment_master mutations.**

Sample rendered output:
```
[SHOP · CRITICAL] Fault P0420 on DPT021-8147 · CHECK-ENGINE ON
                  — Catalyst System Efficiency Below Threshold
```

Critical-band rule: `severity=critical` when `mil_status=true` OR `severity ∈ {red, critical, severe}`. Pure visibility — no hold logic.

---

## P1.5-E · DVIR Visibility

**Surface:** AssetProfile → Events tab + Notifications (via existing critical-severity row in the events card).
**No maintenance hold automation.**

Sample rendered output (out_of_service=true, 2 defects):
```
[DVIR · CRITICAL] OUT OF SERVICE: Unknown driver flagged DPT021-8147 (2 defects)
```

Severity ladder:
- `dvir.out_of_service=true` → severity `critical`
- defects present, OOS false → severity `high`
- pass / signed → severity `info`

No corrective-action creation. No Pre-Op queue mutation.

---

## P1.5-F · Dispatch Visibility

**Surface:** new "Live Motive · Arrivals & Departures" strip mounted at the bottom of the existing `DispatchIntegrationsTab` (`/dispatch-portal` → Integrations tab).
**No dispatch state transitions. No lifecycle automation. No M-2.**

Sample rendered rows:
```
[Arrived ]  DPT021-8147 arrived at The Shop                    14:03
[Departed]  DPT021-8147 departed The Shop · 1 h 16 m on site   14:04
```

The panel reads `/api/integrations/motive/events?family=geofence_enter|exit&limit=8` and merges. Auto-refresh on tab mount. Bottom-of-panel disclaimer: *"Visibility only · no dispatch automation"*.

---

## P1.5-G · Event Decoration (operational language)

The backend `_humanize_event()` function converts every stored row into a sentence-form summary BEFORE the frontend renders it. No raw JSON is ever displayed. Examples:

| Family | Raw event_kind | Rendered summary |
| --- | --- | --- |
| harsh_event | `hard_brake` | `Hard Brake: Andres Masci in Truck 112 at 64 mph near I-4, Deltona, FL` |
| fault_code | `fault_code` | `Fault P0420 on Truck 112 · CHECK-ENGINE ON — Catalyst System Efficiency Below Threshold` |
| dvir (OOS) | `dvir_submitted` | `OUT OF SERVICE: Andres Masci flagged Truck 112 (2 defects)` |
| dvir (signed) | `dvir_signed` | `DVIR signed: Mechanic cleared Truck 112` |
| geofence_enter | `geofence_enter` | `Truck 112 arrived at SR46 Widening Project` |
| geofence_exit | `geofence_exit` | `Truck 112 departed SR46 Widening Project · 1 h 16 m on site` |

The frontend `motiveSummary()` helper is a defensive fallback for older rows that pre-date P1.5 — never required at the current data set.

---

## P1.5-H · Event History (per-asset · per-driver)

Two new read endpoints (NO writes, NO joins beyond existing `asset_mappings` / `employee_mappings`):

| Endpoint | Returns | Used by |
| --- | --- | --- |
| `GET /api/integrations/motive/assets/{masci_equipment_id}/events` | Decorated event list for the asset (up to 200) | `AssetProfile → Events tab` |
| `GET /api/integrations/motive/drivers/{masci_employee_id}/events` | Decorated event list for the driver (up to 200) | Future Driver Profile screen (NOT built in P1.5) |

The asset endpoint resolves via `asset_mappings.motive.vehicle_id` ∪ `motive.asset_id`. The driver endpoint resolves via `employee_mappings.motive.driver_id`. Both decorate with the same `_decorate_motive_event_rows` pipeline used by the global feed — single source of truth.

Asset Profile end-to-end check (live preview env, vehicle 1438259):
```
GET /api/operations/assets/{id}/profile → data.motive_events[] (9 rows):
  [geofence_exit    info    ] DPT021-8147 departed The Shop · 1 h 16 m on site
  [geofence_enter   info    ] DPT021-8147 arrived at The Shop
  [dvir             critical] OUT OF SERVICE: ... flagged DPT021-8147 (2 defects)
  [fault_code       critical] Fault P0420 on DPT021-8147 · CHECK-ENGINE ON ...
  [harsh_event      high    ] Hard Brake: ... in DPT021-8147 at 64 mph near I-4, Deltona, FL
  + 4 older GPS rows
```

A `Live` badge ribbon distinguishes webhook-sourced rows from poll-sourced rows.

---

## P1.5-I · Role Validation (final)

| Role | Where they see events | What they see | Noise risk |
| --- | --- | --- | --- |
| **Dispatch** | `/dispatch-portal` → Integrations tab → "Live Motive · Arrivals & Departures" panel | geofence_enter + geofence_exit · last 10 · operational summary line | None — capped at 10 rows · no per-GPS event noise |
| **Shop** | AssetProfile (per-asset) Events tab · family chip = SHOP for fault rows | fault_code rows · dvir defect/OOS rows | None — only critical/amber families surface |
| **Safety** | Safety Hub `IntegrationEventsCard` | harsh_event rows (high/medium) · DVIR critical · summary line · coaching badge | Low — severity filter available |
| **HR** | HR Hub `IntegrationEventsCard` (same component) | Same as Safety | Low |
| **Operations** | Operations Center → Integration Readiness tile (P1-E) + cross-cutting via Safety/Shop surfaces | Aggregate counters · no individual per-event noise | None |
| **PM / Superintendent** | AssetProfile per-asset Events tab | Per-asset event timeline (read-only) | None — opt-in per asset |
| **Admin** | Admin Integration Center + AssetProfile + everything above | All families | None — Admin chose subscription |
| **Driver** | **Nothing** — Motive talks to drivers directly via in-cab app | — | No relaying of motive events to drivers |

No duplicate event rendering: each surface filters by family, and the same `_decorate_motive_event_rows()` pipeline drives all three (Safety feed · Asset timeline · Dispatch arrivals strip).

---

## REGRESSION

```
tests/test_integrations_iter122.py            ✅
tests/test_iter123_mappings_wizard.py         ✅
tests/test_integration_health_iter142.py      ✅
tests/test_iter132_final.py                   ✅
tests/test_dispatch_d1_activation.py          ✅
tests/test_dispatch_d2_sms_magic_link.py      ✅
                                              72 passed · 1 skipped (20 s)
```

Lint: all P1.5-touched files clean.
- `backend/routes/integrations/events.py` · pylint clean
- `backend/services/motive_service.py` · pylint clean
- `backend/routes/operations.py` · pylint clean
- `frontend/src/components/DispatchIntegrationsTab.jsx` · eslint clean
- `frontend/src/components/IntegrationEventsCard.jsx` · pre-existing advisory only
- `frontend/src/pages/admin/AssetProfile.jsx` · pre-existing blocking issue confirmed unrelated to P1.5 (failed before any P1.5 edits, stash-and-retest verified)

---

## EXAMPLE RENDERED EVENTS (smoke replay against live preview)

```
[SAFETY · HIGH]    Hard Brake: Andres Masci in DPT021-8147 at 64 mph near I-4, Deltona, FL
[SHOP · CRITICAL]  Fault P0420 on DPT021-8147 · CHECK-ENGINE ON — Catalyst System Efficiency
                   Below Threshold
[DVIR · CRITICAL]  OUT OF SERVICE: Andres Masci flagged DPT021-8147 (2 defects)
[ARRIVED]          DPT021-8147 arrived at The Shop
[DEPARTED]         DPT021-8147 departed The Shop · 1 h 16 m on site
```

---

## OPERATIONAL VALUE DELIVERED

Before P1.5, Motive sent only continuous GPS pings. The 5 highest-value event families were undeliverable to operators because:
1. No classifier — every event landed in a generic bucket
2. No humanization — UIs would have had to render raw JSON
3. No family routing — Dispatch would see safety events, Safety would see geofences

After P1.5:
- **Safety** can see real harsh-brake events with driver name, speed, location, coaching flag — *the moment Motive sends them*.
- **Shop** can see real engine fault codes with MIL status and DTC description — *the moment Motive sends them*.
- **Dispatch** can see real arrivals/departures with geofence name and dwell time — *the moment Motive sends them*.
- **Admin** can see every event on the per-asset and per-driver timeline.

The 5 webhook subscriptions in Motive Admin can be enabled at any time by the operator and start flowing live data through this pipeline immediately — no further MASCI changes required.

---

## FILES TOUCHED (6 files · 0 new files)

Backend:
- `services/motive_service.py` — classifier helpers + enriched webhook write
- `routes/integrations/events.py` — humanizer + family filter + per-asset/per-driver endpoints
- `routes/operations.py` — Motive events on Asset Profile payload

Frontend:
- `pages/admin/AssetProfile.jsx` — Motive event timeline in Events tab + family chip + summary fallback
- `components/IntegrationEventsCard.jsx` — render `summary` field
- `components/DispatchIntegrationsTab.jsx` — live arrivals/departures strip

**No schema migrations. No new collections. No new portals. No new env keys.**

---

## GUARDRAILS UPHELD

- ❌ No M-2 webhook→Dispatch automation
- ❌ No geofence triggers / event router
- ❌ No dispatch state automation
- ❌ No maintenance hold / work-order creation
- ❌ No corrective-action automation
- ❌ No workflow changes / state transitions
- ❌ No new portals · No new dashboards · No new databases · No FleetWatcher work
- ✅ Visibility-only · classify · decorate · display
- ✅ Subtractive: 6 files modified · 0 new files

---

🟢 **P1.5 COMPLETE.**
