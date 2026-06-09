"""
backup_verification.py — Weekly Backup Verification Cron (iter79)
=================================================================
A scheduled health-check that verifies the R2 backup archive is alive,
recent, and well-sized — then emails a clean PASS/FAIL summary to the
admin distribution list.

Differs from the existing **watchdog** (`_backup_watchdog_check`) in
that this:
  - Always runs on a weekly cadence (Mon 14:00 UTC by default), even
    when backups are healthy — gives the operator a positive heartbeat
    instead of only firing when something breaks.
  - Cross-checks BOTH the local MongoDB `backup_health` ledger AND the
    real Cloudflare R2 `backups/` prefix — catches the case where the
    backend thinks it backed up but R2 actually rejected the upload.
  - Returns + emails a full health report (record counts, file sizes,
    R2 archive list, last-successful timestamps per mode).

Env knobs:
  - BACKUP_VERIFICATION_ENABLED          — "true" (default) to run the
                                            weekly cron at startup.
  - BACKUP_VERIFICATION_DAY              — 0..6 (Mon=0); default 0
  - BACKUP_VERIFICATION_HOUR_UTC         — 0..23; default 14
                                            (= 10:00 AM ET on Mondays)
  - BACKUP_VERIFICATION_TO               — comma-separated recipients.
                                            Falls back to BACKUP_EMAIL_TO,
                                            then SAFETY_EMAIL_TO.
  - BACKUP_VERIFICATION_MAX_AGE_HOURS    — fail if newest R2 archive is
                                            older than N hours. Default 36.
"""
from __future__ import annotations

import asyncio
import logging
import os
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from operational_footer import render_operational_footer_html

logger = logging.getLogger(__name__)

DEFAULT_DAY_OF_WEEK = 0       # Monday
DEFAULT_HOUR_UTC = 14         # 14:00 UTC ≈ 10:00 AM ET Mon
DEFAULT_MAX_AGE_HOURS = 36


def _env_int(name: str, default: int) -> int:
    raw = (os.environ.get(name) or "").strip()
    try:
        return int(raw)
    except (TypeError, ValueError):
        return default


def _enabled() -> bool:
    return (os.environ.get("BACKUP_VERIFICATION_ENABLED") or "true").strip().lower() in ("1", "true", "yes", "on")


def _verification_recipients() -> List[str]:
    """Recipients fall through: BACKUP_VERIFICATION_TO → BACKUP_EMAIL_TO →
    SAFETY_EMAIL_TO. Returns empty list if none configured."""
    for key in ("BACKUP_VERIFICATION_TO", "BACKUP_EMAIL_TO", "SAFETY_EMAIL_TO"):
        raw = (os.environ.get(key) or "").strip()
        if raw:
            return [x.strip() for x in raw.split(",") if x.strip()]
    return []


def _humanize_size(num_bytes: int) -> str:
    if not num_bytes or num_bytes < 0:
        return "0 B"
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if num_bytes < 1024.0:
            return f"{num_bytes:.1f} {unit}"
        num_bytes /= 1024.0
    return f"{num_bytes:.1f} PB"


