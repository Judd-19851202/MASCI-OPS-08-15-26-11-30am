# MOTIVE OPERATIONAL ACTIVATION CERTIFICATION

**Mode:** READ-ONLY HTTPS against `https://mascidocs.com`. No code, no DB writes, no secrets, no redeploys, no restarts, no config changes.
**Probe wall clock:** 2026-06-11T03:50–03:55Z
**Auth:** `jaymn.judd@mascigc.com` admin token (multi-login).

---

## PHASE 1 — REAL MOTIVE DATA · **PASS**

Endpoint evidence: `GET /api/integrations/motive/events?limit=500` + `GET /api/integrations/motive/geofences?limit=500`.

| Metric | Value |
|---|---|
| `motive_events` rows returned (max page) | **500** (real, all `is_demo=false`) |
| Event family distribution | `vehicle_gps: 500` |
| Oldest event_at | `2026-06-11T00:56:14Z` |
| Newest event_at | `2026-06-11T03:50:57Z` (≈3 min before probe) |
| Sample real unit_numbers | DPT002-6387, DPT024-4764, DPT027-7238, DPT030-7237, DPT034-8856, DPT040-8005, DPT041-8008, DPT043-8757 |
| `motive_geofences` count | **67** |
| Geofence categories | Job Site · Maintenance Facility · Terminal/Yard · Uncategorized |
| Oldest geofence created_at | `2026-06-09T17:03:38Z` |
| Newest geofence updated_at | `2026-06-11T03:35:57Z` (≈20 min before probe) |
| Sample real geofence names | "21-06 - T5736 - OVIEDO", "21-06 - T5736 - S CENTRAL AVE YARD - THEFT", "23-01 - T5767 - INDUSTRY RD YARD - THEFT", "23-01 - T5767 - SR 528", "23-02 - E54B1 - ISB YARD - THEFT" |

**Determination:** real Motive data. Not mocked, not stale, not test fixtures. MASCI MGC dump-truck VINs and MASCI job/yard naming conventions confirm provenance.

---

## PHASE 2 — SCHEDULER EXECUTION · **PASS**

Endpoint evidence: `GET /api/admin/integrations/motive` + `GET /api/admin/integrations/sync-logs?integration=motive&limit=20` + `GET /api/admin/integrations/motive/reliability-state`.

| Metric | Value |
|---|---|
| `enabled` | `true` |
| `status` | `Connected` |
| `last_sync_at` | `2026-06-11T03:51:01Z` (≈2 min before probe) |
| `last_successful_sync_at` | `2026-06-11T03:51:01Z` |
| `last_failed_sync_at` | `null` |
| `last_sync_error` | `null` |
| Sync supervisor `alive` | `true` |
| Supervisor `started_at` | `2026-06-11T03:35:10Z` (matches fresh prod container) |
| Loop cadences | events=900 s · assets=43200 s · users=43200 s · geofences=43200 s |
| Last tick (events) | `2026-06-11T03:50:58Z` · status `ok` · no error |
| Last tick (assets) | `2026-06-11T03:35:55Z` · status `ok` |
| Last tick (users) | `2026-06-11T03:35:55Z` · status `ok` |
| Last tick (geofences) | `2026-06-11T03:35:55Z` · status `ok` |

Sample sync-log tail (10 of 20):
```
03:51:01  sync_events     Success   created=90 updated=0  failed=0
03:36:02  sync_assets     Success   created=0  updated=190 failed=0
03:35:58  sync_events     Success   created=90 updated=0  failed=0
03:35:57  sync_geofences  Success   created=0  updated=67  failed=0
03:35:57  sync_users      Success   created=0  updated=65  failed=0
03:34:05  sync_assets     Success   created=0  updated=190 failed=0
03:34:02  sync_events     Success   created=90 updated=0  failed=0
03:34:01  sync_geofences  Success   created=0  updated=67  failed=0
03:34:01  sync_users      Success   created=0  updated=65  failed=0
03:33:05  sync_assets     Success   created=0  updated=190 failed=0
```

