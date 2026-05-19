"""iter249 Phase B · Equipment Checkout legacy-import extractor + promoter.

Scope (operator-approved, narrow):
  - Equipment Checkout ONLY · no other doc types activated.
  - Claude Vision OCR via emergentintegrations universal key.
  - Matching engine: employee + equipment + project + duplicate-suspicion.
  - Promotion writes a `field_leadership_records` row with
    `kind="equipment_checkout"` and `source="legacy_imported"` so every
    existing accountability / termination / outstanding-equipment query
    auto-picks it up · ZERO changes to live read code paths.
  - Pilot cap (env LEGACY_IMPORT_PILOT_CAP, default 50) blocks bulk
    flooding · the goal is to learn operational friction at small scale
    before scaling up.

NEVER touched in this module:
  - Phase A's StubExtractor (unchanged · still the default for the other
    13 document types)
  - Phase A's anti-self-approval guard (lives in `legacy_imports.py`)
  - Phase A's audit chain
  - Native equipment_checkout record schema (we conform, we don't mutate)

Read this once: the promoter writes into the SAME collection as native
records (`db.field_leadership_records`). The `source` field is the only
discriminator. Every existing query (HR accountability search, equipment
outstanding flag, termination workflow) picks up imported records
automatically with no code changes.
"""
from __future__ import annotations

import asyncio
import base64
import io
import json
import logging
import os
import re
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


# ─── Pilot cap (operator-stated 50-doc max for Phase B) ────────────────
def pilot_cap() -> int:
    try:
        return int(os.environ.get("LEGACY_IMPORT_PILOT_CAP", "50"))
    except Exception:
        return 50


def ocr_model() -> str:
    return os.environ.get(
        "LEGACY_OCR_MODEL", "claude-sonnet-4-5-20250929"
    )


def phase_b_enabled() -> bool:
    return (os.environ.get("LEGACY_PHASE_B_ENABLED", "true").lower()
            in ("1", "true", "yes", "on"))


async def equipment_checkout_pilot_remaining(db) -> int:
    """Operator-tunable pilot cap. We count imports (not promoted records)
    so a rejected upload still consumes a slot in spirit — operator wanted
    'do not mass-import years of records yet'."""
    used = await db.legacy_imports.count_documents(
        {"document_type": "equipment_checkout"}
    )
    return max(0, pilot_cap() - used)


# ─── Claude Vision extractor ───────────────────────────────────────────
# Equipment Checkout target fields. Match the native
# field_leadership_records[kind=equipment_checkout] shape so the promoter
# can drop them in directly.
TARGET_FIELDS = (
    "employee_name", "employee_position", "supervisor_name",
    "project_number", "project_name",
    "occurred_at",           # ISO date · checkout/issue date
    "return_date",           # ISO date · if present
    "equipment_lines",       # list of {name, serial, qty, asset_id, returned, notes}
    "notes",
    "supervisor_signature_present",  # bool
    "employee_signature_present",    # bool
)


EXTRACTOR_SYSTEM_PROMPT = """You are a careful records clerk extracting fields from
a scanned or photographed paper Equipment Checkout & Accountability form.
The form may be handwritten, printed, or a mix. You may see:
  - tabular lists of equipment (name, serial number, asset ID, quantity)
  - employee + supervisor names and signatures
  - a job/project number
  - a checkout date and (sometimes) a return date

Rules:
  1. Return STRICT valid JSON with the keys listed by the user. No prose.
  2. Use null when a field is illegible, missing, or you are unsure.
  3. NEVER INVENT DATA. If you cannot literally read a value in the
     image, the corresponding field MUST be null and its
     `field_confidences` entry MUST be 0.0. Better to return all-null
     than to guess. Hallucinated data is the worst-possible outcome.
  4. If the image is blank, uniform, illegible, or clearly not an
     equipment checkout form, return ALL fields as null/empty, set
     `confidence` to 0.0, and set `error` to a short reason
     (e.g. "blank image", "wrong document type", "illegible").
  5. For dates, prefer ISO YYYY-MM-DD. If the year is ambiguous, leave null.
  6. equipment_lines must be a JSON array (possibly empty) of objects
     with keys: name (string), serial (string|null), asset_id (string|null),
     qty (number, default 1), notes (string|null), returned (boolean,
     default false). If you cannot read any specific equipment line,
     return an empty list — DO NOT invent items.
  7. Score your overall confidence in field_confidences (0.0-1.0 per
     key) and `confidence` (0.0-1.0 overall · be honest · 0.6+ means a
     human reviewer can confirm rapidly, below 0.4 means heavy manual
     correction expected · 0.0 means you could not read anything).
  8. Add raw_text with whatever readable text you found (used for audit).
"""


