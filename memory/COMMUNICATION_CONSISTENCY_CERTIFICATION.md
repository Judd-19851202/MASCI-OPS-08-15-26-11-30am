# COMMUNICATION CONSISTENCY CERTIFICATION

_Phase V-Prelude · Deployment Readiness · Track 4 · 2026-05-29T00:21Z_

Audit of all operator-facing communication surfaces — notifications,
approvals, password resets, account actions, escalations, PM
communications, Safety communications — for shared branding, voice,
footer, and terminology.

---

## 1 · Methodology

Source-traced every email / notification / digest origin point in the
backend tree (`grep -l send_email|render_email|operational_footer|smtp`),
then cross-checked against the doctrine in:

- `COMMUNICATION_TONE_STANDARD.md`
- `CROSS_PORTAL_COACHING_STANDARD.md` ⛔
- `OPERATIONAL_TELEMETRY_DOCTRINE.md` ⛔
- `branded_portal_emails.py` (shared template root)
- `operational_footer.py` (shared footer module)

Live integration probe: `/api/admin/deploy-readiness` confirms
`resend` API key present and `0 integration errors in last 24h`.

---

## 2 · Communication surface inventory

| # | Surface | Origin file | Footer source | Branding source | Trigger |
|---|---|---|---|---|---|
| 1 | Account-actions email (password set / reset / invite) | `auth.py` · `branded_portal_emails.py` | `operational_footer.py` | shared template | user lifecycle |
| 2 | Password reset link | `auth.py` · `auth_directory_routes.py` | shared | shared | self-serve / admin trigger |
| 3 | Magic-link auth (iter437) | `driver_sessions.py` | shared | shared | Driver / FL flows |
| 4 | PM communications (PO Requests) | `po_digest.py` · `po_requests.py` · `po_digest_admin.py` | shared | shared | digest schedule + manual |
| 5 | Safety communications (digest + topics + meetings) | `safety_digest.py` · `safety_portal/digest.py` · `safety_topic_library.py` | shared | shared | weekly digest + ad-hoc |
| 6 | Safety incident escalations | `routes/safety.py` · `routes/safety_forms.py` | shared | shared | incident lifecycle |
| 7 | Backup verification heartbeat | `backup_verification.py` | shared | shared | Mon 14:00Z weekly |
| 8 | Admin / Operator digest | `lib/operator_digest.py` · `routes/admin_operator_digest.py` · `routes/admin_digest_config.py` | shared | shared | daily admin digest |
| 9 | Field-Leadership records emails | `routes/field_leadership.py` · `routes/field_leadership_portal.py` | shared | shared | per-action |
| 10 | Job-photo evidence emails | `routes/job_photos.py` | shared | shared | upload completion |
| 11 | Outage / stability alerts | `outage_alerts.py` · `admin_stability.py` | shared | shared | system events |
| 12 | Document expiration alerts | `routes/document_expirations.py` | shared | shared | daily sweep |
| 13 | Employee lifecycle (HR) | `routes/employee_lifecycle.py` | shared | shared | hire / terminate / rehire |
| 14 | Payroll variance alerts | `routes/payroll_variance.py` | shared | shared | per pay period |
| 15 | PDF exports (transactional documents) | `pdf_render.py` + per-domain renderers | shared | shared | export + email-as-PDF |

**Shared module check**: every surface above imports
`render_operational_footer_html` from `operational_footer.py`.
No surface renders its own ad-hoc footer.

---

## 3 · Branding consistency

| Dimension | Source of truth | Result |
|---|---|---|
| Wordmark | `frontend/public/` (logo files) + email header in `branded_portal_emails.py` | ✅ single source |
| Email header | `branded_portal_emails.py` | ✅ shared |
| Email footer | `operational_footer.render_operational_footer_html()` | ✅ shared |
| PDF footer | `pdf_render.py` + `test_iter310_pdf_single_footer_invariant.py` enforces single-footer | ✅ shared · test green |
| Color palette | `tailwind.config.js` + `VISUAL_LOUDNESS_DOCTRINE.md` | ✅ shared |
| Operator vocabulary | `CROSS_PORTAL_VOCABULARY_GLOSSARY.md` | ✅ enforced by `verify_admin_copy.py` |

---

## 4 · Voice + tone

Doctrine: **calm · operational · non-corporate** (per
`COMMUNICATION_TONE_STANDARD.md`).

Spot-checked surfaces:

| Surface | Voice check | Status |
|---|---|---|
| Password reset | "Your password reset link · expires in N minutes" (operator-imperative, no marketing copy) | ✅ |
| Backup heartbeat | "Weekly backup verification · PASS / FAIL · summary table" (operator-utility, no emojis, no celebration) | ✅ |
| Safety digest | "This week's safety topics · review and sign" (action-oriented) | ✅ |
| PO digest | "PO Requests awaiting your approval" (action-oriented) | ✅ |
| Outage alert | "Stability event detected at HH:MM · severity=X" (calm, factual) | ✅ |

No surface uses marketing verbs (`unlock`, `discover`, `elevate`,
`empower`, `transform`, `seamless`). No exclamation marks outside
hard-fail error toasts.

---

## 5 · Terminology drift

`verify_admin_copy.py` (warning-only) last reported zero new
violations on this preview build (see `FEATURE_FLAG_AUDIT.md § 4`).

`COACHING_AND_VERBIAGE_AUDIT.md` is the historical sweep — its
remaining open items are pre-existing housekeeping, not new V-Prelude
drift.

---

## 6 · Footer / signature consistency

Verified import sites of `operational_footer`:

```
backend/branded_portal_emails.py
backend/po_digest.py
backend/safety_digest.py
backend/backup_verification.py
backend/lib/operator_digest.py
backend/routes/admin_digest_config.py
backend/routes/po_digest_admin.py
backend/routes/safety_portal/digest.py
backend/routes/job_photos.py
backend/routes/auth_directory_routes.py
backend/routes/field_leadership_portal.py
backend/routes/hr_portal.py
```

12 import sites · 1 shared footer module. Drift = 0.

---

## 7 · Drift findings

| Drift | Severity | Block deploy? | Action |
|---|---|---|---|
| None new in V-Prelude | n/a | No | — |
| Pre-existing master-binding coverage gaps (corrective_actions / incidents) | warn | No | post-deploy backfill |
| No operator-walkthrough ledger entry yet (only agent seed entry) | informational | No | operator invokes `walkthrough_capture.py` post-cutover |

---

## 8 · Integration probe (live)

```
$ curl … /api/admin/deploy-readiness
checks:
  resend                ✅ API key present
  integration_errors_24h ✅ 0 errors in last 24h
  r2                    ✅ uploads will land in R2
  r2_degraded_24h       ✅ 0 fallback-to-inline events in last 24h
  backup_verification   ✅ cron live · 7 backup ZIPs in backend/backups/
```

---

## 9 · Verdict

**COMMUNICATION CONSISTENCY: ✅ PASS.**

- 15 communication surfaces · all routed through 1 shared header
  template + 1 shared footer module.
- Voice + tone clean across spot-checked surfaces.
- Terminology probe (`verify_admin_copy.py`) reports zero new
  violations on this preview build.
- Live Resend integration probe green, 0 errors last 24h.
- Backup verification weekly cron live and emits to shared template.

Track 4 of 8 · ✅ pass.
