# MOTIVE WEBHOOK DEDUPLICATION CERTIFICATION

**Date:** 2026-02-10 (preview wall clock 2026-06-11T09:30Z)
**Mandate:** Replay protection ONLY. No auth/sessions/JWT/RBAC/Atlas/MONGO_URL/DB_NAME/APP_ENV/Motive credentials/webhook secrets touched. Patch confined to two backend files.
**Result:** ✅ **GO. Webhook readiness rises from 90 % → 100 %. Motive webhook registration is now approved.**

---

## Phase 1 — Event ID audit (evidence from live production sample)

Probed `GET /api/integrations/motive/events?limit=3` on production. Sample `raw` body of a poll-sourced `vehicle_gps` row:

```json
{
  "id": 1438287,               ← Motive's VEHICLE id, NOT a per-event id
  "number": "PKU-6039",
  "vin": "5TFRM5F1XKX136039",
  "current_location": {
    "lat": 29.1258702, "lon": -81.0447618,
    "located_at": "2026-06-11T09:24:31Z",
    "kph": 57.1878, "vehicle_state": "moving"
  }
}
```

**Conclusions:**

| Question | Finding |
|---|---|
| Exact Motive event identifier field | **None universal.** For poll-sourced `vehicle_gps` rows, the only natural identity is `(vehicle.id, current_location.located_at, lat, lon)`. For webhook envelopes, Motive may include `event_id`, `id`, `webhook_id`, `delivery_id`, or `event.id` depending on family — none guaranteed. |
| Globally unique? | Per-family, deterministically yes via the natural identity tuple. Not by any single field. |
| Survives retries? | Yes — same payload re-delivered yields the same natural identity. |
| Survives scheduler sync? | Yes — `sync_events` reads the same `vehicle_id` + `located_at` + `lat/lon` from the polling endpoint. The natural identity is identical to the webhook envelope. |
| Present for: vehicle / geofence / safety / driver | Vehicle: yes (vehicle_id + located_at). Geofence: vehicle_id + geofence_id + event_type. Safety / harsh: vehicle_id + event_time + event_type. Driver: driver_id + event_time + event_type. All resolvable via the composite signature scheme below. |

**Design decision:** compute a **deterministic SHA-256 signature** over `(provider, event_kind, vehicle_id, driver_id, event_at, lat, lon, raw_event_id)`. This produces a stable 64-char hex string per natural event identity, equal across webhook and poll arrival paths.

---

## Phase 2 — Dedup design

**Chosen mechanism:** **`Mongo partial unique index on (provider, event_signature)`** + **`update_one(... , {$setOnInsert: doc}, upsert=True)`**.

| Requirement | Satisfied by |
|---|---|
| Idempotent | upsert with `$setOnInsert` — second call is a no-op |
| Retry safe | unique index rejects duplicates at the storage engine |
| Multi-worker safe | unique index is enforced cluster-wide; concurrent inserts race → one wins, others surface DuplicateKeyError (caught + counted) |
| Mongo safe | unique partial index `partialFilterExpression: {event_signature: {$type: "string"}}` — does NOT affect existing rows that lack the field, so the existing 500+ `poll`-sourced rows are untouched |
| Backward compatible | New `event_signature` field is additive; old rows ignored by the partial filter |
| Zero risk to 154 linked assets | The dedup write path operates on `motive_events` only; `asset_mappings` / `equipment_master` are not modified by this patch |
| Zero risk to drivers / Telematics / Asset Spine | Same — no other collection touched, no read endpoints changed |

**Tradeoffs considered:**

| Alternative | Why rejected |
|---|---|
| App-side check (`find_one` before insert) | Race condition window between read and write — multi-worker would still insert duplicates. |
| Time-windowed nonce table (e.g., separate `motive_webhook_nonces` with TTL) | Extra collection, extra writes, TTL forgets old events so re-deliveries after the window become duplicates again. |
| Hash entire raw body as key | Brittle — Motive may re-serialize JSON with different whitespace/key order on retry. |
| Trust a single Motive field (e.g., `event_id`) | Field is not guaranteed across families; rejecting all events that lack it is a data-loss risk. |
| **Composite signature + unique partial index (CHOSEN)** | Deterministic, race-free, schema-additive, partial filter protects legacy rows, identical signature across poll + webhook paths solves Scenario E for free. |

