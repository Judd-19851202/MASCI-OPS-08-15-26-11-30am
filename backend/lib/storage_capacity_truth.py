"""Canonical storage-capacity truth owner (P0-CAPACITY-2026-08-13).

ONE authority for storage capacity. Distinguishes three concepts:

  A. PHYSICAL ATLAS STORAGE  — authoritative infrastructure capacity from
     the live mongod volume metrics (dbStats fsTotalSize / fsUsedSize).
     This drives capacity-health severity. Dynamic: if Atlas expands the
     volume, MASCI OPS automatically uses the new real capacity. No code
     or config edit is required when infrastructure storage grows.

  B. LOGICAL DATABASE FOOTPRINT — per-database storage+index footprint of
     the managed MASCI databases. Reported separately. NEVER used as the
     denominator for physical disk capacity.

  C. OPTIONAL OPERATING BUDGET — the legacy ``ATLAS_QUOTA_MB`` value,
     redefined as an OPTIONAL logical planning/cost budget only. It must
     NOT claim the physical disk is full, block writes, drive critical
     physical alarms, refuse startup, or block deployment.

If physical telemetry is unavailable we report physical=UNKNOWN rather than
falling back to the operating budget and calling it disk capacity. Truthful
UNKNOWN is better than fake precision.
"""
from __future__ import annotations

import logging
import os
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from lib.database_authority import managed_database_names

logger = logging.getLogger(__name__)

_MB = 1024 * 1024

# MASCI operational severity thresholds on REAL physical utilization %.
# These are MASCI operating thresholds, not claims about MongoDB hard limits.
SEV_HEALTHY = "HEALTHY"
SEV_WARNING = "WARNING"
SEV_HIGH = "HIGH"
SEV_CRITICAL = "CRITICAL"
SEV_EMERGENCY = "EMERGENCY"
SEV_UNKNOWN = "UNKNOWN"

# Upward-cross thresholds.
THRESHOLDS = {
    SEV_WARNING: 80.0,
    SEV_HIGH: 90.0,
    SEV_CRITICAL: 95.0,
    SEV_EMERGENCY: 98.0,
}
# Hysteresis reset (downward) thresholds — prevent alert flapping/spam.
RESET_THRESHOLDS = {
    SEV_WARNING: 77.0,
    SEV_HIGH: 87.0,
    SEV_CRITICAL: 92.0,
    SEV_EMERGENCY: 95.0,
}
_SEVERITY_RANK = {
    SEV_HEALTHY: 0, SEV_WARNING: 1, SEV_HIGH: 2, SEV_CRITICAL: 3, SEV_EMERGENCY: 4,
}


def canonical_physical_severity(utilization_percent: Optional[float]) -> str:
    """Severity from REAL physical utilization. UNKNOWN if telemetry absent."""
    if utilization_percent is None:
        return SEV_UNKNOWN
    p = float(utilization_percent)
    if p >= THRESHOLDS[SEV_EMERGENCY]:
        return SEV_EMERGENCY
    if p >= THRESHOLDS[SEV_CRITICAL]:
        return SEV_CRITICAL
    if p >= THRESHOLDS[SEV_HIGH]:
        return SEV_HIGH
    if p >= THRESHOLDS[SEV_WARNING]:
        return SEV_WARNING
    return SEV_HEALTHY


def operating_budget_mb() -> Optional[int]:
    """OPTIONAL logical operating budget (legacy ATLAS_QUOTA_MB / new
    ATLAS_OPERATING_BUDGET_MB). Returns None when unset or 0 (unbounded)."""
    raw = os.environ.get("ATLAS_OPERATING_BUDGET_MB")
    if raw is None:
        raw = os.environ.get("ATLAS_QUOTA_MB")
    if raw is None:
        return None
    try:
        v = int(raw)
    except (TypeError, ValueError):
        return None
    return v if v > 0 else None


async def _physical_from_dbstats(client, probe_db_name: str) -> Dict[str, Any]:
    """Read the live volume metrics. fsTotalSize/fsUsedSize are cluster-wide
    (same physical volume regardless of which DB we query)."""
    try:
        stats = await client[probe_db_name].command("dbStats")
    except Exception as exc:  # noqa: BLE001
        logger.warning("[capacity-truth] dbStats unavailable on %s: %s", probe_db_name, type(exc).__name__)
        return {"status": SEV_UNKNOWN, "reason": f"dbstats_unavailable:{type(exc).__name__}"}
    total = stats.get("fsTotalSize")
    used = stats.get("fsUsedSize")
    if not total or used is None:
        return {"status": SEV_UNKNOWN, "reason": "fs_metrics_absent"}
    total = float(total)
    used = float(used)
    free = max(total - used, 0.0)
    pct = round(used / total * 100.0, 1) if total > 0 else None
    return {
        "status": "MEASURED",
        "physical_total_bytes": int(total),
        "physical_used_bytes": int(used),
        "physical_free_bytes": int(free),
        "physical_total_mb": round(total / _MB, 2),
        "physical_used_mb": round(used / _MB, 2),
        "physical_free_mb": round(free / _MB, 2),
        "physical_utilization_percent": pct,
        "metric_source": "mongodb.dbStats.fsTotalSize/fsUsedSize",
    }


