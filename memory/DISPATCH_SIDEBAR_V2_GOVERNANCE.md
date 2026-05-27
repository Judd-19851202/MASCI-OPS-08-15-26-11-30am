# Dispatch Sidebar V2 Governance — Phase IV-BETA.5A-P5B (Sub-Pass 1)

*iter437 · 2026-02-27*
*Status: 🟢 SUB-PASS 1 SHIPPED · sidebar behind flag · zero default-rendering risk*

> **Verification legend:** 🟢 VERIFIED · 🟡 ASSUMED · ⚪ UNTESTED

---

## I. Mandate

Foundational governance alignment ONLY. Build the Dispatch Sidebar V2
component behind `?dispatchSidebarV2=1` — establish the 4-domain
canonical structure without touching the haul-board, lifecycle,
notification engine, or any real-time logic.

## II. What shipped (🟢)

| Artifact | LOC | Purpose |
|---|---|---|
| `memory/DISPATCH_INFORMATION_PRIORITY_MAP.json` | — | 4-domain canonical map (Live Board · Driver Coordination · Lifecycle & Records · Guidance & Support) |
| `frontend/src/components/dispatch/sidebar/DispatchSideNavV2.jsx` (NEW) | ~150 | Sidebar V2 component · mirrors HR/Safety/PM pattern · governance-doctrine-aligned coaching sublines |
| `frontend/src/pages/DispatchHub.jsx` (PATCHED) | +6 | Conditional mount behind `useDispatchSidebarV2Enabled()`; preserves the existing single-column layout when flag is off |
| `scripts/verify_coaching_sublines.py` (EXTENDED) | +1 | `DispatchSideNavV2.jsx` added to `COACHING_FILES` · gate now governs Dispatch sidebar copy |
| `backend/tests/pw_suite/test_p5_dispatch_health_autocheckpoint.py` (NEW · 2 dispatch assertions) | — | Sidebar mount with flag · hidden by default |

## III. Sidebar V2 contract (🟢)

| Domain | Stripe | Purpose |
|---|---|---|
| **Live Board** | `#b91c1c` (red-700) | The ONE red domain — haul-board, escalations, breakdowns. Owns real-time urgency anchoring. |
| **Driver Coordination** | `#0e7490` (cyan-700) | Dispatch chrome — drivers, qualifications, sessions. |
| **Lifecycle & Records** | `#7c3aed` (violet-600) | Read-mostly references — truck lifecycle, history, reports. |
| **Guidance & Support** | `#475569` (slate-600) | Lowest-frequency — operator guides, password rotation. |

All coaching sublines ≤14 words, sentence-case, period-terminated.
Verified via `verify_coaching_sublines.py` (passing).

## IV. Flag posture (🟢)

This sub-pass ships the V2 sidebar **default-OFF**. Mirrors the
discipline used for the very first Safety V2 rollout — no operator
notices anything unless they opt in via `?dispatchSidebarV2=1`.
A future sub-pass (after operator-grade validation) may flip the
default per the established P2B pattern.

## V. What was NOT touched (🟢 honoured)

Per directive:

- ❌ NO haul-board rewrites (`DispatchBoard.jsx` untouched)
- ❌ NO websocket logic changes
- ❌ NO refresh engine changes (`POLL_MS = 5000` preserved)
- ❌ NO assignment workflow changes
- ❌ NO lifecycle logic changes
- ❌ NO notification logic changes
- ❌ NO rapid-refresh logic changes
- ❌ NO backend operational changes
- ❌ NO auth changes
- ❌ NO mobile workflow redesigns

## VI. Operational velocity preservation (🟢)

The sidebar mounts at `lg:` breakpoint only (`hidden lg:block` per the
HR/Safety pattern). At mobile / iPad-portrait, the Dispatch user
continues to see the existing Hub layout — operator scan speed
preserved.

## VII. Doctrine reaffirmed

- ✅ Sub-pass 1 default-OFF · operator opt-in via flag
- ✅ Coaching gate clean
- ✅ Real-time velocity preserved (no board / refresh / lifecycle code touched)
- ✅ Auth / notifications / backend untouched
- ✅ Mobile workflow unchanged
- ✅ Preview only · NO production deploy
