# Driver Workflow Map · Phase 11 · Document 2 of 10

**Date:** 2026-05-24
**Purpose:** Tap-by-tap journey for a driver across one full shift. The ergonomic contract for the mobile experience.

**Doctrine:** A driver should never need to type more than 0–1 fields per state transition.

---

## The shift in 30 seconds

```
06:00 receive magic-link SMS
06:01 tap link → /d/{token} → DriverShell loads with today's first ASSIGNED haul
06:01 tap [ENROUTE_TO_LOAD] giant button → state updates
06:23 arrive plant → tap [AT_LOAD_SITE]
06:25 lined up → tap [LOADING]
06:32 loaded → tap [LOADED] → pick material (one tap from a Recent list)
06:33 optional: tap [Add ticket photo] → camera → snap → done
06:33 tap [ENROUTE_TO_JOB]
06:54 arrive job → tap [ARRIVED_JOB]
06:56 tap [DUMPING]
07:01 tap [COMPLETE] → board automatically queues next ASSIGNED haul
07:03 tap [ENROUTE_TO_LOAD] for cycle 2…
…
8 cycles later: tap [OFF_SHIFT]
```

Total typing across an 8-cycle shift: **0 to 8 single-field touches** (material picker mostly Recent-tap; ticket photos are optional).

---

## Screen-by-screen walkthrough

### Screen 1 · Magic-link entry
**URL:** `/d/{token}` — opaque-token URL sent via SMS at start of shift.

```
┌──────────────────────────────────┐
│  MASCI · Dispatch Lifecycle      │
│  ──────────────────────────      │
│  Welcome, John                   │
│  Today: 8 cycles assigned        │
│                                   │
│  [TAP TO START SHIFT]            │
│                                   │
│  Need help? Call Carlos          │
│  386-322-4501                    │
└──────────────────────────────────┘
```

- Token expiration on the same day; dispatcher can re-issue.
- Phone-number-of-truck-boss displayed by default — the platform never tries to BE the truck boss.

### Screen 2 · Current state · the operational home

This screen is what the driver sees 95% of the day.

```
┌──────────────────────────────────┐
│  T-42  ·  Cycle 1 of 8           │
│  Project · SJR2C Loop Trail      │
│  Material · Asphalt              │
│                                   │
│  CURRENT STATE                   │
│  ┌────────────────────────────┐  │
│  │   ENROUTE_TO_LOAD          │  │
│  │   Started 06:01            │  │
│  │   Elapsed 0:22             │  │
│  └────────────────────────────┘  │
│                                   │
│  NEXT                            │
│  ┌────────────────────────────┐  │
│  │   AT_LOAD_SITE             │  │
│  │   (tap when you arrive)    │  │
│  └────────────────────────────┘  │
│                                   │
│  [WAITING ▼]   [BREAKDOWN]       │
│                                   │
│  ☰ History · Help · Off Shift    │
└──────────────────────────────────┘
```

- **One huge primary action button** = the next state.
- Two secondary buttons = wait state + breakdown.
- Bottom menu (collapsed) = history, help, off shift.

### Screen 3 · LOADED state (one extra tap for material)

```
┌──────────────────────────────────┐
│  Confirm LOADED                  │
│                                   │
│  Material                        │
│  ┌────────────────────────────┐  │
│  │ [Asphalt] (last 4 loads)   │  │
│  └────────────────────────────┘  │
│                                   │
│  Other materials:                │
│  [Dirt] [Millings] [Lime Rock]   │
│  [Aggregate] [Concrete] [...]    │
│                                   │
│  Ticket photo (optional)         │
│  [📷 Snap photo]                  │
│                                   │
│  [LOOKS RIGHT — LOADED]          │
└──────────────────────────────────┘
```

- First button = the material from the driver's last cycle (most common case).
- 8-10 buttons total — no dropdown, no typing.
- Photo is **optional**, never blocking.

### Screen 4 · Wait state sheet

When the driver taps **[WAITING ▼]**:

```
┌──────────────────────────────────┐
│  What are you waiting on?        │
│                                   │
│  [WAITING_ON_PLANT]              │
│  [WAITING_ON_LOADER]             │
│  [WAITING_ON_DUMP]               │
│  [WAITING_ON_PAVER]              │
│  [WAITING_ON_TRAFFIC]            │
│  [WAITING_ON_LANE_CLOSURE]       │
│  [WAITING_ON_ASSIGNMENT]         │
│  [STAGING]                       │
│  [Other — type 1-2 words]        │
│                                   │
│  [Cancel]                        │
└──────────────────────────────────┘
```

- 8 canonical wait reasons; one free-text fallback.
- Tapping any reason transitions to wait state; **timer starts immediately**.
- Driver returns to Screen 2; the primary button is now "Clear wait" → reverts to prior state.

