# Email Template Inventory
**Mode:** READ-ONLY. Zero code changes.
**Format:** Each row = one canonical email. Trigger · Recipients · Subject · Template / Renderer · Active?

---

## A · Auto-Email per Record (PDF attached)
Routed through `schedule_auto_email(kind, record)` → `_dispatch_auto_email` → `pdf_render.build_email_subject` + `render_record_pdf` + Resend.

| # | Kind | Trigger | Recipients | Subject pattern | Template / renderer | Active |
|---|---|---|---|---|---|---|
| A1 | `inspection` | `POST /api/safety/inspections` (`routes/safety.py:318`) | PM-of-record + always-CC list (`recipients_for_record_async`) | `[MASCI · INSP] {project} · {project_number} · {short_title} · {doc_id}` | `pdf_render.render_record_pdf("inspection",…)` HTML→PDF | ✅ (gated by `RESEND_API_KEY` + `AUTO_EMAIL_REPORTS=true`) |
| A2 | `meeting` | `POST /api/safety/meetings` (`routes/safety.py:464`) | same | `[MASCI · SAFETY] …` | same | ✅ |
| A3 | `jha` | `POST /api/safety/jhas` (`routes/safety.py:553`) | same | `[MASCI · JHA] …` | same | ✅ |
| A4 | `incident` | `POST /api/safety/incidents` (`routes/safety.py:649`) | PM + always-CC + (when severe) `severe_incident_cc` | `[MASCI · INC] …` | same | ✅ |
| A5 | `daily-report` | `POST /api/daily-reports` (`routes/daily_reports.py:271`) | PM + always-CC | `[MASCI · DAILY] …` | same | ✅ |
| A6 | `equipment-inspection` | `POST /api/equipment/inspections` (`routes/equipment.py:199`) | **Shop Manager(s) only** (hard override at `server.py:11266-11295`); fallback `SHOP_MANAGER_EMAIL` | `[MASCI · EQUIP] …` (with `equipment_fail=True` decoration if FAIL) | same | ✅ |
| A7 | `qaqc` / `qaqc-inspection` | `POST /api/qaqc` (`routes/qaqc.py:210`) | PM + always-CC | `[MASCI · QA/QC] …` | same | ✅ |

## B · Safety-Office Forms
Routed through `build_email_subject_for_kind` in `pdf_render.py`.

| # | Kind | Trigger | Recipients | Subject pattern | Renderer | Active |
|---|---|---|---|---|---|---|
| B1 | `issuance` | `routes/safety_forms.py:752` | employee + safety + always-CC | `[MASCI · ISSUANCE] …` | `routes/safety_forms.py` HTML builder | ✅ |
| B2 | `return` | `routes/safety_forms.py:766` | same | `[MASCI · RETURN] …` | same | ✅ |
| B3 | `training` | `routes/safety_forms.py:785` | employee + safety | `[MASCI · TRAINING] …` | same | ✅ |

## C · Field-Leadership Records
Routed through `routes/field_leadership.py:748` `build_email_subject_for_kind` calls.

