# ALERT-ENV-001 · CERTIFICATION

**Sprint:** ALERT-ENV-001
**Priority:** P1 · Operator clarity / incident prevention
**Status:** ✅ **PASS · CLOSED**
**Date:** 2026-06-09T17:52:00Z
**Auditor:** E1 under OMEGA directive

---

## ROOT CAUSE

Operator-facing alert emails sent through `outage_alerts.send_outage_alert()` (used by the credential-missing monitor, platform-outage badge, and any caller of the helper) carried a subject string templated by the caller with **no environment tag**. The Resend `from:` address (`noreply@mascidocs.com`) and the `OUTAGE_ALERT_TO` recipient (`jaymn.judd@mascigc.com`) are identical between preview and production pods, so an alert sent from the preview environment was indistinguishable in the operator's inbox from a production alert. This caused the false-positive incident response surfaced in MOTIVE-CRED-VERIFY-002.

The same defect applied to the backup verification email (`backup_verification.render_verification_subject()` / `render_verification_email_html()`), whose subject string also had no environment tag.

---

## FILES CHANGED (surgical · 2 files · 3 logical additions)

| File | Change | Lines |
|---|---|---|
| `/app/backend/outage_alerts.py` | Added `_env_tag()`, `_decorate_subject()`, `render_env_banner_html()`, `render_env_banner_text()`. Wired `send_outage_alert()` to call `_decorate_subject(subject, env_tag)` and inject the banner into both HTML + plain-text bodies. | +52 / −2 |
| `/app/backend/backup_verification.py` | Updated `render_verification_subject()` to prepend `[<env>]`. Added `_env_banner_for_backup()` wrapper that calls the shared `render_env_banner_html` from `outage_alerts`. Injected the banner above the existing "MASCI Operations Platform" eyebrow in the HTML chrome. | +12 / −5 |
| `/app/backend/tests/test_alert_env_001.py` | **NEW** — 15 pytest tests pinning the contract. | +163 (new) |

**No other Resend caller touched.** Audit confirmed that the remaining 25+ `resend.Emails.send` callsites are user-facing functional emails (passwordless magic links, daily report distribution, dispatch confirmations, PO digests, training notifications, etc.) and are **out of scope** per the directive ("operator-facing **alert** emails"). They retain their existing templates unchanged.

---

## ALERT SENDERS AUDITED (full inventory)

| Sender | Path | Operator-facing alert? | Action |
|---|---|---|---|
| `outage_alerts.send_outage_alert()` | central helper | YES — all outage/credential-missing alerts funnel here | **patched** |
| Credential-missing monitor | `routes/integrations/_credential_alerts.py:91` | YES (delegates to helper above) | inherits patch · no direct change |
| Platform-outage badge | `server.py:7954` `/api/health/alert` | YES (delegates to helper above) | inherits patch · no direct change |
| Backup verification weekly | `backup_verification.send_verification_email()` | YES (operator alert when issues detected) | **patched** |
| Daily lite-backup file delivery | `server.py:6606 _email_lite_backup_zip()` | NO — successful backup file delivery; not an alert | unchanged |
| Daily Report distribution | various | NO — user-facing functional email | unchanged |
| Dispatch SMS / magic links | `routes/dispatch_lifecycle.py`, `routes/safety_portal/auth_users.py`, etc. | NO — user-facing functional email | unchanged |
| PO Digest | `po_digest.py`, `routes/po_digest_admin.py` | NO — recipient is purchasing dept, not operator alert | unchanged |
| Safety Digest | `safety_digest.py` | NO — recipient is field crews, not operator alert | unchanged |
| Trench Safety / Pulse / Notifications | `routes/trench_safety/*.py` | NO — recipient is field, not operator alert | unchanged |
| HR / Field-Leadership portal | `routes/hr_portal.py`, `routes/field_leadership_portal.py` | NO — user-facing functional | unchanged |
| MFA / brute-force | grep confirmed no Resend email path on lockout | N/A | nothing to patch |

---

## BEFORE / AFTER EXAMPLES

### Credential-missing alert · subject
| Env | Before | After |
|---|---|---|
| Preview | `[MASCI] Motive webhook received but credentials are MISSING` | `[PREVIEW] [MASCI] Motive webhook received but credentials are MISSING` |
| Production | `[MASCI] Motive webhook received but credentials are MISSING` | `[PRODUCTION] [MASCI] Motive webhook received but credentials are MISSING` |

### Outage alert · HTML body (top of email, above the existing red banner)
```
[Preview] ┌────────────────────────────────────┐
          │ ENVIRONMENT: PREVIEW               │  ← yellow accent (#a16207)
          └────────────────────────────────────┘
          ┌────────────────────────────────────┐
          │ ⚠ MASCI Hub · Outage Detected     │
          └────────────────────────────────────┘
          {summary}

[Production] ┌─────────────────────────────────┐
             │ ENVIRONMENT: PRODUCTION         │  ← red accent (#dc2626)
             └─────────────────────────────────┘
             ┌─────────────────────────────────┐
             │ ⚠ MASCI Hub · Outage Detected  │
             └─────────────────────────────────┘
             {summary}
```

