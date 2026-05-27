# Doctrine Trendline System — Phase IV-BETA.5A-P2A

*iter437 · 2026-02-27*
*Status: 🟢 IMPLEMENTED · operator memory operational*

> **Verification legend:** 🟢 VERIFIED · 🟡 ASSUMED · ⚪ UNTESTED

---

## I. Mandate

Build a **filesystem-only**, **append-only** operational memory file
that lets the platform track **direction**, not just current state.
No database. No charts. No dashboard. Just memory.

## II. What shipped (🟢 VERIFIED)

| Artifact | Purpose |
|---|---|
| `/app/memory/DOCTRINE_TRENDLINE.json` | Append-only operational memory. One record per portal per invocation. Rolling cap at 500 records (the file never balloons). |
| `scripts/diff_doctrine_baseline.py --append` (NEW mode) | Reads the current `HUB_VISUAL_BASELINE.json` and pushes one record per portal onto the trendline. |
| `backend/routes/governance_health.py` (EXTENDED) | The chip endpoint now blends static baseline with trendline data and surfaces a `direction` field. |
| `frontend/src/components/GovernanceHealthChip.jsx` (EVOLVED · same footprint) | Renders one of: `governance stable / improving / drifting / monitor / drift` — without changing element count or visual size. |
| `backend/tests/pw_suite/test_trendline_and_default_posture.py` (NEW) | Trendline append contract + direction field surfaces + escape hatches |

## III. Trendline schema (🟢)

Every appended record carries:

```json
{
  "portal":                "pm",
  "timestamp":             "2026-05-27T15:17:18+00:00",
  "calmness":              32.75,
  "hierarchy_consistency": 100,
  "escalation_noise":      18.75,
  "hue_family_count":      4,
  "badge_density":         2.75,
  "emphasis_score":        7,
  "status":                "stable"
}
```

Record IDs are not needed — the file is a chronological log indexed
purely by `timestamp` + `portal`.

### Rolling cap

The trendline holds the **last 500 records** (≈ 125 per portal). Older
records drop off the head. This keeps the file under ~80 KB even after
hundreds of deploy runs.

## IV. Direction computation (🟢)

Each chip request computes direction as follows:

1. Load all `DOCTRINE_TRENDLINE.json` records for the portal, oldest first.
2. If fewer than `DIRECTION_RECENT_N + DIRECTION_OLDER_N + 1 = 7` records exist, return `direction = "new"` (chip falls back to static state label).
3. Otherwise compare the average calmness of the last **3** records (recent window) against the average of the **3** records preceding them (older window).
4. If `|Δ| < 4.0`: direction = `stable`.
5. If `Δ < -4.0`: direction = `improving` (calmness DROPPED → good).
6. If `Δ > +4.0`: direction = `drifting` (calmness ROSE → warn).

The chip then renders one of 5 labels:

| Condition | Label | Trailing |
|---|---|---|
| State = `drift` (override) | `governance drift` | `nn/100` |
| Direction = `improving` | `governance improving` | `-delta drift` |
| Direction = `drifting` | `governance drifting` | `+delta drift` |
| State = `monitor` | `governance monitor` | `nn/100` |
| else | `governance stable` | `nn/100` |

## V. Chip evolution — footprint preserved (🟢)

The chip now has *more semantic depth* but **zero footprint growth**:

| Property | Before P2A | After P2A | Change |
|---|---|---|---|
| Elements | 1 dot + 2 spans = 3 nodes | Same | none |
| Animation | none | none | none |
| Background colour | none | none | none |
| Text colour | slate-500 + slate-400 | Same | none |
| Font | font-mono | Same | none |
| Size | text-[10px] | Same | none |
| Label set | 3 (stable / monitor / drift) | 5 (+ improving / drifting) | +2 strings |
| `data-direction` attribute | (none) | `stable | improving | drifting | new` | NEW |

## VI. What was deliberately NOT done (🟢 honoured)

Per the directive:

- ❌ NO chart
- ❌ NO dashboard panel
- ❌ NO visual analytics expansion
- ❌ NO gamification
- ❌ NO operator noise
- ❌ NO database collection
- ❌ NO timestamp on the chip (operator does not need to read a date)
- ❌ NO color delta (delta is monochrome slate prose only)
- ❌ NO trend visualisation

## VII. Operator workflows (🟢)

| Workflow | How |
|---|---|
| Append trendline (on deploy) | `python3 scripts/diff_doctrine_baseline.py --append` — wired into `pre_deploy_check.sh` |
| Append trendline (locally) | Same command from any developer shell |
| Read trend by eye | `cat /app/memory/DOCTRINE_TRENDLINE.json` |
| See direction at a glance | The chip on any Hub V2 surface |
| Aggregate snapshot | `python3 scripts/diff_doctrine_baseline.py --summary` (already in IV-BETA.5A-P1D) |

## VIII. Doctrine reaffirmed

- ✅ Filesystem-only · no DB writes · no new collection
- ✅ Append-only · history is preserved
- ✅ Rolling cap prevents bloat
- ✅ Chip footprint unchanged · operationally restrained
- ✅ Direction signal **falls back gracefully** to static state when history is short
- ✅ Preview only · NO production deploy
