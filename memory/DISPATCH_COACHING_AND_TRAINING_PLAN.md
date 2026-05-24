# Dispatch Coaching & Training Plan · Phase 11 · Document 8 of 10

**Date:** 2026-05-24
**Purpose:** Define the in-platform coaching surfaces that teach drivers and dispatchers to use the DLS confidently — without becoming a training bureaucracy.

**Doctrine:** Coach inside the workflow. Never make the user leave to learn.

---

## Coaching architecture inherits platform standards

All DLS coaching reuses the existing infrastructure:

| Pattern | Source phase | DLS application |
|---|---|---|
| LifecycleGuide component | Phase 5D | New guides for Dispatch Lifecycle, Wait States, Cycle Time |
| Operational glossary | Phase 5D | 13 new canonical entries (one per state) + 9 wait sub-states |
| Field-direct voice | Phase 5C/6/7 | Same voice; no new language |
| Banner pattern (slate/amber/rose/emerald) | Phase 6 | Reused for state status |
| EN+ES bilingual | Phase 5C onward | Required for all new strings |
| "What this means" deep-links | Phase 5D | Banner → glossary anchor |

**No new coaching infrastructure invented.** The DLS is built ON the existing teaching surfaces.

---

## Glossary entries · 13 new canonical states + 9 wait sub-states

Each entry follows the established 4-section format (Operational meaning · Lifecycle meaning · Accountability · Downstream visibility). Sample sketches below; full text written when the glossary file is updated.

### State: ASSIGNED
- **Operational:** Dispatcher has placed a haul on this truck. The driver has not yet acknowledged it.
- **Lifecycle:** Entry point of every haul cycle. Transition to ENROUTE_TO_LOAD when the driver moves.
- **Accountability:** Dispatcher owns assignment. Driver owns the transition out.
- **Downstream:** Visible on the Dispatch Board and the driver's mobile screen the moment it's created.

### State: WAITING_ON_PLANT
- **Operational:** Driver is at the asphalt/concrete plant but the plant isn't ready. Production hasn't started yet — only the wait clock has.
- **Lifecycle:** Entered from AT_LOAD_SITE or LOADING. Exits back to whichever state was before it.
- **Accountability:** Driver claims the cause; dispatcher sees the duration. Soft alert at 30 min, hard at 60 min.
- **Downstream:** Plant capacity intelligence + PM change-order data + Convergence Score input.

### State: OPERATIONALLY_COMPLETE (cycle-level)
- **Operational:** Haul cycle finished. Truck is empty and ready for the next assignment.
- **Lifecycle:** Terminal for this cycle. Spawns nothing; dispatcher creates next ASSIGNED if needed.
- **Accountability:** Driver owns the COMPLETE tap; dispatcher confirms the loop closed.
- **Downstream:** Cycle time computation finalizes; data flows to analytics.

**All 22 entries (13 states + 9 wait sub-states) follow this pattern.** Estimated content: ~150 lines of glossary copy.

---

## LifecycleGuide instances · 4 new guides

### Guide 1 · Dispatch Lifecycle Guide
**Where it appears:** Top of `DriverShell` (collapsed by default) + top of `DispatchBoard` (collapsed)
**Content (English):**
- *Why this matters:* "Every haul moves through the same 13 states. Tap the right state and the dispatcher sees you live."
- *What you can do:* "Three taps per state change. The driver is the source of truth — Motive only confirms it."
- *Downstream:* "Cycle time + wait analytics + change-order data all flow from your taps. Tap accurately."

### Guide 2 · Wait State Guide
**Where:** Inside the wait-reason sheet (collapsed; expands on first use)
**Content:**
- *Why this matters:* "Capturing 'why we waited' is how we recover lost time on the next bid."
- *What you can do:* "Pick the closest reason. 'Other' is fine when nothing fits — type 1-2 words."
- *Downstream:* "Plant + paver + lane-closure waits roll up to the PM's change-order data."

### Guide 3 · Cycle Time Coaching
**Where:** Driver's history screen + dispatcher's row drawer
**Content:**
- *Why this matters:* "Cycle time = total time per load. Steady cycle time = steady production."
- *What you can do:* "If a cycle is wildly different than usual, the history will tell us why — a 30-min plant wait, a paver pause, a breakdown."
- *Downstream:* "Estimating uses last quarter's actual cycle times to bid next quarter's work."

### Guide 4 · Ticket Photo Coaching
**Where:** LOADED confirmation screen (collapsed; expands inline)
**Content:**
- *Why this matters:* "Plant ticket photos are insurance against billing disputes."
- *What you can do:* "Optional — only snap when the ticket has a number worth recording."
- *Downstream:* "PM's billing reconciliation pulls ticket photos in cycle order."

**Total LifecycleGuide additions: 4 new instances. Platform total = 12.** (Was 8 after Phase 5D; +4 here.)

---

## Trust Coaching (the soft layer)

Beyond explicit guides, the platform's voice itself teaches trust:

