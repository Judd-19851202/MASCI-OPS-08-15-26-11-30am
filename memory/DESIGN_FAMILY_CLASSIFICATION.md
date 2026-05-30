# DESIGN_FAMILY_CLASSIFICATION.md

_Pass 7 · Workflow family classification + per-family doctrine · 2026-02-01._

## Mission

Classify every operator-facing surface into one of 4 workflow families.
Each family has its own composition doctrine. Pages within a family
share rhythm. Pages across families feel distinctly purpose-built.

## Mockup routes (preview only · not linked from any portal)

| Family | Route | Accent | Mockup screenshot in chat |
|---|---|---|---|
| Index | `/__design` | — | Index of all 4 families |
| **A** | `/__design/family-a` | blue | Field forms (Daily Report Section 3 of 6 · Weather card · Photo evidence) |
| **B** | `/__design/family-b` | purple | Approval consoles (PO Requests filter + queue + approve/reject) |
| **C** | `/__design/family-c` | emerald | Operational status (Fleet metric strip + 6 equipment status cards) |
| **D** | `/__design/family-d` | slate | Configuration consoles (User search + dense list with role badges) |

---

## Family A · Field Forms

**Persona**: Superintendent · Foreman · Operator · Safety Lead
**Context**: On site · iPad / phone · often gloved hands · short attention
**Surfaces**: Daily Reports · JHA / JHP · Safety Meetings · Incident Reports · QA / QC

**Doctrine**:
- **Section-progress header strip** at top — clear sense of "where am I"
- **Numbered section cards** ("SECTION 3 OF 6") with explicit step number
- **Larger touch targets**: inputs are `h-12` (not h-10) · buttons are `h-12 px-7`
- **Larger body text**: `text-base` on inputs (not text-sm)
- **Choice-chip pickers** for short option sets (Sky Conditions, Severity, Status) — 2-col on phone, 4-col on tablet+, NOT a `<Select>` dropdown
- **Photo evidence section** uses dashed-border ADD tile + thumbnails grid 3/4/6 col responsive
- **Save state context chip** ("SAVED LOCALLY · just now") in section footer
- **Primary action: Continue · Section N+1** — large, accented, in footer

**Anti-patterns**:
- ❌ Dense `<Select>` dropdowns for small option sets
- ❌ Tiny h-10 inputs
- ❌ All sections rendered as one giant scroll (use stepped sections)
- ❌ Submit button at the very top

---

## Family B · Approval Consoles

**Persona**: PM · Office Admin · HR · Payroll · Approver
**Context**: Desk / laptop · 1366+ viewport · scan-quickly + approve workflow
**Surfaces**: PO Requests · HR Time Verification · HR Payroll Variance · HR Approvals · HR Time-Off Approvals

**Doctrine** (Pass-6 reference: HR Time Verification + HR Payroll Variance):
- **Filter card at top** with accent-colored frame (`purple-200 bg-purple-50/30`)
- **Filter inputs in 2-col grid** (`grid grid-cols-1 sm:grid-cols-2 gap-x-6 gap-y-4`)
- **Dedicated action footer** with border-top separator:
  - LEFT: queue context chip ("QUEUE · 7 pending · 2 over-threshold")
  - RIGHT: Export CSV (secondary) + Apply Filters (primary)
- **Queue list** as a single Card with `divide-y` rows
- **Each row**: badge LEFT · summary CENTER · amount RIGHT · Reject + Approve buttons FAR RIGHT
- **Approve always rightmost** — primary action position
- **Reject in outline-red**, never `bg-red-700` (signals danger but not destructive default)
- **Detail drawer** opens on row click for full review · sticky footer with Approve / Reject buttons

**Anti-patterns**:
- ❌ Apply / Submit buttons inline as a grid cell
- ❌ Approve + Reject as same-weight buttons (Approve must look primary)
- ❌ Approve at LEFT, Reject at RIGHT (violates primary-rightmost rule)
- ❌ Detail modal instead of drawer (drawer preserves queue context)

---

## Family C · Operational Status

**Persona**: PM · Dispatcher · Mechanic · Operator · Executive
**Context**: Mixed (desk + field) · large screens + iPad · real-time status check
**Surfaces**: Equipment · Fleet · Shop Console · Dispatch · Equipment Pre-Op

**Doctrine**:
- **Metric strip at top** — single Card with internal `sm:divide-x` grid, 3-4 high-signal numbers (FLEET ONLINE 23/28 · PRE-OP FAILED 2 · etc.)
- **Status badges** are PRIMARY visual signal: every entity card has a colored status badge in the top-right (OK / FAILED / DISPATCH / OOS)
- **Color-coded card borders**: `border-emerald-300` for healthy · `border-red-300 bg-red-50/40` for failed · `border-amber-300` for in-progress · `border-slate-300` for OOS
- **Card grid 1 / sm:2 / lg:3** with each card showing: ID (mono small) + Equipment Name (display bold) + Status Badge (top right) + Operator + Project + Notes (failure reason colored)
- **Failed cards visually scream**: red border + red-50 background + red note text
- **Action affordance**: entire card clickable → opens detail view / DVIR / pre-op record

