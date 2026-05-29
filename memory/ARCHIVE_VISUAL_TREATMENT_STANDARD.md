# Archive Visual Treatment · Standard

_Phase V.1 · M1 · 2026-05-29 · permanent visual contract for legacy
records inside MASCI Ops._

> **Operator directive (verbatim):** _"Every historical Daily Report
> must display: ARCHIVED DAILY REPORT · Historical Record · Read Only ·
> Original Format Preserved. Calm · slate styling · no warning colors ·
> no alarm language. Purpose: explain why the record differs from ODR."_

This standard is the single source of truth for how legacy records
are represented anywhere in the MASCI Ops UI.

---

## 1 · Tone (the most important section)

The archive treatment is **calm**, **operational**, and **factual**.

### 1.1 What we say

| Phrase | Where |
|---|---|
| `Archived` | Compact pill badge |
| `ARCHIVED DAILY REPORT` | Section heading |
| `Historical Record · Read Only · Original Format Preserved` | Subhead |
| `Original format preserved` | Inline metadata under each row |
| `This entry was filed before MASCI Ops moved to the Operational Daily Record. Its original shape, signatures, and PDF have not been altered.` | Explainer card on the dashboard header |

### 1.2 What we do NOT say

| ❌ Forbidden phrase | Why |
|---|---|
| "Legacy" (as a user-facing label) | Implies inferiority; archived ≠ legacy in operator language |
| "Outdated" | Implies invalidity |
| "Deprecated" | Engineering language; not operator language |
| "Old format" | Subtly punitive |
| "Convert to ODR" | We do not convert; the directive forbids it |
| "Migrate" / "Migration required" | We do not migrate |
| "Read-only mode" | Slightly defensive; "Read Only" alone is calm |
| Any exclamation marks | Operational calmness doctrine |
| Any "warning" / "caution" / "deprecated" semantics | This is canonical evidence, not a warning |

## 2 · Color (slate · never alarming)

### 2.1 Allowed palette

| Use | Token | Tailwind class |
|---|---|---|
| Badge background | slate-100 | `bg-slate-100` |
| Badge border | slate-300 | `border-slate-300` |
| Badge text | slate-600 | `text-slate-600` |
| Explainer card background | slate-50 | `bg-slate-50` |
| Explainer card border | slate-200 | `border-slate-200` |
| Explainer card text | slate-600 | `text-slate-600` |
| Subtle archive subhead | slate-500 | `text-slate-500` |

### 2.2 Forbidden palette

| Color | Why it is forbidden for archive treatment |
|---|---|
| Red (any shade) | Reserved for the single-red doctrine (active blockers only) |
| Amber / yellow | Reserved for warnings — archive is not a warning |
| Orange | Energetic / urgent — archive is calm |
| Purple / pink | Off-palette · doctrine-prohibited platform-wide |
| Gradients | AI-slop pattern; doctrine-prohibited platform-wide |

## 3 · Component contract

### 3.1 `<ArchiveBadge size="sm|md|lg" />`

- Renders a slate pill with the single word `Archived`.
- `data-testid="archive-badge"` for governance probes.
- Has a `title` tooltip carrying the full subhead string for screen
  readers and hover.
- Sizes are `sm` (10px), `md` (12px, default), `lg` (14px). No
  larger size is permitted — archive must never visually dominate.

### 3.2 `<ArchiveExplainerCard />`

- Renders the dashboard-level explainer subhead.
- Used **once per surface** at the top of the records list.
- Never used as an alert · never used as a modal interruption.

### 3.3 Single-source-of-truth rule

There MUST be exactly one component implementing the archive
treatment (`/app/frontend/src/components/odr/ArchiveBadge.jsx`).
Any other surface that needs an archive indicator imports from this
single source. Doctrine inheritance per
`ODR_PLATFORM_INHERITANCE_DOCTRINE.md`.

## 4 · Placement rules

| Surface | Placement |
|---|---|
| Unified records list | Slate badge inline next to doc_id |
| Unified records list (header) | Explainer card at the top |
| Legacy viewer route (`/daily-reports/<id>`) | Slate badge near the page title |
| Operational timeline (when implemented) | Slate badge inline on the row |
| Cross-portal search results | Slate badge inline next to doc_id |

The badge **never** appears:

- On the foreman entry surface (no archive concept there)
- On the ODR Public Viewer (audience-projected · external context)
- On the PM Panel risk metrics (those aggregate forward-looking signal)

## 5 · Behavior rules

- The archive treatment is **purely visual**. It does not change
  data. It does not lock fields the user could otherwise edit
  (because the legacy substrate is API-frozen — there are no
  editable fields to lock).
- The badge does not link anywhere on its own. The row containing
  the badge links to the legacy viewer.
- Hover tooltip carries the full subhead. No click-through education
  modal — the explainer card on the header is sufficient.

## 6 · Bilingual contract (forward-compatible)

This standard ships English-only because legacy records pre-date
the M0.2A bilingual lift. When ODR's bilingual substrate matures
into a unified i18n surface, the archive copy MUST be added in
Spanish in lockstep:

| EN | ES (forward) |
|---|---|
| Archived | Archivado |
| Archived Daily Report | Reporte Diario Archivado |
| Historical Record · Read Only · Original Format Preserved | Registro Histórico · Solo Lectura · Formato Original Preservado |

These translations are **not in scope for M1** but are recorded
here so the next i18n wave finds them.

## 7 · Accessibility

- Slate-on-white meets WCAG AA contrast at all three badge sizes.
- The badge carries the full subhead in `title=` for screen readers.
- The explainer card uses semantic `<div>` with text content (no
  decorative-only icons), so screen readers pick up every word.
- No motion / no animation on the archive treatment — calm and
  instantaneous.

## 8 · Anti-patterns this standard forbids

1. ❌ Ribbon-style banners ("This is an archived record!")
2. ❌ Modal interruptions on first archive view
3. ❌ Greying out / opacity reduction on archive rows (implies
   degraded data; archive is canonical evidence)
4. ❌ Strikethrough on archive doc_ids (implies invalidity)
5. ❌ Lock icons (implies "you can't have this" — but the user can,
   it is read-only by design and that is normal)
6. ❌ "(Legacy)" suffix on doc_ids (engineering language)
7. ❌ Archive-only filtering as the default state (defaults must
   surface both substrates so timelines stay continuous)
8. ❌ Different typography / different font / different border
   radius for archive cards (Doctrine Lock #2 · platform inheritance)

## 9 · Test hooks

| Test id | Use |
|---|---|
| `archive-badge` | Single archive badge node |
| `archive-explainer` | The explainer card |
| `op-records-list` | Container of mixed rows |
| `op-record-legacy_daily_report-<id>` | Legacy row |
| `op-record-odr-<id>` | ODR row |
| `op-records-counts` | Honest counts indicator |

## 10 · Operator-facing one-liner

> **The archive looks calm because the past is calm.**
>
> Historical Daily Reports are not warnings, not deprecated content,
> not technical debt. They are the operational evidence of MASCI's
> first 21 months of field activity. The slate treatment honors that.

---

_End of ARCHIVE_VISUAL_TREATMENT_STANDARD.md · single source of truth for archive UI in MASCI Ops._
