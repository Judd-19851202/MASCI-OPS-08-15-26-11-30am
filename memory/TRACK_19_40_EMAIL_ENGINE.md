# TRACK 19.40 · EMAIL ENGINE

**One email provider: `lib.fsi_email_sender.fsi_send_email`.**

Every product's live dispatch iterates `list_recipients_for(product_id, active_only=True)` and awaits `fsi_send_email(email, subject, html, db=db)` once per recipient. Errors are captured per-recipient in the audit `delivery[]` payload.

Dry-run mode never imports `fsi_send_email` (lazy import inside the live path). Lock test asserts `mock.called == False` after a dry-run dispatch.

Lock test also greps every OI module for banned sender imports (`resend.emails.send`, `smtplib`, `sendgrid`, `postmark`) — none permitted.