| Surface | Trust message | When |
|---|---|---|
| Driver state confirmation | `Saved · Carlos can see this now` | After every state transition |
| Driver offline indicator | `Offline · taps will sync when signal returns. Already saved on this phone.` | When connectivity drops |
| Driver session expiration | `Session expired. Text Carlos — he can refresh in 10 seconds.` | When magic-link runs out |
| Dispatcher reassignment | `Reassigned to T-44. John has been notified via SMS.` | On reassignment |
| Wait threshold hit | `T-43 at WAITING_ON_PLANT for 30 min. This is data for the next bid.` | When soft threshold crosses |

Trust coaching is voice, not content. It's the difference between corporate software and operational software.

---

## Training integration · existing platform training catalog

The platform's training catalog (`frontend/src/data/training.js` + `routes/safety_portal/training.py`) gets one new short module:

### Training: "Dispatch Lifecycle Basics" (10 minutes)
- **Audience:** All drivers + truck bosses
- **Format:** 5-page in-platform walkthrough (NOT a video — videos rot)
- **Acknowledgment:** Single click `I understand` button stores acknowledgment in `training_records`
- **Bilingual:** EN + ES from day 1
- **Refresher cadence:** Annual or when state machine changes

Pages:
1. Why we replaced text groups with the lifecycle system
2. The 13 states and how to tap them
3. Wait states — what to pick and why it matters
4. Breakdown + hold — the calm path
5. Trust + accountability — what the dispatcher sees

**This training is NOT mandatory before first use.** The platform is designed for tap-and-work. Training is an "if you want to understand the why" surface, not a gate.

---

## Help line · the human chain

Every driver-facing screen displays:

```
Need help? Call Carlos · 386-322-4501
```

The platform supports the human chain. The driver always has a human number to call. The platform never tries to be the help desk.

---

## Onboarding new drivers

### First-shift onboarding (no platform overhead)

1. Truck boss adds driver to platform (`/dispatch-portal/drivers/new`) — 60 seconds.
2. Driver receives SMS with their first magic link 5 minutes before shift start.
3. Driver taps link, sees `[TAP TO START SHIFT]`, taps it.
4. Driver is in. No password. No setup. No tutorial.

### Optional onboarding video (recorded by MASCI internally, hosted in training catalog)

- 3-minute internal training video
- Voiceover available in EN + ES
- Linked from the first-shift entry screen with a `Watch the 3-minute walkthrough` link
- Driver can skip; the platform doesn't gate on it

---

## Coaching for dispatchers

Dispatchers have richer information needs than drivers. Their coaching surfaces:

### LifecycleGuide on Dispatch Board (collapsed by default)
- *Why this matters:* "Every row is a truck. Every state is one tap of truth from the driver. Your job: see bottlenecks before they cascade."
- *What you can do:* "Reassign · Hold · Cancel cycle. Call the driver via tel: link if needed."
- *Downstream:* "Cycle times + wait totals feed PM change orders and next quarter's estimating."

### LifecycleGuide on row drawer
- *Why this matters:* "Every state change has a timestamp + author. This is the audit truth."
- *What you can do:* "If the state is wrong, edit via the driver-side 'Fix it' — never overwrite history."

### Dispatch glossary surface
- The 22 new glossary entries are reachable from the dispatcher's banner deep-links.
- "What this means →" link present on every wait threshold alert + breakdown alert.

### Training: "Dispatch Lifecycle for Truck Bosses" (15 minutes)
- Audience: Truck bosses + dispatch leads
- Same format as driver training (in-platform walkthrough)
- Covers: reading the board · responding to wait alerts · using bottleneck findings · using CSV exports

---

## What this coaching plan explicitly does NOT do

- ❌ Mandatory training before first use (gates adoption)
- ❌ A "Learn" tab anywhere
- ❌ Videos hosted on the platform (videos rot; defer to MASCI's internal training tooling)
- ❌ Quiz-gated access (per `DO_NOT_BUILD_YET.md` § gamification)
- ❌ A help chatbot
- ❌ Walkthrough tooltips that follow the user around (annoying)
- ❌ A "feedback" widget on every screen
- ❌ A separate "documentation" page

The coaching IS the operational language. Inside the workflow. Quiet. Discoverable. Skippable when not needed.

---

## Success criteria for coaching

After 60 days of production:
- ≥ 80% of drivers should never have called Carlos for help with the platform (only for operational questions)
- ≥ 90% of drivers can articulate (in plain words) what "WAITING_ON_PLANT" means
- ≥ 100% of new drivers should be operationally productive within their first shift, without a formal training session
- 0 drivers should report feeling "buried in software"

If those targets hold, the coaching plan is working.

---

## Conclusion

DLS coaching is built ON the existing platform pedagogy: LifecycleGuide · operational glossary · field-direct voice · banner deep-links · in-workflow surfaces. The DLS adds 22 glossary entries, 4 LifecycleGuide instances, 2 training modules, and a voice discipline applied consistently across every state.

No new pedagogy. No new categories. No videos. No quizzes. No bureaucracy.

The platform teaches by being clear. That is the doctrine.
