# WP18CY Daily Report Email Root Cause

## Reported Symptom
Daily Report submission produced an email, but the email used generic operational-event wording, exposed internal control-plane terms, and omitted the dedicated Daily Report PDF package.

## First Proven Divergence
The first divergence occurred **after report persistence and OPPC event emission, before canonical Daily Report auto-email dispatch**.

## Proven Path
1. `routes/daily_reports.py` persisted the report and created an OPPC event.
2. `services/operations_control/control_plane.py` created an email communication for `oppc.daily_report.submitted.v1`.
3. That transport rendered a generic operational HTML body and sent it immediately.
4. `routes/daily_reports.py` then set `email_dispatch_suppressed=True` when OPPC communication existed.
5. Result: the canonical Daily Report dispatcher in `server.py::_dispatch_auto_email` never became the recipient-facing email path for this flow.

## Why the Visible Symptom Happened
- Generic wording came from the OPPC communication renderer, not the Daily Report renderer.
- Missing PDF attachment came from the OPPC email transport, which did not package a Daily Report PDF.
- Internal terms leaked because the OPPC communication was designed for internal accountability, not recipient-facing project communication.

## Smallest Safe Repair
- Preserve OPPC eventing, trust spine, and communication records.
- Repair only the OPPC **email transport branch for `channel_family=daily_report`** so it now:
  - uses `build_email_subject("daily-report", record)`
  - uses `render_email_html("daily-report", record, note)`
  - renders and attaches the Daily Report PDF
  - preserves To/CC/BCC route truth through `deliver_notification`

## Preview Verification
- Main-agent preview verification: `DR-2026-03607`
- Testing-agent independent verification: `DR-2026-03608`
- Both produced branded Daily Report capture records with one PDF attachment and banned internal terms absent.
