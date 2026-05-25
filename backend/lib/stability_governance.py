"""lib/stability_governance.py · iter431 · Phase 29 · Part 4.

Calm, doctrine-restraint cleanup of EXPIRED operational artifacts.

Doctrine
--------
This module is NOT a data shredder. It is a janitor.

What it DOES touch:
    • dispatch_driver_sessions   — revoked or older than 14 days
    • webauthn_challenges        — older than 24 hours (ceremony timeout)
    • temp_upload_chunks         — older than 24 hours
    • offline_replay_records     — `state=replayed` AND older than 7 days

What it NEVER touches:
    • dispatch_assignments       — operational truth · NEVER deleted
    • dispatch_continuity_events — operational memory · NEVER deleted
    • operational_attachments    — append-only proof · NEVER deleted
    • legacy_imports / audit     — accountability · NEVER deleted
    • backup_runs / backup_drift_watch — survivability · NEVER deleted
    • Any user / passkey / role / tenant / project / equipment record

Each cleanup call returns a dict so the operator can see what was
swept. No exceptions are ever surfaced — a stability sweep that fails
must NEVER crash the platform.

TTL indexes are added in `ensure_stability_ttls(db)`. Where the
existing module-level index code already declares a TTL we DO NOT
add a second one — collisions log a warning and continue.
"""
from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Dict

logger = logging.getLogger("stability_governance")


# ─── Retention windows · doctrine-locked ──────────────────────────
DRIVER_SESSION_GRACE_DAYS         = 14   # post-revocation grace
WEBAUTHN_CHALLENGE_GRACE_HOURS    = 24   # ceremony timeout safety
TEMP_UPLOAD_CHUNK_GRACE_HOURS     = 24
OFFLINE_REPLAY_GRACE_DAYS         = 7    # only AFTER state=replayed


def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


def _iso(dt: datetime) -> str:
    return dt.isoformat()


# ─── TTL index ensures ────────────────────────────────────────────
async def ensure_stability_ttls(db) -> Dict[str, Any]:
    """Idempotent TTL index ensures. Safe to call on every startup.
    Returns a report dict for the boot log."""
    report = {"created": [], "skipped": [], "errors": []}

    targets = [
        # (collection, field, expireAfterSeconds, index_name)
        ("webauthn_challenges",   "created_at", WEBAUTHN_CHALLENGE_GRACE_HOURS * 3600,
         "ttl_webauthn_challenges_created_at"),
        ("temp_upload_chunks",    "created_at", TEMP_UPLOAD_CHUNK_GRACE_HOURS * 3600,
         "ttl_temp_upload_chunks_created_at"),
    ]
    for coll, field, ttl_seconds, idx_name in targets:
        try:
            await db[coll].create_index(
                field, expireAfterSeconds=ttl_seconds, name=idx_name,
            )
            report["created"].append(idx_name)
        except Exception as e:  # noqa: BLE001
            # Existing index with different options will raise — log
            # and continue; we never overwrite an existing TTL.
            msg = str(e).lower()
            if "already exists" in msg or "index already exists" in msg:
                report["skipped"].append(idx_name)
            else:
                report["errors"].append({"idx": idx_name, "error": str(e)[:200]})
    return report


# ─── Cleanup sweepers · each is independently safe ─────────────────
async def sweep_driver_sessions(db, *, dry_run: bool = False) -> Dict[str, Any]:
    """Delete dispatch_driver_sessions that are revoked or older than
    `DRIVER_SESSION_GRACE_DAYS`. Active (non-revoked, recent) sessions
    are NEVER touched — operational continuity guard."""
    cutoff = _iso(_now_utc() - timedelta(days=DRIVER_SESSION_GRACE_DAYS))
    q = {
        "$or": [
            {"revoked_at": {"$exists": True, "$ne": None}},
            {"created_at": {"$lt": cutoff}},
        ],
    }
    try:
        count = await db.dispatch_driver_sessions.count_documents(q)
        if dry_run:
            return {"target": "dispatch_driver_sessions", "would_delete": count,
                    "cutoff": cutoff, "applied": False}
        res = await db.dispatch_driver_sessions.delete_many(q)
        return {"target": "dispatch_driver_sessions",
                "deleted": getattr(res, "deleted_count", 0),
                "cutoff": cutoff, "applied": True}
    except Exception as e:  # noqa: BLE001
        return {"target": "dispatch_driver_sessions", "error": str(e)[:240]}


