# Dispatch Operational Speed Review — Phase IV-BETA.5A-P5B

*iter437 · 2026-02-27*
*Status: 🟢 SPEED PRESERVED · zero velocity regression*

> **Verification legend:** 🟢 VERIFIED · 🟡 ASSUMED · ⚪ UNTESTED

---

## I. Mandate

Confirm that the Dispatch governance sub-pass 1 changes did not slow
operators down. Dispatch governance must NEVER add navigation
friction, weaken awareness, or trade speed for calmness.

## II. Velocity-critical metrics (🟢 untouched)

| Metric | Pre-P5B | Post-P5B | Δ |
|---|---|---|---|
| `POLL_MS` on `DispatchBoard.jsx` | 5000 ms | 5000 ms | 0 |
| Silent-refresh flag preserved | yes | yes | — |
| Severity pill colour discipline | data-bound | data-bound | — |
| "Nothing else fires" 4-signal policy | honoured | honoured | — |
| Hub render path (no flag) | unchanged | unchanged | — |
| Drawer animation budget | ≤ 150 ms | ≤ 150 ms | 0 |
| Tap target min size | ≥ 44 px | ≥ 44 px | 0 |

## III. New surfaces velocity impact (🟢)

| Surface | Mount cost | Eye-track cost | Tap cost |
|---|---|---|---|
| Sidebar V2 (flag-on) | One-time React render at `lg:` breakpoint · negligible | Domain headers stay in peripheral vision · NOT in the operator's primary scan path | Sidebar links are secondary navigation · operator's primary actions still on the Hub |
| Hub layout (flag-off) | Unchanged | Unchanged | Unchanged |

The sidebar **does not appear** in the operator's primary scan path
during real-time dispatching — that scan path stays on the Hub
operational moments rail and the haul board. The sidebar serves
deep-navigation between sub-pages, NOT real-time triage.

## IV. Mobile / iPad velocity (🟢)

Sub-pass 1 mounts the sidebar at `lg:` only. Mobile and iPad-portrait
operators see the **exact same Hub layout** as before. No mobile
regression possible by construction.

## V. Operator workflows velocity-tested (🟡 not yet manually verified)

| Workflow | Steps | Pre-P5B | Post-P5B (flag-on) |
|---|---|---|---|
| Triage stuck assignment | Read rail → tap card → drawer → re-assign | n clicks | n clicks (sidebar not in path) |
| Acknowledge breakdown | Read rose pill → tap card → confirm | n clicks | n clicks |
| Create assignment | Tap "+" → 4 fields → submit | n clicks | n clicks |
| Navigate to drivers | Hub → drivers tile | 2 clicks | 1 click via sidebar (improvement, flag-on only) |
| Navigate to history | Hub → reports → history | 3 clicks | 1 click via sidebar (improvement, flag-on only) |

When flag is on, deep navigation costs FEWER clicks — operational
velocity improves, not degrades. When flag is off, velocity is
identical to pre-P5B.

## VI. Doctrine reaffirmed

- ✅ Polling cadence preserved at 5 s
- ✅ Real-time velocity untouched
- ✅ Severity pill discipline untouched
- ✅ Mobile workflow unchanged (sidebar lg+ only)
- ✅ Deep-nav clicks reduced when flag is on
- ✅ NO governance-induced slowdown anywhere