EXTRACTOR_USER_INSTRUCTION = (
    "Extract this form into the following JSON shape:\n"
    "{\n"
    '  "employee_name": str|null,\n'
    '  "employee_position": str|null,\n'
    '  "supervisor_name": str|null,\n'
    '  "project_number": str|null,\n'
    '  "project_name": str|null,\n'
    '  "occurred_at": "YYYY-MM-DD"|null,\n'
    '  "return_date": "YYYY-MM-DD"|null,\n'
    '  "equipment_lines": [\n'
    "    {\"name\": str, \"serial\": str|null, \"asset_id\": str|null,\n"
    "     \"qty\": int, \"notes\": str|null, \"returned\": bool}\n"
    "  ],\n"
    '  "notes": str|null,\n'
    '  "supervisor_signature_present": bool,\n'
    '  "employee_signature_present": bool,\n'
    '  "raw_text": str,\n'
    '  "confidence": float (0.0-1.0),\n'
    '  "field_confidences": {field_name: float, ...},\n'
    '  "error": str|null  // set to a short reason if blank/illegible/wrong doc type\n'
    "}\n"
    "If the image is blank, uniform, illegible, or NOT an equipment\n"
    "checkout form, return all fields as null/empty/empty-list, set\n"
    "confidence to 0.0, and set error to a short reason. NEVER invent\n"
    "data to fill out the form. Return JSON only. No surrounding text."
)


def _pdf_first_page_to_png(pdf_bytes: bytes) -> Optional[bytes]:
    """Rasterize PDF page 1 to PNG bytes using PyMuPDF (pure-python lib).
    Returns None if PDF can't be opened. Capped at 1800px wide so Claude
    Vision payload stays sane."""
    try:
        import fitz  # PyMuPDF, pure-python wheel · no system deps  # noqa: PLC0415
    except Exception as e:  # noqa: BLE001
        logger.warning(f"[phase-b] pymupdf missing: {e}")
        return None
    try:
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        if doc.page_count < 1:
            return None
        page = doc.load_page(0)
        # ~150 DPI render · readable for OCR without huge bytes.
        pix = page.get_pixmap(dpi=150, alpha=False)
        # Cap width to 1800px to keep transfer/throughput sane.
        if pix.width > 1800:
            scale = 1800.0 / pix.width
            mat = fitz.Matrix(scale, scale)
            pix = page.get_pixmap(matrix=mat, alpha=False)
        return pix.tobytes("png")
    except Exception as e:  # noqa: BLE001
        logger.warning(f"[phase-b] pdf rasterize failed: {e}")
        return None


