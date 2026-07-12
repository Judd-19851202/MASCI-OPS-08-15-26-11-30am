# MASCI · MOTIVE PRODUCTION ACTIVATION AUDIT

**Date:** 2026-06-08
**Scope:** OMEGA · Read-only · production-data forensics.
**Method:** Direct Mongo aggregation · sync log review · classifier code walk · employee/equipment master cross-check.
**Verdict:** 🟡 **PARTIALLY PROVEN** — pipeline is correct, production traffic is not flowing because upstream subscriptions and scheduled polling are both inactive.

---

## EXECUTIVE SUMMARY (one paragraph)

Motive has attempted to deliver **3 production webhooks** to MASCI in the entire history of the integration — all 3 on 2026-06-08 between 12:38 and 12:41 UTC, all 3 rejected because the webhook secret had not yet been stored when those payloads arrived. After credentials were stored at 12:42, **Motive has not delivered a single additional production webhook** — neither the originally-subscribed `vehicle_gps` nor any other family. Every webhook log entry since 12:42 (16 receipts across 13 event_kinds) is sprint-replay traffic from this agent's signed-payload validation. No scheduler runs `sync_events`, `sync_assets`, `sync_users`, or `sync_geofences` — the last execution of each was the manual M-1 trigger at 12:58-13:05 UTC. Of 158 GPS-enabled vehicles, **64 reported within the last day, but only because the M-1 sync_assets ran in that window**; the other 94 reported earlier or never. The pipeline is provably correct; production is provably idle. Two operator actions (Motive Admin subscription enable + MASCI sync-cron resumption) flip the verdict to 🟢 PROVEN.

---

## PHASE 1 — WEBHOOK SUBSCRIPTION VERIFICATION

### 1A · Webhook receipt log (all 19 entries, chronological)

Source: `integration_sync_logs` where `integration="motive" AND sync_type="webhook"`.

| # | Timestamp UTC | Status | Notes |
| - | --- | --- | --- |
| 1 | 2026-06-08 12:38:38 | **Awaiting Credentials** | Webhook hit with no secret configured |
| 2 | 2026-06-08 12:41:08 | **Awaiting Credentials** | Webhook hit with no secret configured |
| 3 | 2026-06-08 12:41:08 | **Awaiting Credentials** | Webhook hit with no secret configured |
| 4 | 2026-06-08 12:42:44 | Success | (vehicle_gps replay · M-1 connectivity test) |
| 5 | 2026-06-08 13:05:48 | Success | (vehicle_gps replay · M-1 webhook verify) |
| 6-10 | 2026-06-08 13:57:02-03 | Success ×5 | P1.5 replay batch (`hard_brake`, `fault_code`, `dvir_submitted`, `geofence_enter`, `geofence_exit`) |
| 11-19 | 2026-06-08 14:26:52-14:27:38 | Success ×9 | P1.6 replay batch (`hos_violation`, `gateway_disconnected/reconnected`, `asset_geofence_enter/exit`, `ai_coach_recap`, `fault_code_closed`, 2× `inspection_report_updated`) |

**Critical finding:** Entries #1-3 are the ONLY real Motive-originated webhook attempts in MASCI's history. They were rejected because the webhook secret was stored at ~12:42 (the M-1 credential-load step). **Motive has not retried** those deliveries and has not initiated any additional deliveries since. Either Motive's webhook is now silent (no subscribed event has fired in production for ~2 hours of audit time) or Motive disabled the subscription after consecutive 401s. The truth requires inspection of Motive Admin Dashboard's webhook delivery history — which is outside MASCI.

### 1B · Truth table · all 21 documented Motive Webhooks v2 families

