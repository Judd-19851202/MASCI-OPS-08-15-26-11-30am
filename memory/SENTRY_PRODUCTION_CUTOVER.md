# Sentry — Production Cutover Runbook

> Last updated: 2026-02-XX · Status: **READY for operator-initiated production flip**
> Scope: lightweight observability only (errors · exceptions · release visibility · high-severity alerts).
> Explicitly out of scope: Session Replay · Performance tracing · Profiling.

This doc is the single source of truth for promoting Sentry from preview to production. Preview verification is complete; this captures **exactly** what changes on production, what does NOT change, and how to verify.

---

## 1. What is already done (no operator action needed)

| Surface | Status |
|---|---|
| Backend SDK | ✅ Installed (`sentry-sdk[fastapi]==2.60.0`) |
| Frontend SDK | ✅ Installed (`@sentry/react==10.53.1`) |
| PII scrubber | ✅ Active on both — passwords, tokens, secrets, api_keys, Authorization, Cookie, X-*-Token headers, HMAC-shaped hex blobs |
| Release identifier | ✅ Deterministic — backend `/api/version` and frontend init both report the same `source_hash` (32 chars) |
| Frontend release auto-sync | ✅ `index.js` fetches `/api/version` at boot — no rebuild needed when source_hash changes |
| Preview DSNs wired | ✅ Both projects receive events under `environment=preview` |
| PII review by operator | ✅ Spot-checked 2026-02-XX — no passwords / tokens / Authorization headers visible |

---

## 2. Lightweight posture (locked in code)

This is what production WILL do, regardless of operator env-var choices:

| Capability | State | How it's enforced |
|---|---|---|
| Errors | ✅ ON | All `level=error` logged events become Sentry events |
| Exceptions | ✅ ON | Uncaught exceptions on backend and frontend captured automatically |
| Release health | ✅ ON | `auto_session_tracking=true` / `autoSessionTracking: true`. Aggregated session counts only — crash-free rate, no individual session bodies. |
| Breadcrumbs | ✅ ON (sanitized) | `INFO+` log lines + scrubbed request data |
| **Performance tracing** | 🛑 **OFF** | `traces_sample_rate=0` default; env vars `SENTRY_TRACES_RATE` / `REACT_APP_SENTRY_TRACES_RATE` are clamped to `[0, 1]` |
| **Profiling** | 🛑 **OFF** | `profiles_sample_rate=0` default |
| **Session Replay** | 🛑 **OFF** | `replaysSessionSampleRate=0` AND `replaysOnErrorSampleRate=0`. Previous `Math.max(rate, 0.1)` floor was REMOVED 2026-02-XX so leaving the env var unset means truly zero replay capture. |
| Send default PII | 🛑 **OFF** | `send_default_pii=False` on both — PII control is exclusively via our `before_send` scrubber |

**Do NOT set the following env vars in production:**
- `SENTRY_TRACES_RATE` (leave unset)
- `SENTRY_PROFILES_RATE` (leave unset)
- `REACT_APP_SENTRY_TRACES_RATE` (leave unset)
- `REACT_APP_SENTRY_REPLAY_RATE` (leave unset)

The defaults are correct. Setting any of them to a non-zero value violates the operator directive and increases your Sentry quota burn without delivering the requested capability.

---

## 3. Production cutover steps

### Step 1 — Add DSNs to production env (operator does this)

**Iter190+ auto-detect note:** Both the backend and the frontend now auto-detect environment at runtime:

- **Backend:** reads `APP_URL` (passed by Emergent supervisord) and tags `preview` if the URL contains `.preview.emergentagent.com`, otherwise `production`. Fallback: `preview_endpoint` env var. Override: `SENTRY_ENV`.
- **Frontend:** reads `window.location.hostname` and tags `preview` for `*preview*` / `localhost`, otherwise `production`. Override: `REACT_APP_SENTRY_ENV`.

**This means you do NOT need to set `SENTRY_ENV=production` in production.** The same `.env` file works for both surfaces. The DSN is the only thing that needs to exist in production. If your preview `.env` files already contain `SENTRY_DSN` and `REACT_APP_SENTRY_DSN` (they do), and Emergent's deploy pushes them as-is, **you only need to click Deploy** — Sentry will activate in production automatically with the correct environment tag.