async def sweep_webauthn_challenges(db, *, dry_run: bool = False) -> Dict[str, Any]:
    cutoff = _iso(_now_utc() - timedelta(hours=WEBAUTHN_CHALLENGE_GRACE_HOURS))
    q = {"created_at": {"$lt": cutoff}}
    try:
        count = await db.webauthn_challenges.count_documents(q)
        if dry_run:
            return {"target": "webauthn_challenges", "would_delete": count,
                    "cutoff": cutoff, "applied": False}
        res = await db.webauthn_challenges.delete_many(q)
        return {"target": "webauthn_challenges",
                "deleted": getattr(res, "deleted_count", 0),
                "cutoff": cutoff, "applied": True}
    except Exception as e:  # noqa: BLE001
        return {"target": "webauthn_challenges", "error": str(e)[:240]}


async def sweep_temp_upload_chunks(db, *, dry_run: bool = False) -> Dict[str, Any]:
    cutoff = _iso(_now_utc() - timedelta(hours=TEMP_UPLOAD_CHUNK_GRACE_HOURS))
    q = {"created_at": {"$lt": cutoff}}
    try:
        count = await db.temp_upload_chunks.count_documents(q)
        if dry_run:
            return {"target": "temp_upload_chunks", "would_delete": count,
                    "cutoff": cutoff, "applied": False}
        res = await db.temp_upload_chunks.delete_many(q)
        return {"target": "temp_upload_chunks",
                "deleted": getattr(res, "deleted_count", 0),
                "cutoff": cutoff, "applied": True}
    except Exception as e:  # noqa: BLE001
        return {"target": "temp_upload_chunks", "error": str(e)[:240]}


async def sweep_offline_replay_records(db, *, dry_run: bool = False) -> Dict[str, Any]:
    """Only sweep records that have ALREADY been replayed successfully
    AND are older than the grace window. Unreplayed records are
    operational truth and NEVER touched, no matter how old."""
    cutoff = _iso(_now_utc() - timedelta(days=OFFLINE_REPLAY_GRACE_DAYS))
    q = {
        "state": "replayed",
        "created_at": {"$lt": cutoff},
    }
    try:
        count = await db.offline_replay_records.count_documents(q)
        if dry_run:
            return {"target": "offline_replay_records", "would_delete": count,
                    "cutoff": cutoff, "applied": False}
        res = await db.offline_replay_records.delete_many(q)
        return {"target": "offline_replay_records",
                "deleted": getattr(res, "deleted_count", 0),
                "cutoff": cutoff, "applied": True}
    except Exception as e:  # noqa: BLE001
        return {"target": "offline_replay_records", "error": str(e)[:240]}


async def run_stability_sweep(db, *, dry_run: bool = False) -> Dict[str, Any]:
    """Run all sweepers and aggregate the result. Never raises."""
    started = _iso(_now_utc())
    results = []
    for fn in (sweep_driver_sessions,
               sweep_webauthn_challenges,
               sweep_temp_upload_chunks,
               sweep_offline_replay_records):
        try:
            results.append(await fn(db, dry_run=dry_run))
        except Exception as e:  # noqa: BLE001
            results.append({"target": fn.__name__, "error": str(e)[:240]})
    return {
        "started_at": started,
        "finished_at": _iso(_now_utc()),
        "dry_run": dry_run,
        "results": results,
    }