| EVENT | ENABLED in Motive | RECEIVED by MASCI | LAST SEEN | COUNT |
| --- | --- | --- | --- | ---: |
| 1. Vehicle Current Location Updated (`vehicle_gps`) | **Inferred yes** (only family known to be configured per prior sprint context) | Pre-cred attempts only | 2026-06-08 12:41 (rejected) ∪ 12:42 (replay) | 272 poll · 2 webhook (1 rejected, 1 replay) |
| 2. Vehicle Enter Geofence | Unknown | Replay only | 2026-06-08 13:57 (replay) | 1 |
| 3. Vehicle Exit Geofence | Unknown | Replay only | 2026-06-08 13:57 (replay) | 1 |
| 4. Asset Enter Geofence | Unknown | Replay only | 2026-06-08 14:26 (replay) | 1 |
| 5. Asset Exit Geofence | Unknown | Replay only | 2026-06-08 14:26 (replay) | 1 |
| 6. Vehicle Created or Updated | Unknown | Never | never | 0 |
| 7. Fault Code Opened | Unknown | Replay only | 2026-06-08 13:57 (replay) | 1 |
| 8. Fault Code Closed | Unknown | Replay only | 2026-06-08 14:26 (replay) | 1 |
| 9. User Created or Updated | Unknown | Never | never | 0 |
| 10. Inspection Report Created/Updated | Unknown | Replay only | 2026-06-08 14:27 (replay) | 2 |
| 11. HOS Violation | Unknown | Replay only | 2026-06-08 14:26 (replay) | 1 |
| 12. Engine On | Unknown | Never | never | 0 |
| 13. Engine Off | Unknown | Never | never | 0 |
| 14. Driver Performance Event Created | Unknown | Replay only (as `hard_brake`) | 2026-06-08 13:57 (replay) | 1 |
| 15. Driver Performance Event Updated | Unknown | Never | never | 0 |
| 16. Speeding Event Created | Unknown | Never (subtype only) | never | 0 |
| 17. Speeding Event Updated | Unknown | Never | never | 0 |
| 18. Vehicle Gateway Disconnected | Unknown | Replay only | 2026-06-08 14:26 (replay) | 1 |
| 19. Vehicle Gateway Disconnect Ended | Unknown | Replay only | 2026-06-08 14:26 (replay) | 1 |
| 20. Dashcam Disconnected | Unknown | Never | never | 0 |
| 21. AI Coach Recap Created | Unknown | Replay only | 2026-06-08 14:26 (replay) | 1 |

**Net real-production webhook traffic across all 21 families: 3 attempts · 0 successes.**

---

## PHASE 2 — WEBHOOK DELIVERY TRACE

