# PM Portal · RFI + Schedule Architecture
## Phase V.0 · Architecture & Governance · 2026-05-27

> Where the RFI and Schedule Intelligence subsystems live inside the
> PM portal, how they integrate with PM Sidebar V2, and what cross-
> portal surfaces they expose. Doctrine-locked.

---

## 1 · Primary Home

| Subsystem | Primary home |
|---|---|
| RFI Center | **PM Portal** (`/pm/rfi/*`) |
| Schedule Intelligence | **PM Portal** (`/pm/schedule/*`) |
| Constraints (operational bridge) | **PM Portal** (`/pm/constraints/*` and inline on Schedule + RFI views) |
| External RFI portal | **Dedicated `/rfi/ext/*` surface** (no portal chrome) |
| External schedule access (V.6+) | **Dedicated `/schedule/ext/*` surface** (no portal chrome) |

PM is the contract custodian. The PM portal is the contract command
center. Everything authored here.

---

## 2 · PM Sidebar V2 — New Domains

The existing PM Sidebar V2 (`SideNavV2.jsx`) defines a 4-domain layout.
RFI + Schedule add a **5th domain**: **Operational Records**. The
domain's stripe color is **slate-600** (calm, doctrinally consistent
with Audits & Guidance). Red is **not** added to this domain — red
stays reserved for the Incidents domain in Safety.

Proposed PM Sidebar V2 structure (post-V.1):

```
Project Operations         ── existing
  Project Hub
  Daily Reports
  Crew & Field
  Equipment

Quality & Compliance       ── existing
  QA / QC
  Safety Records
  Document Expirations

Contracts & Finance        ── existing
  PO Requests
  Payroll Variance
  Suppliers / Equipment Master

Operational Records        ── NEW (V.1+)
  RFI Center                  · Draft, review, submit. PM-owned.
  Constraints                 · Schedule impact tracker. Linked to RFIs.
  Schedule Intelligence       · P6 import. Lookahead. Critical path.
  Open Primavera P6 (link)    · Per-project. Same pattern as Basecamp.

Guidance & Coaching        ── existing
```

`Open Primavera P6` is a configurable per-project link styled like
the existing Basecamp / OnStation entries. Blank by default; PM sets
it. Falls back gracefully when absent.

---

## 3 · Route Map

| Route | Purpose | Auth |
|---|---|---|
| `/pm/rfi` | RFI list (scoped to PM projects) | PM / Admin |
| `/pm/rfi/new` | Draft a new RFI | PM / Admin |
| `/pm/rfi/:id` | RFI detail · submitted view · revisions · audit trail | PM / Admin |
| `/pm/rfi/:id/edit` | Draft / revision editor | PM / Admin |
| `/pm/rfi/:id/distribute` | Distribution + tokenized link issuance | PM / Admin |
| `/pm/rfi/:id/pdf` | Download current revision PDF | PM / Admin |
| `/pm/constraints` | Constraint list (scoped) | PM / Admin · cross-portal read |
| `/pm/constraints/:id` | Constraint detail | PM / Admin · cross-portal read |
| `/pm/schedule` | Schedule Intelligence hub | PM / Admin · cross-portal read |
| `/pm/schedule/upload` | Upload `.xer` | PM / Admin |
| `/pm/schedule/import/:id` | Import preview / diff | PM / Admin |
| `/pm/schedule/activities` | Activity list view | PM / Admin · cross-portal read |
| `/pm/schedule/lookahead` | Lookahead view | PM / Admin · cross-portal read |
| `/pm/schedule/critical-path` | Critical-path risk view | PM / Admin · cross-portal read |
| `/pm/schedule/operational-impact` | Operational impact view (constraint × activity) | PM / Admin · cross-portal read |
| `/rfi/ext/:token_id/:token_slug` | External RFI landing page | tokenized only |

The superintendent-facing **draft path** (V.1) lives at:

| Route | Purpose | Auth |
|---|---|---|
| `/field-leadership/portal/rfi/new` | Field-first RFI draft (mobile-first) | Field Leadership |
| `/field-leadership/portal/rfi/:id` | Read draft / submitted RFIs for assigned crews | Field Leadership |

Field Leadership cannot submit. They drop drafts to the PM.

---

## 4 · Component Hierarchy

```
PmShell (existing layout chrome)
  ├── SideNavV2 (existing · adds "Operational Records" domain)
  └── <Outlet>
        ├── /pm/rfi             → <RFIListPage />
        ├── /pm/rfi/new         → <RFIDraftPage />
        ├── /pm/rfi/:id         → <RFIDetailPage />
        │     ├── <RFISummaryBlock />
        │     ├── <RFIMetadataBlock />
        │     ├── <RFIFieldConditionBlock />
        │     ├── <RFIPlanSpecBlock />
        │     ├── <RFIImpactBlock />
        │     ├── <RFIAttachmentsBlock />
        │     ├── <RFIResponseBlock />
        │     ├── <RFIDistributionBlock />
        │     ├── <RFIRevisionHistoryBlock />
        │     └── <RFIAuditTrailBlock />
        ├── /pm/constraints     → <ConstraintListPage />
        ├── /pm/constraints/:id → <ConstraintDetailPage />
        └── /pm/schedule/*      → <ScheduleHubPage />
              ├── <ScheduleActivityListView />
              ├── <ScheduleLookaheadView />
              ├── <ScheduleCriticalPathView />
              ├── <ScheduleOperationalImpactView />
              └── <ScheduleImportPreviewPanel />
```

