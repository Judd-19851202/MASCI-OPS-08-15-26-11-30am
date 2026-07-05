"""ODS-001 · Canonical fact model constants and envelope validation."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


FACT_TYPES = (
    "labor_fact", "equipment_fact", "production_fact", "delay_fact",
    "material_fact", "safety_fact", "quality_fact", "photo_evidence_fact",
    "weather_fact", "readiness_fact", "intelligence_fact",
)

SOURCE_TYPES = (
    "daily_report_v1", "daily_report_v2", "hr_time",
    "equipment_checkout", "safety_form", "qa_form", "job_photo",
    "dispatch_event", "manual_ingest", "mobile_submission",
)

SOURCE_STATUS = ("full", "partial", "regenerated", "superseded")

FACT_ENVELOPE_FIELDS = (
    "fact_id", "fact_type", "tenant_id", "project_id", "date",
    "source_type", "source_id", "source_item_id", "source_version",
    "source_status", "is_current", "submitted_by", "verified_identity",
    "confidence", "trace_id", "ingestion_run_id",
    "created_at", "updated_at", "payload",
)


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def validate_fact_envelope(f: Dict[str, Any]) -> Optional[str]:
    """Return None if valid, else a human error string. Cheap — no I/O."""
    for k in ("fact_id", "fact_type", "tenant_id", "project_id",
              "date", "source_type", "source_id"):
        if not f.get(k):
            return f"missing_field:{k}"
    if f["fact_type"] not in FACT_TYPES:
        return f"invalid_fact_type:{f['fact_type']}"
    if f["source_type"] not in SOURCE_TYPES:
        return f"invalid_source_type:{f['source_type']}"
    if f.get("source_status") and f["source_status"] not in SOURCE_STATUS:
        return f"invalid_source_status:{f['source_status']}"
    conf = f.get("confidence", 1.0)
    try:
        conf = float(conf)
    except (TypeError, ValueError):
        return "confidence_not_numeric"
    if not (0.0 <= conf <= 1.0):
        return f"confidence_out_of_range:{conf}"
    if not isinstance(f.get("payload"), dict):
        return "payload_must_be_dict"
    return None


def normalize_project_id(pid: Any) -> str:
    """Consistently stringify project ids so lookups don't miss due to type."""
    if pid is None:
        return ""
    return str(pid).strip()


def coerce_date(d: Any) -> str:
    """Coerce any date-like into YYYY-MM-DD; empty string if unparseable."""
    if not d:
        return ""
    s = str(d)
    # Already ISO date
    if len(s) >= 10 and s[4] == "-" and s[7] == "-":
        return s[:10]
    try:
        return datetime.fromisoformat(s).date().isoformat()
    except Exception:  # noqa: BLE001
        return ""


def coerce_number(v: Any, default: float = 0.0) -> float:
    try:
        if v in (None, ""):
            return default
        return float(v)
    except (TypeError, ValueError):
        return default
