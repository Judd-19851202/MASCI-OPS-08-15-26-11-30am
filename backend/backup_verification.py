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
import io
import json
import logging
import os
import uuid
import zipfile
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from operational_footer import render_operational_footer_html
from lib.archive_lineage import build_canonical_archive_lineage, public_archive_lineage_payload, threshold_inventory
from lib.backup_runtime import backup_slot_key_for_day, claim_backup_job, complete_backup_job, fail_backup_job, list_backup_jobs, start_backup_job
from lib.ots_truth import OBSERVED, VALIDATED, canonical_truth_card, compatibility_projection, projected_truth_relationship, public_ots_projection
from lib.scheduler_runs import claim_slot as scheduler_claim_slot, mark_completed as scheduler_mark_completed, mark_failed as scheduler_mark_failed

logger = logging.getLogger(__name__)

DEFAULT_DAY_OF_WEEK = 0       # Monday
DEFAULT_HOUR_UTC = 14         # 14:00 UTC ≈ 10:00 AM ET Mon
DEFAULT_MAX_AGE_HOURS = 36
R2_LIST_TIMEOUT_SECONDS = 5.0
R2_MANIFEST_TIMEOUT_SECONDS = 3.0
_BACKEND_ENV_PATH = Path(__file__).resolve().parent / ".env"


def _runtime_env() -> Dict[str, str]:
    """Return a merged env with backend/.env fallback for standalone tools.

    Runtime server processes already populate os.environ before importing this
    module. Standalone verification scripts in the repo sometimes import this
    module directly, so we opportunistically hydrate missing keys from
    backend/.env without overwriting real process env vars.
    """
    merged = dict(os.environ)
    if _BACKEND_ENV_PATH.exists():
        for raw_line in _BACKEND_ENV_PATH.read_text(encoding="utf-8").splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            key = key.strip()
            if merged.get(key):
                continue
            merged[key] = value.strip().strip('"')
    return merged


def _r2_client_from_runtime_env():
    env = _runtime_env()
    endpoint = (env.get("R2_ENDPOINT") or env.get("S3_ENDPOINT_URL") or "").strip()
    bucket = (env.get("R2_BUCKET") or env.get("S3_BUCKET") or "").strip()
    access = (env.get("R2_ACCESS_KEY_ID") or env.get("S3_ACCESS_KEY") or "").strip()
    secret = (env.get("R2_SECRET_ACCESS_KEY") or env.get("S3_SECRET_KEY") or "").strip()
    if not all([endpoint, bucket, access, secret]):
        return None, None
    try:
        import boto3  # noqa: PLC0415
        from botocore.config import Config as _BotoConfig  # noqa: PLC0415
    except Exception:  # noqa: BLE001
        return None, None
    client = boto3.client(
        "s3",
        endpoint_url=endpoint,
        aws_access_key_id=access,
        aws_secret_access_key=secret,
        region_name=(env.get("S3_REGION") or env.get("R2_REGION") or "auto").strip() or "auto",
        config=_BotoConfig(signature_version="s3v4", s3={"addressing_style": "path"}),
    )
    return client, bucket


