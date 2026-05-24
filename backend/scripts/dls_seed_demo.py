"""
dls_seed_demo.py — DEV-ONLY · iter392 follow-up · NOT for production.

Purpose
-------
Populate the Dispatch Lifecycle System (DLS) with realistic demo data so
the iter393 driver mobile surface and the iter394 dispatch board can be
built against live-shaped data WITHOUT contaminating real operational
records.

This script is **never auto-run**. It must be invoked explicitly:

    # From /app/backend
    python -m scripts.dls_seed_demo

    # Or from /app (matching the user-spec invocation)
    python -m backend.scripts.dls_seed_demo          # requires PYTHONPATH=/app

    # Direct file run (always works)
    python /app/backend/scripts/dls_seed_demo.py

Flags
-----
    --reset-demo        Delete all demo rows (tenant_id == DEMO_TENANT_ID)
                        from dispatch_assignments, dispatch_state_events,
                        and haul_cycles before (re)seeding.
    --only-reset        Wipe demo rows and exit (no re-seed).
    --tenant-id ID      Override DEMO_TENANT_ID (default: "dls-demo").
                        Production tenant ("masci") is hard-blocked.
    --base-url URL      Override REACT_APP_BACKEND_URL (default reads it
                        from /app/frontend/.env).
    --admin-password PW Override ADMIN_PASSWORD (default reads it from
                        /app/backend/.env).

Isolation contract
------------------
- All demo rows go into the dedicated tenant ``dls-demo`` so production
  queries (which default to ``masci``) never see them.
- Production tenant (``masci``) is explicitly refused as the demo tenant.
- All demo trucks / drivers / projects use obvious ``DEMO-…`` prefixes.
- Re-running without ``--reset-demo`` is safe but appends new
  assignments — use the flag to keep the demo set stable.

What this script does NOT do
----------------------------
- Does NOT bypass the iter392 lifecycle engine. Every transition goes
  through the real ``/api/dispatch/*`` endpoints so the demo data is
  shaped identically to production data.
- Does NOT create driver sessions / magic-link tokens (iter393 scope).
- Does NOT touch governance, notifications, CSV, or any UI.
- Does NOT introduce permanent demo behavior — there is no scheduler,
  no startup hook, no auto-seed of any kind.
"""
from __future__ import annotations

import argparse
import os
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

import requests
from dotenv import dotenv_values

# Production tenant — refused as a demo target.
_PRODUCTION_TENANT = "masci"
DEFAULT_TENANT_ID = "dls-demo"

DEMO_TRUCKS: List[Dict[str, str]] = [
    {
        "truck_id": "DEMO-T-001",
        "driver_id": "demo-driver-alice",
        "driver_name": "DEMO · Alice Driver",
        "project_number": "DEMO-PRJ-A",
        "project_name": "DEMO · Loop Trail",
        "material": "Asphalt",
        "source_location": "DEMO Plant A",
        "destination": "DEMO Loop Trail Lay Zone",
        "loader_operator_name": "DEMO · Loader Mike",
    },
    {
        "truck_id": "DEMO-T-002",
        "driver_id": "demo-driver-bob",
        "driver_name": "DEMO · Bob Driver",
        "project_number": "DEMO-PRJ-B",
        "project_name": "DEMO · Overlay 17",
        "material": "Base Rock",
        "source_location": "DEMO Quarry East",
        "destination": "DEMO Overlay 17 Stockpile",
        "loader_operator_name": "DEMO · Loader Diane",
    },
    {
        "truck_id": "DEMO-T-003",
        "driver_id": "demo-driver-carol",
        "driver_name": "DEMO · Carol Driver",
        "project_number": "DEMO-PRJ-C",
        "project_name": "DEMO · Patch Run",
        "material": "Millings",
        "source_location": "DEMO Yard",
        "destination": "DEMO Patch Site",
        "loader_operator_name": "DEMO · Yard Crew",
    },
]

