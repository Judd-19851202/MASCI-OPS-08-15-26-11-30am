# TRACK 15.34B · Production-Health-Probe Alert Storm RCA + Hardening

**Track:** 15.34B
**Date:** 2026-02
**Mode:** Read-only investigation → targeted hardening of monitor only · NO production app code changes
**Trigger:** Repeated GitHub email alerts from the `production-health-probe` workflow despite production being healthy.

---

## TL;DR

🟢 **Production (mascidocs.com) is HEALTHY** — all 5 probes pass in ~1 second when run directly.

🔴 **The probe was firing false positives** because:
1. A single 25-second transient blip on a GitHub-hosted runner (DNS/TLS/network) was indistinguishable from a real outage to the workflow.
2. Failure output was uninformative — operator could not triage from the email.
3. The `route` expectation had a latent bash-arithmetic bug that could either silently pass or silently fail on `code=000`.

🛠️ **Fix:** Added a two-pass soak (30s default) to `tools/verify-production.sh`. A probe must be red on BOTH passes before the workflow fails. Added full diagnostic output (curl exit code · errormsg · DNS/TLS/total timings · body excerpt). Added a defensive `if:` guard on the workflow job. Added a GitHub Step Summary on failure.

🛡️ **True outage detection preserved:** any genuine outage lasting more than ~60 seconds will still fail both passes and alert.

---

## 1 · Root Cause Analysis

### 1.1 · Live production proof

```text
$ curl -sS -w "HTTP %{http_code} | time=%{time_total}s\n" https://mascidocs.com/api/health
{"ok":true,"service":"masci-hub","ts":"2026-06-19T09:54:25.050008+00:00"}HTTP 200 | time=0.683s

$ curl -sS -w "HTTP %{http_code} | time=%{time_total}s\n" https://mascidocs.com/api/healthz
{"ok":true}HTTP 200 | time=0.136s
```

Production is healthy. The probe was alerting on transient runner-side network noise, not real outages.

### 1.2 · Why `verify-production.sh` was alert-flapping

The pre-15.34B script had basic retry hardening (`curl --retry 2 --retry-all-errors --retry-delay 1`), but:

| Issue | Detail |
|---|---|
| **No double-take soak** | If any of the 5 probes failed within its ~25s retry window, the workflow exited 1 immediately. There was no concept of "wait 30s and re-verify." A single GH-runner DNS hiccup → email alert. |
| **Uninformative failure output** | The script printed only `HTTP 000` (or worse, accumulated `HTTP 000000` from retries leaking into `%{http_code}`). No DNS time, no TLS time, no curl exit code, no `errormsg`, no response body. The operator opening the failure email could not distinguish "DNS hiccup" from "real 502." |
| **ANSI codes rendered literally in CI logs** | The script unconditionally emitted `\033[…]` color codes. GitHub Actions logs are not TTYs and rendered the escape sequences as literal `[0;32m✅[0m` text — confusing in failure emails. |
| **Latent bash-arithmetic bug on `route` expectation** | `[[ "$code" -lt 500 ]]` treats `code="000"` as integer 0 and passes it as healthy because `0 < 500`. Combined with `[[ "$code" != "000" ]]`, the original guard caught the single-attempt case but could be defeated by the retry accumulation pattern `"000000"`. |

### 1.3 · Workflow trigger config — already clean

The previous trigger config was:
```yaml
on:
  schedule:
    - cron: "*/15 * * * *"
  workflow_dispatch: {}
```
**No `pull_request`. No `push`.** This is correct — the alert storm was NOT from PR/push spam. The complaint about "running on every pull_request unnecessarily" does not apply to this workflow. (However, `ci.yml` and `sigma3-deploy-gate.yml` DO trigger on `push` + `pull_request` — those are separate gates and out of scope for this track.)

### 1.4 · Routes are NOT stale post-Tracks 15.30–15.34

All 5 probed endpoints are live on production:

| Endpoint | HTTP | Status |
|---|---|---|
| `GET /api/health` | 200 | canonical hub health |
| `POST /api/passkeys/login/options` | 200 | passkey path live |
| `GET /api/admin-strict/diag/persistence-health` | 401 | auth gate live (treated as "auth-ok") |
| `GET /api/field-memory/recent` | 401 | auth gate live (treated as "auth-ok") |
| `GET /api/dispatch/operational-moments/by-assignment/test` | 401 | auth gate live (treated as "auth-ok") |

