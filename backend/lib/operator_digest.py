"""lib/operator_digest.py · iter431 · Phase 29 · Part 6.

Weekly plaintext operator situational-awareness digest.

Doctrine
--------
- Plain text · NOT HTML · NOT a dashboard · NOT a report.
- 4-line "is the platform alive?" summary the operator can read on
  their phone in under 10 seconds.
- Reuses existing endpoints (persistence-health, storage-summary,
  legacy-imports audit, backup_runs) — no new collection.
- Sent Monday mornings via Resend (same wire as safety_digest).
- Generator endpoint returns the same plaintext so the operator can
  `curl` it on-demand.

Example output:

    MASCI Operations · Weekly Digest · 2026-05-26 14:00 UTC

    Atlas:                  GREEN (mongo 8.0.23 · 121 collections)
    Last backup:            3h ago (ok=true · size=14.2 MB · → r2)
    Attachments:            70 · 100% R2-backed
    Storage growth (30d):   1.2 MB · projected 90d: 3.6 MB
    Evidence accesses (7d): 12
    Drift warnings:         none

    All systems calm.

That is the entire surface. Nothing else.
"""
from __future__ import annotations

import asyncio
import logging
import os
from datetime import datetime, timedelta, timezone
from typing import Any, Awaitable, Callable, Dict, Optional

logger = logging.getLogger("operator_digest")


def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


def _fmt_bytes(n: Optional[int]) -> str:
    if not n:
        return "0 B"
    units = ["B", "KB", "MB", "GB", "TB"]
    val = float(n)
    for u in units:
        if val < 1024 or u == units[-1]:
            return f"{val:.1f} {u}"
        val /= 1024
    return f"{n} B"


def _fmt_age(ts_iso: Optional[str]) -> str:
    if not ts_iso:
        return "—"
    try:
        ts = datetime.fromisoformat(str(ts_iso).replace("Z", "+00:00"))
    except Exception:
        return ts_iso
    delta = _now_utc() - ts
    secs = max(0, int(delta.total_seconds()))
    if secs < 3600:
        return f"{secs // 60}m ago"
    if secs < 86400:
        return f"{secs // 3600}h ago"
    return f"{secs // 86400}d ago"


async def build_weekly_digest_payload(db) -> Dict[str, Any]:
    """Gather every fact the digest needs. Never raises — every field
    falls back to `None` on probe failure."""
    payload: Dict[str, Any] = {
        "captured_at": _now_utc().isoformat(),
        "atlas": {"connected": False, "mongo_version": None, "collections": 0},
        "last_backup": None,
        "attachments": {"total": 0, "r2_backed": 0, "migrated_pct": 0.0,
                        "total_size_bytes": 0},
        "growth_30d": {"count": 0, "bytes": 0,
                       "projected_90d_count": 0, "projected_90d_bytes": 0},
        "evidence_accesses_7d": 0,
        "drift_warnings": 0,
        "drift_reason": "",
    }

    # Atlas connectivity
    try:
        info = await db.command("buildInfo")
        names = await db.list_collection_names()
        payload["atlas"] = {
            "connected": True,
            "mongo_version": info.get("version"),
            "collections": len(names),
        }
    except Exception:
        pass

    # Last successful backup
    # iter440 · Phase 31.2 health-lock · the scheduler writes every run
    # into `backup_health` (NOT `backup_runs`). Filter to rows that
    # actually produced a zip (filename != null) so the digest never
    # surfaces an `r2-usage-alert` quota probe as if it were a backup.
    try:
        row = await db.backup_health.find_one(
            {"ok": True, "filename": {"$nin": [None, ""]}},
            sort=[("ts", -1)],
            projection={"_id": 0, "ts": 1, "mode": 1, "size_bytes": 1,
                        "filename": 1, "records": 1, "error": 1},
        )
        if row:
            payload["last_backup"] = {
                "ts": row.get("ts"),
                "ok": True,  # filtered above
                "kind": row.get("mode"),
                "size_bytes": row.get("size_bytes"),
                "filename": row.get("filename"),
                "records": row.get("records"),
                "error": row.get("error"),
            }
    except Exception:
        pass

    # Attachment storage summary (mirror the storage_summary route logic)
    try:
        pipeline = [
            {"$match": {"tenant_id": "masci"}},
            {"$group": {
                "_id": {"$cond": [
                    {"$eq": ["$storage_backend", "r2"]}, "r2",
                    {"$cond": [
                        {"$or": [
                            {"$eq": ["$storage_backend", "inline_b64"]},
                            {"$and": [
                                {"$ne": ["$data_b64", None]},
                                {"$ne": ["$data_b64", ""]},
                            ]},
                        ]}, "inline_b64", "unknown",
                    ]},
                ]},
                "count": {"$sum": 1},
                "bytes": {"$sum": {"$ifNull": ["$size_bytes", 0]}},
            }},
        ]
        total_count = 0
        r2_count = 0
        total_size = 0
        async for row in db.operational_attachments.aggregate(pipeline):
            total_count += row.get("count", 0)
            total_size += row.get("bytes", 0)
            if row["_id"] == "r2":
                r2_count = row.get("count", 0)
        payload["attachments"] = {
            "total": total_count,
            "r2_backed": r2_count,
            "migrated_pct": round(100 * r2_count / total_count, 2) if total_count else 100.0,
            "total_size_bytes": total_size,
        }
    except Exception:
        pass

    # 30-day growth
    try:
        cutoff = (_now_utc() - timedelta(days=30)).isoformat()
        rec_pipeline = [
            {"$match": {"tenant_id": "masci", "uploaded_at": {"$gte": cutoff}}},
            {"$group": {"_id": None,
                        "count": {"$sum": 1},
                        "bytes": {"$sum": {"$ifNull": ["$size_bytes", 0]}}}},
        ]
        async for row in db.operational_attachments.aggregate(rec_pipeline):
            cnt = row.get("count", 0)
            byt = row.get("bytes", 0)
            payload["growth_30d"] = {
                "count": cnt,
                "bytes": byt,
                "projected_90d_count": cnt * 3,
                "projected_90d_bytes": byt * 3,
            }
    except Exception:
        pass

    # Evidence access count (last 7 days)
    try:
        cutoff = (_now_utc() - timedelta(days=7)).isoformat()
        payload["evidence_accesses_7d"] = await db.legacy_import_audit.count_documents(
            {"action": "evidence_accessed", "timestamp": {"$gte": cutoff}},
        )
    except Exception:
        pass

    # Drift watch heartbeat (last 36h)
    # iter440 · Phase 31.2 health-lock · the complete-archive scheduler
    # writes snapshots to `backup_drift_history` with a `recorded_at`
    # datetime field (NOT `backup_drift_watch.ts/updated_at`).
    try:
        cutoff = _now_utc() - timedelta(hours=36)
        heart = await db.backup_drift_history.find_one(
            {"recorded_at": {"$gte": cutoff}},
        )
        if not heart:
            payload["drift_warnings"] = 1
            payload["drift_reason"] = "no heartbeat in the last 36h"
    except Exception:
        pass

    return payload