| # | Kind | Trigger | Recipients | Subject pattern | Active |
|---|---|---|---|---|---|
| C1 | `write_up` | FL form submit | employee + supervisor + safety | `[MASCI · LEADERSHIP] …` | ✅ |
| C2 | `verbal_coaching` | FL form submit | same | `[MASCI · LEADERSHIP] …` | ✅ |
| C3 | `attendance` | FL form submit | same | `[MASCI · LEADERSHIP] …` | ✅ |
| C4 | `recognition` | FL form submit | employee + supervisor | `[MASCI · LEADERSHIP] …` | ✅ |
| C5 | `equipment_checkout` | FL form submit | employee + shop | `[MASCI · LEADERSHIP] …` | ✅ |
| C6 | `new_employee_eval` | FL form submit | HR + supervisor | `[MASCI · LEADERSHIP] …` | ✅ |
| C7 | `crew_eval` | FL form submit | supervisor + leadership | `[MASCI · LEADERSHIP] …` | ✅ |
| C8 | `promotion_recommendation` | FL form submit | HR + leadership | `[MASCI · LEADERSHIP] …` | ✅ |
| C9 | `training_deficiency` | FL form submit | safety + leadership | `[MASCI · LEADERSHIP] …` | ✅ |
| C10 | `supervisor_notes` | FL form submit | supervisor + leadership | `[MASCI · LEADERSHIP] …` | ✅ |
| C11 | `employee_termination` | FL termination | HR + admin | `[MASCI · TERMINATION] …` | ✅ |
| C12 | `time_off_request` (status change) | `routes/field_leadership.py:1401` | employee + supervisor | `[MASCI] {DRAFT?}Time Off Request {status} — {employee_name}` | ✅ |
| C13 | `time_off_request` (please complete) | `routes/field_leadership.py:1453` | employee | `[MASCI] Time Off Request — please complete` | ✅ |

## D · Lifecycle revision / reopen
Async via `fsi_send_email`.

| # | Event | Trigger | Recipients | Subject | Renderer | Active |
|---|---|---|---|---|---|---|
| D1 | Daily-report revision requested | `routes/daily_report_lifecycle.py:181` | submitter (FSI-resolved) | `[MASCI] Daily Report revision needed — {project_label}` | `daily_report_lifecycle._render_revision_html` | ✅ |
| D2 | Incident reopened | `routes/incident_lifecycle.py:169` | submitter | `[MASCI] Incident reopened — {project_label}` | `incident_lifecycle._render_html` | ✅ |
| D3 | Incident corrective action requested | `routes/incident_lifecycle.py:172` | submitter | `[MASCI] Incident corrective action requested — {project_label}` | same | ✅ |

## E · Portal Account / Password Reset
| # | Portal | Trigger | Recipient | Subject | Renderer | Active |
|---|---|---|---|---|---|---|
| E1 | Safety Portal — password reset link | `routes/safety_portal/auth_users.py:166` | user | `MASCI Safety Portal — Reset password` | inline HTML | ✅ |
| E2 | Safety Portal — temp password invite | `routes/safety_portal/auth_users.py:230` | user | `[MASCI] Your Safety Portal account — temporary password inside` | inline HTML | ✅ |
| E3 | PM Portal — reset | `routes/pm_routes.py:531` | user | `[MASCI] Reset your PM Portal password` | inline HTML | ✅ |
| E4 | Shop Portal — reset | `server.py:2024` | user | `[MASCI] Reset your Shop Portal password` | inline HTML | ✅ |
| E5 | HR Portal — reset | `routes/hr_portal.py:252` | user | `[MASCI] Reset your HR Portal password` | inline HTML | ✅ |
| E6 | HR Portal — new account | `routes/hr_portal.py:1441` | user | `[MASCI] Your HR Portal account — temporary password inside` | inline HTML | ✅ |
| E7 | Field Leadership Portal — reset | `routes/field_leadership_portal.py:320` | user | `[MASCI] Reset your Field Leadership Portal password` | inline HTML | ✅ |
| E8 | Field Leadership Portal — new account | `routes/field_leadership_portal.py:774` | user | `[MASCI] Your Field Leadership Portal account — temporary password inside` | inline HTML | ✅ |

## F · Access / Auth Directory
| # | Event | Trigger | Recipient | Subject | Active |
|---|---|---|---|---|---|
| F1 | Access account created / role changed | `routes/auth_directory_routes.py:164` | user | `[MASCI] Your access account — {action} (temporary password inside)` | ✅ |
| F2 | Privileged access change notice | `routes/pm_admin.py:347` | admin | `[MASCI · ACCESS] {headline}` | ✅ |

## G · Mentions / Tagging
| # | Event | Trigger | Recipient | Subject | Active |
|---|---|---|---|---|---|
| G1 | User mention in a target (Phase 4 collab) | `phase4.py:147` | mentioned user | `You were mentioned — {target_label[:60]}` | ✅ |

