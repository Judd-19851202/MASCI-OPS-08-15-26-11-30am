# TRACK 15.68D · Final Contamination Scan

_Generated 2026-06-22_

## Command

```
cd /app/backend && python3 scripts/track_15_67_customer_2_contamination_scan.py
```

## Result

```
{
  "total_hits": 12269,
  "disallowed_count": 425,
  "categories": {
    "masci_tenant_config": 1001,
    "test_fixture": 1796,
    "backend_internal": 1153,
    "historical_migration": 6940,
    "uncategorized": 979,
    "masci_data_library": 400
  }
}
```

Persisted artefacts:

- `/app/test_reports/track_15_67_customer_2_contamination_scan.json`
- `/app/memory/TRACK_15_67_CUSTOMER_2_CONTAMINATION_SCAN.md`

## Disallowed Hit Anatomy

The 425 disallowed hits are not 425 visible leaks. They are 425
**potential** leaks identified by static grep. The breakdown:

| Bucket | Count | Render gate? | Visible to C2? |
|---|---:|---|---|
| Hits inside `t("…")` calls (interpolated by `_brandSubst()`) | 96 | YES via i18n interpolation | NO |
| Hits inside files with `isMasci` / `tenant_key === "masci"` gates | ~80 | YES | NO |
| Hits in dev-only / preview-only banners (`EnvBanner.jsx`) | ~5 | YES (`env !== "production"`) | NO in production |
| Hits in admin-tier owner's manual / V2 demo pages | ~50 | partial | partial |
| Hits in deeper-content pages (TrainingHub, NewMeeting, etc.) | ~190 | partial | YES (TBD) |

**Net visible leaks for daily-use customer chrome (Customer #2):** zero
on the home/hub, sign-in, admin login, safety, field, and dispatch
surfaces. See `TRACK_15_68D_CUSTOMER_2_VISUAL_WALKTHROUGH.md`.

## Tier-2 Backlog (Out of 15.68D scope)

The remaining ~190 deeper-content hits across ~180 files are deep-text
content edits (paragraphs, examples, training transcripts) that do not
gate render on `branding.tenant_key`. Migrating them is a content-rewrite
exercise, not a label sweep. Captured in `ROADMAP.md` as P1 follow-up
(Track 16.x candidate).

## Scanner Trend

| Track | Disallowed | Δ vs. previous |
|---|---:|---:|
| 15.67 baseline | 495 | — |
| 15.68 | 491 | -4 |
| 15.68A | 464 | -27 |
| 15.68B | 454 | -10 |
| 15.68C | 449 | -5 |
| 15.68D | **425** | **-24** |

A 14% reduction across the family, with the steepest cuts coming from
admin-tab chrome (15.68A) and i18n migration (15.68D).

## Verdict

⚠️ **HARD-FAIL** by scanner threshold (≥1 disallowed), but the user's
explicit doctrine states: _"If visual proof and contamination scan
disagree, visual proof wins."_ Visual proof confirms zero MASCI on the
six daily-use customer surfaces. The remaining 425 are flagged for the
Tier-2 follow-up track.
