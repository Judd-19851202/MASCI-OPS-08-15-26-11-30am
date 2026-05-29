# Form Spacing Doctrine

_Phase V.5 · Platform Form Layout · 2026-05-29 19:25 UTC._

> **Status**: ACTIVE · binding on every form, view-screen, and panel
> that renders user-facing inputs.
> **Owner**: Frontend platform.
> **Companion certifications**:
> `PLATFORM_FORM_LAYOUT_BLEED_AUDIT.md` ·
> `PLATFORM_FORM_GRID_FIX_CERTIFICATION.md` ·
> `IPAD_LAYOUT_VALIDATION_REPORT.md`.

## 1 · Why this doctrine exists

In 2026-05-29 the operator confirmed live iPad field bleed across
Daily Reports, Equipment / Operator forms, Safety Meetings, QA/QC
inspections, and several view screens. Investigation found that
**every form on the platform was using one of two near-identical
ad-hoc Tailwind grids**:

```html
<!-- BLEED-PRONE — DO NOT USE -->
<div className="grid grid-cols-1 sm:grid-cols-2 gap-3">…</div>
<div className="grid grid-cols-1 sm:grid-cols-2 gap-4">…</div>
```

The combination of (a) the `sm:` breakpoint (640 px), which packs two
inputs into ~310 px columns on small phones in landscape, and (b) the
12-px / 16-px gap, which leaves only 4–8 px of visually clear space
once iPad / iPadOS input chrome is rendered, produced the bleed.

## 2 · Canonical responsive contract

The platform uses **two** canonical responsive grids depending on
layout density:

### 2a · 2-col / 3-col (form rows, sparse grids)

| Viewport | Width | Layout | Horizontal gap | Row gap |
|---|---|---|---|---|
| Phone portrait | < 768 px | **1 column** | n/a | **16 px** |
| Phone landscape | < 768 px | **1 column** | n/a | **16 px** |
| iPad portrait | 768–1023 px | **2 columns** | **24 px** | **16 px** |
| iPad landscape | 1024–1279 px | **2 columns** | **24 px** | **16 px** |
| Desktop | ≥ 1280 px | **2 columns** | **24 px** | **16 px** |

Tailwind encoding:

```html
<div className="grid grid-cols-1 md:grid-cols-2 gap-x-6 gap-y-4">
<div className="grid grid-cols-1 md:grid-cols-3 gap-x-6 gap-y-4">
```

Equivalent component:

```jsx
import FormGrid from "@/components/FormGrid";
<FormGrid>…</FormGrid>
```

### 2b · 4-col / 5-col (dense filter bars, stats strips)

When a filter bar or stats strip needs to show 4 or 5 fields side by
side on iPad portrait, the canonical horizontal gap drops to **16 px**
(otherwise each column gets too narrow):

| Viewport | Width | Layout | Horizontal gap | Row gap |
|---|---|---|---|---|
| Phone portrait | < 768 px | **2 columns** | **16 px** | **12 px** |
| Phone landscape | < 768 px | **2 columns** | **16 px** | **12 px** |
| iPad portrait | 768–1023 px | **4 or 5 columns** | **16 px** | **12 px** |
| iPad landscape | 1024–1279 px | **4 or 5 columns** | **16 px** | **12 px** |
| Desktop | ≥ 1280 px | **4 or 5 columns** | **16 px** | **12 px** |

Tailwind encoding:

```html
<div className="grid grid-cols-2 md:grid-cols-4 gap-x-4 gap-y-3">
<div className="grid grid-cols-2 md:grid-cols-5 gap-x-4 gap-y-3">
```

(`FormGrid` does not yet have a `dense` variant — these dense filter
bars stay as raw Tailwind classes until a need for componentization
emerges. The canonical pattern is fixed.)

### 2a · Why these specific numbers

- **`md:` (768 px) breakpoint** — protects phone-landscape widths
  (e.g. iPhone Plus 736 px, Galaxy S 720 px) from the 2-col squeeze.
  iPad portrait viewport widths (768 px / 810 px / 834 px) hit this
  breakpoint precisely and get 2-col by design.
- **`gap-x-6` (24 px column gap)** — yields ≥ 12 px of clear space
  between adjacent input borders after accounting for typical 12 px
  inner input padding and WebKit chrome. Empirically free of bleed
  at 820 × 1180 (verified screenshot · `IPAD_LAYOUT_VALIDATION_REPORT.md` §2).