def render_digest_plaintext(p: Dict[str, Any]) -> str:
    """Render the payload into the doctrine-mandated 4-line plaintext."""
    lines = []
    lines.append(f"MASCI Operations · Weekly Digest · {p.get('captured_at', '')}")
    lines.append("")
    atlas = p.get("atlas") or {}
    if atlas.get("connected"):
        lines.append(
            f"Atlas:                  GREEN "
            f"(mongo {atlas.get('mongo_version') or '?'} · "
            f"{atlas.get('collections', 0)} collections)"
        )
    else:
        lines.append("Atlas:                  RED · connection probe failed")

    lb = p.get("last_backup")
    if lb:
        dest_str = ",".join(lb.get("destinations") or []) or "local"
        lines.append(
            f"Last backup:            {_fmt_age(lb.get('ts'))} "
            f"(ok={str(bool(lb.get('ok'))).lower()} · size={_fmt_bytes(lb.get('size_bytes'))} "
            f"· → {dest_str})"
        )
    else:
        lines.append("Last backup:            none recorded")

    att = p.get("attachments") or {}
    lines.append(
        f"Attachments:            {att.get('total', 0)} · "
        f"{att.get('migrated_pct', 0):.1f}% R2-backed"
    )

    g = p.get("growth_30d") or {}
    lines.append(
        f"Storage growth (30d):   {_fmt_bytes(g.get('bytes'))} · "
        f"projected 90d: {_fmt_bytes(g.get('projected_90d_bytes'))}"
    )

    lines.append(f"Evidence accesses (7d): {p.get('evidence_accesses_7d', 0)}")
    if p.get("drift_warnings"):
        lines.append(f"Drift warnings:         {p.get('drift_warnings')} · "
                     f"{p.get('drift_reason') or ''}")
    else:
        lines.append("Drift warnings:         none")
    lines.append("")
    # Calm verdict — single sentence. Operator owns interpretation.
    everything_green = (
        atlas.get("connected")
        and lb and lb.get("ok")
        and att.get("migrated_pct", 0) >= 99.0
        and not p.get("drift_warnings")
    )
    lines.append("All systems calm." if everything_green
                 else "Operator review recommended.")
    return "\n".join(lines)


def _enabled() -> bool:
    return (os.environ.get("OPERATOR_DIGEST_ENABLED") or "true").strip().lower() in (
        "1", "true", "yes", "on"
    )


