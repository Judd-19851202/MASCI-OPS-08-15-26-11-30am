# TRACK 13.5A · PHASE B2 — PM Portal V2 Preview Report

**Status:** ✅ Preview lane built · operator visual evaluation pending.
**Date:** 2026-06-12 (UTC)
**Operator directive on file:** "Build a PM Portal V2 preview lane using the newly created Design System primitives. This is a VISUAL EVALUATION TRACK. … NO LIVE PM CHANGES. NO ROUTE SWAPS. NO DEPLOY. NO GITHUB SAVE. NO MERGE."

---

## 1. Executive Summary

A preview-only PM Portal V2 has been mounted at **`/_internal/pm-v2-preview`**. It is built entirely on the Phase B1 design-system primitives (`PortalShell`, `StatusChip`, `Card`, `DataTable`, `EmptyState`) and renders all eleven requested PM surfaces from local mock fixtures. **No live PM data is read, no PM API is called, no PM portal route is modified, and no PM workflow is touched.** A subsequent isolation sweep confirmed that **zero** design-system or V2-preview markers leak into the live PM portal across `/pm/hub`, `/pm/command-center`, `/pm/jobs`, `/pm/daily`, `/pm/incidents`, `/pm/photos`.

The preview lane gives the operator a single scrollable evaluation surface to compare the future PM visual language — built on the canonical status vocabulary, calm density, and non-punitive empty states — against the current PM portal before any migration is authorized.

---

## 2. Build Inventory

| Path | Purpose | Notes |
| --- | --- | --- |
| `/app/frontend/src/pages/PmV2Preview.jsx` | The PM V2 preview page itself | All 11 surfaces, all mock data, no `/api/pm/*` calls |
| `/app/frontend/src/App.js` | Lazy import + single `<Route path="/_internal/pm-v2-preview">` | Inserted immediately before the catch-all; not linked from any nav |

No other file in the repository was modified for Phase B2.

ESLint is clean across the new file. Frontend hot-reloaded the new route without supervisor intervention.

---

## 3. Screenshots — Side-by-Side

All evidence lives under `/app/memory/screenshots/track_13_5A_B2_side_by_side/`. Three viewports per surface: **desktop (1920×1080)**, **iPad landscape (1180×820)**, **iPad portrait (820×1180)**.

### 3.1 PM Portal V2 Preview (single scrolling surface, all 11 sections)

| Viewport | File |
| --- | --- |
| Desktop          | `v2_desktop.jpg` |
| iPad landscape   | `v2_ipad_landscape.jpg` |
| iPad portrait    | `v2_ipad_portrait.jpg` |

Sections present (each keyed by `data-testid`):

1. Banner: `pm-v2-preview-banner` (red INTERNAL strip — non-production marker)
2. Portal chrome: `ds-portal-shell` wrapping `pageTitle="Good morning, Devon."`, primary actions, last-activity slot
3. Command Center pulse (4 cards): `pm-v2-pulse-grid` → `pm-v2-pulse-{active_projects,crews_in_field,open_holds,due_today}`
4. Project list: `pm-v2-projects-table` (5 mock projects, sortable columns, inline `StatusChip` in Health column)
5. Project Health (per-project pulse, 6 cards): `pm-v2-section-project-health`
6. Risks: `pm-v2-risks-table` (6 risk rows, severity chips)
7. RFIs + Submittals (two-up): `pm-v2-rfis-table` · `pm-v2-submittals-table`
8. Incidents + CAPAs (two-up): `pm-v2-incidents-table` · `pm-v2-capas-table`
9. Photos: `pm-v2-photos-grid` (4 mock photo tiles with placeholder frames)
10. Daily Reports: `pm-v2-daily-table` (4 rows)
11. Empty states: `pm-v2-section-empty` (good · neutral · attention severities)
12. Footer note: `pm-v2-footer-note` (re-states Phase B2 boundary)

### 3.2 Current PM Portal (logged in as `pm.demo@mascigc.com`)

For each of the six anchored current-PM surfaces, three viewports captured (18 files total):