class _R2RangeReader(io.BufferedIOBase):
    """Tiny seekable range reader for R2/S3-backed ZIP inspection.

    Purposefully minimal: enough for `zipfile.ZipFile` to read the central
    directory and a small manifest entry without downloading the entire
    archive.
    """

    def __init__(self, s3, bucket: str, key: str, size: int, block_size: int = 1024 * 1024):
        self._s3 = s3
        self._bucket = bucket
        self._key = key
        self._size = max(0, int(size or 0))
        self._block_size = max(64 * 1024, int(block_size or 1024 * 1024))
        self._pos = 0
        self._cache: Dict[int, bytes] = {}

    def readable(self) -> bool:  # pragma: no cover - trivial
        return True

    def seekable(self) -> bool:  # pragma: no cover - trivial
        return True

    def tell(self) -> int:
        return self._pos

    def seek(self, offset: int, whence: int = io.SEEK_SET) -> int:
        if whence == io.SEEK_SET:
            new_pos = offset
        elif whence == io.SEEK_CUR:
            new_pos = self._pos + offset
        elif whence == io.SEEK_END:
            new_pos = self._size + offset
        else:  # pragma: no cover - defensive
            raise ValueError(f"unsupported whence: {whence}")
        self._pos = max(0, min(self._size, int(new_pos)))
        return self._pos

    def _read_block(self, index: int) -> bytes:
        cached = self._cache.get(index)
        if cached is not None:
            return cached
        start = index * self._block_size
        if start >= self._size:
            data = b""
        else:
            end = min(self._size, start + self._block_size) - 1
            resp = self._s3.get_object(
                Bucket=self._bucket,
                Key=self._key,
                Range=f"bytes={start}-{end}",
            )
            data = resp["Body"].read()
        self._cache[index] = data
        return data

    def read(self, size: int = -1) -> bytes:
        if self._pos >= self._size:
            return b""
        if size is None or size < 0:
            size = self._size - self._pos
        end_pos = min(self._size, self._pos + int(size))
        out: List[bytes] = []
        while self._pos < end_pos:
            block_idx = self._pos // self._block_size
            block = self._read_block(block_idx)
            if not block:
                break
            offset = self._pos % self._block_size
            take = min(len(block) - offset, end_pos - self._pos)
            out.append(block[offset: offset + take])
            self._pos += take
        return b"".join(out)


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
    s3, bucket = _r2_client_from_runtime_env()
    if s3 is None or not bucket:
        return []
    out: List[Dict[str, Any]] = []
    try:
        # boto3 list_objects_v2 is sync — wrap in to_thread. Paginate by
        # ContinuationToken so we handle >1000 objects defensively.
        token: Optional[str] = None
        while True:
            kwargs: Dict[str, Any] = {"Bucket": bucket, "Prefix": prefix, "MaxKeys": 1000}
            if token:
                kwargs["ContinuationToken"] = token
            resp = await asyncio.wait_for(
                asyncio.to_thread(s3.list_objects_v2, **kwargs),
                timeout=R2_LIST_TIMEOUT_SECONDS,
            )
            for it in resp.get("Contents") or []:
                lm = it.get("LastModified")
                key = it.get("Key")
                out.append({
                    "key": key,
                    "filename": (str(key).rsplit("/", 1)[-1] if key else None),
                    "size_bytes": int(it.get("Size") or 0),
                    "last_modified_iso": lm.isoformat() if lm else None,
                    "etag": (it.get("ETag") or "").strip('"') or None,
                })
            if resp.get("IsTruncated"):
                token = resp.get("NextContinuationToken")
                if not token:
                    break
            else:
                break
    except asyncio.TimeoutError:
        logger.warning("[verify] R2 list_objects_v2 timed out after %.1fs", R2_LIST_TIMEOUT_SECONDS)
        return out
    except Exception as e:  # noqa: BLE001
        logger.exception(f"[verify] R2 list_objects_v2 failed: {e}")
        return []

    out.sort(key=lambda r: r.get("last_modified_iso") or "", reverse=True)
    return out


async def read_r2_backup_manifest(key: str) -> Optional[Dict[str, Any]]:
    """Read only the backup manifest from an R2 archive.

    Returns `None` when R2 is unavailable, the object is unreadable, or no
    recognised manifest is present.
    """
    s3, bucket = _r2_client_from_runtime_env()
    if s3 is None or not bucket:
        return None

    def _read() -> Optional[Dict[str, Any]]:
        head = s3.head_object(Bucket=bucket, Key=key)
        size = int(head.get("ContentLength") or 0)
        reader = _R2RangeReader(s3, bucket, key, size)
        with zipfile.ZipFile(reader, "r") as zf:
            manifest_name = None
            for candidate in ("backup_manifest.json", "MANIFEST.json"):
                if candidate in zf.namelist():
                    manifest_name = candidate
                    break
            if manifest_name is None:
                return None
            manifest = json.loads(zf.read(manifest_name).decode("utf-8"))
            etag = (head.get("ETag") or "").strip('"') or None
            last_modified = head.get("LastModified")
            return {
                "key": key,
                "manifest_name": manifest_name,
                "manifest": manifest,
                "content_length": size,
                "etag": etag,
                "last_modified_iso": (
                    last_modified.astimezone(timezone.utc).isoformat()
                    if isinstance(last_modified, datetime)
                    else None
                ),
                "checksum_sha256": head.get("ChecksumSHA256"),
                "checksum_type": head.get("ChecksumType"),
            }

    try:
        return await asyncio.wait_for(asyncio.to_thread(_read), timeout=R2_MANIFEST_TIMEOUT_SECONDS)
    except asyncio.TimeoutError:
        logger.warning("[verify] timed out reading R2 backup manifest for %s after %.1fs", key, R2_MANIFEST_TIMEOUT_SECONDS)
        return None
    except Exception as e:  # noqa: BLE001
        logger.warning("[verify] failed to read R2 backup manifest for %s: %s", key, e)
        return None


