# Doctrine Checkpoint Protocol

*iter437 · Phase IV-BETA.5A-P3A · 2026-02-27*
*Status: 🟢 OPERATIONAL PROTOCOL · operator-driven*

> **Verification legend:** 🟢 VERIFIED · 🟡 ASSUMED · ⚪ UNTESTED

---

## I. Purpose

Provide a **lightweight, operator-driven protocol** for declaring,
honouring, and superseding doctrine checkpoints. Checkpoints turn
governance memory from *math* into *agreement*.

## II. When to declare a checkpoint (🟢 recommended events)

| Event | Operator action |
|---|---|
| End of a governance phase (e.g. IV-BETA.5A-P3) | Declare a checkpoint named after the phase |
| Operator-blessed stability review | Declare a checkpoint reflecting the review |
| Major feature merge that holds doctrine | Optional: declare a "post-merge" checkpoint |
| Pre-deploy of a high-stakes change | Declare a checkpoint immediately before deploy |
| Recovery from a doctrine regression | Declare a fresh checkpoint after rollback |

## III. How to declare (🟢)

```bash
python3 scripts/diff_doctrine_baseline.py --append \
  --checkpoint "Short operator-readable label"
```

Constraints (enforced by the script):

- Label is **operator free text**.
- Label is **trimmed and capped at 80 characters** (prevents
  log/UI overflow).
- One invocation writes ONE record per portal (4 records total per
  call).
- All four records share the same `checkpoint_label` and
  `timestamp`, so a checkpoint is **atomic at the platform level**.

## IV. Label conventions (🟡 recommended · advisory)

Operators may use any free text, but the platform reads better with:

| Pattern | Example |
|---|---|
| `<phase> · <date>` | `IV-BETA.5A-P3 baseline · 2026-02-27` |
| `<portal> stable · <reviewer>` | `Safety stable · jaymn.judd` |
| `<release-name>` | `Safety calmness pass · operator-blessed` |
| `<recovery-context>` | `Post-rollback · doctrine reset` |

Avoid:

- ❌ "TODO", "test", "asdf" — non-operational labels become noise.
- ❌ Emojis or status icons — the chip is monochrome.
- ❌ All-caps — the chip uppercase-transforms via Tailwind.

## V. How the chip honours a checkpoint (🟢)

1. Endpoint `/api/governance/health/{portal}` loads all trendline
   records for the portal.
2. If **any** record has `checkpoint=true`, the endpoint uses the
   **most-recent** one as the reference point (last-write-wins).
3. Direction is computed by comparing **current loudness** against the
   checkpoint's `calmness` value:
   - `|Δ| < 4.0` → `direction = stable`
   - `Δ < -4.0` → `direction = improving` (good)
   - `Δ > +4.0` → `direction = drifting` (warn)
4. Endpoint also returns `delta_since_checkpoint`, `checkpoint_label`,
   `checkpoint_timestamp`, and `checkpoint_calmness`.
5. Chip suffixes `" since checkpoint"` on the trailing text. Tooltip
   carries the checkpoint label.

## VI. How to supersede (🟢)

A checkpoint is **superseded by declaring a newer one**. There is no
delete operation — checkpoints are append-only. Old checkpoints remain
in the trendline for historical reference until the rolling-cap
(`TRENDLINE_MAX_RECORDS = 500`) ages them out.

If an operator needs to *force* the chip back to rolling-window math,
they can:

- Wait for the rolling cap to age the checkpoint out (slow but
  doctrine-pure), OR
- Move the trendline file aside (`mv DOCTRINE_TRENDLINE.json
  DOCTRINE_TRENDLINE.archive.{date}.json`) and start fresh.

## VII. What the protocol DOES NOT do (🟢 honoured)

- ❌ NOT send any notification
- ❌ NOT write to MongoDB
- ❌ NOT change any portal visible to a non-operator user
- ❌ NOT call any external service
- ❌ NOT mark records as "verified" via auth (the protocol is operator
  trust, not auth)
- ❌ NOT enforce a deploy gate (warning-only by design)

## VIII. Recommended cadence (🟡 advisory)

| Cadence | Action |
|---|---|
| End of every governance phase | One checkpoint capturing post-phase state |
| Weekly during stabilisation periods | Optional — usually only useful in unstable seasons |
| Per quarter | At least one explicit checkpoint, even if nothing major shipped |
| After ANY rollback | A fresh checkpoint capturing the recovered state |

## IX. Doctrine reaffirmed

- ✅ Operator-driven · no automation declares checkpoints
- ✅ Append-only · checkpoints are immutable once written
- ✅ Atomic per platform (all 4 portals at once)
- ✅ Last-write-wins reference semantics — simple, predictable
- ✅ Chip behaviour falls back gracefully when no checkpoint exists
- ✅ Preview only · NO production deploy

## X. First operator checkpoint (🟢 SUGGESTED)

After this iteration completes, the operator may declare the iter437
P3A checkpoint with:

```bash
python3 scripts/diff_doctrine_baseline.py --append \
  --checkpoint "iter437 IV-BETA.5A-P3 · platform baseline"
```

This anchors future drift detection to the **post-P3 baseline** —
the calmest, most-tested, most-instrumented platform state to date.
