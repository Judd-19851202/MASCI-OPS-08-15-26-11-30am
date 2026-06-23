"""Track 15.69D · Behavior-matrix + absent-vs-false parity proof.

Read-only · no DB writes · no emails sent · no production state touched.

Proves:
  1. Exhaustive truth table for routing_v2_enabled() matches the spec.
  2. Absent env var and value 'false'/'FALSE'/'0' produce BIT-IDENTICAL
     resolver behavior across every seeded route (recipient sets + source).
"""
from __future__ import annotations
import asyncio, json, os, sys
from pathlib import Path
from datetime import datetime, timezone

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))

from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
load_dotenv(HERE.parent / ".env")

import email_routing_v2 as v2  # noqa: E402

TENANT = "masci"

# Shared legacy provider map (mirrors track_15_65_parity_verify.py)
ROUTE_LEGACY_PROVIDERS = {
    "SAFETY_FORMS_TO": lambda: (os.environ.get("SAFETY_FORMS_EMAIL_TO") or "safety@mascigc.com,jaymn.judd@mascigc.com").split(","),
    "FIELD_LEADERSHIP_ALWAYS_TO": lambda: [
        os.environ.get("LEADERSHIP_ALWAYS_TO_1") or "jaymn.judd@mascigc.com",
        os.environ.get("LEADERSHIP_ALWAYS_TO_2") or "safety@mascigc.com",
    ],
    "PRE_OP_FAIL_FALLBACK": lambda: os.environ.get("SHOP_MANAGER_EMAIL") or "shopmanager@mascigc.com",
    "INCIDENT_SEVERE_CC": lambda: [e.strip() for e in (os.environ.get("SEVERE_INCIDENT_CC") or "").split(",") if e.strip()],
    "BACKUP_ALERTS": lambda: [e.strip() for e in (os.environ.get("BACKUP_EMAIL_TO") or "").split(",") if e.strip()],
    "HEALTH_ALERTS": lambda: [e.strip() for e in (os.environ.get("HEALTH_ALERT_RECIPIENTS") or os.environ.get("BACKUP_EMAIL_TO") or "safety@mascigc.com").split(",") if e.strip()],
    "OUTAGE_ALERTS": lambda: [os.environ.get("OUTAGE_ALERT_TO") or "jaymn.judd@mascigc.com"],
    "SAFETY_DIGEST_TO": lambda: [os.environ.get("SAFETY_DIGEST_TO_EMAIL") or "safety@mascigc.com"],
    "OPERATOR_DIGEST_RECIPIENTS": lambda: [e.strip() for e in (os.environ.get("OPERATOR_DIGEST_RECIPIENTS") or os.environ.get("SAFETY_DIGEST_TO_EMAIL") or "safety@mascigc.com").split(",") if e.strip()],
    "PAYROLL_VARIANCE_TO": lambda: [e.strip() for e in (os.environ.get("PAYROLL_VARIANCE_EMAIL_TO") or os.environ.get("SUPER_ADMIN_EMAIL") or "jaymn.judd@mascigc.com").split(",") if e.strip()],
    "ADMIN_DEAD_LETTER_TO": lambda: [(os.environ.get("ADMIN_DEAD_LETTER_EMAIL") or "safety@mascigc.com")],
    "DISPATCH_ROLE_TO": lambda: [(os.environ.get("DISPATCH_EMAIL") or os.environ.get("SUPER_ADMIN_EMAIL") or "jaymn.judd@mascigc.com")],
    "SUPER_ADMIN_TO": lambda: [os.environ.get("SUPER_ADMIN_EMAIL") or "jaymn.judd@mascigc.com"],
    "COMPLIANCE_ALWAYS_CC": lambda: ["jaymn.judd@mascigc.com", "safety@mascigc.com"],
    "TRENCH_SAFETY_PULSE_SAFETY": lambda: [os.environ.get("SAFETY_DIGEST_TO_EMAIL") or os.environ.get("SUPER_ADMIN_EMAIL") or "safety@mascigc.com"],
    "TRENCH_SAFETY_PULSE_SHOP": lambda: [os.environ.get("SHOP_MANAGER_EMAIL") or "shopmanager@mascigc.com"],
}

# ------------------------------------------------------------------
# PART A · Truth-table
# ------------------------------------------------------------------
SPEC = [
    (None,        False),
    ("",          False),
    ("false",     False),
    ("False",     False),
    ("FALSE",     False),
    ("0",         False),
    ("no",        False),
    ("off",       False),
    ("random",    False),
    ("true",      True),
    ("True",      True),
    ("TRUE",      True),
    ("1",         True),
    ("yes",       True),
    ("Yes",       True),
    ("YES",       True),
    ("on",        True),
    ("ON",        True),
    ("  true  ",  True),
    ("  false ",  False),
]