**Anti-patterns**:
- ❌ Status as inline text instead of colored badge
- ❌ Cards all in same color (status must communicate at-a-glance)
- ❌ Long-form text descriptions in cards (cards are scan-fodder, not detail)
- ❌ Centered headings (left-align for ops grids)

---

## Family D · Configuration Consoles

**Persona**: Super Admin · IT Admin · Owner
**Context**: Desktop · power-user · admin workflow
**Surfaces**: Admin Users · Admin Sessions · Admin Settings · Admin Integrations · Admin Banners · Admin Promo Assets

**Doctrine**:
- **Search-first**: top of page is a wide search input + Filters dropdown + Primary CTA ("New User") in a single horizontal action bar
- **Dense table-style list**: rows are compact (`p-4`), not tall cards
- **Column-typed columns**: User column wraps name + email; Role column has Badge; Last Active is mono small text; Actions column has small icon buttons
- **Responsive column hiding**: less critical columns hide at `<md:hidden` (Last Active hidden on phone)
- **Icon-only action buttons** (Settings cog, Trash icon) at end of row · `h-8 w-8` ghost buttons
- **No accent color** — slate / neutral · admin context doesn't need decoration
- **Bulk operations toolbar** appears above list when rows selected (deferred to Pass-8)

**Anti-patterns**:
- ❌ Tall cards instead of compact rows (admin needs density)
- ❌ Full-width primary buttons (admin uses compact buttons)
- ❌ Decorative gradients (admin should feel utilitarian)
- ❌ Hiding search behind a Filters dropdown (search is primary)

---

## Cross-family principles

1. **Every page has an unambiguous primary action.** Field forms = Continue · Section N+1. Approval consoles = Apply Filters + per-row Approve. Operational status = card click → detail. Admin = New User / Save Settings.
2. **Primary action is always rightmost in any action cluster.** Secondary / cancel actions to its left.
3. **Action buttons NEVER live inside the input grid.** Always in the SectionCard footer.
4. **Color accent matches family.** A surface accidentally using purple in Family C looks wrong — that's the point.
5. **Empty / loading / error states have explicit treatment** per family (Family A: large helpful illustration; Family B: empty-queue badge; Family C: "no assets matching filter" muted card; Family D: empty-list compact message).

## Surface → Family mapping (binding)

| Surface | Family | Status |
|---|---|---|
| Daily Reports | A | 📐 awaiting Pass-8 |
| JHA / JHP | A | 📐 awaiting Pass-8 |
| Safety Meetings | A | 📐 awaiting Pass-8 |
| Incident Reports | A | 📐 awaiting Pass-8 |
| QA / QC | A | 📐 awaiting Pass-8 |
| PO Requests | B | 📐 awaiting Pass-8 |
| HR Time Verification | B | ✅ Pass-6 shipped (reference) |
| HR Payroll Variance | B | ✅ Pass-6 shipped (reference) |
| HR Approvals | B | 📐 awaiting Pass-8 |
| HR Time Off | B | 📐 awaiting Pass-8 |
| HR Incidents | B | 📐 awaiting Pass-8 |
| HR Employees | B+D hybrid | 📐 awaiting Pass-8 |
| Equipment | C | 📐 awaiting Pass-8 |
| Fleet (DVIR) | C | 📐 awaiting Pass-8 |
| Shop Console | C | 📐 awaiting Pass-8 |
| Dispatch | C | 📐 awaiting Pass-8 |
| Equipment Pre-Op | C | 📐 awaiting Pass-8 |
| Admin Users | D | 📐 awaiting Pass-8 |
| Admin Sessions | D | 📐 awaiting Pass-8 |
| Admin Integrations | D | 📐 awaiting Pass-8 |
| Admin Banners | D | 📐 awaiting Pass-8 |
| Admin Settings | D | 📐 awaiting Pass-8 |

## Rollout sequence (Pass-8 proposal · awaits operator approval)

1. **Family B remainder** (HR Approvals, HR Time-Off, HR Incidents, HR Employees filter, PO Requests filter+drawer) — fastest because Pass-6 already proved the pattern
2. **Family A** (DR Section card refactor, JHA/JHP, Safety Meeting, Incident, QA-QC submit rows) — biggest user-facing impact (field users)
3. **Family C** (Equipment, Fleet DVIR, Shop, Dispatch, Pre-Op) — visible to PM + Dispatch
4. **Family D** (Admin surfaces) — last because admin users are most-tolerant of "looks-functional"

Per-family rollout includes:
- Implementation of remaining primitives (`MetricStrip`, `FormSection`, `DrawerLayout`, `ModalLayout`)
- Per-surface refactor following the family doctrine
- Per-family screenshot proof at 1366 × 1024 viewport (operator's review viewport)

---

_End of DESIGN_FAMILY_CLASSIFICATION.md._
