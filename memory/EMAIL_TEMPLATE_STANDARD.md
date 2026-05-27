# Email Template Standard — Phase IV-B

**Iteration:** iter437+ · Phase IV · 2026-02
**Status:** 🟡 TEMPLATE SPECIFIED · CODE EXTRACTION DEFERRED
**Gold standard source:** `/app/backend/po_digest.py` lines 246–280

This document is the **machine-readable specification** of the canonical email shell. Any new email rendered by the platform after Phase IV.B.1 ships MUST conform to this spec.

---

## Visual structure (top to bottom)

```
┌─────────────────────────────────────────────┐  outer wrapper · max-w 640 px
│  ▓▓▓▓ INDIGO HEADER BAND ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓ │  bg #4338ca · padding 16/22 · radius 6 0 0 6
│  MASCI · <DOMAIN>                           │  mono · 11px · 0.18em tracking · opacity 0.85
│  <Headline>                                 │  22px · weight 900
│  <Date · Recipient label>                   │  11px · opacity 0.85
│                                             │
│  ─────────────────────────────────────────  │
│  ░░░░░ WHITE BODY ░░░░░░░░░░░░░░░░░░░░░░  │  bg white · 1px border slate-200 · radius 0 0 6 6
│                                             │
│  <Intro paragraph · 13px · slate-600>       │  margin 0 0 14 0 · line-height 1.5
│                                             │
│  ┌──────────────┬──────────────┐           │  KPI cards · 2-up table
│  │ KPI 1 (sev)  │ KPI 2 (sev)  │           │  radii 4 0 0 4 / 0 4 4 0
│  └──────────────┴──────────────┘           │
│                                             │
│  SECTION HEADER (mono · uppercase)          │  13px · 0.18em tracking
│  <data table or content>                    │
│                                             │
│       ┌─────────────────────┐               │  centered CTA button
│       │  OPEN < SCREEN > →  │               │  bg #4338ca · padding 10/22 · radius 4
│       └─────────────────────┘               │  13px · weight 700 · 0.04em tracking · uppercase
│                                             │
│  ─────────────────────────────────────────  │
│  <Footer signature · 11px slate-400 ·       │  border-top 1px slate-100 · padding-top 10
│   1-2 lines explaining what + who acts>     │
└─────────────────────────────────────────────┘
```

---

## Exact CSS contract (inline styles · MJML-free)

### Outer wrapper

```html
<div style="font-family:Helvetica,Arial,sans-serif;max-width:640px;margin:0 auto;color:#0f172a">
```

### Header band

```html
<div style="background:#4338ca;color:white;padding:16px 22px;border-radius:6px 6px 0 0">
  <div style="font-family:Courier,monospace;font-size:11px;letter-spacing:0.18em;opacity:0.85">
    MASCI · {DOMAIN_UPPERCASE}
  </div>
  <h1 style="font-size:22px;margin:4px 0 0;font-weight:900">{Headline}</h1>
  <div style="font-size:11px;opacity:0.85;margin-top:4px">{date_iso_10}{ · }{recipient_label}</div>
</div>
```

### Body container

```html
<div style="background:white;border:1px solid #e5e7eb;border-top:none;padding:18px 22px;border-radius:0 0 6px 6px">
  <p style="margin:0 0 14px;font-size:13px;color:#475569;line-height:1.5">{intro_html}</p>
  ...
</div>
```

### KPI card pair (two-up table)

```html
<table cellpadding="0" cellspacing="0" border="0" style="width:100%;border-collapse:collapse;margin:0 0 6px"><tr>
  <td style="width:50%;padding:8px 10px;background:{sev_bg_left};border:1px solid {sev_border_left};border-radius:4px 0 0 4px">
    <div style="font-family:Courier,monospace;font-size:10px;letter-spacing:0.18em;color:{sev_fg_left};font-weight:700;text-transform:uppercase">
      {kpi_label_left}
    </div>
    <div style="font-size:26px;font-weight:900;color:{sev_fg_left};line-height:1.1;margin-top:4px">
      {kpi_value_left}
    </div>
  </td>
  <td style="width:50%;padding:8px 10px;background:{sev_bg_right};border:1px solid {sev_border_right};border-radius:0 4px 4px 0">
    {... mirrored ...}
  </td>
</tr></table>
```

### Section header

```html
<h2 style="font-size:13px;margin:18px 0 6px;color:#0f172a;font-family:Courier,monospace;letter-spacing:0.18em;text-transform:uppercase">
  {Section Label}
</h2>
```

### Data row table

```html
<table cellpadding="0" cellspacing="0" border="0" style="width:100%;border-collapse:collapse;border:1px solid #e5e7eb;border-radius:4px">
  <tr style="background:#f8fafc">
    <td style="padding:8px 10px;font-family:Courier,monospace;font-size:11px;letter-spacing:0.04em;color:#475569;font-weight:700;text-transform:uppercase;border-bottom:1px solid #e5e7eb">
      {column_label}
    </td>
    ...
  </tr>
  <tr>
    <td style="padding:8px 10px;font-size:13px;color:#0f172a;border-bottom:1px solid #f1f5f9">
      {row_value}
    </td>
    ...
  </tr>
</table>
```