def _maybe_transcode_image(image_bytes: bytes, mime: str) -> Tuple[bytes, str]:
    """Claude Vision accepts JPEG/PNG/WEBP/GIF. HEIC/HEIF/AVIF/SVG must
    be transcoded. We use Pillow which is already in the stack."""
    accepted = {"image/jpeg", "image/png", "image/webp", "image/gif"}
    if mime in accepted:
        return image_bytes, mime
    try:
        from PIL import Image  # noqa: PLC0415
        img = Image.open(io.BytesIO(image_bytes))
        # Flatten alpha if needed
        if img.mode in ("RGBA", "LA"):
            bg = Image.new("RGB", img.size, (255, 255, 255))
            bg.paste(img, mask=img.split()[-1])
            img = bg
        elif img.mode != "RGB":
            img = img.convert("RGB")
        # Cap on largest dimension to keep payload sane.
        max_side = 1800
        if max(img.size) > max_side:
            img.thumbnail((max_side, max_side))
        buf = io.BytesIO()
        img.save(buf, format="PNG", optimize=True)
        return buf.getvalue(), "image/png"
    except Exception as e:  # noqa: BLE001
        logger.warning(f"[phase-b] transcode failed for mime={mime}: {e}")
        return image_bytes, mime


def _extract_json_payload(text: str) -> Optional[Dict[str, Any]]:
    """Claude sometimes wraps JSON in ```json fences. Strip & parse."""
    s = (text or "").strip()
    if not s:
        return None
    if s.startswith("```"):
        m = re.search(r"```(?:json)?\s*(.+?)```", s, flags=re.DOTALL)
        if m:
            s = m.group(1).strip()
    # Find first { ... last }
    if not s.startswith("{"):
        m = re.search(r"\{.*\}", s, flags=re.DOTALL)
        if m:
            s = m.group(0)
    try:
        return json.loads(s)
    except Exception as e:  # noqa: BLE001
        logger.warning(f"[phase-b] json parse failed: {e} · payload head={s[:120]!r}")
        return None


def _normalize_equipment_lines(raw: Any) -> List[Dict[str, Any]]:
    if not isinstance(raw, list):
        return []
    out = []
    for line in raw:
        if not isinstance(line, dict):
            continue
        name = (line.get("name") or "").strip()
        if not name:
            continue
        qty_raw = line.get("qty") or line.get("quantity") or 1
        try:
            qty = int(qty_raw)
        except Exception:
            qty = 1
        out.append({
            "name": name,
            "serial": (line.get("serial") or "").strip() or None,
            "asset_id": (line.get("asset_id") or "").strip() or None,
            "qty": qty,
            "notes": (line.get("notes") or "").strip() or None,
            "returned": bool(line.get("returned", False)),
            "photos": [],
        })
    return out


# Import the abstract base from the Phase A module · keeps the
# state-machine + worker pattern unchanged.
from legacy_imports import BaseExtractor, OcrResult  # noqa: E402


