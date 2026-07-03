# TRACK 19.45B · Corporate Intelligence · Data Source Map

Corporate Intelligence introduces **zero new data sources**. Every value
comes from another implemented Operational Intelligence product.

| Signal | Source | Method |
|---|---|---|
| Domain score (safety, project, fleet, shop, transportation, hr, training, po, executive ops) | Each domain OI product | `engine.compose(db, product_id=X).operational_intelligence_score.overall_score` |
| Domain attention items | Each domain OI product | `sections[section_key='needs_immediate_attention'].items` |
| Corporate weighted score | Local weight table `CORPORATE_WEIGHTS` (see score model doc) | Weighted average of scored domains only |
| Domains with insufficient data | Domain OI product's `confidence` field | Excluded from rollup, listed at bottom of top-5 table |

## Composition contract
Corporate must never fabricate a domain score. If a domain aggregator
returns `confidence: insufficient_data`, that domain is:
1. **Excluded from the weighted rollup** (its weight is redistributed
   because we normalise by the sum of scored weights, not the full
   100).
2. **Listed at the bottom of the domain table** with score "—" and
   attention "insufficient_data" — visible, not hidden.

## Zero-drift guarantees
- No new database collections.
- No new email provider.
- No new scheduler.
- No new recipient list — Corporate Intelligence uses the shared
  Track 19.45A recipient engine (`corporate_intelligence` group).
- No new renderer, PDF engine, audit collection, or history collection.
