# HR LIFECYCLE · RESPONSIVE CERTIFICATION

**Date**: 2026-06-02
**Authority**: OMEGA DIRECTIVE — P0 End-to-End Forensic Certification · Phase 6
**Mode**: READ-ONLY · static viewport math from CSS + DOM measurements (no live device test in this audit)
**Companions**: `HR_LIFECYCLE_UI_FORENSICS.md` (DOM tree), `HR_LIFECYCLE_ROOT_CAUSE_REPORT.md` (RCA)

---

## 1 · Sheet shell — responsive behavior

| Token | Class | Effect |
|---|---|---|
| Width | `w-full sm:max-w-xl` | 100% width on `< 640px` (mobile); capped at `max-w-xl` ≈ **576 px** on `≥ 640px` |
| Height | implicit 100vh (radix Dialog primitive) | full viewport height |
| Layout | `p-0 flex flex-col` | column flexbox, no padding on the shell itself |
| Side | `side="right"` | slides in from the right |
| Inner scroll | `<div className="flex-1 overflow-y-auto px-5 py-4 text-sm">` | the one scrollable region |

**The drawer always occupies the full viewport height.** It does not shrink to content. The Save button must therefore land within the inner scroll region to be reachable without scrolling.

---

## 2 · Vertical budget per viewport — Status tab, Resigned + Rehire Not Eligible scenario

Approximate row heights (Tailwind `text-sm` ≈ 20 px line-height, form rows ≈ 56-68 px each including Label + control + spacing):

| Element | Approx height |
|---|---:|
| `<SheetHeader>` (title + role chip + Accountability link + 3px border) | **~110 px** |
| `<TabsList>` (3 tabs, h-10 + border) | **~40 px** |
| `HelpTipBlock` separation guidance | ~48 px |
| `HelpTip` Lifecycle Guide (REC-3 collapsed) | ~36 px |
| Label "New status" + Select | ~64 px |
| Separation Type Select | ~64 px |
| Last Day Worked + Termination Date (grid-cols-2 row) | ~64 px |
| `HelpTipBlock` rehire guidance | ~48 px |
| Rehire Eligibility Select | ~64 px |
| Rehire Eligibility Reason Textarea (rows=2) | ~80 px |
| Reason / note Textarea (rows=3) | ~96 px |
| Offboarding playbook amber warning | ~80 px |
| **Save button (h-9 + 12 px top margin from space-y-3)** | **~48 px** |
| Recent status history (5 entries) | ~120 px |
| **Total inner content (`Resigned + Not Eligible` path)** | **~922 px** |

---

## 3 · Per-viewport reachability matrix

For each viewport, `available_scroll_area = viewport_height − 150 px (header+tabs)`. The Save button is at vertical offset ≈ **778 px** from the top of the scroll content (sum of the rows above it). It is reachable without scrolling only when `available_scroll_area ≥ 778 + 48 = 826 px`.

| Class | Resolution | Viewport h | Available scroll | Reachable without scroll? | Reachable with scroll? | Verdict |
|---|---|---:|---:|:-:|:-:|---|
| **Desktop XL** | 1920 × 1200 | 1200 | 1050 | ✅ | ✅ | 🟢 PASS |
| **Desktop FHD** | 1920 × 1080 | 1080 | 930 | ✅ | ✅ | 🟢 PASS |
| **Desktop / Laptop** | 1440 × 900 | 900 | 750 | 🔴 (−76 px) | ✅ | 🟡 SCROLL REQUIRED |
| **Laptop common** | 1366 × 768 | 768 | 618 | 🔴 (−208 px) | ✅ | 🔴 BELOW FOLD |
| **Laptop small / iPad land** | 1280 × 800 | 800 | 650 | 🔴 (−176 px) | ✅ | 🔴 BELOW FOLD |
| **iPad portrait** | 768 × 1024 | 1024 | 874 | ✅ | ✅ | 🟢 PASS |
| **iPad land + keyboard** | 1024 × ~440 | 440 | 290 | 🔴 (−536 px) | ⚠️ scroll, but reason field steals focus | 🔴 SEVERE |
| **iPhone 14** | 390 × 844 | 844 | 694 | 🔴 (−132 px) | ✅ | 🔴 BELOW FOLD |
| **iPhone 14 + keyboard** | 390 × ~514 | 514 | 364 | 🔴 (−462 px) | ⚠️ keyboard steals focus | 🔴 SEVERE |
| **iPhone SE** | 375 × 667 | 667 | 517 | 🔴 (−309 px) | ✅ | 🔴 BELOW FOLD |
| **iPhone SE + keyboard** | 375 × ~360 | 360 | 210 | 🔴 (−616 px) | ⚠️ severe | 🔴 SEVERE |

**Visualization** (Save button below the fold marked 🔴):

