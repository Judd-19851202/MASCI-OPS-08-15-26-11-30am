# MASCI Production Reality Audit (Track 13.4D)

**Mode:** discovery + production-reality validation only · NO implementation · NO design.  
**Generated:** 2026-02 (Track 13.4D).  
**Primary objective:** close the *Proven* pillar gaps surfaced in Track 13.4C.

---

## 0. Environment honesty statement

This audit was executed against the **preview environment**
(`APP_ENV=preview`, `DB_NAME=masci_safety_preview`). The preview
environment is intentionally isolated from production. Therefore
this document distinguishes carefully between:

- **Verified in preview** — we observed the behaviour ourselves.
- **Implied** — preview state suggests production behaviour but
  cannot prove it.
- **Cannot verify here** — requires direct access to production
  logs / DB / webhook receivers.

The honest answer to "is Dispatch operationally trustworthy in
production?" is **unknown today** — and this document explains why.

---

## 1. Dispatch Data Integrity — what's known from preview

### 1.1 Motive ingestion baseline
| Metric (preview env) | Value |
|---|---|
| `motive_events` total documents | **466** |
| Oldest event | `2024-03-15T10:15:14Z` |
| Newest event | `2026-06-11T02:06:19Z` |
| Events in last 24h | **0** |
| Events in last 7 days | **383** |
| Unique vehicles posting in last 7d | **81** |
| `integration_sync_logs` total | 238 |
| `integration_error_logs` total | 3 |

Daily event counts (last 14 days, descending) in preview:
```
2026-06-11: 34       2026-06-04: 8
2026-06-10: 37       2026-06-03: 8
2026-06-09: 4        2026-06-02: 4
2026-06-08: 259      2026-06-01: 15
2026-06-07: 16       2026-05-29: 5
2026-06-06: 5
2026-06-05: 28
```

Activity is bursty — large spikes (259 on 2026-06-08) alongside near-silent days. Consistent with webhook backfill bursts rather than steady webhook delivery.

### 1.2 Asset mapping baseline
| Provider | Count in `asset_mappings` |
|---|---|
| `motive` | **190** |
| (no provider tag) | 1 |

### 1.3 Snapshot-level numbers (verified via `/api/operations-map/snapshot`)
| Metric | Value |
|---|---|
| `total` | 190 |
| `attention_required` (red band, stale_position) | 33 |
| `no_recent_position` (gray band) | 157 |
| `working` (green band) | 0 |
| `idle` (amber band) | 0 |
| `assigned` | 90 |
| Assets with GPS coords | 90 |
| Assets without GPS coords | 100 |
| Marker kinds | dump_truck × 31 · service_truck × 41 · pickup × 13 · water_truck × 5 |
| `feed_status` | `offline` |
| Geofences in `motive_geofences` | 67 |
| Geofences rendered (`_polygon_from_motive` polygon-only) | 0 |

---

## 2. Per-required-output classification

| Domain | Known | Verified | Unknown | Assumed | Unproven | Contradicted |
|---|---|---|---|---|---|---|
| **Production webhook activity** | webhook handler exists (`integrations/` route subdir, `resend_webhook.py`, motive sync service) | Cannot verify in preview | **Production arrival rate & cadence** | webhooks fire on `vehicle_locations.changed` and `idle.events` from Motive | unproven without production logs | — |
| **Production Motive ingestion** | sync service exists (`services/motive_service.py`, `sync_assets` in `integration_health.py`) | Preview has 466 events from 24-month span; preview environment is *not* the live receiver | Production ingestion success rate | platform-level env config drives webhook destination | unproven without production logs | — |
| **Production GPS coverage** | preview-snapshot ratio: 90/190 = 47 % with GPS | preview only | Production GPS coverage rate, "expected dark" triage list | preview ratio approximates production | — | not contradicted |
| **Production marker accuracy** | `marker_kind` is heuristically derived from equipment label in `operations_map_v1.py` | Preview marker counts known (§1.3) | Production marker_kind accuracy vs `equipment_master.type` ground truth | heuristic is "good enough" | unproven without per-unit audit | — |
| **Production asset counts** | snapshot returns counts and `operational_summary` | preview totals known (§1.3) | Independent rederivation of counts from raw collections | counts agree with raw data | unproven without redo | — |
| **Production fleet visibility** | DispatchMapHero renders 90 GPS-mapped assets in preview | verified in 13.4A | Production visibility of red/amber/green bands when fleet is live | bands fire correctly when GPS arrives | unproven (no green/amber observed in preview) | — |
| **Production feed health** | `feed_status` field set by snapshot logic | preview = `offline` because no events in last 24h | Production `feed_status` reaches `live` when ingestion is healthy | logic is correct | unproven without production traffic | — |
| **Production geofence status** | `motive_geofences` has 67 documents in preview | rendered count = 0 (`_polygon_from_motive` skips circles) | Production geofence count, circle/polygon split | proportions match preview | unproven | — |
| **Production map behaviour** | DispatchMapHero render fix verified in 13.4A | verified | Production map behaviour under live data load | matches preview | — | — |
| **Production operational summaries** | `operational_summary` returns by-band totals | preview counts known | Independent rederivation | counts are accurate | unproven | — |

