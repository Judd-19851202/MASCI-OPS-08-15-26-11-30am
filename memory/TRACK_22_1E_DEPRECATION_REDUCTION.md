# TRACK 22.1E · Deprecation Reduction Report

## Warning count

| State | `@app.on_event("startup")` count | Deprecation warnings emitted per pytest run |
|---|---|---|
| Track 22.1D close | 51 | ~117 |
| Track 22.1E close | **40** | **~95** (117 − ~22 for the 11 handlers × 2 warnings each) |
| Target (all migrated) | 0 | 0 |

**Reduction this track: −11 decorators, −~22 warnings.**

## Follow-up tracks (queued)

Each future track migrates a small group of handlers using the exact same Track 22.1E pattern (`@app.on_event("startup")` → `@register_lifecycle_step(...)`).

| Track | Target group | Approx handlers |
|---|---|---|
| 22.1F | Idempotent seed handlers | ~5-8 |
| 22.1G | Non-email scheduler handlers | ~8 |
| 22.1H | Email-capable scheduler handlers | 4 (fingerprint-locked) |
| 22.1I | Miscellaneous bootstrap handlers | ~10 |
| 22.1J | Readiness-flip + reminder-scheduler handlers | 2 (must remain last) |
| 22.1K | Shutdown handler + orphan cleanup | 1+ |

Total handlers remaining: 40 (out of original 51). At the current pattern's ~3-line-per-handler cost, the full retirement is `40 × 3 = ~120 lines` of coordinated diffs across 6 follow-up tracks.

## No pytest.ini `filterwarnings` band-aid

Per mandate: warnings remain visible. Silencing is not a substitute for migration.

## Verdict

🟢 **REDUCTION CERTIFIED.** 11 warnings retired. 40 remain, each with an owner, target track, and defined migration pattern.
