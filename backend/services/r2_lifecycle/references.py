"""
Phase 2/3 · Ownership resolver + database cross-reference.

This module holds the EXTENSIBLE registry of Mongo collections that
legitimately reference R2 objects. Each source describes:

- `collection`     — the Mongo collection name.
- `owner`          — the human-readable owner label (e.g. "Daily Report").
- `feature`        — the platform feature (e.g. "daily_reports").
- `paths`          — a list of JSONPath-style dot paths where R2 refs
                     may appear. Wildcards `*` traverse arrays.
- `ref_scheme`     — the string scheme this source uses ("photo://",
                     "r2://", or "raw_key" for direct S3 keys).

The walker extracts every R2 key mentioned by any document in the
listed collections and persists them to `r2_references`, keyed by the
extracted R2 key. This is the source-of-truth Mongo → R2 back-index
that the classifier consumes.

Adding a new source is a one-line append to `REFERENCE_SOURCES`;
no code change elsewhere.
"""
from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, Iterable, List, Optional, Tuple
from uuid import uuid4

logger = logging.getLogger(__name__)


# ── Reference source registry ──────────────────────────────────────────
@dataclass
class ReferenceSource:
    collection: str
    owner: str
    feature: str
    paths: List[str]
    ref_scheme: str = "photo://"  # photo:// | r2:// | raw_key
    doc_id_field: str = "id"

    def as_dict(self) -> Dict[str, Any]:
        return {
            "collection": self.collection,
            "owner": self.owner,
            "feature": self.feature,
            "paths": self.paths,
            "ref_scheme": self.ref_scheme,
        }


# Extend this list — never hardcode outside it.
REFERENCE_SOURCES: List[ReferenceSource] = [
    # `photos` collection stayed empty in practice — daily_reports/etc.
    # store photo:// URIs directly in top-level arrays. Kept here for
    # forward compatibility (any future photo-index rebuild lands here).
    ReferenceSource("photos",                "Photo",             "photos",           ["storage_ref", "url", "photo_ref"]),
    # `daily_reports.photos` is a list of raw photo:// strings.
    # TRACK 27.07B repair C · `daily_reports.attachments[*]` are dicts
    # whose R2 refs live in the `attachment_ref` field per Track 19.04.
    ReferenceSource("daily_reports",         "Daily Report",      "daily_reports",    ["photos.*", "attachments.*", "attachments.*.attachment_ref"]),
    ReferenceSource("meetings",              "Meeting",           "meetings",         ["photos.*", "attachments.*", "attachments.*.attachment_ref"]),
    ReferenceSource("qaqc_inspections",      "QA/QC Inspection",  "qaqc",             ["photos.*", "photo_captions.*", "attachments.*", "attachments.*.attachment_ref"]),
    ReferenceSource("site_inspections",      "Site Inspection",   "site_inspections", ["photos.*", "attachments.*", "attachments.*.attachment_ref"]),
    # `incidents.photos` is base64 data URIs — no R2 reference. Keep
    # attachments-style paths only in case a future migration lands.
    ReferenceSource("incidents",             "Incident",          "incidents",        ["evidence.*", "evidence.*.attachment_ref", "attachments.*", "attachments.*.attachment_ref"]),
    ReferenceSource("training_records",      "Training Record",   "training",         ["media.*", "media.*.attachment_ref", "attachments.*", "attachments.*.attachment_ref"]),
    # Documents with raw-key pattern (bucket embedded in the key).
    ReferenceSource("equipment_documents",   "Equipment Document","equipment",        ["storage_ref", "url", "file_ref"]),
    ReferenceSource("asset_documents",       "Asset Document",    "assets",           ["storage_ref", "url", "file_ref"]),
    ReferenceSource("dispatch_continuity",   "Dispatch Evidence", "dispatch",         ["photos.*", "attachments.*", "attachments.*.attachment_ref"]),
    ReferenceSource("legacy_imports",        "Historical Import", "legacy_imports",   ["source_document_ref", "photos.*", "attachments.*.attachment_ref"]),
    # Operational attachments — uses `r2_key` (raw key, not photo:// URI).
    ReferenceSource("operational_attachments","Operational Attachment","attachments", ["r2_key"], ref_scheme="raw_key"),
    # Carrier + driver document store — uses `file_ref` (photo:// URI).
    # `file_key` also has R2 key but with bucket prefix, so keep photo:// path.
    ReferenceSource("carrier_documents",     "Carrier Document",  "carriers",         ["file_ref"]),
    ReferenceSource("driver_documents",      "Driver Document",   "drivers",          ["file_ref"]),
    # HR employee records — uses `source_file_ref` (photo:// URI).
    ReferenceSource("employee_records",      "Employee Record",   "hr",               ["source_file_ref"]),
    ReferenceSource("promo_assets",          "Promo Asset",       "promo_assets",     ["storage_ref", "url"]),
    ReferenceSource("pdf_packages",          "PDF Package",       "pdf_packages",     ["storage_ref", "url"]),
    ReferenceSource("exports",               "Export",            "exports",          ["storage_ref", "url"]),
    # Backups — the recovery archives themselves. These are BACKUP_PROTECTED.
    ReferenceSource("backup_health",         "Backup Archive",    "backups",          ["filename", "key", "url"], ref_scheme="raw_key"),
    ReferenceSource("recovery_snapshots",    "Recovery Snapshot", "recovery",         ["archive_key", "key"], ref_scheme="raw_key"),
    # TRACK 27.07B repair A · Safety Portal document library.
    # `safety_documents.file_data` holds a `doc://<bucket>/<key>` URI
    # (see backend/routes/safety_portal/documents.py + safety_doc_storage.py).
    ReferenceSource("safety_documents",      "Safety Document",   "safety_documents", ["file_data"], ref_scheme="doc://"),
    # TRACK 27.07B repair A · Fire-extinguisher attachments live as an
    # array of dicts on the `fire_extinguishers` doc; each dict carries
    # `file_data: doc://<bucket>/<key>` (backend/routes/safety_portal/
    # fire_ext_attachments.py L143). Nested traversal + `doc://` scheme.
    ReferenceSource("fire_extinguishers",    "Fire Extinguisher Attachment", "fire_extinguishers",
                                             ["attachments.*.file_data"], ref_scheme="doc://"),
]


