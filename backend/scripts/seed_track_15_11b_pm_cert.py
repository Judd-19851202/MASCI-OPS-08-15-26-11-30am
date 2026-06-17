"""TRACK 15.11B — PM Portal runtime certification seed script.

Modes:
    python3 scripts/seed_track_15_11b_pm_cert.py --seed       # write cert dataset
    python3 scripts/seed_track_15_11b_pm_cert.py --verify     # read-only sanity
    python3 scripts/seed_track_15_11b_pm_cert.py --rollback   # remove all cert data

Hard safety contract:
  * APP_ENV=production OR DB_NAME=masci_safety → REFUSE every write mode
    (exit 2). --verify is allowed read-only against any env.
  * Every inserted/updated record carries `cert_track: "TRACK15_11B"`
    + `cert_run_id` + `created_by_cert: true`. Rollback matches ONLY
    those tags — no cross-record collateral.
  * No external network — no real emails, no real SMS.
  * Idempotent: re-running --seed only fills missing rows. Re-running
    --rollback only matches still-present cert rows.
  * Ledger JSON written to /app/memory/track_15_11b_<mode>_<ts>.json
    for every run.
"""
from __future__ import annotations
import argparse, asyncio, hashlib, json, logging, os, sys, uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from motor.motor_asyncio import AsyncIOMotorClient

logger = logging.getLogger("track_15_11b_cert")
logging.basicConfig(level=logging.INFO, format="# %(message)s")

CERT_TRACK = "TRACK15_11B"
PROJECT_NUMBER = "TRACK15-11B"
PROJECT_NUMBER_OTHER = "TRACK15-11B-OTHER"
PM_EMAIL = "track15.11b.cert.pm@mascicert.local"
FOREMAN_EMAIL = "track15.11b.cert.foreman@mascicert.local"
SAFETY_EMAIL = "track15.11b.cert.safety@mascicert.local"
ASSET_EMAIL = "track15.11b.cert.shop@mascicert.local"
NOLOGIN_EMAIL = "track15.11b.cert.nologin@mascicert.local"
LEDGER_DIR = Path("/app/memory")


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()