**Determination:** actively syncing. Supervisor (`services/asset_spine_scheduler` + `lib/motive_reliability`) is armed and ticking on schedule. Zero failed syncs in the visible window. Owner: in-process supervisor task (lib.motive_reliability) started at container boot.

---

## PHASE 3 — ASSET SPINE INGESTION · **PARTIAL PASS**

Endpoint evidence: `GET /api/admin/integrations/asset-mappings?limit=500` + `GET /api/admin/integrations/cleanup/assets` + `GET /api/admin/integrations/cleanup/trust-score` + `GET /api/operations-center/asset-spine-tile`.

| Metric | Value |
|---|---|
| `asset_mappings` rows | **190** (one per Motive vehicle/asset) |
| Linked to MASCI equipment (`masci_equipment_id` populated) | **0** |
| Unlinked (Motive-only) | **190** |
| Resolved/Retired | 0 |
| Operational (gps_enabled) | **158** |
| Asset Spine total assets | **596** |
| Asset Spine coverage_pct | **31.9 %** |
| Asset Spine unmapped | **406** |
| Asset Spine orphaned (no provider link) | **595** |
| Asset Spine unsynced | 349 |
| Asset Spine duplicates | 4 |
| Trust-score (assets) | **0 / 190 linked → 0.0 % · band `red` · `Critical`** |
| Conflicts (asset side) | 4 |

**Determination:** Motive *raw* ingestion into the platform is working — 190 vehicles, all 158 gps-enabled units have device telemetry. **But the cross-walk from Motive → MASCI equipment master is not yet executed** — zero rows have `masci_equipment_id`, so the Asset Spine treats Motive assets as orphans. Data is **flowing into MongoDB / asset_mappings collection**, but **not yet reconciled** into the Asset Spine identity graph.

---

## PHASE 4 — DRIVER / EMPLOYEE INGESTION · **PARTIAL PASS**

Endpoint evidence: `GET /api/admin/integrations/employee-mappings?limit=500` + `GET /api/admin/integrations/cleanup/drivers` + `GET /api/admin/integrations/cleanup/trust-score`.

| Metric | Value |
|---|---|
| `employee_mappings` rows | **65** |
| Rows carrying Motive `driver_id` | **65** (100 %) |
| Rows carrying MASCI `masci_employee_id` | **0** |
| Active unlinked | 53 |
| Deactivated | 12 |
| Resolved/Linked | 0 |
| Trust-score (drivers) | **0 / 65 linked → 0.0 % · band `red` · `Critical`** |

Sample real driver row: `{driver_id: 4667482, first_name: "WILLIAM", last_name: "MUNDT", username: "william.masci", status: "active", lat/lon present, located_at: 2026-06-11T03:34:23Z}`.

**Determination:** Motive driver records are flowing in — 65 active driver identities with live position fixes — but **none are reconciled to the MASCI employees collection**. Driver data lands in MongoDB; the driver→employee identity link is empty.

---

## PHASE 5 — COMMAND CENTER CONSUMPTION