def _hours_since(iso_str: str) -> Optional[float]:
    if not iso_str:
        return None
    try:
        dt = datetime.fromisoformat(iso_str.replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return (datetime.now(timezone.utc) - dt).total_seconds() / 3600.0
    except (ValueError, TypeError):
        return None


# ─────────────────────────────────────────────────────────────────────
# R2 archive enumeration
# ─────────────────────────────────────────────────────────────────────
async def list_r2_backup_archives(prefix: str = "backups/") -> List[Dict[str, Any]]:
    """List every object under r2://<bucket>/backups/. Returns
    [{key, size_bytes, last_modified_iso}], newest first. Empty list when
    R2 is not configured."""
    try:
        from photo_storage import is_configured as _ps_cfg, _client, _bucket
    except Exception:  # noqa: BLE001
        logger.warning("[verify] photo_storage import failed")
        return []

    if not _ps_cfg():
        return []

    s3 = _client()
    if s3 is None:
        return []

    bucket = _bucket()
    out: List[Dict[str, Any]] = []
    try:
        # boto3 list_objects_v2 is sync — wrap in to_thread. Paginate by
        # ContinuationToken so we handle >1000 objects defensively.
        token: Optional[str] = None
        while True:
            kwargs: Dict[str, Any] = {"Bucket": bucket, "Prefix": prefix, "MaxKeys": 1000}
            if token:
                kwargs["ContinuationToken"] = token
            resp = await asyncio.to_thread(s3.list_objects_v2, **kwargs)
            for it in resp.get("Contents") or []:
                lm = it.get("LastModified")
                out.append({
                    "key": it.get("Key"),
                    "size_bytes": int(it.get("Size") or 0),
                    "last_modified_iso": lm.isoformat() if lm else None,
                })
            if resp.get("IsTruncated"):
                token = resp.get("NextContinuationToken")
                if not token:
                    break
            else:
                break
    except Exception as e:  # noqa: BLE001
        logger.exception(f"[verify] R2 list_objects_v2 failed: {e}")
        return []

    out.sort(key=lambda r: r.get("last_modified_iso") or "", reverse=True)
    return out


# ─────────────────────────────────────────────────────────────────────
# Build verification report
# ─────────────────────────────────────────────────────────────────────
async def build_verification_report(db) -> Dict[str, Any]:
    """Assemble the full verification report. Cross-checks R2 archives
    against the local backup_health ledger and applies the max-age rule.
    Returns a single dict the email renderer + endpoint consumers all use."""

    max_age_hours = _env_int("BACKUP_VERIFICATION_MAX_AGE_HOURS", DEFAULT_MAX_AGE_HOURS)
    now = datetime.now(timezone.utc)

    # ── 1. R2 archives ─────────────────────────────────────────────
    archives = await list_r2_backup_archives()
    r2_configured = bool(archives) or False
    try:
        from photo_storage import is_configured as _ps_cfg
        r2_configured = _ps_cfg()
    except Exception:  # noqa: BLE001
        pass

    newest = archives[0] if archives else None
    newest_age_hrs = _hours_since(newest["last_modified_iso"]) if newest else None
    total_size_bytes = sum(a["size_bytes"] for a in archives)

    r2_status = "ok"
    r2_issues: List[str] = []
    if not r2_configured:
        r2_status = "not_configured"
        r2_issues.append("Cloudflare R2 not configured on this deployment.")
    elif not archives:
        r2_status = "empty"
        r2_issues.append("R2 bucket has zero objects under backups/.")
    elif newest_age_hrs is None:
        r2_status = "warn"
        r2_issues.append("Newest R2 archive has no last-modified timestamp.")
    elif newest_age_hrs > max_age_hours:
        r2_status = "stale"
        r2_issues.append(
            f"Newest R2 archive is {newest_age_hrs:.1f}h old "
            f"(threshold: {max_age_hours}h)."
        )

    # ── 2. Local backup_health ledger ──────────────────────────────
    # BACKUP-FIX-001 · Option α — widen the "successful full backup"
    # acceptance set to also include the R2 hourly pipeline.
    #   • full          → disk-based full zip (legacy)
    #   • lite          → disk-based slim zip (OOM-watermark fallback)
    #   • complete-r2   → R2 hourly archive (current production cadence)
    # Historical rows untouched; writer modes unchanged; archive naming
    # unchanged. See /app/memory/BACKUP_AUDIT_001_FORENSIC_REPORT.md.
    FULL_BACKUP_MODES = ("full", "lite", "complete-r2")

    last_full: Optional[Dict[str, Any]] = None
    last_r2: Optional[Dict[str, Any]] = None
    last_failure: Optional[Dict[str, Any]] = None
    recent_runs: List[Dict[str, Any]] = []
    try:
        async for r in db.backup_health.find({}, {"_id": 0}).sort("ts", -1).limit(20):
            recent_runs.append(r)
            if r.get("ok"):
                mode = (r.get("mode") or "").lower()
                if last_full is None and mode in FULL_BACKUP_MODES:
                    last_full = r
                if last_r2 is None and "r2" in mode:
                    last_r2 = r
            else:
                if last_failure is None:
                    last_failure = r
    except Exception as e:  # noqa: BLE001
        logger.warning(f"[verify] backup_health read failed: {e}")

    ledger_status = "ok"
    ledger_issues: List[str] = []
    if last_full is None:
        ledger_status = "warn"
        ledger_issues.append("No successful full backup recorded in last 20 runs.")
    elif _hours_since(last_full.get("ts")) and _hours_since(last_full["ts"]) > max_age_hours:
        ledger_status = "stale"
        ledger_issues.append(
            f"Last successful full/lite backup was "
            f"{_hours_since(last_full['ts']):.1f}h ago."
        )

    # ── 3. MongoDB record counts (proves the data we're backing up exists) ──
    try:
        from server import EXPORTABLE_KINDS  # late import — avoid circular
        kinds = list(EXPORTABLE_KINDS.items())
    except Exception:  # noqa: BLE001
        kinds = [
            ("inspection", "inspections"),
            ("meeting", "meetings"),
            ("incident", "incidents"),
            ("jha", "job_hazard_plans"),
            ("daily-report", "daily_reports"),
            ("equipment-inspection", "equipment_inspections"),
            ("qaqc", "qaqc_inspections"),
        ]
    per_collection_counts: Dict[str, int] = {}
    total_records = 0
    try:
        for kind, coll_name in kinds:
            try:
                c = await db[coll_name].count_documents({})
            except Exception:
                c = 0
            per_collection_counts[kind] = c
            total_records += c
    except Exception as e:  # noqa: BLE001
        logger.warning(f"[verify] record counts failed: {e}")

    # ── 4. Overall verdict ─────────────────────────────────────────
    if r2_status == "ok" and ledger_status == "ok":
        verdict = "pass"
    elif r2_status in ("stale", "empty") or ledger_status == "stale":
        verdict = "fail"
    else:
        verdict = "warn"

    return {
        "ts": now.isoformat(),
        "verdict": verdict,                  # pass | warn | fail
        "r2": {
            "configured": r2_configured,
            "status": r2_status,
            "issues": r2_issues,
            "archive_count": len(archives),
            "newest": newest,
            "newest_age_hrs": newest_age_hrs,
            "total_size_bytes": total_size_bytes,
            "total_size_human": _humanize_size(total_size_bytes),
            "max_age_threshold_hrs": max_age_hours,
            "all_archives": archives[:25],   # cap for emails
            "all_archives_truncated": len(archives) > 25,
        },
        "ledger": {
            "status": ledger_status,
            "issues": ledger_issues,
            "last_full": last_full,
            "last_r2": last_r2,
            "last_failure": last_failure,
            "recent_runs_count": len(recent_runs),
        },
        "data": {
            "per_collection_counts": per_collection_counts,
            "total_records": total_records,
        },
    }


# ─────────────────────────────────────────────────────────────────────
# Email rendering
# ─────────────────────────────────────────────────────────────────────
def _verdict_badge(verdict: str) -> str:
    return {
        "pass": "✅ HEALTHY",
        "warn": "⚠ WARNING",
        "fail": "🚨 FAILED",
    }.get(verdict, "ℹ INFO")


def _verdict_color(verdict: str) -> str:
    return {
        "pass": "#15803d",  # green-700
        "warn": "#b45309",  # amber-700
        "fail": "#c8102e",  # red
    }.get(verdict, "#475569")


def render_verification_subject(report: Dict[str, Any]) -> str:
    # iter437 IV-BETA.3A · doctrine A.I (no non-reserved emoji) + A.III
    # severe-tier prefix on hard failure. See COMMUNICATION_UNIFICATION_DOCTRINE.md.
    verdict = report.get("verdict") or "info"
    archives = report["r2"]["archive_count"]
    if verdict == "pass":
        return f"[MASCI \u00b7 BACKUP] Weekly Verification \u00b7 {archives} archives healthy"
    if verdict == "fail":
        return "\U0001F6A8 BACKUP VERIFICATION FAILED \u00b7 check immediately"
    return f"[MASCI \u00b7 BACKUP] Weekly Verification \u00b7 {archives} archives \u00b7 issues detected"


def render_verification_email_html(report: Dict[str, Any]) -> str:
    """Brand-matched HTML email. Mirrors render_email_html chrome from
    pdf_render.py (MASCI Operations Platform eyebrow, Inc. footer,
    ForgedOps™ attribution)."""
    from html import escape as _esc

    verdict = report.get("verdict") or "info"
    badge = _verdict_badge(verdict)
    badge_color = _verdict_color(verdict)

    r2 = report["r2"]
    ledger = report["ledger"]
    data = report["data"]

    # ── R2 archive list rows ──
    archive_rows = ""
    for a in r2["all_archives"]:
        key = _esc(a.get("key") or "")
        size_h = _humanize_size(a.get("size_bytes") or 0)
        lm = a.get("last_modified_iso") or ""
        age_hrs = _hours_since(lm)
        age_label = f"{age_hrs:.1f}h ago" if age_hrs is not None else "—"
        archive_rows += (
            f"<tr>"
            f"<td style='padding:6px 10px;border-bottom:1px solid #e2e8f0;font-family:Courier New,monospace;font-size:11px;color:#0f172a'>{key}</td>"
            f"<td style='padding:6px 10px;border-bottom:1px solid #e2e8f0;font-size:11px;color:#475569;text-align:right'>{size_h}</td>"
            f"<td style='padding:6px 10px;border-bottom:1px solid #e2e8f0;font-size:11px;color:#475569;text-align:right'>{age_label}</td>"
            f"</tr>"
        )
    if not archive_rows:
        archive_rows = (
            "<tr><td colspan='3' style='padding:14px;text-align:center;"
            "font-size:12px;color:#94a3b8;font-style:italic'>"
            "No R2 archives found.</td></tr>"
        )
    if r2.get("all_archives_truncated"):
        archive_rows += (
            "<tr><td colspan='3' style='padding:8px 10px;text-align:center;"
            "font-size:10px;color:#94a3b8;font-style:italic'>"
            f"… {r2['archive_count'] - 25} more archives not shown.</td></tr>"
        )

    # ── Issues list (combined R2 + ledger) ──
    all_issues = list(r2.get("issues") or []) + list(ledger.get("issues") or [])
    issues_html = ""
    if all_issues:
        items = "".join(f"<li style='margin:4px 0'>{_esc(i)}</li>" for i in all_issues)
        issues_html = (
            f"<div style='margin:18px 0;padding:12px 14px;background:#fef2f2;"
            f"border-left:3px solid #c8102e;color:#991b1b;font-size:13px;"
            f"font-weight:500;line-height:1.5;'>"
            f"<strong>Issues detected:</strong>"
            f"<ul style='margin:6px 0 0 0;padding-left:18px'>{items}</ul>"
            f"</div>"
        )

    # ── Recent runs summary ──
    last_full = ledger.get("last_full") or {}
    last_r2 = ledger.get("last_r2") or {}
    last_failure = ledger.get("last_failure") or {}

    def _fmt_ledger_row(label: str, doc: Dict[str, Any]) -> str:
        if not doc:
            return (
                f"<tr><td style='padding:5px 0;font-size:11px;font-family:Courier New,monospace;"
                f"text-transform:uppercase;letter-spacing:0.15em;color:#94a3b8;'>{label}</td>"
                f"<td style='padding:5px 0;font-size:12px;color:#94a3b8;font-style:italic'>—</td></tr>"
            )
        ts = doc.get("ts") or ""
        age = _hours_since(ts)
        age_label = f" · {age:.1f}h ago" if age is not None else ""
        size_h = _humanize_size(doc.get("size_bytes") or 0)
        records = doc.get("records") or 0
        return (
            f"<tr><td style='padding:5px 0;font-size:11px;font-family:Courier New,monospace;"
            f"text-transform:uppercase;letter-spacing:0.15em;color:#475569;'>{label}</td>"
            f"<td style='padding:5px 0;font-size:12px;color:#0f172a'>"
            f"<code style='font-size:11px'>{_esc(doc.get('filename') or '')}</code>"
            f" · {size_h} · {records:,} records{age_label}</td></tr>"
        )

    # ── Per-collection counts ──
    counts = data.get("per_collection_counts") or {}
    counts_chips = "".join(
        f"<span style='display:inline-block;margin:2px 4px 2px 0;padding:2px 8px;"
        f"background:#f1f5f9;border-radius:4px;font-size:11px;color:#475569;'>"
        f"{_esc(k)}: <strong style='color:#0f172a'>{v:,}</strong></span>"
        for k, v in sorted(counts.items())
    ) or "<span style='font-size:11px;color:#94a3b8;font-style:italic'>none</span>"

    return f"""<!doctype html>
<html><body style="margin:0;padding:24px;background:#f8fafc;font-family:Helvetica,Arial,sans-serif;color:#0f172a;">
  <table style="max-width:640px;margin:0 auto;background:#fff;border:1px solid #e2e8f0;border-radius:6px;padding:24px;">
    <tr><td>
      <div style="font-family:'Courier New',monospace;font-size:11px;letter-spacing:0.25em;text-transform:uppercase;color:#c8102e;font-weight:700;">MASCI Operations Platform</div>
      <h1 style="margin:8px 0 4px;font-size:24px;font-weight:900;letter-spacing:-0.02em;">Backup Verification Report</h1>
      <div style="font-family:'Courier New',monospace;font-size:11px;letter-spacing:0.18em;text-transform:uppercase;color:#475569;">
        Generated {_esc(report['ts'])}
      </div>

      <!-- Verdict banner -->
      <div style="margin:20px 0;padding:14px 16px;background:#f8fafc;border:2px solid {badge_color};border-radius:6px;text-align:center">
        <div style="font-family:'Courier New',monospace;font-size:11px;letter-spacing:0.25em;text-transform:uppercase;color:#475569;font-weight:bold">Overall Status</div>
        <div style="margin-top:6px;font-size:22px;font-weight:900;color:{badge_color};letter-spacing:0.02em">{badge}</div>
      </div>

      {issues_html}

      <!-- R2 Archive Summary -->
      <div style="margin-top:18px;font-family:'Courier New',monospace;font-size:11px;letter-spacing:0.18em;text-transform:uppercase;color:#475569;font-weight:bold">Cloudflare R2 Archives</div>
      <div style="margin-top:6px;font-size:13px;color:#0f172a">
        <strong>{r2['archive_count']}</strong> archives ·
        <strong>{r2['total_size_human']}</strong> total
        {'· newest: ' + f"{r2['newest_age_hrs']:.1f}h ago" if r2['newest_age_hrs'] is not None else ''}
      </div>
      <table style="margin-top:10px;width:100%;border-collapse:collapse;border:1px solid #e2e8f0;border-radius:4px">
        <thead>
          <tr style="background:#f8fafc">
            <th style="padding:8px 10px;text-align:left;font-size:10px;letter-spacing:0.15em;text-transform:uppercase;color:#475569;border-bottom:1px solid #e2e8f0">Archive</th>
            <th style="padding:8px 10px;text-align:right;font-size:10px;letter-spacing:0.15em;text-transform:uppercase;color:#475569;border-bottom:1px solid #e2e8f0">Size</th>
            <th style="padding:8px 10px;text-align:right;font-size:10px;letter-spacing:0.15em;text-transform:uppercase;color:#475569;border-bottom:1px solid #e2e8f0">Age</th>
          </tr>
        </thead>
        <tbody>{archive_rows}</tbody>
      </table>

      <!-- Local ledger summary -->
      <div style="margin-top:20px;font-family:'Courier New',monospace;font-size:11px;letter-spacing:0.18em;text-transform:uppercase;color:#475569;font-weight:bold">Local Backup Ledger (last entries)</div>
      <table style="margin-top:6px;width:100%;border-collapse:collapse">
        {_fmt_ledger_row('Last Full / Lite', last_full)}
        {_fmt_ledger_row('Last R2 Archive', last_r2)}
        {_fmt_ledger_row('Last Failure', last_failure)}
      </table>

      <!-- Data counts -->
      <div style="margin-top:20px;font-family:'Courier New',monospace;font-size:11px;letter-spacing:0.18em;text-transform:uppercase;color:#475569;font-weight:bold">Records Currently Backed Up</div>
      <div style="margin-top:6px;font-size:13px;color:#0f172a">
        <strong>{data.get('total_records', 0):,}</strong> total records across {len(counts)} collections.
      </div>
      <div style="margin-top:8px">{counts_chips}</div>

      <hr style="border:0;border-top:1px solid #e2e8f0;margin:24px 0 18px 0" />
      {render_operational_footer_html(portal="Admin", doc_id=f"backup-{report.get('verdict','info')}")}
      <div style="font-family:'Courier New',monospace;font-size:10px;letter-spacing:0.2em;text-transform:uppercase;color:#475569;font-weight:bold;margin-top:14px;">
        MASCI General Contractors Inc. · 386-322-4500 · mascidocs.com
      </div>
      <div style="font-family:'Courier New',monospace;font-size:9px;letter-spacing:0.2em;text-transform:uppercase;color:#94a3b8;font-weight:normal;margin-top:6px;">
        Generated through MASCI Operations Platform &mdash; Powered by ForgedOps&trade; | &copy; 2026 ForgedOps&trade;
      </div>
    </td></tr>
  </table>
</body></html>"""


# ─────────────────────────────────────────────────────────────────────
# Email send
# ─────────────────────────────────────────────────────────────────────
async def send_verification_email(db, *, force_recipients: Optional[List[str]] = None) -> Dict[str, Any]:
    """Build the report and email it. Returns
    {sent, recipients, verdict, report, error?}."""
    report = await build_verification_report(db)
    recipients = force_recipients or _verification_recipients()
    api_key = (os.environ.get("RESEND_API_KEY") or "").strip()

    result: Dict[str, Any] = {
        "sent": False,
        "recipients": recipients,
        "verdict": report["verdict"],
        "report": report,
    }

    if not recipients:
        result["error"] = "No recipients configured (BACKUP_VERIFICATION_TO / BACKUP_EMAIL_TO / SAFETY_EMAIL_TO all empty)."
        logger.warning(f"[verify] {result['error']}")
        return result

    if not api_key:
        result["error"] = "RESEND_API_KEY not configured."
        logger.warning(f"[verify] {result['error']}")
        return result

    try:
        import resend  # noqa: E402
        resend.api_key = api_key
        sender_email = os.environ.get("SENDER_EMAIL", "noreply@mascidocs.com")
        params = {
            "from": f"MASCI Operations Platform <{sender_email}>",
            "to": recipients,
            "subject": render_verification_subject(report),
            "html": render_verification_email_html(report),
        }
        reply_to = (os.environ.get("REPLY_TO_EMAIL") or "").strip()
        if reply_to:
            params["reply_to"] = reply_to
        await asyncio.to_thread(resend.Emails.send, params)
        result["sent"] = True
        logger.info(
            f"[verify] sent verification email → {recipients} · "
            f"verdict={report['verdict']} · archives={report['r2']['archive_count']}"
        )
    except Exception as e:  # noqa: BLE001
        logger.exception(f"[verify] email send failed: {e}")
        result["error"] = repr(e)

    return result


# ─────────────────────────────────────────────────────────────────────
# Weekly scheduler loop
# ─────────────────────────────────────────────────────────────────────
async def verification_scheduler_loop(db) -> None:
    """Long-running asyncio task: fires send_verification_email once per
    week on the configured day/hour (default Mon 14:00 UTC). Uses a
    `last_run_iso` marker in MongoDB so the cron survives restarts —
    if the backend crashes Monday morning and restarts at 2 PM, the
    email still fires (we run any past-due cron immediately at boot)."""

    if not _enabled():
        logger.info("[verify] weekly cron disabled via BACKUP_VERIFICATION_ENABLED")
        return

    day_of_week = _env_int("BACKUP_VERIFICATION_DAY", DEFAULT_DAY_OF_WEEK) % 7
    hour_utc = _env_int("BACKUP_VERIFICATION_HOUR_UTC", DEFAULT_HOUR_UTC) % 24

    logger.info(
        f"[verify] scheduler armed — fires weekly on day-of-week={day_of_week} "
        f"(Mon=0) at {hour_utc:02d}:00 UTC"
    )

    while True:
        try:
            # Read the last-run marker
            marker = await db.backup_health.find_one(
                {"id": "_verification_last_run"}, {"_id": 0}
            )
            last_run_dt: Optional[datetime] = None
            if marker and marker.get("ts"):
                try:
                    last_run_dt = datetime.fromisoformat(marker["ts"].replace("Z", "+00:00"))
                    if last_run_dt.tzinfo is None:
                        last_run_dt = last_run_dt.replace(tzinfo=timezone.utc)
                except (ValueError, TypeError):
                    last_run_dt = None

            now = datetime.now(timezone.utc)
            # Compute next scheduled fire-time at-or-after now
            next_fire = _next_scheduled_dt(now, day_of_week, hour_utc)

            # If we have no last-run marker AND we're already past the
            # most-recent scheduled time within the last 7 days, fire
            # immediately (handles crash-during-cron + first deploy).
            should_fire_now = False
            most_recent_scheduled = _most_recent_past_scheduled_dt(now, day_of_week, hour_utc)
            if last_run_dt is None or last_run_dt < most_recent_scheduled:
                if now >= most_recent_scheduled:
                    should_fire_now = True

            if should_fire_now:
                logger.info(
                    f"[verify] firing weekly verification (last_run={last_run_dt})"
                )
                try:
                    await send_verification_email(db)
                except Exception as e:  # noqa: BLE001
                    logger.exception(f"[verify] weekly send failed: {e}")
                # Record marker regardless of email success — we don't want
                # a Resend outage to retry every tick.
                try:
                    await db.backup_health.update_one(
                        {"id": "_verification_last_run"},
                        {"$set": {"id": "_verification_last_run", "ts": now.isoformat()}},
                        upsert=True,
                    )
                except Exception as e:  # noqa: BLE001
                    logger.warning(f"[verify] marker update failed: {e}")
                # Schedule the NEXT one for a week from now
                next_fire = _next_scheduled_dt(now + timedelta(minutes=1), day_of_week, hour_utc)

            sleep_seconds = max(60, (next_fire - now).total_seconds())
            # Cap sleep at 1h so config changes are picked up reasonably fast
            sleep_seconds = min(sleep_seconds, 3600)
            await asyncio.sleep(sleep_seconds)
        except asyncio.CancelledError:
            raise
        except Exception as e:  # noqa: BLE001
            logger.exception(f"[verify] scheduler tick failed: {e}")
            await asyncio.sleep(300)  # back off 5 min on tick error


def _next_scheduled_dt(after: datetime, day_of_week: int, hour_utc: int) -> datetime:
    """Return the next datetime ≥ `after` that lands on (day_of_week, hour_utc:00 UTC)."""
    candidate = after.replace(minute=0, second=0, microsecond=0)
    # Shift to the right hour today
    candidate = candidate.replace(hour=hour_utc)
    # Jump to the target weekday
    days_ahead = (day_of_week - candidate.weekday()) % 7
    candidate = candidate + timedelta(days=days_ahead)
    if candidate < after:
        candidate = candidate + timedelta(days=7)
    return candidate


def _most_recent_past_scheduled_dt(now: datetime, day_of_week: int, hour_utc: int) -> datetime:
    """Return the most recent (day_of_week, hour_utc:00 UTC) on-or-before now."""
    cand = now.replace(minute=0, second=0, microsecond=0, hour=hour_utc)
    days_back = (cand.weekday() - day_of_week) % 7
    cand = cand - timedelta(days=days_back)
    if cand > now:
        cand = cand - timedelta(days=7)
    return cand
