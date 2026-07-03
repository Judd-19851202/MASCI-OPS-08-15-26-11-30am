# TRACK 19.40 · HISTORY ENGINE

`operational_intelligence_history` collection (additive). One row per dispatch (dry-run or live). Immutable — insert-only, no update surface.

Row shape:
```
{ id, product_id, period (ISO-week or manual key),
  digest_object, rendered_html,
  generated_by, generated_at }
```

Search/filter/download surfaces (Phase 2 · dashboard track). Historical truth: never regenerated — the row captures the exact digest at the moment it was composed.