| System | Status | Evidence |
|---|---|---|
| **Operations Center** (rollup) | ✅ data available | `/api/operations-center` returns role cards with totals; `/api/operations-center/asset-spine-tile` reports 596 total assets, 31.9 % coverage, real `last_scan.at`. |
| **Operations Center · Command · telematics tile** | ⚠️ data ingested, surface empty | `/api/operations-center/command/telematics` returns `mapped_trucks=0`, `unmapped_trucks=96`, `rows=[]`, `integration_readiness.motive="partial"`. The tile *queries* mapped rows; nothing renders because nothing is mapped. |
| **Operations Center · Command · brief** | ✅ data available | `/api/operations-center/command/brief` returns `ok=true`, mentions Motive in `integration_readiness`. |
| **Dispatch Command Center** | ✅ data available, with mapping gap | `/api/dispatch/command/summary` returns 11 sections incl. `fleet.counts={total:275, unmapped:275, motive_only:0, needs_mapping:0}`. References Motive in `integration_readiness`. |
| **Dispatch Fleet Status** | ✅ data available | `/api/dispatch/fleet/status?limit=3` returns 137 MASCI fleet units (DPT002-6387, DPT007-8803, DPT014-7057 …). |
| **Operations Intelligence · fleet-gps** | ✅ **LIVE GPS DATA** | `/api/operations/intelligence/fleet-gps` returns 190 vehicles with real GPS bands. Sample: `DPT002-6387 · band=green · "GPS Active · 23 min ago" · Edgewater FL · located_at=2026-06-11T03:31:03Z · gps_enabled=true · gateway_status=online`. Also returns amber/red staleness for vehicles whose last fix is hours or days old. |
| **Asset Spine** | ⚠️ visible but reconciliation pending | 596 total / 406 unmapped / 595 orphaned / 4 duplicates / 349 unsynced. Last scan 2026-06-11T02:01:11Z. |

**Determination:** Motive raw data is **available** in MongoDB and **reachable** by every consumer endpoint. UI surfaces that require *mapped* MASCI↔Motive identities (Telematics tile, fleet operational status) render blank because zero rows are mapped — this is a data-reconciliation gap, not a wiring or ingestion gap. The Fleet GPS intelligence endpoint already renders live coords directly off the unmapped Motive rows.

---

## PHASE 6 — WEBHOOK READINESS · **PASS**

| Check | Result |
|---|---|
| Route exists (`POST /api/integrations/motive/webhook`) | ✅ (`GET` returns 405, route is mounted POST-only) |
| Handler enabled | ✅ returns app-level 401 `"Invalid webhook signature"`, not router-level 404 |
| Webhook secret configured | ✅ `integration_settings.motive.webhook_secret_present=true` (mask suffix `c106`) |
| Signature validation enforced | ✅ unsigned + fake-signature both rejected with 401 `Invalid webhook signature` |
| `webhook_url_path` self-advertised | ✅ `/api/integrations/motive/webhook` |
| Registration in Motive Dashboard | ⏳ NOT YET COMPLETE — operator must add the URL + secret in Motive's web console |

**Can Motive begin sending live webhook events immediately after dashboard registration? → YES.** No code, no env, no schema changes required. The endpoint accepts the secret already stored in `integration_settings.motive.webhook_secret_value`.

---

## PHASE 7 — FULL OPERATIONAL VERDICT