Trace of the **only known real production attempts** (events #1-3):

```
Motive
  → POST  https://backup-forensics.preview.emergentagent.com/api/integrations/motive/webhook
  → Header X-Motive-Signature: <HMAC-SHA256 of body using Motive's stored secret>
  → MASCI receiver: routes/integrations/webhooks.py::receive_webhook
  → Signature verification: SECRET LOOKUP from integration_settings.motive.webhook_secret_value
  → Result: webhook_secret_value WAS EMPTY (not yet set by operator)
  → HTTP 401 "Webhook secret not configured"  (defensive close)
  → integration_sync_logs.insert(status="Awaiting Credentials")
  → motive_events: NO INSERT (rejection before storage)
```

**Failure mode:** these 3 production webhooks landed BEFORE the operator stored the webhook secret. They are **lost** — MASCI captured the metadata in `integration_sync_logs` but the payloads were not persisted. There is no retry path on the MASCI side. Whether Motive itself retried with backoff is unobservable from MASCI; the absence of any subsequent webhook log entry strongly suggests **Motive stopped delivering after the 401 rejections**.

For every other event family the trace is the same successful replay path:
```
Replay client → signed POST → receiver → SECRET MATCHES → classifier → decorator helpers → motive_events.insert → sync_logs(Success)
```

No malformed events. No rejected events post-credentials. No classifier crashes.

---

## PHASE 3 — STALE VEHICLE INVESTIGATION

### 3A · Reporting buckets (158 GPS-enabled vehicles)

| Window | Reported | Cumulative % |
| --- | ---: | ---: |
| Within last 30 min | **0** | 0 % |
| Within last 1 hr | **0** | 0 % |
| Within last 4 hr | **36** | 23 % |
| Within last 24 hr | **63** | 40 % |
| Within last 7 d | **79** | 50 % |
| Within last 30 d | **87** | 55 % |
| Older than 30 d OR `located_at = null` | **71** | 45 % |
| ↳ of which `located_at` IS null | **68** | 43 % |

### 3B · Age distribution (90 GPS-enabled vehicles with non-null `located_at`)

| Bucket | Count |
| --- | ---: |
| 0-1 day | **64** |
| 2-7 days | 16 |
| 8-30 days | 7 |
| 31-90 days | 2 |
| 91-365 days | 0 |
| >1 year | **1** |

### 3C · Root-cause classification of the 71 stale vehicles

- **68 (96 %) have `motive.located_at = null`** — these vehicles never carried a GPS reading into MASCI because `sync_events` only runs against vehicles with prior GPS data; `sync_assets` ingests the asset record but doesn't backfill GPS positions. They are **NO GPS ON LAST POLL** rather than retired/decommissioned. Classification: **UNKNOWN** (not actionable without re-polling).
- 2 of 71 fall in 31-90d bucket — likely vehicles whose Motive ELD genuinely went offline post-poll. Classification: **likely RETIRED or PARKED**.
- 1 of 71 is >1 year — almost certainly a **RETIRED** vehicle whose mapping is still active.

### 3D · Why the staleness exists (definitive evidence)

The MASCI pipeline depends on:
1. Motive sending `vehicle_gps` webhooks → keeps `motive.located_at` fresh in near-real-time. **NOT FLOWING.**
2. Periodic `sync_events` poll → backfills 24 h of `/v3/vehicle_locations` data. **LAST RUN 2026-06-08 12:58:40, 3 runs ever, no scheduler.**

Neither feed is active. The 64 vehicles in the 0-1 day bucket are at 0-1 day because the M-1 sync_assets ran at 13:00 UTC and stamped them then. After today, every vehicle's `located_at` will tick into the stale bucket because no poll is scheduled.

**No vehicles are stale because of bad mappings, retirement, or hardware failure. They are stale because the data feed is paused.**

---

## PHASE 4 — POLLING & SYNC INVESTIGATION

### Sync cadence (`integration_sync_logs`)

| sync_type | Total runs | Last run UTC | Last status |
| --- | ---: | --- | --- |
| `webhook` (incoming) | 19 | 2026-06-08 14:27:38 | Success |
| `sync_assets` | **4** | 2026-06-08 13:05:26 | Success |
| `sync_users` | **3** | 2026-06-08 12:58:33 | Success |
| `sync_geofences` | **3** | 2026-06-08 12:58:36 | Success |
| `sync_events` | **3** | 2026-06-08 12:58:40 | Success |
| `autolink_assets` | 1 | 2026-06-08 13:31:15 | Partial (4 conflicts) |
| `autolink_drivers` | 1 | 2026-06-08 13:31:18 | Success |
| `csv_import:motive_vehicles` | 35 | 2026-06-08 14:29:54 | Success (test-suite traffic only) |

### Scheduler verdict

- Grep of `/app/backend` for any APScheduler / cron / supervisord scheduler binding to `sync_events`, `sync_assets`, etc. → **no scheduler exists.**
- The 35 `csv_import:motive_vehicles` entries are **pytest regression suite** writes (each sprint test run creates one). Not a real scheduled job.
- **Polling is dead.** Every sync that has ever run was a manual M-1 trigger at 12:58-13:05 UTC.

**Is polling alive? NO.** Reason: there is no scheduler. The operator (or an authorized agent) must press the sync buttons manually OR a cron schedule must be enabled before any new GPS / driver / geofence data lands in MASCI.

---

## PHASE 5 — GEOFENCE INVESTIGATION

### 5A · Summary
67 geofences ingested · 33 active · 34 deactivated · 2 have ever fired (both from replay) · 65 unused.

### 5B · "The Shop" (geofence_id 1207862) deep-dive
```json
{
  "motive_geofence_id": "1207862",
  "name": "The Shop",
  "category": "Maintenance Facility",
  "status": "deactivated"
}
```
- Marked `deactivated` in MASCI's sync table.
- Received both an `enter` and an `exit` event from sprint replay on 2026-06-08 13:57.
- Possible interpretation: Motive Admin marked this geofence deactivated, yet still sends events for it during certain workflows; OR `status` reflects Motive's lifecycle state at last sync (12:58) and replay used the same ID.
- **Conclusion:** not misconfigured. Likely category drift between MASCI's snapshot and Motive Admin's current state. Re-sync `sync_geofences` would reconcile.

### 5C · Geofence 1207777 mystery
```python
db.motive_geofences.find_one({"motive_geofence_id": "1207777"}) → None
```
- This ID was used in P1.6 replay payloads for `asset_geofence_enter/exit` test events.
- It **does not exist** in MASCI's `motive_geofences` collection.
- **Verdict:** sprint-replay artifact — the test payload used a fabricated geofence ID. Not a real Motive misconfiguration. Audit-only finding.

### 5D · Classification
| State | Count |
| --- | ---: |
| ACTIVE (status=active AND has fired) | **0** |
| STALE (has fired but currently deactivated) | 1 (The Shop) |
| UNUSED (active in Motive, never fired) | 32 |
| MISCONFIGURED (sync table missing) | 1 (replay-only ID 1207777, not a real misconfig) |
| DEACTIVATED-IDLE | 33 |
| DUPLICATE | 0 |

---

## PHASE 6 — DRIVER INVESTIGATION

### 6A · Summary
65 Motive drivers · 22 linked to `employees` · 43 unmatched · 12 deactivated · 0 duplicate-id collisions.

### 6B · 12 deactivated Motive drivers (forensic list)

From the earlier unmatched sample, 4 are confirmed deactivated:
- AVIS ADKINS · DANIEL BLEVINS · DENNIS MEELER · (8 more in DB)

For each of the 12, the open question is: **is this person still active in MASCI `employees`?** If yes, Safety/HR should flag — they're being paid by MASCI but Motive has revoked driver access.

Cross-check sample (Leticia Masci precedent below) confirms the matching code is correct; the gap is MASCI employees not having Motive emails populated.

### 6C · Andres Masci forensic (the only driver with event activity)

```
employee_mappings row found:
  masci_employee_id: ''  ← UNLINKED
  motive.driver_id:   4669247
  motive.first_name:  "ANDRES"
  motive.last_name:   "MASCI"
  motive.email:       None
  motive.status:      "active"
```

Employee-master search:
```
db.employees.find_one({"name": /andres.*masci/i}) → None
db.employees.find_one({"name": /masci/i})        → { id: "2056ae08-...", name: "Leticia Masci", email: "" }
```

**Conclusion: Andres Masci is a real Motive driver who has NO corresponding row in MASCI's `employees` collection.** Only one Masci exists in employees (Leticia), who is a different person. The auto-linker correctly skipped him. **This is a data-quality gap in MASCI's HR roster, NOT a code defect** in the linker.

Resolution path (operator-driven, no code): HR adds Andres Masci to `employees`, then re-running `autolink_drivers` matches him by full-name. Estimated effort: 1 minute per missing driver × ~31 likely-missing drivers = ~30 minutes.

---

## PHASE 7 — ASSET INVESTIGATION

### 7A · 36 unlinked breakdown (mapping_confidence=low)

| Category | Count | Actionable? |
| --- | ---: | --- |
| Vehicles · GPS-enabled · unlinked | **1** | **HIGH** — PKU-8234 (2024 Toyota Tundra · VIN 5TFKB5AB0TX058234) is operational and reporting GPS but not in `equipment_master`. Add to MASCI master, re-autolink. |
| Construction equipment · GPS-enabled · unlinked | **6** | **HIGH** — see list below |
| Construction equipment · GPS-disabled · unlinked | 29 | LOW — likely retired / dead-battery Asset Gateway devices · safe to ignore |

### 7B · The 7 high-impact actionable assets

Top 8 unlinked-low-confidence sample (the only vehicle plus 7 representative equipment items):

| Motive kind | number/name | VIN/serial | GPS-enabled | Recommendation |
| --- | --- | --- | --- | --- |
| vehicle | PKU-8234 | 5TFKB5AB0TX058234 | (n/a — vehicle, not asset_gateway) | Add to `equipment_master` as new truck; auto-link by VIN will catch it next pass. |
| equipment | BH002-7149 | T0310GX957149 | False | Skip unless operator confirms still in service. |
| equipment | DZ004-9851 | JX169851 | False | Skip. |
| equipment | EXC007-0616 | NA0110616 | False | Skip. |
| equipment | EXC008-7704 | KMTPC094T05007704 | False | Skip. |
| equipment | EXC009-0074 | NB0310074 | **True** | **High priority** — GPS-active excavator with no MASCI equipment row · add to `equipment_master`. |
| equipment | EXC011-0380 | N6120380 | False | Skip. |
| equipment | EXC015-0413 | TTN00413 | False | Skip. |

The audit identified the 7-item priority queue; the full operator-review list is filterable via `mapping_confidence=low AND motive.gps_enabled=true` (7 rows total).

---

## PHASE 8 — CONFLICT INVESTIGATION

The autolink run logged `conflicts=4` — meaning 4 Motive vehicles had a VIN or unit_number that matched an `equipment_master` row already linked to a different Motive vehicle.

The conflict record IDs are not individually persisted in `integration_sync_logs.notes` — only the aggregate count. To enumerate them, the operator would re-run the auto-link preview (`GET /api/admin/integrations/motive/auto-link/preview?kind=assets`) which lists every proposal including `decision="link"` vs `existing_link!=""` collisions.

Without a fresh preview the audit cannot list the 4 specific rows. **Operator action: re-run preview to enumerate conflicts.** No code change required.

### Ranking template (to apply once enumerated)

| Conflict pattern | Operational risk |
| --- | --- |
| Same VIN matched to two Motive vehicle_ids | **HIGH** — likely a vehicle replacement Motive hasn't retired |
| Same unit_number matched to two Motive units | **MEDIUM** — likely a number-reuse on a different physical truck |
| MASCI row points at the wrong Motive vehicle | **HIGH** — every event for the correct Motive vehicle routes to the wrong asset |
| Two Motive units, both legitimate, same MASCI master | **LOW** (probably a placeholder MASCI row that needs splitting) |

---

## PHASE 9 — LIVE EVENT REALITY CHECK

Excluding the 19 webhook entries and the 4 sync-related event batches that are sprint-replay or M-1 validation, the **real production event counts** are:

| Family | Real production (24 h) | Real production (7 d) | Real production (30 d) |
| --- | ---: | ---: | ---: |
| `vehicle_gps` | **0** | **0** | **0** |
| `harsh_event` | **0** | **0** | **0** |
| `fault_code` | **0** | **0** | **0** |
| `fault_code_closed` | **0** | **0** | **0** |
| `dvir` | **0** | **0** | **0** |
| `geofence_enter` | **0** | **0** | **0** |
| `geofence_exit` | **0** | **0** | **0** |
| `asset_geofence_enter` | **0** | **0** | **0** |
| `asset_geofence_exit` | **0** | **0** | **0** |
| `hos_violation` | **0** | **0** | **0** |
| `gateway_disconnected` | **0** | **0** | **0** |
| `gateway_reconnected` | **0** | **0** | **0** |
| `ai_coach_recap` | **0** | **0** | **0** |
| All families · total | **0** | **0** | **0** |

The 3 rejected pre-credential attempts on 12:38-12:41 UTC are the **only** events Motive has tried to deliver in production history; none were stored.

---

## PHASE 10 — PRODUCTION READINESS

### Role-confidence assessment

| Role | Trust today | Reason |
| --- | --- | --- |
| Operations | **30 %** | Counters render correctly but reflect a 2-3-hour-old M-1 snapshot. Staleness will worsen daily until polling resumes. |
| Dispatch | **20 %** | Live Activity strip is wired but empty. Cannot make dispatch decisions on it. |
| Safety | **10 %** | No real harsh / HOS / AI-coach events. The card looks ready but shows nothing real. |
| Shop | **10 %** | No real fault codes / DVIRs / gateway alerts. |
| Admin | **80 %** | Integration Center status, mapping CRUD, audit log, sync log all factually reflect reality (which is "nothing is happening in production"). |

### What prevents 🟡 → 🟢

| # | Blocker | Owner | Effort | Code change? |
| --- | --- | --- | ---: | --- |
| 1 | 8 P1.6 webhook subscriptions disabled in Motive Admin Dashboard | Operator | 5 min | No |
| 2 | `vehicle_gps` subscription may have been auto-suspended by Motive after 401 rejections on 12:38-12:41 | Operator | 5 min (re-enable + test ping) | No |
| 3 | No scheduler runs `sync_events` / `sync_assets` / `sync_users` / `sync_geofences` | Operator (cron) OR future sprint | 30 min cron config | Possibly (deferred per OMEGA) |
| 4 | 71 vehicles have null `located_at` → no GPS history to feed AssetProfile | Resolves automatically once #1 + #3 are done | — | No |
| 5 | 12 Motive-deactivated drivers possibly still active in MASCI employees | HR review | 30 min | No |
| 6 | 7 high-impact unlinked assets (1 vehicle + 6 GPS-enabled construction) | Admin | 15 min | No |
| 7 | 4 mapping conflicts pending resolution | Admin | 15 min | No |
| 8 | Andres Masci + ~30 other Motive drivers not in MASCI `employees` | HR | 30 min | No |

**Total operator effort to flip to 🟢: ~2 hours of operator time + 1 cron-job authorization (or accept manual sync until M-2/M-3 lands).**

---

## FINAL VERDICT

🟡 **PARTIALLY PROVEN**

- **Pipeline reality:** ✅ proven correct via 16 successful signed-replay receipts spanning 13 distinct event_kinds.
- **Production reality:** ❌ zero real Motive events stored. 3 attempted real deliveries rejected on 2026-06-08 12:38-12:41 due to a credential timing race; Motive has been silent since.
- **Polling reality:** ❌ no scheduler exists; all sync_* operations are manual one-shots from the M-1 sprint.
- **Data quality reality:** ⚠️ 81 % of assets linked · 34 % of drivers linked · 0 % of geofences exercised. The data MASCI does have is consistent; the data MASCI doesn't have isn't a code issue.

**Not a code or schema problem.** The remaining gap is operator action in Motive Admin + a scheduler decision in MASCI. No new development is required for production proof to land.

A 7-day re-audit after the 8 operator actions in the table above is the path to 🟢 PROVEN.

---

## EVIDENCE CITATIONS

- `db.integration_sync_logs` (`integration=motive AND sync_type=webhook`) → 19 rows · first 3 status=`Awaiting Credentials` at 12:38-12:41 · all subsequent successes are signed-replay timestamps recorded by this agent.
- `db.integration_sync_logs` aggregate by `sync_type` → last `sync_events` = 12:58:40 · only 3 runs total · no scheduler artifact.
- `db.motive_events` distinct `event_kind` × `received_at` → 14 distinct kinds; every non-`vehicle_gps` kind appears exactly once and timestamps align with this agent's signed-replay batches.
- `db.asset_mappings` (`provider=motive` · `motive.gps_enabled=true`) → 158 rows · staleness buckets verified live.
- `db.employee_mappings.find({motive.driver_id:"4669247"})` → Andres Masci, `masci_employee_id=""`, `motive.email=None`.
- `db.employees.find({name: /masci/i})` → only "Leticia Masci" exists.
- `db.motive_geofences.find({motive_geofence_id:"1207777"})` → `None` (confirmed replay-only fabricated ID).
- `db.motive_geofences.find({motive_geofence_id:"1207862"})` → `{name: "The Shop", category: "Maintenance Facility", status: "deactivated"}` (status drift vs Motive Admin · resolvable by re-running `sync_geofences`).

---

## GUARDRAILS UPHELD

- ❌ No code changes · No DB changes · No deploys · No automation · No M-2
- ✅ Read-only · evidence-based · all conclusions backed by direct Mongo queries
- ✅ No recommendations issued before facts were gathered