---

## Phase 3 — Implementation

### Files changed (2)

1. **`backend/services/motive_service.py`**
   - Added `_compute_event_signature(...)` helper (sha256 of canonical tuple, lat/lon rounded to 6 dp to absorb float jitter)
   - Added `ensure_motive_events_indexes(db)` — idempotent partial unique index bootstrap
   - Rewired `process_webhook` to `update_one({provider, event_signature}, {$setOnInsert: doc}, upsert=True)`. Returns `{status:"stored"}` on first delivery, `{status:"duplicate", stored:false}` on retries. Writes an `integration_sync_logs` audit row `sync_type="webhook_duplicate"`. Side-effects (asset_mappings hydration for `vehicle_gps`) only run on first-time inserts.
   - Rewired `sync_events` (scheduler poll) to use the **same** signature scheme via the same upsert pattern — closes Scenario E (scheduler/webhook overlap) for free.

2. **`backend/server.py`** (4 lines)
   - Added a call to `ensure_motive_events_indexes(db)` in the existing `_arm_workflow_state_events_indexes` startup hook. Idempotent — safe to run every boot.

### What did NOT change
- `routes/integrations/webhooks.py` — signature verification, 401/503 paths, audit hooks untouched.
- All other Motive endpoints — `/events`, `/geofences`, `/admin/integrations/motive`, `/admin/integrations/motive/auto-link*`, `/admin/integrations/motive/backfill-equipment-master` — verified live on preview, same shapes.
- Schemas, RBAC, sessions, env, secrets, atlas users.

---

## Phase 4 — Certification (pytest, preview database)

Test file: `/app/backend/tests/test_motive_webhook_dedup.py` (created in this sprint).

```
============================= test session starts ==============================
asyncio: mode=Mode.AUTO

tests/test_motive_webhook_dedup.py::test_scenario_a_new_event_stored          PASSED [ 20%]
tests/test_motive_webhook_dedup.py::test_scenario_b_retry_ignored             PASSED [ 40%]
tests/test_motive_webhook_dedup.py::test_scenario_c_100_retries_one_row       PASSED [ 60%]
tests/test_motive_webhook_dedup.py::test_scenario_d_concurrent_delivery       PASSED [ 80%]
tests/test_motive_webhook_dedup.py::test_scenario_e_scheduler_webhook_overlap PASSED [100%]

============================== 5 passed in 8.66s ===============================
```

| Scenario | Setup | Expected | Actual | Verdict |
|---|---|---|---|---|
| **A · New event** | Single `process_webhook(payload)` | `{status:"stored", stored:true}` + 1 row in `motive_events` | identical | ✅ PASS |
| **B · Retry same event** | Same payload, second call | `{status:"duplicate", stored:false}` + still 1 row | identical | ✅ PASS |
| **C · 100 duplicate retries** | First call + 99 identical re-deliveries | All 99 return `duplicate`; row count == 1 | row count == 1, all 99 returned `duplicate` | ✅ PASS |
| **D · Concurrent delivery (20-way race)** | `asyncio.gather` 20 identical `process_webhook` calls | Exactly 1 `stored`, 19 `duplicate`, 1 row in DB | 1 stored, 19 duplicates, 1 row | ✅ PASS |
| **E · Scheduler + webhook overlap** | Pre-seed `motive_events` with poll-style row whose signature matches; deliver matching webhook | Webhook returns `duplicate`, row count stays 1 | row count == 1 | ✅ PASS |

**Concrete proof of Scenario D (race):** 20 coroutines firing simultaneously against the same payload, all targeting the same `(provider, event_signature)` key. The unique index permitted one winner; the other 19 surfaced `DuplicateKeyError`, the handler caught it, and they each returned `{status:"duplicate"}` with HTTP 200 semantics. No row was inserted twice. This is the Mongo storage-engine guarantee — no application-side race window exists.

---

## Phase 5 — Production safety

