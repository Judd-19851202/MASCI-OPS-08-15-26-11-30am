# Executive Command Center · Production Certification Report

**Batch:** Pillar 2 · Phase A · Path B · Post-deploy production certification probe
**Date:** 2026-05-31 (probes captured 13:47 UTC)
**Scope:** Probe production (`https://mascidocs.com`) for the 5 required verifications: source hash, `/admin/command-center` SPA route, `/api/admin/command-center/snapshot` endpoint, D5 evidence (Approvals card), and scheduler/backups/recovery regression check.
**Discipline:** OMEGA · evidence-only · no code change · no deploy executed.

---

## 1 · Executive verdict

🔴 **NOT CERTIFIED — Production has NOT been deployed with the Path B build (nor with the underlying Phase A initial implementation).**

The five verifications were performed honestly against the live production environment. Verification 1 (source hash) and Verification 3 (snapshot endpoint reachable) **both fail** because the production source tree predates Phase A entirely. Verifications 2 and 5 pass; Verification 4 cannot be assessed because the endpoint required to compute it does not yet exist in production.

This is **NOT a code regression**. It is a state mismatch: preview holds the Path B build; production still holds the pre-Phase A code that was last certified on 2026-05-31 in `OMEGA_PRE_DEPLOYMENT_CERTIFICATION_REPORT.md` (source_hash `533c269640ae7153de97ac56a998089a` — the same hash production reports today).

Operator action required: explicit production deploy authorization. No code, no deploy, no scope change has been performed by this report.

---

## 2 · The five verifications · evidence table

### V1 · Production source hash

| Environment | `source_hash` | `app_env` | `db_name` | `started_at` | `uptime_s` |
|---|---|---|---|---|---|
| Preview | **`54b8a402de538a17579cabc2e6aaac38`** | `preview` | `masci_safety_preview` | 2026-05-31T13:21:17Z | 1,511 |
| Production | **`533c269640ae7153de97ac56a998089a`** | `production` | `masci_safety` | 2026-05-31T02:39:11Z | 40,038 |

**Diff:** hashes differ → **production has NOT been redeployed since the Path B work was committed in preview.** Production uptime (~11h09m) confirms it has been running on the same pre-Phase A binary since 02:39 UTC, well before the Path B patches landed (12:35 UTC).

Cross-reference: `OMEGA_PRE_DEPLOYMENT_CERTIFICATION_REPORT.md` §1 recorded preview = prod = `533c269640ae7153de97ac56a998089a` BEFORE Phase A was built. That hash is also today's production hash. The Phase A initial implementation (commit `22f40ff` · 2026-05-31 04:01 UTC) and the Path B patch (commit `1820fe9` · 2026-05-31 12:35 UTC) have only ever existed in preview.

| Boot/process health (production) | Value |
|---|---|
| `boot_exception` | `None` |
| `sentry.enabled` | `true` |
| `session_timeouts.enabled` | `true` |
| `/api/health` | `{"ok": true, "ts": "2026-05-31T13:47:00Z"}` |

🔴 **V1 verdict: FAIL — production is not on the Path B source hash.**

### V2 · `/admin/command-center` loads on production

```
prod /admin/command-center  → 200
prod /admin/login           → 200
prod /                      → 200
```

🟡 **V2 verdict: PARTIAL.** The route returns 200 only because the React SPA catch-all serves the shell HTML for any path. Once a real session opens that page, the client-side `RequireAdmin` shell will mount `AdminCommandCenter.jsx`, which will immediately call `GET /api/admin/command-center/snapshot` — and that call will 404 (see V3). The page will render an empty/error state in production until V3 is satisfied.

(The `AdminCommandCenter.jsx` source itself was added in commit `22f40ff` but has not been deployed; production has neither the page component nor the sidebar link.)

### V3 · Snapshot endpoint behaves correctly

| Probe | Result (production) | Result (preview · for comparison) |
|---|---|---|
| `GET /api/admin/command-center/snapshot` (no token) | **404** body `{"detail":"Not Found"}` | 401 |
| `GET /api/admin/command-center/snapshot` (admin token) | **404** body `{"detail":"Not Found"}` | 200 with snapshot payload |
| `GET /api/admin/command-center/thresholds` (no token) | 404 | 401 |
| `GET /api/admin/command-center/thresholds` (admin token) | 404 | 200 |
| `GET /api/admin/command-center/calendar` (no token) | 404 | 401 |
| `GET /api/admin/command-center/calendar` (admin token) | 404 | 200 |

FastAPI `{"detail":"Not Found"}` is the framework's own 404 — proving the route is not registered (this is not an nginx, ingress, or auth-gate 404; it is a "no such route" 404). The same probe on preview returns 401 unauth / 200 with token, proving the same routes exist on the Path B build.

🔴 **V3 verdict: FAIL — `/api/admin/command-center/*` routes do not exist on production.**

### V4 · D5 count appears in production

