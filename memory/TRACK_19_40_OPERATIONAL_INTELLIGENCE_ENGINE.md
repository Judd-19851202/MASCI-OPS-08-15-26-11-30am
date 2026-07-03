# TRACK 19.40 · OPERATIONAL INTELLIGENCE ENGINE

**Date:** 2026-07-03 · **Status:** 🟢 GO · **Six Pillar: 58/60 · Zero-Drift**

## Charter
Build the permanent foundation for every operational briefing, digest, executive report, and cross-domain intelligence surface. Every current and future digest product plugs into this engine — no second scheduler, renderer, audit, or email pipeline may exist anywhere in the codebase.

## What shipped
- **Package:** `backend/operational_intelligence/` with 5 modules: `registry` · `engine` · `recipients` · `scheduler` · `products` · `routes`.
- **Engine version:** `1.0.0`.
- **10 registered products** — 2 IMPLEMENTED · 8 CONTRACT_REGISTERED.
- **3 new endpoints** — `/api/operational-intelligence/products` · `/…/{product_id}/preview` · `/…/{product_id}/dispatch`.
- **3 additive collections** — `operational_intelligence_audit` · `operational_intelligence_history` · `operational_intelligence_dedupe` · plus `operational_recipient_groups`. Existing `morning_digest_recipients` collection reused (already carried `digest_type` for multi-product use).

## Registered products
| Product ID | Status | Perm | Freq | Day |
|---|---|---|---|---|
| `safety_morning_digest` | IMPLEMENTED | safety+admin | weekly | Mon 13:00 UTC |
| `executive_operations_brief` | IMPLEMENTED | admin-only | weekly | Mon 14:00 UTC |
| `weekly_operations_digest` | CONTRACT | admin-only | weekly | Mon 13:00 |
| `transportation_intelligence` | CONTRACT | safety+admin | weekly | Mon 13:00 |
| `fleet_intelligence` | CONTRACT | safety+admin | weekly | Mon 13:00 |
| `hr_intelligence` | CONTRACT | admin-only | weekly | Mon 13:00 |
| `training_intelligence` | CONTRACT | admin-only | weekly | Mon 13:00 |
| `project_intelligence` | CONTRACT | admin-only | weekly | Mon 13:00 |
| `shop_intelligence` | CONTRACT | safety+admin | weekly | Mon 13:00 |
| `corporate_intelligence` | CONTRACT | admin-only | monthly | 1st 14:00 |

CONTRACT_REGISTERED products expose full metadata but their aggregator raises `NotImplementedError` — no fabricated data. Follow-up tracks (19.40b/c/…) implement each domain aggregator.

## Zero-drift
- Reuses Track 19.39's `morning_digest_recipients` collection (already multi-product-shaped).
- No mutation of any existing collection.
- No second scheduler · renderer · audit path · email provider (uses existing `fsi_send_email` from lib).
- Track 19.39's `POST /morning-digest/send` continues to work unchanged.

## Rollback
1. Comment out the `_register_oi_routes(...)` block in `server.py`.
2. Delete `backend/operational_intelligence/`.
3. Optional collection drops (`operational_intelligence_audit`, `_history`, `_dedupe`, `operational_recipient_groups`) — additive, safe to leave.

Rollback confidence: **HIGH.**
