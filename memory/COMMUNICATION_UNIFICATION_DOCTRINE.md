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


---

# Addendum · iter437 / Phase IV-BETA.3 (2026-02-27)

*Owner: platform governance · scope: subject-line + body + footer contract*
*Status: 🟡 DOCTRINE PUBLISHED · template alignment NOT YET implemented*
*This addendum extends the original doctrine above with operator-grade
subject-line rules and a per-site drift inventory. It does NOT supersede
the visual shell doctrine — it complements it.*

## Verification legend used in this addendum

🟢 **VERIFIED** — measured in the live preview / asserted by a passing test.
🟡 **ASSUMED** — backed by code reading but not exercised end-to-end this pass.
⚪ **UNTESTED** — proposed standard, no current code uses it yet.

## A.I · Gold-standard subject-line contract (🟢 VERIFIED for PM auto-emails)

The PM auto-email subject builder (`pdf_render.py::build_email_subject`,
iter238) is the canonical pattern. Every other portal's outbound mail
should eventually compose subjects via this builder.

```
[MASCI · {TAG}] {project_label} · {project_number} · {short_title} · {doc_id}
```

| Token | Source | Rule |
|---|---|---|
| `MASCI` | brand constant | Brand only. Never product-name flavours ("Hub", "Safety Hub", …) |
| `TAG` | `SUBJECT_TYPE_TAGS[kind]` | Uppercase. Concrete operational kind ("SAFETY", "JHA", "INCIDENT", "PARTS", "RESET", "DIGEST"). Never "Update", "FYI", "Notice". |
| `project_label` | trimmed `project_name` → ≤ 32 chars or trailing segment | If multi-site: keep the trailing segment (the operator's site identity). |
| `project_number` | record's `project_number` | Bare. No "Job#", no "Project:". |
| `short_title` | `SHORT_KIND_TITLES[kind]` | ≤ 18 chars. Sentence-cased operational noun. |
| `doc_id` | record's `doc_id` | Inbox-Cmd-F target. Include whenever available. |

### Reserved attention-grabbing prefixes (🟢 VERIFIED · iter238)

| Condition | Prefix | When |
|---|---|---|
| Severe incident | `🚨 SEVERE INCIDENT` | Only for `kind=incident` with severity=severe |
| Equipment fail | `⚠ EQUIPMENT FAIL` | Only for pre-op/post-op records with at least one failed check |

**No other emoji in subject lines.** Confetti, hourglasses, green-check
marks etc. are forbidden — they patronise the operator and corrupt
mobile preview alignment.

## A.II · Body tone contract (🟡 ASSUMED today · proposed standard)

Operational emails answer three questions in this order:

1. **What happened?** — one sentence, past tense, neutral
2. **What do I need to do?** — verb-first list or single CTA
3. **Where do I do it?** — one deep link, never a homepage

### Forbidden in body copy

- Welcomes / greetings ("Hi there", "Hey team", "Hope you're well")
- Emoji "tone" punctuation (🎉 😎 ✨ 🚀)
- Marketing connectives ("Just a heads up", "Quick FYI")
- Apologies ("Sorry to bother you")
- Soft requests ("If you have a moment", "Whenever you get a chance")
- "Don't hesitate to reach out" / "Feel free to" / "We're here to help"
- "AI-powered", "seamless", "effortless", "intuitive"
- Exclamation marks anywhere except severe-incident escalations

### Required in body copy

- First word is a verb when an action is expected
  (`Review`, `Approve`, `Reject`, `Sign`, `Replace`, `Acknowledge`).
- One CTA per email; if two are needed, one **primary** + one **secondary**.
- Timestamps in operator-local time with timezone suffix
  (`2026-02-27 06:14 CST`). Never "today at 2pm" alone.
- Job number visible in the first paragraph, not buried.

### CTA contract

| Component | Rule |
|---|---|
| Button label | One verb-noun. ≤ 3 words. Sentence case. (`Review report`) |
| Button URL | Deep-link to the exact record. Never a portal home. |
| Secondary link | Plain underlined link, same verb form (`Open record · DR-2026-0418`) |
| Fallback URL | Always include the raw URL below the button. |

## A.III · Urgency vocabulary (⚪ UNTESTED · proposed standard)

Three urgency tiers, three only. Mixing dilutes the signal.

| Tier | Subject prefix | Body opener | When | Example |
|---|---|---|---|---|
| **Routine** | none (`[MASCI · TAG]`) | `Record submitted · DR-2026-0418 at 06:14 CST.` | Normal operations | Daily report, parts order ack, digest |
| **Action required** | none (TAG carries the meaning) | `Action required · approve PO-2026-0073 by 17:00 CST today.` | Specific operator owes specific action by specific deadline | PO approval, signature pending, expiring cert |
| **Severe / immediate** | `🚨 SEVERE INCIDENT` / `⚠ EQUIPMENT FAIL` | `Immediate action · {what} · {who} · {by when}.` | Safety- or operationally-critical | Severe incident, equipment fail, outage alert |

**Banned urgency words:** `URGENT`, `IMPORTANT`, `Critical` (unless paired
with `incident`), `Please`, `Kindly`, `ASAP`, `As soon as possible`,
`Time-sensitive`, `Heads up`. These either patronise (`Please`, `Kindly`)
or shout without signal.

## A.IV · Footer contract (⚪ UNTESTED · proposed standard)

Every email ends with the same 3-line footer. No exceptions.

```
—
MASCI · automated · do-not-reply
{portal-name} · {doc-id-or-record-link}
```

- **Line 1**: em-dash separator only. No "Best regards", "Cheers",
  "Thanks!". No spoofed human signatures.
- **Line 2**: `MASCI · automated · do-not-reply` — ends the illusion
  of a human author.
- **Line 3**: portal context + inbox-Cmd-F target.

Transactional emails carry no unsubscribe link (they are operationally
required, not marketing). Digest and notification emails MAY include an
unsubscribe link **only** if the underlying preference is genuinely
user-controlled.

## A.V · Inventory of system-generated communications (🟢 VERIFIED · grep audit)

| File · Line | Surface | Subject style today | Status |
|---|---|---|---|
| `pdf_render.py:701-810` | PM auto-emails (forms, reports, incidents, JHAs, trench boxes) | 🟢 Gold standard `[MASCI · TAG] · …` | ✅ Compliant |
| `pdf_render.py::render_email_html:1419+` | PM auto-email body | n/a · structured, no greetings | ✅ Compliant |
| `routes/safety_forms.py:798` | Safety form submission emails | 🟡 Inherits gold standard via `build_email_subject` | ✅ Compliant by composition |
| `routes/shop_parts.py:323` | Parts orders | 🟡 `[MASCI] Parts Order · {unit} · {count} item(s)` — **missing the TAG segment** (`[MASCI · PARTS]`) | ⚠ Subject drift |
| `routes/pm_admin.py:333` | PM admin notifications | 🟡 `[MASCI] {headline}` — **no TAG, no project, no number** | ⚠ Subject drift |
| `routes/pm_routes.py:531` | PM password reset | `[MASCI] Reset your PM Portal password` (no project context exists) | ✅ Compliant for account email |
| `server.py:2059` | Shop password reset | `[MASCI] Reset your Shop Portal password` | ✅ Compliant for account email |
| `po_digest.py:321` | PO/cost digest | 🟡 Single constant `DIGEST_SUBJECT` — needs date / portal context | ⚠ Subject drift |
| `outage_alerts.py:115` | Outage alerts (Sentry-driven) | 🟡 Custom subject | ⚠ Needs A.III.severe-tier check |
| `health_monitor.py:113` | Backend health alerts | 🟡 Custom subject | ⚠ Needs A.III.severe-tier check |
| `backup_verification.py:498` | Backup verification reports | 🟡 `render_verification_subject` — structured | ⚠ Needs subject contract conformance |

### Drift summary

5 of 11 sites already conform via composition with `build_email_subject`.
6 sites have at least one subject-style drift this addendum identifies
but **does not change yet** (per operator directive: "Do not rewrite
notification engine yet · Pure template/tone alignment only where safe").

## A.VI · What changed in code this iteration

**Nothing.** This addendum is the alignment artifact. Implementation is
intentionally deferred to a future IV-BETA.3-impl iteration so each
drift site can be remediated with a focused test.

## A.VII · Roll-out plan for IV-BETA.3-impl (⚪ UNTESTED · plan only)

When authorised, change order:

1. **Parts order subject** (`routes/shop_parts.py:323`) — add `· TAG`
   segment → `[MASCI · PARTS] · {project} · {project_number} · …`.
2. **PM admin notifications** (`routes/pm_admin.py:333`) — route
   through `build_email_subject` with `kind="pm_admin"` + new
   `SHORT_KIND_TITLES["pm_admin"]` entry.
3. **PO digest** (`po_digest.py:321`) — replace `DIGEST_SUBJECT`
   constant with a builder that injects digest date + portal.
4. **Outage / health alerts** — formalise the `🚨` prefix gate via
   A.III.severe-tier; eliminate false-positives on routine warnings.
5. **Backup verification** — verify subject already conforms or adjust
   `render_verification_subject`.
6. **Footer rollout** — add `MASCI · automated · do-not-reply` footer
   to `render_email_html` first; propagate to non-PM emails after.

Each step ships as a separate PR with a focused unit test extending
`tests/test_iter238_email_uniformity.py` to lock the new conformance.

## A.VIII · Regression coverage (🟢 VERIFIED · today)

`tests/test_iter238_email_uniformity.py` already locks the PM
auto-email subject contract from A.I. Any IV-BETA.3-impl change above
must **extend** that file (not replace) so the existing contract stays
intact while new sites are folded in.

## A.IX · Constraints reaffirmed

- ✅ No backend rewrite this iteration
- ✅ No production touches
- ✅ No new email integration; existing send-paths untouched
- ✅ Doctrine is a governance artifact, not a behaviour change
- ✅ Subject-line patterns for severe / equipment-fail prefixes
  remain exactly as iter238 defined them

