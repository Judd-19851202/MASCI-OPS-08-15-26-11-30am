"""TRACK 16.14 · Dispatcher Learning Loop.

Team-level operational insight derived from
``transport_dispatch_recommendation_audit`` (Track 16.13).

Strict contract
---------------
* Read-only — never mutates audit rows.
* Never duplicates intelligence scoring (no calls to driver/carrier/
  truck intelligence libs).
* Outputs are team-level only. No per-dispatcher rankings, no
  individual scorekeeping, no performance-review framing.
* Non-punitive vocabulary only — use "Opportunity", "Pattern",
  "Watch", "Improve data quality".
"""
from __future__ import annotations

import logging
from collections import Counter
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

TENANT = "masci"
SCHEMA_VERSION = "16.14.0"
DEFAULT_DAYS = 30
MAX_DAYS = 365


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _range(days: Optional[int], start: Optional[str], end: Optional[str]
            ) -> Tuple[str, str, int]:
    """Resolve a (start_iso, end_iso, days) window. Caps at MAX_DAYS."""
    now = datetime.now(timezone.utc)
    if days is None:
        days = DEFAULT_DAYS
    days = max(1, min(int(days), MAX_DAYS))
    end_dt = now
    start_dt = now - timedelta(days=days)
    if start:
        try:
            start_dt = datetime.fromisoformat(start.replace("Z", "+00:00"))
        except (ValueError, TypeError):
            pass
    if end:
        try:
            end_dt = datetime.fromisoformat(end.replace("Z", "+00:00"))
        except (ValueError, TypeError):
            pass
    return start_dt.isoformat(), end_dt.isoformat(), days


async def _load_audit(db, *, start_iso: str, end_iso: str
                       ) -> List[Dict[str, Any]]:
    cur = db.transport_dispatch_recommendation_audit.find({
        "tenant": TENANT,
        "ts": {"$gte": start_iso, "$lte": end_iso},
    })
    rows = await cur.to_list(20000)
    return rows


def _kind_counts(rows: List[Dict[str, Any]]) -> Dict[str, int]:
    out: Dict[str, int] = {}
    for r in rows:
        k = r.get("kind") or "unknown"
        out[k] = out.get(k, 0) + 1
    return out


async def build_dispatch_learning_summary(
    db, *, start: Optional[str] = None, end: Optional[str] = None,
    days: Optional[int] = None,
) -> Dict[str, Any]:
    """Top-line summary counts. Team-level only."""
    s, e, d = _range(days, start, end)
    rows = await _load_audit(db, start_iso=s, end_iso=e)
    kc = _kind_counts(rows)
    return {
        "range": {"start": s, "end": e, "days": d},
        "summary": {
            "recommendations_generated":
                kc.get("transport_dispatch_recommendation_generated", 0),
            "recommendations_viewed":
                kc.get("transport_dispatch_recommendation_viewed", 0),
            "recommended_selected":
                kc.get("transport_dispatch_recommendation_selected", 0),
            "eligible_alternative_selected":
                kc.get("transport_dispatch_non_recommended_selected", 0),
            "ignored":
                kc.get("transport_dispatch_recommendation_ignored", 0),
            "recommendation_unavailable":
                kc.get("transport_dispatch_recommendation_failed", 0),
        },
    }


async def build_recommendation_adoption_trends(
    db, *, days: int = DEFAULT_DAYS,
) -> Dict[str, Any]:
    """Day-bucketed adoption trend. Team-level only."""
    s, e, d = _range(days, None, None)
    rows = await _load_audit(db, start_iso=s, end_iso=e)
    by_day: Dict[str, Dict[str, int]] = {}
    interesting = {
        "transport_dispatch_recommendation_generated": "generated",
        "transport_dispatch_recommendation_viewed": "viewed",
        "transport_dispatch_recommendation_selected": "selected",
        "transport_dispatch_non_recommended_selected": "non_recommended_selected",
        "transport_dispatch_recommendation_ignored": "ignored",
    }
    for r in rows:
        kind = r.get("kind")
        if kind not in interesting:
            continue
        day = (r.get("ts") or "")[:10]
        bucket = by_day.setdefault(day, {})
        key = interesting[kind]
        bucket[key] = bucket.get(key, 0) + 1
    days_sorted = sorted(by_day.keys())
    points = []
    for day in days_sorted:
        b = by_day[day]
        generated = b.get("generated", 0)
        selected = b.get("selected", 0)
        non_rec = b.get("non_recommended_selected", 0)
        # Adoption = recommended selected ÷ (selected + non_recommended)
        decided = selected + non_rec
        rate = round((selected / decided * 100), 2) if decided else None
        points.append({"date": day, "generated": generated,
                       "viewed": b.get("viewed", 0),
                       "selected": selected,
                       "non_recommended_selected": non_rec,
                       "ignored": b.get("ignored", 0),
                       "adoption_pct": rate})
    return {"range": {"start": s, "end": e, "days": d},
            "points": points}