If you DO want to be explicit, add these to production env (overrides auto-detect):

```
SENTRY_DSN=<your masci-backend-python DSN>
SENTRY_ENV=production

REACT_APP_SENTRY_DSN=<your masci-frontend-javascript-react DSN>
REACT_APP_SENTRY_ENV=production
```

**Use the SAME DSNs as preview** unless you intentionally want separate Sentry projects per environment. The `environment` tag is how Sentry differentiates preview from production within a single project. Both are valid; same-project is simpler.

### Step 2 — Trigger a production deploy
The frontend `REACT_APP_*` vars are baked at build time, so a redeploy is required. The backend picks up the new env on next process restart.

### Step 3 — Verify (within 5 minutes of deploy)
```bash
curl -s https://mascidocs.com/api/version | python3 -m json.tool | grep -A2 sentry
```
Expected:
```
"sentry": {
  "enabled": true,
  "release": "<32-char hex matching source_hash>"
}
```

Then in the Sentry dashboard:
1. Switch the environment filter to `production`
2. Visit the live site once
3. **You should see release-health "session started" within ~2 min** in the Releases tab — confirms the frontend SDK is alive in production
4. Trigger a controlled test error (recommended: temporarily click the version chip 5x to dump an INFO breadcrumb, or use the same controlled script that ran in preview pointing at the production DSN)

### Step 4 — Configure alert rules (see § 5)

### Step 5 — Monitor for 24h
- Watch the issues feed for unexpected error spikes
- Confirm scrubber working on a fresh production event (open the event JSON, search payload for `password`, `token`, `Bearer`, etc. — should not appear unredacted)

---

## 4. Production rollback

If anything goes wrong:

```
# Remove or comment out from production env
SENTRY_DSN=
REACT_APP_SENTRY_DSN=
```

Redeploy. Sentry reverts to a complete no-op. No code change required. The SDKs are env-gated by design — empty DSN means zero side effects.

---

## 5. Alert rules (configure in Sentry UI after Step 3 verification)

Five recommended alerts. They map 1-to-1 to the operational signals you actually care about. Configure these in **Alerts → Create Alert → Issue Alert**. Notifications go to the integration you choose (email, Slack, etc.); the rule logic is portable.

### Alert 1 — New high-severity issue in latest release
**Why:** catches regressions on the very next deploy without flooding you with old known issues.
- **Project:** both (configure separately or use a global rule)
- **When:** A new issue is created
- **If:**
  - `level:` equals `error` OR `fatal`
  - `release:` equals `latest`
  - `environment:` equals `production`
- **Then:** send notification immediately
- **Frequency:** every time it fires (do not throttle — these are by definition new issues)

### Alert 2 — Issue regression (resolved → unresolved)
**Why:** something you've already triaged and resolved has come back. This is a strong "the fix didn't stick" signal.
- **When:** An issue changes state from `resolved` to `unresolved`
- **If:** `environment:` equals `production`
- **Then:** send notification immediately

### Alert 3 — Backend exception spike on critical paths
**Why:** an outage on admin or auth surfaces is operationally critical.
- **Project:** `masci-backend-python`
- **When:** The issue is seen more than 5 times in 5 minutes
- **If:**
  - `transaction:` starts with `/api/admin` OR starts with `/api/auth` OR contains `login`
  - `level:` equals `error` OR `fatal`
  - `environment:` equals `production`
- **Then:** send notification + assign to operator
- **Frequency:** at most once per hour

### Alert 4 — Frontend uncaught exception burst
**Why:** a deployed bug visible to end users in the field.
- **Project:** `masci-frontend-javascript-react`
- **When:** The issue is seen more than 10 times in 10 minutes
- **If:**
  - `level:` equals `error` OR `fatal`
  - `environment:` equals `production`
  - `mechanism:` is `unhandled` (Sentry's tag for crashes that escaped React's error boundary)
- **Then:** send notification
- **Frequency:** at most once every 30 minutes

### Alert 5 — Crash-free session rate drop (release health)
**Why:** the single best early-warning signal that a deploy is bad. If crash-free rate on the latest release dips even 2–3 points below the prior release, something regressed.
- **Type:** Metric Alert (not Issue Alert) → `Crash Free Sessions`
- **Filter:** `environment:production`
- **Condition:** crash-free session rate `< 98%` over a 1-hour window
- **Frequency:** at most once per hour

