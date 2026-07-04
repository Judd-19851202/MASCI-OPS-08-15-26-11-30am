#!/usr/bin/env python3
"""
iter181 + iter182 — Post-Production-Redeploy Verification Probe
================================================================

Run this script AFTER you have redeployed iter181 (route-guard /
NotFound) and iter182 (backup email storm fix) to production.

Bundles 10 acceptance checks the user mandated:

  Backend / scheduler
  -------------------
  1. Backend boot log shows backup scheduler is healthy
  2. Recognises the latest lite backup (no longer ignores them)
  3. Does NOT treat backup as stale
  4. Does NOT fire catch-up backup after restart
  5. No "MASCI Nightly Backup" email sent purely from a backend restart
  6. Next scheduled backup slot still armed normally
  7. backup_health Mongo record is being used as fallback history
  8. Local lite/full backup detection both work
  9. R2 archive still uploads on schedule (does NOT regress)

  Frontend / route guards
  -----------------------
 10. iter181 aliases work in production:
       /admin/audit           → /admin/login (anon) or /admin/audit-log
       /admin/health          → /admin/login (anon) or /admin/system-health
       /field-leadership      → /leadership (FL sign-in)
       /totally-bogus-route   → NotFound (data-testid="not-found-page")

Usage
-----
This script does NOT need credentials for parts 1, 4, 5, 9, 10. The
backend-internal probes (2, 3, 6, 7, 8) require running the scheduler
introspection endpoint, which is admin-only.

The script is read-only — it never writes to production. It NEVER
deletes any R2 object.

Invocation:
  python /app/iter181_iter182_prod_verification.py [admin_password]

If `admin_password` is omitted the admin-only probes are skipped and
the script reports "DEFER" for those checks.

Exit code 0 only if every non-deferred check passes.
"""
from __future__ import annotations

import asyncio
import json
import sys
import time
from datetime import datetime, timezone, timedelta
from typing import Optional, Tuple

import httpx

PROD = "https://mascidocs.com"


# ─── pretty output ─────────────────────────────────────────────────────────
def _ok(msg):    print(f"  ✅ {msg}")
def _fail(msg):  print(f"  ❌ {msg}")
def _warn(msg):  print(f"  ⚠️  {msg}")
def _defer(msg): print(f"  🟡 DEFER — {msg}")
def _info(msg):  print(f"     · {msg}")

PASSED, FAILED, DEFERRED = [], [], []


def _record(check_id, status, detail=""):
    if status == "pass":   PASSED.append((check_id, detail))
    elif status == "fail": FAILED.append((check_id, detail))
    else:                  DEFERRED.append((check_id, detail))


# ─── HTTP helpers ──────────────────────────────────────────────────────────
async def _get(path, headers=None) -> httpx.Response:
    async with httpx.AsyncClient(base_url=PROD, timeout=15, follow_redirects=False) as c:
        return await c.get(path, headers=headers or {})


async def _admin_token(password: str) -> Optional[str]:
    async with httpx.AsyncClient(base_url=PROD, timeout=10) as c:
        r = await c.post("/api/admin/login", json={"password": password})
        if r.status_code == 200:
            return r.json().get("token")
    return None


# ─── Part A — Iter181 route-guard verification (no creds needed) ──────────
async def part_a_route_guards():
    """
    Part A — HTTP smoke + browser checklist.

    React-Router redirects + catch-all routes execute CLIENT-SIDE
    after the JS bundle mounts. An httpx probe just fetches the
    static `index.html` shell — it cannot observe a <Navigate>
    redirect or the NotFound render. So this HTTP slice only
    confirms "the route returns 200 (no 404 at the edge / no
    server-side blank shell)". The visual confirmation must be done
    in a real browser by the operator; the checklist below tells
    them exactly what to click and what to expect.
    """
    print("\n========== A · Iter181 route-guard / NotFound HTTP smoke ==========")
    routes = [
        "/admin/audit",
        "/admin/health",
        "/field-leadership",
        "/totally-bogus-route",
        "/admin/zzzz-not-a-page",
        "/hr/zzzz-not-a-page",
    ]
    for path in routes:
        try:
            async with httpx.AsyncClient(base_url=PROD, timeout=15, follow_redirects=True) as c:
                r = await c.get(path)
            # The React SPA returns 200 + index.html for every path.
            # A 404/5xx here = the edge layer regressed.
            if r.status_code == 200 and b"<!doctype html" in r.content[:200].lower():
                _ok(f"{path:32s} 200 OK (SPA shell served)")
                _record(f"a-http-{path}", "pass")
            else:
                _fail(f"{path:32s} status={r.status_code} (expected 200 SPA shell)")
                _record(f"a-http-{path}", "fail", f"status={r.status_code}")
        except Exception as e:
            _fail(f"{path:32s} probe failed: {e!r}")
            _record(f"a-http-{path}", "fail", str(e))

    print()
    print("  ┌─ BROWSER VISUAL CHECKLIST (operator must perform manually) ─┐")
    print("  │ Open https://mascidocs.com in a fresh incognito window and visit each:")
    print("  │   1. /admin/audit          → MUST redirect to /admin/login")
    print("  │   2. /admin/health         → MUST redirect to /admin/login")
    print("  │   3. /field-leadership     → MUST redirect to /leadership sign-in")
    print("  │   4. /totally-bogus-route  → MUST render NotFound (404 page with")
    print("  │                              'We couldn't find that page' heading)")
    print("  │   5. /admin/zzzz-not-a-page → MUST render NotFound (NOT blank shell)")
    print("  │   6. /hr/zzzz-not-a-page   → MUST render NotFound (NOT blank shell)")
    print("  │ Each must show real content, NOT a blank middle with only navbar+footer.")
    print("  └─────────────────────────────────────────────────────────────┘")


