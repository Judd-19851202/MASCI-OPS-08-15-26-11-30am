# TRACK 19.45B · Zero-Drift Matrix

Every additive vs. mutative change made in Track 19.45B is enumerated
here. Nothing outside this table changed.

## Schemas
| Change | Type | Zero-drift impact |
|---|---|---|
| No new MongoDB collections | — | ✅ |
| No new indexes | — | ✅ |
| No new fields on existing collections | — | ✅ |

## Routes
| Change | Type | Zero-drift impact |
|---|---|---|
| No new routes — existing `/api/operational-intelligence/{product_id}/preview` and `/dispatch` handle both new products | — | ✅ |
| No new route file | — | ✅ |

## Emails
| Change | Type | Zero-drift impact |
|---|---|---|
| Uses shared `fsi_send_email` | additive | ✅ |
| No new email provider | — | ✅ |
| No new template file | — | ✅ (shared `render_html`) |

## Scheduler
| Change | Type | Zero-drift impact |
|---|---|---|
| Shop schedule declared via product metadata (weekly Mon 13:00 UTC) | metadata only | ✅ |
| Corporate schedule declared via product metadata (monthly first Mon 14:00 UTC) | metadata only | ✅ |
| No new cron / no new scheduler runtime | — | ✅ |

## Recipients
| Change | Type | Zero-drift impact |
|---|---|---|
| Uses shared Track 19.45A recipient engine | additive doc | ✅ |
| No new recipient collection | — | ✅ |
| No new admin panel | — | ✅ |

## Audit / history / dedupe
| Change | Type | Zero-drift impact |
|---|---|---|
| Uses shared `operational_intelligence_audit` | — | ✅ |
| Uses shared `operational_intelligence_history` | — | ✅ |
| Uses shared `operational_intelligence_dedupe` | — | ✅ |

## Score / trend
| Change | Type | Zero-drift impact |
|---|---|---|
| Uses shared `OperationalIntelligenceScore` | — | ✅ |
| Corporate weight table `CORPORATE_WEIGHTS` added to `products.py` | additive constant | ✅ |
| No new score model file | — | ✅ |

## Rollback
Revert `products.py` to remove `_agg_shop_intelligence`,
`_agg_corporate_intelligence`, `_get` shim, `CORPORATE_WEIGHTS`, and
re-add the previously CONTRACT_REGISTERED entries for both products.
Delete `test_track_19_45b_shop_corporate_intelligence.py` and the 11
Track 19.45B markdown docs. Rollback risk: **HIGH** (clean · no schema
touched).