def _seconds_until_next_send() -> float:
    """Mirror safety_digest cron: weekday (0=Mon) + hour UTC. Defaults
    to Monday 14:00 UTC (≈ Monday morning ET)."""
    try:
        hour = int(os.environ.get("OPERATOR_DIGEST_HOUR_UTC", "14"))
        weekday = int(os.environ.get("OPERATOR_DIGEST_WEEKDAY", "0"))
    except ValueError:
        hour, weekday = 14, 0
    hour = max(0, min(23, hour))
    weekday = max(0, min(6, weekday))
    now = _now_utc()
    target = now.replace(hour=hour, minute=0, second=0, microsecond=0)
    days_ahead = (weekday - now.weekday()) % 7
    if days_ahead == 0 and target <= now:
        days_ahead = 7
    target = target + timedelta(days=days_ahead)
    return (target - now).total_seconds()


EmailFn = Callable[[str, str, str], Awaitable[Any]]


async def operator_digest_scheduler_loop(
    db,
    send_email_fn: Optional[EmailFn],
) -> None:
    """Long-running cron · never raises out · same shape as
    safety_digest_scheduler_loop so it cohabits well in supervisor.

    iter445 · Sprint · Scheduler Hardening — dedup via scheduler_runs.
    """
    from lib.scheduler_runs import claim_slot, mark_completed, mark_failed
    while True:
        try:
            if not _enabled():
                await asyncio.sleep(3600)
                continue
            wait_s = _seconds_until_next_send()
            logger.info(f"[operator-digest] sleeping {wait_s/3600:.1f}h until next send")
            await asyncio.sleep(max(60.0, wait_s))
            slot_dt = _now_utc().replace(minute=0, second=0, microsecond=0)
            slot_key = slot_dt.isoformat()
            claim = await claim_slot(db, "operator_digest", slot_key)
            if claim is None:
                logger.warning(f"[operator-digest] slot {slot_key} already sent — dedup skip")
                continue
            try:
                payload = await build_weekly_digest_payload(db)
                text = render_digest_plaintext(payload)
                # Track 15.66 · DB-first recipient resolution. Flag OFF
                # produces identical legacy behaviour.
                def _legacy_recipients() -> list[str]:
                    raw = (os.environ.get("OPERATOR_DIGEST_RECIPIENTS")
                           or os.environ.get("SAFETY_DIGEST_TO_EMAIL")
                           or "safety@mascigc.com").strip()
                    return [r.strip() for r in raw.split(",") if r.strip()]
                try:
                    from email_routing_v2 import resolve_and_audit as _v2_resolve  # noqa: PLC0415
                    _res = await _v2_resolve(
                        db,
                        "OPERATOR_DIGEST_RECIPIENTS",
                        legacy_provider=_legacy_recipients,
                        fallback_env_keys=["OPERATOR_DIGEST_RECIPIENTS", "SAFETY_DIGEST_TO_EMAIL"],
                        calling_module="operator_digest",
                    )
                    recipient_list = _res.to or _legacy_recipients()
                except Exception:
                    recipient_list = _legacy_recipients()
                if not recipient_list:
                    logger.info(f"[operator-digest] no recipients · skipping · payload preview=\n{text}")
                    await mark_completed(db, "operator_digest", slot_key, recipients=0,
                                         meta={"reason": "no_recipients"})
                    continue
                if send_email_fn is None:
                    logger.info(f"[operator-digest] no email fn · preview=\n{text}")
                    await mark_completed(db, "operator_digest", slot_key, recipients=0,
                                         meta={"reason": "no_email_fn"})
                    continue
                # HTML-wrap the plaintext so Resend renders it as a code
                # block (preserves alignment in mail clients).
                html_body = (
                    "<pre style=\"font-family: ui-monospace, SFMono-Regular, "
                    "Menlo, monospace; white-space: pre-wrap; font-size: 13px; "
                    "line-height: 1.5;\">"
                    + text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
                    + "</pre>"
                )
                sent_count = 0
                for r in recipient_list:
                    try:
                        await send_email_fn(r, "[MASCI] Weekly Operations Digest", html_body)
                        logger.info(f"[operator-digest] sent to {r}")
                        sent_count += 1
                    except Exception as e:  # noqa: BLE001
                        logger.warning(f"[operator-digest] send to {r} failed: {e}")
                await mark_completed(
                    db, "operator_digest", slot_key,
                    recipients=sent_count,
                    meta={"to": recipient_list, "attempted": len(recipient_list)},
                )
            except Exception as send_err:  # noqa: BLE001
                logger.exception(f"[operator-digest] send failed: {send_err}")
                await mark_failed(db, "operator_digest", slot_key, error=str(send_err))
                raise
        except asyncio.CancelledError:
            raise
        except Exception as e:  # noqa: BLE001
            logger.exception(f"[operator-digest] loop crashed: {e}")
            await asyncio.sleep(600)