The retired shared-auth paths (Shop HMAC, PM/Admin shared password) are NOT probed by this script. Tracks 15.30–15.34 did not stale these probes.

### 1.5 · True root cause

**A single transient GitHub-hosted-runner network event ≈ a real outage in the workflow's eyes.** The GitHub-hosted runner pool sometimes has DNS or TLS micro-blips that resolve within 30 seconds. Without a soak/double-take, every blip = email. With ~96 runs/day, even a 1% blip rate produces a near-daily false alert + a "back to healthy" alert = alert fatigue.

---

## 2 · Files Changed

| File | Change |
|---|---|
| `tools/verify-production.sh` | Rewritten. Two-pass soak (30s default, configurable via `SOAK_SECONDS`), full diagnostic capture (`%{exitcode}`, `%{errormsg}`, `%{time_namelookup}`, `%{time_connect}`, `%{time_total}`, body excerpt), strict regex status-code parsing (no more bash-arith `route` bug), TTY-aware ANSI colors (clean output in CI logs), `STRICT_NO_SOAK=1` override for post-deploy use. |
| `.github/workflows/production-health-probe.yml` | Added defensive job-level `if:` guard (`github.event_name == 'schedule' \|\| github.event_name == 'workflow_dispatch'`) so even if someone later adds `push` or `pull_request` to the trigger block, the job still won't run on PR events. Added `tee` of probe output to `/tmp/probe.log` + a GitHub Step Summary that publishes the full diagnostic to the workflow UI on failure. Set `SOAK_SECONDS: "30"` explicitly. |

**Production application code: UNTOUCHED.**

---

## 3 · Before / After Behavior

### 3.1 · Workflow triggers (before vs after)

| | Before | After |
|---|---|---|
| `schedule */15 * * * *` | ✅ enabled | ✅ enabled |
| `workflow_dispatch` | ✅ enabled | ✅ enabled |
| `push` | (not in trigger) | (not in trigger) + job-level `if:` guard rejects it |
| `pull_request` | (not in trigger) | (not in trigger) + job-level `if:` guard rejects it |

No change to the trigger surface. Added belt-and-suspenders job-level `if:` so future edits to the trigger block can't accidentally re-enable PR spam.

### 3.2 · Probe behavior on a single transient blip (before vs after)

**Before:**
```
T+0s     run starts
T+25s    probe N fails after 3 retries → workflow exits 1
T+25s    GitHub sends "workflow failed" email
T+15min  next scheduled run; if it passes, GitHub sends "back to passing" email
         RESULT: 2 alert emails per single transient blip · ~daily occurrence
```

**After:**
```
T+0s     run starts (pass 1)
T+25s    probe N fails on pass 1 → enter soak
T+55s    soak ends; pass 2 begins
T+57s    probe N passes on pass 2 → workflow exits 0 (no alert)
         RESULT: 0 alert emails for any blip that recovers within 60s
```

### 3.3 · Probe behavior on a real outage (before vs after)

**Before:**
- 25-second window red → exit 1 → email.

**After:**
- Pass 1 red (25s) + 30s soak + pass 2 red (25s) → exit 1 with full diagnostic → email + GitHub Step Summary.
- Worst-case total runtime: ~85s. Real outages typically last minutes; this still catches them.

### 3.4 · Failure output (before vs after)

**Before:**
```
❌ GET  /api/health                              HTTP 000000
❌ GET  /api/admin-strict/diag/persistence-health HTTP 000000
```
(no idea why · no diagnostic · ANSI escape sequences rendered literally in email)

**After:**
```
FAIL  GET  /api/health                                           HTTP 000 · curl_exit=6
      └─ DNS=0.000000s  connect=0.000000s  total=0.001135s
      └─ curl: Could not resolve host: mascidocs.com
      └─ body:
```
Plus a GitHub Step Summary on the workflow UI with the full output + operator triage checklist.

---

## 4 · Live Production Health Proof (post-fix)