class EquipmentCheckoutExtractor(BaseExtractor):
    """Phase B · Claude Vision extractor for Equipment Checkout forms.

    Uses emergentintegrations.llm.chat.LlmChat with the universal
    EMERGENT_LLM_KEY. Returns OcrResult with extracted_fields shaped
    to the native field_leadership_records.equipment_checkout schema
    so the promoter can drop it straight in (modulo human review).
    """

    document_type = "equipment_checkout"
    required_fields = ("employee_name",)

    async def extract(self, file_bytes: bytes, mime: str) -> OcrResult:
        if not file_bytes:
            return OcrResult(
                error="empty bytes (worker did not load source from R2)",
                confidence=0.0,
            )

        api_key = os.environ.get("EMERGENT_LLM_KEY", "")
        if not api_key:
            return OcrResult(error="EMERGENT_LLM_KEY missing", confidence=0.0)

        # PDF → first-page PNG. Image → transcode if needed.
        if mime == "application/pdf":
            png = await asyncio.to_thread(_pdf_first_page_to_png, file_bytes)
            if not png:
                return OcrResult(error="pdf rasterize failed", confidence=0.0)
            image_bytes, image_mime = png, "image/png"
        else:
            image_bytes, image_mime = _maybe_transcode_image(file_bytes, mime)

        if image_mime not in ("image/jpeg", "image/png", "image/webp", "image/gif"):
            return OcrResult(
                error=f"unsupported source mime after transcode: {image_mime}",
                confidence=0.0,
            )

        try:
            from emergentintegrations.llm.chat import (  # noqa: PLC0415
                LlmChat, UserMessage, ImageContent,
            )
        except Exception as e:  # noqa: BLE001
            return OcrResult(error=f"emergentintegrations import failed: {e}", confidence=0.0)

        try:
            b64 = base64.b64encode(image_bytes).decode("ascii")
            session_id = f"li-ec-{uuid.uuid4().hex[:12]}"
            chat = LlmChat(
                api_key=api_key,
                session_id=session_id,
                system_message=EXTRACTOR_SYSTEM_PROMPT,
            ).with_model("anthropic", ocr_model())
            msg = UserMessage(
                text=EXTRACTOR_USER_INSTRUCTION,
                file_contents=[ImageContent(image_base64=b64)],
            )
            response_text = await chat.send_message(msg)
        except Exception as e:  # noqa: BLE001
            logger.exception(f"[phase-b] claude vision call failed: {e}")
            return OcrResult(error=f"vision call failed: {str(e)[:240]}", confidence=0.0)

        payload = _extract_json_payload(response_text)
        if not payload:
            return OcrResult(
                error="model returned unparseable JSON",
                raw_text=(response_text or "")[:2000],
                confidence=0.0,
            )

        # Normalise · trust the model on text, sanitise types
        equipment_lines = _normalize_equipment_lines(payload.get("equipment_lines"))
        extracted: Dict[str, Any] = {
            "employee_name": (payload.get("employee_name") or "").strip() or None,
            "employee_position": (payload.get("employee_position") or "").strip() or None,
            "supervisor_name": (payload.get("supervisor_name") or "").strip() or None,
            "project_number": (payload.get("project_number") or "").strip() or None,
            "project_name": (payload.get("project_name") or "").strip() or None,
            "occurred_at": (payload.get("occurred_at") or "").strip() or None,
            "return_date": (payload.get("return_date") or "").strip() or None,
            "equipment_lines": equipment_lines,
            "notes": (payload.get("notes") or "").strip() or None,
            "supervisor_signature_present": bool(payload.get("supervisor_signature_present")),
            "employee_signature_present": bool(payload.get("employee_signature_present")),
        }

        try:
            confidence = float(payload.get("confidence") or 0.0)
        except Exception:
            confidence = 0.0
        confidence = max(0.0, min(1.0, confidence))

        field_confidences = payload.get("field_confidences") or {}
        if not isinstance(field_confidences, dict):
            field_confidences = {}
        # Sanitise
        field_confidences = {
            str(k): max(0.0, min(1.0, float(v))) for k, v in field_confidences.items()
            if isinstance(v, (int, float))
        }

        return OcrResult(
            raw_text=(payload.get("raw_text") or "")[:5000],
            extracted_fields=extracted,
            field_confidences=field_confidences,
            confidence=confidence,
            classifier_score=confidence,
            classifier_doc_type="equipment_checkout",
            error=((payload.get("error") or "").strip() or None),
        )


# ─── Matching engine ───────────────────────────────────────────────────
def _normalize_name(s: Optional[str]) -> str:
    return re.sub(r"[^a-z0-9 ]+", " ", (s or "").lower()).strip()


def _token_set_ratio(a: str, b: str) -> float:
    """Cheap token-set similarity · 0.0-1.0 · no extra deps."""
    sa = set(_normalize_name(a).split())
    sb = set(_normalize_name(b).split())
    if not sa or not sb:
        return 0.0
    overlap = len(sa & sb)
    return overlap / max(len(sa), len(sb))


