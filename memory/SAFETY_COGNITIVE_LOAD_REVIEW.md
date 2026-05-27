# Safety Cognitive Load Review

*Phase IV-BETA.4C · iter437 · 2026-02-27*
*Status: 🟢 ANALYSIS COMPLETE · IMPLEMENTATION NOT STARTED*

> **Verification legend:** 🟢 VERIFIED · 🟡 ASSUMED · ⚪ UNTESTED

---

## I. Cognitive load drivers in Safety today

Cognitive load on a Safety surface is dominated by three failure modes:

1. **Visual collision** — too many simultaneous accents fighting for
   the eye. Safety today: 9 hue families on the Hub (vs PM Hub 3, HR
   Hub 5).
2. **Urgency dilution** — every row marked "important", so nothing
   reads as important. Safety today: 42 `bg-red-*` occurrences across
   25 pages, most of which are decorative.
3. **Coaching absence** — operators have to infer what each tile
   does from its 1-word label. PM/HR coaching sublines cut this; Safety
   tiles today have **no doctrine sublines** under the icon.

## II. Per-page cognitive load (🟢 spot-checked)

| Page | Driver(s) | Severity |
|---|---|---|
| `SafetyHub.jsx` | All 3 (collision + dilution + coaching gap) | 🔴 highest |
| `SafetyCorrectiveActions.jsx` | Mostly collision — large filter row + heavy column count | 🟡 |
| `SafetyDocuments.jsx`, `SafetyDocumentsLibrary.jsx` | Stripe palette mixed with severity colour | 🟡 |
| `SafetyIncidents.jsx` | Already disciplined (SEV_PILL) | 🟢 |
| `SafetyAudits.jsx` | Domain colour not formally defined → eye searches for the anchor | 🟡 |
| Auth pages (Login, Forgot, Reset, Change Password) | Single-purpose, low load | 🟢 |

## III. Reduction levers (⚪ UNTESTED · plan only)

For the Safety V2 implementation pass, three levers cut cognitive load
without touching workflow:

| Lever | Estimated load reduction |
|---|---|
| Consolidate 9 hues → 4 (one per domain) | ~40% |
| Reserve red for severity pills + severe CTAs only | ~25% |
| Add ≤14-word coaching sublines per tile | ~15% |
| Single neutral CTA across the Hub | ~10% |

Combined target: **~75% lower cognitive load on the Hub**, brought
into Admin/PM/HR cohort. Estimated post-trim DOM-style loudness:
roughly **PM-tier (≤55)** if discipline matches HR P1B.

## IV. Operator scan-clarity benchmarks (🟡 ASSUMED)

| Question | Pre-trim Safety today (intuited) | Post-V2 target |
|---|---|---|
| "Find this morning's open severe incidents" — clicks from cold start | 2-3 (Hub → Incidents → filter) | 2 (Hub → Incidents) |
| "Find an expired OSHA cert on a dispatched worker" | 3-4 (Hub → Documents → filter → cross-reference) | 2 (Documents tile with badge count) |
| "Decide whether the day requires safety officer attention" — scan time of Hub | ~6 seconds (visual collision) | <3 seconds |

These are operator-intuited benchmarks, not measured — they become
measurable once the V2 pass ships and we run an operator pilot day.

## V. Stress-resilience (🟢 inherited posture)

Safety is the portal an operator opens **during** stress, not before.
Three properties preserve scan clarity under stress:

1. **Single dominant accent** per domain — eye locks on one colour.
2. **Severity pills as the only red signal** — eye finds severe rows
   in <1 second.
3. **Calm chrome (slate-900)** — no flashing, no animation, no glow.

The platform already enforces #3 across Admin/PM/HR; Safety V2 must
adopt the same.

## VI. Doctrine reaffirmed

- ✅ Analysis only · NO Safety code changes
- ✅ True danger preserved (severity pills, severe-tier prefixes)
- ✅ Coaching alignment will inherit `CROSS_PORTAL_COACHING_STANDARD.md §V`
- ✅ Preview only
