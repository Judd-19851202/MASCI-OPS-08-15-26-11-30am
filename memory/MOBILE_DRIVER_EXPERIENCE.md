# Mobile Driver Experience · Phase 11 · Document 7 of 10

**Date:** 2026-05-24
**Purpose:** The contract for what a driver experiences end-to-end on a phone, in a truck, with gloves on, in sunlight, sometimes without signal. Inherits Phase 6 mobile audit and Phase 5C/5C.1 compression discipline.

**Doctrine:** Tap and work. Nothing more.

---

## The contract (non-negotiable)

The driver experience MUST satisfy ALL of these criteria:

| Constraint | Value |
|---|---|
| Entry friction | Magic-link URL · 0 passwords · 0 account creation |
| Total taps per cycle | ≤ 6 |
| Total typed characters per cycle | 0 |
| Primary action button size | ≥ 80 px height |
| Secondary action button size | ≥ 60 px height |
| Reachable with one hand on 6.1" device | ✅ |
| Glove-friendly (Mechanix work gloves) | ✅ |
| Sunlight readable (40% brightness on white BG) | ✅ |
| Time from tap to network confirm | ≤ 5 s end-to-end |
| Works with patchy signal | ✅ (optimistic UI + retry queue) |
| Works in EN + ES from day 1 | ✅ |

If any criterion fails, the iteration does not ship.

---

## Entry · the magic link

### How the driver gets in

1. Dispatcher creates assignment OR refreshes driver's session.
2. Backend mints an opaque token, valid for the dispatcher's working day window (e.g., 06:00–22:00 local).
3. Backend sends SMS via existing notification surface: `MASCI Dispatch · Tap to start: https://app.masci.com/d/{token}`
4. Driver taps. Browser opens. They are in.

### Why magic-link (and not a portal account)

| Approach | Verdict | Reason |
|---|---|---|
| Magic-link via SMS | ✅ Chosen | Industry-standard for field/mobile workforces. 0 passwords. Works on any phone. |
| Full portal account + password | ❌ Rejected | Password reset chaos. Per-driver setup time. Adoption death. |
| Per-truck shared password | ❌ Rejected | No accountability; audit trail breaks. |
| QR code launched from dispatch board | 🟡 Possible add-on | Useful for shift handoff; not the primary entry. |
| Native mobile app | ❌ Rejected | App store overhead. Forced update cycles. Adoption tax. |

The magic-link approach was used successfully in the existing FL portal (Phase 5D) and is the platform's de facto pattern for low-friction field access.

### Token security

- Opaque random 32-byte tokens.
- Signed (HMAC) to prevent forgery.
- Stored in `dispatch_driver_sessions` (see architecture doc).
- Expire end-of-day; dispatcher can re-issue.
- Single-use per shift: rotating tokens is more disruption than benefit. The session document tracks `last_seen_at` for audit.
- Compromised token recovery: dispatcher invalidates + re-issues in < 10 seconds.

---

## Screens · referenced from `DRIVER_WORKFLOW_MAP.md`

All 6 driver screens (Magic-link entry · Current state · LOADED · Wait sheet · Breakdown sheet · History) are specified there. This document specifies the **ergonomic + technical** contract per screen.

---

## Touch target standards

| Element | Minimum size | Spacing |
|---|---|---|
| Primary action button | 80 × 80 px (or 80 px tall full-width) | 24 px below |
| Secondary action button | 60 × 60 px | 16 px below |
| Material picker tile | 60 × 60 px each, 4-across grid | 12 px gap |
| Wait reason tile | 60 × 60 px each, full-width stack | 12 px gap |
| Close / cancel | 44 × 44 px | 16 px from edge |

Targets exceed Apple HIG (44 × 44 px) and Material Design (48 × 48 px) standards by 30-80% to account for gloves + truck motion.

---

## Typography

| Element | Size | Weight |
|---|---|---|
| Current state name | 24 px | bold |
| Timer / elapsed | 20 px | regular |
| Cycle number + project | 18 px | regular |
| Material name | 18 px | semibold |
| Primary button label | 20 px | bold uppercase |
| Secondary button label | 16 px | bold |
| Helper text | 14 px | regular |
| History row | 14 px | regular |

All sizes hold their contrast ratio at sunlight 40% brightness on white background.

---

## Color discipline (inherits Phase 5D/6/7 platform tones)

| State category | Tone |
|---|---|
| Active in-progress states (ENROUTE, LOADING, DUMPING) | slate-700 background, white text |
| Complete states | emerald-700 |
| Wait states under threshold | amber-600 |
| Wait states over hard threshold | rose-700 |
| Breakdown | red-700 (existing platform danger color) |
| Hold | slate-500 |
| Off shift | slate-300 |

No new color tokens introduced. Platform palette stays consistent across portals.

---

## Optimistic UI + signal resilience

Drivers in trucks have variable cell signal. The DLS must feel instant.

### Pattern · Optimistic UI