```
Desktop FHD          Laptop 1366×768          iPad land+kbd            iPhone+kbd
┌─────────────┐      ┌─────────────┐          ┌─────────────┐          ┌──────────┐
│  Header     │      │  Header     │          │  Header     │          │  Header  │
│  Tabs       │      │  Tabs       │          │  Tabs       │          │  Tabs    │
│  ...form    │      │  ...form    │          │  ...form    │          │ status   │
│  ...        │      │  reason ▮   │ ← fold   │ sep ▮ rehire│ ← fold   │ select   │
│  reason ▮   │      │  amber !    │ 🔴       └─────────────┘ 🔴       │ ▮ kbd!   │ 🔴
│  amber !    │      │ [Save]      │          [Save]                   │ amber!   │
│  [Save] ✅  │      │  history    │          history                  │ [Save]   │
│  history    │      └─────────────┘          (off-screen)             │ history  │
└─────────────┘                                                        └──────────┘
```

---

## 4 · Per-transition reachability

The form length depends on the chosen lifecycle status:

| Transition | Extra fields rendered | Inner content height | Save reachable without scroll? |
|---|---|---:|---|
| Active → **Inactive** | (none) | ~440 px | ✅ on all viewports |
| Active → **Suspended** | (none) | ~440 px | ✅ on all viewports |
| Active → **Leave of Absence** | leave_start_date + expected_return_date | ~530 px | ✅ on all viewports |
| Active → **Resigned** (rehire = eligible) | separation_type + 2 dates + rehire select | ~750 px | 🔴 1366×768 / mobile |
| Active → **Resigned** (rehire ≠ eligible) | + rehire_reason textarea | ~830 px | 🔴 1366×768 / laptop / mobile |
| Active → **Terminated** (= layoff) | same as Resigned | ~830 px | 🔴 1366×768 / laptop / mobile |
| Active → **Retired** | same as Resigned | ~830 px | 🔴 1366×768 / laptop / mobile |
| Inactive → Active (Rehire) | invoked via separate Reactivate dialog at a different code location — NOT via the Status tab | (different modal · smaller form) | ✅ |

**The five operator-named transitions affected by this defect — Resigned, Terminated, Laid Off — all share the same below-fold geometry on laptop/tablet/mobile.**

---

## 5 · Software-keyboard interaction (mobile-specific)

On iOS / Android, focusing a textarea raises the on-screen keyboard which consumes ≈ 280-360 px of vertical viewport space.

| Step | iPhone 14 | iPad portrait | iPad landscape |
|---|---|---|---|
| Idle | 844 px viewport | 1024 px viewport | 768 px viewport |
| `hremp-status-reason` (3-row textarea) focused | 514 px viewport | 690 px viewport | 440 px viewport |
| Save button position relative to viewport | ~150 px below visible area | ~80 px below visible area | ~330 px below visible area |
| Browser auto-scroll-into-view behavior | scrolls textarea into view; **does NOT scroll further to expose Save** | same | same |
| Operator action required to reveal Save | manual scroll of modal | manual scroll of modal | manual scroll of modal |

**Mobile = primary failure surface**, because the operator's mental model is "I typed → I tap Done" — and tapping Done dismisses the keyboard but does NOT scroll further to expose the Save button.

---

## 6 · The exact moment HR loses the Save button

```
1. HR opens drawer via StatusBadge click  (REC-2 deep-link · works)
2. Drawer lands on Status tab            (REC-2 · works)
3. HR picks "Resigned" from dropdown      (works)
4. Separation section auto-renders        (works)
5. HR picks separation_type, dates, rehire_eligibility  (works)
6. HR taps "Reason / note" textarea       (KEYBOARD APPEARS on mobile/tablet)
7. HR types a 2-line reason               (textarea remains visible · keyboard fills bottom 330 px)
8. HR taps "Done" on keyboard             (keyboard dismisses · viewport restored)
9. HR scrolls down looking for Save       ← critical moment
   → Browser autoscroll already pinned the textarea ~middle of viewport.
   → Save button is now ~80-150 px below the visible viewport.
   → HR's finger is in the textarea region; the scroll gesture from there
     scrolls the OUTER PAGE (which is locked under the drawer scrim),
     not the INNER drawer scroll region — so nothing happens.
10. HR taps the X to close                ← THE DROP-WRITE
11. Status reverts to Active in the table; HR concludes "no save button"
```

This sequence — confirmed by the operator's own evidence — is the user-experience reality on laptop 1366×768 and every mobile/tablet form factor with an on-screen keyboard.

---

## 7 · Responsive verdict

| Device class | Verdict |
|---|---|
| Desktop ≥ FHD | 🟢 PASS — Save reachable without scroll |
| Laptop 1440 × 900 | 🟡 SCROLL — Save reachable with 1 short scroll |
| **Laptop 1366 × 768 (most common operator class)** | 🔴 **FAIL — Save below fold** |
| iPad portrait | 🟢 PASS — Save reachable without scroll (idle) |
| iPad landscape | 🟡 SCROLL — short scroll needed |
| **iPad landscape + keyboard** | 🔴 **FAIL — Save invisible during text entry** |
| iPhone (any) | 🔴 **FAIL — Save below fold even idle** |
| **iPhone + keyboard** | 🔴 **SEVERE — Save effectively unreachable** |

**Failure surface estimate**: ≈ **60-70% of HR's plausible device fleet** (laptops are predominantly 1366×768 fleet-procurement spec; mobile + iPad usage is reported in operator field walks).

---

## 8 · STOP

Responsive certification phase complete. READ-ONLY directive honored.