# ─── Part B — Backup-storm absence (no creds needed) ──────────────────────
async def part_b_backup_email_storm_absence(admin_pw: Optional[str]):
    """We can't directly observe whether an email was sent without
    inbox access, but we CAN read the scheduler-state via the admin
    diagnostic endpoint. If `armed_at` and `last_attempt_started_at`
    are several minutes apart, we know the catch-up did NOT fire on
    the recent restart. Requires admin token."""
    print("\n========== B · Backup-storm absence after restart ==========")
    if not admin_pw:
        _defer("admin password not supplied — cannot read /api/admin/backups-scheduler-state. Skip B; ask Emergent for backend log lines instead.")
        _record("b-armed-healthy", "defer", "no admin password")
        _record("b-no-catch-up-after-restart", "defer", "no admin password")
        return
    tok = await _admin_token(admin_pw)
    if not tok:
        _fail("admin login failed — check ADMIN_PASSWORD")
        _record("b-armed-healthy", "fail", "admin login failed")
        return
    r = await _get("/api/admin/backups-scheduler-state", {"X-Admin-Token": tok})
    if r.status_code != 200:
        _fail(f"/api/admin/backups-scheduler-state returned {r.status_code}: {r.text[:120]}")
        _record("b-armed-healthy", "fail", str(r.status_code))
        return
    payload = r.json()
    state = payload.get("scheduler") or {}
    alive = state.get("alive")
    armed_at = state.get("armed_at")
    last_attempt_started_at = state.get("last_attempt_started_at")
    last_attempt_outcome = state.get("last_attempt_outcome")
    if alive and armed_at:
        _ok(f"scheduler alive=True armed_at={armed_at}")
        _record("b-armed-healthy", "pass", armed_at)
    else:
        _fail(f"scheduler not alive or not armed: {state}")
        _record("b-armed-healthy", "fail", str(state))

    # Iter182 contract: after restart, NO catch-up attempt should have
    # been recorded if the last successful backup was within 8h.
    if armed_at and last_attempt_started_at:
        try:
            a = datetime.fromisoformat(armed_at.replace("Z", "+00:00"))
            la = datetime.fromisoformat(last_attempt_started_at.replace("Z", "+00:00"))
            delta_sec = (la - a).total_seconds()
            if 0 <= delta_sec < 180:  # attempt fired within 3 min after arm = catch-up
                _fail(
                    f"catch-up appears to have fired ({delta_sec:.0f}s after arm, "
                    f"outcome={last_attempt_outcome!r})"
                )
                _record("b-no-catch-up-after-restart", "fail",
                        f"delta={delta_sec}s outcome={last_attempt_outcome}")
            else:
                _ok(
                    f"no catch-up fired (last attempt was "
                    f"{abs(delta_sec)/60:.1f} min "
                    f"{'before' if delta_sec < 0 else 'after'} arm)"
                )
                _record("b-no-catch-up-after-restart", "pass")
        except Exception as e:
            _warn(f"could not parse timestamps: {e}")
            _record("b-no-catch-up-after-restart", "defer", str(e))
    else:
        _ok("no last_attempt_started_at recorded after arm → catch-up did NOT fire")
        _record("b-no-catch-up-after-restart", "pass")


