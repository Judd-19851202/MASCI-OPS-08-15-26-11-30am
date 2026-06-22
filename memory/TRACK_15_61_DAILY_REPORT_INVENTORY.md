# TRACK 15.61 — Daily Report Production Inventory (Phase 1)

**Source:** live production `mascidocs.com` (`APP_ENV=production`, `DB_NAME=masci_safety`)
**Captured:** 2026-06-22 12:18 UTC
**Tool:** `/app/tests/post_deploy/track_15_61_audit.py`
**Raw data:** `/app/memory/track_15_61_data/forensics.json`

## Headline counts

| Metric | Value |
|---|---|
| Total Daily Reports in production database | **154** |
| Reports in the last 60 days | **154** (the entire production corpus is younger than 60 days) |

Inference: the platform's Daily Report dataset is **young**. Either older reports were never migrated, OR they have been deleted, OR the platform's Daily Report adoption window is genuinely ~2 months. This is itself a finding — see `TRACK_15_61_RECOMMENDATIONS.md` item R-AGE.

## Reports per project — top 20

| # | Project | Reports (60d) |
|---|---|---|
| 1 | 24-12 | 64 |
| 2 | 25-21 | 26 |
| 3 | 26-01 - CP | 19 |
| 4 | 24-13 - CP | 18 |
| 5 | 26-07 | 14 |
| 6 | 25-22 - CP | 6 |
| 7 | 25-03 | 2 |
| 8 | 20-07 | 1 |
| 9 | ZZ-RC1-LIVE-VERIFY-2026 | 1 (synthetic) |
| 10 | 26-02 | 1 |
| 11 | _PROD_CERT_DO_NOT_USE | 1 (synthetic) |
| 12 | PROD-ORPHAN-CORNER-VERIFY | 1 (synthetic) |

The tail is dominated by certification harness records (3 of the 12 unique projects are synthetic). The real-world distribution is concentrated in ~5 projects: 24-12 (Parent Loop family) and 25-21 lead.

## Least active projects (bottom 20)

Every project beyond #5 has ≤6 reports in 60 days. **Real per-job daily-report cadence is poor for everything except 24-12 and 25-21.** A working civil job should generate roughly 20 daily reports per month per active crew. The corpus shows ~64/60 days on 24-12 — about one per day, healthy. 26-07 with 14/60 (≈ 23%) and 26-01 with 19/60 (≈ 32%) are below cadence.

## Reports per superintendent — top 10

| # | Superintendent | Reports |
|---|---|---|
| 1 | (unset · field left blank) | **29** |
| 2 | Christopher Gaines | 23 |
| 3 | Bob | 19 |
| 4 | Allen | 16 |
| 5 | Jaymn Judd | 13 |
| 6 | Lenny | 12 |
| 7 | Allen Smathers | 12 |
| 8 | RICH SANCHEZ | 6 |
| 9 | ALLEN SMATHERS | 5 |
| 10 | JOE SPIKER | 4 |

**Findings:**
- **The `superintendent` field is left blank on 29 of 154 (18.8%) of reports.** This is the single largest "person" in the data — an absence.
- **Identity drift.** "Allen" and "Allen Smathers" and "ALLEN SMATHERS" are almost certainly the same person; same for "Lenny"/possibly others; the free-text superintendent name is not bound to an employee identity.

## Reports per preparer (foreman) — top 10

| # | Preparer | Reports |
|---|---|---|
| 1 | Joe spiker | 24 |
| 2 | Ivan Lopez | 16 |
| 3 | JOE SPIKER | 13 |
| 4 | CHRISTOPHER GAINES | 11 |
| 5 | DULIER "IVAN" LOPEZ | 11 |
| 6 | Christopher Gaines | 11 |
| 7 | Superintendent | 11 |
| 8 | Leandro Juarez | 10 |
| 9 | MICHAEL TRAIL | 9 |
| 10 | Mike | 8 |

**Findings:**
- "Joe spiker" + "JOE SPIKER" = 37 reports by ONE person spread across two casings — the field is free-text typed, not bound to identity.
- "Ivan Lopez" + "DULIER \"IVAN\" LOPEZ" = at least 27, same human across two name variants.
- "Christopher Gaines" + "CHRISTOPHER GAINES" = 22 across two casings.
- **"Superintendent" with 11 reports is the literal word, not a name.** A foreman typed "Superintendent" into the `prepared_by` field, treating the field like a role label.

This points to a **UX flaw in the `prepared_by` field** — operators do not consistently know what to put there. See `TRACK_15_61_HUMAN_USABILITY_AUDIT.md`.

## Reports per crew — top 10

Crew names are stored inside `masci_crews[]` rows with no canonical key. The harness counted the most-common `crew_name`/`foreman`/`supervisor` field across all crew rows. Results:

| # | Crew label | Reports referencing |
|---|---|---|
| 1 | Joe spiker | 21 |
| 2 | Ivan Lopez | 16 |
| 3 | Christopher Gaines | 11 |
| 4 | Mike | 8 |

(Same identity-drift caveat applies.)

## Notable

- The harness saw at least **3 synthetic certification records** present in production (`_PROD_CERT_DO_NOT_USE`, `PROD-ORPHAN-CORNER-VERIFY`, `ZZ-RC1-LIVE-VERIFY-2026`). These should be confirmed legitimate test fixtures or, if leftover, cleaned up under a future track. They are NOT part of Track 15.61's clean-up scope (15.61 is read-only).
- Several reports are dated with future-looking ISO strings — preview-time creation timestamps that don't match construction reality. Not a 15.61 finding to fix; an artefact of how reports get created.