# Three lifecycle scripts — one per demo truck.
# Each step is (to_state, optional kwargs). The lifecycle engine
# tags non-standard transitions automatically; we don't need to flag.
HAPPY_PATH: List[Dict[str, Any]] = [
    {"to_state": "ENROUTE_TO_LOAD", "note": "DEMO · departing yard"},
    {"to_state": "AT_LOAD_SITE", "note": "DEMO · arrived at plant"},
    {"to_state": "LOADING", "note": "DEMO · loading commenced"},
    {"to_state": "LOADED", "note": "DEMO · load secured, ticket photographed"},
    {"to_state": "ENROUTE_TO_JOB", "note": "DEMO · heading to job"},
    {"to_state": "ARRIVED_JOB", "note": "DEMO · on site"},
    {"to_state": "DUMPING", "note": "DEMO · dumping"},
    {"to_state": "COMPLETE", "note": "DEMO · cycle complete"},
]

# Wait-state demo truck STOPS at WAITING so the dispatch board (iter394)
# has a live "stuck on plant" row to render. The state_history still
# captures the journey ASSIGNED → ENROUTE_TO_LOAD → AT_LOAD_SITE →
# WAITING with wait_reason=WAITING_ON_PLANT.
WAIT_PATH: List[Dict[str, Any]] = [
    {"to_state": "ENROUTE_TO_LOAD", "note": "DEMO · departing yard"},
    {"to_state": "AT_LOAD_SITE", "note": "DEMO · arrived at quarry"},
    {
        "to_state": "WAITING",
        "wait_reason": "WAITING_ON_PLANT",
        "note": "DEMO · plant down — queue backed up (left stuck for board demo)",
    },
]

NON_STANDARD_PATH: List[Dict[str, Any]] = [
    {"to_state": "ENROUTE_TO_LOAD", "note": "DEMO · departing yard"},
    # Intentional truck-boss override — short haul, skipping intermediate states.
    {
        "to_state": "COMPLETE",
        "correction_reason": "DEMO · truck-boss override — micro haul, no plant stop",
        "note": "DEMO · non-standard jump for governance demo",
    },
]


def _read_env_value(env_path: Path, key: str) -> str:
    try:
        for line in env_path.read_text().splitlines():
            if line.startswith(f"{key}="):
                return line.split("=", 1)[1].strip().strip('"').rstrip("/")
    except Exception:
        return ""
    return ""


def _resolve_base_url(arg_url: Optional[str]) -> str:
    if arg_url:
        return arg_url.rstrip("/")
    url = (
        _read_env_value(Path("/app/frontend/.env"), "REACT_APP_BACKEND_URL")
        or os.environ.get("REACT_APP_BACKEND_URL")
        or ""
    ).rstrip("/")
    if not url:
        raise SystemExit(
            "ERROR: REACT_APP_BACKEND_URL not found. Pass --base-url explicitly.",
        )
    return url


def _resolve_admin_password(arg_pw: Optional[str]) -> str:
    if arg_pw:
        return arg_pw
    pw = (
        _read_env_value(Path("/app/backend/.env"), "ADMIN_PASSWORD")
        or os.environ.get("ADMIN_PASSWORD")
        or ""
    )
    if not pw:
        raise SystemExit(
            "ERROR: ADMIN_PASSWORD not found. Pass --admin-password explicitly.",
        )
    return pw


def _admin_login(base_url: str, password: str) -> str:
    r = requests.post(
        f"{base_url}/api/admin/login",
        json={"password": password},
        timeout=15,
    )
    if r.status_code != 200:
        raise SystemExit(f"ERROR: admin login failed ({r.status_code}): {r.text[:200]}")
    token = r.json().get("token")
    if not token:
        raise SystemExit("ERROR: admin login returned no token")
    return token


def _headers(token: str, tenant_id: str) -> Dict[str, str]:
    return {
        "X-Admin-Token": token,
        "X-Tenant-Id": tenant_id,
        "Content-Type": "application/json",
    }


