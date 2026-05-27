# Governance Checkpoint System — Phase IV-BETA.5A-P3A

*iter437 · 2026-02-27*
*Status: 🟢 IMPLEMENTED · 9/9 regression assertions green*

> **Verification legend:** 🟢 VERIFIED · 🟡 ASSUMED · ⚪ UNTESTED

---

## I. Mandate

Allow doctrine drift to be measured against **operator-blessed
baselines** — not just rolling averages. Checkpoints are
institutional memory; the chip now reads against them when present.

## II. What shipped (🟢 VERIFIED)

| Artifact | Purpose |
|---|---|
| `scripts/diff_doctrine_baseline.py --checkpoint LABEL` (NEW flag) | Append + tag the new records as `checkpoint=true` with `checkpoint_label=LABEL`. Implies `--append`. |
| `backend/routes/governance_health.py::_direction_for` (EXTENDED) | When a checkpoint exists for the portal, the endpoint compares current loudness against the **most-recent checkpoint** rather than the rolling window. Falls back to rolling math when no checkpoint exists. |
| `frontend/src/components/GovernanceHealthChip.jsx` (EVOLVED · same footprint) | Renders `data-reference="checkpoint"` and suffixes `" since checkpoint"` on the trailing text when drifting/improving. Title tooltip carries the checkpoint label. |
| `backend/tests/pw_suite/test_checkpoint_system.py` (NEW · 9 assertions) | Script writes label · 80-char cap · endpoint reference flip · chip data-attr · lowercase coaching contract |

## III. Schema (🟢)

Existing `DOCTRINE_TRENDLINE.json` records gain **two optional fields**
when written via the checkpoint flag — and ZERO new fields otherwise:

```json
{
  "portal": "safety",
  "timestamp": "2026-05-27T15:46:54+00:00",
  "calmness": 72.41,
  "hierarchy_consistency": 100,
  "escalation_noise": 24.41,
  "hue_family_count": 3,
  "badge_density": 12.41,
  "emphasis_score": 21,
  "status": "monitor",

  "checkpoint":       true,
  "checkpoint_label": "P3A operator-blessed initial baseline"
}
```

Non-checkpoint records are byte-for-byte identical to the P2A schema.

## IV. Endpoint payload (🟢)

```
GET /api/governance/health/{portal}
```

When a checkpoint exists for the portal, the response now carries:

```json
{
  "ok": true,
  "portal": "pm",
  "loudness": 32.75,
  "state": "stable",
  "direction": "stable",
  "delta": 0.0,
  "reference": "checkpoint",
  "checkpoint_label": "P3A operator-blessed initial baseline",
  "checkpoint_timestamp": "2026-05-27T15:46:54+00:00",
  "checkpoint_calmness": 32.75,
  "delta_since_checkpoint": 0.0
}
```

When no checkpoint exists, `reference="rolling"` and the original P2A
direction/delta semantics apply (recent vs older window).

## V. Chip evolution — footprint unchanged (🟢)

| Property | Before P3A | After P3A | Change |
|---|---|---|---|
| Elements | 3 (dot + 2 spans) | Same | none |
| Colour | slate-500 / slate-400 | Same | none |
| Animation | none | none | none |
| Label set | 5 (stable / improving / drifting / monitor / drift) | Same | none |
| Trailing suffix | `+6 drift` | `+6 drift since checkpoint` (when reference is checkpoint) | ~16 chars |
| `data-reference` attr | (none) | `rolling | checkpoint` | NEW attr |
| Tooltip | static summary | checkpoint label when present | richer |

The visual footprint is unchanged. The label is **monochrome** and
**lowercase source** so the verbiage gate still inspects clean text.

## VI. Operator workflow (🟢)

```bash
# Routine append (every deploy)
python3 scripts/diff_doctrine_baseline.py --append

# Operator-blessed checkpoint (manual · after a stability review)
python3 scripts/diff_doctrine_baseline.py --append \
  --checkpoint "Safety V2 stable review · 2026-02-27"

# Read back from disk
cat /app/memory/DOCTRINE_TRENDLINE.json | jq '.records[] | select(.checkpoint)'
```

After the operator blesses a checkpoint, every Hub V2 chip
automatically switches to comparing **against that checkpoint** — no
redeploy, no flag flip, no UI change visible to operator users.

## VII. Doctrine compliance (🟢)

- ✅ Filesystem-only · no DB writes
- ✅ Append-only · immutable once written
- ✅ Timestamped (`isoformat(timespec="seconds")`)
- ✅ Lightweight (2 new optional fields, both small strings/bools)
- ✅ NO dashboard panel
- ✅ NO notification on drift
- ✅ NO chart
- ✅ NO automation-induced drift correction (operator-driven)
- ✅ Chip footprint preserved
- ✅ Preview only · NO production deploy