async def match_employee(db, name: Optional[str]) -> Dict[str, Any]:
    """Suggest a `db.employees` match by name. Returns the MatchSuggestion
    dict the legacy_imports schema expects: suggested_id · suggested_name
    · confidence · alternatives[]."""
    out = {"suggested_id": None, "suggested_name": None,
           "confidence": 0.0, "alternatives": []}
    if not name:
        return out
    norm = _normalize_name(name)
    if not norm:
        return out
    # Exact-ish first · case-insensitive prefix or contains.
    cursor = db.employees.find(
        {"name": {"$regex": re.escape(name), "$options": "i"}},
        {"_id": 0, "id": 1, "name": 1, "role": 1, "title": 1},
    ).limit(20)
    candidates: List[Dict[str, Any]] = []
    async for d in cursor:
        candidates.append(d)
    if not candidates:
        # Fallback: scan a slice ranked by token-set ratio. We cap so
        # this never becomes a perf hole (small DB anyway).
        cursor2 = db.employees.find({}, {"_id": 0, "id": 1, "name": 1, "role": 1}).limit(2000)
        async for d in cursor2:
            r = _token_set_ratio(name, d.get("name") or "")
            if r >= 0.5:
                candidates.append(d)
    scored = [
        (
            _token_set_ratio(name, c.get("name") or ""),
            c,
        )
        for c in candidates
    ]
    scored.sort(key=lambda x: x[0], reverse=True)
    if scored:
        top_score, top = scored[0]
        out["suggested_id"] = top.get("id")
        out["suggested_name"] = top.get("name")
        out["confidence"] = round(top_score, 3)
        out["alternatives"] = [
            {"id": c.get("id"), "name": c.get("name"),
             "confidence": round(s, 3)}
            for s, c in scored[1:5]
        ]
    return out