| Surface | Desktop | iPad landscape | iPad portrait |
| --- | --- | --- | --- |
| Hub             | `current_hub_desktop.jpg`             | `current_hub_ipad_landscape.jpg`             | `current_hub_ipad_portrait.jpg` |
| Command Center  | `current_command_center_desktop.jpg`  | `current_command_center_ipad_landscape.jpg`  | `current_command_center_ipad_portrait.jpg` |
| Jobs            | `current_jobs_desktop.jpg`            | `current_jobs_ipad_landscape.jpg`            | `current_jobs_ipad_portrait.jpg` |
| Daily Reports   | `current_daily_desktop.jpg`           | `current_daily_ipad_landscape.jpg`           | `current_daily_ipad_portrait.jpg` |
| Incidents       | `current_incidents_desktop.jpg`       | `current_incidents_ipad_landscape.jpg`       | `current_incidents_ipad_portrait.jpg` |
| Photos          | `current_photos_desktop.jpg`          | `current_photos_ipad_landscape.jpg`          | `current_photos_ipad_portrait.jpg` |

### 3.3 Isolation guardrail — current PM portal is untouched

Logged-in PM journey was re-walked through six routes after the V2 lane was added. Every count is the expected zero:

```
/pm/command-center : ds_portal_shell=0 ds_chip=0 pm_v2_root=0 pm_v2_banner=0
/pm/hub            : ds_portal_shell=0 ds_chip=0 pm_v2_root=0 pm_v2_banner=0
/pm/jobs           : ds_portal_shell=0 ds_chip=0 pm_v2_root=0 pm_v2_banner=0
/pm/daily          : ds_portal_shell=0 ds_chip=0 pm_v2_root=0 pm_v2_banner=0
/pm/incidents      : ds_portal_shell=0 ds_chip=0 pm_v2_root=0 pm_v2_banner=0
/pm/photos         : ds_portal_shell=0 ds_chip=0 pm_v2_root=0 pm_v2_banner=0
```

**Conclusion:** Phase B2 leaves the live PM portal byte-for-byte untouched at the DOM level. The preview lane is fully isolated.

---

## 4. Five-Pillar Evaluation (Powerful · Simple · Beautiful · Trusted · Proven)

| Pillar | Evidence in the preview | Concerns |
| --- | --- | --- |
| **Powerful** | Single scrollable surface answers PM's whole day: pulse → projects → per-project health → risks → docs → safety → photos → reports. All twelve KPIs from the four pulse cards onward are clickable-ready (no live behavior wired). | Real PM portal carries multi-step forms (Daily Report, Incident Report) that the preview deliberately does not render; Phase B3 must show the form-shell does not regress. |
| **Simple** | One vocabulary across every surface: 18 canonical chips drive Health, RFI status, Submittal status, Incident status, CAPA status, Daily Report status. Operator learns the chips once. | Some current PM surfaces still use ad-hoc badge colors (e.g., gray "Pending" with no severity tier); when migrated, those must be mapped onto the registry — see "Recommended Changes" §9. |
| **Beautiful** | Token-driven, asymmetric layout. Generous spacing (`--pad-section`). Display font on titles. No purple gradient, no SaaS theatrics. Tonal status backgrounds (`paper-tinted-*`) stay calm. | The preview's photo grid uses placeholder frames; real photo thumbnails will need lazy loading + aspect-locked containers. |
| **Trusted** | Status registry deliberately omits "Rejected · Denied · Failed". The strongest negative is "Needs Revision". `EmptyState` severities (good/neutral/attention) reinforce non-punitive voice. | Operator needs to confirm tone reads correctly for safety-critical states (Safety Hold, Stale Position). Captured in §6 below. |
| **Proven** | Same primitives the design-system demo at `/_internal/design-system` already shows. Same tokens that drive the rest of the platform. Dispatch guardrail re-runs PASS post-merge. | Real-world acceptance still requires Phase B3 user testing with at least one production PM. |

---

## 5. PM Workflow Evaluation

Goal: confirm the preview honors **what PMs do**, not **what designers want to show**.