def _reset_demo(tenant_id: str) -> Dict[str, int]:
    """Wipe demo rows directly via pymongo. Refuses to touch the
    production tenant. Returns deletion counts per collection."""
    if tenant_id == _PRODUCTION_TENANT:
        raise SystemExit(
            f"REFUSED: refusing to wipe production tenant '{_PRODUCTION_TENANT}'.",
        )
    env = dotenv_values("/app/backend/.env")
    mongo_url = env.get("MONGO_URL") or os.environ.get("MONGO_URL")
    db_name = env.get("DB_NAME") or os.environ.get("DB_NAME")
    if not (mongo_url and db_name):
        raise SystemExit("ERROR: MONGO_URL / DB_NAME missing for reset")

    from pymongo import MongoClient
    db = MongoClient(mongo_url)[db_name]
    counts: Dict[str, int] = {}
    for coll in ("dispatch_assignments", "dispatch_state_events", "haul_cycles"):
        res = db[coll].delete_many({"tenant_id": tenant_id})
        counts[coll] = int(res.deleted_count)
    return counts


def _create_assignment(
    *, base_url: str, headers: Dict[str, str], truck_spec: Dict[str, str],
) -> Dict[str, Any]:
    r = requests.post(
        f"{base_url}/api/dispatch/assignments",
        headers=headers,
        json=truck_spec,
        timeout=20,
    )
    if r.status_code != 200:
        raise SystemExit(
            f"ERROR: create_assignment failed ({r.status_code}): {r.text[:300]}",
        )
    return r.json()["assignment"]


def _run_path(
    *,
    base_url: str,
    headers: Dict[str, str],
    assignment_id: str,
    path: List[Dict[str, Any]],
    delay_seconds: float,
) -> List[Dict[str, Any]]:
    """Walk an assignment through a lifecycle path via the real API.
    Returns the final assignment.state_history[]."""
    last_assignment: Dict[str, Any] = {}
    for step in path:
        # Spread between transitions so the resulting haul_cycles row
        # has a meaningful total_seconds (still bounded — keep it small
        # for dev iteration).
        if delay_seconds > 0:
            time.sleep(delay_seconds)
        r = requests.post(
            f"{base_url}/api/dispatch/assignments/{assignment_id}/transition",
            headers=headers,
            json=step,
            timeout=20,
        )
        if r.status_code != 200:
            raise SystemExit(
                f"ERROR: transition {step.get('to_state')} failed "
                f"({r.status_code}): {r.text[:300]}",
            )
        last_assignment = r.json()["assignment"]
    return list(last_assignment.get("state_history") or [])


