# TRACK 19.45B · Corporate Intelligence Digest

**Status:** IMPLEMENTED · shipped in Track 19.45B (2026-07-04).

## Purpose
Company-wide executive rollup. Composes every implemented Operational
Intelligence product, applies a weighted score model, and answers four
questions in under 60 seconds:
1. How is the company doing operationally? (Corporate Score)
2. Which domains need attention? (Domain scores table)
3. What should leadership look at first? (Top attention signals)
4. Where do I click? (Deep links + preview endpoints)

## Product identity
- product_id: `corporate_intelligence`
- Display name: **Corporate Intelligence Digest**
- Permission role: `admin_only`
- Template: `executive_v1`
- Schedule: monthly · first Monday 14:00 UTC
- Aggregator: `_agg_corporate_intelligence` in `operational_intelligence/products.py`
- Section contract: canonical 14-section layout (Track 19.41)
- Score model: weighted rollup on top of the universal 0-100 model.

## Composition
Corporate Intelligence composes each domain digest via
`engine.compose(db, product_id=X)` and folds the domain
`operational_intelligence_score.overall_score` into a weighted
average (see `TRACK_19_45B_CORPORATE_SCORE_MODEL.md`).

**No new data sources** — every value is derived from another
implemented OI product. Zero drift enforced.

## Six-Pillar audit
- **Powerful** — surfaces the weakest 3 domains + concrete attention
  items from each.
- **Simple** — one corporate score + domain table + signals list.
- **Beautiful** — shared executive layout · deep links included.
- **Trusted** — insufficient-data domains excluded from the rollup
  (never averaged as zero) and shown explicitly at the bottom of the
  domain table so gaps are visible, not hidden.
- **Proven** — 5 lock tests (`test_track_19_45b_shop_corporate_intelligence.py`).
- **Operational** — every domain row exposes a preview deep link.

## No-Auto-Decision
Cross-domain attention signal only. The platform does NOT declare
the company compliant, does NOT declare legal risk conclusions, does
NOT determine liability or discipline, and does NOT issue automatic
executive decisions.