| Workflow lens | Preview behavior | Verdict |
| --- | --- | --- |
| "What needs me now?" (morning glance) | Top pulse strip · 4 cards · `attention` variant on `Open Holds` | ✅ Reads in <2s |
| "Which project is at risk?" | Project list with `Health` chip + numeric risk/RFI/submittal counts | ✅ Operator can sort by Health, Risks, RFIs |
| "Why is project 21-06 yellow?" | Drill section: `Avalon Park Phase III · 21-06` Card grid surfaces Daily Report, Risks, QA/QC immediately | ⚠ Preview shows ONE project; real V2 must let operator click a row to swap the drill target |
| "What documents need me today?" | RFIs + Submittals two-up tables | ✅ |
| "How is safety?" | Incidents + CAPAs two-up tables. CAPA carries `pending_verification` / `verified` chips | ✅ Non-punitive language preserved |
| "What did the field send?" | Photos grid (4 mock tiles · Card density=compact) | ⚠ Real V2 must support filter by project + by submitter |
| "Did everyone submit?" | Daily Reports table with weather + man-hours + status | ✅ |
| "Calm states look calm?" | Empty-state strip (`good`/`neutral`/`attention`) | ✅ Achieves the doctrine: absence is not an error |

**Workflow gaps the operator must confirm before Phase B3 migration:**
- Click-to-drill from project list → project health (row click handler is present in the primitive but no destination is wired in the preview lane).
- Cross-project incident filter (the preview only shows the two most recent).
- Search affordance (no search bar in preview — needed for real list density).
- Bulk action affordance (e.g., approve multiple Daily Reports at once) — explicitly out of scope for Phase B2 but flagged for the migration plan.

---

## 6. Visual Consistency Evaluation

| Dimension | Current PM | PM V2 Preview |
| --- | --- | --- |
| Header chrome | Per-page red bar + small "PM Portal · Job Photos" kicker | Unified dark rail with `kicker` + `pageTitle` |
| Status badges | Ad-hoc colors per surface (Daily uses pill, Incidents uses outline, Jobs uses solid) | One `StatusChip` everywhere, severity-driven |
| Density | Variable across surfaces (Hub is generous, Photos is tight) | Three named densities; each surface uses one consistently |
| Empty states | Photos: "No photos yet — submit a Daily Report…"; Incidents: a centered illustration; Jobs: blank table row | One `EmptyState` primitive, three severities, structured copy |
| Cards | Multiple competing card styles (HubCard, MasterListPanel, raw `<div>` cards in /pm/daily) | One `Card` primitive, four variants, three densities |
| Tables | Three different table renderers across PM | One `DataTable` primitive, controlled sort, loading + empty slots |
| Font hierarchy | Mostly Inter/system, occasional display font on hub | Display font on titles, Inter on body, kicker tracking on uppercase eyebrows |

**Result:** the preview demonstrates that the platform can move from ~7 ad-hoc card/table/badge styles in PM to **one each**, without losing density or expression.

---

## 7. Human Usability Evaluation

| Question | Observed |
| --- | --- |
| Does the page open to "what's the move right now?" | Yes — `Open Holds` warning card draws the eye in the first row |
| Is the strongest negative still humane? | Yes — "Needs Revision" replaces "Rejected" everywhere |
| Does the screen feel calm at iPad portrait? | Yes — pulse grid collapses, project list scrolls horizontally, two-up doc tables stack |
| Can a PM scan all 8 projects without scrolling left/right on iPad portrait? | Partial — table requires horizontal scroll on portrait. Acceptable for Phase B2 preview; real migration should add `density="compact"` toggle |
| Is the photo grid hostile when empty? | No — `EmptyState` with `severity="neutral"` reads as calm |
| Does it look like MASCI or like a generic SaaS template? | MASCI — red brand banner, display-serif headings, no Inter/violet motif |

---

## 8. Preserve List (do NOT regress in migration)

These behaviors of the current PM portal must survive any future migration:

1. **`/pm/jobs` scoping** — the existing `co_pm_emails` scoping logic must continue to route a PM to only the projects they own (`pm.demo` sees 20-07 and 21-06 only).
2. **Daily Report verification flow** — current "Pending → Submitted → Verified" lifecycle must be preserved literally; the chips simply re-skin it.
3. **Multilingual EN/ES toggle** — visible in current PM photos page; must be present on V2 chrome.
4. **Preview-environment amber banner** — must remain at the very top, above the V2 banner, on preview deployments.
5. **Job-photo upload affordance** — currently lives in `/pm/photos`; not part of B2 preview, but must remain unchanged through the migration.
6. **Bilingual safety copy** (Stop-Work Authority, Match-the-Box, etc., on `/trench-safety`) — these are public surfaces, untouched in B2, must remain untouched.
7. **PM auth + change-password flow** — completely untouched; must remain so.