D5 is the BSON-Date vs ISO-string cross-type fix on `po_requests.created_at`. The certification evidence is the `approvals.headline_counts.pending_amber` value surfaced by `/api/admin/command-center/snapshot`.

**Result:** Cannot be assessed. The endpoint does not exist in production (per V3). There is no production snapshot payload to read.

For context, the live preview snapshot (Path B build) reports:
```
approvals.headline_counts: {"pending_amber": 139, "pending_red": 0, "pending_week_plus": 0}
approvals.warnings:        ["139 PO(s) pending approval 3-4 days"]
```
This is what production *would* report once Path B is deployed and snapshot is recomputed against `masci_safety`. The specific count will reflect production data, not preview data.

🟡 **V4 verdict: NOT ASSESSABLE pre-deploy. Will become a 🟢 GREEN check the first time the production snapshot endpoint responds 200 with a populated `approvals.headline_counts`.**

### V5 · No scheduler / backups / recovery regression

| Production probe | Status | Body excerpt |
|---|---|---|
| `GET /api/health` | **200** | `{ok:true, ts:2026-05-31T13:47:00Z}` |
| `GET /api/admin/backups-scheduler-state` (admin) | **200** | keys: `scheduler · task_alive · seconds_since_last_tick · manual_run · manual_in_progress · lite_mode_only_env · oom_watermark_mb · watchdog_threshold_hours · now_utc · scheduled_hours_utc` |
| `GET /api/admin/recovery/snapshot` (admin) | **200** | `pill=AMBER · computed_at=2026-05-31T13:47:29Z · keys: last_backup · last_drill · backup_age_minutes · rpo · rto · archive_count · bucket_usage · archive_size_trend · failures_7d` |
| Production boot state | clean | `boot_exception=None` |
| Production uptime | 40,038s (~11h09m) | continuous since 02:39 UTC |

Production scheduler, backups, and recovery surfaces respond exactly as documented in `OMEGA_PRE_DEPLOYMENT_CERTIFICATION_REPORT.md` (gates 2, 5, 8). Path B preview work did not touch any of these subsystems and therefore could not have regressed them. The probes above confirm the assumption with live evidence.

🟢 **V5 verdict: PASS — no scheduler/backups/recovery regression detected on production.**

---

## 3 · Combined verification scorecard

| # | Verification | Verdict |
|---|---|---|
| V1 | Production source hash matches Path B build | 🔴 FAIL · production on pre-Phase A hash `533c269640ae7153de97ac56a998089a` |
| V2 | `/admin/command-center` loads on production | 🟡 PARTIAL · SPA shell 200, but client will hit V3 failure on first API call |
| V3 | `/api/admin/command-center/snapshot` reachable | 🔴 FAIL · 404 (route not registered in production) |
| V4 | D5 count surfaces in production | 🟡 NOT ASSESSABLE · gated by V3 |
| V5 | No scheduler / backups / recovery regression | 🟢 PASS |

**Result: 1 PASS · 2 PARTIAL/NOT-ASSESSABLE · 2 FAIL. Production is NOT certified post-deploy because there has been no deploy.**

---

## 4 · Operational impact today (production is still pre-Phase A)

- Executive Command Center is **invisible in production** (no sidebar link, no functional page) — the operator-facing dashboard does not yet exist for the production user base.
- Production approvals card under-reporting (D5) is **also not in production** — but only because the card itself isn't there. The risk surfaces *only after* deploy, at which point the Path B build (already mitigating D5) ships at the same time. Path B will not arrive late.
- D1 / D2 (Safety closure-state miss) is **moot** in production today — same reason.
- All other production behavior — backups, scheduler, recovery dashboard, every existing portal — is **unaffected and healthy**.

---

## 5 · What this report did NOT do

- ❌ Did not deploy anything.
- ❌ Did not modify any code (preview or production).
- ❌ Did not change any env var.
- ❌ Did not invalidate any cache or restart any service.
- ❌ Did not draw conclusions beyond the five live probes.
- ❌ Did not extend Path B scope.

---

## 6 · Operator decision required

To certify production end-to-end, the operator must:

1. Authorize a production deploy of the current preview source tree (Path B build).
2. Re-run the five verifications against production after deploy:
   - V1 → expect both hashes match `54b8a402de538a17579cabc2e6aaac38` (or whatever Path B commits to at deploy time).
   - V2 → unchanged 200.
   - V3 → expect 401 unauth · 200 admin (currently 404 unauth · 404 admin).
   - V4 → expect `approvals.headline_counts.pending_amber` to populate from `masci_safety` data and pulse aggregates to reconcile.
   - V5 → expect unchanged 🟢 PASS (zero regression).
3. If any verification returns red post-deploy, rollback is a single-button revert (no schema delta in Path B; rollback is code-only).

🛑 **STOPPED.** No deploy executed. No code change. No further action will be taken until explicit operator authorization is issued.
