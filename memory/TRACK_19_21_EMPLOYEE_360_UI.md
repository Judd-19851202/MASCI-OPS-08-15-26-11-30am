# Track 19.21 · Employee 360° UI

**Path:** `/hr/employees/:empId/profile`  
**Component:** `/app/frontend/src/pages/EmployeeProfile.jsx`  
**Backend:** reads `GET /api/hr/employees/{id}/accountability/timeline` + `/accountability/brief.pdf` (both pre-existing · zero drift)

## Layout

```
┌─────────────────────────────────────────────┬─────────────────┐
│  IDENTITY HEADER                            │  Right rail:    │
│  Name · trade · department · supervisor     │  Current state  │
│  Lifecycle status chip · Days tenure        │   one-liner     │
│  ─                                          │  Category count │
│  Employee Story paragraph (auto-composed)   │   grid (>0 only)│
│  "Hired 2019-03-11 as a Foreman for the     │  HR Compliance  │
│   Underground Department. Currently Active. │   Brief PDF btn │
│   Approved company driver · CDL VA."        │                 │
│  ─                                          │                 │
│  Next-Action chip (if expiring certs)       │                 │
├─────────────────────────────────────────────┤                 │
│  Tabs · All / Training / PPE / Incidents /  │                 │
│         Discipline / Driver Qual /          │                 │
│         HR Lifecycle                        │                 │
├─────────────────────────────────────────────┤                 │
│  Timeline spine (visual)                    │                 │
│    Category counter · category filter       │                 │
│    Empty-state message when tab is empty    │                 │
│    Color-coded dots per category            │                 │
└─────────────────────────────────────────────┴─────────────────┘
```

## Design pattern

Mirrors `SafetyCaseWorkspace.jsx` (Track 19.18) verbatim:
- Same identity-header + story-paragraph + Next-Action chip
- Same visual timeline spine (`<ol before:absolute>` + colored dots)
- Same right-rail one-liner headline + category count grid with empty-state filter
- Same data-testid convention (`employee-profile-*`, `employee-event-*`, `employee-profile-tab-*`)

## Category → color mapping

- **Training** → blue-600
- **PPE & Equipment** → emerald-600
- **Incidents** → red-600
- **Field Leadership** (discipline) → amber-600
- **Driver Qualification** → purple-600
- **HR Lifecycle** → slate-900

## HR Admin Test result

Q: Can an HR administrator open an employee and immediately understand the complete record without hunting across portals?  
**A:** ✅ Yes. Every data source that appears in the HR aggregation endpoint (10 collections) renders on this one page.

## Read-only doctrine

- Employee 360° issues zero mutations. Only `GET` requests.
- Enforced by a lock test: `grep -v 'method: "POST"' | 'method: "PUT"' | 'method: "DELETE"' | 'method: "PATCH"'`
- Data corrections happen in the source-of-truth surfaces (HR portal · Safety portal · Field Leadership). Employee 360° is a lens, not an editor.

## Bilingual

All labels wrapped in `t()`. Track 19.21 introduced no new EN-only strings — the aggregate response uses category names ("Training", "PPE & Equipment", "Incidents", "Field Leadership", "Driver Qualification", "HR Lifecycle") which map through existing i18n keys.

## data-testid catalog

- `employee-profile` — root
- `employee-profile-header` · `employee-profile-name` · `employee-profile-story` · `employee-profile-days-tenure` · `employee-profile-next-action`
- `employee-profile-tabs` · `employee-profile-tab-{key}` (7 tabs)
- `employee-profile-timeline-wrap` · `employee-profile-timeline` · `employee-profile-timeline-empty`
- `employee-event-{source}-{source_id}` — per row
- `employee-profile-exec` · `employee-profile-exec-headline`
- `employee-profile-category-counts` · `employee-profile-exports` · `employee-profile-brief-pdf`
- `employee-profile-loading` · `employee-profile-error` · `employee-profile-back`
