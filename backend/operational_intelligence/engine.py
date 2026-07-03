"""The engine core — compose · render · dispatch · audit · history ·
dedupe · trend. ONE of each."""
from __future__ import annotations

import hashlib
import os
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from .registry import require_product, ProductStatus
from .recipients import list_recipients_for


ENGINE_VERSION = "1.0.0"

# Additive collection names (canonical for the engine).
# Track 19.39 collections continue to work; the engine now writes new
# products to the canonical audit + history collections below and
# leaves 19.39 rows in place (zero drift).
COLLECTION_AUDIT = "operational_intelligence_audit"
COLLECTION_HISTORY = "operational_intelligence_history"
COLLECTION_DEDUPE = "operational_intelligence_dedupe"


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _iso_week(now: Optional[datetime] = None) -> str:
    d = now or datetime.now(timezone.utc)
    y, w, _ = d.isocalendar()
    return f"{y}-W{w:02d}"


# ---------------------------------------------------------------------------
# Dedupe
# ---------------------------------------------------------------------------
def dedupe_key_for(product_id: str, *, period: Optional[str] = None,
                   recipient_hash: str = "") -> str:
    p = period or _iso_week()
    return f"{product_id}:{p}:{recipient_hash}"


async def dedupe_seen(db, key: str) -> bool:
    return bool(await db[COLLECTION_DEDUPE].find_one({"key": key}))


async def dedupe_mark(db, key: str, *, meta: Optional[Dict[str, Any]] = None) -> None:
    await db[COLLECTION_DEDUPE].insert_one({
        "key": key, "created_at": _now_iso(), "meta": meta or {},
    })


# ---------------------------------------------------------------------------
# Trend engine
# ---------------------------------------------------------------------------
def compute_trend(current: float, previous: float) -> Dict[str, Any]:
    """Deterministic trend calculation. Returns arrow · delta · pct · tone."""
    try:
        curr = float(current or 0)
        prev = float(previous or 0)
    except Exception:
        curr, prev = 0.0, 0.0
    delta = curr - prev
    if prev == 0:
        pct = None if curr == 0 else 100.0
    else:
        pct = (delta / prev) * 100.0
    if delta > 0:
        arrow, tone = "▲", "up"
    elif delta < 0:
        arrow, tone = "▼", "down"
    else:
        arrow, tone = "→", "flat"
    return {
        "current": curr, "previous": prev,
        "delta": delta,
        "pct_change": round(pct, 1) if pct is not None else None,
        "arrow": arrow, "tone": tone,
    }


# ---------------------------------------------------------------------------
# Audit + history (append-only)
# ---------------------------------------------------------------------------
async def write_audit(db, *, product_id: str, event: str,
                      actor: str = "system",
                      payload: Optional[Dict[str, Any]] = None) -> str:
    row = {
        "id": str(uuid.uuid4()),
        "product_id": product_id,
        "event": event,
        "actor": actor,
        "at": _now_iso(),
        "payload": payload or {},
    }
    await db[COLLECTION_AUDIT].insert_one(row)
    return row["id"]


async def write_history(db, *, product_id: str, digest_object: Dict[str, Any],
                        rendered_html: str = "",
                        generated_by: str = "system",
                        period: Optional[str] = None) -> str:
    row = {
        "id": str(uuid.uuid4()),
        "product_id": product_id,
        "period": period or _iso_week(),
        "digest_object": digest_object,
        "rendered_html": rendered_html,
        "generated_by": generated_by,
        "generated_at": _now_iso(),
    }
    await db[COLLECTION_HISTORY].insert_one(row)
    return row["id"]


# ---------------------------------------------------------------------------
# Compose · Render · Dispatch
# ---------------------------------------------------------------------------
async def compose(db, *, product_id: str, **kwargs) -> Dict[str, Any]:
    p = require_product(product_id)
    if p.status != ProductStatus.IMPLEMENTED or p.aggregator is None:
        raise NotImplementedError(
            f"Operational Intelligence product {product_id!r} is contract-registered "
            f"but its aggregator is not yet implemented. "
            f"Ship a follow-up track to wire the aggregator."
        )
    digest = await p.aggregator(db, **kwargs)
    # Every digest carries the engine version + product identity.
    digest.setdefault("engine_version", ENGINE_VERSION)
    digest.setdefault("product_id", product_id)
    digest.setdefault("generated_at", _now_iso())
    return digest


