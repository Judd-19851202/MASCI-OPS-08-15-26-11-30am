# Governance Baseline Lock — Phase IV-BETA.5A-P4A

*iter437 · 2026-02-27*
*Status: 🟢 LOCKED · institutional reference standard*

> **Verification legend:** 🟢 VERIFIED · 🟡 ASSUMED · ⚪ UNTESTED

---

## I. Mandate

Lock the iter437 IV-BETA.5A-P4 governance state as the **institutional
reference standard** for future drift detection. Document the calmness,
hierarchy, and escalation-noise scores so future iterations can be
read against this anchor.

## II. Locked baseline (🟢)

| Field | Value |
|---|---|
| Checkpoint label | `iter437 IV-BETA.5A-P4 · operational governance baseline` |
| Checkpoint timestamp | `2026-05-27T16:06:16+00:00` |
| Trendline records | 52 (this checkpoint = records 49–52) |
| Records flagged checkpoint | 16 (across all checkpoint declarations to date) |

## III. Per-portal lock state (🟢)

### Admin
| Metric | Value |
|---|---|
| Calmness | 36.11 |
| Hue families | 5 |
| Badge density | 2.11 |
| Escalation noise | 22.1 |
| Hierarchy consistency | 100 (single hash across viewports) |
| State | 🟢 stable |

### PM
| Metric | Value |
|---|---|
| Calmness | 32.75 |
| Hue families | 4 |
| Badge density | 2.75 |
| Escalation noise | 18.8 |
| Hierarchy consistency | 100 |
| State | 🟢 stable |

### HR
| Metric | Value |
|---|---|
| Calmness | 70.15 |
| Hue families | 3 |
| Badge density | 14.15 |
| Escalation noise | 26.1 |
| Hierarchy consistency | 100 |
| State | 🟡 monitor (data-bound badges drive composite) |

### Safety
| Metric | Value |
|---|---|
| Calmness | 72.41 |
| Hue families | 3 |
| Badge density | 12.41 |
| Escalation noise | 24.4 |
| Hierarchy consistency | 100 |
| State | 🟡 monitor (data-bound badges drive composite) |

## IV. Locked portal classifications (🟢)

| Portal | V2 default posture | Doctrine state | Notes |
|---|---|---|---|
| Admin | n/a (no Sidebar V2 yet) | 🟢 stable | calmness refinement P3C surgical demotion landed |
| PM | **DEFAULT (V2 on)** | 🟢 stable | escape hatch `?pmSidebarV2=0` |
| HR | **DEFAULT (V2 on)** | 🟡 monitor (data-bound) | escape hatch `?hrSidebarV2=0` |
| Safety | OFF (legacy default) | 🟡 caution | needs 1 more stable iteration before flip |

## V. Doctrine compliance at lock time (🟢)

- ✅ Severity pills (`SEV_PILL`) untouched · true urgency loud
- ✅ Severe-tier banners record-level only
- ✅ OSHA Recordable pill preserved at red-900
- ✅ Severe-incident email subject `🚨 SEVERE INCIDENT · …` preserved
- ✅ Communication footers standardised
- ✅ Coaching sublines ≤ 14 words across all governed surfaces
- ✅ Single neutral CTA on all Hub V2 tiles
- ✅ Red reserved for incidents-domain stripes + severity + severe banners
- ✅ Zero `/api/admin/*` leakage from non-admin contexts
- ✅ Hierarchy consistent across desktop / iPad / mobile (every portal)

## VI. Reference standard semantics (🟢)

This baseline is now the **calmest, most-tested, most-instrumented
state** of the MASCI platform to date. Future iterations that drift
beyond `±4` loudness points from these per-portal numbers will surface
on the Hub V2 chip as `governance drifting · +N drift since checkpoint`.

When the operator authorises the NEXT major phase (Safety 5B, Dispatch
governance, or Safety V2 default flip), the natural cadence is:

1. Implement the phase.
2. Re-run `test_visual_doctrine_baseline.py` to capture new state.
3. Run `diff_doctrine_baseline.py --append` to log the new record.
4. If everything held doctrine, declare a **new** checkpoint:
   ```bash
   python3 scripts/diff_doctrine_baseline.py --append \
     --checkpoint "<new-phase-name> · post-implementation"
   ```
5. The chip naturally rotates to the new reference (last-write-wins).

## VII. Doctrine reaffirmed

- ✅ Baseline locked · institutional reference established
- ✅ Append-only · no overwriting old checkpoints
- ✅ Last-write-wins rotation when new checkpoints arrive
- ✅ Preview only · NO production deploy