# ── Reference extraction ───────────────────────────────────────────────
_PHOTO_REF_RE = re.compile(r"^photo://([^/]+)/(.+)$")
_R2_REF_RE = re.compile(r"^r2://([^/]+)/(.+)$")
_DOC_REF_RE = re.compile(r"^doc://([^/]+)/(.+)$")   # TRACK 27.07B repair B
_HTTP_R2_HOST_RE = re.compile(
    r"^https?://[^/]*(?:r2\.cloudflarestorage\.com|s3[.-][^/]+\.amazonaws\.com|r2\.dev)/[^/]+/(.+?)(?:\?.*)?$"
)


def _percent_decode(s: str) -> str:
    from urllib.parse import unquote  # noqa: PLC0415 — lazy
    try:
        return unquote(s)
    except Exception:  # noqa: BLE001
        return s


def _extract_key(ref: Any, scheme: str) -> Optional[str]:
    """Return the R2 key portion of ``ref``, or None if ``ref`` doesn't
    match the expected scheme.

    Malformed references, mismatched buckets, and non-string values
    return None (the caller counts these as *unresolved* — they never
    become owner references, and they never become orphans either).
    """
    if not ref or not isinstance(ref, str):
        return None
    # TRACK 27.07B repair B · Also handle full HTTPS R2/S3 URLs
    # regardless of the source's declared scheme (some legacy fields
    # persist a full URL rather than a photo:///doc:// URI).
    m = _HTTP_R2_HOST_RE.match(ref)
    if m:
        return _percent_decode(m.group(1).lstrip("/"))
    if scheme == "photo://":
        m = _PHOTO_REF_RE.match(ref)
        return _percent_decode(m.group(2)) if m else None
    if scheme == "r2://":
        m = _R2_REF_RE.match(ref)
        return _percent_decode(m.group(2)) if m else None
    if scheme == "doc://":
        m = _DOC_REF_RE.match(ref)
        return _percent_decode(m.group(2)) if m else None
    if scheme == "raw_key":
        # Direct S3 key — accept only if it looks like a path (no scheme prefix).
        if "://" in ref:
            return None
        return _percent_decode(ref.lstrip("/"))
    return None


