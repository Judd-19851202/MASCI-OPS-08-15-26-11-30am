"""
pdf_branding.py — Iter136 (Phase-1 Iter C). Shared PDF chrome so every
report/guide/history.pdf coming out of the platform looks like the same
product. Each generator imports `BRAND_CSS` and `wrap_pdf_html(body,
title=...)` to get consistent header, footer, and typography.

Usage:
    from pdf_branding import BRAND_CSS, wrap_pdf_html
    html_body = "<h1>My Report</h1>…"  # body-only HTML
    full = wrap_pdf_html(html_body, title="My Report", kicker="SAFETY · REPORT")
    pdf = HTML(string=full).write_pdf()

TRACK 15.41 · Universal PDF Foundation
--------------------------------------
Extended with white-label support + audit/metadata block helpers that
ANY PDF generator (WeasyPrint HTML or ReportLab canvas) can call to
get the same trusted chrome:

    from pdf_branding import (
        get_white_label,              # WhiteLabelConfig from env
        build_audit_block_html,       # HTML snippet for HTML PDFs
        build_metadata_block_html,    # HTML snippet for HTML PDFs
        BRAND_CSS, wrap_pdf_html,     # existing
    )

Foundation rules (CRITICAL DIRECTIVE #3):
* Additive only — never strip existing body content.
* AFTER PDF text MUST be a superset of BEFORE PDF text.
* MASCI remains the default white-label config; env vars override.
* No new collections, no new endpoints, no schema changes.
"""
from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import datetime, timezone
from html import escape
from typing import Optional


# ───────────────────────── WHITE-LABEL CONFIG (env-driven) ──────────────────
#
# MASCI defaults are baked in so every legacy PDF keeps the exact same
# branding it had before this track. Future ForgedOps customers override
# via env vars — no collection, no DB write, no migration.

@dataclass(frozen=True)
class WhiteLabelConfig:
    brand_name: str            # e.g. "MASCI"
    brand_long_name: str       # e.g. "MASCI Operations Platform"
    brand_logo_url: str        # data:/... URI or http(s)://... URL
    brand_color: str           # hex (without the #)
    footer_tagline: str        # bottom-of-page tagline
    company_legal_name: str    # legal-line copyright owner
    platform_owner: str        # e.g. "ForgedOps™" — never overridden


_DEFAULT_BRAND_NAME = "MASCI"
_DEFAULT_BRAND_LONG = "MASCI Operations Platform"
_DEFAULT_BRAND_COLOR = "c8102e"
_DEFAULT_TAGLINE = (
    "Generated through MASCI Operations Platform "
    "\u2014 Powered by ForgedOps\u2122 | \u00A9 2026 ForgedOps\u2122"
)
_DEFAULT_LEGAL = "MASCI General Contractors Inc. · 386-322-4500 · mascidocs.com"


def get_white_label() -> WhiteLabelConfig:
    """Read PDF_BRAND_* env vars with MASCI fallbacks. Called fresh
    per render so a config change takes effect on the next PDF without
    a backend restart."""
    return WhiteLabelConfig(
        brand_name=os.environ.get("PDF_BRAND_NAME", _DEFAULT_BRAND_NAME),
        brand_long_name=os.environ.get(
            "PDF_BRAND_LONG_NAME", _DEFAULT_BRAND_LONG,
        ),
        brand_logo_url=os.environ.get("PDF_BRAND_LOGO_URL", ""),
        brand_color=os.environ.get(
            "PDF_BRAND_COLOR_HEX", _DEFAULT_BRAND_COLOR,
        ).lstrip("#"),
        footer_tagline=os.environ.get(
            "PDF_BRAND_FOOTER_TAGLINE", _DEFAULT_TAGLINE,
        ),
        company_legal_name=os.environ.get(
            "PDF_BRAND_LEGAL_LINE", _DEFAULT_LEGAL,
        ),
        platform_owner="ForgedOps\u2122",
    )


# ───────────────────────── ENVIRONMENT TAG ─────────────────────────────────
#
# Used on the audit block. preview / production / staging / dev — pulled
# from the same DB_NAME the rest of the platform uses, so the tag is
# always correct for the running environment.

def _env_tag() -> str:
    db = (os.environ.get("DB_NAME") or "").lower()
    if "preview" in db:
        return "PREVIEW"
    if "stag" in db:
        return "STAGING"
    if "dev" in db:
        return "DEV"
    if db:
        return "PRODUCTION"
    return "UNKNOWN"


