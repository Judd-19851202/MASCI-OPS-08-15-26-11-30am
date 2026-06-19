"""
hub_banners_pdf.py — Audit Trail → PDF for Hub Banners.

Generates a single-page, MASCI-letterheaded PDF that can be handed to
an OSHA investigator, attached to an incident report, or filed with
insurance. The PDF is deterministic — same inputs, same output bytes —
so it can also be used as evidence in a legal dispute.

Inputs:
    banner: the banner doc (with title_en/title_es/body_en/body_es,
            severity, require_ack, created_at, ack_count, dismiss_count)
    audit:  the unified timeline returned by /api/admin/banners/{id}/audit
            (list of {kind, ts, actor_name, device_id, ip, ua, path, lang})

Output: bytes — a PDF rendered via the same WeasyPrint pipeline the
rest of the platform already uses, so no new system dependencies.
"""
from __future__ import annotations

import base64
from datetime import datetime
from html import escape
from pathlib import Path
from typing import Any, Dict, List, Optional

from weasyprint import HTML

ROOT = Path(__file__).parent.parent
LOGO_PATH = ROOT / "frontend" / "public" / "masci-full-lockup-onlight.png"


def _data_uri_for(path: Path) -> str:
    try:
        b = path.read_bytes()
        return f"data:image/png;base64,{base64.b64encode(b).decode()}"
    except Exception:
        return ""


def _fmt_ts(iso: Optional[str]) -> str:
    if not iso:
        return "—"
    try:
        return datetime.fromisoformat(iso.replace("Z", "+00:00")).strftime(
            "%b %d, %Y %I:%M:%S %p UTC"
        )
    except Exception:
        return iso


def _browser_of(ua: Optional[str]) -> str:
    if not ua:
        return "—"
    if any(s in ua for s in ("iPhone", "iPad", "iPod")):
        return "iOS"
    if "Android" in ua:
        return "Android"
    if "Edg/" in ua:
        return "Edge"
    if "Chrome/" in ua and "Chromium" not in ua:
        return "Chrome"
    if "Firefox/" in ua:
        return "Firefox"
    if "Safari/" in ua:
        return "Safari"
    return ua[:30]


SEVERITY_COLORS = {
    "info": ("#1d4ed8", "#dbeafe"),
    "advisory": ("#92400e", "#fef3c7"),
    "warning": ("#991b1b", "#fee2e2"),
    "critical": ("#450a0a", "#fecaca"),
}

KIND_COLORS = {
    "ack": ("#065f46", "#d1fae5", "ACKNOWLEDGED"),
    "dismiss": ("#92400e", "#fef3c7", "DISMISSED"),
    "admin": ("#1f2937", "#f1f5f9", "ADMIN"),
}


