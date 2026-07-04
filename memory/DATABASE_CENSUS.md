# Database Census

- Unique Mongo collections referenced: **170** (`db.<name>` regex over `backend/`).
- Storage size: `backend/storage/` = 533 MB · `backend/backups/` = 32 KB (preview).

## Full collection ID list
See `PLATFORM_MANIFEST.json` → `collections` array (170 `COLL-####` IDs).

## Aggregate classification
- **KEEP** — ~155 collections (production-canonical: `daily_reports`, `incidents`, `meetings`, `jhas`, `qaqc_inspections`, `equipment_master`, `fire_extinguishers`, `employee_records`, `vendor_records`, `asset_records`, `trust_spine_events`, `user_directory_sessions`, etc.).
- **MERGE (Phase-2)** — `db.fire_extinguishers` → `db.equipment_master` (Track 19.62 Phase B roadmap).
- **RETIRE (post-deploy)** — 5 legacy candidates: `db.legacy_*`, `db.deprecated_*` prefixes — grep shows no active writes, only historical reads.
- **INDEXES** — verified via startup log `[safety-indexes] ensured` (Track 19.05 · Track 15.28A retention indexes intact).
- **TTL / retention** — Track 15.28A retention indexes + Track iter425 auto-90d backup retention verified.

## Zero drift
No collection added or renamed in Tracks 20.6B, 20.7, 20.8, 20.9, 21.0.
