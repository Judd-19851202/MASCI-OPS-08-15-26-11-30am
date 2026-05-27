# Auto-Deploy Checkpoint System — Phase IV-BETA.5A-P5A

*iter437 · 2026-02-27*
*Status: 🟢 IMPLEMENTED · operator-checkpoint sanctity preserved*

> **Verification legend:** 🟢 VERIFIED · 🟡 ASSUMED · ⚪ UNTESTED

---

## I. Mandate

Every successful deploy must leave a **retrievable governance
breadcrumb** WITHOUT diluting operator-blessed checkpoints. Two
classes of checkpoint now coexist:

1. **Operator checkpoints** — manual, sacred, milestone-grade, low-frequency
2. **Deploy checkpoints** — automatic, quiet, append-only, operational breadcrumbs

## II. What shipped (🟢 VERIFIED)

| Artifact | Purpose |
|---|---|
| `scripts/pre_deploy_check.sh` (EXTENDED) | On successful gate-pass, appends `--checkpoint "auto · deploy {git-sha}"` automatically |
| `backend/routes/governance_health.py::_direction_for` (EVOLVED) | Operator checkpoints OUTRANK auto-deploy checkpoints; falls back to auto when no operator checkpoint exists |
| `frontend/src/components/GovernanceHealthChip.jsx` (EVOLVED · same footprint) | Suffixes `"since deploy"` (auto) vs `"since checkpoint"` (operator) on drift |
| `backend/tests/pw_suite/test_p5_dispatch_health_autocheckpoint.py` (NEW · 4 P5A assertions) | Auto-deploy records persist · operator outranks auto · kind label distinguishable |

## III. Reference hierarchy (🟢)

The chip endpoint's checkpoint-resolution order:

1. If **any** operator checkpoint exists for the portal → reference it.
2. Otherwise, if **any** auto-deploy checkpoint exists → reference it.
3. Otherwise → fall back to rolling-window math.

This guarantees: **declaring an operator checkpoint NEVER gets
overwritten by deploy noise**. Auto checkpoints serve only as
breadcrumbs *between* operator milestones.

## IV. Chip behaviour (🟢)

| Reference kind | Label | Trailing |
|---|---|---|
| Operator (stable) | `governance stable` | `27/100` |
| Operator (drifting) | `governance drifting` | `+6 drift since checkpoint` |
| Operator (improving) | `governance improving` | `-4 drift since checkpoint` |
| Auto (stable) | `governance stable` | `27/100` |
| Auto (drifting) | `governance drifting` | `+4 drift since deploy` |
| Auto (improving) | `governance improving` | `-2 drift since deploy` |
| No checkpoint | `governance stable / monitor / drift` | `nn/100` |

The chip footprint (1 dot + 2 spans) is unchanged; only the trailing
text varies. The `data-reference="checkpoint"` attribute on the chip
exposes the reference class for testing.

## V. Schema (🟢 · backward-compatible)

Auto-deploy checkpoint records carry the **exact same fields** as
operator checkpoints. The only distinguishing signal is the
`checkpoint_label` prefix `auto · deploy ` — both the endpoint and
the chip interpret this prefix to determine `checkpoint_kind`.

```json
{
  "portal": "pm",
  "timestamp": "2026-05-27T16:24:41+00:00",
  "calmness": 32.75,
  "checkpoint": true,
  "checkpoint_label": "auto · deploy 7af3c12"
}
```

No new top-level fields. No schema migration. Older trendline records
remain interpretable.

## VI. Why filesystem-only (🟢 doctrine compliance)

- ✅ Filesystem-only · no DB writes
- ✅ Append-only · immutable once written
- ✅ Rolling-cap (500 records · per P2A) keeps file size bounded
- ✅ NO notifications · NO dashboard panels · NO operator interruption
- ✅ NO new API endpoints — chip endpoint already returns the data

## VII. Doctrine reaffirmed

- ✅ Operator checkpoint sanctity preserved · operator outranks auto
- ✅ Chip footprint unchanged
- ✅ Auto records auditable from disk: `cat DOCTRINE_TRENDLINE.json`
- ✅ Pre-deploy gate continues to PASS even if checkpoint append fails (`|| true`)
- ✅ Preview only · NO production deploy
