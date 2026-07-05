# DR-ROI-001E · Deprecation / Cleanup Plan

## What Phase E does NOT deprecate
- V1 Daily Report page (`NewDailyReport.jsx`).
- V1 Daily Report route (`/daily/new`).
- V1 Daily Report list (`DailyReportsDashboard.jsx`).
- Existing `/admin/operational-intelligence` page (legacy admin OI —
  different route, different file).
- Existing PM / Admin dashboards (Hub-level tiles).

## What Phase E introduces (additive only)
- `/pm/operational-intelligence`
- `/admin/ods-intelligence`
- `/executive/ods-intelligence`
- `/api/ods/pm/attention`, `/api/ods/pm/projects/{id}/attention`,
  `/api/ods/admin/attention`.

## Cleanup Candidates (post-Phase G)
- **None from Phase E**. Every new file is a first-class citizen; no
  transitional scaffolding to retire.
- Optional (Phase H+): merge the legacy `/admin/operational-intelligence`
  route with the new `/admin/ods-intelligence` view once user validates
  the horizon layout. **Requires explicit user directive.**

## Naming Conventions Locked In
- **Route path suffix `/ods-intelligence`** on the Admin + Executive
  side to disambiguate from the pre-existing
  `/admin/operational-intelligence` lazy route (naming collision fixed
  at the top of this track).
- **Component name `OdsAdminIntelligence` / `OdsExecutiveIntelligence`**
  in the `AppRoutes` import graph, again to avoid clashing with the
  existing lazy `AdminOperationalIntelligence` component name.
- **Backend prefix `/api/ods/*`** — mirrors the ODS-001 spine namespace.

## Legacy Compatibility Notes
- `ods_briefs_cache` is a new collection — no migration required.
- No collection removed. No index removed.

## Deprecation Log
_None._ (This track is 100% additive.)