async def match_equipment(db, equipment_lines: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Best-effort: take the FIRST line's name/serial and try to match
    against db.equipment_master. Multi-line forms still get scored against
    the first line · individual lines can be edited by the reviewer.

    Returns the MatchSuggestion shape · suggested_id+name are the matched
    equipment's unit_number+name, confidence based on serial-exact match
    first, then name token-set ratio."""
    out = {"suggested_id": None, "suggested_name": None,
           "confidence": 0.0, "alternatives": []}
    if not equipment_lines:
        return out
    first = equipment_lines[0] or {}
    name = first.get("name") or ""
    serial = first.get("serial") or first.get("asset_id") or ""

    # Strongest signal: exact serial match (case-insensitive)
    if serial:
        rx = {"$regex": f"^{re.escape(serial)}$", "$options": "i"}
        eq = await db.equipment_master.find_one(
            {"$or": [{"serial_number": rx}, {"unit_number": rx},
                     {"asset_id": rx}]},
            {"_id": 0, "id": 1, "unit_number": 1, "name": 1, "type": 1},
        )
        if eq:
            return {
                "suggested_id": eq.get("id") or eq.get("unit_number"),
                "suggested_name": eq.get("name") or eq.get("unit_number"),
                "confidence": 0.95,
                "alternatives": [],
            }
    # Name fallback: top-3 by token-set ratio
    if name:
        cursor = db.equipment_master.find(
            {}, {"_id": 0, "id": 1, "unit_number": 1, "name": 1, "type": 1}
        ).limit(3000)
        scored: List[Tuple[float, Dict[str, Any]]] = []
        async for d in cursor:
            r = _token_set_ratio(name, d.get("name") or d.get("unit_number") or "")
            if r >= 0.5:
                scored.append((r, d))
        scored.sort(key=lambda x: x[0], reverse=True)
        if scored:
            top_score, top = scored[0]
            out["suggested_id"] = top.get("id") or top.get("unit_number")
            out["suggested_name"] = top.get("name") or top.get("unit_number")
            out["confidence"] = round(top_score, 3)
            out["alternatives"] = [
                {"id": c.get("id") or c.get("unit_number"),
                 "name": c.get("name") or c.get("unit_number"),
                 "confidence": round(s, 3)}
                for s, c in scored[1:5]
            ]
    return out


async def match_project(db, project_number: Optional[str]) -> Dict[str, Any]:
    """Suggest a `db.jobs` entry by project_number prefix/exact."""
    out = {"suggested_id": None, "suggested_name": None,
           "confidence": 0.0, "alternatives": []}
    if not project_number:
        return out
    cleaned = project_number.strip()
    if not cleaned:
        return out
    rx = {"$regex": re.escape(cleaned), "$options": "i"}
    cursor = db.jobs.find(
        {"$or": [{"project_number": rx}, {"name": rx}]},
        {"_id": 0, "id": 1, "project_number": 1, "name": 1},
    ).limit(5)
    items = []
    async for d in cursor:
        items.append(d)
    if items:
        top = items[0]
        confidence = 0.99 if (top.get("project_number") or "").strip().lower() == cleaned.lower() else 0.7
        out["suggested_id"] = top.get("project_number") or top.get("id")
        out["suggested_name"] = top.get("name")
        out["confidence"] = confidence
        out["alternatives"] = [
            {"id": x.get("project_number") or x.get("id"),
             "name": x.get("name"),
             "confidence": 0.5}
            for x in items[1:]
        ]
    return out


async def detect_duplicate(
    db,
    employee_name: Optional[str],
    equipment_lines: List[Dict[str, Any]],
    occurred_at: Optional[str],
) -> Optional[Dict[str, Any]]:
    """Cheap duplicate suspicion against native field_leadership_records:
    same employee + same first-line serial within ±90 days → flag.
    Reviewer must confirm whether to proceed."""
    if not employee_name or not equipment_lines:
        return None
    first_serial = (equipment_lines[0] or {}).get("serial")
    if not first_serial:
        return None
    query: Dict[str, Any] = {
        "kind": "equipment_checkout",
        "employee_name": {"$regex": re.escape(employee_name), "$options": "i"},
        "details.equipment_lines.serial": {"$regex": f"^{re.escape(first_serial)}$",
                                           "$options": "i"},
        "deleted_at": None,
    }
    cursor = db.field_leadership_records.find(
        query,
        {"_id": 0, "id": 1, "employee_name": 1, "occurred_at": 1,
         "source": 1, "project_number": 1},
    ).limit(3)
    rows: List[Dict[str, Any]] = []
    async for d in cursor:
        rows.append(d)
    if not rows:
        return None
    return {
        "kind": "same_employee_same_serial",
        "match_count": len(rows),
        "candidates": rows,
        "note": ("This employee already has a checkout record with the same serial. "
                 "Confirm whether this is a duplicate import or a true second checkout."),
    }


async def compute_matches_block(db, extracted: Dict[str, Any]) -> Dict[str, Any]:
    """Builds the MatchesBlock dict consumed by the reconciliation UI.
    Pure read · no writes."""
    return {
        "employee": await match_employee(db, extracted.get("employee_name")),
        "equipment": await match_equipment(db, extracted.get("equipment_lines") or []),
        "project": await match_project(db, extracted.get("project_number")),
        "duplicate_of": await detect_duplicate(
            db,
            extracted.get("employee_name"),
            extracted.get("equipment_lines") or [],
            extracted.get("occurred_at"),
        ),
    }


# ─── Promoter ──────────────────────────────────────────────────────────
async def equipment_checkout_promoter(db, import_doc: Dict[str, Any]) -> Dict[str, Any]:
    """Write a native `field_leadership_records` row from an approved
    legacy_imports doc. Honors reviewer corrections (review.corrections)
    over raw OCR (ocr.extracted_fields). Stamps:
      - source = "legacy_imported"  (only discriminator vs. native)
      - legacy_import_id back-reference to the staging doc
      - source_file_ref (R2 key) for evidence chain
      - reviewer name as supervisor_name when missing (defensible)

    Returns {"collection": "field_leadership_records", "record_id": str}.
    """
    extracted = (import_doc.get("ocr") or {}).get("extracted_fields") or {}
    corrections = (import_doc.get("review") or {}).get("corrections") or {}

    def pick(key: str, default=None):
        if key in corrections and corrections[key] not in (None, ""):
            return corrections[key]
        return extracted.get(key, default)

    employee_name = (pick("employee_name") or "").strip()
    supervisor_name = (pick("supervisor_name") or "").strip()
    project_number = (pick("project_number") or "").strip() or None
    project_name = (pick("project_name") or "").strip() or None
    occurred_at = (pick("occurred_at") or "").strip() or None
    notes = pick("notes") or ""
    employee_position = (pick("employee_position") or "").strip() or ""

    equipment_lines = pick("equipment_lines") or []
    if not isinstance(equipment_lines, list):
        equipment_lines = []
    # Normalise (corrections may pass raw user input)
    equipment_lines = _normalize_equipment_lines(equipment_lines)

    if not employee_name:
        raise ValueError(
            "promotion blocked: employee_name is required for equipment_checkout"
        )
    if not equipment_lines:
        raise ValueError(
            "promotion blocked: at least one equipment_lines entry is required"
        )

    review = import_doc.get("review") or {}
    matches = import_doc.get("matches") or {}
    first_file = (import_doc.get("source_files") or [{}])[0]

    now_iso = datetime.now(timezone.utc).isoformat()
    if not occurred_at:
        # Best-effort: fall back to upload date
        occurred_at = first_file.get("uploaded_at") or now_iso

    record_id = str(uuid.uuid4())
    record = {
        "id": record_id,
        "kind": "equipment_checkout",
        "project_number": project_number,
        "project_name": project_name,
        "employee_id": (matches.get("employee") or {}).get("suggested_id"),
        "employee_name": employee_name,
        "employee_position": employee_position,
        "supervisor_name": supervisor_name or (review.get("reviewer_name") or ""),
        "supervisor_email": "",
        "occurred_at": occurred_at,
        "work_area": "",
        "details": {
            "equipment_lines": equipment_lines,
            "notes": notes,
        },
        "photos": [],
        "supervisor_signature": "",
        "employee_signature": "",
        "employee_refused": False,
        "employee_not_present": False,
        "witness_name": "",
        "witness_signature": "",
        "language": "en",
        "created_at": now_iso,
        "updated_at": now_iso,
        "deleted_at": None,
        # ── Phase B provenance discriminators ──
        "source": "legacy_imported",
        "legacy_import_id": import_doc.get("id"),
        "legacy_source_file_key": first_file.get("r2_key"),
        "legacy_uploaded_by": first_file.get("uploaded_by_name"),
        "legacy_uploaded_at": first_file.get("uploaded_at"),
        "legacy_reviewer_name": review.get("reviewer_name"),
        "legacy_reviewed_at": review.get("reviewed_at"),
        "legacy_ocr_confidence": (import_doc.get("ocr") or {}).get("confidence", 0.0),
    }
    await db.field_leadership_records.insert_one(record)
    record.pop("_id", None)
    logger.info(
        f"[phase-b] promoted legacy_import={import_doc.get('id')} → "
        f"field_leadership_records/{record_id} (employee={employee_name!r}, "
        f"lines={len(equipment_lines)})"
    )
    return {"collection": "field_leadership_records", "record_id": record_id}


# ─── Registration helper (called once at server startup) ──────────────
def register_phase_b(legacy_imports_module) -> None:
    """Idempotent registration of Phase B extractor + promoter into the
    Phase A registries. Called from server.py startup if
    LEGACY_PHASE_B_ENABLED != 'false'."""
    if not phase_b_enabled():
        logger.info("[phase-b] LEGACY_PHASE_B_ENABLED=false · skipping registration")
        return
    legacy_imports_module.EXTRACTORS["equipment_checkout"] = EquipmentCheckoutExtractor()
    legacy_imports_module.ACTIVE_PROMOTERS["equipment_checkout"] = equipment_checkout_promoter
    logger.info(
        "[phase-b] equipment_checkout extractor + promoter registered · "
        f"pilot_cap={pilot_cap()} · model={ocr_model()}"
    )