**98% is a sensible starting floor.** Adjust after one week of baseline data: take the median crash-free rate, subtract 1 percentage point, and use that as your alert threshold. Don't set it tighter than 0.5pp below baseline or it will fire on routine deploys.

---

## 6. What to do when an alert fires

1. **Open the issue** in Sentry. Read the title, stack trace, and breadcrumbs.
2. **Check `release:`** — is it the latest deploy? If yes, this is likely a regression; consider rolling back the deploy.
3. **Check `environment:`** — production only. Preview alerts can be ignored or filtered.
4. **Check the user-agent / route** — is it a single user / single page? Or platform-wide?
5. **If platform-wide and traceable to the latest release:** rollback via Emergent Deploy → previous build. Document in `/app/memory/CHANGELOG.md` or your incident log.
6. **If isolated:** resolve in Sentry with a short note. If it recurs, Alert 2 (regression) will catch it.

---

## 7. Quota & cost discipline

The current lightweight posture should keep monthly event volume well under typical Sentry free-tier limits for a single small-team deployment. Key levers if you ever hit a quota wall:

| Lever | Effect |
|---|---|
| Increase `before_send` rejection rate for specific noisy issues | Use Sentry's "Inbound Filters" UI — preferable to code changes |
| Set per-project rate limit in Sentry Settings → Subscription → Quotas | Hard cap; events past the cap are dropped at ingest |
| Tighten `LoggingIntegration.event_level` from `ERROR` to `CRITICAL` | Backend only — drops the lower tier from being captured as events. Currently `ERROR`. |
| Disable a project's environment temporarily | If preview becomes too chatty during dev work, filter `environment != preview` in alert rules instead of disabling the SDK |

**Do NOT enable** tracing, profiling, or replay to "get more value out of the quota." Those features are explicitly out of scope per operator directive 2026-02-XX and will exhaust quota fast on a multi-user platform.

---

## 8. Maintenance checklist (quarterly)

- [ ] Open a recent Sentry event JSON. Confirm scrubber still strips `Authorization`, `Cookie`, `X-Admin-Token`, `X-PM-Token`, password fields. (Why: a future code change might add a new sensitive header that needs to be added to `_DENY_HEADERS` in `sentry_init.py`.)
- [ ] Verify the 5 alert rules above are still configured (Sentry occasionally orphans rules during plan changes).
- [ ] Compare crash-free session rate week-over-week. Adjust Alert 5's threshold if the trend has shifted.
- [ ] Verify `sentry-sdk` and `@sentry/react` versions match the platform's package files — Sentry deprecates old SDKs and dropping an upgrade silently can stop event ingestion.

---

## 9. Honest residual risks

- **Sentry-side outage = blind spot.** If Sentry has an incident, the platform itself runs fine but you stop receiving alerts. The lightweight posture does not introduce any production dependency on Sentry being up. The platform itself never calls `sentry_sdk` synchronously in a request path.
- **Release tagging depends on `/api/version` being reachable from the browser at boot.** If `/api/version` is 5xx during initial load, frontend events tag with `release="unknown"` for that session only. Subsequent reloads recover. Not a blocker — events still arrive.
- **No alert covers backend-down (the backend is literally not running).** Alerts come FROM the backend; you need a separate uptime monitor (UptimeRobot, BetterStack, etc.) to catch that case. **Not in scope for this cutover.** Document it as a Phase 3+ item if you decide to add it.
- **PII scrubber is regex-based.** A new sensitive field with a non-matching name (e.g. `bank_account_number`) would not be scrubbed automatically. The quarterly checklist (§ 8) is the mitigation.

---

## 10. Production cutover sign-off

When you have completed Steps 1–4 and the 24h monitoring window in Step 5 has passed without surprise, append a row here:

| Date | Operator | Production release at cutover | Verification notes |
|---|---|---|---|
| _pending_ | _pending_ | _pending_ | _pending_ |

A row in this table is the canonical record that production Sentry is live. Until it appears, treat production as Sentry-uninstrumented.