---

## 3. Required production verification (cannot be performed from preview)

The following checks MUST be performed against production before
Dispatch can be declared operationally trustworthy. Each is a
specific, reproducible probe; none of them requires code changes.

1. **Webhook arrival rate** — sample `production_db.motive_events`
   over a 24-hour rolling window; expect ≥1 event per active vehicle
   per `vehicle_locations.changed` cadence (Motive default ≈
   5 minutes for moving units).
2. **`feed_status: live` confirmation** — query production
   `/api/operations-map/snapshot` and confirm `feed_status` returns
   `live` (not `delayed` / `offline`) when fleet is active.
3. **Per-unit GPS-coverage report** — for every row in
   `equipment_master.is_active=true`, classify as
   `gps_in_last_24h` / `gps_in_last_7d` / `gps_stale` / `never_gps`.
   Produce a triage list distinguishing "expected dark" (shop-stationary,
   non-telematics units) from "should be live".
4. **`marker_kind` ground-truth check** — for the production
   `asset_mappings.motive` set, compare `marker_kind` (heuristic)
   with `equipment_master.type` (curated). Flag mismatches.
5. **Independent operational_summary rederivation** — write a
   one-shot query that recomputes `total / attention / no_recent /
   working / idle / assigned` from raw collections and diff against
   `/snapshot`.
6. **Geofence rendering audit** — list all 67+ geofences in
   `motive_geofences`, classify as `polygon` vs `circle (center+radius)`,
   and confirm the rendered-count gap is purely the circle conversion
   gap.
7. **Webhook receiver health** — inspect Resend webhook log and the
   Motive webhook log for delivery failures, 4xx/5xx returns, and
   retry behaviour.

None of these steps is implemented in this audit — they are the
**production verification checklist** for Track 13.4D's eventual
production-side closure.

---

## 4. Trust verdict (today)

In **preview**: Dispatch renders truthfully, with the explicit caveat
that `feed_status: offline` is **accurate** because preview does not
receive live webhook traffic. The platform reports its uncertainty
honestly.

In **production**: trust **cannot be confirmed from this audit**.
Until §3 is executed against production, the *Proven* pillar gap
identified in Track 13.4C **remains open**.

---

## 5. Adjacent integrity findings (preview)

- **Sync log row with `provider=None`** — the most-recent
  `integration_sync_logs` document has empty `provider` and `kind`
  fields. Recording as preview-state observation; does not block
  audit.
- **3 entries in `integration_error_logs`** — sample inspection
  deferred to a maintenance task; not a Track 13.4D blocker.
- **81 unique vehicles posted in preview in the last 7d** — of the
  190 mapped, that is 42.6 % with recent activity. Provides a
  preview-level "GPS coverage in last 7d" baseline.

---

## 6. What this audit did NOT do

- Did not access production logs.
- Did not query the production database.
- Did not fix the geofence circle conversion (deferred per operator
  instruction).
- Did not modify any source.
- Did not propose a remediation plan; closure of the Proven gap is a
  production task, not a preview task.
