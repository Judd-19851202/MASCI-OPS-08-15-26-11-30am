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

# TRACK 27.03 · Phase 2 · Route every operator-visible "Generated" stamp
# through the canonical platform-time formatter so PDFs, emails, and
# exports never leak UTC into a human-facing field.
from lib.platform_time import format_platform_stamp


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
    """Read PDF brand from active tenant context first, then PDF_BRAND_*
    env vars with MASCI fallbacks. Called fresh per render so a tenant
    branding change takes effect on the next PDF without a backend
    restart.

    Track 15.68A: prioritises `tenant_branding` doc so Customer #2 PDFs
    automatically inherit their branding (`company_name`,
    `platform_display_name`, `logo_url`, `primary_color`) without env
    edits or code changes."""
    # Best-effort tenant lookup. Falls back to env on any error so MASCI
    # behaviour is preserved when the tenant doc / DB is unreachable.
    tenant_brand = _read_tenant_brand_sync()
    return WhiteLabelConfig(
        brand_name=(
            tenant_brand.get("brand_name")
            or os.environ.get("PDF_BRAND_NAME")
            or _DEFAULT_BRAND_NAME
        ),
        brand_long_name=(
            tenant_brand.get("brand_long_name")
            or os.environ.get("PDF_BRAND_LONG_NAME")
            or _DEFAULT_BRAND_LONG
        ),
        brand_logo_url=(
            tenant_brand.get("brand_logo_url")
            or os.environ.get("PDF_BRAND_LOGO_URL", "")
        ),
        brand_color=(
            tenant_brand.get("brand_color")
            or os.environ.get("PDF_BRAND_COLOR_HEX")
            or _DEFAULT_BRAND_COLOR
        ).lstrip("#"),
        footer_tagline=(
            tenant_brand.get("footer_tagline")
            or os.environ.get("PDF_BRAND_FOOTER_TAGLINE")
            or _DEFAULT_TAGLINE
        ),
        company_legal_name=(
            tenant_brand.get("company_legal_name")
            or os.environ.get("PDF_BRAND_LEGAL_LINE")
            or _DEFAULT_LEGAL
        ),
        platform_owner="ForgedOps\u2122",
    )


def _read_tenant_brand_sync() -> dict:
    """Synchronously read the active tenant's branding doc. Returns
    {} on any error (DB down, tenant is MASCI, etc.). Uses a synchronous
    Mongo client so it works inside WeasyPrint render contexts that
    aren't async-aware."""
    try:
        from tenant_context import resolve_tenant_key, is_masci
        tk = resolve_tenant_key()
        # MASCI tenant — preserve env-driven path. The MASCI doc itself
        # mirrors env defaults, but we shortcut here so MASCI PDFs are
        # bit-for-bit identical to the pre-15.68A output.
        if is_masci(tk):
            return {}
        from pymongo import MongoClient  # type: ignore
        client = MongoClient(os.environ["MONGO_URL"], serverSelectionTimeoutMS=1000)
        doc = client[os.environ["DB_NAME"]].tenant_branding.find_one(
            {"_id": tk}, {"_id": 0}
        ) or {}
        client.close()
        if not doc:
            return {}
        company = doc.get("company_name") or "Customer"
        display = doc.get("platform_display_name") or "Operations Platform"
        return {
            "brand_name": company,
            "brand_long_name": display,
            "brand_logo_url": doc.get("logo_url") or "",
            "brand_color": (doc.get("primary_color") or "").lstrip("#"),
            "footer_tagline": (
                f"Generated through {display} — Powered by ForgedOps™ | "
                f"© 2026 ForgedOps™"
            ),
            "company_legal_name": (
                f"{company}"
                + (f" · {doc.get('support_email')}" if doc.get("support_email") else "")
            ),
        }
    except Exception:
        return {}


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
    # Storage of `generated_at` stays UTC (aware datetime); display is
    # rendered via the canonical local formatter — never raw UTC.
    when = format_platform_stamp(generated_at or datetime.now(timezone.utc))
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
    when = format_platform_stamp(datetime.now(timezone.utc))
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
    # TRACK 15.42 · Universal adoption — optional foundation chrome.
    # Any caller can pass these to gain audit + metadata blocks
    # without rewriting their renderer. Backwards compatible:
    # omit them and the wrapper behaves exactly as before.
    audit_record_id: Optional[str] = None,
    audit_source_module: Optional[str] = None,
    audit_project: Optional[str] = None,
    audit_generated_by: Optional[str] = None,
    metadata_document_type: Optional[str] = None,
    metadata_document_id: Optional[str] = None,
    metadata_project_number: Optional[str] = None,
) -> str:
    """Compose a full <html> document with brand chrome + body content.

    TRACK 15.42 · `audit_*` and `metadata_*` kwargs are additive — when
    provided, the wrapper injects a Universal Metadata block right after
    the brand bar and a Universal Audit block immediately before
    `</body>`. Existing body content is never modified.
    """
    generated = format_platform_stamp(datetime.now(timezone.utc))
    meta_html = ""
    if metadata_document_type or audit_source_module:
        meta_html = build_metadata_block_html(
            document_type=metadata_document_type or (kicker or title or "Document"),
            document_id=metadata_document_id or audit_record_id,
            project_number=metadata_project_number,
        )
    audit_html = ""
    if audit_source_module:
        audit_html = build_audit_block_html(
            record_id=audit_record_id or "—",
            source_module=audit_source_module,
            project=audit_project,
            generated_by=audit_generated_by,
        )
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
{meta_html}
{body_html}
{audit_html}
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
