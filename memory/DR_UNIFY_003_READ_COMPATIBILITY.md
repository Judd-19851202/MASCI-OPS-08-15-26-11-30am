# DR-UNIFY-003 · Read Compatibility

## Purpose

Let application code read from the canonical `daily_report_*`
collections without breaking when the data currently lives in the
legacy `dr_v2_*` collections (or across both during the migration
window).

## Contract

```python
from lib.daily_report_collections import (
    resolve_read_collection_name,     # picks canonical vs. legacy
    canonical_write_collection_name,  # always canonical
    legacy_name,                      # canonical → legacy string
    COLLECTION_ALIASES,               # source-of-truth mapping
)
```

### Read

```python
name = await resolve_read_collection_name(db, "daily_report_drafts")
doc = await db[name].find_one({...})
```

- Returns the canonical name **only when it holds at least one
  document**. Otherwise returns the legacy name. Never merges.
- Cheap probe: `find_one({}, {"_id": 1})` per collection.
- Async so callers can await inside async routes.

### Write

```python
name = canonical_write_collection_name("daily_report_drafts")
await db[name].insert_one({...})
```

- Always canonical. This is a plain passthrough function today —
  reserved as a function so a future audit can grep for every
  callsite that mutates a daily-report-related collection.

## Guarantees (locked by tests)

- `test_compat_helper_exposes_expected_aliases` — the six canonical
  ↔ legacy pairs are exactly as documented.
- `test_resolve_read_prefers_canonical_when_populated` — three cases:
  canonical has data (returns canonical), only legacy has data
  (returns legacy), neither has data (returns canonical default).
- `test_compat_helper_never_returns_a_merge` — resolver source has no
  `+` on a return line, no `extend(`, no `update(` — it always
  returns a single collection name string.

## Adoption plan

- **Today (DR-UNIFY-003):** helper published. Existing callers still
  reference `dr_v2_*` directly. Both are equivalent because canonical
  collections are empty pre-migration and the read-compat helper
  transparently returns the legacy name.
- **DR-UNIFY-004 (preview):** migrate the three consumers to route
  every read through the helper:
    - `services/dr_ai/cache.py` (`dr_v2_ai_cache` reads)
    - `services/photo_intelligence/store.py` (`dr_v2_photo_intelligence`)
    - `services/ods_spine/ingest.py` (`dr_v2_drafts` approval-fact read)
- **DR-UNIFY-005 (production cleanup):** drop the legacy collections
  and remove the helper (or leave it as a no-op if useful for
  future migrations).

## No double-counting proof

The resolver returns a single string. It is impossible to accidentally
merge results because the function signature makes the merge case
un-representable — callers get a name, then execute a single query.
Regression lock: `test_compat_helper_never_returns_a_merge`.
