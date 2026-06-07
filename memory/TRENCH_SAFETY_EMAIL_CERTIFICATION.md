# Phase 7.5C · Email Certification

## Sender wrapper
File: `backend/server.py` — `async def _trench_send_email(to_email, subject, html)`.

Mirrors `_safety_send_email` exactly:
- Same Resend SDK path (`resend.Emails.send`).
- Same two-flag gating (`RESEND_API_KEY` non-empty + `AUTO_EMAIL_REPORTS` in `{true,1,yes}`).
- Same `noreply@mascidocs.com` sender, branded as `MASCI Trench Safety`.
- Returns `True` only when Resend was actually invoked. Returns `False` for stub/preview.
- Inherits the Resend webhook deliverability chain (`notification_delivery_*`) automatically — no new audit code.

## Subject standard
- `pdf_render.SUBJECT_TYPE_TAGS["trench-safety"] = "TRENCH SAFETY"`.
- Subject format (from `notifications.py:_send_email`):
  ```
  [MASCI · TRENCH SAFETY] <event tail> — <asset_id>
  ```
- Examples:
  - `[MASCI · TRENCH SAFETY] Safety Hold Issued — TB-07`
  - `[MASCI · TRENCH SAFETY] Certification Expired — TB-04`
  - `[MASCI · TRENCH SAFETY] Critical Inspection Failure — TB-01`
  - `[MASCI · TRENCH SAFETY] Certification Due ≤ 7 days — TB-12`

Stable prefix means existing Gmail/Outlook filters that match `[MASCI · …]` continue to work, and ops can add a `[MASCI · TRENCH SAFETY]` filter rule for safety on a single subject substring.

## Body template
`backend/routes/trench_safety/notifications.py:_email_body` — HTML matching the
platform's existing transactional emails (Safety / HR portal):
- MASCI Trench Safety eyebrow line.
- H1 = event title.
- Asset detail table (Asset ID · Type/Size · Serial · Location · Status).
- Coaching block (What happened / Why it matters / What to do next).
- Primary CTA button → `<PORTAL_URL>/safety/trench-safety/assets/{asset_id}`.
- Footer link → public field-safe view.

No template engine. Plain HTML, same shape as other transactional emails.

## Events that send email (from routing matrix)

| Event | Subject tail | Recipients |
|---|---|---|
| Safety Hold opened | "Safety Hold Issued" | safety, shop, dispatch, admin |
| Certification Hold opened | "Certification Hold Issued" | safety, admin |
| Critical inspection fail | "Critical Inspection Failure" | safety, shop |
| Cert due ≤ 14 days | "Certification Due ≤ 14 days" | safety |
| Cert due ≤ 7 days | "Certification Due ≤ 7 days" | safety, admin |
| Cert expired | "Certification Expired" | safety, shop, admin |

## Events that do NOT email (bell only per routing matrix)
- Major inspection fail (digest only)
- Damage report (bell + digest)
- Unsafe condition (bell + digest)
- Cert due ≤ 30 days (bell + digest)
- Hold cleared (bell)
- Maintenance/Inspection holds opened (bell)
- Repair awaiting verification (bell)
- Asset returned to service (bell + digest)

This matches the directive matrix exactly.

## Preview env behaviour
With `AUTO_EMAIL_REPORTS=false`:
- `_trench_send_email` returns `False` and logs `[trench-email-preview] to=… subject=…`.
- No Resend API call is made.
- Bell notifications are still created (these use the internal `db.notifications` collection, not Resend).
- Digest section still surfaces in `/api/safety/notifications/digest`.

This is the same gating model used by `_safety_send_email`, so preview environments inherit the same behaviour automatically.