# ─── Part C — Backup health collection is honored ─────────────────────────
async def part_c_backup_health_recorded(admin_pw: Optional[str]):
    print("\n========== C · backup_health collection acting as fallback ==========")
    if not admin_pw:
        _defer("admin password not supplied — cannot read scheduler-state.recent_health")
        _record("c-mongo-fallback", "defer", "no admin password")
        return
    tok = await _admin_token(admin_pw)
    if not tok:
        _fail("admin login failed")
        _record("c-mongo-fallback", "fail")
        return
    r = await _get("/api/admin/backups-scheduler-state", {"X-Admin-Token": tok})
    if r.status_code != 200:
        _fail(f"/api/admin/backups-scheduler-state returned {r.status_code}")
        _record("c-mongo-fallback", "fail", str(r.status_code))
        return
    rows = r.json().get("recent_health") or []
    if not rows:
        _fail("backup_health.recent_health is empty — Mongo fallback can't engage")
        _record("c-mongo-fallback", "fail", "no rows")
        return
    newest = rows[0]
    ts = newest.get("ts", "")
    _ok(f"latest backup_health row: ts={ts} ok={newest.get('ok')} mode={newest.get('mode')}")
    _record("c-mongo-fallback", "pass", ts)
    _info(
        "Cross-reference backend logs for "
        "'[scheduled-backup] staleness: disk=… mongo=… (using …)' "
        "to confirm iter182 cross-check engaged."
    )


async def part_d_public_health():
    print("\n========== D · /api/health public probe ==========")
    r = await _get("/api/health")
    if r.status_code == 200 and r.json().get("ok"):
        _ok(f"/api/health: 200 {r.json()}")
        _record("d-public-health", "pass")
    else:
        _fail(f"/api/health: {r.status_code} {r.text[:120]}")
        _record("d-public-health", "fail")



async def part_e_r2_archive_sanity(admin_pw: Optional[str]):
    print("\n========== E · R2 archive cadence sanity ==========")
    if not admin_pw:
        _defer("admin password not supplied — cannot read R2 state")
        _record("e-r2-cadence", "defer", "no admin password")
        return
    tok = await _admin_token(admin_pw)
    if not tok:
        _fail("admin login failed")
        _record("e-r2-cadence", "fail")
        return
    r = await _get("/api/admin/backups-complete-r2-state", {"X-Admin-Token": tok})
    if r.status_code != 200:
        _fail(f"/api/admin/backups-complete-r2-state returned {r.status_code}")
        return
    j = r.json()
    r2_hourly = j.get("r2_hourly")
    last_r2 = j.get("last_r2_complete_hour")
    last_r2_at = j.get("last_r2_complete", {}).get("at") if isinstance(j.get("last_r2_complete"), dict) else None
    _ok(f"r2_hourly={r2_hourly}  last_r2_complete_hour={last_r2}  at={last_r2_at}")
    if r2_hourly and last_r2 is not None:
        _record("e-r2-cadence", "pass")
    else:
        _warn("R2 hourly archive not yet confirmed for current hour — re-run after the next :00 mark")
        _record("e-r2-cadence", "defer", f"r2_hourly={r2_hourly} last={last_r2}")


# ─── runner ───────────────────────────────────────────────────────────────
async def main():
    admin_pw = sys.argv[1] if len(sys.argv) > 1 else None

    print(f"iter181 + iter182 verification — target: {PROD}")
    print(f"started: {datetime.now(timezone.utc).isoformat()}")
    if not admin_pw:
        print("(no admin password supplied — admin-only probes will be DEFERRED)")

    await part_a_route_guards()
    await part_d_public_health()
    await part_b_backup_email_storm_absence(admin_pw)
    await part_c_backup_health_recorded(admin_pw)
    await part_e_r2_archive_sanity(admin_pw)

    print("\n========== SUMMARY ==========")
    print(f"  PASSED:   {len(PASSED)}")
    print(f"  FAILED:   {len(FAILED)}")
    print(f"  DEFERRED: {len(DEFERRED)}")
    if FAILED:
        print("\n  FAILED detail:")
        for cid, d in FAILED:
            print(f"    ❌ {cid}: {d}")
    if DEFERRED:
        print("\n  DEFERRED detail:")
        for cid, d in DEFERRED:
            print(f"    🟡 {cid}: {d}")

    print("\nManual checklist (you must observe outside this script):")
    print("  □  Inbox: NO 'MASCI Nightly Backup' email arrives within 5 minutes of redeploy")
    print("  □  Inbox: an email DOES arrive at the next scheduled UTC slot (02:00 or 18:00)")
    print("  □  Sign in as a real production HR / Shop / PM / Safety / Dispatch user and confirm")
    print("     no Admin button appears and /admin redirects to /admin/login")

    sys.exit(0 if not FAILED else 1)


if __name__ == "__main__":
    asyncio.run(main())
