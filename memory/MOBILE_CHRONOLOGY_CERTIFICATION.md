# Mobile Chronology Certification

**Phase V-Prelude · Wave 1.1**
**Status:** 🟢 **CERTIFIED · preview env**
**Date:** 2026-05-28

---

## Scope

The Operational Timeline Sidecar's mobile rendering contract. Locks in
the calmness + ergonomic guarantees for field operators using the
PM Project Detail surface on iPhone-class viewports.

## Viewport target

- **Primary:** iPhone 13 emulation (390 × 844 px logical · DSR 3 ·
  Mobile Safari UA). This is the platform's canonical "field operator
  device" profile — see `backend/tests/pw_suite/conftest.py` viewport
  table.
- **Secondary:** iPad (1024 × 1366 px) — sidecar renders identically
  with more horizontal breathing room.
- **Desktop:** 1920 × 1080 px — sidecar maintains its bounded width
  (no full-bleed expansion).

## Mobile guarantees

### Layout
- **Single column.** No multi-column table, no side-by-side rows.
  `ChronologyPanel` renders an `<ol>` of stacked `<li>` rows — natural
  mobile rhythm.
- **No horizontal body overflow.** Playwright asserts
  `document.body.scrollWidth ≤ clientWidth + 4` on the iPhone profile.
- **No towering vertical feed.** The sidecar's `max-h-[420px]` scroll
  container keeps the chronology bounded; the rest of the
  PmProjectDetail surface stays accessible without endless scrolling.

### Tap targets
- **Refresh control.** Tailwind `min-h-[32px]`. Playwright asserts
  `boundingBox().height ≥ 31` on every viewport.
- **"Show all" affordance.** Same `min-h-[32px]` floor.
- **No micro-touch traps.** No < 28 px hit areas inside the sidecar.

### Reading rhythm
- **Slate-500 metadata + slate-800 body.** Type contrast tuned for
  outdoor mobile readability (≥4.5:1 against the white sidecar bg).
- **Tabular-nums** on the date column (`formatLocalShort`) — keeps the
  left-rail aligned across rows on small screens.
- **`break-words`** on titles + subtitles — long station IDs / sub
  names wrap cleanly within the column.

### Anti-doctrine guarantees
- ❌ No FAB.
- ❌ No bottom-sheet modal triggered from the sidecar.
- ❌ No swipe-to-dismiss gestures.
- ❌ No haptic patterns.
- ❌ No notification badge counters on the sidecar header.

## Probes

`backend/tests/pw_suite/test_v_prelude_wave1_1_sidecar_calmness.py`:
- `test_sidecar_mounts_on_pm_project_detail[mobile]` — sidecar
  visible at 390 × 844.
- `test_sidecar_mobile_single_column_no_overflow[mobile]` —
  bounding box width ≤ 394 px AND body has no horizontal scroll.
- `test_sidecar_refresh_button_is_thumb_safe[mobile]` — ≥ 32 px.

All 🟢 green.

## Future considerations (NOT in scope for Wave 1.1)

The following would each be Wave 3 (Mobile polish) work — explicitly
excluded from Wave 1.1:
- Sticky-top date headers per chronological day.
- Pull-to-refresh gesture (replacing the explicit Refresh control).
- Quick-filter chips (would introduce loud color accents — vetoed by
  doctrine until Wave 4).

---

— certified by E1 · 2026-05-28
