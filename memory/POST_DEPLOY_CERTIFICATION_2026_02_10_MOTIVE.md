# POST-DEPLOY CERTIFICATION + MOTIVE ACTIVATION CLOSEOUT

**Date (probe wall clock):** 2026-06-11T03:38Z
**Target:** https://mascidocs.com (production)
**Operator:** Jaymn Judd (jaymn.judd@mascigc.com — super admin)
**Mode:** READ-ONLY. No writes, no redeploy, no secret/Atlas/Motive-dashboard changes.
**Verdict:** **PARTIAL PASS** — production identity + Motive integration are PROVEN ACTIVE; three System-Health surfaces still mis-report Motive as `mocked / stubbed / yellow` because they read `os.environ["MOTIVE_API_KEY"]` only and ignore the DB-stored `integration_settings.motive.api_key_value` (where the prod key actually lives).

---

## Phase 1 — Production identity (GET /api/version) ✅ PASS

```
service        : masci-hub
app_env        : production            ✅
db_name        : masci_safety          ✅
source_hash    : 10ed6fc98616f7490e533b6556448fc4   ✅ matches expected
release        : 10ed6fc98616f7490e533b6556448fc4
started_at     : 2026-06-11T03:32:22Z  (≈ 5 min before probe — fresh container)
uptime_s       : 317
sentry.enabled : true
```

Startup consistency guard fired without `sys.exit(98)` → no env-vs-DB mismatch.

---

## Phase 2 — Motive live data on production ✅ PASS

| Endpoint                                       | HTTP | Evidence                                                                                 |
|------------------------------------------------|------|------------------------------------------------------------------------------------------|
| `GET /api/integrations/motive/events?limit=5`  | 200  | Real GPS pings (vehicles DPT049-5978 / DPT050-5974 — Mack Granite 2025) at I-95 Titusville FL and Old Mission Rd Edgewater FL, `event_at=2026-06-11T03:35:53Z` (≈2 min before probe). |
| `GET /api/integrations/motive/geofences?limit=5` | 200 | Real Motive geofence rows incl. `21-06 - T5736 - OVIEDO` (Job Site category), `updated_at=2026-06-11T03:35:55Z`. |
| `GET /api/admin/integrations/motive`           | 200  | `enabled=true`, `demo_mode=false`, `api_key_present=true`, `webhook_secret_present=true`, `webhook_url_path=/api/integrations/motive/webhook`, `last_successful_sync_at=2026-06-11T03:36:02Z`, `last_failed_sync_at=null`. Notes: `MOTIVE-PROD-INCIDENT-001: production credential restoration … See /app/memory/MOTIVE_PROD_INCIDENT_001_REMEDIATION_REPORT.md`. |

**Motive integration is unambiguously live on production:** the credentials are present, sync ran ~90 s before the probe, and data is flowing into both `motive_events` and `motive_geofences`.

---

## Phase 3 — System Health card (`GET /api/admin/integrations/health`) ❌ FAIL (misreports)

```
overall_status : ok
probes:
  mongo        : ok      Ping OK (2267ms)
  r2           : ok      Bucket `masci-hub` reachable
  resend       : ok      Key present · auto-email ON
  emergent_llm : ok      Key present (universal)
  maintainx    : disabled   "MOCKED — live API not configured"   (intentional)
  motive       : disabled   "MOCKED — MOTIVE_API_KEY not set"    ❌ INCORRECT
```

**Root cause (preview code, lines 137-141 of `/app/backend/routes/integration_health.py`):**

```python
api_key = os.environ.get("MOTIVE_API_KEY", "").strip()
if not api_key:
    return _result("motive", "Motive (Telematics)", "disabled", 0,
                   "MOCKED — MOTIVE_API_KEY not set", mocked=True)
```

The probe reads **only** the env var. In production the key was restored into the DB (see `MOTIVE_PROD_INCIDENT_001`), not into the deploy env. The polling service correctly falls back to both sources (`services/motive_service.py:55-56`), which is why data flows; the probe never got that fallback, so the card stays yellow/mocked.

---

## Phase 4 — `GET /api/platform/data-truth` ⚠️ PARTIAL

| Field                | Value             | Verdict |
|----------------------|-------------------|---------|
| environment          | production        | ✅ |
| data_source          | mongodb           | ✅ |
| database             | masci_safety      | ✅ |
| verified             | true              | ✅ |
| ui_banner.visible    | false             | ✅ (production hides banner) |
| integrations.motive.configured | **false** | ❌ (same env-var-only bug, lines 84-88 of `routes/platform_data_truth.py`) |
| integrations.motive.active     | **false** | ❌ comment says "MASCI activates Motive externally" — stale doctrine |
| integrations.resend_email     | active     | ✅ |
| integrations.emergent_llm     | active     | ✅ |

---

