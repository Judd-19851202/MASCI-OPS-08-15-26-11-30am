# TRACK 19.42 · Legacy `safety_digest.py` · Forensic Audit

**Classification:** C — **KEEP ACTIVE UNTIL OPERATOR CONFIRMS CUTOVER.**

## Discovery

- Module: `/app/backend/safety_digest.py` (122 lines).
- Wiring: `server.py` L10829 imports · L11890–L11909 `_start_safety_digest_cron` schedules `safety_digest_scheduler_loop` under `run_with_singleton_lock(db, "safety_digest", ...)`.
- Provider: `fsi_send_email` (existing).
- Recipients: single address from `SAFETY_DIGEST_TO_EMAIL` (default `safety@mascigc.com`).
- Schedule: Weekly Mon 14:00 UTC via `_seconds_until_next_send()`.
- Env: `SAFETY_DIGEST_ENABLED` (default `true`), `SAFETY_DIGEST_HOUR_UTC` (14), `SAFETY_DIGEST_WEEKDAY` (0=Mon).
- Track 15.75 status page (`server.py::_last_for("safety_digest")`) still reports its last run.

## Active state

| Env | State | Notes |
|---|---|---|
| Preview | 🟢 **Disabled** — `SCHEDULER_ENABLED=false` short-circuits every `run_with_singleton_lock` cron. No live send in preview. |
| Production | 🟡 **Active** — `SCHEDULER_ENABLED=true` in prod; cron continues to fire Monday 14:00 UTC to `safety@mascigc.com`. |

## Overlap with Track 19.39

Track 19.39 (`safety_morning_digest`) is the modernised replacement. It supersedes `safety_digest.py`:

| Dimension | Legacy `safety_digest.py` | Track 19.39 `safety_morning_digest` |
|---|---|---|
| Recipients | Single env address | Managed via `morning_digest_recipients` collection |
| Layout | Custom HTML | Standard 14-section (retrofitted in Track 19.42) |
| Score | ❌ None | ✅ Operational Intelligence Score |
| Trend | ❌ None | ✅ `compute_trend` engaged |
| Dry-run | Env-gated (`AUTO_EMAIL_REPORTS`) | Explicit `dry_run` param, default True |
| Audit | ❌ None | `morning_digest_audit` + engine audit rows |
| Dedupe | none | Engine dedupe |
| Preview | Curl-only | HTTP endpoint |
| Permissions | Env address only | Safety+Admin gated CRUD |

## Cutover plan

Track 19.42 does **not** disable the legacy cron in production. Reasoning:
- Different recipient set (env-address vs managed list).
- Safety leadership may still rely on the legacy digest during transition.
- Zero-drift doctrine — no silent behavior change.

### Recommended sequence (Track 19.43 operator gate)

1. Operator adds current `SAFETY_DIGEST_TO_EMAIL` recipients into `morning_digest_recipients` (`digest_type=safety_morning_digest`).
2. Operator opts in to Track 19.39 live-send.
3. Run one week overlap — verify Track 19.39 delivery on Monday morning.
4. Set `SAFETY_DIGEST_ENABLED=false` in production `.env`.
5. Confirm no send from legacy path via `scheduler_runs` audit.
6. Track 19.44 archives `safety_digest.py` (still present for rollback but never imported).

## No double-send risk today

- Preview: `SCHEDULER_ENABLED=false` → neither cron fires.
- Production: legacy sends Monday 14:00 UTC to a **different single-address recipient set**. Track 19.39 has no scheduler wired yet (dispatch is manual via `/api/incident-intelligence/morning-digest/send`). No overlap fire until the operator explicitly triggers it.

## Retention

- Code retained for rollback confidence.
- Track 19.42 lock test asserts module still present + preview scheduler is disabled.