# ───────────────────────── FOUNDATION VERSION ───────────────────────────────
#
# Bumped by track #. Appears on every audit block so legal discovery can
# pin a PDF to the foundation revision that produced it.
PDF_FOUNDATION_VERSION = "15.41.1"


# ───────────────────────── AUDIT BLOCK (HTML) ───────────────────────────────

def build_audit_block_html(
    *,
    record_id: str,
    source_module: str,
    project: Optional[str] = None,
    document_version: Optional[str] = None,
    generated_by: Optional[str] = None,
    generated_at: Optional[datetime] = None,
) -> str:
    """Return a tiny HTML snippet that any HTML-based PDF can append
    just above the final closing </body>. Mono-spaced, page-break-
    avoidant, last-page friendly. Renders only fields the caller passes.

    Track 15.41 · Universal Audit Block. Foundation requirement.
    """
    wl = get_white_label()
    when = (generated_at or datetime.now(timezone.utc)).strftime("%Y-%m-%d %H:%M:%S UTC")
    rows = [
        ("Record ID", record_id),
        ("Source Module", source_module),
        ("Project", project or "—"),
        ("Document Version", document_version or PDF_FOUNDATION_VERSION),
        ("Generated By", generated_by or "system"),
        ("Generated On", when),
        ("Environment", _env_tag()),
        ("Foundation", f"v{PDF_FOUNDATION_VERSION}"),
    ]
    cells = "".join(
        f'<tr><td class="t1541-k">{escape(k)}</td>'
        f'<td class="t1541-v">{escape(str(v))}</td></tr>'
        for k, v in rows
    )
    return (
        '<div class="t1541-audit" data-track="15.41" '
        'style="page-break-inside:avoid;margin-top:14pt;padding:8pt 10pt;'
        f'border:1px solid #cbd5e1;border-left:3px solid #{wl.brand_color};'
        'border-radius:3px;background:#f8fafc;">'
        '<div class="t1541-audit-title" '
        'style="font-family:\'Courier New\',monospace;font-size:8pt;'
        'letter-spacing:0.18em;text-transform:uppercase;'
        'color:#475569;margin-bottom:4pt;font-weight:700;">'
        'Audit Trail \u00B7 Foundation v' + PDF_FOUNDATION_VERSION +
        '</div>'
        '<table class="t1541-audit-table" '
        'style="width:100%;border-collapse:collapse;font-size:8pt;'
        'font-family:\'Courier New\',monospace;">'
        + cells +
        '</table>'
        '<style>'
        '.t1541-audit-table .t1541-k {'
        ' width:30%;padding:1pt 6pt 1pt 0;color:#64748b;'
        ' letter-spacing:0.1em;text-transform:uppercase;}'
        '.t1541-audit-table .t1541-v {'
        ' padding:1pt 0;color:#0f172a;}'
        '</style></div>'
    )


# ───────────────────────── METADATA BLOCK (HTML) ────────────────────────────

def build_metadata_block_html(
    *,
    document_type: str,
    document_id: Optional[str] = None,
    project_number: Optional[str] = None,
    extra: Optional[dict] = None,
) -> str:
    """Return an HTML snippet that lives in the document header area
    (typically right next to the brand bar). Captures the things every
    PDF needs at-a-glance: doc type, project, doc id, generated time.

    Track 15.41 · Universal Metadata Block. Foundation requirement.
    """
    when = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    pieces = []
    pieces.append(f'<span class="t1541-meta-k">DocType:</span> {escape(document_type)}')
    if document_id:
        pieces.append(f'<span class="t1541-meta-k">DocID:</span> {escape(str(document_id))}')
    if project_number:
        pieces.append(f'<span class="t1541-meta-k">Project#:</span> {escape(str(project_number))}')
    pieces.append(f'<span class="t1541-meta-k">Generated:</span> {escape(when)}')
    pieces.append(f'<span class="t1541-meta-k">Env:</span> {escape(_env_tag())}')
    if extra:
        for k, v in extra.items():
            if v:
                pieces.append(f'<span class="t1541-meta-k">{escape(str(k))}:</span> {escape(str(v))}')
    return (
        '<div class="t1541-meta" data-track="15.41" '
        'style="font-family:\'Courier New\',monospace;font-size:7pt;'
        'letter-spacing:0.12em;text-transform:uppercase;color:#475569;'
        'margin:0 0 6pt 0;padding:0;">'
        + ' \u00B7 '.join(pieces)
        + '<style>.t1541-meta .t1541-meta-k{color:#94a3b8;'
          'font-weight:700;letter-spacing:0.18em;}</style>'
        '</div>'
    )