## H · Operational broadcasts
| # | Event | Trigger | Recipients | Subject | Active |
|---|---|---|---|---|---|
| H1 | Parts request created/updated | `routes/shop_parts.py:326` | shop + PM | `[MASCI · PARTS] {unit_number} · …` | ✅ |
| H2 | Photo bundle email | `routes/job_photos.py:1066` | recipients in payload | `MASCI Photos — {N} photo(s)` (or operator-supplied subject) | ✅ (gated) |
| H3 | Dispatch auto-email | `server.py:11410` (`schedule_auto_email`) | per-record | uses `build_email_subject(kind, record)` | ✅ |
| H4 | Operational Daily Record (ODR) | `routes/odr/pdf.py:647` | per-record | `Operational Daily Record` | ✅ |
| H5 | Headline email broadcast | `server.py:3162` | admin-defined | `[MASCI] {headline}` | ✅ |

## I · Weekly Digests
| # | Stream | Cron | Recipients | Subject | Renderer | Active |
|---|---|---|---|---|---|---|
| I1 | Safety Digest | Mon 14:00 UTC (`server.py:10092`) | `SAFETY_DIGEST_TO_EMAIL` or routing key | `[MASCI] Weekly Safety Digest` | `safety_digest.render_digest_html` | ✅ |
| I2 | Operator Digest | Mon 14:00 UTC (`server.py:10119`) | `OPERATOR_DIGEST_RECIPIENTS` → fallback Safety list | `[MASCI] Weekly Operations Digest` | `lib/operator_digest.render` | ✅ |
| I3 | PO Request Digest | Mon 14:00 UTC (`server.py:10191`) | every active PM (scoped) + every active HR user | `po_digest.build_digest_subject()` (project-scoped) | `po_digest._build_digest_html` | ✅ |
| I4 | Safety Portal Digest (manual / scheduled) | `routes/safety_portal/digest.py:164` | per-portal routing | `[MASCI] Weekly Safety Digest` | shared with I1 | ✅ |
| I5 | Admin Safety Digest manual | `routes/admin_digest_config.py:112` (gated by `AUTO_EMAIL_REPORTS`) | recipients in payload | `[MASCI] Weekly Safety Digest (manual)` | shared | ✅ |

## J · Admin alarms (system health)
| # | Event | Trigger | Recipients | Subject | Active |
|---|---|---|---|---|---|
| J1 | Health failure | `health_monitor.py:109` (RED) | `BACKUP_EMAIL_TO` | `🚨 HEALTH FAIL · {n} subsystem(s)` | ✅ |
| J2 | Health summary OK/Yellow | `health_monitor.py:111` | same | `[MASCI · HEALTH] System Health {STATE} · …` | ✅ |
| J3 | Backup weekly verification | `backup_verification.py:309` | `BACKUP_VERIFICATION_TO` → fallback | `[MASCI · BACKUP] Weekly Verification · {n} archives healthy` | ✅ |
| J4 | Backup silent alarm | `server.py:5812` | `BACKUP_EMAIL_TO` | `[MASCI ALARM] Backup silent for {h}h — action needed` | ✅ |
| J5 | Platform outage | `outage_alerts.py` → `server.py:7879` | `OUTAGE_ALERT_TO` | `🚨 PLATFORM OUTAGE · {issue_key}` (15-min cooldown per key) | ✅ |

---

## Gating summary
Every email path checks two flags before contacting Resend:
- `RESEND_API_KEY` present and non-empty.
- `AUTO_EMAIL_REPORTS in {"true","1","yes"}` (case-insensitive).
When either is missing, the wrapper logs a `[xxx-stub]` or `[xxx-preview]` line and returns False. **Preview environment currently has `AUTO_EMAIL_REPORTS=false`**, so all sends log-only.

No template files (Jinja / etc.) — every HTML body is built inline or in a per-module renderer. PDF attachments are rendered via `pdf_render.render_record_pdf`.
