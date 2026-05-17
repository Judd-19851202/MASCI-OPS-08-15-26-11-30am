#!/usr/bin/env python3
"""export_human_readable.py — convert a MASCI technical backup into a
non-technical, audit-friendly, customer-deliverable archive.

See /app/memory/DATA_PORTABILITY.md for the surrounding strategy.

Stage A — DONE:
    • CSV per collection
    • Photo extraction grouped by module + record
    • EXPORT_INDEX.csv + DATA_DICTIONARY.csv + MANIFEST.json
    • README_START_HERE.txt + Verification_Report.txt + Export_Errors.csv
    • RAW_JSON/ mirror preserved for technical recovery
    • Sensitive fields redacted in the human-readable layer

Stage B — DONE (this file):
    • Per-record PDFs via HYBRID strategy:
        - Platform-native templates (pdf_render.render_record_pdf,
          field_leadership_pdf.render_field_leadership_pdf) where they
          exist — those PDFs look exactly like what the live system prints.
        - Standardized fallback PDF (export_pdf_fallback.render_fallback_pdf)
          for every other record type.
    • Photo refs (photo://) inside records are pre-resolved to local
      data: URLs from the extracted backup so PDFs render correctly even
      when R2 is offline or the operator is on a plane.
    • PDF rendering failures NEVER crash the export — they log a WARN
      and continue.

Stage C (TODO) will add an Admin UI button.

STORAGE-ARCHITECTURE NEUTRALITY (intentional)
    This script knows NOTHING about Cloudflare R2, the MASCI server, S3,
    SFTP, or any other delivery target. It reads a source (local zip OR
    extracted folder) and writes to a single ``--out`` directory you give
    it. The caller decides where that output ultimately lands.

    Future delivery integrations (Admin UI download, MASCI-owned archive
    server, customer S3 bucket, etc.) will be THIN WRAPPERS that:
        1. Call this exporter into a tmpdir
        2. Upload the produced zip to the chosen destination
        3. Delete the tmpdir

    The platform never auto-persists a human-readable export. That is a
    deliberate design choice — these archives contain HR / safety /
    employee data and belong on the customer's storage, not the platform
    vendor's. See DATA_PORTABILITY.md § 11 ("Storage architecture").

SAFETY GUARANTEES
    • READ-ONLY against the source backup. The exporter never writes to,
      modifies, or deletes the source zip / folder / R2 bucket.
    • The platform's existing backup pipeline is not touched. This script
      runs offline against an already-built backup.

Usage:
    python3 scripts/export_human_readable.py --backup path/to/backup.zip --out ./exports
    python3 scripts/export_human_readable.py --from-source-folder path/to/extracted --out ./exports
    python3 scripts/export_human_readable.py --backup b.zip --out ./exp --dry-run
    python3 scripts/export_human_readable.py --backup b.zip --out ./exp --modules SAFETY,HR
    python3 scripts/export_human_readable.py --backup b.zip --out ./exp --no-zip
    python3 scripts/export_human_readable.py --backup b.zip --out ./exp --no-pdf  (fast)

Env vars:
    EXPORT_COMPANY_NAME    Defaults to "MASCI". Drives the output archive name.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import logging
import os
import re
import shutil
import sys
import tempfile
import traceback
import zipfile
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

logger = logging.getLogger("masci.export.human")
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

# ─────────────────────────────────────────────────────────────────────────────
# Module map. Maps each Mongo collection to a business module + sort hints.
#
#   • module           — top-level folder in the export (DAILY_REPORTS, SAFETY…)
#   • label            — human label used in CSV headings & README
#   • date_field       — primary date field for By_Date subfolder grouping
#   • group_field      — secondary grouping (project, unit, employee, …)
#   • title_template   — Python format string for the per-record filename
#
# Collections not listed here are dumped under module="OTHER" with no CSV,
# logged in Verification_Report.txt so we know to extend this map.
# ─────────────────────────────────────────────────────────────────────────────
MODULE_MAP: Dict[str, Dict[str, Any]] = {
    # DAILY REPORTS
    "daily_reports": {
        "module": "DAILY_REPORTS", "label": "Daily Reports",
        "date_field": "report_date", "group_field": "project_name",
        "title_template": "{id}__{report_date}__{project_name}",
    },
    # SAFETY
    "incidents": {
        "module": "SAFETY", "label": "Incidents",
        "date_field": "incident_date", "group_field": "project_name",
        "title_template": "{id}__{incident_date}__{incident_type}",
    },
    "corrective_actions": {
        "module": "SAFETY", "label": "Corrective Actions",
        "date_field": "created_at", "group_field": "project_name",
        "title_template": "{id}__{created_at}",
    },
    "inspections": {
        "module": "SAFETY", "label": "Safety Inspections / Audits",
        "date_field": "inspection_date", "group_field": "project_name",
        "title_template": "{id}__{inspection_date}__{project_name}",
    },
    "meetings": {
        "module": "SAFETY", "label": "Safety Meetings / Toolbox Talks",
        "date_field": "meeting_date", "group_field": "project_name",
        "title_template": "{id}__{meeting_date}__{topic_title}",
    },
    "jhas": {
        "module": "SAFETY", "label": "Job Hazard Analyses (JHA / JSA)",
        "date_field": "jha_date", "group_field": "project_name",
        "title_template": "{id}__{jha_date}__{project_name}",
    },
    "job_hazard_plans": {
        "module": "SAFETY", "label": "Job Hazard Plans",
        "date_field": "created_at", "group_field": "project_name",
        "title_template": "{id}__{created_at}",
    },
    "fire_extinguishers": {
        "module": "SAFETY", "label": "Fire Extinguishers",
        "date_field": "last_inspection_date", "group_field": "location",
        "title_template": "{id}__{tag_number}",
    },
    "safety_training_records": {
        "module": "TRAINING", "label": "Safety Training Records",
        "date_field": "training_date", "group_field": "course_name",
        "title_template": "{id}__{training_date}__{employee_name}",
    },
    "safety_equipment_issuances": {
        "module": "SAFETY", "label": "Safety Equipment Issuances",
        "date_field": "issued_date", "group_field": "employee_name",
        "title_template": "{id}__{issued_date}",
    },
    "safety_equipment_trainings": {
        "module": "SAFETY", "label": "Safety Equipment Trainings",
        "date_field": "training_date", "group_field": "employee_name",
        "title_template": "{id}__{training_date}",
    },
    "safety_documents": {
        "module": "SAFETY", "label": "Safety Documents",
        "date_field": "uploaded_at", "group_field": "category",
        "title_template": "{id}__{title}",
    },
    "safety_forms": {
        "module": "SAFETY", "label": "Safety Forms",
        "date_field": "created_at", "group_field": None,
        "title_template": "{id}",
    },
    "qaqc_inspections": {
        "module": "SAFETY", "label": "QA/QC Inspections",
        "date_field": "inspection_date", "group_field": "project_name",
        "title_template": "{id}__{inspection_date}",
    },
    # HR
    "field_leadership_records": {
        "module": "HR", "label": "Field Leadership Records (Write-ups, Coaching, Recognition, Termination, etc.)",
        "date_field": "record_date", "group_field": "record_type",
        "title_template": "{id}__{record_date}__{record_type}__{employee_name}",
    },
    "employees": {
        "module": "HR", "label": "Employee Directory",
        "date_field": "hire_date", "group_field": "department",
        "title_template": "{id}__{employee_name}",
    },
    "payroll_variance_batches": {
        "module": "HR", "label": "Payroll Variance Batches",
        "date_field": "created_at", "group_field": "pay_period",
        "title_template": "{id}__{pay_period}",
    },
    "payroll_variance_decisions": {
        "module": "HR", "label": "Payroll Variance Decisions",
        "date_field": "decided_at", "group_field": "employee_name",
        "title_template": "{id}__{decided_at}",
    },
    "document_expirations": {
        "module": "HR", "label": "Document Expirations",
        "date_field": "expires_at", "group_field": "doc_type",
        "title_template": "{id}__{employee_name}__{doc_type}",
    },
    # EQUIPMENT
    "equipment": {
        "module": "EQUIPMENT", "label": "Equipment Records",
        "date_field": "created_at", "group_field": "equipment_type",
        "title_template": "{id}",
    },
    "equipment_master": {
        "module": "EQUIPMENT", "label": "Equipment Master",
        "date_field": None, "group_field": "equipment_type",
        "title_template": "{equipment_unit}",
    },
    "equipment_inspections": {
        "module": "EQUIPMENT", "label": "Equipment Inspections (Pre-Op, Daily, Damage)",
        "date_field": "inspection_date", "group_field": "equipment_unit",
        "title_template": "{id}__{inspection_date}__{equipment_unit}",
    },
    "equipment_parts": {
        "module": "EQUIPMENT", "label": "Equipment Parts",
        "date_field": None, "group_field": "equipment_unit",
        "title_template": "{id}",
    },
    "equipment_units": {
        "module": "EQUIPMENT", "label": "Equipment Units",
        "date_field": None, "group_field": "equipment_type",
        "title_template": "{id}",
    },
    "trench_boxes": {
        "module": "EQUIPMENT", "label": "Trench Boxes",
        "date_field": None, "group_field": None,
        "title_template": "{id}",
    },
    "asset_assignments": {
        "module": "EQUIPMENT", "label": "Asset Assignments",
        "date_field": "assigned_at", "group_field": "asset_id",
        "title_template": "{id}__{assigned_at}",
    },
    "asset_mappings": {
        "module": "EQUIPMENT", "label": "Asset Mappings",
        "date_field": None, "group_field": "source",
        "title_template": "{id}",
    },
    # DISPATCH
    "asset_transfers": {
        "module": "DISPATCH", "label": "Asset Transfers",
        "date_field": "transfer_date", "group_field": "from_project",
        "title_template": "{id}__{transfer_date}",
    },
    "asset_holds": {
        "module": "DISPATCH", "label": "Asset Holds",
        "date_field": "hold_started_at", "group_field": "asset_id",
        "title_template": "{id}__{hold_started_at}",
    },
    "asset_idle_flags": {
        "module": "DISPATCH", "label": "Asset Idle Flags",
        "date_field": "flagged_at", "group_field": "asset_id",
        "title_template": "{id}__{flagged_at}",
    },
    "transfer_requests": {
        "module": "DISPATCH", "label": "Transfer Requests",
        "date_field": "created_at", "group_field": "from_project",
        "title_template": "{id}__{created_at}",
    },
    # TRAINING
    "training_track_records": {
        "module": "TRAINING", "label": "Training Track Records",
        "date_field": "completed_at", "group_field": "course_name",
        "title_template": "{id}__{completed_at}__{employee_name}",
    },
    "training_hits": {
        "module": "TRAINING", "label": "Training Hits / Watches",
        "date_field": "watched_at", "group_field": "video_id",
        "title_template": "{id}__{watched_at}",
    },
    "training_videos": {
        "module": "TRAINING", "label": "Training Videos",
        "date_field": None, "group_field": "category",
        "title_template": "{id}__{title}",
    },
    "training_guides": {
        "module": "TRAINING", "label": "Training Guides",
        "date_field": None, "group_field": "category",
        "title_template": "{id}__{title}",
    },
    # ADMIN / AUDIT
    "admin_audit": {
        "module": "ADMIN_AUDIT", "label": "Admin Audit Log",
        "date_field": "ts", "group_field": "actor",
        "title_template": "{id}__{ts}",
    },
    "audit_events": {
        "module": "ADMIN_AUDIT", "label": "Audit Events",
        "date_field": "ts", "group_field": "kind",
        "title_template": "{id}__{ts}",
    },
    "user_directory": {
        "module": "ADMIN_AUDIT", "label": "User Directory",
        "date_field": "created_at", "group_field": "role_template_id",
        "title_template": "{id}__{email}",
    },
    "role_templates": {
        "module": "ADMIN_AUDIT", "label": "Role Templates",
        "date_field": None, "group_field": None,
        "title_template": "{id}__{name}",
    },
    "deploy_version_history": {
        "module": "ADMIN_AUDIT", "label": "Deploy Version History",
        "date_field": "deployed_at", "group_field": None,
        "title_template": "{id}__{deployed_at}",
    },
    "alert_events": {
        "module": "ADMIN_AUDIT", "label": "Alert Events",
        "date_field": "ts", "group_field": "kind",
        "title_template": "{id}__{ts}",
    },
    "operations_events": {
        "module": "ADMIN_AUDIT", "label": "Operations Events",
        "date_field": "ts", "group_field": "kind",
        "title_template": "{id}__{ts}",
    },
    "usage_events": {
        "module": "ADMIN_AUDIT", "label": "Usage Events",
        "date_field": "ts", "group_field": "kind",
        "title_template": "{id}__{ts}",
    },
    "hub_banner_audit": {
        "module": "ADMIN_AUDIT", "label": "Hub Banner Audit",
        "date_field": "ts", "group_field": None,
        "title_template": "{id}__{ts}",
    },
    "hub_banners": {
        "module": "ADMIN_AUDIT", "label": "Hub Banners",
        "date_field": "created_at", "group_field": None,
        "title_template": "{id}",
    },
    "backup_health": {
        "module": "ADMIN_AUDIT", "label": "Backup Health",
        "date_field": "ts", "group_field": "mode",
        "title_template": "{id}__{ts}",
    },
    # PROJECTS
    "projects": {
        "module": "PROJECTS", "label": "Projects",
        "date_field": "created_at", "group_field": None,
        "title_template": "{id}__{project_name}",
    },
    "jobs_master": {
        "module": "PROJECTS", "label": "Jobs Master",
        "date_field": "created_at", "group_field": None,
        "title_template": "{id}",
    },
}

# Photo subfolder per source module (for PHOTOS_AND_ATTACHMENTS/).
PHOTO_FOLDER_FOR_MODULE = {
    "DAILY_REPORTS": "Daily_Reports",
    "SAFETY": "Safety_Records",
    "HR": "HR",
    "EQUIPMENT": "Equipment",
    "DISPATCH": "Dispatch",
    "TRAINING": "Training",
    "ADMIN_AUDIT": "Admin",
    "PROJECTS": "Projects",
}

# Sensitive fields redacted in human-readable layer. The RAW_JSON/ mirror
# is left untouched — developers/IT need the originals for restore.
REDACT_FIELD_NAMES = {
    "password", "password_hash", "hash", "secret", "api_key",
    "token", "bearer", "auth_token", "session_token", "refresh_token",
    "private_key", "client_secret",
}
REDACT_SUBSTRING_PATTERNS = ("password", "secret", "token", "api_key", "private_key")

# Collections never written to module folders (they still appear in RAW_JSON).
SKIP_HUMAN_READABLE = {
    "admin_users", "hr_users", "shop_users", "dispatch_users",
    "project_managers", "users",
    "signatures",
    "job_photo_thumb_cache",
    "notifications",
    "system_counters",
}

# Photo key regex — matches photos/<YYYY>/<MM>/<source-id>/<uuid>.<ext>
PHOTO_KEY_RX = re.compile(
    r"^photos/(?P<year>\d{4})/(?P<month>\d{2})/(?P<source_id>[^/]+)/(?P<filename>.+)$"
)


# Platform-native PDF kinds — map collection name to the `kind` argument
# accepted by /app/backend/pdf_render.py::render_record_pdf. Anything not
# in this map falls back to the standardized layout in
# /app/backend/export_pdf_fallback.py::render_fallback_pdf.
PLATFORM_PDF_KINDS = {
    "daily_reports": "daily-report",
    "inspections": "inspection",
    "meetings": "meeting",
    "jhas": "jha",
    "incidents": "incident",
    "equipment_inspections": "equipment-inspection",
    "qaqc_inspections": "qaqc",
}

# Collections that have their own dedicated renderer.
USE_FIELD_LEADERSHIP_RENDERER = {"field_leadership_records"}

# Lazy-imported render functions. Backend package must be on sys.path; we
# add /app/backend at module load so the script works from /app/scripts/.
_BACKEND_DIR = Path("/app/backend")
if _BACKEND_DIR.is_dir() and str(_BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(_BACKEND_DIR))


_PHOTO_REF_RX = re.compile(r"^photo://([^/]+)/(.+)$")


def _localize_photo_refs(value: Any, photos_root: Path,
                         hit_counter: Dict[str, int]) -> Any:
    """Walk ``value`` recursively. Any string of the form
    ``photo://<bucket>/<key>`` that resolves to a file in ``photos_root``
    is replaced with a base64 ``data:image/...`` URL so weasyprint can
    embed the photo without network access. Refs that don't resolve are
    left unchanged so the renderer's own fallback (or the fallback PDF's
    "[photo not embedded]" placeholder) handles them.

    ``hit_counter`` is mutated: keys 'resolved' / 'missing' / 'skipped'."""
    if isinstance(value, str) and value.startswith("photo://"):
        m = _PHOTO_REF_RX.match(value)
        if not m:
            hit_counter["skipped"] = hit_counter.get("skipped", 0) + 1
            return value
        key = m.group(2)
        local = photos_root / key
        if not local.is_file():
            hit_counter["missing"] = hit_counter.get("missing", 0) + 1
            return value
        try:
            import base64
            raw = local.read_bytes()
            ext = local.suffix.lstrip(".").lower() or "jpg"
            ct = {
                "png": "image/png", "webp": "image/webp", "avif": "image/avif",
                "heic": "image/heic", "heif": "image/heif", "gif": "image/gif",
            }.get(ext, "image/jpeg")
            hit_counter["resolved"] = hit_counter.get("resolved", 0) + 1
            return f"data:{ct};base64,{base64.b64encode(raw).decode('ascii')}"
        except Exception:
            hit_counter["missing"] = hit_counter.get("missing", 0) + 1
            return value
    if isinstance(value, dict):
        return {k: _localize_photo_refs(v, photos_root, hit_counter) for k, v in value.items()}
    if isinstance(value, list):
        return [_localize_photo_refs(v, photos_root, hit_counter) for v in value]
    return value


def _render_pdf_for_record(
    coll_name: str, record: Dict[str, Any], cfg: Dict[str, Any],
    photos_root: Optional[Path], errors: "ExportErrors",
    timeout_s: int = 20,
) -> Tuple[Optional[bytes], str]:
    """Return (pdf_bytes, strategy) where strategy is one of:
        'platform' | 'field_leadership' | 'fallback' | 'failed'
    Always returns; never raises. (pdf_bytes is None on failed.)

    Defensive timeout (signal.SIGALRM, Unix only): legacy records that
    embedded multi-megabyte base64 photos before iter64 occasionally
    take 30s+ to render. Cap at ``timeout_s`` and fall through to the
    standardized fallback when the platform renderer hangs.
    """
    import signal

    class _RenderTimeout(Exception):
        pass

    def _alarm_handler(signum, frame):  # noqa: ARG001
        raise _RenderTimeout()

    def _run(fn, *args, **kw):
        """Run fn with a SIGALRM-based timeout. Returns the result or
        raises _RenderTimeout / whatever fn raised."""
        if not hasattr(signal, "SIGALRM"):
            return fn(*args, **kw)
        prev = signal.signal(signal.SIGALRM, _alarm_handler)
        signal.alarm(timeout_s)
        try:
            return fn(*args, **kw)
        finally:
            signal.alarm(0)
            signal.signal(signal.SIGALRM, prev)

    # Localize photos so we can embed them into the PDF deterministically.
    hit = {}
    if photos_root and photos_root.is_dir():
        rec_for_pdf = _localize_photo_refs(record, photos_root, hit)
    else:
        rec_for_pdf = record

    # 1. Platform-native renderer (pdf_render.py)?
    if coll_name in PLATFORM_PDF_KINDS:
        try:
            import pdf_render  # type: ignore[import-not-found]
            pdf = _run(pdf_render.render_record_pdf, PLATFORM_PDF_KINDS[coll_name], rec_for_pdf)
            if pdf and pdf[:5] == b"%PDF-":
                return pdf, "platform"
            errors.add("WARN", "pdf_platform_invalid", coll_name, "non-PDF bytes returned")
        except _RenderTimeout:
            errors.add("WARN", "pdf_platform_timeout", coll_name,
                       f"exceeded {timeout_s}s — using fallback")
        except Exception as e:  # noqa: BLE001
            errors.add("WARN", "pdf_platform_failed", coll_name, repr(e)[:300])

    # 2. Field-leadership-specific renderer
    if coll_name in USE_FIELD_LEADERSHIP_RENDERER:
        try:
            import field_leadership_pdf  # type: ignore[import-not-found]
            pdf = _run(field_leadership_pdf.render_field_leadership_pdf, rec_for_pdf)
            if pdf and pdf[:5] == b"%PDF-":
                return pdf, "field_leadership"
            errors.add("WARN", "pdf_fl_invalid", coll_name, "non-PDF bytes returned")
        except _RenderTimeout:
            errors.add("WARN", "pdf_fl_timeout", coll_name,
                       f"exceeded {timeout_s}s — using fallback")
        except Exception as e:  # noqa: BLE001
            errors.add("WARN", "pdf_fl_failed", coll_name, repr(e)[:300])

    # 3. Standardized fallback
    try:
        from export_pdf_fallback import render_fallback_pdf  # type: ignore[import-not-found]
        # Build a friendly title from the title_template the index uses.
        title = _format_title(cfg.get("title_template", "{id}"), record)
        kind_label = cfg.get("label", coll_name)
        pdf = _run(render_fallback_pdf, rec_for_pdf,
                   kind_label=kind_label, record_title=title)
        if pdf and pdf[:5] == b"%PDF-":
            return pdf, "fallback"
        errors.add("WARN", "pdf_fallback_invalid", coll_name, "non-PDF bytes returned")
    except _RenderTimeout:
        errors.add("WARN", "pdf_fallback_timeout", coll_name,
                   f"exceeded {timeout_s}s — skipping PDF")
    except Exception as e:  # noqa: BLE001
        errors.add("WARN", "pdf_fallback_failed", coll_name, repr(e)[:300])

    return None, "failed"


# ═════════════════════════════════════════════════════════════════════════════
# Errors / counters
# ═════════════════════════════════════════════════════════════════════════════
@dataclass
class ExportErrors:
    rows: List[Dict[str, str]] = field(default_factory=list)

    def add(self, level: str, where: str, what: str, detail: str = "") -> None:
        self.rows.append({
            "level": level, "where": where, "what": what,
            "detail": detail[:500],
            "ts": datetime.now(timezone.utc).isoformat(),
        })
        if level == "ERROR":
            logger.error("[%s] %s: %s", where, what, detail[:200])
        elif level == "WARN":
            logger.warning("[%s] %s: %s", where, what, detail[:200])

    def write(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=["ts", "level", "where", "what", "detail"])
            w.writeheader()
            for r in self.rows:
                w.writerow(r)

    def count(self, level: str) -> int:
        return sum(1 for r in self.rows if r["level"] == level)


# ═════════════════════════════════════════════════════════════════════════════
# Helpers
# ═════════════════════════════════════════════════════════════════════════════
def _safe_segment(s: Any, max_len: int = 80) -> str:
    """Make a string filesystem-safe and human-readable."""
    if s is None:
        return "unknown"
    s = str(s).strip()
    if not s:
        return "unknown"
    s = re.sub(r"[^\w\-. ]+", "_", s)
    s = re.sub(r"\s+", "_", s)
    s = s.strip("._-") or "unknown"
    return s[:max_len]


def _date_segment(value: Any) -> str:
    if value is None:
        return "undated"
    s = str(value)
    m = re.match(r"^(\d{4}-\d{2}-\d{2})", s)
    if m:
        return m.group(1)
    return _safe_segment(s, max_len=20)


def _redact(obj: Any) -> Any:
    """Recursively redact sensitive fields. Returns a NEW structure; does
    not mutate input."""
    if isinstance(obj, dict):
        out = {}
        for k, v in obj.items():
            kl = str(k).lower()
            if kl in REDACT_FIELD_NAMES or any(p in kl for p in REDACT_SUBSTRING_PATTERNS):
                out[k] = "***REDACTED***"
            else:
                out[k] = _redact(v)
        return out
    if isinstance(obj, list):
        return [_redact(v) for v in obj]
    return obj


def _flatten_for_csv(doc: Dict[str, Any], prefix: str = "", max_depth: int = 2) -> Dict[str, str]:
    """Flatten a doc into CSV-friendly key/value pairs. Lists become JSON
    strings; nested dicts are dotted up to max_depth, then JSON-stringified."""
    out: Dict[str, str] = {}
    for k, v in doc.items():
        key = f"{prefix}{k}"
        if isinstance(v, dict):
            if max_depth > 0:
                out.update(_flatten_for_csv(v, prefix=f"{key}.", max_depth=max_depth - 1))
            else:
                out[key] = json.dumps(v, default=str)
        elif isinstance(v, list):
            # If it's a list of scalars, join with " | "; else JSON.
            if v and all(not isinstance(x, (dict, list)) for x in v):
                out[key] = " | ".join(str(x) for x in v)
            else:
                out[key] = json.dumps(v, default=str)[:2000]
        elif v is None:
            out[key] = ""
        else:
            s = str(v)
            out[key] = s if len(s) <= 4000 else s[:4000] + "…[truncated]"
    return out


def _format_title(template: str, doc: Dict[str, Any]) -> str:
    """Best-effort safe format. Missing keys become 'unknown'."""
    class _SafeDict(dict):
        def __missing__(self, key):
            return "unknown"
    safe = _SafeDict({k: _safe_segment(v, max_len=40) for k, v in doc.items()})
    try:
        return template.format_map(safe)
    except Exception:
        return _safe_segment(doc.get("id", "record"))


def _file_sha256(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


# ═════════════════════════════════════════════════════════════════════════════
# Exporter
# ═════════════════════════════════════════════════════════════════════════════
class Exporter:
    def __init__(
        self,
        source_dir: Path,
        out_dir: Path,
        company_name: str = "MASCI",
        modules: Optional[List[str]] = None,
        dry_run: bool = False,
        source_label: str = "",
        render_pdfs: bool = True,
    ):
        self.source_dir = source_dir
        self.out_dir = out_dir
        self.company_name = company_name
        self.modules_filter = set(m.upper() for m in modules) if modules else None
        self.dry_run = dry_run
        self.source_label = source_label or source_dir.name
        self.errors = ExportErrors()
        self.render_pdfs = render_pdfs

        # Bookkeeping
        self.records_seen: Dict[str, int] = defaultdict(int)
        self.records_written: Dict[str, int] = defaultdict(int)
        self.records_skipped_collection: Dict[str, int] = defaultdict(int)
        self.photos_total = 0
        self.photos_associated = 0
        self.photos_orphaned = 0
        self.pdfs_platform = 0
        self.pdfs_field_leadership = 0
        self.pdfs_fallback = 0
        self.pdfs_failed = 0
        self.unmapped_collections: List[str] = []
        self.index_rows: List[Dict[str, str]] = []
        self.started_at = datetime.now(timezone.utc)

        # Build record-id → (collection, module) map for photo association.
        self.id_to_collection: Dict[str, str] = {}

    # ── stage 0: discover ────────────────────────────────────────────────
    def discover(self) -> Dict[str, List[Path]]:
        """Walk source_dir/<collection>/json/*.json and group by collection.
        Treats both flat layouts and the platform's canonical layout."""
        by_collection: Dict[str, List[Path]] = defaultdict(list)
        if not self.source_dir.exists():
            self.errors.add("ERROR", "discover", "source not found", str(self.source_dir))
            return by_collection

        for json_dir in self.source_dir.rglob("json"):
            if not json_dir.is_dir():
                continue
            # Collection name is the parent directory name. Normalize
            # hyphens to underscores so "daily-reports" → "daily_reports".
            coll_name = json_dir.parent.name.replace("-", "_")
            for f in json_dir.glob("*.json"):
                by_collection[coll_name].append(f)
        return by_collection

    # ── stage 1: records ─────────────────────────────────────────────────
    def export_records(self, by_collection: Dict[str, List[Path]]) -> None:
        for coll_name in sorted(by_collection):
            files = by_collection[coll_name]
            self.records_seen[coll_name] = len(files)

            if coll_name in SKIP_HUMAN_READABLE:
                self.records_skipped_collection[coll_name] = len(files)
                self.errors.add("INFO", "export_records",
                                "skipped (security-sensitive collection)",
                                f"{coll_name} ({len(files)} records left in RAW_JSON/)")
                continue

            cfg = MODULE_MAP.get(coll_name)
            if not cfg:
                self.unmapped_collections.append(coll_name)
                cfg = {
                    "module": "OTHER", "label": coll_name,
                    "date_field": None, "group_field": None,
                    "title_template": "{id}",
                }

            module = cfg["module"]
            if self.modules_filter and module not in self.modules_filter:
                self.records_skipped_collection[coll_name] = len(files)
                continue

            self._export_one_collection(coll_name, files, cfg)

    def _export_one_collection(
        self, coll_name: str, files: List[Path], cfg: Dict[str, Any]
    ) -> None:
        module = cfg["module"]
        label = cfg["label"]
        date_field = cfg.get("date_field")
        group_field = cfg.get("group_field")
        title_template = cfg.get("title_template", "{id}")

        # CSV columns are the UNION of all keys observed (in order of first
        # appearance) so the spreadsheet has every field anyone might want.
        csv_columns: List[str] = []
        csv_seen: set = set()
        csv_rows: List[Dict[str, str]] = []

        records_dir = self.out_dir / module / _safe_segment(label, 60)
        csv_dir = self.out_dir / module / "CSV"
        if not self.dry_run:
            records_dir.mkdir(parents=True, exist_ok=True)
            csv_dir.mkdir(parents=True, exist_ok=True)

        for fp in files:
            try:
                doc = json.loads(fp.read_text(encoding="utf-8"))
            except Exception as e:
                self.errors.add("WARN", "parse_json", f"bad json: {fp.name}", str(e))
                continue

            if not isinstance(doc, dict):
                self.errors.add("WARN", "parse_json", f"non-dict json: {fp.name}", "")
                continue

            rec_id = str(doc.get("id") or fp.stem)
            self.id_to_collection[rec_id] = coll_name

            redacted = _redact(doc)
            title = _format_title(title_template, redacted)

            # Per-record JSON path
            out_path = records_dir / f"{_safe_segment(title, 120)}.json"
            pdf_rel_path = ""
            if not self.dry_run:
                # If a name collision occurs (same title, different record),
                # suffix with a short hash.
                if out_path.exists():
                    h = hashlib.md5(rec_id.encode()).hexdigest()[:8]
                    out_path = records_dir / f"{_safe_segment(title, 110)}__{h}.json"
                out_path.write_text(json.dumps(redacted, indent=2, default=str), encoding="utf-8")

                # Stage B — per-record PDF (hybrid). Render the ORIGINAL
                # (un-redacted) record so the PDF matches what users would
                # have printed live — passwords/tokens are stripped by the
                # platform's own templates already; the fallback renderer
                # has its own _HIDDEN_FIELDS set as belt-and-braces.
                # PDF render failures NEVER crash the export.
                if self.render_pdfs:
                    photos_root = self.source_dir / "photos"
                    pdf_bytes, strategy = _render_pdf_for_record(
                        coll_name, doc, cfg,
                        photos_root if photos_root.exists() else None,
                        self.errors,
                    )
                    if pdf_bytes is not None:
                        pdf_path = out_path.with_suffix(".pdf")
                        try:
                            pdf_path.write_bytes(pdf_bytes)
                            pdf_rel_path = str(pdf_path.relative_to(self.out_dir))
                        except Exception as e:  # noqa: BLE001
                            self.errors.add("WARN", "pdf_write", coll_name, str(e))
                            strategy = "failed"
                    if strategy == "platform":
                        self.pdfs_platform += 1
                    elif strategy == "field_leadership":
                        self.pdfs_field_leadership += 1
                    elif strategy == "fallback":
                        self.pdfs_fallback += 1
                    else:
                        self.pdfs_failed += 1

            # CSV row (flat)
            flat = _flatten_for_csv(redacted)
            for k in flat:
                if k not in csv_seen:
                    csv_seen.add(k)
                    csv_columns.append(k)
            csv_rows.append(flat)

            # Index row
            date_val = doc.get(date_field) if date_field else None
            group_val = doc.get(group_field) if group_field else None
            self.index_rows.append({
                "module": module,
                "collection": coll_name,
                "record_type": label,
                "record_id": rec_id,
                "date": _date_segment(date_val) if date_val else "",
                "group": _safe_segment(group_val, 60) if group_val else "",
                "title": title,
                "json_path": str(out_path.relative_to(self.out_dir)) if not self.dry_run else "",
                "pdf_path": pdf_rel_path,
                "raw_json_path": f"RAW_JSON/{coll_name}/{fp.name}",
                "csv_path": f"{module}/CSV/{coll_name}.csv",
                "photo_paths": "",  # filled in stage 2
            })

            self.records_written[coll_name] += 1

        # Write CSV
        if csv_rows and not self.dry_run:
            csv_path = csv_dir / f"{coll_name}.csv"
            try:
                with csv_path.open("w", newline="", encoding="utf-8") as f:
                    w = csv.DictWriter(f, fieldnames=csv_columns, extrasaction="ignore")
                    w.writeheader()
                    for row in csv_rows:
                        w.writerow(row)
            except Exception as e:
                self.errors.add("ERROR", "csv_write", f"{coll_name}.csv", str(e))

    # ── stage 2: photos ──────────────────────────────────────────────────
    def export_photos(self) -> None:
        photos_root = self.source_dir / "photos"
        if not photos_root.exists():
            return

        out_root = self.out_dir / "PHOTOS_AND_ATTACHMENTS"
        orphan_root = out_root / "ORPHANED_FILES"
        if not self.dry_run:
            out_root.mkdir(parents=True, exist_ok=True)

        photo_to_record: Dict[str, str] = {}
        orphan_index: List[Dict[str, str]] = []

        for p in photos_root.rglob("*"):
            if not p.is_file():
                continue
            self.photos_total += 1
            rel = p.relative_to(photos_root)
            # The platform's per-photo storage key (set in photo_storage.py)
            # already starts with "photos/", so the in-zip path is
            # "photos/<key>" → on disk after extract it's just "<key>".
            # i.e. rel ALREADY equals the canonical key.
            key = rel.as_posix()
            m = PHOTO_KEY_RX.match(key)
            raw_source_id = m.group("source_id") if m else None

            # The platform's source_id convention is "<collection>_<record-id>"
            # (e.g. "meetings_d17748f0-…"). Strip the collection prefix if it
            # matches a known collection. Fall back to the raw value so
            # bare-id fixtures and unknown prefixes still work.
            source_id = raw_source_id
            if raw_source_id and "_" in raw_source_id:
                for coll in MODULE_MAP:
                    prefix = f"{coll}_"
                    if raw_source_id.startswith(prefix):
                        source_id = raw_source_id[len(prefix):]
                        break
            coll = self.id_to_collection.get(source_id) if source_id else None
            cfg = MODULE_MAP.get(coll) if coll else None
            module = cfg["module"] if cfg else None

            if module and module in PHOTO_FOLDER_FOR_MODULE:
                self.photos_associated += 1
                dest_dir = out_root / PHOTO_FOLDER_FOR_MODULE[module] / _safe_segment(source_id, 60)
                photo_to_record[key] = source_id  # noqa: F841 (tracked elsewhere)
            else:
                self.photos_orphaned += 1
                dest_dir = orphan_root / (rel.parent.as_posix() or "unknown")
                orphan_index.append({
                    "source_path": str(rel),
                    "source_id_guess": source_id or "",
                    "reason": "no matching record" if source_id else "unparseable key",
                })

            if self.dry_run:
                continue

            try:
                dest_dir.mkdir(parents=True, exist_ok=True)
                dest = dest_dir / p.name
                if dest.exists():
                    dest = dest_dir / f"{p.stem}__{hashlib.md5(key.encode()).hexdigest()[:6]}{p.suffix}"
                shutil.copy2(p, dest)
            except Exception as e:
                self.errors.add("WARN", "photo_copy", str(rel), str(e))

        # Stitch photo paths into EXPORT_INDEX rows that match by record id.
        if photo_to_record:
            by_id: Dict[str, List[str]] = defaultdict(list)
            for key, rid in photo_to_record.items():
                by_id[rid].append(key)
            for row in self.index_rows:
                paths = by_id.get(row["record_id"])
                if paths:
                    row["photo_paths"] = " | ".join(paths)

        # Orphan index
        if orphan_index and not self.dry_run:
            orphan_root.mkdir(parents=True, exist_ok=True)
            with (orphan_root / "INDEX.csv").open("w", newline="", encoding="utf-8") as f:
                w = csv.DictWriter(f, fieldnames=["source_path", "source_id_guess", "reason"])
                w.writeheader()
                for r in orphan_index:
                    w.writerow(r)

    # ── stage 3: RAW_JSON mirror ─────────────────────────────────────────
    def mirror_raw_json(self) -> None:
        if self.dry_run:
            return
        raw_root = self.out_dir / "RAW_JSON"
        raw_root.mkdir(parents=True, exist_ok=True)
        for json_dir in self.source_dir.rglob("json"):
            if not json_dir.is_dir():
                continue
            coll_name = json_dir.parent.name
            dst = raw_root / coll_name
            try:
                shutil.copytree(json_dir, dst, dirs_exist_ok=True)
            except Exception as e:
                self.errors.add("WARN", "raw_json_mirror", coll_name, str(e))

    # ── stage 4: artefacts ───────────────────────────────────────────────
    def write_index(self) -> None:
        if self.dry_run:
            return
        path = self.out_dir / "EXPORT_INDEX.csv"
        cols = ["module", "collection", "record_type", "record_id",
                "date", "group", "title", "json_path", "pdf_path",
                "raw_json_path", "csv_path", "photo_paths"]
        with path.open("w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=cols)
            w.writeheader()
            for r in self.index_rows:
                w.writerow(r)

    def write_data_dictionary(self) -> None:
        if self.dry_run:
            return
        path = self.out_dir / "DATA_DICTIONARY.csv"
        with path.open("w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["module", "collection", "human_label", "date_field",
                        "group_field", "in_human_readable_export", "notes"])
            seen = set()
            for coll, cfg in MODULE_MAP.items():
                if coll in seen:
                    continue
                seen.add(coll)
                w.writerow([
                    cfg["module"], coll, cfg["label"],
                    cfg.get("date_field") or "", cfg.get("group_field") or "",
                    "no" if coll in SKIP_HUMAN_READABLE else "yes",
                    "credentials redacted" if coll in SKIP_HUMAN_READABLE else "",
                ])

    def write_readme(self) -> None:
        if self.dry_run:
            return
        path = self.out_dir / "README_START_HERE.txt"
        text = f"""\
{self.company_name} OPERATIONS PLATFORM — HUMAN-READABLE EXPORT
================================================================

Generated:        {self.started_at.isoformat()}
Source backup:    {self.source_label}
Total records:    {sum(self.records_written.values())} written
Total photos:     {self.photos_total} ({self.photos_associated} associated, {self.photos_orphaned} orphaned)
Errors:           {self.errors.count('ERROR')}    Warnings: {self.errors.count('WARN')}

WHAT THIS ARCHIVE IS
--------------------
This is an *operator-friendly* export of every operational record stored
in your {self.company_name} Operations Platform at the time of the source
backup. It is designed so a non-technical person (manager, supervisor,
HR, safety, attorney, auditor) can open it on any computer and use it
without needing developer help.

HOW TO USE IT (in 30 seconds)
-----------------------------
1. Find what you need in EXPORT_INDEX.csv (opens in Excel / Sheets).
   Every record we have is listed there with its title, date, project,
   and the path to its file.
2. Open the folder for the area you want:
       DAILY_REPORTS/       — every daily report
       SAFETY/              — incidents, JHAs, inspections, toolbox talks,
                              fire extinguishers, safety training records
       HR/                  — write-ups, coaching, recognition, evaluations,
                              terminations, payroll variance
       EQUIPMENT/           — equipment master, inspections, parts, assignments
       DISPATCH/            — asset transfers, holds, idle flags
       TRAINING/            — training records, certifications, videos
       ADMIN_AUDIT/         — audit log, user directory, role templates
       PROJECTS/            — project list
3. For spreadsheet review, open the CSV/ folder inside any module — every
   CSV opens in Excel / Google Sheets / Power BI / Tableau.
4. Photos are in PHOTOS_AND_ATTACHMENTS/, grouped by module and record.
5. For technical / developer use, RAW_JSON/ contains the original record
   files exactly as they sit in the platform. Hand this to IT.

FILE LAYOUT
-----------
README_START_HERE.txt          ← you are here
MANIFEST.json                  ← machine-readable inventory
EXPORT_INDEX.csv               ← every exported record, one row each
DATA_DICTIONARY.csv            ← what each module / field means
PHOTOS_AND_ATTACHMENTS/        ← every photo, by module + record
DAILY_REPORTS/                 ← daily reports
SAFETY/                        ← safety records (incidents, JHAs, …)
HR/                            ← personnel records
EQUIPMENT/                     ← equipment records
DISPATCH/                      ← dispatch records
TRAINING/                      ← training records
ADMIN_AUDIT/                   ← audit + admin records
PROJECTS/                      ← project + jobs records
OTHER/                         ← collections not yet mapped to a module
RAW_JSON/                      ← original platform JSON (for IT / developers)
SYSTEM/Backup_Info.txt         ← about the source backup
SYSTEM/Export_Log.txt          ← full run log
SYSTEM/Export_Errors.csv       ← errors / warnings (zero is good)
SYSTEM/Verification_Report.txt ← QA report — read this for trust signals

PRIVACY / SECURITY NOTES
------------------------
• Passwords, API keys, tokens, and secrets are REDACTED in the module
  folders. They remain present in RAW_JSON/ for technical recovery only.
• Authentication-only collections (admin_users, hr_users, shop_users,
  dispatch_users, project_managers, users) are NOT exported into the
  module folders. They are in RAW_JSON/ for IT.
• Treat this archive as you would treat your HR files. It contains
  personnel, safety, and operational records.

THINGS THIS EXPORT DOES NOT DO YET
----------------------------------
• Per-record printable PDFs — coming in Stage B. For now, use the JSON
  files (text-readable) or click into the live platform's "Download PDF"
  on each record.
• Admin UI button — coming in Stage C. For now, this is a CLI script run
  by an admin.

QUESTIONS / VERIFICATION
------------------------
• Open SYSTEM/Verification_Report.txt for the QA summary (record counts,
  errors, source backup hash).
• Hand this entire zip to your auditor or attorney — they can review
  everything without platform access.
• To restore the platform from a backup, use the technical layer
  (RAW_JSON/ + the original backup zip + the restore drill procedure).
  This human-readable export is NOT meant for restore.

POWERED BY FORGEDOPS™
"""
        path.write_text(text, encoding="utf-8")

    def write_manifest(self, source_hash: str = "") -> None:
        if self.dry_run:
            return
        path = self.out_dir / "MANIFEST.json"
        m = {
            "company_name": self.company_name,
            "generated_at": self.started_at.isoformat(),
            "exporter_version": "stage-A-1",
            "source": {
                "label": self.source_label,
                "sha256": source_hash,
            },
            "totals": {
                "records_written": sum(self.records_written.values()),
                "records_seen": sum(self.records_seen.values()),
                "photos_total": self.photos_total,
                "photos_associated": self.photos_associated,
                "photos_orphaned": self.photos_orphaned,
                "pdfs_platform": self.pdfs_platform,
                "pdfs_field_leadership": self.pdfs_field_leadership,
                "pdfs_fallback": self.pdfs_fallback,
                "pdfs_failed": self.pdfs_failed,
                "errors": self.errors.count("ERROR"),
                "warnings": self.errors.count("WARN"),
            },
            "per_collection": {
                k: {"seen": self.records_seen.get(k, 0),
                    "written": self.records_written.get(k, 0)}
                for k in sorted(set(list(self.records_seen.keys()) + list(self.records_written.keys())))
            },
            "unmapped_collections": self.unmapped_collections,
            "modules_filter": sorted(self.modules_filter) if self.modules_filter else None,
        }
        path.write_text(json.dumps(m, indent=2, default=str), encoding="utf-8")

    def write_verification(self, source_hash: str = "") -> None:
        # Always written — even in dry-run — so operators can preview the
        # plan before committing disk to a full export.
        path = self.out_dir / "SYSTEM" / "Verification_Report.txt"
        path.parent.mkdir(parents=True, exist_ok=True)
        ended_at = datetime.now(timezone.utc)
        elapsed = (ended_at - self.started_at).total_seconds()

        lines = [
            f"{self.company_name} Operations Platform — Human-Readable Export Verification Report",
            "=" * 78,
            f"Started:   {self.started_at.isoformat()}",
            f"Ended:     {ended_at.isoformat()}",
            f"Elapsed:   {elapsed:.1f} s",
            "",
            f"Source backup: {self.source_label}",
            f"Source SHA-256: {source_hash or 'n/a'}",
            f"Modules filter: {sorted(self.modules_filter) if self.modules_filter else 'ALL'}",
            "",
            f"TOTAL RECORDS WRITTEN: {sum(self.records_written.values())}",
            f"TOTAL RECORDS SEEN:    {sum(self.records_seen.values())}",
            f"PHOTOS TOTAL:          {self.photos_total}",
            f"  associated:          {self.photos_associated}",
            f"  orphaned:            {self.photos_orphaned}",
            f"PDFS RENDERED:         {self.pdfs_platform + self.pdfs_field_leadership + self.pdfs_fallback}",
            f"  platform-template:   {self.pdfs_platform}",
            f"  field-leadership:    {self.pdfs_field_leadership}",
            f"  standardized:        {self.pdfs_fallback}",
            f"  failed:              {self.pdfs_failed}",
            f"ERRORS:                {self.errors.count('ERROR')}",
            f"WARNINGS:              {self.errors.count('WARN')}",
            "",
            "Per-collection breakdown",
            "-" * 78,
        ]
        for coll in sorted(set(list(self.records_seen.keys()) + list(self.records_written.keys()))):
            seen = self.records_seen.get(coll, 0)
            written = self.records_written.get(coll, 0)
            skipped = self.records_skipped_collection.get(coll, 0)
            mapped = "yes" if coll in MODULE_MAP else "no"
            sec = "yes" if coll in SKIP_HUMAN_READABLE else "no"
            lines.append(
                f"  {coll:<36} seen={seen:>5}  written={written:>5}  "
                f"skipped_collection={skipped:>5}  mapped={mapped:<4} security_skip={sec}"
            )
        lines.append("")
        if self.unmapped_collections:
            lines.append("Unmapped collections (landed in OTHER/):")
            for c in sorted(set(self.unmapped_collections)):
                lines.append(f"  - {c}")
            lines.append("")

        verdict = "PASS"
        if self.errors.count("ERROR") > 0:
            verdict = "PASS WITH ERRORS"
        if sum(self.records_written.values()) == 0:
            verdict = "FAIL — no records written"
        lines.append(f"VERDICT: {verdict}")
        path.write_text("\n".join(lines), encoding="utf-8")

    # ── orchestration ────────────────────────────────────────────────────
    def run(self, source_hash: str = "") -> Dict[str, Any]:
        if not self.dry_run:
            self.out_dir.mkdir(parents=True, exist_ok=True)
        logger.info("source: %s", self.source_dir)
        logger.info("output: %s", self.out_dir)

        by_collection = self.discover()
        logger.info("discovered %d collections", len(by_collection))

        try:
            self.export_records(by_collection)
        except Exception as e:
            self.errors.add("ERROR", "export_records", "fatal", traceback.format_exc())
            logger.exception("export_records fatal: %s", e)

        try:
            self.export_photos()
        except Exception as e:
            self.errors.add("ERROR", "export_photos", "fatal", traceback.format_exc())
            logger.exception("export_photos fatal: %s", e)

        try:
            self.mirror_raw_json()
        except Exception as e:
            self.errors.add("ERROR", "mirror_raw_json", "fatal", traceback.format_exc())
            logger.exception("mirror_raw_json fatal: %s", e)

        self.write_index()
        self.write_data_dictionary()
        self.write_readme()
        self.write_manifest(source_hash=source_hash)
        self.write_verification(source_hash=source_hash)

        if not self.dry_run:
            self.errors.write(self.out_dir / "SYSTEM" / "Export_Errors.csv")
            (self.out_dir / "SYSTEM").mkdir(parents=True, exist_ok=True)
            (self.out_dir / "SYSTEM" / "Backup_Info.txt").write_text(
                f"Source: {self.source_label}\nSHA-256: {source_hash or 'n/a'}\n"
                f"Source path at export time: {self.source_dir}\n",
                encoding="utf-8",
            )

        return {
            "records_written": sum(self.records_written.values()),
            "records_seen": sum(self.records_seen.values()),
            "photos_total": self.photos_total,
            "photos_associated": self.photos_associated,
            "photos_orphaned": self.photos_orphaned,
            "pdfs_platform": self.pdfs_platform,
            "pdfs_field_leadership": self.pdfs_field_leadership,
            "pdfs_fallback": self.pdfs_fallback,
            "pdfs_failed": self.pdfs_failed,
            "errors": self.errors.count("ERROR"),
            "warnings": self.errors.count("WARN"),
            "unmapped_collections": sorted(set(self.unmapped_collections)),
        }


# ═════════════════════════════════════════════════════════════════════════════
# CLI
# ═════════════════════════════════════════════════════════════════════════════
def _ts_compact() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d_%H%M%SZ")


def main() -> int:
    ap = argparse.ArgumentParser(
        description="MASCI human-readable backup exporter (Stage A: CSV + photos + index)",
    )
    src = ap.add_mutually_exclusive_group(required=True)
    src.add_argument("--backup", help="Path to a MASCI complete backup zip")
    src.add_argument("--from-source-folder",
                     help="Path to an already-extracted backup folder")

    ap.add_argument("--out", required=True, help="Output directory")
    ap.add_argument("--company-name",
                    default=os.environ.get("EXPORT_COMPANY_NAME", "MASCI"),
                    help="Company name used in archive filename (env: EXPORT_COMPANY_NAME)")
    ap.add_argument("--modules", default="",
                    help="Comma-separated module filter (e.g. SAFETY,HR). Default: all")
    ap.add_argument("--no-zip", action="store_true",
                    help="Leave the output as a folder; do not zip")
    ap.add_argument("--no-pdf", action="store_true",
                    help="Skip per-record PDF generation (Stage B). Faster.")
    ap.add_argument("--dry-run", action="store_true",
                    help="Count records and write Verification_Report.txt only")
    args = ap.parse_args()

    out_dir = Path(args.out).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    company = args.company_name.strip() or "MASCI"
    safe_company = re.sub(r"[^A-Za-z0-9_-]+", "_", company).strip("_") or "MASCI"
    archive_stem = f"{safe_company}_HUMAN_READABLE_EXPORT_{_ts_compact()}"
    export_folder = out_dir / archive_stem

    source_label = ""
    source_hash = ""

    with tempfile.TemporaryDirectory(prefix="masci_export_src_") as tmp:
        if args.backup:
            zp = Path(args.backup).resolve()
            if not zp.exists():
                print(f"FAIL: --backup not found: {zp}", file=sys.stderr)
                return 2
            source_label = zp.name
            try:
                source_hash = _file_sha256(zp)
            except Exception:
                source_hash = ""
            logger.info("extracting %s to %s", zp, tmp)
            with zipfile.ZipFile(zp, "r") as zf:
                zf.extractall(tmp)
            source_dir = Path(tmp)
        else:
            source_dir = Path(args.from_source_folder).resolve()
            if not source_dir.exists():
                print(f"FAIL: --from-source-folder not found: {source_dir}", file=sys.stderr)
                return 2
            source_label = source_dir.name

        modules = [m.strip() for m in args.modules.split(",") if m.strip()] or None
        exp = Exporter(
            source_dir=source_dir,
            out_dir=export_folder,
            company_name=company,
            modules=modules,
            dry_run=args.dry_run,
            source_label=source_label,
            render_pdfs=not args.no_pdf,
        )
        result = exp.run(source_hash=source_hash)

    print("")
    print("─" * 78)
    print(f"Export folder: {export_folder}")
    print(f"  records_written     : {result['records_written']}")
    print(f"  records_seen        : {result['records_seen']}")
    print(f"  photos_total        : {result['photos_total']}")
    print(f"    associated        : {result['photos_associated']}")
    print(f"    orphaned          : {result['photos_orphaned']}")
    print(f"  errors / warnings   : {result['errors']} / {result['warnings']}")
    print(f"  PDFs                 : {result['pdfs_platform']+result['pdfs_field_leadership']+result['pdfs_fallback']} "
          f"(platform={result['pdfs_platform']}, "
          f"field-leadership={result['pdfs_field_leadership']}, "
          f"fallback={result['pdfs_fallback']}, "
          f"failed={result['pdfs_failed']})")
    if result["unmapped_collections"]:
        print(f"  unmapped_collections: {', '.join(result['unmapped_collections'])}")
    print("─" * 78)

    if args.dry_run:
        print("DRY-RUN — wrote Verification_Report.txt only, no records emitted.")
        return 0

    if args.no_zip:
        print(f"OK — left as folder: {export_folder}")
        return 0

    zip_path = out_dir / f"{archive_stem}.zip"
    logger.info("zipping %s → %s", export_folder, zip_path)
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED, compresslevel=6) as zf:
        for p in export_folder.rglob("*"):
            if p.is_file():
                zf.write(p, p.relative_to(out_dir))
    # Clean up the staged folder; zip is the final deliverable.
    shutil.rmtree(export_folder, ignore_errors=True)
    print(f"OK — wrote {zip_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