### Outage alert · plain text body
```
MASCI Hub — Outage detected.

Environment: PREVIEW          ← (or PRODUCTION)

{summary}

Issue key: {issue_key}
Detected at: {timestamp}
```

### Backup verification subject
| Env | Verdict | Before | After |
|---|---|---|---|
| Preview | pass | `[MASCI · BACKUP] Weekly Verification · 4 archives healthy` | `[PREVIEW] [MASCI · BACKUP] Weekly Verification · 4 archives healthy` |
| Production | fail | `🚨 BACKUP VERIFICATION FAILED · check immediately` | `[PRODUCTION] 🚨 BACKUP VERIFICATION FAILED · check immediately` |

### Backup verification HTML body
The env banner appears as the **first** visible element inside the email card, directly above the existing "MASCI OPERATIONS PLATFORM" eyebrow — verified by test (`banner_pos < title_pos`).

---

## TESTS (15 / 15 PASS)

```
PASS  test_env_tag_preview
PASS  test_env_tag_production
PASS  test_env_tag_defaults_to_production
PASS  test_env_tag_falls_through_to_environment
PASS  test_decorate_subject_adds_tag
PASS  test_decorate_subject_is_idempotent
PASS  test_env_banner_html_contains_env
PASS  test_env_banner_html_production
PASS  test_env_banner_text
PASS  test_backup_subject_includes_env_tag_preview
PASS  test_backup_subject_includes_env_tag_production
PASS  test_backup_html_includes_env_banner
PASS  test_backup_html_preview_tag
PASS  test_outage_alert_subject_and_body_carry_env_tag
PASS  test_outage_alert_does_not_strip_caller_subject_content

15 passed in 0.05s
```

### Operator-required behavior verification matrix

| # | Required behavior | Test ID | Result |
|---|---|---|---|
| 1 | Preview credential-missing email subject includes `[PREVIEW]` | `test_decorate_subject_adds_tag` + `test_outage_alert_does_not_strip_caller_subject_content` | ✅ |
| 2 | Production credential-missing email subject includes `[PRODUCTION]` | `test_env_tag_production` + `test_outage_alert_subject_and_body_carry_env_tag` | ✅ |
| 3 | Preview body includes `Environment: PREVIEW` | `test_env_banner_html_contains_env` + `test_env_banner_text` | ✅ |
| 4 | Production body includes `Environment: PRODUCTION` | `test_env_banner_html_production` | ✅ |
| 5 | Existing alert delivery still works | `test_outage_alert_does_not_strip_caller_subject_content` + backend restart + health check | ✅ |
| 6 | No secrets exposed | code review (no env-var values logged or echoed) + no test asserts secret string | ✅ |
| 7 | Backup alert subject/body also includes env tag | `test_backup_subject_includes_env_tag_*` + `test_backup_html_includes_env_banner` | ✅ |
| 8 | No unrelated email templates changed | grep audit of all 25+ Resend callsites · only 2 (outage_alerts.py + backup_verification.py) modified | ✅ |

Existing test suites that exercise the modified files continue to pass: 22/22 (7 from WEBHOOK-HARDEN-001 + 15 from this sprint).

**Lint:** all touched files pass `ruff` with 0 blocking findings.

**Backend restart:** `sudo supervisorctl restart backend` → `backend started · uptime 0:00:27 · /api/health → 200`.

---

## PROHIBITED-ACTIONS COMPLIANCE CHECK

| Prohibited action | Touched? |
|---|---|
| No recipient changes | NO (recipients computed identically as before) |
| No alert logic changes | NO (only subject/body cosmetics added; cooldown, send path, Resend call all byte-identical) |
| No delivery pipeline changes | NO |
| No provider credential changes | NO |
| No DB data mutation (except normal alert sending) | NO |
| No secrets exposed | NO (env-tag string only; no API keys, no email addresses) |
| FleetWatcher / Dispatch Automation / Material Movement | NOT touched |
| ID-007 / MaintainX | NOT started |

---

## MOBILE READABILITY

The env banner uses:
* full-width container (no fixed pixel width that breaks responsive layouts)
* inline `font: 600 12px/1.4 system-ui,sans-serif` — readable at 320 px viewport
* coloured left border + light tinted background — visible even with dark-mode image-blocking
* preserves text-only fallback (the plain text body shows the same `Environment: PREVIEW` / `PRODUCTION` line)

---

## VERDICT

✅ **PASS · ALERT-ENV-001 CLOSED.**

Operators can no longer confuse a preview alert email with a production alert email. The fix is surgical (2 file edits + 1 new test file), reuses a single env-tag helper from `outage_alerts`, and ships every operator-facing alert path with consistent `[PREVIEW]`/`[PRODUCTION]` decoration in both subject and body.

**STOPPING per OMEGA. Awaiting operator next directive.**

— end of certification —