def render_html(digest: Dict[str, Any]) -> str:
    """Canonical HTML renderer — one template family, product-specific
    section blocks composed from the digest object."""
    subject = digest.get("subject") or f"Operational Intelligence · {digest.get('product_id','')}"
    generated = digest.get("generated_at") or _now_iso()
    sections_html = _render_sections(digest.get("sections") or [])
    notice = digest.get("no_auto_decision_notice") or (
        "This report is an attention signal only. Owners of each domain "
        "own investigation and classification."
    )
    css = _CSS
    return (
        "<!DOCTYPE html><html><head><meta charset='utf-8'/>"
        f"<title>{_esc(subject)}</title><style>{css}</style></head><body>"
        f"<h1>{_esc(subject)}</h1>"
        f"<div class='meta'>Engine v{_esc(digest.get('engine_version', ENGINE_VERSION))}"
        f" · Generated {_esc(generated)} · Product {_esc(digest.get('product_id',''))}</div>"
        f"{sections_html}"
        f"<div class='notice'>{_esc(notice)}</div>"
        "</body></html>"
    )


def _render_sections(sections: List[Dict[str, Any]]) -> str:
    if not sections:
        return "<p class='muted'>No sections produced.</p>"
    out: List[str] = []
    for sec in sections:
        title = _esc(sec.get("title") or "")
        kind = sec.get("kind") or "kv"
        body = ""
        if kind == "kv":
            body = "".join(
                f"<div class='row'><div class='lbl'>{_esc(k)}</div>"
                f"<div class='val'>{_render_trend_or_value(v)}</div></div>"
                for k, v in (sec.get("rows") or {}).items()
            )
        elif kind == "table":
            headers = sec.get("headers") or []
            rows = sec.get("rows") or []
            th = "".join(f"<th>{_esc(h)}</th>" for h in headers)
            tr = "".join(
                "<tr>" + "".join(f"<td>{_render_cell(c)}</td>" for c in r) + "</tr>"
                for r in rows
            )
            body = f"<table><thead><tr>{th}</tr></thead><tbody>{tr}</tbody></table>"
        elif kind == "list":
            body = "<ul>" + "".join(
                f"<li>{_render_cell(item)}</li>" for item in sec.get("items") or []
            ) + "</ul>"
        out.append(f"<section><h2>{title}</h2>{body}</section>")
    return "".join(out)


def _render_trend_or_value(v: Any) -> str:
    if isinstance(v, dict) and "arrow" in v and "current" in v:
        tone_class = f"trend-{v.get('tone','flat')}"
        pct = v.get("pct_change")
        pct_str = f" · {pct:+.1f}%" if pct is not None else ""
        return (f"<span class='{tone_class}'>{_esc(v['current'])} "
                f"{_esc(v['arrow'])}{_esc(pct_str)}</span>")
    if isinstance(v, dict) and "href" in v and "text" in v:
        return f"<a href='{_esc(v['href'])}'>{_esc(v['text'])}</a>"
    return _esc(v)


def _render_cell(v: Any) -> str:
    return _render_trend_or_value(v)


def _esc(v: Any) -> str:
    import html as _h
    return _h.escape("" if v is None else str(v))


