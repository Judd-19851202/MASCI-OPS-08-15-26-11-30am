# TRACK 15.52A · Health-Probe Forensics

**Status:** Live trace · evidence-only · captured 2026-06-19 20:50 UTC.
**Question:** What does `backup_recent` actually check? Why is `production-health-probe` reportedly emailing operators?

## 1 · `/api/health/full` · before Track 15.52 fix

Source: `backend/server.py` lines 973-991 (pre-fix snapshot recovered from `TRACK_15_52_HEALTH_PROBE_BACKUP_OBSERVABILITY_FIX.md`).

```python
latest_ok = await db.backup_health.find_one(
    {"ok": True}, sort=[("ts", -1)], projection={"_id": 0, "ts": 1}
)
if latest_ok and latest_ok.get("ts"):
    ...
    out["backup_recent"] = age_s < (26 * 3600)
```

**`backup_recent` previously checked**: one row · from the Mongo collection `backup_health` · filtered by `ok=true` · sorted by `ts desc` · checking if age < 26 hours.

## 2 · `/api/health/full` · after Track 15.52 fix (current preview)

Source: `backend/server.py` lines 974-1024 (current).

```python
backup_age_s = await _r2_backup_age_seconds_cached()
if backup_age_s is not None:
    out["backup_recent"] = backup_age_s < (26 * 3600)
else:
    # Fallback to backup_health DB row (existing logic, plus filename guard).
    ...
```

`_r2_backup_age_seconds_cached()` (new in Track 15.52):
- Calls `photo_storage._client().get_paginator("list_objects_v2")` against `Bucket=masci-hub Prefix=backups/`.
- Walks every page, finds the newest `LastModified`.
- Returns `(now - newest).total_seconds()`.
- Caches in `_R2_BACKUP_AGE_CACHE` for 5 min.

**`backup_recent` NOW checks**: the most recent `LastModified` on any object under `s3://masci-hub/backups/` · 5-min cached · falls back to the original `backup_health` DB row only on R2 infrastructure failure.

## 3 · `/api/health/full` · `ok` truth table

`ok = mongo AND scheduler AND backup_recent`, except for the legacy fast-path at line 998-1000 that promotes `scheduler` when `backup_recent` is true and the heartbeat tick is briefly missing (RC-2.1 fix from 2026-06-11).

Returns HTTP 200 when ok=true, **HTTP 503 when ok=false**.

## 4 · `production-health-probe.yml` · what it actually probes

Source: `.github/workflows/production-health-probe.yml` + `tools/verify-production.sh`.

```bash
PROBES=(
  "GET  /api/health                                          | expect=ok"
  "POST /api/passkeys/login/options                          | expect=route"
  "GET  /api/admin-strict/diag/persistence-health            | expect=auth"
  "GET  /api/field-memory/recent                             | expect=auth"
  "GET  /api/dispatch/operational-moments/by-assignment/test | expect=auth"
)
```

Cadence: `cron */15 * * * *` (every 15 min) + manual `workflow_dispatch`.

Failure logic: a probe is RED only if it fails on **both** the initial pass and the 30-second soak re-verify (Track 15.34B hardening). Email only fires on workflow exit non-zero.

**`production-health-probe.yml` DOES NOT consult `/api/health/full`.** This is the most important finding of this forensic phase.

## 5 · Live execution of the exact probe set against `mascidocs.com`

Run at 2026-06-19 20:50 UTC, same logic as the workflow:

```
GET  /api/health                                             HTTP=200  expect=ok      PASS   0.193s
POST /api/passkeys/login/options                             HTTP=200  expect=route   PASS   0.246s
GET  /api/admin-strict/diag/persistence-health               HTTP=401  expect=auth    PASS   0.169s
GET  /api/field-memory/recent                                HTTP=401  expect=auth    PASS   0.116s
GET  /api/dispatch/operational-moments/by-assignment/test    HTTP=401  expect=auth    PASS   0.182s
```

