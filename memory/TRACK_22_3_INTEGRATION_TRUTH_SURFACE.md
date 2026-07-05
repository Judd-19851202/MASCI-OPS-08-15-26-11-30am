# TRACK 22.3 — Integration Truth Surface + AI Key Status Fix + DR-V2 Alias Telemetry

**Status**: ✅ IMPLEMENTED · 2026-07-05
**Environment**: PREVIEW (production not yet touched)
**Doctrine anchor**: Rebuilds trust after F-01 (fake-green AI status) and F-02
(unproven Motive live claim) discovered in the Track 22.2 Brutal Reality Audit.

---

## 1. Trust Doctrine (why this exists)

Track 22.2 exposed two P0 lies:

- **F-01** — AI Configuration UI read `.env` placeholders and reported
  keys as "configured" while the running process actually got its keys
  from Emergent-injected secrets via `os.environ`. Operators had no way
  to see which keys were live at runtime.
- **F-02** — Motive was labelled `live` from configuration alone; there
  was no independent proof the integration was actually working.

TRACK 22.3 builds an admin-only Integration Truth surface that reports
**runtime reality only**. Three principles:

1. **Runtime, not placeholder**. All AI key reads go through
   `os.environ` — never `dotenv_values`.
2. **Configuration ≠ connectivity ≠ operational activity**. All three
   states are reported independently. `LIVE_VERIFIED` requires proof of
   recent successful activity, not just credentials.
3. **Zero secret leakage**. Only booleans + masked last-4 leave the
   server. No raw API keys ever hit the wire.

---

## 2. Backend surface

Route module: `/app/backend/routes/integration_truth.py`

All routes gated by `require_admin_strict` — PM/HR/Field/Shop/Dispatch
tokens are rejected. 401 without an admin token.

### `GET /api/admin/ai/keys/status`

Reads every AI provider env var from `os.environ` at request time.
Never touches `dotenv_values`. Advertises `reads_from: "os.environ
(runtime — not dotenv/.env placeholders)"` in the response so operators
can prove the reading path.

Reports `emergent_llm`, `anthropic`, `openai`, `gemini`, `google_ai`.
Rows include:

- `key_present: bool`
- `key_last4: "…XXXX"` (masked; never full value)
- `covered_by_universal: bool` — true when a provider key is absent
  but the Emergent Universal LLM key can cover it.
- `status: CONFIGURED | CONFIGURED_VIA_UNIVERSAL | MISSING_SECRET`

### `GET /api/admin/integrations/truth-status`

Three-state truth per integration:

- `config_status`: `CONFIGURED | PARTIAL_CONFIG | MISSING_CONFIG | MOCKED | DISABLED`
- `connectivity_status`: `REACHABLE | UNREACHABLE | UNKNOWN | NOT_APPLICABLE`
- `operational_status`: `LIVE_VERIFIED | IDLE | STALE | NO_ACTIVITY | NOT_APPLICABLE`
- `overall`: rolled up from the three states.

Integrations covered:

| id | Name | Expected | Live-verification path |
|---|---|---|---|
| `mongo` | MongoDB (Atlas) | LIVE | `db.command("ping")` |
| `motive` | Motive (Telematics) | LIVE | 3s ping to `/v1/users/me` + 15-min activity window |
| `maintainx` | MaintainX (Work Orders) | MOCKED | never claims LIVE_VERIFIED |
| `resend` | Resend Email | LIVE | `re_…` shape + `AUTO_EMAIL_REPORTS` |
| `r2` | Cloudflare R2 | LIVE | env presence: `S3_ACCESS_KEY/SECRET_KEY/BUCKET/ENDPOINT_URL` |
| `sentry` | Sentry | OPTIONAL | `SENTRY_DSN` presence |
| `emergent_llm` | Emergent Universal LLM Key | LIVE | `sk-emergent-…` shape check |

**Motive doctrine**: safe, read-only 3-second connectivity probe. Never
declares LIVE_VERIFIED from configuration alone. Recent successful sync
(≤ 15 min) counts as `LIVE_VERIFIED` even if the ping momentarily fails,
so temporary Motive-side blips do not falsely declare the integration
dead.

