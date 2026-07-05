# DR-ROI-001 · UI Flow

**Route:** `/daily-report/v2` (feature-flagged · V1 remains at `/new-daily-report`)

## Progressive shell — 10 sections + 4 panels

**Sections** (top-to-bottom):
1. Day Setup — project · date · shift · supervisor · weather · GPS
2. Crew Time — HR-linked (existing model preserved)
3. Equipment — existing model + minor extend
4. **Activity Cards** — new · replaces `activities[]`
5. **Constraint Chips** — new · replaces free-text delay narratives
6. **Tomorrow Readiness** — new
7. Safety / Quality — existing gates, simplified UI
8. Photos — existing min-6, linkable to Activity Cards
9. **AI Summary** — placeholder this session
10. Signature + Submit — existing signature flow

**Sticky panels** (right rail on desktop · collapsible drawer on tablet/phone):
- **Confidence Panel** — real-time AI confidence gauge
- **PM Intelligence Panel** — PM brief + action items preview
- **Photo Intelligence Panel** — Vision tags + activity-link suggestions
- **Supervisor Approval Panel** — accept / edit / regenerate controls

## Interaction principles

- **Field-first, narrative-last.** Supervisor enters structured facts; AI narrates.
- **Chip-driven enums.** Constraints, tomorrow needs, safety flags = single-tap chips.
- **Card-based repeating groups.** Activities are cards with area/quantity/photos/crew/equipment inline.
- **Live validation checklist.** Visible at all times · shows what blocks submit.
- **Sticky AI questions tray.** Max 3 at a time · dismissible with logged reason (stored in `dismissed_ai_suggestions[]`).

## Device targets

- **iPad** (primary) — glove-usable · large tap targets · sticky right rail becomes bottom-sheet in portrait
- **Phone** (secondary) — single-column stack · panels behind chip drawer
- **ToughBook / Windows tablet** (tertiary) — desktop-like right rail
- **Desktop** — PM read-out only · not the entry surface

## Time target (per directive)

- Normal day: **5–8 minutes**
- Complex day: still structured and manageable
- Explicit non-goal: 45-minute reports

*Details in `DR_ROI_001_CONSOLIDATED_PLANS.md § 4`.*
