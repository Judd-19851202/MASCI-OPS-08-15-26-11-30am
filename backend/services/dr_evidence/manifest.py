"""TRACK 24.13 · Daily Report canonical Evidence Manifest.

The manifest is the ONLY input the AI summary engine is permitted to
reason over. It is built from:

* the saved Daily Report document (V1 legacy shape)
* the analyzed photo intelligence rows
  (:mod:`services.photo_intelligence`)
* the document-extraction results for every attachment
  (:mod:`services.dr_evidence.extract`)
* material-ticket reconciliation
  (:mod:`services.dr_evidence.materials`)

The AI prompt is instructed to treat any field marked
``extraction_status`` outside ``extracted`` as **metadata only** — it
must not describe file contents it did not see.

Hashing
-------
:func:`manifest_hash` returns a stable SHA-256 of the sorted manifest
JSON, minus timestamps + confidence floats. Two manifests built from
the same DR + attachments produce the same hash — the AI summary layer
uses this hash for its own caching.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from .materials import (
    NormalizedTicket,
    normalize_ticket_row,
    reconcile_tickets,
    tickets_from_rows,
)


MANIFEST_VERSION = "24.13.1"


# ── Data shapes ─────────────────────────────────────────────────────

@dataclass
class ManifestAttachment:
    id: str = ""
    filename: str = ""
    mime: str = ""
    size_bytes: int = 0
    source_section: str = ""
    extraction_status: str = "not_started"
    extraction_reason: str = ""
    text_preview: str = ""
    row_count: int = 0
    page_count: int = 0
    sheet_names: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    confidence: float = 0.0
    file_hash: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class ManifestPhoto:
    id: str = ""
    ref: str = ""
    caption: str = ""
    source: str = ""
    analysis_status: str = "not_started"
    narrative: str = ""
    observations: List[Dict[str, Any]] = field(default_factory=list)
    confidence: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class EvidenceManifest:
    version: str = MANIFEST_VERSION
    generated_at: str = ""
    report_id: str = ""
    project_number: str = ""
    project_name: str = ""
    client: str = ""
    project_manager: str = ""
    location: str = ""
    report_date: str = ""
    supervisor_name: str = ""
    weather: Dict[str, Any] = field(default_factory=dict)
    gps_location: str = ""
    # Structured typed fields (mirrored, never filtered).
    typed_fields: Dict[str, Any] = field(default_factory=dict)
    # Attachments, one row per uploaded doc.
    attachments: List[ManifestAttachment] = field(default_factory=list)
    # Photos + grounded observations.
    photos: List[ManifestPhoto] = field(default_factory=list)
    # Ticket reconciliation output (advisory).
    material_reconciliation: Dict[str, Any] = field(default_factory=dict)
    # Cross-cutting warnings the AI + PDF should surface.
    warnings: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "version": self.version,
            "generated_at": self.generated_at,
            "report_id": self.report_id,
            "project_number": self.project_number,
            "project_name": self.project_name,
            "client": self.client,
            "project_manager": self.project_manager,
            "location": self.location,
            "report_date": self.report_date,
            "supervisor_name": self.supervisor_name,
            "weather": self.weather,
            "gps_location": self.gps_location,
            "typed_fields": self.typed_fields,
            "attachments": [a.to_dict() for a in self.attachments],
            "photos": [p.to_dict() for p in self.photos],
            "material_reconciliation": self.material_reconciliation,
            "warnings": self.warnings,
        }


# ── Manifest builder ────────────────────────────────────────────────

_TYPED_FIELD_GROUPS = (
    "masci_crews", "visitors", "equipment_used", "equipment", "materials",
    "outbound_materials", "subcontractors", "vendors", "activity_cards",
    "constraint_cards", "tomorrow_readiness", "safety_quality",
    "near_misses", "excavation", "competent_person", "work_stoppage",
    "general_notes", "photo_captions", "photo_observations",
    "production", "constraints", "safety", "signatures",
)


def _typed_fields_from_report(report: Dict[str, Any]) -> Dict[str, Any]:
    out: Dict[str, Any] = {}
    for k in _TYPED_FIELD_GROUPS:
        v = report.get(k)
        if v in (None, "", [], {}):
            continue
        out[k] = v
    return out


def _photos_from_intelligence(
    report: Dict[str, Any], photo_intel: Optional[Dict[str, Any]],
) -> List[ManifestPhoto]:
    out: List[ManifestPhoto] = []
    intel_rows = ((photo_intel or {}).get("photos") or [])
    intel_by_id = {r.get("photo_id"): r for r in intel_rows}

    def _walk(items: Any, source: str) -> None:
        if not isinstance(items, list):
            return
        for item in items:
            if isinstance(item, dict):
                pid = item.get("id") or item.get("key") or item.get("ref") or ""
                ref = item.get("ref") or item.get("url") or item.get("key") or ""
                caption = item.get("caption") or ""
            else:
                pid = str(item)
                ref = str(item)
                caption = ""
            # Match against intelligence store by trimmed id if present.
            row = None
            for k, r in intel_by_id.items():
                if k and k in (pid or "") or (ref and (r.get("photo_ref") == ref)):
                    row = r
                    break
            mp = ManifestPhoto(
                id=str(pid)[:64], ref=str(ref)[:512], caption=caption[:280],
                source=source,
            )
            if row:
                mp.analysis_status = row.get("analysis_status") or "not_started"
                mp.narrative = (row.get("narrative") or "")[:280]
                mp.observations = [
                    {
                        "label": o.get("label"),
                        "description": o.get("description"),
                        "category": o.get("category"),
                        "confidence": o.get("confidence"),
                    }
                    for o in (row.get("observations") or [])[:12]
                ]
                mp.confidence = float(row.get("confidence") or 0.0)
            out.append(mp)

    _walk(report.get("photos"), "photos")
    for sub in (report.get("subcontractors") or []):
        if isinstance(sub, dict):
            _walk(sub.get("photos"), "subcontractor_photos")
    for m in (report.get("materials") or []):
        if isinstance(m, dict):
            _walk(m.get("ticket_photos"), "material_ticket_photos")
    return out


def _reconcile_materials(
    report: Dict[str, Any],
    attachments: List[ManifestAttachment],
    extracted_row_map: Dict[str, List[List[str]]],
) -> Dict[str, Any]:
    """Build the material ticket reconciliation payload.

    ``extracted_row_map`` maps ``attachment_id → rows`` (from the
    :class:`ExtractionResult`) so we can pull ticket-like rows out of
    XLSX/CSV attachments without re-extracting.
    """
    entered = [
        normalize_ticket_row(m, source="entered")
        for m in (report.get("materials") or [])
        if isinstance(m, dict)
    ] + [
        # V3 outbound materials may exist separately.
        normalize_ticket_row(m, source="entered")
        for m in (report.get("outbound_materials") or [])
        if isinstance(m, dict)
    ]

    extracted: List[NormalizedTicket] = []
    for att in attachments:
        if att.extraction_status != "extracted":
            continue
        rows = extracted_row_map.get(att.id) or []
        if not rows:
            continue
        source = "xlsx" if att.mime and "spreadsheet" in att.mime else "csv"
        if att.filename.lower().endswith(".xls"):
            source = "xlsx"
        if att.filename.lower().endswith(".csv"):
            source = "csv"
        extracted.extend(tickets_from_rows(rows, source=source))

    if not entered and not extracted:
        return {"entered": [], "extracted": [], "matched": [],
                "unmatched_entered": [], "unmatched_extracted": [],
                "quantity_totals": {}, "advisories": [], "confidence": 0.0}
    return reconcile_tickets(entered, extracted).to_dict()


def build_manifest(
    report: Dict[str, Any],
    *,
    attachment_extractions: Optional[List[Dict[str, Any]]] = None,
    photo_intel: Optional[Dict[str, Any]] = None,
) -> EvidenceManifest:
    """Build a :class:`EvidenceManifest` for a Daily Report.

    Parameters
    ----------
    report
        Legacy Daily Report doc (or draft) — same shape as
        ``db.daily_reports``.
    attachment_extractions
        Optional list of ``{id, filename, mime, size_bytes,
        source_section, extraction: ExtractionResult}`` dicts.
    photo_intel
        Optional aggregated intel envelope from
        :func:`services.photo_intelligence.pipeline.list_report_intelligence`.
    """
    m = EvidenceManifest()
    m.generated_at = datetime.now(timezone.utc).isoformat()  # TRACK-27.03-EXEMPT: machine manifest metadata; never rendered directly to operators (frontend/PDF formats it)
    m.report_id = (
        report.get("doc_id")
        or report.get("report_number")
        or report.get("id") or ""
    )
    m.project_number = report.get("project_number") or ""
    m.project_name = report.get("project_name") or ""
    m.client = report.get("client") or ""
    m.project_manager = report.get("project_manager") or ""
    m.location = report.get("location") or ""
    m.report_date = report.get("report_date") or ""
    m.supervisor_name = (
        report.get("supervisor_name") or report.get("prepared_by") or ""
    )
    m.weather = report.get("weather") or {}
    m.gps_location = report.get("gps_location") or ""
    m.typed_fields = _typed_fields_from_report(report)

    # Attachments.
    extracted_row_map: Dict[str, List[List[str]]] = {}
    for a in attachment_extractions or []:
        ext = a.get("extraction") or {}
        ma = ManifestAttachment(
            id=str(a.get("id") or ""),
            filename=a.get("filename") or "",
            mime=a.get("mime") or "",
            size_bytes=int(a.get("size_bytes") or ext.get("ext_meta", {}).get("size_bytes") or 0),
            source_section=a.get("source_section") or "",
            extraction_status=ext.get("status") or "not_started",
            extraction_reason=ext.get("reason") or "",
            text_preview=(ext.get("text") or "")[:2000],
            row_count=len(ext.get("rows") or []),
            page_count=int(ext.get("page_count") or 0),
            sheet_names=list(ext.get("sheet_names") or []),
            warnings=list(ext.get("warnings") or []),
            confidence=float(ext.get("confidence") or 0.0),
            file_hash=str(a.get("file_hash") or ""),
        )
        m.attachments.append(ma)
        if ext.get("rows"):
            extracted_row_map[ma.id] = list(ext.get("rows"))

    # Photos.
    m.photos = _photos_from_intelligence(report, photo_intel)

    # Materials reconciliation.
    m.material_reconciliation = _reconcile_materials(
        report, m.attachments, extracted_row_map,
    )

    # Warnings surface the manifest-level truthful limitations.
    for att in m.attachments:
        if att.extraction_status in (
            "unsupported", "too_large", "encrypted", "corrupt", "failed",
            "scanned_pdf_no_text",
        ):
            m.warnings.append(
                f"{att.filename}: {att.extraction_status}"
                + (f" ({att.extraction_reason})" if att.extraction_reason else "")
            )
    if photo_intel and photo_intel.get("pending"):
        m.warnings.append(
            f"{photo_intel['pending']} photo(s) still analyzing — "
            "AI summary may miss visual observations."
        )
    return m


# ── Hash ────────────────────────────────────────────────────────────

_HASH_EXCLUDE_KEYS = {"generated_at", "confidence"}


def _strip_for_hash(value: Any) -> Any:
    if isinstance(value, dict):
        return {
            k: _strip_for_hash(v)
            for k, v in sorted(value.items())
            if k not in _HASH_EXCLUDE_KEYS
        }
    if isinstance(value, list):
        return [_strip_for_hash(v) for v in value]
    return value


def manifest_hash(manifest: EvidenceManifest | Dict[str, Any]) -> str:
    """Stable SHA-256 hash for AI-cache lookups."""
    if isinstance(manifest, EvidenceManifest):
        payload = manifest.to_dict()
    else:
        payload = dict(manifest or {})
    body = json.dumps(_strip_for_hash(payload), sort_keys=True, default=str)
    return "sha256:" + hashlib.sha256(body.encode("utf-8")).hexdigest()


# ── AI-facing bundle ────────────────────────────────────────────────

def manifest_to_ai_bundle(m: EvidenceManifest) -> Dict[str, Any]:
    """Compact bundle for the AI prompt.

    We downsize photos and attachments to their AI-relevant fields so
    a 40-photo, 20-attachment DR still fits inside a reasonable prompt
    budget (~8 K input tokens).
    """
    return {
        "manifest_version": m.version,
        "report": {
            "report_id": m.report_id,
            "project_number": m.project_number,
            "project_name": m.project_name,
            "client": m.client,
            "project_manager": m.project_manager,
            "location": m.location,
            "report_date": m.report_date,
            "supervisor_name": m.supervisor_name,
            "weather": m.weather,
            "gps_location": m.gps_location,
        },
        "typed_fields": m.typed_fields,
        "attachments": [
            {
                "filename": a.filename,
                "source_section": a.source_section,
                "extraction_status": a.extraction_status,
                "extraction_reason": a.extraction_reason,
                # Trim the text preview to keep token budget bounded.
                "text_preview": (a.text_preview or "")[:1200],
                "page_count": a.page_count,
                "row_count": a.row_count,
                "sheet_names": a.sheet_names,
                "warnings": a.warnings,
                "confidence": a.confidence,
            }
            for a in m.attachments[:30]
        ],
        "photos": [
            {
                "id": p.id,
                "source": p.source,
                "caption": p.caption,
                "analysis_status": p.analysis_status,
                "narrative": p.narrative,
                "observations": p.observations,
                "confidence": p.confidence,
            }
            for p in m.photos[:40]
        ],
        "material_reconciliation": m.material_reconciliation,
        "warnings": m.warnings,
    }


__all__ = [
    "MANIFEST_VERSION",
    "EvidenceManifest",
    "ManifestAttachment",
    "ManifestPhoto",
    "build_manifest",
    "manifest_hash",
    "manifest_to_ai_bundle",
]