def _walk_path(doc: Dict[str, Any], path: str) -> Iterable[Any]:
    """Yield every value at the JSONPath-style dot path in ``doc``.
    A `*` segment expands array elements. Missing keys are silent."""
    parts = path.split(".")
    stack: List[Tuple[int, Any]] = [(0, doc)]
    while stack:
        depth, node = stack.pop()
        if depth == len(parts):
            yield node
            continue
        seg = parts[depth]
        if seg == "*":
            if isinstance(node, list):
                for item in node:
                    stack.append((depth + 1, item))
            continue
        if isinstance(node, dict) and seg in node:
            stack.append((depth + 1, node[seg]))


async def scan_mongo_references(db, *, now: Optional[datetime] = None) -> Dict[str, Any]:
    """Walk every registered reference source and persist a fresh
    Mongo → R2 back-index into `r2_references`. Prior rows are
    truncated so stale references don't cause false VERIFIED_OWNER
    classifications."""
    now = now or datetime.now(timezone.utc)
    run_id = f"ref-{uuid4().hex[:12]}"

    await db.r2_references.delete_many({})

    total_sources_scanned = 0
    total_refs_found = 0
    total_unresolved = 0
    by_source: Dict[str, int] = {}
    unresolved_by_source: Dict[str, int] = {}
    failed_sources: List[Dict[str, Any]] = []
    ops: List[Dict[str, Any]] = []

    for source in REFERENCE_SOURCES:
        try:
            total_sources_scanned += 1
            source_hits = 0
            source_unresolved = 0
            # TRACK 27.07B repair · Project the full top-level field for
            # every path, because nested paths like `attachments.*.attachment_ref`
            # require the entire array (not just a projected sub-key).
            projection: Dict[str, int] = {"_id": 0, source.doc_id_field: 1}
            for p in source.paths:
                projection[p.split(".")[0]] = 1
            cursor = db[source.collection].find({}, projection)
            async for doc in cursor:
                doc_id = doc.get(source.doc_id_field) or doc.get("_id")
                for p in source.paths:
                    for val in _walk_path(doc, p):
                        # Skip container types silently — the walker
                        # yields them when a path terminates on an
                        # array element that turned out to be a dict.
                        if not isinstance(val, str):
                            continue
                        key = _extract_key(val, source.ref_scheme)
                        if key is None:
                            # TRACK 27.07B repair D · malformed / foreign
                            # bucket references are counted as UNRESOLVED
                            # rather than silently dropped. They surface
                            # via ``unresolved_by_source`` so downstream
                            # classification can't turn ambiguity into
                            # a false orphan.
                            source_unresolved += 1
                            total_unresolved += 1
                            continue
                        ops.append({
                            "r2_key": key,
                            "collection": source.collection,
                            "owner": source.owner,
                            "feature": source.feature,
                            "doc_id": str(doc_id) if doc_id is not None else None,
                            "field_path": p,
                            "raw_ref": val,
                            "captured_at": now.isoformat(),
                            "run_id": run_id,
                        })
                        source_hits += 1
                        total_refs_found += 1
                        if len(ops) >= 500:
                            await db.r2_references.insert_many(ops, ordered=False)
                            ops.clear()
            by_source[source.collection] = source_hits
            unresolved_by_source[source.collection] = source_unresolved
        except Exception as e:  # noqa: BLE001
            # TRACK 27.07B repair E · A failed reference source is a
            # completeness blocker — the classifier MUST NOT produce
            # VERIFIED_ORPHANs when any mandatory source failed.
            logger.warning(
                "[r2-references] source failed: %s: %s",
                source.collection, e,
            )
            by_source[source.collection] = 0
            unresolved_by_source[source.collection] = 0
            failed_sources.append({"collection": source.collection, "error": str(e)[:240]})
    if ops:
        await db.r2_references.insert_many(ops, ordered=False)

    complete = not failed_sources
    summary = {
        "run_id": run_id,
        "kind": "references",
        "started_at": now.isoformat(),
        "completed_at": datetime.now(timezone.utc).isoformat(),
        "sources_scanned": total_sources_scanned,
        "references_found": total_refs_found,
        "unresolved_refs": total_unresolved,
        "refs_by_source": by_source,
        "unresolved_by_source": unresolved_by_source,
        "failed_sources": failed_sources,
        "complete": complete,
    }
    await db.r2_lifecycle_runs.insert_one(dict(summary))
    return summary


async def reference_summary(db) -> Dict[str, Any]:
    row = await db.r2_lifecycle_runs.find_one(
        {"kind": "references"}, {"_id": 0}, sort=[("completed_at", -1)],
    )
    return row or {"has_data": False}