### Screen 5 · Breakdown sheet

```
┌──────────────────────────────────┐
│  Breakdown — sorry to hear it.   │
│                                   │
│  What kind?                      │
│  [Mechanical]                    │
│  [Tire/Flat]                     │
│  [Hydraulic]                     │
│  [Electrical]                    │
│  [Other]                         │
│                                   │
│  Carlos has been notified.       │
│  Stay safe. Call if needed.      │
│                                   │
│  [I'm Safe — Submit]             │
└──────────────────────────────────┘
```

- Breakdown auto-notifies dispatch + shop (per `DISPATCH_NOTIFICATION_DISCIPLINE.md`).
- Voice is warm, not corporate.

### Screen 6 · History (collapsed by default)

```
┌──────────────────────────────────┐
│  Today's history                 │
│                                   │
│  CYCLE 1  06:01 → 07:01          │
│  • ENROUTE_TO_LOAD  06:01        │
│  • AT_LOAD_SITE     06:23        │
│  • LOADING          06:25        │
│  • LOADED · Asphalt 06:32        │
│  • ENROUTE_TO_JOB   06:33        │
│  • ARRIVED_JOB      06:54        │
│  • DUMPING          06:56        │
│  • COMPLETE         07:01        │
│                                   │
│  CYCLE 2  07:03 → in progress    │
│  • ENROUTE_TO_LOAD  07:03        │
│  • [WAITING_ON_PLANT 07:20-07:42]│
│  • AT_LOAD_SITE     07:42        │
│                                   │
│  [Mistake? Fix it →]             │
└──────────────────────────────────┘
```

- Read-only by default; "Fix it" action allows corrections that write to `state_history` (never overwrite).
- Provides operational confidence: the driver can see what was recorded.

---

## Ergonomic specifications

| Element | Target |
|---|---|
| Primary button height | ≥ 80 px |
| Secondary button height | ≥ 60 px |
| Tap target spacing | ≥ 16 px between touchable elements |
| Font size (state name) | 24 px bold |
| Font size (timer) | 18 px regular |
| Color contrast | WCAG AA min (4.5:1) for normal text, 3:1 for large |
| Sunlight readability | Tested at 40% brightness on white background |
| Glove-friendliness | Verified with Mechanix gloves (industry standard) |
| One-handed operation | Primary button reachable with thumb on 6.1" device |

These specs **inherit and extend** the Phase 6 mobile audit. Nothing here contradicts existing platform patterns.

---

## Bilingual coverage

Every screen ships EN + ES from day 1. Translation keys added to `i18n.js`:

| EN | ES |
|---|---|
| TAP TO START SHIFT | TOCAR PARA INICIAR TURNO |
| Cycle 1 of 8 | Ciclo 1 de 8 |
| What are you waiting on? | ¿Qué está esperando? |
| Breakdown — sorry to hear it. | Avería — qué mal. |
| Today's history | Historial de hoy |
| Need help? Call Carlos | ¿Necesita ayuda? Llame a Carlos |
| Looks right — Loaded | Correcto — Cargado |

Total new translation keys: ~80.

---

## Friction-removal principles

1. **No login screen.** Magic-link URL is the login.
2. **No password.** Token is opaque + signed + same-day-expiring.
3. **No "save" button.** Every action is atomic.
4. **No dropdowns.** Material pick = grid of 8 buttons.
5. **No free-text typing unless absolutely required.** Free text only for "Other wait reason" fallback (max 1-2 words).
6. **No multi-step forms.** Every screen = at most 1 question + 1 primary action.
7. **No "are you sure?" modals on normal transitions.** Trust the driver.
8. **One-tap correction available.** History → Fix it → revise.
9. **Optional photo never blocks submit.**
10. **Phone number of truck boss visible on every screen.** The platform supports the human chain, not replaces it.

---

## What the driver experience explicitly avoids

- ❌ A username + password field anywhere
- ❌ A "create account" flow
- ❌ A "forgot password" flow
- ❌ A "edit profile" surface
- ❌ A notification center / inbox
- ❌ A chat / message thread
- ❌ A map view of their own truck
- ❌ A leaderboard / scoring surface
- ❌ A multi-step form for any state transition
- ❌ A "Submit" button on any normal action (one-tap is the contract)
- ❌ Any required field beyond material picker (and even that defaults to last load)

---

## Driver experience success criteria

A driver should be able to complete one full haul cycle:
- in **< 6 total taps**
- in **< 30 seconds of in-app time**
- across **6 state transitions**
- with **0 typed characters**
- on a **390 px screen with gloves on**
- in **sunlight at 40% brightness**

This is the test. The first iteration ships if and only if it meets this contract.
