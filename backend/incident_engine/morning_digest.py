"""Track 19.39 · Morning Safety Intelligence Digest.

Read-only, opt-in, permission-safe weekly digest.

- Composes the digest from Track 19.38 portfolio aggregator (which
  reuses the Track 19.37 scorer). No duplicate scoring logic.
- Sends via the existing ``fsi_send_email`` helper — no new email
  provider.
- Dry-run mode short-circuits before send and writes an audit row.
- Recipients are stored in the additive Mongo collection
  ``morning_digest_recipients`` and can be added / updated via
  admin-gated routes. Inactive recipients are excluded from send.
- Never mutates any incident, case, evidence, CAPA, task, medical,
  agency, or communication collection.
- Never decides OSHA recordability, root cause, liability, fault,
  discipline, or insurance responsibility.

Callable from an eventual scheduler (Phase 2 · out of scope for
Track 19.39). Endpoints registered from ``server.py``.
"""
from __future__ import annotations

import os
import uuid
import html as _html
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from .portfolio_intelligence import _list_cases_readonly, _rows_for_cases


MORNING_DIGEST_MODEL_VERSION = "1.0.0"
DIGEST_TYPE_DEFAULT = "safety_morning_digest"
SUBJECT_DEFAULT = "MASCI Morning Safety Intelligence — Weekly Attention Brief"

COLLECTION_RECIPIENTS = "morning_digest_recipients"
COLLECTION_AUDIT = "morning_digest_audit"

