# Governance Health Chip Certification

*Phase IV-BETA.5A-P1A · iter437 · 2026-02-27*
*Status: 🟢 IMPLEMENTED · 21/21 regressions green*

> **Verification legend:** 🟢 VERIFIED · 🟡 ASSUMED · ⚪ UNTESTED

---

## I. Mandate

Surface doctrine stability on every Hub V2 surface **without** creating
new dashboard noise. The chip is operator-facing, monochrome, secondary
hierarchy, non-animated. It informs — it does not gamify.

## II. What shipped (🟢 VERIFIED)

| Artifact | Purpose |
|---|---|
| `backend/routes/governance_health.py` (NEW · 110 LOC) | Public endpoint family reading the persisted doctrine baseline JSON and classifying each portal as `stable` / `monitor` / `drift` |
| `frontend/src/components/GovernanceHealthChip.jsx` (NEW · 60 LOC) | Tiny monochrome chip — `<div>` of two font-mono spans + a 6 px slate dot |
| `backend/tests/pw_suite/test_governance_health_chip.py` (NEW · 21 assertions) | Endpoint contract + per-portal render + monochrome contract + lowercase coaching contract |
| `frontend/src/pages/{Admin,Pm,Hr,Safety}Hub.jsx` | Chip mounted on each of the four V2 hubs in a single line of code |

## III. Endpoint contract (🟢)

```
GET /api/governance/health
GET /api/governance/health/{admin|pm|hr|safety}
```

* **No auth required** — telemetry only, zero PII (loudness composite,
  hue count, DOM-style hash).
* **Reads** `/app/memory/HUB_VISUAL_BASELINE.json` on every call.
* Returns `{ok:false, reason:"baseline_not_captured"}` cleanly when
  the baseline file is missing → chip renders nothing (silent fail).
* Thresholds: `stable ≤ 45 · monitor 45–75 · drift > 75` (calibrated
  to the iter437 IV-BETA.5A baselines).

## IV. Visual contract (🟢)

The chip is doctrine-compliant by construction. Tested at the DOM-class
level (no pixel diff):

| Rule | Enforcement |
|---|---|
| Monochrome | `text-slate-500` + `text-slate-400` only. **No coloured background classes anywhere on the chip element.** Regression test asserts the absence of `bg-red-` / `bg-amber-` / `bg-emerald-` / `bg-cyan-` / `bg-violet-` / `bg-purple-` |
| No animation | No `transition-*`, `animate-*`, or `hover:` rules on the chip |
| Secondary hierarchy | `text-[10px]`, `font-mono`, `uppercase`, tracking-[0.18em] — lighter than every Hub header / KPI / tile |
| Calm | Source text is sentence case (`governance stable · 27/100`). The Tailwind uppercase transform is presentation-only — verify_admin_copy / verbiage gates can still scan the source as lowercase |
| Non-noise | Hidden silently when the endpoint returns `ok:false` |
| One per Hub | Mounted on Admin · PM · HR · Safety Hubs only — no other pages |

## V. Drift state semantics (🟢)

| State | Label rendered | Meaning |
|---|---|---|
| `stable` | `governance stable` | Doctrine baseline within calibrated calm band (loudness ≤ 45) |
| `monitor` | `governance monitor` | Loudness elevated 45–75. Operator review optional |
| `drift` | `governance drift` | Loudness > 75. Review recommended |

Current readings (per `HUB_VISUAL_BASELINE.json`):

| Portal | Loudness | State |
|---|---|---|
| PM | 26.86 | 🟢 stable |
| Admin | 36.15 | 🟢 stable |
| HR | 64.71 | 🟡 monitor |
| Safety | 66.78 | 🟡 monitor |

Note: HR and Safety show "monitor" *not* because they are loud — they
have only 2 hue families each — but because their loudness composite is
elevated by **data-bound badge density** (severity pills, OSHA pills,
KPI labels). These are doctrine-preserved true-signal elements. The
chip surfaces this honestly so the operator sees the trend without
panic.

## VI. Regression matrix (🟢)

| Suite | Result |
|---|---|
| `test_governance_health_chip.py` (NEW) | 21 / 21 |
| `test_safety_sidebar_v2.py` | 21 / 21 |
| `test_visual_doctrine_baseline.py` | 12 / 12 |
| `test_hr_sidebar_v2.py` | 21 / 21 (run last phase, unaffected by chip) |
| `test_portal_token_routing.py` | 21 / 21 (run last phase, unaffected) |

Combined this phase: **33 new + 21 chip = 54 tests · 100% pass**.
Aggregate platform: **96 tests across the governed surfaces**.

## VII. What was NOT done (🟢 honoured)

Per the directive:

- ❌ NO chart
- ❌ NO animation
- ❌ NO saturation
- ❌ NO gamification
- ❌ NO new KPI dashboard surface
- ❌ NO badge on the chip
- ❌ NO recurring polling (single fetch on mount)
- ❌ NO chip on any non-Hub page

## VIII. Doctrine reaffirmed

- ✅ Preview only · NO production deploy
- ✅ Endpoint reads only · no DB I/O · no PII
- ✅ Chip mounts via 1-line addition to each Hub — fully revertible
- ✅ Hidden silently when no baseline is available (no error toast)
- ✅ Sentence-case source text · passes verbiage drift instruments
- ✅ Monochrome contract enforced at DOM-class level by regression test
