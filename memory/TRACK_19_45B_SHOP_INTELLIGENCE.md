# TRACK 19.45B · Shop Intelligence Digest

**Status:** IMPLEMENTED · shipped in Track 19.45B (2026-07-04).

## Purpose
Weekly boardroom-quality briefing on shop health. Surfaces safety holds,
critical + aging defects, OOS units, work-order backlog, DVIR field
defects, and equipment incidents so shop/fleet/safety owners can act on
Monday morning.

## Product identity
- product_id: `shop_intelligence`
- Display name: **Shop Intelligence Digest**
- Permission role: `safety_or_admin`
- Template: `executive_v1`
- Schedule: weekly · Monday 13:00 UTC
- Aggregator: `_agg_shop_intelligence` in `operational_intelligence/products.py`
- Section contract: canonical 14-section layout (Track 19.41)
- Score model: universal 0-100 `OperationalIntelligenceScore` (Track 19.41)

## Six-Pillar audit
- **Powerful** — weighs safety holds > aging critical defects > OOS units.
- **Simple** — score + attention level + 5 signals · under 60 seconds.
- **Beautiful** — Executive Ops rendered via shared `render_html`.
- **Trusted** — every metric backed by a real collection · empty
  collections show as 0 (never fabricated) · insufficient_data path
  preserved.
- **Proven** — 6 lock tests (see `test_track_19_45b_shop_corporate_intelligence.py`).
- **Operational** — every attention item maps to a deep link.

## Sections shipped
Every one of the 14 canonical sections is present. Insufficient-data
paths handled honestly.

## No-Auto-Decision
The report is an attention signal. The platform does NOT determine
mechanic fault, operator fault, preventability, discipline, or
return-to-service authorisation.