```text
$ bash /app/tools/verify-production.sh

  Pass 1 · production health smoke @ https://mascidocs.com
  ────────────────────────────────────────────────────────────────────
  OK    GET  /api/health                                           HTTP 200 · 0.202632s
  OK    POST /api/passkeys/login/options                           HTTP 200 · 0.225464s
  OK    GET  /api/admin-strict/diag/persistence-health             HTTP 401 · 0.133862s
  OK    GET  /api/field-memory/recent                              HTTP 401 · 0.106401s
  OK    GET  /api/dispatch/operational-moments/by-assignment/test  HTTP 401 · 0.124542s
  ────────────────────────────────────────────────────────────────────

  OK    All 5 probes healthy in 1s.

Exit: 0
```

---

## 5 · Re-Run Proof (synthetic outage path)

Test of the soak + diagnostic path against an unreachable host (simulating a "real" outage that fails both passes):

```text
$ SOAK_SECONDS=3 PROD_URL="https://this-host-does-not-exist-12345.example" bash /app/tools/verify-production.sh

  Pass 1 · production health smoke @ https://this-host-does-not-exist-12345.example
  ────────────────────────────────────────────────────────────────────
  FAIL  GET  /api/health                                           HTTP 000 · curl_exit=6
  FAIL  POST /api/passkeys/login/options                           HTTP 000 · curl_exit=6
  FAIL  GET  /api/admin-strict/diag/persistence-health             HTTP 000 · curl_exit=6
  FAIL  GET  /api/field-memory/recent                              HTTP 000 · curl_exit=6
  FAIL  GET  /api/dispatch/operational-moments/by-assignment/test  HTTP 000 · curl_exit=6
  ────────────────────────────────────────────────────────────────────

  WARN  5 probe(s) red on pass 1. Soaking 3s before pass 2…

  Pass 2 · soak re-verify @ this-host-does-not-exist-12345.example
  ────────────────────────────────────────────────────────────────────
  FAIL  GET  /api/health                                           HTTP 000 · curl_exit=6
        └─ DNS=0.000000s  connect=0.000000s  total=0.001135s
        └─ curl: Could not resolve host: this-host-does-not-exist-12345.example
  […4 more probes with the same diagnostic detail…]
  ────────────────────────────────────────────────────────────────────

  FAIL  5 probe(s) RED on both passes (real outage signal) in 4s.
```

✅ Real-outage detection works.
✅ Diagnostics are visible.
✅ Exit code 1 → GitHub will still alert when production is actually down.

---

## 6 · Validation

| Check | Result |
|---|---|
| `bash -n tools/verify-production.sh` | ✅ syntax valid |
| YAML lint (`python3 yaml.safe_load`) | ✅ parses cleanly · triggers = `[schedule, workflow_dispatch]` · job `if:` guard present |
| Live production all-green probe | ✅ 5/5 in 1s |
| Synthetic-outage probe (real failure path) | ✅ fails both passes, exits 1, full diagnostic emitted |
| `STRICT_NO_SOAK=1` post-deploy mode | ✅ fast-fails without soak (preserves the original post-deploy contract) |

---

## 7 · Rollback Plan

If the new probe logic causes any unexpected behavior, rollback is two file restorations from git:

```bash
cd /app
# Restore the previous probe script:
git checkout HEAD~1 -- tools/verify-production.sh
# Restore the previous workflow:
git checkout HEAD~1 -- .github/workflows/production-health-probe.yml
```

(`HEAD~1` here refers to the commit immediately preceding the Track 15.34B commit. Adjust as needed.)

The previous version is preserved in git history and can be restored without touching any production app code.

Alternatively, to disable the workflow entirely while keeping the new script, comment out the `schedule:` block in `.github/workflows/production-health-probe.yml`. The workflow will still be runnable via the "Run workflow" button.

---

## 8 · Summary

| Goal | Status |
|---|---|
| Keep true outage detection | ✅ Real outages >60s still fail both passes |
| Eliminate single-blip false positives | ✅ Two-pass soak (30s default) catches transient runner-side blips |
| Add retries if missing | ✅ Two-pass soak is the structural retry; per-attempt curl has `-m 8` strict timeout |
| Add clear failure output showing exact URL/status/curl error | ✅ HTTP code, curl exit code, `errormsg`, DNS/TLS timings, response body excerpt — all visible in the workflow log AND posted to GitHub Step Summary |
| Prevent pull_request spam | ✅ Trigger was already clean; added job-level `if:` guard as belt-and-suspenders |
| Do not hide real failures | ✅ Both-pass-red still exits 1 → email still fires for genuine outages |

🟢 **No more bullshit alert storm unless production is actually down.**
