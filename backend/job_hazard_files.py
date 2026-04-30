"""
job_hazard_files.py — multi-file library, used for:
  • scope="jha"  — Job Hazard plans keyed by project_number
  • scope="trench_box"  — manufacturer tabulated-data PDFs + educational
                          resources keyed by box_id (or "general")

Same storage engine for both (disk for >8 MB, inline base64 below). This
module is generic; callers decide the scope + key at upload time. Legacy
JHA callers that omit scope are treated as scope="jha" for backwards
compatibility.

Schema (db.job_hazard_files):
  id              str (uuid)
  scope           "jha" | "trench_box"   (defaults to "jha")
  project_number  str (scope=jha)  OR trench_box_id (scope=trench_box)
                   OR "general" for shared educational docs
  filename        str
  content_type    str
  file_size       int
  storage         "inline" | "disk"
  file_data       base64 data URL (inline only)
  file_path       str (disk only, rel to STORAGE_ROOT)
  notes           str
  uploaded_by     str
  uploaded_at     iso-utc
"""
from __future__ import annotations

import base64
import logging
import re
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from fastapi import HTTPException, UploadFile

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Storage layout
# ---------------------------------------------------------------------------
STORAGE_ROOT = Path("/app/backend/storage/jha_plans").resolve()
STORAGE_ROOT.mkdir(parents=True, exist_ok=True)

# Inline-vs-disk threshold: anything ≤ 8 MB is base64-encoded into Mongo
# for fast list/download. Anything bigger streams to disk.
DISK_THRESHOLD = 8 * 1024 * 1024

# Hard cap per file. Bumped to 250 MB so a full FDOT plan set zip fits.
MAX_FILE_BYTES = 250 * 1024 * 1024

# Allowed extensions (everything common). Extension is informational only —
# we don't run magic-byte validation on these because crews legitimately
# upload PDFs, Word, Excel, photos, and ZIPs from many sources.
ALLOWED_EXTENSIONS = {
    "pdf",
    "xlsx", "xls", "csv",
    "docx", "doc", "rtf", "odt",
    "txt", "md",
    "png", "jpg", "jpeg", "heic", "heif", "webp", "gif",
    "zip", "7z", "tar", "gz",
    "dwg", "dxf",
    "kml", "kmz", "shp",
    "mp4", "mov",   # crews have asked for short safety briefing videos
}

# Filename safety regex
_SAFE_NAME_CHARS = re.compile(r"[^A-Za-z0-9._\-]+")


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _safe_filename(name: str) -> str:
    base = (name or "").strip() or f"upload-{uuid.uuid4().hex[:8]}"
    # Strip any path components — never trust client.
    base = base.replace("\\", "/").split("/")[-1]
    base = _SAFE_NAME_CHARS.sub("_", base)
    if len(base) > 200:
        # Keep the extension when truncating
        if "." in base:
            stem, ext = base.rsplit(".", 1)
            base = stem[: 195 - len(ext)] + "." + ext
        else:
            base = base[:200]
    return base


def _ext_of(name: str) -> str:
    if "." not in name:
        return ""
    return name.rsplit(".", 1)[-1].lower()


def _project_dir(project_number: str) -> Path:
    """Disk dir for a project. Sanitized to a flat slug."""
    slug = _SAFE_NAME_CHARS.sub("_", project_number.strip())[:80] or "_unknown"
    p = STORAGE_ROOT / slug
    p.mkdir(parents=True, exist_ok=True)
    return p


def _doc_to_summary(d: Dict[str, Any]) -> Dict[str, Any]:
    """Strip heavy fields for list responses — never return file_data."""
    return {
        "id": d.get("id"),
        "scope": d.get("scope", "jha"),
        "project_number": d.get("project_number"),
        "filename": d.get("filename"),
        "content_type": d.get("content_type"),
        "file_size": d.get("file_size", 0),
        "storage": d.get("storage", "inline"),
        "notes": d.get("notes", ""),
        "uploaded_by": d.get("uploaded_by", ""),
        "uploaded_at": d.get("uploaded_at"),
    }


# ---------------------------------------------------------------------------
# CRUD
# ---------------------------------------------------------------------------
async def list_files_for_project(
    db, project_number: str, scope: str = "jha"
) -> List[Dict[str, Any]]:
    cursor = (
        db.job_hazard_files.find(
            {"project_number": project_number, **_scope_filter(scope)},
            {"_id": 0, "file_data": 0},  # never ship the blob in lists
        ).sort("uploaded_at", 1)
    )
    docs = await cursor.to_list(500)
    return [_doc_to_summary(d) for d in docs]


def _scope_filter(scope: str) -> Dict[str, Any]:
    """Include legacy docs that don't have a scope field (default = jha)."""
    if scope == "jha":
        return {"$or": [{"scope": "jha"}, {"scope": {"$exists": False}}]}
    return {"scope": scope}


async def list_all_files_grouped(
    db, scope: str = "jha"
) -> List[Dict[str, Any]]:
    """List every file in the given scope, grouped by project_number."""
    cursor = (
        db.job_hazard_files.find(
            _scope_filter(scope), {"_id": 0, "file_data": 0}
        ).sort([("project_number", 1), ("uploaded_at", 1)])
    )
    docs = await cursor.to_list(5000)
    grouped: Dict[str, List[Dict[str, Any]]] = {}
    for d in docs:
        pn = d.get("project_number") or "_unknown"
        grouped.setdefault(pn, []).append(_doc_to_summary(d))
    return [
        {"project_number": pn, "files": grouped[pn]}
        for pn in sorted(grouped.keys())
    ]


