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
"""
from __future__ import annotations

from datetime import datetime, timezone

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


__all__ = ["BRAND_CSS", "brand_header", "wrap_pdf_html"]