# ─────────────────────────────────────────────────────────────────────
# Build verification report
# ─────────────────────────────────────────────────────────────────────
async def build_verification_report(db) -> Dict[str, Any]:
    """Assemble the full verification report. Cross-checks R2 archives
    against the local backup_health ledger and applies the max-age rule.
    Returns a single dict the email renderer + endpoint consumers all use."""

    max_age_hours = _env_int("BACKUP_VERIFICATION_MAX_AGE_HOURS", DEFAULT_MAX_AGE_HOURS)
    now = datetime.now(timezone.utc)
    lineage = await build_canonical_archive_lineage(db)
    authoritative = lineage.get("authoritative_artifact") or {}
    newest_valid = lineage.get("newest_valid_recoverable_artifact") or {}
    newest_observed = lineage.get("newest_observed_artifact") or {}
    threshold_meta = threshold_inventory().get("verification_max_age_hours") or {}

    # ── 1. R2 archives ─────────────────────────────────────────────
    archives = await list_r2_backup_archives()
    r2_configured = bool(archives)
    try:
        from photo_storage import is_configured as _ps_cfg
        r2_configured = bool(_ps_cfg() or r2_configured)
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
    elif lineage.get("authoritative_recovery_point_time") is None:
        r2_status = "warn"
        r2_issues.append("Canonical archive lineage could not prove an authoritative recovery point.")
    elif (lineage.get("freshness_age_hours") or 0) > max_age_hours:
        r2_status = "stale"
        r2_issues.append(
            f"Authoritative recoverable archive is {lineage.get('freshness_age_hours'):.1f}h old "
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
            mode = (r.get("mode") or "").lower()
            if r.get("ok"):
                if last_full is None and mode in FULL_BACKUP_MODES:
                    last_full = r
                if last_r2 is None and mode == "complete-r2":
                    last_r2 = r
            else:
                if last_failure is None and not str(r.get("id") or "").startswith("_verification_") and mode not in ("r2-usage-alert", "r2-usage-warn"):
                    last_failure = r
    except Exception as e:  # noqa: BLE001
        logger.warning(f"[verify] backup_health read failed: {e}")

    recent_complete_jobs = []
    try:
        recent_complete_jobs = await list_backup_jobs(db, kind="complete-r2", limit=5)
    except Exception as e:  # noqa: BLE001
        logger.warning(f"[verify] backup job read failed: {e}")

    ledger_status = "ok"
    ledger_issues: List[str] = []
    if last_full is None:
        ledger_status = "warn"
        ledger_issues.append("No successful full backup recorded in last 20 runs.")
    elif lineage.get("freshness_age_hours") is not None and lineage.get("freshness_age_hours") > max_age_hours:
        ledger_status = "stale"
        ledger_issues.append(
            f"Canonical authoritative recoverable archive is {lineage.get('freshness_age_hours'):.1f}h old."
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

    report = {
        "ts": now.isoformat(),
        "verdict": verdict,                  # pass | warn | fail
        "r2": {
            "configured": r2_configured,
            "status": r2_status,
            "issues": r2_issues,
            "archive_count": len(archives),
            "newest": newest,
            "newest_age_hrs": newest_age_hrs,
            "authoritative_recovery_point_time": lineage.get("authoritative_recovery_point_time"),
            "authoritative_age_hrs": lineage.get("freshness_age_hours"),
            "authoritative_artifact": authoritative,
            "newest_valid_recoverable_artifact": newest_valid,
            "newest_observed_artifact": newest_observed,
            "archive_lineage": public_archive_lineage_payload(lineage),
            "total_size_bytes": total_size_bytes,
            "total_size_human": _humanize_size(total_size_bytes),
            "max_age_threshold_hrs": max_age_hours,
            "max_age_threshold_source": threshold_meta.get("source"),
            "max_age_threshold_authority": threshold_meta.get("authority"),
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
            "canonical_authoritative_recovery_point_time": lineage.get("authoritative_recovery_point_time"),
        },
        "backup_jobs": {
            "recent_complete_jobs": recent_complete_jobs,
        },
        "data": {
            "per_collection_counts": per_collection_counts,
            "total_records": total_records,
        },
        "archive_lineage": public_archive_lineage_payload(lineage),
    }
    truth_card = canonical_truth_card(
        truth_subject="bcss_backup_archive_lineage",
        canonical_owner="bcss_backup_archive_lineage",
        truth_surface_id="bcss_backup_archive_lineage",
        evidence_state="independently_verified" if authoritative else "observed",
        evidence_quality="VALIDATED" if authoritative else "DIRECT_OBSERVED",
        evidence_confidence=lineage.get("lineage_confidence") or "LOW",
        truth_evaluation="VERIFIED" if authoritative else "UNVERIFIABLE",
        permitted_claim=VALIDATED if authoritative else OBSERVED,
        claim_ceiling=VALIDATED,
        claim_basis=["archive_lineage", "backup_health ledger", "R2 archive facts", "verification report"],
        prohibited_claims=["CERTIFIED"],
        degradation_reasons=list(lineage.get("degradation_reasons") or []) + list(r2_issues or []) + list(ledger_issues or []),
        unknowns=[] if (authoritative or newest_observed) else ["No archive evidence is currently available."],
        contradictory_evidence=[],
        evidence_timestamp=lineage.get("authoritative_recovery_point_time") or (newest_observed or {}).get("observed_time") or now.isoformat(),
        evaluation_timestamp=now.isoformat(),
        audit_reference="OTS-C5-BACKUP-VERIFICATION",
        evidence_required_to_raise_claim=["restore execution evidence", "BCSS-R13 recovery certification evidence"],
        notes=["Backup Verification validates archive-lineage truth only.", "This surface does not prove restore or recovery certification."],
    )
    compatibility = compatibility_projection(
        preserved_fields=9,
        deprecated_fields=0,
        new_fields=3,
        alias_fields=["verdict"],
        breaking_changes=0,
    )
    report["ots_truth"] = public_ots_projection(truth_card)
    report["truth_relationship"] = projected_truth_relationship(
        surface_id="bcss_backup_archive_lineage",
        card=truth_card,
        canonical_owner_route="/api/admin/backup-verification/preview",
        derivation_explanation="Backup Verification is a bounded validation/report projection over canonical archive-lineage evidence.",
        derived_status=truth_card["truth_evaluation"],
    )
    report["compatibility"] = compatibility
    return report


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
    # ALERT-ENV-001 · prepend env tag for operator clarity.
    from outage_alerts import _env_tag
    env_prefix = f"[{_env_tag()}]"
    verdict = report.get("verdict") or "info"
    archives = report["r2"]["archive_count"]
    if verdict == "pass":
        return f"{env_prefix} [MASCI \u00b7 BACKUP] Weekly Verification \u00b7 {archives} archives healthy"
    if verdict == "fail":
        return f"{env_prefix} \U0001F6A8 BACKUP VERIFICATION FAILED \u00b7 check immediately"
    return f"{env_prefix} [MASCI \u00b7 BACKUP] Weekly Verification \u00b7 {archives} archives \u00b7 issues detected"


def _env_banner_for_backup() -> str:
    """ALERT-ENV-001 · Thin wrapper so the verification HTML can call
    the shared banner helper from `outage_alerts`."""
    from outage_alerts import render_env_banner_html
    return render_env_banner_html()


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
    archive_lineage = report.get("archive_lineage") or r2.get("archive_lineage") or {}
    authoritative_time = archive_lineage.get("authoritative_recovery_point_time")
    authoritative_age_hrs = archive_lineage.get("freshness_age_hours")
    authoritative_source = archive_lineage.get("authoritative_time_source") or "UNKNOWN"
    lineage_confidence = archive_lineage.get("lineage_confidence") or "LOW"
    integrity_status = archive_lineage.get("integrity_status") or "UNKNOWN"
    completeness_status = archive_lineage.get("completeness_status") or "UNKNOWN"
    availability_status = archive_lineage.get("availability_status") or "ABSENT"
    degradation_reasons = list(archive_lineage.get("degradation_reasons") or [])
    authoritative_artifact = r2.get("authoritative_artifact") or archive_lineage.get("newest_valid_recoverable_artifact") or {}
    newest_observed = r2.get("newest") or archive_lineage.get("newest_observed_artifact") or {}
    ots_truth = report.get("ots_truth") or {}

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

    authoritative_summary = "No archive evidence is currently available"
    authoritative_detail = "No authoritative recoverable point is currently proven"
    if authoritative_time:
        age_label = f"{authoritative_age_hrs:.1f}h ago" if authoritative_age_hrs is not None else "age unknown"
        authoritative_summary = f"Authoritative recoverable point: {authoritative_time} · {age_label}"
        authoritative_detail = (
            f"Source={authoritative_source} · confidence={lineage_confidence} · "
            f"integrity={integrity_status} · completeness={completeness_status} · availability={availability_status}"
        )
    elif newest_observed:
        authoritative_summary = "No authoritative recoverable point is currently proven"
        authoritative_detail = (
            f"Observed object exists, but recoverable-point proof is insufficient · "
            f"integrity={integrity_status} · completeness={completeness_status} · availability={availability_status}"
        )

    degradation_html = ""
    if degradation_reasons:
        degradation_items = "".join(f"<li style='margin:4px 0'>{_esc(reason)}</li>" for reason in degradation_reasons)
        degradation_html = (
            "<div style='margin-top:10px;font-size:12px;color:#7c2d12'>"
            "<strong>Degradation reasons</strong>"
            f"<ul style='margin:6px 0 0 0;padding-left:18px'>{degradation_items}</ul>"
            "</div>"
        )

    newest_observed_html = "No archive evidence is currently available"
    if newest_observed:
        newest_key = newest_observed.get("object_key") or newest_observed.get("key") or newest_observed.get("filename") or "unknown"
        newest_age = newest_observed.get("freshness_age_minutes")
        if newest_age is None and r2.get("newest_age_hrs") is not None:
            newest_age = round(float(r2.get("newest_age_hrs") or 0.0) * 60.0, 2)
        newest_age_label = f"{(float(newest_age) / 60.0):.1f}h ago" if newest_age is not None else "age unknown"
        newest_observed_html = (
            f"Newest observed archive object: <code style='font-size:11px'>{_esc(str(newest_key))}</code>"
            f" · {newest_age_label} · integrity={_esc(str(newest_observed.get('integrity_status') or 'UNKNOWN'))}"
            f" · completeness={_esc(str(newest_observed.get('completeness_status') or 'UNKNOWN'))}"
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
      {_env_banner_for_backup()}
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
      </div>
      <div style="margin-top:12px;padding:12px 14px;background:#f8fafc;border:1px solid #e2e8f0;border-radius:6px;">
        <div style="font-family:'Courier New',monospace;font-size:10px;letter-spacing:0.16em;text-transform:uppercase;color:#475569;font-weight:bold">Authoritative Recoverable Point</div>
        <div style="margin-top:6px;font-size:13px;color:#0f172a;font-weight:700">{_esc(authoritative_summary)}</div>
        <div style="margin-top:4px;font-size:12px;color:#475569">{_esc(authoritative_detail)}</div>
        {degradation_html}
      </div>
      <div style="margin-top:10px;padding:10px 12px;background:#ffffff;border:1px dashed #cbd5e1;border-radius:6px;">
        <div style="font-family:'Courier New',monospace;font-size:10px;letter-spacing:0.16em;text-transform:uppercase;color:#64748b;font-weight:bold">Newest Observed Archive Object (Secondary Diagnostic Evidence Only)</div>
        <div style="margin-top:6px;font-size:12px;color:#475569">{newest_observed_html}</div>
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

      <div style="margin-top:18px;padding:10px 12px;background:#fff7ed;border:1px solid #fdba74;border-radius:6px;font-size:12px;color:#9a3412;line-height:1.5;">
        <strong>Claim boundary:</strong> This verification report describes archive lineage, integrity, completeness, and recoverable-point freshness only. It does not prove restore certification, deployment readiness, or BCSS recovery-class certification.
      </div>
      <div style="margin-top:10px;padding:10px 12px;background:#f8fafc;border:1px solid #cbd5e1;border-radius:6px;font-size:12px;color:#334155;line-height:1.5;">
        <strong>Operational Truth Spine:</strong> Truth subject={_esc(str(ots_truth.get('truth_subject') or 'bcss_backup_archive_lineage'))} · permitted claim={_esc(str(ots_truth.get('permitted_claim') or 'UNKNOWN'))} · confidence={_esc(str(ots_truth.get('evidence_confidence') or 'UNKNOWN'))}. This surface does not prove restore certification or BCSS recovery certification.
      </div>

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
async def send_verification_email(db, *, force_recipients: Optional[List[str]] = None, manual: bool = False) -> Dict[str, Any]:
    """Build the report and email it. Returns
    {sent, recipients, verdict, report, error?}."""
    from lib.notification_delivery import deliver_notification  # noqa: PLC0415
    from branding_resolver import (  # noqa: PLC0415
        resolve_reply_to_email as _resolve_reply_to_email,
    )

    if manual or force_recipients:
        slot_key = backup_slot_key_for_day(datetime.now(timezone.utc)) + f"::weekly-verification-manual::{datetime.now(timezone.utc).strftime('%H%M%S')}"
        slot_claim = {"manual": True}
    else:
        slot_key = backup_slot_key_for_day(datetime.now(timezone.utc)) + "::weekly-verification"
        slot_claim = await scheduler_claim_slot(db, "backup_verification", slot_key)
        if slot_claim is None:
            return {
                "sent": False,
                "recipients": force_recipients or _verification_recipients(),
                "verdict": "warn",
                "report": None,
                "error": "Verification already claimed for this slot.",
            }
    verify_job = await claim_backup_job(
        db,
        job_type="verification",
        kind="verification",
        slot_key=slot_key,
        trigger="manual" if (manual or force_recipients) else "scheduled",
        metadata={"force_recipients": force_recipients or []},
    )
    if verify_job:
        await start_backup_job(db, verify_job["job_id"])
    report = await build_verification_report(db)
    recipients = force_recipients or _verification_recipients()

    result: Dict[str, Any] = {
        "sent": False,
        "recipients": recipients,
        "verdict": report["verdict"],
        "report": report,
    }

    if not recipients:
        result["error"] = "No recipients configured (BACKUP_VERIFICATION_TO / BACKUP_EMAIL_TO / SAFETY_EMAIL_TO all empty)."
        logger.warning(f"[verify] {result['error']}")
        if verify_job:
            await fail_backup_job(db, verify_job["job_id"], error=result["error"], state="failed")
        await scheduler_mark_failed(db, "backup_verification", slot_key, error=result["error"])
        return result

    try:
        delivery = await deliver_notification(
            db=db,
            workflow="backup-verification",
            correlation_id=f"cid-backup-verify-{uuid.uuid4().hex}",
            record_id=f"backup-verify-{report.get('generated_at') or datetime.now(timezone.utc).isoformat()}",
            recipients=recipients,
            subject=render_verification_subject(report),
            html=render_verification_email_html(report),
            reply_to=(await _resolve_reply_to_email(db)) if db is not None else None,
            metadata={
                "kind": "backup_verification",
                "verdict": report.get("verdict"),
                "archive_count": ((report.get("r2") or {}).get("archive_count")),
            },
        )
        result.update({
            "delivery_mode": delivery.get("delivery_mode"),
            "delivery_status": delivery.get("notification_state"),
            "provider_called": delivery.get("provider_called"),
            "provider_accepted": delivery.get("provider_accepted"),
            "notification_capture_available": delivery.get("notification_capture_available"),
            "notification_capture_id": delivery.get("capture_id"),
        })
        result["sent"] = bool(delivery.get("provider_accepted"))
        result["captured_preview"] = delivery.get("notification_state") == "captured_preview"
        if delivery.get("notification_state") == "configuration_blocked":
            result["error"] = delivery.get("failure_reason") or "notification configuration blocked"
        logger.info(
            f"[verify] notification dispatched → {recipients} · "
            f"verdict={report['verdict']} · status={delivery.get('notification_state')} · "
            f"archives={report['r2']['archive_count']}"
        )
        if verify_job:
            await complete_backup_job(db, verify_job["job_id"], outcome="ok" if result["sent"] else "warn", result=result)
        if not manual and not force_recipients:
            await scheduler_mark_completed(
                db,
                "backup_verification",
                slot_key,
                recipients=len(recipients),
                status="done",
                meta={"sent": bool(result.get("sent")), "verdict": report.get("verdict")},
            )
    except Exception as e:  # noqa: BLE001
        logger.exception(f"[verify] email send failed: {e}")
        result["error"] = repr(e)
        if verify_job:
            await fail_backup_job(db, verify_job["job_id"], error=repr(e))
        if not manual and not force_recipients:
            await scheduler_mark_failed(db, "backup_verification", slot_key, error=repr(e))

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