## Phase 5 — `GET /api/admin/system-health` ❌ FAIL (hard-coded yellow)

```
overall : yellow
cards:
  database       : green  Connected
  r2             : green  Configured · ready
  backup         : green  2026-06-11T03:07:07Z (0.5h ago)
  auth_failures  : green  0 attempts (1h)
  integrations   : YELLOW  "Motive + MaintainX (stubbed)"   ❌
    └ motive     : YELLOW  "Stubbed"
    └ maintainx  : YELLOW  "Stubbed"
  failed_syncs   : green  0 failures (24h)
  active_sessions: green  1 signed-in user (12h)
  version        : green  unknown · built —
```

**Root cause (`/app/backend/routes/admin_ops.py` lines 141-160):**

1. `await db.integration_settings.find_one({}, {"_id": 0})` returns a single root document — but the actual schema stores **one row per provider** (`{provider: "motive", api_key_value: …, enabled: true, …}`). So `cfg.get("motive", {})` is always `{}`. Wrong query against the new schema.
2. Outer card status is hard-coded `"status": "yellow"` with the comment `# always yellow until live` — this overrides whatever the children say.
3. Detail text is hard-coded `"Motive + MaintainX (stubbed)"`.

This is the surface that drives the operator's "System Health" green/yellow indicator, so it is the most visible symptom.

---

## Phase 6 — Webhook route ✅ PASS

| Test                                                          | HTTP | Meaning                              |
|--------------------------------------------------------------|------|--------------------------------------|
| `GET  /api/integrations/motive/webhook`                       | 405  | Route exists, POST-only.             |
| `POST /api/integrations/motive/webhook` (no signature)        | 401  | Route exists; HMAC signature required (`Invalid webhook signature`). |
| `/api/admin/integrations/motive` → `webhook_url_path`         | `/api/integrations/motive/webhook` | Self-advertised path matches. |
| `/api/admin/integrations/motive` → `webhook_secret_present`   | true  | Secret stored in `integration_settings.motive.webhook_secret_value`. |

Webhook endpoint is publicly reachable and properly authenticated — ready for Motive Dashboard registration whenever the operator chooses.

---

## Phase 7 — Operator-gated items (READ-ONLY mandate prevented agent execution)

| Item | Status | What the operator must run |
|------|--------|----------------------------|
| `asset_mappings` count (prod DB) | NOT EXECUTED | In a prod backend pod: `db.asset_mappings.count_documents({})` — currently `/api/admin/integrations/motive.records_mapped = 0`, so expectation is 0 until mapping is initiated. |
| `employee_mappings` count (prod DB) | NOT EXECUTED | Same — `db.employee_mappings.count_documents({})`. |
| Motive Dashboard webhook registration | NOT EXECUTED | Operator-only step; agent has no Motive console access. Register `https://mascidocs.com/api/integrations/motive/webhook` with the secret from `integration_settings.motive.webhook_secret_value`. |
| Atlas "Password" user clarification | BLOCKED | Waiting on Emergent Support reply (per Message 347 forward). |

---

## Overall verdict

- **Production deploy:** ✅ CLEAN. New source hash (`10ed6fc…`) is live, `app_env=production`, `db_name=masci_safety`, startup guard did not trip, ~5 min uptime.
- **Motive integration:** ✅ FULLY ACTIVE on production. Polling is working (`last_successful_sync_at` < 2 min before probe), webhook route is mounted and signature-verified, credentials are present in the DB (`api_key_present=true`, `webhook_secret_present=true`).
- **Operator-visible health surfaces:** ❌ STILL LIE. Three endpoints (`/api/admin/integrations/health`, `/api/admin/system-health`, `/api/platform/data-truth`) report Motive as `mocked / stubbed / yellow` even though it is active. The bug is exclusively in the *probes*; the integration itself is unaffected.

This is a **PARTIAL PASS**: the deploy and Motive activation closeout are operationally complete, but the three health-card readers need a 1-line fix each (read from `integration_settings` DB row in addition to env var) before the green light promised in Message 348 can be earned.

---

## Recommended next steps (require operator approval — not executed)

1. **Patch the three health probes** to consult `integration_settings.<provider>` in MongoDB *before* falling back to env vars. One-line change in each of:
   - `routes/integration_health.py::_probe_motive`
   - `routes/admin_ops.py::compute_system_health` (lines 141-160 — also fix the hard-coded `"yellow"` and the find_one schema bug)
   - `routes/platform_data_truth.py` lines 84-99 (read DB; remove `"active": False  # MASCI activates Motive externally` stale doctrine)
2. Redeploy and re-run this 7-phase certification to claim the FULL PASS.
3. Register the webhook in the Motive Dashboard once the green card is earned, then re-probe `/api/admin/integrations/motive.last_sync_at` to confirm push events arrive in addition to the poll.
