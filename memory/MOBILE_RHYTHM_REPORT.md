# Mobile Rhythm — Report

**Phase V-Prelude · Wave 1 Observation Window**
**Status:** 🟢 **mobile contract green at window open**
**Date:** 2026-05-28

---

## What is being observed

The chronology sidecar (`/pm/projects/:projectNumber`) is the first
field-operator-targeted surface in the platform's V-Prelude phase.
Mobile rhythm — readability + ergonomics + fatigue — is the harder
half of the calmness contract. This report tracks it.

## Mobile contract (locked)

| Contract clause | Enforcement |
|---|---|
| Single-column at 390 px | Tailwind utility classes (no multi-column layout) |
| No body horizontal overflow | Playwright asserts `scrollWidth ≤ clientWidth + 4` |
| Refresh control ≥ 32 px tap target | Tailwind `min-h-[32px]` + Playwright bounding-box check |
| "Show all" control ≥ 32 px | Same |
| `max-h-[420px]` sidecar scroll | Bounded by Tailwind class; verified by DOM inspection |
| Slate-text reading rhythm | Single accent (Clock3 icon) · no gradient · no badge fill |
| Tabular-nums on date column | `formatLocalShort` rendering with `tabular-nums` |
| `break-words` on long titles | Tailwind class on chronology row |
| No FAB / no haptic / no swipe | Sidecar code review + Playwright DOM sweep |

## Playwright sweep (window open)

```
test_sidecar_mounts_on_pm_project_detail · mobile        · PASS
test_sidecar_mobile_single_column_no_overflow · mobile  · PASS
test_sidecar_refresh_button_is_thumb_safe · mobile       · PASS
test_sidecar_calm_chrome_no_loud_badges · mobile         · PASS
```

10/10 sidecar Playwright tests green across desktop · iPad · mobile.

## Calmness telemetry — per-viewport baseline

From `TIMELINE_LOUDNESS_TRENDLINE.json` latest entry:

| Viewport | accent_ratio | hierarchy | red_usage | vertical_density |
|---|---|---|---|---|
| Mobile (390 × 844) | 0.00 | 4 | 0 | 0 |
| iPad (1024 × 1366) | 0.00 | 4 | 0 | 0 |
| Desktop (1920 × 1080) | 0.00 | 4 | 0 | 0 |

Mobile and desktop render IDENTICALLY on every heuristic dimension at
window open. That is the canonical mobile rhythm baseline.

## What mobile rhythm SHOULD feel like (qualitative)

When the substrate populates, the operator's mobile experience should
match these doctrinal patterns:

1. **Thumb-only reachability.** Refresh, "Show all", back-link — all
   reachable in the bottom 60 % of a one-handed grip. Confirmed by
   Tailwind sizing + no top-bar-only controls.
2. **Single-page completeness.** A PM reviewing chronology should
   need ONE scroll arc to scan the sidecar — not a panning gesture
   in two axes. Bounded `max-h` and single-column layout enforce.
3. **Outdoor readability.** Slate-800 on white (≥ 4.5:1 contrast)
   passes the sunlight test. No light-grey-on-grey patterns
   anywhere in the sidecar.
4. **Pause-friendly.** No animations · no auto-refresh · no
   loading-spinner anxiety. The sidecar is the same when an operator
   returns to it 5 minutes later as when they left.
5. **Zero phantom motion.** No skeleton screens · no shimmer
   gradients · no progress bars. Empty state shows static italic
   text and waits patiently.

## Anti-patterns to watch for on mobile

| Pattern | Why it matters | Detector |
|---|---|---|
| Horizontal scroll appears | Layout regression | Playwright body-overflow check |
| Tap target falls below 28 px | Touch fatigue | Playwright bounding-box check |
| Hover-only controls | Mobile inaccessibility | DOM `:hover` style sweep |
| Auto-collapse / animation | Calmness drift | Visual-loudness probe sweep |
| Bottom-sheet modal trigger | Enterprise mobile drift | Code review |
| Pinned header on scroll | Calmness drift (vertical density rises) | Calmness probe `vertical_density` |
| Loud color appears on touch | Doctrine breach | Playwright class sweep |

## Mobile walkthrough scenarios (operator + 1 PM, recommended)

Each <5 minute on a real iPhone:

1. **Scenario · cold open.** Open the PM portal · navigate to a
   project · find the chronology. Time-to-comprehension expectation:
   ≤ 5 seconds.
2. **Scenario · reconstruction.** With the sidecar at >5 rows,
   answer the question "what was the FPL hold's resolution note?"
   Expected: ≤ 10 seconds without zoom.
3. **Scenario · interruption.** Open chronology, switch to phone
   app for 2 minutes, return. Expectation: chronology is exactly
   where it was, no auto-refresh, no scroll position lost.
4. **Scenario · outdoor.** Read the chronology with the device in
   sunlight (or simulated bright environment). Expectation: every
   row legible, no need to shade the screen.

Each scenario produces a `≤ 100 ms` snapshot via the calmness probe
post-walk:
```bash
python3 /app/scripts/timeline_calmness_probe.py \
  --iteration walkthrough-<scenario>-<initials>
```

## Stop-the-line conditions for mobile specifically

- A PM asks "can I make the text bigger?" — current sizing is
  expected to be sufficient; this question signals readability
  regression.
- A PM rotates their device to landscape to "read more" — landscape
  should not be a comprehension requirement.
- A row produces clipped text without `break-words` working — would
  indicate an upstream CSS regression.
- Refresh control no longer hits the ≥ 32 px floor — Playwright will
  catch but log here anyway.

## Reverification protocol (per window event)

Run after any significant change to the sidecar or to its CSS:
```bash
cd /app/backend && python -m pytest \
  tests/pw_suite/test_v_prelude_wave1_1_sidecar_calmness.py -q
python3 /app/scripts/timeline_calmness_probe.py --iteration reverify-mobile
```

Both should remain 🟢. Any regression is a stop-the-line event.

---

— issued by E1 · V-Prelude Wave 1 observation posture · 2026-05-28