BRAND_CSS = """
@page {
  size: letter;
  margin: 0.75in;
  @top-right {
    content: "MASCI Operations Platform";
    font-family: 'Helvetica', Arial, sans-serif;
    font-size: 8pt;
    color: #94a3b8;
    letter-spacing: 0.12em;
    text-transform: uppercase;
  }
  @bottom-left {
    content: "Generated " env(generated_at);
    font-family: 'Helvetica', Arial, sans-serif;
    font-size: 8pt;
    color: #94a3b8;
  }
  @bottom-right {
    content: "Page " counter(page) " of " counter(pages);
    font-family: 'Helvetica', Arial, sans-serif;
    font-size: 8pt;
    color: #94a3b8;
  }
}
body {
  font-family: 'Helvetica', Arial, sans-serif;
  color: #0f172a;
  font-size: 11pt;
  line-height: 1.5;
}
.brand-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  border-bottom: 3px solid #b91c1c;
  padding-bottom: 6pt;
  margin-bottom: 12pt;
}
.brand-mark {
  font-family: 'Helvetica', Arial Black, sans-serif;
  font-size: 22pt;
  font-weight: 900;
  color: #b91c1c;
  letter-spacing: -0.02em;
}
.brand-tag {
  font-family: 'Courier New', monospace;
  font-size: 8pt;
  letter-spacing: 0.16em;
  text-transform: uppercase;
  color: #475569;
}
.report-kicker {
  font-family: 'Courier New', monospace;
  letter-spacing: 0.18em;
  font-size: 9pt;
  color: #475569;
  text-transform: uppercase;
}
.report-title {
  font-size: 22pt;
  margin: 2pt 0 4pt 0;
  color: #0f172a;
  font-weight: 900;
  letter-spacing: -0.01em;
}
h1 { font-size: 22pt; margin: 4pt 0 6pt 0; color: #0f172a; }
h2 { font-size: 14pt; margin: 18pt 0 4pt 0; color: #0c4a6e; border-bottom: 2px solid #e2e8f0; padding-bottom: 3pt; }
h3 { font-size: 11pt; margin: 12pt 0 3pt 0; color: #1e293b; }
p { margin: 6pt 0; }
table { width: 100%; border-collapse: collapse; font-size: 10pt; }
th { background: #f1f5f9; text-align: left; padding: 5pt 7pt;
     font-family: 'Courier New', monospace; font-size: 8pt; letter-spacing: 0.14em;
     color: #475569; text-transform: uppercase; border-bottom: 2px solid #cbd5e1; }
td { padding: 5pt 7pt; border-bottom: 1px solid #e2e8f0; vertical-align: top; }
code { background: #f1f5f9; padding: 1px 4px; border-radius: 3px; font-size: 9.5pt; }
.callout-tip  { background: #ecfeff; border-left: 4px solid #0e7490; padding: 8pt 10pt; margin: 8pt 0; font-size: 10pt; }
.callout-warn { background: #fef3c7; border-left: 4px solid #b45309; padding: 8pt 10pt; margin: 8pt 0; font-size: 10pt; }
.status-pass  { color: #047857; font-weight: 700; }
.status-fail  { color: #b91c1c; font-weight: 700; }
.status-other { color: #92400e; font-weight: 700; }
.muted { color: #64748b; }
"""


def brand_header(title: str = "", kicker: str = "") -> str:
    """Standard top-of-document brand bar — red MASCI mark + kicker + title."""
    parts = ['<div class="brand-bar"><div class="brand-mark">MASCI</div>',
             '<div class="brand-tag">Operations Platform</div></div>']
    if kicker:
        parts.append(f'<div class="report-kicker">{kicker}</div>')
    if title:
        parts.append(f'<div class="report-title">{title}</div>')
    return "".join(parts)


def wrap_pdf_html(
    body_html: str,
    *,
    title: str = "",
    kicker: str = "",
    extra_css: str = "",
) -> str:
    """Compose a full <html> document with brand chrome + body content."""
    generated = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    return f"""<!DOCTYPE html>
<html><head><meta charset="utf-8" />
<style>
{BRAND_CSS}
:root {{ --generated-at: "{generated}"; }}
@page {{ @bottom-left {{ content: "Generated {generated}"; }} }}
{extra_css}
</style></head>
<body>
{brand_header(title, kicker)}
{body_html}
</body></html>
"""


__all__ = [
    "BRAND_CSS",
    "brand_header",
    "wrap_pdf_html",
    # TRACK 15.41 · Universal PDF Foundation exports
    "WhiteLabelConfig",
    "get_white_label",
    "build_audit_block_html",
    "build_metadata_block_html",
    "PDF_FOUNDATION_VERSION",
]