def _stamp(extra: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    base = {"cert_track": CERT_TRACK, "created_by_cert": True}
    if extra:
        base.update(extra)
    return base

def _validate_env(args, app_env: Optional[str], db_name: Optional[str]) -> Optional[str]:
    if args.verify and not (args.seed or args.rollback):
        return None  # read-only mode is always safe
    env = (app_env or "").strip().lower()
    db = (db_name or "").strip()
    if env == "production":
        return f"Refusing write mode against APP_ENV=production (got {app_env!r})."
    if db == "masci_safety":
        return f"Refusing write mode against DB_NAME=masci_safety (got {db_name!r})."
    return None


async def _ensure_user(db, run_id, email, name, *, portals, has_password=True, disabled=False) -> str:
    existing = await db.user_directory.find_one({"email": email}, {"_id": 0, "id": 1})
    if existing:
        return existing["id"]
    uid = f"cert-user-{hashlib.sha1(email.encode()).hexdigest()[:16]}"
    doc = _stamp({
        "id": uid, "email": email, "name": name,
        "portals": portals, "disabled": disabled,
        "must_change_password": False,
        "password_hash": ("$2b$12$" + "a"*53) if has_password else None,
        "last_login_at": _now() if has_password else None,
        "created_at": _now(),
        "cert_run_id": run_id,
    })
    await db.user_directory.insert_one(doc)
    return uid


async def _ensure_job(db, run_id, project_number, project_name, pm_email) -> str:
    existing = await db.jobs_master.find_one({"project_number": project_number}, {"_id": 0, "id": 1})
    if existing:
        return existing["id"]
    doc = _stamp({
        "id": f"cert-job-{project_number}",
        "project_number": project_number,
        "project_name": project_name,
        "pm_email": pm_email,
        "co_pm_emails": [],
        "active": True,
        "deleted_at": None,
        "created_at": _now(),
        "cert_run_id": run_id,
    })
    await db.jobs_master.insert_one(doc)
    return doc["id"]


async def _ensure_assignment(db, run_id, project_number, user_id, email, role) -> str:
    q = {"project_number": project_number, "user_id": user_id, "assignment_role": role, "active": True}
    existing = await db.project_team_assignments.find_one(q, {"_id": 0, "id": 1})
    if existing:
        return existing["id"]
    doc = _stamp({
        "id": f"cert-asgn-{project_number}-{role}-{hashlib.sha1(email.encode()).hexdigest()[:8]}",
        "project_number": project_number, "user_id": user_id, "email": email,
        "assignment_role": role, "active": True, "is_primary": False,
        "created_at": _now(), "cert_run_id": run_id,
    })
    await db.project_team_assignments.insert_one(doc)
    return doc["id"]


async def _ensure_daily_report(db, run_id, project_number, pm_email) -> str:
    q = {"project_number": project_number, "cert_track": CERT_TRACK}
    existing = await db.daily_reports.find_one(q, {"_id": 0, "id": 1})
    if existing:
        return existing["id"]
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    doc = _stamp({
        "id": f"cert-dr-{project_number}-{run_id[:8]}",
        "report_number": f"DR-CERT-{run_id[:8]}",
        "report_date": today, "project_number": project_number,
        "project_name": "Track 15.11B Runtime Certification Project",
        "location": "Cert lot 1", "prepared_by": pm_email,
        "superintendent": "Cert Super", "weather_summary": "Clear, 70°F",
        "narrative": "TRACK15_11B certification DR — synthetic.",
        "masci_crews": [{"foreman": "Cert Foreman", "members": [{"name": "Cert Member", "hours": 8}]}],
        "subcontractors": [], "visitors": [], "photos": [],
        "created_at": _now(), "cert_run_id": run_id,
    })
    await db.daily_reports.insert_one(doc)
    return doc["id"]


async def _ensure_photo(db, run_id, project_number, dr_id) -> str:
    q = {"project_number": project_number, "cert_track": CERT_TRACK}
    existing = await db.job_photos.find_one(q, {"_id": 0, "id": 1})
    if existing:
        return existing["id"]
    doc = _stamp({
        "id": f"cert-photo-{run_id[:8]}",
        "project_number": project_number, "source": "daily_reports", "source_id": dr_id,
        "filename": "cert.jpg", "key": f"cert/{run_id}/cert.jpg",
        "captured_at": _now(), "created_at": _now(), "cert_run_id": run_id,
    })
    await db.job_photos.insert_one(doc)
    return doc["id"]


async def _ensure_incident(db, run_id, project_number) -> str:
    q = {"project_number": project_number, "cert_track": CERT_TRACK}
    existing = await db.incidents.find_one(q, {"_id": 0, "id": 1})
    if existing:
        return existing["id"]
    doc = _stamp({
        "id": f"cert-inc-{run_id[:8]}",
        "project_number": project_number, "status": "open",
        "severity": "low", "description": "Cert incident — TRACK15_11B.",
        "reported_at": _now(), "created_at": _now(), "cert_run_id": run_id,
    })
    await db.incidents.insert_one(doc)
    return doc["id"]


async def _ensure_jha(db, run_id, project_number) -> str:
    q = {"project_number": project_number, "cert_track": CERT_TRACK}
    existing = await db.jha_records.find_one(q, {"_id": 0, "id": 1})
    if existing:
        return existing["id"]
    doc = _stamp({
        "id": f"cert-jha-{run_id[:8]}",
        "project_number": project_number, "title": "Cert JHP",
        "status": "active", "created_at": _now(), "cert_run_id": run_id,
    })
    await db.jha_records.insert_one(doc)
    return doc["id"]


async def _ensure_equipment(db, run_id, project_number) -> str:
    q = {"project_number": project_number, "cert_track": CERT_TRACK}
    existing = await db.equipment_inspections.find_one(q, {"_id": 0, "id": 1})
    if existing:
        return existing["id"]
    doc = _stamp({
        "id": f"cert-equip-{run_id[:8]}",
        "project_number": project_number, "unit_number": "CERT-001",
        "kind": "equipment", "inspection_date": _now()[:10],
        "passed": True, "failures": [],
        "created_at": _now(), "cert_run_id": run_id,
    })
    await db.equipment_inspections.insert_one(doc)
    return doc["id"]


async def seed(db, run_id) -> Dict[str, Any]:
    logger.info(f"# seed start · run_id={run_id}")
    ledger: Dict[str, Any] = {"mode": "seed", "run_id": run_id, "ts": _now(), "rows": {}}

    pm_id = await _ensure_user(db, run_id, PM_EMAIL, "Cert PM", portals=["pm"])
    foreman_id = await _ensure_user(db, run_id, FOREMAN_EMAIL, "Cert Foreman", portals=["pm", "field-leadership"])
    safety_id = await _ensure_user(db, run_id, SAFETY_EMAIL, "Cert Safety", portals=["safety"])
    asset_id = await _ensure_user(db, run_id, ASSET_EMAIL, "Cert Shop", portals=["shop"])
    nologin_id = await _ensure_user(db, run_id, NOLOGIN_EMAIL, "Cert NoLogin",
                                    portals=["pm"], has_password=False)
    ledger["rows"]["users"] = {"pm": pm_id, "foreman": foreman_id, "safety": safety_id,
                               "asset": asset_id, "nologin": nologin_id}

    job_id = await _ensure_job(db, run_id, PROJECT_NUMBER,
                               "Track 15.11B Runtime Certification Project", PM_EMAIL)
    other_id = await _ensure_job(db, run_id, PROJECT_NUMBER_OTHER,
                                 "Track 15.11B OTHER (scope-leak test)",
                                 "track15.11b.cert.other@mascicert.local")
    ledger["rows"]["jobs"] = {"primary": job_id, "other": other_id}

    sup_id = await _ensure_assignment(db, run_id, PROJECT_NUMBER, pm_id, PM_EMAIL, "superintendent")
    ledger["rows"]["assignments"] = {"superintendent": sup_id}

    dr_id = await _ensure_daily_report(db, run_id, PROJECT_NUMBER, PM_EMAIL)
    ledger["rows"]["daily_report"] = dr_id
    ledger["rows"]["photo"] = await _ensure_photo(db, run_id, PROJECT_NUMBER, dr_id)
    ledger["rows"]["incident"] = await _ensure_incident(db, run_id, PROJECT_NUMBER)
    ledger["rows"]["jha"] = await _ensure_jha(db, run_id, PROJECT_NUMBER)
    ledger["rows"]["equipment"] = await _ensure_equipment(db, run_id, PROJECT_NUMBER)

    # Scope-leak fixtures on TRACK15-11B-OTHER:
    other_dr = await _ensure_daily_report(db, run_id, PROJECT_NUMBER_OTHER, "track15.11b.cert.other@mascicert.local")
    ledger["rows"]["scope_leak"] = {
        "daily_report": other_dr,
        "photo": await _ensure_photo(db, run_id, PROJECT_NUMBER_OTHER, other_dr),
        "incident": await _ensure_incident(db, run_id, PROJECT_NUMBER_OTHER),
    }

    logger.info(f"# seed complete · rows={sum(1 for v in ledger['rows'].values() if v)}")
    return ledger


async def verify(db) -> Dict[str, Any]:
    counts = {}
    for coll in ("user_directory", "jobs_master", "project_team_assignments",
                 "daily_reports", "job_photos", "incidents", "jha_records",
                 "equipment_inspections"):
        c = await db[coll].count_documents({"cert_track": CERT_TRACK})
        counts[coll] = c
    return {"mode": "verify", "ts": _now(), "counts": counts}


async def rollback(db) -> Dict[str, Any]:
    deleted = {}
    for coll in ("daily_reports", "job_photos", "incidents", "jha_records",
                 "equipment_inspections", "project_team_assignments",
                 "jobs_master", "user_directory"):
        r = await db[coll].delete_many({"cert_track": CERT_TRACK})
        deleted[coll] = r.deleted_count
    return {"mode": "rollback", "ts": _now(), "deleted": deleted}


def _write_ledger(mode, payload):
    LEDGER_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    path = LEDGER_DIR / f"track_15_11b_{mode}_{ts}.json"
    path.write_text(json.dumps(payload, indent=2, default=str))
    logger.info(f"# ledger: {path}")
    return path


def cli_args(argv=None):
    p = argparse.ArgumentParser()
    p.add_argument("--seed", action="store_true")
    p.add_argument("--verify", action="store_true")
    p.add_argument("--rollback", action="store_true")
    return p.parse_args(argv)


async def main(args):
    mongo_url = os.environ.get("MONGO_URL")
    db_name = os.environ.get("DB_NAME") or "masci_safety_preview"
    app_env = os.environ.get("APP_ENV") or "preview"
    if not mongo_url:
        print("# MONGO_URL is required", file=sys.stderr); return 2
    err = _validate_env(args, app_env, db_name)
    if err:
        print(f"# SAFETY GUARD: {err}", file=sys.stderr); return 2
    client = AsyncIOMotorClient(mongo_url)
    db = client[db_name]
    logger.info(f"# TRACK 15.11B · db={db_name} env={app_env}")
    run_id = str(uuid.uuid4())

    if args.seed:
        _write_ledger("seed", await seed(db, run_id))
    if args.verify or not (args.seed or args.rollback):
        _write_ledger("verify", await verify(db))
    if args.rollback:
        _write_ledger("rollback", await rollback(db))
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(asyncio.run(main(cli_args())))
