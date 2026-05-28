# Governance Trendline — Extension

**Phase V-Prelude · Wave 1.1A**
**Status:** 🟢 **EXTENDED · preview env**
**Date:** 2026-05-28

---

## What changed

Before Wave 1.1A the platform had ONE governance trendline file:
- `memory/LOUDNESS_TRENDLINE.json` — portal-wide visual-loudness
  averages produced by `measure_visual_loudness.py`.

Wave 1.1A adds a **scoped, focused** trendline:
- `memory/TIMELINE_LOUDNESS_TRENDLINE.json` — sidecar-only calmness
  scores produced by `timeline_calmness_probe.py`.

Both trendlines coexist. They measure different things at different
scopes and are designed never to overlap.

## Why a separate trendline file

A portal-wide average hides regressions inside a single surface. The
Operational Timeline sidecar is a sensitive surface — its calmness IS
the user-trust contract for the entire chronology substrate. We need a
trendline that does NOT get smoothed out by the rest of the portal.

## Shape contract

Each entry in `TIMELINE_LOUDNESS_TRENDLINE.json`:

```json
{
  "iteration": "deploy-<short-sha>",
  "timestamp": "2026-05-28T19:08:00.123Z",
  "score": 0.0,
  "aggregate": {
    "accent_class_ratio": 0.0,
    "badge_density_per_1k_px2": 0.0,
    "red_usage": 0.0,
    "hierarchy_compression": 4.0,
    "vertical_density": 0.0,
    "chronology_dup_ratio": 0.0
  },
  "gate_breaches": [],
  "viewports_measured": 3,
  "chronology_row_count": 0,
  "chronology_truncated": false
}
```

Doctrine guarantees:
- **Append-only.** Old entries never mutate. Verified by pytest.
- **TRUST-TIME-1.** Every timestamp ends with `Z`. Verified by pytest.
- **List-shaped.** The file is `[ {…}, {…}, … ]` — never an object.
  A future agent that overwrites with `{…}` will be caught by the
  same pytest.
- **No PII.** Only structural scores. No operator names, project
  numbers, or content.

## How to read the trendline

| Pattern | Meaning |
|---|---|
| `score` flat near 0 across iterations | substrate is healthy |
| `score` slowly rising over deploys | calmness erosion in progress · review recent UI changes |
| Single-deploy spike then back to 0 | a transient bug landed and was reverted |
| `gate_breaches` non-empty | the probe blocked a deploy · root cause MUST be filed |
| `chronology_row_count` rising rapidly | a project is being spammed · consider review |
| `chronology_truncated=true` recurring | a project exceeds the 200-row cap · Wave 2 search territory |

## Governance probe inventory (after Wave 1.1A)

| Probe | Mode | Trendline / Report | Phase |
|---|---|---|---|
| `authority_mismatch_probe.py` | blocking | `AUTHORITY_MISMATCH_REPORT.md` | GOVERNANCE-INFRA-1 |
| `timestamp_doctrine_probe.py` | blocking | `TIMESTAMP_DOCTRINE_PROBE_REPORT.md` | TRUST-TIME-1B |
| `operational_links_doctrine_probe.py` | blocking | (probe output) | V-Prelude Wave 1 |
| `measure_visual_loudness.py` | warning | `LOUDNESS_TRENDLINE.json` | IV-BETA.2 |
| `timeline_calmness_probe.py` | warning + 5× blocking | `TIMELINE_LOUDNESS_TRENDLINE.json` | V-Prelude Wave 1.1A |
| `verify_no_contamination.py` | blocking | (script output) | iter437 P0 |
| `verify_env_identity.sh` | blocking | (script output) | iter437 P0 |
| `diff_doctrine_baseline.py` | warning | `DOCTRINE_BASELINE.md` | IV-BETA.4A |

## What "institutional calmness memory" means in practice

Six months from now, an operator can run:

```bash
python3 - <<'PY'
import json
h = json.load(open('/app/memory/TIMELINE_LOUDNESS_TRENDLINE.json'))
for e in h:
  print(e['timestamp'][:10], 'score=', e['score'], 'breaches=', len(e['gate_breaches']))
PY
```

…and SEE the calmness story of the platform deploy-by-deploy. That is
the institutional memory we're building: an honest, machine-recorded,
operator-invisible record of whether we kept our calmness promise.

---

— issued by E1 · 2026-05-28