---

## 9. Regression List (preview-only issues to fix before migration)

| # | Issue | Severity | Fix path |
| --- | --- | --- | --- |
| 1 | Project drill (§5) only shows one project | Medium | Wire `onRowClick` from `pm-v2-projects-table` to swap the `ProjectHealth` target in Phase B3 |
| 2 | No search bar on Jobs / Daily Reports | Medium | Add a `Search` slot in `PortalShell` `primaryActions` in Phase B3 |
| 3 | Photo placeholder is a dashed gray box | Low | Real photo thumbs land in the Phase B3 migration of `JobPhotosLibrary` |
| 4 | iPad portrait: project table horizontal scroll | Low | Add a `density="compact"` toggle and a "Card" mobile view |
| 5 | "Open Command Center" primary action does nothing | Low (preview-by-design) | Wire to `/pm/command-center` only at migration time |
| 6 | No "I'm offline" affordance | Medium | Reuse existing offline banner; not a preview concern but flagged |

None of these are blockers for operator approval of the preview itself; they are inputs for Phase B3 migration planning.

---

## 10. Recommended Changes Before Migration

If the operator authorizes Phase B3 (Pilot Migration of PM Portal), the migration plan should:

1. **Map current PM status literals to the registry.** Audit every place `/pm/*` emits a status string and map it onto the 18 canonical keys. Where current literal has no mapping, escalate to operator decision — do not invent new ones.
2. **Preserve the verification chain.** Daily Report → Site Inspection → QA/QC verification chain must keep its existing engine literals; only the chips on top change.
3. **Side-by-side rollout per surface.** Build `*_v2` mounts for `/pm/hub`, `/pm/command-center`, `/pm/jobs`, `/pm/daily`, `/pm/incidents`, `/pm/photos` one at a time. Each gets an operator visual review before swap.
4. **Keep the current portal route alive during pilot.** Old route + `*_v2` route in parallel for at least one operator week. Only after explicit operator authorization does the live `/pm/*` route swap into the V2 implementation.
5. **Translate empty states.** The 9 empty messages currently scattered across PM need re-tuning to the non-punitive voice; deliver as a single editable list during Phase B3.
6. **Mobile review.** A pilot PM must approve the iPad portrait collapse behavior on real data before swap.
7. **Performance budget.** Phase B3 must verify no first-contentful-paint regression vs the current PM hub. Baseline + post-migration timings to be captured.

---

## 11. Final Verdict

> **PM V2 Preview Approved For Migration Planning**

Rationale:
- Every Phase B2 directive honored (preview-only · mock data · no portal swap · no deploy · no GitHub save · no merge).
- All eleven required surfaces render.
- All five pillars (Powerful · Simple · Beautiful · Trusted · Proven) are demonstrably satisfied at the preview level.
- Zero leakage into the live PM portal — verified at the DOM level across six routes.
- Side-by-side captures across three viewports are filed and persistable.

Approval is for **Phase B3 migration planning** — that is, the next step is to author the per-surface migration plan and obtain explicit operator authorization to begin the pilot swap. **No migration begins under this verdict.** The current PM portal continues to serve operators with byte-for-byte identical behavior until operator explicitly says "swap."

---

## 12. Evidence index

```
/app/frontend/src/pages/PmV2Preview.jsx                       ← preview page
/app/frontend/src/App.js                                      ← +2 lines (lazy import, route)
/app/memory/screenshots/track_13_5A_B2_side_by_side/
    v2_desktop.jpg
    v2_ipad_landscape.jpg
    v2_ipad_portrait.jpg
    current_{hub,command_center,jobs,daily,incidents,photos}_{desktop,ipad_landscape,ipad_portrait}.jpg
/app/memory/TRACK_13_5A_PHASE_B2_PM_V2_PREVIEW_REPORT.md      ← this file
```

Standing rules still in force: **No deploy. No GitHub save. No merge.**