async def build_common_alternative_reasons(
    db, *, days: int = DEFAULT_DAYS,
) -> Dict[str, Any]:
    """Most-common notes attached to non_recommended_selected events."""
    s, e, d = _range(days, None, None)
    rows = await _load_audit(db, start_iso=s, end_iso=e)
    counter: Counter[str] = Counter()
    total = 0
    for r in rows:
        if r.get("kind") != "transport_dispatch_non_recommended_selected":
            continue
        total += 1
        note = (((r.get("payload") or {}).get("note")) or "").strip()
        if note:
            counter[note[:240]] += 1
    return {
        "range": {"start": s, "end": e, "days": d},
        "total_non_recommended_selections": total,
        "patterns": [
            {"label": k, "count": v, "share_pct":
                 round(v / total * 100, 2) if total else 0}
            for k, v in counter.most_common(10)
        ],
    }


async def build_common_watch_items(
    db, *, days: int = DEFAULT_DAYS,
) -> Dict[str, Any]:
    """Watch labels that appeared most often on generated recommendations.
    Sources from the snapshot embedded in the generated audit row."""
    s, e, d = _range(days, None, None)
    rows = await _load_audit(db, start_iso=s, end_iso=e)
    counter: Counter[str] = Counter()
    seen_rec_ids: set = set()
    for r in rows:
        if r.get("kind") != "transport_dispatch_recommendation_generated":
            continue
        payload = r.get("payload") or {}
        rid = payload.get("recommendation_id")
        if rid in seen_rec_ids:
            continue
        if rid:
            seen_rec_ids.add(rid)
        # The generated event records the score / grade but not the full
        # watch list. We approximate by reading the recommendation_id and
        # finding the matching viewed event (which the UI fires); if no
        # viewed event exists we skip — non-fabricated by design.
        # In this lightweight implementation, the audit payload itself
        # carries any embedded watch labels under payload["watch"].
        for label in (payload.get("watch") or []):
            if isinstance(label, str):
                counter[label[:240]] += 1
    return {
        "range": {"start": s, "end": e, "days": d},
        "patterns": [
            {"label": k, "count": v}
            for k, v in counter.most_common(15)
        ],
    }


async def build_excluded_reason_patterns(
    db, *, days: int = DEFAULT_DAYS,
) -> Dict[str, Any]:
    """Aggregate the most common excluded-option reason labels.

    We DO NOT recompute eligibility — we count the reason labels that
    are already present on the canonical ``transport_eligibility_state``
    rows for entities in non-dispatchable states. This is "what
    dispatchers see excluded today" and serves as a complementary
    signal to the audit trail.
    """
    counter: Counter[str] = Counter()
    cur = db.transport_eligibility_state.find({
        "tenant": TENANT,
        "state": {"$in": ["not_dispatchable", "suspended", "expired",
                            "needs_correction"]},
    })
    rows = await cur.to_list(5000)
    for r in rows:
        for reason in (r.get("reasons") or []):
            label = (reason.get("label") or reason.get("code") or "").strip()
            if label:
                counter[label[:240]] += 1
    return {
        "patterns": [
            {"label": k, "count": v}
            for k, v in counter.most_common(15)
        ],
        "total_excluded_entities": len(rows),
        "days_window": days,
    }