async def upload_file(
    db,
    project_number: str,
    file: UploadFile,
    notes: str = "",
    uploaded_by: str = "",
    scope: str = "jha",
) -> Dict[str, Any]:
    """Stream the upload to disk (or keep inline for small files), then
    insert a metadata doc into job_hazard_files."""
    pn = (project_number or "").strip()
    if not pn:
        raise HTTPException(400, "project_number is required")
    scope = (scope or "jha").strip().lower()

    fname = _safe_filename(file.filename or "")
    ext = _ext_of(fname)
    if ext and ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            400,
            f"Unsupported file type: .{ext}. Allowed: "
            f"{', '.join(sorted(ALLOWED_EXTENSIONS))}",
        )

    file_id = str(uuid.uuid4())
    # Stream to a temp on-disk path first to learn the size, then decide
    # whether to keep on disk or inline-base64 it. This bounds memory.
    proj_dir = _project_dir(pn)
    disk_name = f"{file_id}.{ext}" if ext else file_id
    disk_path = proj_dir / disk_name

    bytes_written = 0
    chunk_size = 1024 * 1024  # 1 MB chunks
    with disk_path.open("wb") as f_out:
        while True:
            chunk = await file.read(chunk_size)
            if not chunk:
                break
            bytes_written += len(chunk)
            if bytes_written > MAX_FILE_BYTES:
                f_out.close()
                try:
                    disk_path.unlink(missing_ok=True)
                except Exception:
                    pass
                raise HTTPException(
                    413,
                    f"File too large ({bytes_written // (1024*1024)} MB). "
                    f"Max {MAX_FILE_BYTES // (1024*1024)} MB per file.",
                )
            f_out.write(chunk)

    if bytes_written == 0:
        try:
            disk_path.unlink(missing_ok=True)
        except Exception:
            pass
        raise HTTPException(400, "Empty file")

    content_type = (
        file.content_type
        or "application/octet-stream"
    )

    doc: Dict[str, Any] = {
        "id": file_id,
        "scope": scope,
        "project_number": pn,
        "filename": fname,
        "content_type": content_type,
        "file_size": bytes_written,
        "notes": (notes or "").strip(),
        "uploaded_by": (uploaded_by or "").strip(),
        "uploaded_at": _now(),
    }

    # If small enough, inline it and remove the disk copy. Saves disk and
    # keeps the legacy "I can grab any file straight from Atlas" model.
    if bytes_written <= DISK_THRESHOLD:
        try:
            with disk_path.open("rb") as fr:
                raw = fr.read()
            b64 = base64.b64encode(raw).decode("ascii")
            doc["storage"] = "inline"
            doc["file_data"] = f"data:{content_type};base64,{b64}"
            try:
                disk_path.unlink(missing_ok=True)
            except Exception:
                pass
        except Exception as e:  # noqa: BLE001
            logger.warning(f"jha file inline-promotion failed, keeping on disk: {e}")
            doc["storage"] = "disk"
            doc["file_path"] = str(disk_path.relative_to(STORAGE_ROOT))
    else:
        doc["storage"] = "disk"
        doc["file_path"] = str(disk_path.relative_to(STORAGE_ROOT))

    await db.job_hazard_files.insert_one(doc)
    doc.pop("_id", None)
    return _doc_to_summary(doc)


async def get_file_for_download(
    db, file_id: str
) -> Tuple[Dict[str, Any], bytes, Optional[Path]]:
    """Returns (doc, raw_bytes, disk_path).
    For disk-backed files, raw_bytes is empty and the caller should stream
    from disk_path. For inline files, disk_path is None and raw_bytes is the
    decoded payload."""
    doc = await db.job_hazard_files.find_one({"id": file_id}, {"_id": 0})
    if not doc:
        raise HTTPException(404, "File not found")

    storage = doc.get("storage", "inline")
    if storage == "disk":
        rel = doc.get("file_path") or ""
        full = (STORAGE_ROOT / rel).resolve()
        # Path-traversal guard
        if STORAGE_ROOT not in full.parents and full != STORAGE_ROOT:
            raise HTTPException(404, "File not found")
        if not full.exists():
            raise HTTPException(404, "File missing on disk")
        return doc, b"", full

    # inline base64
    raw = b""
    data_url = doc.get("file_data") or ""
    if data_url.startswith("data:"):
        try:
            _, _, b64 = data_url.partition("base64,")
            raw = base64.b64decode(b64)
        except Exception:
            raise HTTPException(500, "Stored file is corrupt")
    return doc, raw, None


async def delete_file(db, file_id: str) -> bool:
    doc = await db.job_hazard_files.find_one({"id": file_id}, {"_id": 0})
    if not doc:
        return False
    # Remove the on-disk file too if any.
    if doc.get("storage") == "disk":
        rel = doc.get("file_path") or ""
        full = (STORAGE_ROOT / rel).resolve() if rel else None
        if full and STORAGE_ROOT in full.parents:
            try:
                full.unlink(missing_ok=True)
            except Exception:
                pass
    res = await db.job_hazard_files.delete_one({"id": file_id})
    return res.deleted_count > 0


async def ensure_indexes(db) -> None:
    try:
        await db.job_hazard_files.create_index([("project_number", 1), ("uploaded_at", 1)])
        await db.job_hazard_files.create_index("id", unique=True)
    except Exception as e:  # noqa: BLE001
        logger.warning(f"job_hazard_files index: {e}")
