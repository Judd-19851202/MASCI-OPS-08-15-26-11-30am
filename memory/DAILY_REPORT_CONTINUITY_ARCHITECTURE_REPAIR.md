# Daily Report Continuity — Architecture Repair

- Stable identity source: canonical authenticated user object ID where available (`directory user.id`, `fl user.id`, portal user IDs), device ID only for device scoping.
- Canonical scope: `daily-report-new::<project_number>::<report_date>::<report_number-or-default>`.
- Commit model: successful submit clears exact live draft + exact idempotency key via `clearDraft()`; operator discard continues to archive via `discardDraft()`.
- Legacy migration: enumerate candidate legacy keys, select newest valid envelope, promote, verify target readback, delete source only after verified success.
- Telemetry contract: canonical auth helpers only; canonical events include `draft.write.ok`, `draft.write.fail`, `quota.warning`, `draft.restore.offered`, `draft.restore.action`, `draft.restore.blocked_cross_actor`.