original = os.environ.get("EMAIL_ROUTING_V2")
matrix_rows = []
matrix_pass = True
for value, expected in SPEC:
    if value is None:
        os.environ.pop("EMAIL_ROUTING_V2", None)
    else:
        os.environ["EMAIL_ROUTING_V2"] = value
    actual = v2.routing_v2_enabled()
    ok = actual == expected
    matrix_pass = matrix_pass and ok
    matrix_rows.append({
        "input":    "<unset>" if value is None else repr(value),
        "expected": expected,
        "actual":   actual,
        "pass":     ok,
    })

# ------------------------------------------------------------------
# PART B · absent-vs-false-vs-FALSE-vs-0 parity across all routes
# ------------------------------------------------------------------
async def _snapshot(env_value):
    if env_value is None:
        os.environ.pop("EMAIL_ROUTING_V2", None)
    else:
        os.environ["EMAIL_ROUTING_V2"] = env_value
    v2.invalidate_cache()

    client = AsyncIOMotorClient(os.environ["MONGO_URL"])
    db = client[os.environ["DB_NAME"]]
    routes = await db.email_routes.find({"tenant_key": TENANT}, {"_id": 0}).sort("route_key", 1).to_list(200)

    out = {}
    for doc in routes:
        rk = doc["route_key"]
        provider = ROUTE_LEGACY_PROVIDERS.get(rk)
        try:
            res = await v2.resolve(db, rk, legacy_provider=provider)
            out[rk] = {
                "to":   sorted(res.to or []),
                "cc":   sorted(res.cc or []),
                "bcc":  sorted(res.bcc or []),
                "from": res.from_email,
                "source": res.source,
                "v2_enabled_at_resolve": v2.routing_v2_enabled(),
            }
        except Exception as e:  # noqa: BLE001
            out[rk] = {"error": repr(e)}
    client.close()
    return out

async def main():
    snap_absent = await _snapshot(None)
    snap_false  = await _snapshot("false")
    snap_FALSE  = await _snapshot("FALSE")
    snap_0      = await _snapshot("0")
    snap_empty  = await _snapshot("")

    def diff(a, b):
        return {k: {"absent": a[k], "other": b[k]} for k in a if a[k] != b[k]}

    out = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "matrix_pass": matrix_pass,
        "matrix_rows": matrix_rows,
        "routes_tested": len(snap_absent),
        "parity": {
            "absent_vs_false":  {"pass": diff(snap_absent, snap_false)  == {}, "diff": diff(snap_absent, snap_false)},
            "absent_vs_FALSE":  {"pass": diff(snap_absent, snap_FALSE)  == {}, "diff": diff(snap_absent, snap_FALSE)},
            "absent_vs_0":      {"pass": diff(snap_absent, snap_0)      == {}, "diff": diff(snap_absent, snap_0)},
            "absent_vs_empty":  {"pass": diff(snap_absent, snap_empty)  == {}, "diff": diff(snap_absent, snap_empty)},
        },
        "sources_seen_under_absent": sorted({v.get("source") for v in snap_absent.values() if isinstance(v, dict) and "source" in v}),
        "sources_seen_under_false":  sorted({v.get("source") for v in snap_false.values()  if isinstance(v, dict) and "source" in v}),
    }

    # Restore baseline
    if original is None:
        os.environ.pop("EMAIL_ROUTING_V2", None)
    else:
        os.environ["EMAIL_ROUTING_V2"] = original
    v2.invalidate_cache()

    Path("/app/test_reports").mkdir(parents=True, exist_ok=True)
    Path("/app/test_reports/track_15_69d_behavior_matrix.json").write_text(json.dumps(out, indent=2, default=str))
    print(json.dumps({
        "matrix_pass": out["matrix_pass"],
        "routes_tested": out["routes_tested"],
        "absent_vs_false_pass": out["parity"]["absent_vs_false"]["pass"],
        "absent_vs_FALSE_pass": out["parity"]["absent_vs_FALSE"]["pass"],
        "absent_vs_0_pass":     out["parity"]["absent_vs_0"]["pass"],
        "absent_vs_empty_pass": out["parity"]["absent_vs_empty"]["pass"],
        "sources_seen_absent":  out["sources_seen_under_absent"],
        "sources_seen_false":   out["sources_seen_under_false"],
        "report": "/app/test_reports/track_15_69d_behavior_matrix.json",
    }, indent=2))

if __name__ == "__main__":
    asyncio.run(main())