**ALL 5 PROBES PASS.** The production-health-probe workflow, executed as-coded against production, exits zero with no failure summary. **No email would fire from THIS workflow in THIS moment.**

## 6 · Why might operators have seen failure emails?

Possible explanations, evidence-ranked:

| Hypothesis | Evidence for | Evidence against |
|---|---|---|
| **A · UptimeRobot 503 on `/api/health/full`** (NOT this GitHub workflow) | UptimeRobot is documented as the consumer in `backend/tests/test_iter183_health_full_endpoint.py` + `server.py` comments. The earlier Track 15.52 fix found `backup_recent=false → 503` on PREVIEW. | Production `/api/health/full` returns 200 now and reports `backup_recent=true` (audit row is fresh on prod's `backup_health` collection). |
| **B · Production `/api/health/full` briefly 503 during deploy window** | Production was restarted at 2026-06-19 10:20 UTC (`uptime_s=37774`). For ~30 s after restart, the scheduler is in `await asyncio.sleep(30)` (line 7679) before the first tick. If UptimeRobot polled in that 30-s window, `last_tick_ts=None` → `scheduler=false` → 503. | This window is rare (30 s out of every 15 min UptimeRobot tick = 3.3% chance per restart). |
| **C · GitHub-runner DNS/TLS hiccup tripping `route` expect** | Real-world GitHub-hosted runner blips exist. | Track 15.34B added the 30-s soak specifically to suppress this. Both passes must fail for the workflow to email. |
| **D · A different probe configured elsewhere** | The user's GitHub Actions may include private workflows not in this repo. | Cannot verify from this container. |
| **E · The earlier Track 15.52 false-red feedback loop** | Track 15.52 DID identify `/api/health/full` returning 503 on preview. If the operator's UptimeRobot also pointed at preview during a test window, they'd see those alert emails and attribute them to "production-health-probe". | The workflow file itself is verifiably not the source. |

Most likely root cause = **A or E**: the false-red emails came from UptimeRobot probing `/api/health/full`, which was failing on preview (and could intermittently flap on production during restart windows). The operator naming-collapsed "GitHub Actions production-health-probe" with "the production health probe" (UptimeRobot is also a "production health probe" in colloquial usage).

The Track 15.52 fix (R2-direct `backup_recent`) addresses BOTH:
- Preview `/api/health/full` now stably 200.
- Production deploy-window-restart class of false-red would also be muted post-deploy because the R2 truth path is independent of the in-process `last_tick_ts` heartbeat.

## 7 · "Why is GitHub emailing operators?"

**Best evidence-based answer:** They probably aren't, from the workflow in this repository. All 5 probed endpoints return PASS as of 2026-06-19 20:50 UTC. The most likely source of operator-visible alert emails was UptimeRobot's external probe of `/api/health/full`, which:
- Was reliably returning 503 on preview before Track 15.52 (audit-row drift).
- Could intermittently return 503 on production during the 30-s post-restart window.
- After Track 15.52 (R2-direct truth source) is propagated to production, this failure class is eliminated.

If the operator sees specific GitHub `production-health-probe` failure emails, the workflow run page would show which of the 5 probes failed — and `verify-production.sh` includes full diagnostic output (DNS, connect, total, body excerpt). **Without that run URL or log, I cannot reproduce or attribute the failure to a backup issue.**

## 8 · Fallback path verification (Track 15.52 fix)

Verified end-to-end:
- R2 reachable → uses R2 LastModified (the canonical truth).
- R2 unreachable (simulated by setting cache to `None`) → falls back to `db.backup_health.find_one({ok:true, filename:nin:[None,""]})`, same 26-h SLO.
- Both R2 and DB unreachable → `backup_recent=false → 503`. Real outage still alerts.

Contract test `backend/tests/test_iter183_health_full_endpoint.py` · 3/3 PASS.