async def build_capacity_truth(client, runtime_identity: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Canonical capacity payload. NEVER uses the operating budget as the
    physical denominator."""
    runtime_identity = runtime_identity or {}
    identity = (runtime_identity.get("identity") if isinstance(runtime_identity, dict) else None) or {}
    active_db = identity.get("db_name") if isinstance(identity, dict) else None
    if hasattr(active_db, "to_safe_dict"):
        active_db = None
    candidates = managed_database_names(runtime_identity or {})
    probe_db = active_db or (candidates[0] if candidates else "admin")

    # --- A. Physical (authoritative) ---
    physical = await _physical_from_dbstats(client, probe_db)

    # --- B. Logical footprint ---
    dbs: Dict[str, float] = {}
    logical_total_mb = 0.0
    seen = set()
    for name in candidates:
        if not name or name in seen:
            continue
        seen.add(name)
        try:
            st = await client[name].command("dbStats")
            fp = ((st.get("storageSize", 0) or 0) + (st.get("indexSize", 0) or 0)) / _MB
            dbs[name] = round(fp, 2)
            logical_total_mb += dbs[name]
        except Exception:  # noqa: BLE001
            continue
    prod_mb = next((v for k, v in dbs.items() if k.endswith("safety") and not k.endswith("preview")), None)
    preview_mb = next((v for k, v in dbs.items() if k.endswith("preview")), None)
    other_mb = round(logical_total_mb - sum(v for v in (prod_mb, preview_mb) if v is not None), 2)

    # --- C. Optional operating budget (planning only) ---
    budget_mb = operating_budget_mb()
    budget = {
        "configured": budget_mb is not None,
        "operating_budget_mb": budget_mb,
        "logical_used_mb": round(logical_total_mb, 2),
        "logical_pct_of_budget": round(logical_total_mb / budget_mb * 100.0, 1) if budget_mb else None,
        "label": "Operating budget (logical planning target — NOT physical disk capacity)",
        "deprecated_env": "ATLAS_QUOTA_MB",
        "note": "Advisory only. Does not constrain infrastructure capacity, block writes, or gate deployment.",
    }

    pct = physical.get("physical_utilization_percent")
    severity = canonical_physical_severity(pct)

    shared_cluster = len([k for k in dbs if k]) > 1
    return {
        "ok": True,
        "physical": physical,
        "logical": {
            "total_mb": round(logical_total_mb, 2),
            "production_mb": prod_mb,
            "preview_mb": preview_mb,
            "other_mb": other_mb if other_mb > 0 else 0.0,
            "dbs": dbs,
        },
        "operating_budget": budget,
        "severity": severity,
        "severity_basis": "physical_utilization" if severity != SEV_UNKNOWN else "unknown_physical_telemetry",
        "shared_cluster": shared_cluster,
        "shared_cluster_note": (
            "Physical capacity is SHARED cluster capacity: preview and production "
            "databases reside on the same Atlas cluster." if shared_cluster else None
        ),
        "measured_at": datetime.now(timezone.utc).isoformat(),
    }


# ---------------------------------------------------------------------------
# Targeted administrative email alerting with threshold-cross hysteresis.
# Modeled on lib/red_alert.py. Best-effort, never raises. Never emails
# ordinary employees — recipients are designated infrastructure admins/owners.
# ---------------------------------------------------------------------------
ALERT_DOC_ID = "atlas_physical_capacity"
_ALERT_STATE_COLLECTION = "storage_capacity_alert_state"


def resolve_capacity_alert_recipients() -> list[str]:
    raw = (
        os.environ.get("CAPACITY_ALERT_TO")
        or os.environ.get("INFRA_ALERT_TO")
        or os.environ.get("OPS_ALERT_TO")
        or os.environ.get("ADMIN_DEAD_LETTER_EMAIL")
        or os.environ.get("SUPER_ADMIN_EMAIL")
        or os.environ.get("ADMIN_EMAIL")
        or ""
    )
    return [a.strip() for a in raw.split(",") if a.strip() and "@" in a]


def _should_alert(prev: str, current: str, pct: float) -> bool:
    """Upward threshold-cross with hysteresis: only alert when severity
    increased to a higher band than last alerted."""
    return _SEVERITY_RANK.get(current, 0) > _SEVERITY_RANK.get(prev, 0)


def _has_recovered(prev: str, pct: Optional[float]) -> bool:
    """True when a previously-alerted band has dropped below its reset line."""
    if pct is None or prev in (SEV_HEALTHY, SEV_UNKNOWN, "", None):
        return False
    reset = RESET_THRESHOLDS.get(prev)
    return reset is not None and pct < reset


async def maybe_send_capacity_alert(db, truth: Dict[str, Any], *, dry_run: bool = False) -> Dict[str, Any]:
    """Evaluate physical severity and send at most one targeted admin email
    per upward threshold cross; send one recovery email when it clears."""
    physical = truth.get("physical") or {}
    pct = physical.get("physical_utilization_percent")
    current = truth.get("severity") or SEV_UNKNOWN
    now = datetime.now(timezone.utc)
    try:
        state = await db[_ALERT_STATE_COLLECTION].find_one({"_id": ALERT_DOC_ID}) or {}
        prev = state.get("severity") or SEV_HEALTHY

        await db[_ALERT_STATE_COLLECTION].update_one(
            {"_id": ALERT_DOC_ID},
            {"$set": {"severity": current, "last_pct": pct, "last_seen_at": now.isoformat()},
             "$setOnInsert": {"_id": ALERT_DOC_ID}},
            upsert=True,
        )

        if current == SEV_UNKNOWN:
            return {"result": "unknown_physical", "severity": current}

        # Recovery path.
        if current in (SEV_HEALTHY,) and _has_recovered(prev, pct):
            sent = await _send(db, now, subject=f"MASCI OPS — Atlas storage recovered ({pct}%)",
                               body=_recovery_body(prev, pct, physical), dry_run=dry_run)
            await db[_ALERT_STATE_COLLECTION].update_one(
                {"_id": ALERT_DOC_ID},
                {"$set": {"last_alerted_severity": SEV_HEALTHY, "last_alert_at": now.isoformat()}})
            return {"result": "recovered" if sent else "recovered_not_sent", "previous": prev, "severity": current}

        # Upward cross.
        if _should_alert(prev, current, pct or 0.0):
            sent = await _send(db, now, subject=f"[MASCI OPS] Atlas storage {current} — {pct}% physical",
                               body=_alert_body(current, pct, truth), dry_run=dry_run)
            await db[_ALERT_STATE_COLLECTION].update_one(
                {"_id": ALERT_DOC_ID},
                {"$set": {"last_alerted_severity": current, "last_alert_at": now.isoformat(), "last_alert_pct": pct}})
            return {"result": "sent" if sent else "sent_suppressed", "previous": prev, "severity": current, "dry_run": dry_run}

        return {"result": "no_change", "previous": prev, "severity": current}
    except Exception as exc:  # noqa: BLE001
        logger.warning("[capacity-alert] maybe_send failed: %s", exc)
        return {"result": "error", "error": str(exc)[:200]}


async def _send(db, now, *, subject: str, body: str, dry_run: bool) -> bool:
    recipients = resolve_capacity_alert_recipients()
    if not recipients:
        return False
    if dry_run:
        return True
    if os.environ.get("AUTO_EMAIL_REPORTS", "false").lower() != "true" or not os.environ.get("RESEND_API_KEY"):
        return False
    try:
        import resend  # noqa: PLC0415
        resend.api_key = os.environ["RESEND_API_KEY"]
        resend.Emails.send({
            "from": os.environ.get("RESEND_FROM", "alerts@mascigc.com"),
            "to": recipients,
            "subject": subject,
            "html": body,
        })
        return True
    except Exception as exc:  # noqa: BLE001
        logger.warning("[capacity-alert] resend failed: %s", exc)
        return False


def _alert_body(severity: str, pct, truth: Dict[str, Any]) -> str:
    ph = truth.get("physical") or {}
    lg = truth.get("logical") or {}
    return (
        f"<div style='font-family:system-ui,sans-serif;font-size:14px;color:#0f172a'>"
        f"<h2 style='color:#c8102e'>MASCI OPS — Atlas physical storage {severity}</h2>"
        f"<p>Physical utilization: <strong>{pct}%</strong></p>"
        f"<ul>"
        f"<li>Total: {ph.get('physical_total_mb')} MB</li>"
        f"<li>Used: {ph.get('physical_used_mb')} MB</li>"
        f"<li>Free: {ph.get('physical_free_mb')} MB</li>"
        f"<li>Production DB: {lg.get('production_mb')} MB</li>"
        f"<li>Preview DB: {lg.get('preview_mb')} MB</li>"
        f"</ul>"
        f"<p>Recommended action: review the largest logical consumers and, if this is "
        f"shared-cluster pressure from preview, separate or prune preview; otherwise expand the Atlas tier.</p>"
        f"</div>"
    )


def _recovery_body(prev: str, pct, physical: Dict[str, Any]) -> str:
    return (
        f"<div style='font-family:system-ui,sans-serif;font-size:14px;color:#0f172a'>"
        f"<h2 style='color:#15803d'>MASCI OPS — Atlas storage recovered</h2>"
        f"<p>Prior severity: <strong>{prev}</strong> → now <strong>HEALTHY</strong> at {pct}% physical.</p>"
        f"<p>Free capacity: {physical.get('physical_free_mb')} MB of {physical.get('physical_total_mb')} MB.</p>"
        f"</div>"
    )