### Primary CTA

```html
<div style="margin-top:22px;text-align:center">
  <a href="{cta_url}" style="display:inline-block;background:#4338ca;color:white;text-decoration:none;font-weight:700;font-size:13px;padding:10px 22px;border-radius:4px;letter-spacing:0.04em;text-transform:uppercase">
    {cta_label} &rarr;
  </a>
</div>
```

### Footer

```html
<p style="margin:22px 0 0;font-size:11px;color:#94a3b8;line-height:1.5;border-top:1px solid #f1f5f9;padding-top:10px">
  {footer_signature_line_1}
  {footer_signature_line_2}
</p>
```

---

## Severity palette (the only allowed KPI/badge colors)

| Severity | bg | border | fg |
|---|---|---|---|
| `info` | `#eef2ff` | `#c7d2fe` | `#3730a3` |
| `pending` | `#fef3c7` | `#fde68a` | `#92400e` |
| `overdue` | `#fee2e2` | `#fecaca` | `#991b1b` |
| `neutral` | `#f1f5f9` | `#e2e8f0` | `#0f172a` |

No other colors are permitted inside the email body.

---

## Subject-line contract

| Urgency | Subject prefix | Subject body |
|---|---|---|
| Routine | `[MASCI] ` | `<Plain English subject>` |
| Action needed | `[MASCI] Action needed — ` | `<Plain English subject>` |
| Time-sensitive | `[MASCI] Action by <YYYY-MM-DD> — ` | `<Plain English subject>` |
| Critical | `[MASCI · CRITICAL] ` | `<Plain English subject>` |

Subjects never use ALL CAPS. Never use emojis. Never exceed 78 characters total.

---

## Footer signature templates (per email type)

| Email type | Signature |
|---|---|
| Weekly digest | `MASCI Operations Platform · <Domain> Digest · <Cadence>.\n<One-line operational context>` |
| Action notification | `MASCI Operations Platform · <Feature> · <Who triggered it>.\n<What recipient needs to do.>` |
| Magic link | `MASCI Operations Platform · Magic Link · Issued by <Issuer Role>.\nThis link expires in <N> hours and can only be used once.` |
| Password reset | `MASCI Operations Platform · Password Reset.\nIf you did not request this, ignore the email. The link expires in 30 minutes.` |
| Invitation | `MASCI Operations Platform · Account Invitation.\nThis invitation expires in 7 days.` |

Each signature is exactly 2 lines. No "Best regards", no "Thanks", no taglines.

---

## API contract for `lib/email_shell.render_email(...)`

```python
def render_email(
    *,
    domain_uppercase: str,             # "PO OPERATIONS", "SAFETY", "HR", etc.
    headline: str,                     # "Weekly Request PO Digest"
    timestamp_iso: str,                # "2026-05-27T03:30:00+00:00" — first 10 chars used
    recipient_label: str,              # "Project Manager: Jaymn Judd"
    intro_html: str,                   # "<Body intro · 1-2 sentences>"
    kpi_pairs: list[KpiPair] = [],     # max 4 pairs (8 total KPIs)
    sections: list[Section] = [],      # zero or more section_label + html_body
    cta: Optional[CTA] = None,         # label + url
    footer_signature: str,             # exact 2-line signature
) -> tuple[str, str]:                  # (html, plaintext)
    ...
```

The function returns a tuple of `(html, plaintext)` so every email automatically has a plaintext fallback.

---

## Migration map (8 callers · ordered)

| # | Caller file | Current shell | Migration target |
|---|---|---|---|
| 1 | `po_digest.py` | `_pm_digest_html` (REFERENCE) | Re-export from `lib/email_shell.py` |
| 2 | `lib/operator_digest.py` | Custom layout | Use `render_email()` |
| 3 | `routes/safety_portal/digest.py` | Partially borrowed | Use `render_email()` |
| 4 | `routes/safety_portal/auth_users.py` | Plain `<p>` | Use `render_email()` |
| 5 | `routes/payroll_variance.py` | Plain table | Use `render_email()` |
| 6 | `routes/admin_digest_config.py` | Configurable | Use `render_email()` |
| 7 | `pm_routing.py` | Inline plaintext only | Add HTML via `render_email()` |
| 8 | Magic-link / notification ad-hoc | Various | Audit + use `render_email()` |

---

## Test coverage requirement

`/app/backend/tests/test_email_shell_conformance.py` (Phase IV.B.3) will assert for every send-email call site that the rendered HTML body:

- Starts with `<div style="font-family:Helvetica,Arial,sans-serif;max-width:640px;`
- Contains `MASCI · `
- Contains the canonical indigo `#4338ca` in the header
- Ends with the footer signature block + `</div>`
- Plaintext fallback is present and non-empty

Failure of any assertion = CI failure.

---

## Verdict

🟡 **TEMPLATE SPECIFIED · IMPLEMENTATION DEFERRED.** Once `lib/email_shell.py` lands in Phase IV.B.1, all 8 caller migrations proceed one at a time per the migration map above.