_CSS = (
    "body{font-family:Helvetica,Arial,sans-serif;color:#0f172a;font-size:14px;"
    "line-height:1.5;max-width:820px;margin:0 auto;padding:24px}"
    "h1{font-size:22px;margin:0 0 4px}"
    ".meta{color:#64748b;font-size:11px;text-transform:uppercase;letter-spacing:0.14em;margin-bottom:12px}"
    "section{margin:16px 0;border-top:1px solid #e2e8f0;padding-top:8px}"
    "h2{font-size:15px;margin:0 0 8px;letter-spacing:0.02em}"
    ".row{display:flex;padding:2px 0;border-bottom:1px solid #f1f5f9}"
    ".lbl{flex:0 0 30%;color:#64748b;font-size:11px;text-transform:uppercase;letter-spacing:0.08em}"
    ".val{flex:1 1 70%}"
    ".trend-up{color:#166534}.trend-down{color:#991b1b}.trend-flat{color:#475569}"
    "table{width:100%;border-collapse:collapse}"
    "th,td{border:1px solid #cbd5e1;padding:5px 8px;font-size:12px;text-align:left;vertical-align:top}"
    "th{background:#f1f5f9;text-transform:uppercase;letter-spacing:0.08em;font-size:10px}"
    ".notice{margin-top:20px;padding:10px 14px;border-left:3px solid #cbd5e1;"
    "background:#f8fafc;color:#334155;font-style:italic;font-size:12px}"
    ".muted{color:#94a3b8;font-style:italic}"
)


async def dispatch(
    db, *, product_id: str, dry_run: bool = True,
    generated_by: str = "system",
    period: Optional[str] = None,
    dedupe: bool = True,
    aggregator_kwargs: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Compose + optionally send. Writes audit + history rows. Applies
    the shared dedupe guard when ``dedupe=True``.

    Live-send path uses ``lib.fsi_email_sender.fsi_send_email``.
    """
    kwargs = aggregator_kwargs or {}
    digest = await compose(db, product_id=product_id, **kwargs)
    html = render_html(digest)
    active = await list_recipients_for(db, product_id=product_id, active_only=True)
    recipient_emails = [r["email"] for r in active]
    recipient_hash = hashlib.sha1(
        ",".join(sorted(recipient_emails)).encode()
    ).hexdigest()[:12]
    dk = dedupe_key_for(product_id, period=period, recipient_hash=recipient_hash)

    if not dry_run and dedupe and await dedupe_seen(db, dk):
        await write_audit(db, product_id=product_id, event="dispatch_skipped_dedupe",
                          actor=generated_by, payload={"dedupe_key": dk})
        return {"dry_run": False, "send_status": "skipped_dedupe",
                "dedupe_key": dk, "recipient_count": len(active),
                "generated_at": digest["generated_at"]}

    send_status = "dry_run" if dry_run else "pending"
    delivery: List[Dict[str, Any]] = []
    if not dry_run:
        from lib.fsi_email_sender import fsi_send_email  # noqa: PLC0415
        subject = digest.get("subject") or f"Operational Intelligence · {product_id}"
        for r in active:
            try:
                resp = await fsi_send_email(r["email"], subject, html, db=db)
                delivery.append({"email": r["email"], "ok": True,
                                 "provider_id": (resp or {}).get("id") or ""})
            except Exception as e:  # noqa: BLE001
                delivery.append({"email": r["email"], "ok": False, "error": str(e)})
        send_status = "sent" if all(d.get("ok") for d in delivery) else "partial"
        if dedupe and send_status in ("sent", "partial"):
            await dedupe_mark(db, dk, meta={"send_status": send_status})

    history_id = await write_history(db, product_id=product_id,
                                     digest_object=digest,
                                     rendered_html=html,
                                     generated_by=generated_by,
                                     period=period)
    audit_id = await write_audit(db, product_id=product_id, event="dispatch",
                                 actor=generated_by,
                                 payload={"dry_run": bool(dry_run),
                                          "send_status": send_status,
                                          "recipient_count": len(active),
                                          "dedupe_key": dk,
                                          "delivery": delivery,
                                          "history_id": history_id})
    return {
        "dry_run": bool(dry_run),
        "send_status": send_status,
        "recipient_count": len(active),
        "recipients": recipient_emails,
        "subject": digest.get("subject", ""),
        "generated_at": digest["generated_at"],
        "dedupe_key": dk,
        "audit_id": audit_id,
        "history_id": history_id,
        "delivery": delivery,
    }


__all__ = [
    "ENGINE_VERSION", "COLLECTION_AUDIT", "COLLECTION_HISTORY", "COLLECTION_DEDUPE",
    "compose", "render_html", "dispatch",
    "dedupe_key_for", "dedupe_seen", "dedupe_mark",
    "compute_trend", "write_audit", "write_history",
]