### `GET /api/admin/dr-v2-alias-telemetry?recent_limit=N`

Returns two shapes:

- `aggregates[]` — one row per `METHOD /api/dr-v2/*` route (permanent
  until DR-UNIFY-005), with `first_observed_at`, `last_observed_at`,
  `lifetime_hits`, `last_role`, `last_env`, and a dynamic
  `retirement_recommendation` (`SAFE_TO_RETIRE` or `REVIEW_BEFORE_RETIRE`).
- `recent[]` — the last N detail events (default 50, max 500).

Detail events auto-expire after 30 days via a Mongo TTL index. Aggregate
statistics survive TTL so DR-UNIFY-005 can prove the aliases are dead
before removing them.

---

## 3. Middleware: DR-V2 alias tracker

Registered in `server.py` alongside the iter453.6 readiness gate. For
every request whose path starts with `/api/dr-v2/`, it:

1. Fires the actual request through the existing routes (zero drift).
2. Schedules a fire-and-forget task that writes:
   - one detail event to `dr_v2_alias_telemetry_events` (TTL 30 days)
   - one upsert to `dr_v2_alias_aggregate` (permanent-until-retirement)

Telemetry writes NEVER block or fail the request. Any exception is
swallowed and logged at DEBUG level.

Collections:

- `dr_v2_alias_telemetry_events` — TTL index on `at` (30 days),
  secondary index on `(path, at desc)`.
- `dr_v2_alias_aggregate` — unique index on `route_key`.

Both retired under DR-UNIFY-005 unless a documented operational reason
to keep them exists.

---

## 4. Frontend surface

New admin page: `/app/frontend/src/pages/admin/IntegrationTruth.jsx`
route: `/admin/integration-truth`

Three panels stacked on `AdminShell`:

1. **AI Key Status** — one card per provider, badge + env var name +
   masked last-4 + human-readable detail.
2. **Integration Truth** — table with configuration, connectivity,
   operational status, and detail per integration. Roll-up badge in
   the header.
3. **Legacy /api/dr-v2/* Alias Telemetry** — summary stats + aggregate
   table with retirement recommendation column.

Every interactive element has a stable `data-testid` (`refresh-*-btn`,
`integration-row-*`, `ai-key-row-*`, `alias-agg-row-*`).

Sidebar entries added to both `AdminShell.jsx` (flat menu) and
`components/admin/sidebar/domainMap.js` (grouped V2 sidebar).

---

## 5. Tests

`/app/backend/tests/test_track_22_3_integration_truth.py` — 9 tests, all passing:

| Test | Verifies |
|---|---|
| `test_endpoints_require_admin[…]` | All 3 endpoints 401 without admin token |
| `test_ai_keys_status_reads_from_environ` | Advertises os.environ source; EMERGENT_LLM_KEY visible at runtime |
| `test_ai_keys_status_never_leaks_raw_secrets` | Full raw keys never in response; last-4 matches expected pattern |
| `test_integrations_truth_status_three_state_model` | Three-state model shape; MaintainX never LIVE_VERIFIED |
| `test_motive_never_live_verified_from_config_alone` | Motive rolls up to LIVE_VERIFIED only with proof (F-02 fix) |
| `test_dr_v2_alias_telemetry_captures_hits` | Middleware writes detail + aggregate rows |
| `test_dr_v2_alias_events_have_ttl_index` | Detail events collection carries the 30-day TTL |

---

## 6. Retirement plan

When DR-UNIFY-005 lands:

1. Confirm every aggregate row shows `retirement_recommendation =
   SAFE_TO_RETIRE`.
2. Delete `/api/dr-v2/*` routes and canonicalize helper.
3. Drop collections `dr_v2_alias_telemetry_events` and
   `dr_v2_alias_aggregate` unless a documented operational reason to
   keep them exists.
4. Remove the middleware from `server.py`.
5. Remove this route module and its tests.

This is migration telemetry, not a permanent product feature.