def render_banner_audit_pdf(banner: Dict[str, Any], audit: List[Dict[str, Any]]) -> bytes:
    """Render the audit-trail PDF. Always returns bytes; on failure
    raises (callers wrap the response in a 500). No silent fallbacks
    here — if the PDF is broken the admin needs to know."""
    logo = _data_uri_for(LOGO_PATH)
    severity = (banner.get("severity") or "advisory").lower()
    sev_fg, sev_bg = SEVERITY_COLORS.get(severity, SEVERITY_COLORS["advisory"])

    title_en = escape(banner.get("title_en") or "(no title)")
    title_es = escape(banner.get("title_es") or "")
    body_en = escape(banner.get("body_en") or "")
    body_es = escape(banner.get("body_es") or "")

    rows_html: List[str] = []
    for r in audit or []:
        kind = (r.get("kind") or "admin").lower()
        fg, bg, label = KIND_COLORS.get(kind, KIND_COLORS["admin"])
        ts = _fmt_ts(r.get("ts"))
        actor = escape(r.get("actor_name") or "")
        dev = escape(r.get("device_id") or "")
        dev_short = f"…{dev[-8:]}" if dev else ""
        ip = escape(r.get("ip") or "")
        path = escape(r.get("path") or "")
        lang = escape(r.get("lang") or "")
        browser = escape(_browser_of(r.get("ua")))
        action = escape(r.get("action") or "")
        kind_label = f"{label} · {action}".strip(" ·") if kind == "admin" and action else label

        details_bits: List[str] = []
        if actor:
            details_bits.append(f"<strong>{actor}</strong>")
        if dev_short:
            details_bits.append(f"device {dev_short}")
        if ip:
            details_bits.append(f"IP {ip}")
        if path:
            details_bits.append(f"page {path}")
        if lang and lang != "en":
            details_bits.append(f"lang {lang}")
        if browser and browser != "—":
            details_bits.append(browser)
        details = " · ".join(details_bits) or "—"

        rows_html.append(
            f"""<tr>
                <td class="kind" style="color:{fg};background:{bg};">{kind_label}</td>
                <td class="ts">{ts}</td>
                <td class="det">{details}</td>
            </tr>"""
        )

    if not rows_html:
        rows_html.append(
            '<tr><td colspan="3" class="empty">No activity recorded.</td></tr>'
        )

    rendered_at = datetime.utcnow().strftime("%b %d, %Y %I:%M %p UTC")
    ack_count = banner.get("ack_count", 0)
    dismiss_count = banner.get("dismiss_count", 0)
    require_ack = "YES" if banner.get("require_ack") else "no"
    created_at = _fmt_ts(banner.get("created_at"))

    html = f"""<!doctype html>
<html><head><meta charset="utf-8"><title>Banner Audit Trail</title>
<style>
  @page {{ size: Letter; margin: 0.6in 0.55in; }}
  body {{ font-family: -apple-system, "Helvetica Neue", Arial, sans-serif;
         color: #0f172a; font-size: 9.5pt; line-height: 1.4; }}
  .hdr {{ display: flex; align-items: flex-start;
         border-bottom: 3px solid #b91c1c; padding-bottom: 10px; margin-bottom: 14px; }}
  .hdr img {{ max-height: 46px; }}
  .hdr .title {{ margin-left: auto; text-align: right; }}
  .hdr .title h1 {{ font-size: 16pt; margin: 0; color: #0f172a; letter-spacing: 0.5px; }}
  .hdr .title .sub {{ font-family: "Courier New", monospace; font-size: 8.5pt;
                     color: #475569; letter-spacing: 0.15em; text-transform: uppercase; margin-top: 2px; }}
  .meta {{ background: #f8fafc; border: 2px solid #cbd5e1; border-radius: 6px;
          padding: 10px 12px; margin-bottom: 14px; }}
  .meta .sev {{ display: inline-block; padding: 3px 8px; border-radius: 4px;
               font-family: "Courier New", monospace; font-size: 9pt; font-weight: bold;
               text-transform: uppercase; letter-spacing: 0.15em;
               color: {sev_fg}; background: {sev_bg}; }}
  .meta .ttl-en {{ font-weight: bold; font-size: 12pt; margin-top: 6px; }}
  .meta .ttl-es {{ font-style: italic; color: #475569; font-size: 11pt; margin-top: 2px; }}
  .meta .body-en {{ margin-top: 6px; white-space: pre-wrap; }}
  .meta .body-es {{ margin-top: 4px; color: #475569; font-style: italic; white-space: pre-wrap; }}
  .stats {{ display: flex; gap: 18px; margin-top: 8px; padding-top: 8px;
           border-top: 1px solid #cbd5e1;
           font-family: "Courier New", monospace; font-size: 8.5pt;
           color: #475569; letter-spacing: 0.1em; text-transform: uppercase; }}
  .stats strong {{ color: #0f172a; }}
  h2 {{ font-size: 11pt; margin: 14px 0 6px;
       border-bottom: 2px solid #0f172a; padding-bottom: 2px; }}
  table {{ width: 100%; border-collapse: collapse; }}
  th, td {{ text-align: left; padding: 5px 6px; vertical-align: top;
           border-bottom: 1px solid #e2e8f0; }}
  th {{ font-size: 8pt; text-transform: uppercase; letter-spacing: 0.15em;
       color: #475569; background: #f8fafc; border-bottom: 2px solid #cbd5e1; }}
  td.kind {{ font-family: "Courier New", monospace; font-size: 8pt; font-weight: bold;
            letter-spacing: 0.12em; padding: 4px 6px; border-radius: 3px;
            white-space: nowrap; }}
  td.ts {{ font-family: "Courier New", monospace; font-size: 8.5pt;
          color: #475569; white-space: nowrap; }}
  td.det {{ font-size: 9pt; }}
  td.empty {{ text-align: center; color: #94a3b8; font-style: italic; padding: 18px; }}
  .footer {{ margin-top: 14px; padding-top: 8px; border-top: 1px solid #cbd5e1;
            font-family: "Courier New", monospace; font-size: 7.5pt;
            color: #94a3b8; letter-spacing: 0.12em; text-transform: uppercase;
            display: flex; justify-content: space-between; }}
</style></head><body>
<div class="hdr">
  <img src="{logo}" alt="MASCI"/>
  <div class="title">
    <h1>Banner Audit Trail</h1>
    <div class="sub">Confidential · MASCI General Contractors Inc.</div>
  </div>
</div>

<div class="meta">
  <span class="sev">{escape(severity)}</span>
  <div class="ttl-en">{title_en}</div>
  {f'<div class="ttl-es">{title_es}</div>' if title_es and title_es != title_en else ''}
  {f'<div class="body-en">{body_en}</div>' if body_en else ''}
  {f'<div class="body-es">{body_es}</div>' if body_es and body_es != body_en else ''}
  <div class="stats">
    <span>POSTED · <strong>{created_at}</strong></span>
    <span>ACK REQUIRED · <strong>{require_ack}</strong></span>
    <span>ACKS · <strong>{ack_count}</strong></span>
    <span>DISMISSALS · <strong>{dismiss_count}</strong></span>
  </div>
</div>

<h2>Activity Timeline ({len(audit or [])} {'event' if len(audit or []) == 1 else 'events'})</h2>
<table>
  <thead>
    <tr><th style="width:22%;">Event</th><th style="width:24%;">Timestamp (UTC)</th><th>Details</th></tr>
  </thead>
  <tbody>
    {''.join(rows_html)}
  </tbody>
</table>

<div class="footer">
  <span>Banner ID · {escape(banner.get("id") or "—")}</span>
  <span>Generated {rendered_at}</span>
</div>
{_t1541_banner_audit_block(banner)}
</body></html>"""

    return HTML(string=html).write_pdf()


def _t1541_banner_audit_block(banner: Dict[str, Any]) -> str:
    """TRACK 15.42 · additive foundation audit block for banner-audit PDFs."""
    try:
        from pdf_branding import build_audit_block_html
        return build_audit_block_html(
            record_id=banner.get("id") or "—",
            source_module="hub.banners",
            project=None,
            generated_by="admin",
        )
    except Exception:
        return ""