def _summarize(
    *, base_url: str, headers: Dict[str, str], tenant_id: str,
) -> None:
    board = requests.get(
        f"{base_url}/api/dispatch/assignments/board",
        headers=headers, timeout=20,
    ).json()
    events = requests.get(
        f"{base_url}/api/dispatch/state-events",
        headers=headers, params={"limit": 500}, timeout=20,
    ).json()
    cycles = requests.get(
        f"{base_url}/api/dispatch/haul-cycles",
        headers=headers, timeout=20,
    ).json()
    non_std = requests.get(
        f"{base_url}/api/dispatch/state-events",
        headers=headers, params={"non_standard_only": "true", "limit": 100},
        timeout=20,
    ).json()
    listing = requests.get(
        f"{base_url}/api/dispatch/assignments",
        headers=headers, params={"include_completed": "true", "limit": 100},
        timeout=20,
    ).json()
    print()
    print("=" * 64)
    print(f"  DLS demo summary · tenant_id = {tenant_id}")
    print("=" * 64)
    print(f"  /dispatch/assignments/board ............ active = {board.get('count', 0)}")
    print(f"  /dispatch/assignments  (incl. complete)  total  = {listing.get('count', 0)}")
    print(f"  /dispatch/state-events ................. rows   = {events.get('count', 0)}")
    print(f"  /dispatch/haul-cycles .................. rows   = {cycles.get('count', 0)}")
    print(f"  /dispatch/state-events?non_standard_only = rows   = {non_std.get('count', 0)}")
    print()
    print("  Active trucks on the board:")
    for a in board.get("assignments", []):
        print(
            f"    {a.get('truck_id'):<14} state={a.get('current_state'):<16} "
            f"driver={a.get('driver_name')}",
        )
    if cycles.get("count", 0):
        print()
        print("  Completed haul_cycles:")
        for c in cycles.get("cycles", []):
            print(
                f"    {c.get('truck_id'):<14} transitions={c.get('transitions')} "
                f"non_std={c.get('non_standard_transitions')} "
                f"total_s={c.get('total_seconds')} wait_s={c.get('wait_seconds')}",
            )
    if non_std.get("count", 0):
        print()
        print("  Non-standard events (for governance demo):")
        for e in non_std.get("events", []):
            print(
                f"    {e.get('from_state')} -> {e.get('to_state'):<16} "
                f"tag={e.get('warning_tag')} reason={e.get('correction_reason') or '—'}",
            )
    print()


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="DLS dev-only seed helper.")
    parser.add_argument("--reset-demo", action="store_true",
                        help="Delete demo rows before re-seeding.")
    parser.add_argument("--only-reset", action="store_true",
                        help="Delete demo rows and exit (no re-seed).")
    parser.add_argument("--tenant-id", default=DEFAULT_TENANT_ID,
                        help=f"Demo tenant_id (default: {DEFAULT_TENANT_ID}). "
                             f"Cannot be the production tenant.")
    parser.add_argument("--base-url", default=None,
                        help="Override REACT_APP_BACKEND_URL.")
    parser.add_argument("--admin-password", default=None,
                        help="Override ADMIN_PASSWORD.")
    parser.add_argument("--delay", type=float, default=0.25,
                        help="Seconds between transitions (default 0.25). "
                             "Small positive values make haul_cycles "
                             "total_seconds non-zero.")
    args = parser.parse_args(argv)

    tenant_id = (args.tenant_id or DEFAULT_TENANT_ID).strip()
    if tenant_id == _PRODUCTION_TENANT:
        print(
            f"REFUSED: --tenant-id cannot be '{_PRODUCTION_TENANT}' "
            "(production). Pick another label.",
            file=sys.stderr,
        )
        return 2

    if args.reset_demo or args.only_reset:
        counts = _reset_demo(tenant_id)
        print(
            f"[reset] tenant_id={tenant_id} · deleted "
            f"dispatch_assignments={counts['dispatch_assignments']} "
            f"dispatch_state_events={counts['dispatch_state_events']} "
            f"haul_cycles={counts['haul_cycles']}",
        )
        if args.only_reset:
            return 0

    base_url = _resolve_base_url(args.base_url)
    admin_pw = _resolve_admin_password(args.admin_password)
    token = _admin_login(base_url, admin_pw)
    headers = _headers(token, tenant_id)

    print(f"[seed] base_url={base_url} tenant_id={tenant_id}")
    print(f"[seed] creating {len(DEMO_TRUCKS)} demo assignments…")

    paths = (HAPPY_PATH, WAIT_PATH, NON_STANDARD_PATH)
    labels = ("HAPPY_PATH", "WAIT_PATH (WAITING_ON_PLANT)", "NON_STANDARD_PATH")
    for spec, path, label in zip(DEMO_TRUCKS, paths, labels):
        a = _create_assignment(base_url=base_url, headers=headers, truck_spec=spec)
        print(f"[seed]   created assignment id={a['id']} truck={a['truck_id']} "
              f"plan={label}")
        history = _run_path(
            base_url=base_url, headers=headers,
            assignment_id=a["id"], path=path, delay_seconds=args.delay,
        )
        final_state = history[-1]["to_state"] if history else a.get("current_state")
        print(f"[seed]   walked {len(path)} transition(s) — final state = {final_state}")

    _summarize(base_url=base_url, headers=headers, tenant_id=tenant_id)
    print("[seed] done.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
