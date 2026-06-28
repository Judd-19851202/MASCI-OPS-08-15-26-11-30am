"""TRACK 16.12 · Transportation Operations Intelligence — shared core.

Pure helpers reused across driver / carrier / truck intelligence and
the recommendation + prediction engines. NEVER mutates source records.

Hard rules
----------
* Deterministic. No randomness, no AI guessing.
* Every score carries an `explanations` trail mapping the score to the
  concrete records that produced it.
* Reads only from already-canonical MASCI collections.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, Iterable, List, Optional

TENANT = "masci"
SCHEMA_VERSION = "16.12.0"


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def now_dt() -> datetime:
    return datetime.now(timezone.utc)


def parse_iso(value: Any) -> Optional[datetime]:
    """Best-effort ISO-8601 parse — never raises."""
    if not isinstance(value, str) or len(value) < 10:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except (ValueError, TypeError):
        return None


def days_until(value: Any, now: Optional[datetime] = None) -> Optional[int]:
    dt = parse_iso(value)
    if not dt:
        return None
    base = now or now_dt()
    return int((dt - base).total_seconds() // 86400)


def clamp(n: float, lo: float = 0.0, hi: float = 100.0) -> float:
    return max(lo, min(hi, n))


def grade(score: float) -> str:
    """Operator-facing band — non-punitive vocabulary only."""
    if score >= 90:
        return "excellent"
    if score >= 75:
        return "strong"
    if score >= 60:
        return "fair"
    if score >= 40:
        return "watch"
    return "critical"


def make_explanation(
    *, code: str, label: str, impact: str, weight: float,
    delta: float, record_id: Optional[str] = None,
    record_type: Optional[str] = None,
    fix: Optional[str] = None,
) -> Dict[str, Any]:
    """Single explanation row. Every score change must produce one."""
    return {
        "code": code, "label": label, "impact": impact,
        "weight": round(weight, 2), "delta": round(delta, 2),
        "record_id": record_id, "record_type": record_type,
        "fix": fix,
        "at": now_iso(),
    }


def composite(parts: Iterable[Dict[str, Any]]) -> float:
    """Weighted average of {score, weight} parts. Returns 0–100."""
    total_weight = 0.0
    weighted = 0.0
    for p in parts:
        w = float(p.get("weight") or 0)
        s = float(p.get("score") or 0)
        if w <= 0:
            continue
        total_weight += w
        weighted += w * s
    if total_weight <= 0:
        return 0.0
    return clamp(weighted / total_weight)


def derive_band(score: float) -> Dict[str, Any]:
    return {"score": round(score, 2), "grade": grade(score)}


async def write_intelligence_audit(
    db, *, kind: str, subject_type: str, subject_id: Optional[str],
    snapshot: Dict[str, Any], actor: str = "system",
) -> None:
    """Append a single intelligence audit row. Never raises."""
    try:
        import uuid
        await db.transport_intelligence_audit.insert_one({
            "id": uuid.uuid4().hex,
            "tenant": TENANT,
            "kind": kind,
            "subject_type": subject_type,
            "subject_id": subject_id,
            "snapshot": snapshot,
            "actor": actor,
            "schema_version": SCHEMA_VERSION,
            "ts": now_iso(),
        })
    except Exception:  # noqa: BLE001
        # Audit best-effort — never break callers.
        pass


def projection_strip(doc: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    if not doc:
        return None
    out = {k: v for k, v in doc.items() if k != "_id"}
    return out