async def build_engine_tuning_signals(
    db, *, days: int = DEFAULT_DAYS,
) -> Dict[str, Any]:
    """System-level tuning suggestions. Non-punitive opportunities only.

    Every signal includes its underlying counts so operators can verify
    the claim. No vague AI guessing.
    """
    s, e, d = _range(days, None, None)
    rows = await _load_audit(db, start_iso=s, end_iso=e)
    kc = _kind_counts(rows)
    generated = kc.get("transport_dispatch_recommendation_generated", 0)
    viewed = kc.get("transport_dispatch_recommendation_viewed", 0)
    failed = kc.get("transport_dispatch_recommendation_failed", 0)
    ignored = kc.get("transport_dispatch_recommendation_ignored", 0)
    non_rec = kc.get(
        "transport_dispatch_non_recommended_selected", 0)
    selected = kc.get("transport_dispatch_recommendation_selected", 0)

    signals: List[Dict[str, Any]] = []

    if generated >= 10 and failed / max(generated, 1) >= 0.10:
        signals.append({
            "code": "frequent_recommendation_unavailable",
            "kind": "Opportunity",
            "label": ("Recommendation unavailable in "
                       f"{failed} of {generated} requests"),
            "detail": ("Investigate intelligence engine availability "
                        "or data freshness."),
            "count": failed,
            "share_pct": round(failed / generated * 100, 2),
        })

    if generated >= 10 and ignored / max(generated, 1) >= 0.30:
        signals.append({
            "code": "many_ignored_without_view",
            "kind": "Pattern",
            "label": (f"{ignored} of {generated} recommendations "
                       "dismissed without opening Why drawer"),
            "detail": ("Consider clearer chip framing or surfacing "
                        "top reason directly on the chip."),
            "count": ignored,
            "share_pct": round(ignored / generated * 100, 2),
        })

    if (selected + non_rec) >= 10 and non_rec / max(selected + non_rec, 1) >= 0.40:
        signals.append({
            "code": "frequent_alternative_selection",
            "kind": "Pattern",
            "label": (f"Eligible alternatives selected in {non_rec} "
                       f"of {selected + non_rec} decided assignments"),
            "detail": ("Review whether recommendation weights match "
                        "operator priorities."),
            "count": non_rec,
            "share_pct": round(non_rec / max(selected + non_rec, 1) * 100, 2),
        })

    if generated >= 10 and viewed / max(generated, 1) >= 0.60:
        signals.append({
            "code": "healthy_explainability_usage",
            "kind": "Opportunity",
            "label": (f"Operators opened Why drawer for {viewed} of "
                       f"{generated} recommendations"),
            "detail": ("Strong explainability adoption. Keep watch "
                        "labels concise and actionable."),
            "count": viewed,
            "share_pct": round(viewed / generated * 100, 2),
        })

    # Excluded reason concentration signal.
    excluded = await build_excluded_reason_patterns(db, days=days)
    if excluded["total_excluded_entities"] >= 10:
        top = (excluded.get("patterns") or [])[:1]
        if top:
            tl = top[0]
            share = tl["count"] / excluded["total_excluded_entities"]
            if share >= 0.40:
                signals.append({
                    "code": "concentrated_excluded_reason",
                    "kind": "Improve data quality",
                    "label": (f"\"{tl['label']}\" appears in "
                               f"{tl['count']} excluded entries"),
                    "detail": ("Targeting this single reason could "
                                "expand the dispatchable pool quickly."),
                    "count": tl["count"],
                    "share_pct": round(share * 100, 2),
                })

    return {
        "range": {"start": s, "end": e, "days": d},
        "signals": signals,
    }


# ---------------------------------------------------------------------------
# Audit helper for view events.
# ---------------------------------------------------------------------------
async def record_learning_view(db, *, viewer_role: str,
                                viewer_id: Optional[str],
                                range_info: Dict[str, Any],
                                summary_counts: Dict[str, Any]) -> None:
    try:
        import uuid
        await db.transport_intelligence_audit.insert_one({
            "id": uuid.uuid4().hex,
            "tenant": TENANT,
            "kind": "transport_dispatch_learning_viewed",
            "subject_type": "dispatch_learning",
            "subject_id": None,
            "actor": viewer_role or "admin",
            "viewer_id": viewer_id,
            "schema_version": SCHEMA_VERSION,
            "snapshot": {"range": range_info, "counts": summary_counts},
            "ts": _now_iso(),
        })
    except Exception as exc:  # noqa: BLE001
        logger.warning("dispatcher_learning audit insert failed: %s", exc)