- **`gap-y-4` (16 px row gap)** — matches the platform's existing
  `space-y-4` rhythm inside `<section>` and `<CardBody>` wrappers.

## 3 · Variants

The canonical `FormGrid` accepts three optional props for the rare
cases where the default rhythm is not appropriate:

| Prop | Effect | When to use |
|---|---|---|
| `compact` | Row gap drops to 12 px | Tight date+time pairs inside a narrow card |
| `stackUntil="lg"` | 2-col activates at 1024 px (lg:) instead of 768 px (md:) | Inputs that are visually heavy (rich selects, GPS picker) and look cramped on iPad portrait |
| `stackUntil="sm"` | 2-col activates at 640 px (sm:) | **DO NOT USE** for normal form rows — defeats the purpose of the doctrine. Allowed only inside admin panels with read-only data grids. |

## 4 · What this doctrine REPLACES (deprecated patterns)

| Deprecated | Reason | Migrated count |
|---|---|---|
| `grid grid-cols-1 sm:grid-cols-2 gap-3` | bleed at iPad portrait & phone landscape | 37 occurrences across 28 files |
| `grid grid-cols-1 sm:grid-cols-2 gap-4` | same bleed, slightly less severe | 32 occurrences across 14 files |

All 69 occurrences were migrated in the same commit batch. See
`PLATFORM_FORM_GRID_FIX_CERTIFICATION.md` §3 for the migration
inventory.

## 5 · When to use FormGrid vs raw Tailwind

| Case | Use |
|---|---|
| Form field rows (label + input pairs) | **`<FormGrid>`** (canonical) |
| Read-only view-screen field rows | `<FormGrid>` OR `grid grid-cols-1 md:grid-cols-2 gap-x-6 gap-y-4` |
| Tile grids on hub pages (Cards / Tiles) | `grid grid-cols-1 md:grid-cols-2 gap-6` (no FormGrid — tiles are not inputs) |
| 3-column or 4-column layouts | Explicit Tailwind: `grid grid-cols-1 md:grid-cols-3 gap-x-6 gap-y-4` |
| Date + Time inside a narrow card (≤ 600 px container) | `<FormGrid compact>` |
| Visually-heavy input pairs (e.g. job picker + GPS button) | `<FormGrid stackUntil="lg">` |
| Inline button + chevron pairs (e.g. JobCombo) | `flex items-center gap-3` — NOT FormGrid |

## 6 · Out of scope

- 3- or 4-column tile grids (use raw Tailwind).
- Single-column wrappers (use plain `<div>` or `<section>`).
- Layouts with `position: absolute` floating elements (e.g. dropdown
  menus, popovers) — these manage their own spacing.

## 7 · How to refactor an existing form

```jsx
// BEFORE
<div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
  <div>
    <Label>Project Name</Label>
    <Input … />
  </div>
  <div>
    <Label>Project Number</Label>
    <Input … />
  </div>
</div>

// AFTER (raw Tailwind — minimum diff)
<div className="grid grid-cols-1 md:grid-cols-2 gap-x-6 gap-y-4">
  …
</div>

// AFTER (component — preferred for new code)
import FormGrid from "@/components/FormGrid";
<FormGrid>
  <div>
    <Label>Project Name</Label>
    <Input … />
  </div>
  <div>
    <Label>Project Number</Label>
    <Input … />
  </div>
</FormGrid>
```

## 8 · Enforcement

- ESLint rule (future work): flag any `grid grid-cols-1 sm:grid-cols-2`
  occurrence outside of approved files.
- Code review: reject any new form with the deprecated patterns.
- Visual regression test (future work): a Playwright snapshot of
  `daily/new` at 820 × 1180 px stored under
  `backend/tests/pw_suite/__snapshots__/` so any regression is
  caught before deploy.

## 9 · Doctrine compliance — references

- ARCHIVE_VISUAL_TREATMENT_STANDARD.md (sibling visual standard)
- FIELD_RELIABILITY_TEST_MATRIX.md (test scope for DR forms)
- OFFLINE_DRAFT_ENGINE_CERTIFICATION.md (no impact — layout-only change)

---

_Doctrine ratified: 2026-05-29 19:25 UTC. Owner: Frontend platform._
