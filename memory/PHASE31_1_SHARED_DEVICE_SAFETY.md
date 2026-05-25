# PHASE 31.1 · Shared Device Safety

_iter437 · 2026-05-25_

## The threat model

The MASCI Daily Report is filed from MANY device contexts:
- A foreman's personal iPhone
- A shared trailer iPad (multiple crews touch it across a week)
- A truck-mounted rugged tablet (whole shift uses it)
- A spare phone at the office
- A bench tablet at the shop

Phase 31.1 must NEVER let crew A's setup silently leak onto crew B's
form just because they grabbed the same iPad.

## How crew-memory protects shared devices

### 1. NEVER silent auto-fill
The Daily Report form NEVER reads the saved setup and applies it
automatically on mount. It ALWAYS goes through the calm restore
prompt: **Use Setup · Start Blank · Clear Saved Setup**. The wrong
operator always has a clean exit (Start Blank) and a hygiene exit
(Clear Saved Setup) without ever seeing the prior crew's data
applied.

### 2. The prompt shows what's about to be loaded
The prompt surfaces a calm summary BEFORE any field is touched:
> Oxford Resurfacing 2026 · 3 crew members · 1 subcontractor · 2 equipment items

An operator who sees an unfamiliar project name or unfamiliar crew
count immediately knows to tap **Start Blank** or **Clear Saved Setup**.

### 3. Optional nickname makes ownership explicit
The optional nickname chip (e.g. "Paving Crew A", "Airport Night
Crew") lets operators self-label setups on a shared device. When
someone else picks up the device and sees "PAVING CREW A · SAVED
YESTERDAY", the ownership is obvious. This is doctrine, not analytics.

### 4. Clear Saved Setup is a first-class button
Not buried in a settings menu, not hidden behind a confirm dialog —
right there next to **Use Setup**. The operator chooses.

### 5. Calm coaching microcopy
The prompt itself contains the discipline in plain language:

> _Saved setups stay only on this device. Use this option only if
> this is your crew device or personal device._

> _You can edit crew and equipment after loading. Starting blank will
> not erase previously submitted reports._

### 6. Banned fields are stripped at save time, not at load time
A defensive `extractSetupSnapshot()` runs INSIDE `saveCrewSetup()`,
not just at the call site. Even if a future iteration accidentally
passes the full form payload (`saveCrewSetup(payload)` — exactly
what `pages/NewDailyReport.jsx` does today), the stored record holds
ZERO banned fields. Notes / signatures / weather / incidents / GPS /
photos all dropped at the write boundary.

### 7. 30-day TTL with rolling expiration
Saved setups expire 30 days after the last save. Each "Use Setup"
refreshes `lastUsedAt`, but the underlying 30-day window from
`savedAt` is the hard cap unless a fresh save occurs. A trailer iPad
that sits in a yard for 5 weeks comes back blank.

### 8. Schema version pin
The persisted record carries `schemaVersion: 1`. Any future change
to the snapshot shape bumps the version and the loader silently
drops old records. There is no "best effort" migration — operators
get a clean blank instead.

## What this does NOT protect

- **Auth boundary**: this is a UX hygiene boundary, NOT a security
  boundary. A determined attacker with physical device access can
  read `localStorage` via Safari DevTools. The defense is that the
  saved fields are ONLY non-sensitive setup data (no notes, no
  incidents, no signatures, no quantities) — by design.
- **Profile theft**: the saved record contains crew NAMES (which are
  not secret) and project NAMES (also not secret on a jobsite). It
  does NOT contain emails, phone numbers, addresses, payroll data,
  or any HR-protected attribute.
- **Cross-device**: nothing in this primitive syncs anywhere. Two
  devices have two independent stores; that is the entire point.

## Acceptance checklist (operator-owned)

Before declaring Phase 31.1 production-ready on a given device:
- [ ] Open Daily Report → confirm restore prompt appears with summary
- [ ] Tap Start Blank → form is empty
- [ ] Tap Use Setup → form fields populate · prompt clears
- [ ] Tap Clear Saved Setup → prompt clears · IDB key absent
- [ ] Refresh → no prompt (since cleared)
- [ ] File a real report → next morning · prompt offers it again

## Anti-scope

- ❌ NO biometric gate on the prompt
- ❌ NO "are you sure" double confirmation
- ❌ NO server log of who saw whose setup
- ❌ NO "shared device mode" toggle in settings
- ❌ NO multi-slot setup library (one slot per device · matches the
  spec example "yesterday's setup")
