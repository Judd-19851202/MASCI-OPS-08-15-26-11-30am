# TRACK 19.46 · Email Governance

## Provider
`lib.fsi_email_sender.fsi_send_email` — one provider for the entire
Operational Intelligence engine. Track 19.46 introduces zero new
email code paths.

## Delivery contract (unchanged)
- **Preview** — HTML rendered via shared `engine.render_html(digest)`
  and returned by `GET /api/operational-intelligence/weekly_operations_digest/preview`.
  Never sends email.
- **Dispatch dry-run** (default) — composes + writes history + writes
  audit but does not send.
- **Dispatch live** — requires explicit `dry_run=false` on the
  authorized route. Applies the shared dedupe guard
  (`operational_intelligence_dedupe`).
- **Recipient expansion** — through the Track 19.45A universal
  recipient engine (`list_recipients_for`). No hardcoded emails.

## Test guarantee
Every Track 19.46 lock test runs in-process against a fake DB.
No live network calls · no real recipient lookup · no accidental
delivery.

## Cutover status
Weekly Operations is a new product · no legacy weekly digest
existed · no cutover gate required.

## History + Audit API email posture
Neither read-only endpoint sends email under any condition. They
only expose existing rows written by the engine.
