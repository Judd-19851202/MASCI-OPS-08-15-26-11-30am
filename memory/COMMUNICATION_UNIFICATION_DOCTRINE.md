# Communication Unification Doctrine — Phase IV-B

**Iteration:** iter437+ · Phase IV · 2026-02
**Status:** 🟡 DOCTRINE LOCKED · IMPLEMENTATION DEFERRED
**Gold standard:** `/app/backend/po_digest.py` `_pm_digest_html` shell

---

## Why this exists

The platform now sends email from at least **8 distinct render paths**:

| Source | What it sends | Visual identity |
|---|---|---|
| `po_digest.py` | Weekly PO digest to PMs | ✅ Modern indigo shell + monospace eyebrow + KPI cards |
| `lib/operator_digest.py` | Weekly operations digest | 🟡 Different layout · plain table |
| `routes/safety_portal/digest.py` | Weekly safety digest | 🟡 Different layout · partially borrowed |
| `routes/safety_portal/auth_users.py` | Password reset, invitations | 🟠 Plain `<p>` tags, no shell |
| `routes/payroll_variance.py` | Payroll variance batch | 🟠 Plain table dump |
| `routes/admin_digest_config.py` | Configurable digest | 🟡 Inherits per-portal divergence |
| `pm_routing.py` | PM auto-routing alerts | 🟠 Inline plaintext |
| Various ad-hoc places | Magic links · notifications · etc. | 🔴 No shell at all |

Each one looks different. Each one feels different. Each one uses different CTA styles, different signature blocks, different urgency colors. Operators subconsciously distrust mail that doesn't look like the previous mail.

## The doctrine

**One shell. One typography. One CTA. One footer.** Only the body content changes per use case.

### What MUST be identical across every portal-generated email

| Element | Standard |
|---|---|
| Outer wrapper | `<div style="font-family:Helvetica,Arial,sans-serif;max-width:640px;margin:0 auto;color:#0f172a">` |
| Header band | `background:#4338ca` (indigo-700) · `padding:16px 22px` · `border-radius:6px 6px 0 0` |
| Header eyebrow | `font-family:Courier,monospace;font-size:11px;letter-spacing:0.18em;opacity:0.85` · text format `MASCI · <DOMAIN UPPERCASE>` |
| Header H1 | `font-size:22px;font-weight:900` · sentence case |
| Header timestamp | `font-size:11px;opacity:0.85` · ISO date + recipient role + name |
| Body container | white background · `border:1px solid #e5e7eb;border-top:none;padding:18px 22px;border-radius:0 0 6px 6px` |
| Body intro | `<p style="margin:0 0 14px;font-size:13px;color:#475569;line-height:1.5">` |
| KPI cards | 2-up table with eyebrow + big-number block · radii `4px 0 0 4px` left / `0 4px 4px 0` right |
| Section H2 | `font-size:13px;font-family:Courier,monospace;letter-spacing:0.18em;text-transform:uppercase` |
| Primary CTA button | `background:#4338ca;color:white;padding:10px 22px;border-radius:4px;font-weight:700;font-size:13px;letter-spacing:0.04em;text-transform:uppercase` |
| Footer | `font-size:11px;color:#94a3b8;line-height:1.5;border-top:1px solid #f1f5f9;padding-top:10px` |

### Severity palette (used in KPI cards and badges)

| Severity | Background | Border | Text | When |
|---|---|---|---|---|
| info | `#eef2ff` | `#c7d2fe` | `#3730a3` (indigo) | default / counts |
| pending | `#fef3c7` | `#fde68a` | `#92400e` (amber) | awaiting action |
| overdue | `#fee2e2` | `#fecaca` | `#991b1b` (red) | breach |
| neutral | `#f1f5f9` | `#e2e8f0` | `#0f172a` (slate) | totals |

These are the ONLY colors. No teal, no cyan, no pink — those introduce visual noise without communicating distinct severity.

### Urgency hierarchy in body language

