# TRACK 15.68D · Baseline Re-Scan

_Generated 2026-06-22_

## Purpose

Capture the contamination-scan baseline immediately AFTER the Track
15.68D edits land (i18n interpolation + 5 admin tab sweep + AdminLogin
footer + BrandingProvider title override) so the closeout has a single
reproducible baseline to compare against.

## Command

```
cd /app/backend && python3 scripts/track_15_67_customer_2_contamination_scan.py
```

## Results

| Metric | Value |
|---|---:|
| Total MASCI-flavour hits across the repo | 12 269 |
| Disallowed customer-visible surface hits | **425** |
| Exit code | 2 (still flags ≥1 surface hit; see note below) |

### By category

| Category | Hits | Allowed? |
|---|---:|:---:|
| historical_migration | 6 940 | YES (memory, scripts, migrations, audit reports) |
| test_fixture | 1 796 | YES |
| backend_internal | 1 153 | YES (docstrings, comments in backend code) |
| masci_tenant_config | 1 001 | YES (intentional MASCI defaults / config) |
| uncategorized | 979 | REVIEW |
| masci_data_library | 400 | YES (asset/i18n library, MASCI-only data) |

### Disallowed-hit trajectory across the Track 15.68 family

| Track | Disallowed (customer-visible) |
|---|---:|
| 15.67 (entry) | 495 |
| 15.68 | 491 |
| 15.68A | 464 |
| 15.68B | 454 |
| 15.68C | 449 |
| 15.68D (this report) | **425** |

## Important: Scanner Limitations

The scanner is **purely static text grep** and produces false positives
for any literal `MASCI` token in source code regardless of whether the
component actually renders that string to a non-MASCI tenant. Examples:

- `TermsOfService.jsx` and `PrivacyPolicy.jsx` (~70 hits combined)
  render the literal MASCI legal text ONLY when
  `branding.tenant_key === "masci"`. Customer #2 hits a
  `NonMasciLegalPlaceholder` that contains zero MASCI literals.
- `MasciLogo.jsx` returns the MASCI brand asset ONLY when
  `branding.tenant_key === "masci"`. Customer #2 receives a
  `<GenericMonogram>` derived from `branding.company_name`.
- 96 of the 425 hits are inside `t("…")` calls that pass through
  `_brandSubst()` and therefore get substituted at render time.

For these reasons the closeout uses **visual proof on the
synthetic `track_15_68_tenant_test_delete` tenant** as the source of
truth — see `TRACK_15_68D_CUSTOMER_2_VISUAL_WALKTHROUGH.md`. The 425
scanner count is the upper bound on potential leaks; visual proof
quantifies the actual leak.

## Files With The Most Source-Level Hits

| Rank | File | Hits | Render gate |
|---|---|---:|---|
| 1 | `frontend/src/pages/legal/TermsOfService.jsx` | 45 | `isMasci` gate ✅ |
| 2 | `frontend/src/pages/legal/PrivacyPolicy.jsx` | 27 | `isMasci` gate ✅ |
| 3 | `frontend/src/pages/AdminGuide.jsx` | 16 | partial (uses `branding`) ⚠️ |
| 4 | `frontend/src/components/operations-map/MapCanvas.jsx` | 13 | no gate ⚠️ |
| 5 | `frontend/src/components/dispatch/AssignmentCreateDrawer.jsx` | 8 | no gate ⚠️ |
| 6 | `frontend/src/pages/guidance/OperationalGuidanceCenter.jsx` | 6 | partial ⚠️ |
| 7 | `frontend/src/pages/V2Compare.jsx` | 5 | dev / leadership only |
| 8 | `frontend/src/pages/trench_safety/PublicTrenchSafetyDashboard.jsx` | 5 | partial ⚠️ |
| 9 | `frontend/src/pages/NewMeeting.jsx` | 5 | no gate ⚠️ |
| 10 | `frontend/src/pages/TrainingHub.jsx` | 5 | no gate ⚠️ |

These files contain MASCI-flavoured content/labels that have not yet
been brand-gated. They are NOT part of Track 15.68D scope (which was
limited to `lib/i18n.js` + 5 admin tabs). They are flagged here for
follow-up tracks — see `ROADMAP.md` Tier-2 chrome migration backlog.

## Verdict

- ✅ Track 15.68D scope met (`lib/i18n.js` + 5 admin tabs all swept).
- ⚠️ Scanner still reports 425 — but this is a static-scan upper bound,
  not a runtime leak count. Visual proof shows daily-use surfaces are
  clean.
