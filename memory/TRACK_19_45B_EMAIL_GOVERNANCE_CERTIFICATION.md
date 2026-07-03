# TRACK 19.45B · Email Governance Certification

## Provider
`lib.fsi_email_sender.fsi_send_email` — one provider for the entire
Operational Intelligence engine. Track 19.45B introduces zero new
email code paths.

## Delivery contract
- **Preview** — HTML rendered by `engine.render_html(digest)` and
  returned via `GET /api/operational-intelligence/{product_id}/preview`.
  Never sends email.
- **Dispatch dry-run** (default) — composes + writes history + writes
  audit but does not send. Returned to caller with recipient list so an
  operator can verify.
- **Dispatch live** — requires explicit `dry_run=false` on the
  authorized dispatch route. Applies the shared dedupe guard (per
  ISO-week key + recipient hash).
- **Idempotency** — the shared dedupe collection
  (`operational_intelligence_dedupe`) prevents double-sends within a
  period.

## Test guarantee
Every Track 19.45B lock test runs in-process against a fake DB. No live
network calls. No real recipient lookup. No accidental delivery.

## Cutover status
- Shop Intelligence — new product · no legacy shop digest existed · no
  cutover gate required.
- Corporate Intelligence — new product · no legacy corporate digest
  existed · no cutover gate required.

## Six pillars
- **Powerful** — one provider used by every OI product.
- **Simple** — dry-run default protects all environments.
- **Beautiful** — shared HTML renderer produces boardroom output.
- **Trusted** — dedupe guard + audit trail on every send.
- **Proven** — Track 19.40 lock test still enforces "one provider".
- **Operational** — recipient expansion done at send time via
  `list_recipients_for`, guaranteeing group membership is current.
