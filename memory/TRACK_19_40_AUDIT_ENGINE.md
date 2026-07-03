# TRACK 19.40 · AUDIT ENGINE

`operational_intelligence_audit` collection (additive). Append-only.

Row shape:
```
{ id, product_id, event, actor, at, payload }
```

## Events tracked
- `dispatch` — every send (dry-run or live) writes one row. Payload includes `dry_run`, `send_status`, `recipient_count`, `dedupe_key`, `delivery[]`, `history_id`.
- `dispatch_skipped_dedupe` — recorded when the dedupe guard blocks a send.
- Future: `preview_viewed`, `pdf_downloaded`, `history_viewed` (Phase 2 dashboard).

Never mutated. Never deleted. This is the compliance trail.
