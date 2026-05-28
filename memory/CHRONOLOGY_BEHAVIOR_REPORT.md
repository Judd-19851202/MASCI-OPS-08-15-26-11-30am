# Chronology Behavior — Report

**Phase V-Prelude · Wave 1 Observation Window**
**Status:** 🟢 **substrate calm at window open**
**Date:** 2026-05-28

---

## What is being observed

The chronology surface — `ChronologyPanel` rendered inside the
sidecar and the constraint detail view — is the platform's first
attempt at a project-rhythm view. This report tracks how it behaves
in the substrate and what to watch for over the observation window.

## Substrate state (window open)

| Metric | Value |
|---|---|
| Live constraints (preview) | 0 |
| Live operational_links (preview) | 0 |
| Timeline rows aggregated across all projects | 0 |
| Trendline entries (calmness) | 4 |
| Most recent calmness score | 0.0 |
| Chronology dup ratio | 0.0 |
| Low-value bare-action rows | 0 |
| `truncated` flag fired? | never |

The chronology canvas is **empty**. Wave 1 observation begins from a
zero baseline by design — this means every row that lands during the
window is operator-introduced, not test residue.

## Behavior contract (locked by Wave 1)

Per `OPERATIONAL_TIMELINE_FOUNDATION.md` and the Wave 1.1 sidecar
implementation:

| Behavior | Enforced by |
|---|---|
| Newest-first sort | Backend `at`-descending sort + Playwright assertion |
| ≤ 200 items per call | Backend `MAX_ITEMS = 200` constant |
| Single-project per call | `project_id` query param REQUIRED |
| TRUST-TIME-1 timestamps | Regex enforced by trendline probe + Pydantic models |
| Voided links never surface | Backend filter + Wave 1.1 regression test |
| Audit-only links hidden from non-admin | Backend filter + Wave 1.1 PM probe |
| No client-side reordering | Frontend renders the list as received |
| Empty state copy | "No operational events recorded for this project yet." |
| Loading state copy | "Loading chronology…" |
| 30-row floor → "Show all" | Sidecar `MAX_VISIBLE = 30` constant |

## What chronology should LOOK like (substrate canonical)

When the substrate fills with real operations during the window, an
ideal row will resemble one of these patterns:

### Pattern A — Constraint event
```
14:32 · constraint: Utility conflict STA 144+50 · utilities · high
```
(date · kind label · constraint title · discipline · severity)

### Pattern B — Constraint chronology event
```
15:08 · constraint: Utility conflict STA 144+50 · owner contacted · Spoke w/ FPL coord 9:15a
```
(date · kind label · constraint title · action · note)

### Pattern C — Cross-artifact link
```
15:45 · photo: PH-… → constraint · evidence_for
```
(date · source kind · source id → target kind · relationship)

Each row answers ONE question — "what operationally happened?" —
and nothing else.

## Anti-patterns to watch for

These are the chronology drift markers. If ANY appear during the
observation window, treat them as freeze triggers:

| Anti-pattern | Why it matters | Detector |
|---|---|---|
| 5+ identical-signature rows from the same project | spam / replay bug | `chronology_dup_ratio > 0.20` |
| Subtitle = single word with no note | low operational signal | `low_value_repeats` rising |
| "Show all" expanded by default | enterprise feed drift | sidecar code review |
| Hover tooltips appearing | calmness drift | DOM sweep in calmness probe |
| Color in chronology rows | doctrine breach | Playwright loud-badge sweep |
| Cross-project rows | scope leak | timeline API probe |
| Older row appearing above newer | order regression | trendline + API probes |

## What "useful chronology" looks like (qualitative)

Drawn from operational doctrine — these are the qualitative tests
the operator + PM should apply during walkthroughs:

1. **Reconstruction time.** Question: "When did the FPL conflict
   start?" Answer should be findable in the sidecar in <10 seconds
   without scrolling past noise.
2. **Operational vocabulary.** Every row should use words the field
   actually uses ("STA 144+50", "FPL hold", "owner contacted") —
   never enterprise jargon ("activity", "engagement", "interaction").
3. **Past-tense focus.** Rows describe what HAPPENED. No row should
   read like a notification ("3 new updates", "click to expand").
4. **Operator agency.** Operators should feel they could safely
   ignore the sidecar for 24 hours and miss nothing operationally
   critical (because the chronology is reference, not alert).
5. **One-glance comprehension.** A PM should be able to scan five
   rows in five seconds and understand the operational story.

## Observation cadence

- **Per-deploy:** `timeline_calmness_probe.py` measures heuristics on
  the canonical surface; entry appended to trendline.
- **Weekly:** Routine `--iteration weekly-check` run logs the
  baseline calmness as the substrate begins to populate.
- **Per walkthrough:** Operator captures verbatim quotes + verdicts
  into `OPERATIONAL_TRUST_VALIDATION_REPORT.md`.

## Stop-the-line conditions for chronology specifically

Beyond the 18 freeze triggers, the chronology layer has these
additional behavioural triggers worth watching:

- A single project produces > 100 chronology rows in 24 hours.
- A PM asks "how do I delete a chronology entry?" — chronology is
  append-only by doctrine; this question signals UX confusion.
- A row appears with both an action AND empty note AND empty title.
- A row appears with a relationship NOT in the canonical 14-set.

---

— issued by E1 · V-Prelude Wave 1 observation posture · 2026-05-28