| Level | Subject prefix | Body opener |
|---|---|---|
| Routine | `[MASCI] <Subject>` | `Here is …` / `Your weekly …` |
| Action needed | `[MASCI] Action needed — <Subject>` | `<N> items need your attention.` |
| Time-sensitive | `[MASCI] Action by <date> — <Subject>` | `Please act before <date>.` |
| Critical | `[MASCI · CRITICAL] <Subject>` | `Immediate action required.` |

No exclamation marks. No "URGENT!" bangs. No emoji. The visual band + the subject prefix are the urgency signal — the body remains calm.

### Signature block (immutable)

```
MASCI Operations Platform · <feature-name> · <cadence-phrase>
<one-line operational context — who acts on this and why>
```

Examples:

- `MASCI Operations Platform · Weekly Request PO Digest · Mondays.\nField Leadership submits the request; PM, Co-PMs, HR, and Admin issue the official PO.`
- `MASCI Operations Platform · Magic Link · Issued by Dispatch.\nThis link expires in 14 hours and can only be used once.`

No "Best regards" / "Sincerely" / signoffs. This is operational mail, not correspondence.

---

## Implementation contract

### Phase IV.B.1 · Extract the shell

Create `/app/backend/lib/email_shell.py` exporting:

```python
def render_email(
    *,
    domain_uppercase: str,           # e.g., "PO OPERATIONS"
    headline: str,                   # e.g., "Weekly Request PO Digest"
    timestamp_iso: str,
    recipient_label: str,            # e.g., "Project Manager: Jaymn Judd"
    intro_html: str,
    body_html: str,
    cta_label: Optional[str] = None,
    cta_url: Optional[str] = None,
    footer_signature: str,           # the immutable signature block
) -> str: ...
```

Internals are exactly the `_pm_digest_html` shell from `po_digest.py`, generalised. All 8 callers above migrate to this single function over the course of Phase IV.B.

### Phase IV.B.2 · Per-portal migration order

1. `lib/operator_digest.py` (1 caller)
2. `routes/safety_portal/digest.py` (1 caller)
3. `routes/safety_portal/auth_users.py` (2 callers · reset + invite)
4. `routes/payroll_variance.py` (1 caller)
5. `routes/admin_digest_config.py` (configurable)
6. `pm_routing.py` (alerts)
7. Magic-link / notification ad-hoc senders (audit and migrate)

Each migration is its own PR. Each PR includes:

- A side-by-side rendered comparison (before/after screenshot in `/app/memory/email_comparison_<caller>.png`)
- Subject-prefix conformance check
- Per-locale spot-check (EN baseline · ES if available)
- Regression test that asserts the rendered HTML contains the canonical shell sentinels (`MASCI · `, `#4338ca`, the footer signature)

### Phase IV.B.3 · Guards

- A pytest collector in `/app/backend/tests/test_email_shell_conformance.py` will inspect every `send_email_fn` caller and assert that the rendered HTML starts with the canonical wrapper and ends with the canonical footer. New senders that bypass the shell fail CI.
- Lint rule (custom): forbid inline `<table style="background:#"` outside `lib/email_shell.py`.

### What this doctrine does NOT touch

- Existing **scheduled** email senders keep their cron times.
- Recipient lists don't change.
- Subject lines stay backward-compatible during migration (prefix added, body unchanged).
- No email is delayed, dropped, or re-sent during the migration.

---

## Notification doctrine (in-app bell + push)

In-app notifications share the same urgency hierarchy:

| Severity | Bell badge color | Toast tone | Sound |
|---|---|---|---|
| info | slate dot | quiet slide-in · 4s | none |
| pending | amber dot | quiet slide-in · 6s | none |
| overdue | red dot | quiet slide-in · 8s | none |
| critical | red ring | sticky banner until dismissed | none |

No sounds. No animations beyond a 200ms slide. The signal is the color + position, not motion.

---

## Verdict

🟡 **DOCTRINE COMPLETE · CODE MIGRATION DEFERRED to Phase IV.B implementation iteration.**

Until the shell is extracted, every NEW email feature MUST be written using the standards above, even if a temporary inline copy of `_pm_digest_html` is included in the new file. No new divergence is permitted.