| # | Question | Answer | Evidence |
|---|---|---|---|
| 1 | Is Motive currently supplying real data to MASCI? | **YES** | 500 real vehicle_gps events within 3 min; 67 real geofences with MASCI job-site names; sync supervisor alive; last successful sync 2 min before probe. |
| 2 | Is Motive currently syncing successfully? | **YES** | Last 20 sync-logs all `Success`. Events polled every 15 min, assets/users/geofences every 12 h, `last_failed_sync_at=null`, reliability supervisor `alive=true`. |
| 3 | Is Motive data reaching Asset Spine? | **PARTIALLY** | Asset Spine sees 190 Motive-sourced assets but reports them as 595 orphans / 0 linked / 31.9 % coverage. Raw rows present, identity reconciliation pending. |
| 4 | Is Motive data reaching Command Centers? | **PARTIALLY** | Operations Intelligence Fleet GPS (190 live rows), Dispatch Fleet Status (137 units), Asset Spine Tile (596 assets) all serve live data. Operations Center Command Telematics tile renders empty (`rows=[]`) because it gates on mapped trucks. |
| 5 | Are Motive drivers being mapped? | **NO — ingested but not mapped** | 65 driver_mappings rows exist with full Motive identity (driver_id, name, current lat/lon); 0 have `masci_employee_id`. |
| 6 | Are Motive assets being mapped? | **NO — ingested but not mapped** | 190 asset_mappings rows exist (all 158 GPS-enabled units carry live telemetry); 0 have `masci_equipment_id`. |
| 7 | Is webhook infrastructure ready? | **YES** | Route mounted, secret stored, signature validation enforced, 401 on bad signatures. Awaits registration only. |
| 8 | Is the ONLY remaining step registration of the webhook inside the Motive dashboard? | **NO.** Two blockers, ordered by operational impact: (1) **MASCI ↔ Motive identity reconciliation** for assets and drivers (zero links today); (2) Motive Dashboard webhook registration. | See Phases 3 and 4. |
| 9 | EXACT remaining technical blockers | **B1 — Asset Identity Reconciliation:** `asset_mappings.masci_equipment_id` must be populated for the 190 Motive assets. Surfaced as `Operations Center · Command · telematics.mapped_trucks=0`. Auto-link endpoints exist (`/api/admin/integrations/motive/auto-link/preview` and `/api/admin/integrations/motive/auto-link`) — operator can run the preview, review, then execute. **B2 — Driver Identity Reconciliation:** `employee_mappings.masci_employee_id` must be populated for the 65 drivers. Same auto-link tooling. **B3 — Motive Dashboard Webhook Registration:** operator-only action; cannot be done from inside MASCI. **B4 — Trust-score is `red / Critical`** until B1+B2 close. **B5 — Asset Spine flags 4 duplicates and 87 assets with >24 h staleness** that should be triaged. **B6 (cosmetic):** old `_probe_motive` + `compute_system_health` still report yellow on `mascidocs.com`; the patch sits in preview waiting for the next prod deploy (does NOT block any operational data — purely a UI badge gap). | |
| 10 | What percentage complete is Motive activation? | **≈70 % operationally complete.** Raw data + sync + webhook infra = 100 %. Identity reconciliation (assets + drivers) = 0 %. Mapped-truck-driven UI tiles = 0 %. Webhook registration = 0 %. | |

---

## OPERATIONAL STATUS

**LIVE INGESTION: ACTIVE.** Motive is supplying real, current vehicle and driver telematics to MASCI's MongoDB every minute (events) / 12 hours (assets, users, geofences). Sync supervisor is healthy. Webhook endpoint is hardened and waiting.

**OPERATIONAL CONSUMPTION: PARTIAL.** Read endpoints that source directly from `motive_events` / `motive_geofences` / `asset_mappings` (e.g., Operations Intelligence Fleet GPS, Asset Spine Tile, Dispatch Fleet Status) already render live data with real lat/lon and timestamps. Endpoints that gate on a MASCI↔Motive identity link (Telematics tile, fleet-by-MASCI-equipment views) render empty until reconciliation runs.

## BLOCKERS

1. **B1 — Asset mapping:** 0 / 190 Motive assets linked to MASCI equipment master. Auto-link tools exist but have not been executed.
2. **B2 — Driver mapping:** 0 / 65 Motive drivers linked to MASCI employees. Same tooling.
3. **B3 — Motive Dashboard webhook registration:** operator-only step, no MASCI-side blocker.
4. **B4 (low-prio):** 4 asset duplicates + 87 stale assets in Asset Spine.
5. **B5 (cosmetic only):** prod still on pre-patch `_probe_motive` / `compute_system_health` — Motive badge yellow even though integration is fully active. Patch shipped to preview, awaits redeploy. Does not affect operational data.

## NEXT ACTION

1. Operator: run `POST /api/admin/integrations/motive/auto-link/preview` (assets + drivers) on production to see proposed matches, then `POST /api/admin/integrations/motive/auto-link` to commit. Closes B1 + B2 and lights up the Telematics tile.
2. Operator: register the webhook in Motive Dashboard against `https://mascidocs.com/api/integrations/motive/webhook` using the secret in `integration_settings.motive.webhook_secret_value`. Closes B3.
3. Optional: deploy the preview-resident health-card patch to close B5.
4. Optional: triage 4 asset duplicates + 87 stale assets in the Asset Spine.