1. Driver taps `[ENROUTE_TO_LOAD]`.
2. UI **immediately** updates to the new state (no spinner).
3. Network request fires in background.
4. On success: silent (the UI already reflects truth).
5. On failure: small slate banner appears `Tap not synced · retrying...`; queue persists.
6. On retry success: banner fades; UI stays accurate.
7. On retry fail (5 attempts over 60 s): rose banner `Sync failed · tap to retry`; driver action visible but recoverable.

### Pattern · Retry queue

- Failed state transitions stored in `localStorage` as a queue.
- Queue retries on next online event + every 15s while offline.
- Idempotency keys ensure no double-write on retry.

**Cost of an in-tunnel transition: 0 driver experience disruption.**

### Pattern · Draft persistence for ticket photos

- Photos are taken in-browser via `navigator.mediaDevices.getUserMedia()` or camera input.
- Compressed to ≤ 200 KB via the existing platform photo compression helper.
- Stored in `localStorage` as base64 until upload succeeds.
- Upload retries every 30s while offline.

**A photo taken in a tunnel uploads when signal returns. The driver doesn't think about it.**

---

## Accessibility

Beyond ergonomic + signal handling, the driver experience meets the platform's existing accessibility standards:

- WCAG 2.1 AA contrast on all text.
- Native keyboard never required (and therefore never wrong-toggled on by mistake).
- VoiceOver / TalkBack labels on every button.
- `data-testid` on every interactive element for testability.
- Bilingual switching via existing `t()` helper.
- No animations that violate `prefers-reduced-motion`.

---

## Empty / edge states

### Driver opens link · no active assignment yet

```
┌──────────────────────────────────┐
│  Hi John                         │
│  No active assignment yet.       │
│                                   │
│  Carlos will text you when       │
│  the first haul is ready.        │
│                                   │
│  [Refresh]                       │
└──────────────────────────────────┘
```

### Driver opens link · token expired

```
┌──────────────────────────────────┐
│  Session expired.                │
│  Text Carlos for a fresh link.   │
│                                   │
│  [Call 386-322-4501]             │
└──────────────────────────────────┘
```

No re-login flow. The platform supports the human chain.

### Driver opens link · device offline

```
┌──────────────────────────────────┐
│  Offline                         │
│  Last synced 0:14 ago.           │
│                                   │
│  You can still tap state         │
│  changes — they'll sync when     │
│  signal returns.                 │
│                                   │
│  [Try Now]                       │
└──────────────────────────────────┘
```

The platform tells the truth about offline state.

---

## What the driver can NEVER do (by design)

- ❌ Change another truck's assignment
- ❌ See another truck's state
- ❌ See another driver's history
- ❌ See the dispatcher board
- ❌ Generate any reports
- ❌ Adjust geofences or thresholds
- ❌ See compensation or scoring data about themselves
- ❌ Be presented with ads or "tips" or upsells

The driver experience is **exactly one thing**: log what I'm doing.

---

## Bilingual specifics

EN ↔ ES parity for every driver-facing string. Sample set:

| EN | ES |
|---|---|
| Tap to start shift | Tocar para iniciar turno |
| Cycle 1 of 8 | Ciclo 1 de 8 |
| Current state | Estado actual |
| Next | Siguiente |
| Tap when you arrive | Tocar al llegar |
| Loaded · Asphalt | Cargado · Asfalto |
| What are you waiting on? | ¿Qué está esperando? |
| Sync failed · tap to retry | Sincronización fallida · tocar para reintentar |
| Session expired | Sesión expirada |
| Call Carlos | Llamar a Carlos |

Driver can switch language at any time via a small flag toggle in the bottom menu.

---

## Performance targets

| Metric | Target |
|---|---|
| First contentful paint (cold) | < 1.5 s on 4G |
| First contentful paint (warm via service worker) | < 600 ms |
| Bundle size for DriverShell | < 80 KB gzip |
| State transition end-to-end (optimistic) | < 100 ms perceived |
| State transition end-to-end (server confirm) | < 5 s |
| Photo capture → compressed → ready | < 3 s |
| Photo upload (200 KB on 4G) | < 5 s |
| Total daily data usage per driver | < 10 MB / shift |

---

## What the first iteration ships

| Component | Status |
|---|---|
| Magic-link entry flow | ✅ Ship |
| 6 primary screens | ✅ Ship |
| Optimistic UI + retry queue | ✅ Ship |
| Ticket photo capture (optional) | ✅ Ship |
| Bilingual EN+ES | ✅ Ship |
| Offline state messaging | ✅ Ship |
| Mock-tested at 390 px in sunlight + gloves | ✅ Required before ship |
| Service worker for warm cache | 🟡 Phase 11.2 |
| QR-code-launched magic link (instead of SMS) | 🟡 Phase 11.2 |
| Voice command for state transitions | ❌ Not ever (per `DO_NOT_BUILD_YET.md`) |

---

## Conclusion

The driver experience is a single, opinionated mobile surface. Magic-link entry. One screen of operational truth. Two secondary actions (wait + breakdown). Optimistic UI + retry queue for signal resilience. Bilingual from day 1.

The contract is testable: ≤ 6 taps per cycle, 0 typed characters, ≤ 5 second end-to-end confirmation. If the first iteration meets the contract, the platform delivers on its driver-experience promise.