Every block is a calm, single-purpose component. No 600-line
monoliths. Each block carries a `data-testid`. Each block participates
in the visual doctrine baseline probe.

---

## 5 · Cross-Portal Surfaces

| Portal | What it sees about RFI/Schedule | Why |
|---|---|---|
| Superintendent / Field Leadership | Drafts they originated · Submitted RFIs on their jobs (read) · Active constraints affecting their work (read) | Field execution awareness |
| Safety Portal | RFIs flagged with safety/compliance exposure (read) · Constraints of type `safety_hold` (read) | Compliance oversight |
| Dispatch Portal | RFIs flagged with MOT/phasing/haul impact (read) · Constraints of type `mot_restriction` or `access_restriction` (read) | Routing impact |
| HR Portal | None | Out of scope |
| Admin Portal | Full read · audit · void co-signer | System of record oversight |
| Executive view | Aging critical-path exposures · count of overdue critical-path RFIs (read) | Strategic oversight |

External access lives on its own surface (no portal chrome). Never
inside `/pm`.

---

## 6 · Governance Health Chip Integration

The Governance Health Chip already exists on PM Hub headers. Two new
signals feed it from this subsystem:

1. **Operational exposure indicator** — when the PM scope contains a
   project with **critical-path exposure days > 0**, the chip surfaces
   `governance monitor` (slate). When exposure days > project float on
   any one CP activity, chip surfaces `governance drift`. **Never red.**
2. **Overdue external response indicator** — when any RFI in scope is
   in `cei_review` or `engineer_review` past `response_due_date` by
   more than 48 hours, the chip's secondary line reads:
   *"<N> overdue external responses".*

Both signals are doctrinally calm: text-only, monochrome, no flashing.

---

## 7 · Mobile Discipline

| Surface | Mobile target |
|---|---|
| `/pm/rfi` list | Full feature parity. List view paginates. Filters become a bottom sheet. |
| `/pm/rfi/new` (PM mobile) | Acceptable. Full draft path. |
| `/field-leadership/portal/rfi/new` (Superintendent mobile) | **Primary target.** ≤ 60 seconds draft on phone. Photo-first. Voice-to-text. |
| `/pm/schedule/lookahead` | Mobile-first. Default view is next 14 days · one activity per row. |
| Activity detail | Bottom sheet. Constraint badges visible inline. |
| External `/rfi/ext/*` | Mobile-first for CEI / Engineer reading on the field. |

No table-only views without a mobile fallback. No giant Gantt on mobile.

---

## 8 · Configuration Storage

| Setting | Where |
|---|---|
| Per-project `rfi_template` | `projects` collection |
| Per-project `p6_link_url` | `projects` collection |
| Per-project `basecamp_url` | `projects` collection (existing) |
| Per-project `onstation_url` | `projects` collection (existing) |
| Default `response_due` windows by priority | `app_config` (NEW) or `RFI_template` JSON |
| Default `float_warning_threshold_days` | `projects` collection (override-able) |
| RFI template files | `/app/memory/rfi_templates/*.json` |

Configuration is **declarative**. PM panel pages edit these settings
with the existing Admin Settings discipline.

---

## 9 · Backend Routing Discipline

New routers (in line with the existing `/app/backend/routes/` pattern,
not in `server.py`):

| Router | Path |
|---|---|
| `routes/rfi/__init__.py` | mounts all RFI sub-routers |
| `routes/rfi/list.py` | list / search / filter |
| `routes/rfi/draft.py` | create / edit / save / discard |
| `routes/rfi/submit.py` | submit, revise, void |
| `routes/rfi/response.py` | accept / reject / clarification-required |
| `routes/rfi/distribute.py` | tokenized link issuance + revocation |
| `routes/rfi/external.py` | tokenized external endpoints |
| `routes/rfi/pdf.py` | PDF render + R2 fetch |
| `routes/rfi/audit.py` | audit-trail reader |
| `routes/schedule/__init__.py` | mounts all Schedule sub-routers |
| `routes/schedule/import_xer.py` | upload + preview |
| `routes/schedule/revisions.py` | activate / reject / re-activate |
| `routes/schedule/activities.py` | activity list / detail |
| `routes/schedule/lookahead.py` | lookahead computation |
| `routes/schedule/critical_path.py` | CP risk + exposure |
| `routes/schedule/operational_impact.py` | RFI × constraint × activity view |
| `routes/constraints/__init__.py` | constraint CRUD + cross-portal reads |

**No new endpoints land in `server.py`.** All new code lives in its
own routers. This continues the safe-decomposition doctrine.

---

## 10 · Sign-off

- **Author:** E1 · Phase V.0 architecture authoring pass
- **Status:** 🟢 Doctrine-grade
- **Implementation gate:** Sidebar V2 amendment lands in V.1. New routers land as each phase activates.