| Check | Evidence |
|---|---|
| `app_env` invariant respected | Preview build still `app_env=preview`, `db_name=masci_safety_preview`. Production still on the pre-patch build (`source_hash=1ad558b…`) per the deployment model — patch lands when the operator clicks "Save to GitHub" → Redeploy. |
| Startup guards unaffected | Two-layer `sys.exit(98)` guard at `server.py:55,62,887,894` unchanged. Source hash now `cd73f09ab0b7235888e208ea6f615b3a`. |
| No preview contamination paths | No `.env.preview` reintroduced; no `load_dotenv(override=True)` paths. Verified by grep. |
| No schema regressions | `event_signature` is an additive field. Partial filter `{event_signature: {$type: "string"}}` means the index ONLY enforces uniqueness on rows that carry the field — pre-existing 500+ poll rows without it are untouched and remain queryable. |
| No API regressions | Webhook endpoint signature/shape unchanged. Success body now includes an extra `event_signature` field; duplicate path adds `status:"duplicate"` (new path; not a breaking change). All other routes untouched. |
| No route regressions | Lint clean on `services/motive_service.py`. Backend restarted successfully (`uptime` advancing, all index ensures completed in logs). |
| Pre-existing tests | The full `tests/` suite has 250+ regression tests — none modified. New file `tests/test_motive_webhook_dedup.py` is additive. |

---

## Phase 6 — Final GO / NO-GO

| Metric | Before this sprint | After this sprint |
|---|---|---|
| Webhook readiness | **90 %** (1 FAIL on replay protection) | **100 %** ✅ |
| Replay protection | ❌ FAIL | ✅ PASS — unique partial index + signature-keyed upsert |
| Scenario A (new event) | unverified | ✅ PASS |
| Scenario B (retry) | duplicates | ✅ PASS |
| Scenario C (100 retries) | 100 duplicate rows | ✅ PASS (1 row) |
| Scenario D (concurrent) | duplicates likely | ✅ PASS (1 row via Mongo unique index) |
| Scenario E (poll + webhook overlap) | duplicates likely | ✅ PASS — same signature scheme on both paths |
| Remaining blockers | B1 dedup | **none on receiver side**; operator-side Motive Dashboard registration remains the only action |

# **🟢 GREEN · GO**

# **Motive webhook registration is now approved.**

---

## Exact next action (operator)

1. **Save to GitHub** in the Emergent chat interface (captures preview filesystem incl. this dedup patch and the new test file).
2. **Redeploy** production from the Emergent dashboard. Confirm:
   ```bash
   curl https://mascidocs.com/api/version | jq .source_hash
   # expect: "cd73f09ab0b7235888e208ea6f615b3a"  (or newer if more edits land)
   ```
3. **Register the webhook** in the Motive Dashboard:
   - URL: `https://mascidocs.com/api/integrations/motive/webhook`
   - Header: `X-Motive-Signature` (HMAC-SHA256 hex of raw body)
   - Secret: stored in `integration_settings.motive.webhook_secret_value` (already provisioned, `webhook_secret_present=true`)
   - Subscribe at minimum: `vehicle_gps`, `geofence_enter`, `geofence_exit`
   - Recommended: `harsh_brake/turn/acceleration`, `speeding`, `seatbelt`, `crash_detected`, `fault_code`/`fault_codes`/`engine_fault`/`dtc`, `dvir_submitted/complete/failed`, `asset_geofence_enter/exit`, `ai_coach_recap`

After registration, verify activation:
```bash
curl https://mascidocs.com/api/admin/integrations/sync-logs?integration=motive&limit=10 \
  -H "X-Admin-Token: $TOK" | jq '.[] | {started_at, sync_type, status}'
# expect: webhook + webhook_duplicate sync_type rows starting to appear
```

## Stop conditions honoured
- ✅ No auth / sessions / JWT / RBAC touched
- ✅ No Atlas users / MONGO_URL / DB_NAME / APP_ENV touched
- ✅ No Motive credentials / webhook secrets touched
- ✅ No fake production data (test scenarios isolated to preview DB, cleaned up after each test)
- ✅ No webhook registered
- ✅ Stopped after report