NO_AUTO_DECISION_NOTICE = (
    "This digest is an attention signal only. Safety owns investigation "
    "and classification. The platform does not decide OSHA recordability, "
    "root cause, liability, fault, discipline, or insurance responsibility."
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _default_recipients_from_env() -> List[Dict[str, Any]]:
    """Configurable via MORNING_DIGEST_DEFAULT_RECIPIENTS
    (comma-separated list of ``email|display_name|role_label``). If unset,
    seeds Jaymn + a Safety placeholder — admins can replace the Safety
    placeholder via the recipient endpoints without any code change."""
    raw = os.environ.get("MORNING_DIGEST_DEFAULT_RECIPIENTS") or ""
    entries: List[Dict[str, Any]] = []
    if raw.strip():
        for part in raw.split(","):
            fields = [p.strip() for p in part.split("|")]
            email = fields[0] if fields else ""
            if not email:
                continue
            entries.append({
                "email": email,
                "display_name": fields[1] if len(fields) > 1 else "",
                "role_label": fields[2] if len(fields) > 2 else "",
            })
    if not entries:
        entries = [
            {"email": "jaymn.judd@mascigc.com",
             "display_name": "Jaymn Judd",
             "role_label": "Super Admin"},
            {"email": "safety@mascigc.com",
             "display_name": "Safety Inbox (placeholder)",
             "role_label": "Safety Manager"},
        ]
    return entries


async def ensure_default_recipients_seeded(db) -> int:
    """Seed default recipients on first read. Idempotent · returns
    number of rows inserted (0 if the collection already has any row)."""
    count = await db[COLLECTION_RECIPIENTS].count_documents({})
    if count > 0:
        return 0
    now = _now_iso()
    docs = []
    for e in _default_recipients_from_env():
        docs.append({
            "id": str(uuid.uuid4()),
            "email": e["email"],
            "display_name": e.get("display_name") or "",
            "role_label": e.get("role_label") or "",
            "active": True,
            "digest_type": DIGEST_TYPE_DEFAULT,
            "created_at": now,
            "updated_at": now,
            "added_by": "system:seed",
            "notes": ("Default recipient seeded by Track 19.39. Admin should "
                      "replace Safety placeholder with the real Safety alias."),
        })
    if docs:
        await db[COLLECTION_RECIPIENTS].insert_many(docs)
    return len(docs)


async def list_recipients(
    db, *, digest_type: str = DIGEST_TYPE_DEFAULT,
    active_only: bool = False,
) -> List[Dict[str, Any]]:
    await ensure_default_recipients_seeded(db)
    q: Dict[str, Any] = {"digest_type": digest_type}
    if active_only:
        q["active"] = True
    cur = db[COLLECTION_RECIPIENTS].find(q, {"_id": 0}).sort("created_at", 1)
    return [d async for d in cur]


async def add_recipient(
    db, *,
    email: str, display_name: str = "", role_label: str = "",
    added_by: str = "admin", notes: str = "",
    digest_type: str = DIGEST_TYPE_DEFAULT,
) -> Dict[str, Any]:
    email = (email or "").strip().lower()
    if "@" not in email:
        raise ValueError(f"invalid email: {email!r}")
    now = _now_iso()
    doc = {
        "id": str(uuid.uuid4()),
        "email": email,
        "display_name": display_name or "",
        "role_label": role_label or "",
        "active": True,
        "digest_type": digest_type,
        "created_at": now,
        "updated_at": now,
        "added_by": added_by,
        "notes": notes or "",
    }
    await db[COLLECTION_RECIPIENTS].insert_one(doc)
    return doc


async def update_recipient(
    db, *, recipient_id: str, patch: Dict[str, Any],
) -> Optional[Dict[str, Any]]:
    now = _now_iso()
    allowed = {"display_name", "role_label", "active", "notes"}
    apply_ = {k: v for k, v in (patch or {}).items() if k in allowed}
    if not apply_:
        return await db[COLLECTION_RECIPIENTS].find_one({"id": recipient_id}, {"_id": 0})
    apply_["updated_at"] = now
    await db[COLLECTION_RECIPIENTS].update_one(
        {"id": recipient_id}, {"$set": apply_},
    )
    return await db[COLLECTION_RECIPIENTS].find_one({"id": recipient_id}, {"_id": 0})


# ---------------------------------------------------------------------------
# Digest composition (pure-ish · reads only via the aggregator)
# ---------------------------------------------------------------------------
async def compose_digest(
    db, *, digest_window_days: int = 7, top_n: int = 5, limit: int = 200,
) -> Dict[str, Any]:
    """Assemble the digest payload. Reuses the Track 19.38 aggregator.

    Returns a JSON-serialisable dict with sections that a caller can
    render as HTML (see :func:`render_html`) or emit as JSON for a
    preview surface.
    """
    cases = await _list_cases_readonly(db, limit=limit)
    rows = await _rows_for_cases(db, cases, want_attention=True)
    rows.sort(key=lambda r: (
        -(r.get("attention_score") or 0),
        -(r.get("days_open") or 0),
    ))

    now = datetime.now(timezone.utc)
    window_seconds = digest_window_days * 86400
    open_states = {"CLOSED"}

    def _submitted_within_window(r: Dict[str, Any]) -> bool:
        s = r.get("submitted_at") or ""
        try:
            d = datetime.fromisoformat(s.replace("Z", "+00:00"))
        except Exception:
            return False
        return (now - d).total_seconds() <= window_seconds

    total_open = sum(1 for r in rows if (r.get("state") or "").upper() not in open_states)
    high_attention = sum(1 for r in rows if r.get("attention_level") == "high")
    opened_recent = sum(1 for r in rows if _submitted_within_window(r))
    closed_recent = 0
    for c in cases:
        closed_at = c.get("closed_at") or ""
        if not closed_at:
            continue
        try:
            d = datetime.fromisoformat(closed_at.replace("Z", "+00:00"))
        except Exception:
            continue
        if (now - d).total_seconds() <= window_seconds:
            closed_recent += 1

    overdue_capa_total = sum(
        1 for r in rows
        for s in (r.get("_attention_full") or {}).get("signals", [])
        if s.get("signal_key") == "possible_overdue_capa" and (s.get("score") or 0) > 0
    )

    # Average readiness — coarse mapping band → percent.
    band_pct = {"low": 25, "medium": 60, "high": 90}
    ready_vals = [band_pct.get(r.get("readiness_band"), 25) for r in rows]
    avg_readiness = round(sum(ready_vals) / len(ready_vals)) if ready_vals else 0

    oldest = max(rows, key=lambda r: r.get("days_open") or 0, default=None)

    # Top attention cases (with rationale of top signal each).
    top_cases: List[Dict[str, Any]] = []
    for r in rows[:top_n]:
        signals = ((r.get("_attention_full") or {}).get("signals") or [])
        firing = [s for s in signals if (s.get("score") or 0) > 0]
        top_signal = max(firing, key=lambda s: s.get("score") or 0, default=None)
        top_cases.append({
            "case_id":         r["case_id"],
            "case_number":     r["case_number"],
            "job_number":      r["job_number"],
            "incident_type":   r["incident_type"],
            "attention_level": r["attention_level"],
            "attention_score": r["attention_score"],
            "days_open":       r["days_open"],
            "readiness_band":  r["readiness_band"],
            "capa_open":       r["capa_open"],
            "top_signal_key":  (top_signal or {}).get("signal_key") or "",
            "top_signal_rationale": (top_signal or {}).get("rationale") or "",
        })

    # Needs Attention Today buckets — count of rows firing each signal.
    def _count(key: str) -> int:
        n = 0
        for r in rows:
            for s in (r.get("_attention_full") or {}).get("signals", []):
                if s.get("signal_key") == key and (s.get("score") or 0) > 0:
                    n += 1
                    break
        return n

    needs_today = {
        "evidence_gaps":            _count("possible_open_evidence_gap"),
        "overdue_capas":             _count("possible_overdue_capa"),
        "delayed_closeout":          _count("possible_delayed_closeout"),
        "executive_review_needed":   _count("possible_executive_review_needed"),
    }

    # Portfolio trends — count of open cases per incident_type.
    trend_types = [
        "utility_strike", "employee_injury", "vehicle_accident",
        "equipment_accident", "property_damage", "near_miss",
        "near_miss_injury", "environmental", "spill", "release",
        "workplace_violence",
    ]
    trends = {t: 0 for t in trend_types}
    for r in rows:
        it = (r.get("incident_type") or "").lower()
        if it in trends:
            trends[it] += 1

    return {
        "model_version": MORNING_DIGEST_MODEL_VERSION,
        "generated_at": _now_iso(),
        "digest_window_days": digest_window_days,
        "subject": SUBJECT_DEFAULT,
        "executive_summary": {
            "total_open_cases":    total_open,
            "high_attention_cases": high_attention,
            "cases_opened_recent": opened_recent,
            "cases_closed_recent": closed_recent,
            "overdue_capas":       overdue_capa_total,
            "average_readiness_pct": avg_readiness,
            "oldest_open": {
                "case_id":     (oldest or {}).get("case_id") or "",
                "case_number": (oldest or {}).get("case_number") or "",
                "days_open":   (oldest or {}).get("days_open") or 0,
            } if oldest else None,
        },
        "top_attention_cases": top_cases,
        "needs_attention_today": needs_today,
        "portfolio_trends": trends,
        "no_auto_decision_notice": NO_AUTO_DECISION_NOTICE,
    }


def _base_url() -> str:
    return (os.environ.get("PUBLIC_APP_URL")
            or os.environ.get("REACT_APP_BACKEND_URL")
            or "").rstrip("/")


def _esc(v: Any) -> str:
    return _html.escape("" if v is None else str(v))


def render_html(digest: Dict[str, Any]) -> str:
    """Boardroom-clean HTML for the email body."""
    base = _base_url()
    es = digest["executive_summary"]
    top = digest["top_attention_cases"]
    needs = digest["needs_attention_today"]
    trends = digest["portfolio_trends"]

    def _link(cid: str, label: str) -> str:
        if not base or not cid:
            return _esc(label)
        return (f'<a href="{_esc(base)}/safety/cases/{_esc(cid)}/executive-report" '
                f'style="color:#0f172a;text-decoration:underline">{_esc(label)}</a>')

    top_rows = ""
    for r in top:
        top_rows += (
            "<tr>"
            f"<td>#{_link(r['case_id'], r['case_number'] or r['case_id'][:8])}</td>"
            f"<td>{_esc(r.get('job_number'))}</td>"
            f"<td>{_esc(r.get('incident_type'))}</td>"
            f"<td>{_esc((r.get('attention_level') or 'low').upper())} · {_esc(r.get('attention_score'))}</td>"
            f"<td>{_esc(r.get('days_open'))}</td>"
            f"<td>{_esc(r.get('readiness_band'))}</td>"
            f"<td>{_esc(r.get('capa_open'))}</td>"
            f"<td>{_esc(r.get('top_signal_key'))} — {_esc(r.get('top_signal_rationale'))}</td>"
            "</tr>"
        )
    if not top_rows:
        top_rows = '<tr><td colspan="8" style="color:#64748b;font-style:italic">No open cases.</td></tr>'

    trend_rows = "".join(
        f"<li>{_esc(k.replace('_', ' '))} — <strong>{_esc(v)}</strong></li>"
        for k, v in trends.items() if v > 0
    ) or '<li style="color:#64748b;font-style:italic">No open cases in tracked categories.</li>'

    oldest = es.get("oldest_open") or {}
    oldest_line = (
        f"Oldest open: #{_link(oldest.get('case_id',''), oldest.get('case_number') or 'n/a')} "
        f"— {_esc(oldest.get('days_open'))} day(s) open."
        if oldest.get("case_id") else "Oldest open: n/a."
    )

    css = (
        "body{font-family:Helvetica,Arial,sans-serif;color:#0f172a;font-size:14px;"
        "line-height:1.5;max-width:820px;margin:0 auto;padding:24px}"
        "h1{font-size:22px;margin:0 0 4px}"
        "h2{font-size:15px;margin:24px 0 8px;letter-spacing:0.02em;"
        "border-bottom:1px solid #cbd5e1;padding-bottom:4px}"
        "table{width:100%;border-collapse:collapse;font-size:12px}"
        "th,td{border:1px solid #cbd5e1;padding:6px 8px;text-align:left;vertical-align:top}"
        "th{background:#f1f5f9;text-transform:uppercase;letter-spacing:0.08em;font-size:10px}"
        ".stat{display:inline-block;margin:4px 12px 4px 0}"
        ".stat b{font-size:18px;display:block}"
        ".stat span{font-size:10px;text-transform:uppercase;letter-spacing:0.12em;color:#64748b}"
        ".notice{margin-top:24px;padding:10px 14px;border-left:3px solid #cbd5e1;"
        "background:#f8fafc;color:#334155;font-style:italic;font-size:12px}"
    )
    return (
        f'<!DOCTYPE html><html><head><meta charset="utf-8"/>'
        f'<title>{_esc(digest["subject"])}</title>'
        f'<style>{css}</style></head><body>'
        f'<h1>{_esc(digest["subject"])}</h1>'
        f'<div style="color:#64748b;font-size:11px;text-transform:uppercase;letter-spacing:0.14em">'
        f'Generated {_esc(digest["generated_at"])} · Window: last {_esc(digest["digest_window_days"])} days</div>'
        # Executive Summary
        f'<h2>Executive Summary</h2>'
        f'<div class="stat"><b>{es["total_open_cases"]}</b><span>Open cases</span></div>'
        f'<div class="stat"><b>{es["high_attention_cases"]}</b><span>High attention</span></div>'
        f'<div class="stat"><b>{es["cases_opened_recent"]}</b><span>Opened (7d)</span></div>'
        f'<div class="stat"><b>{es["cases_closed_recent"]}</b><span>Closed (7d)</span></div>'
        f'<div class="stat"><b>{es["overdue_capas"]}</b><span>Overdue CAPA</span></div>'
        f'<div class="stat"><b>{es["average_readiness_pct"]}%</b><span>Avg readiness</span></div>'
        f'<p style="margin-top:6px">{oldest_line}</p>'
        # Top Attention Cases
        f'<h2>Top Attention Cases</h2>'
        f'<table><thead><tr>'
        f'<th>Case</th><th>Project</th><th>Type</th><th>Attention</th>'
        f'<th>Days</th><th>Ready</th><th>CAPA open</th><th>Top signal · rationale</th>'
        f'</tr></thead><tbody>{top_rows}</tbody></table>'
        # Needs Attention Today
        f'<h2>Needs Attention Today</h2>'
        f'<ul>'
        f'<li>Evidence gaps: <strong>{needs["evidence_gaps"]}</strong></li>'
        f'<li>Overdue CAPAs: <strong>{needs["overdue_capas"]}</strong></li>'
        f'<li>Delayed closeout: <strong>{needs["delayed_closeout"]}</strong></li>'
        f'<li>Executive review needed: <strong>{needs["executive_review_needed"]}</strong></li>'
        f'</ul>'
        # Portfolio Trends
        f'<h2>Portfolio Trends</h2>'
        f'<ul>{trend_rows}</ul>'
        # No-auto-decision notice
        f'<div class="notice">{_esc(digest["no_auto_decision_notice"])}</div>'
        f'</body></html>'
    )


# ---------------------------------------------------------------------------
# Send + audit
# ---------------------------------------------------------------------------
async def send_digest(
    db, *, dry_run: bool = True, digest_window_days: int = 7,
    top_n: int = 5, generated_by: str = "admin",
) -> Dict[str, Any]:
    """Compose + (optionally) send. Always writes an audit row.

    ``dry_run=True`` (default) never invokes ``fsi_send_email`` — proven
    by the audit row's ``send_status`` and the lock test's mock.
    """
    digest = await compose_digest(db, digest_window_days=digest_window_days,
                                  top_n=top_n)
    active = [r for r in await list_recipients(db, active_only=True)]
    html = render_html(digest)

    audit_id = str(uuid.uuid4())
    send_status = "dry_run" if dry_run else "pending"
    delivery: List[Dict[str, Any]] = []
    if not dry_run:
        # Live send — import lazily so tests can mock without importing.
        from lib.fsi_email_sender import fsi_send_email  # noqa: PLC0415
        for r in active:
            try:
                resp = await fsi_send_email(
                    r["email"], digest["subject"], html, db=db,
                )
                delivery.append({
                    "email": r["email"], "ok": True,
                    "provider_id": (resp or {}).get("id") or "",
                })
            except Exception as e:  # noqa: BLE001
                delivery.append({
                    "email": r["email"], "ok": False, "error": str(e),
                })
        send_status = "sent" if all(d.get("ok") for d in delivery) else "partial"

    audit_row = {
        "id": audit_id,
        "dry_run": bool(dry_run),
        "generated_at": digest["generated_at"],
        "generated_by": generated_by,
        "digest_window_days": digest_window_days,
        "subject": digest["subject"],
        "top_case_count": len(digest["top_attention_cases"]),
        "recipient_count": len(active),
        "recipients": [{"email": r["email"], "role_label": r.get("role_label", "")} for r in active],
        "send_status": send_status,
        "delivery": delivery,
    }
    await db[COLLECTION_AUDIT].insert_one(dict(audit_row))

    return {
        "dry_run": bool(dry_run),
        "recipient_count": len(active),
        "recipients": [r["email"] for r in active],
        "subject": digest["subject"],
        "top_case_count": len(digest["top_attention_cases"]),
        "generated_at": digest["generated_at"],
        "digest_window": f"last {digest_window_days} days",
        "send_status": send_status,
        "audit_id": audit_id,
        "delivery": delivery,
    }


__all__ = [
    "MORNING_DIGEST_MODEL_VERSION",
    "DIGEST_TYPE_DEFAULT",
    "SUBJECT_DEFAULT",
    "COLLECTION_RECIPIENTS",
    "COLLECTION_AUDIT",
    "NO_AUTO_DECISION_NOTICE",
    "ensure_default_recipients_seeded",
    "list_recipients",
    "add_recipient",
    "update_recipient",
    "compose_digest",
    "render_html",
    "send_digest",
]
