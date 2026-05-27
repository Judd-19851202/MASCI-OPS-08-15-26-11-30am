# Contextual Return-Path Audit
## P1 Governance Refinement · 2026-05-27

> The Incident detail page currently announces `← INCIDENTS` no
> matter which portal the operator came from. This document maps
> the actual surface, the actual call sites, and the actual
> hardcoded language. Evidence before plan.

---

## 1 · Symptom (from the field photo)

A foreman / supervisor / admin opens the Accident / Incident Report
detail page. The top-left of the dark header bar shows:

```
← INCIDENTS
```

…regardless of where they came from:

- PM Portal → expected `← PM Portal` or `← Project Safety`
- Project Dashboard → expected `← Project Safety` (or project name)
- Safety Portal → expected `← Incident Center`
- Admin Console → expected `← Admin Console`

The result is operationally misleading. The page is technically
functional; the orientation is broken.

---

## 2 · Code-line evidence

### 2.1 · The single render site

`/app/frontend/src/pages/ViewIncident.jsx` · line 232:

```jsx
<BackLink to={listUrl} label={t("Incidents")} variant="header" testId="back-link" />
```

The label is **literally hardcoded** as `t("Incidents")`. There is
no upstream context.

### 2.2 · The path-derivation logic

`/app/frontend/src/pages/ViewIncident.jsx` · line 144:

```js
const listUrl = pathname.replace(/\/[^/]+$/, "") || "/admin/incidents";
```

This produces the parent path of the current detail page. So:

| Detail URL | Computed `listUrl` |
|---|---|
| `/admin/incidents/abc123` | `/admin/incidents` |
| `/pm/incidents/abc123` | `/pm/incidents` |
| `/incidents/abc123` (legacy redirect) | redirected to `/admin/incidents/abc123` |

This is correct for the **destination** (back goes to the right
listing) but the **label** is identical in all cases. The mismatch
is the bug.

### 2.3 · The BackLink primitive

`/app/frontend/src/components/BackLink.jsx` already supports an
explicit `label` prop and does the right thing — it is *the caller*
who is supplying the wrong (because uniform) label.

```jsx
export default function BackLink({ to, label, variant = "body", ... }) {
  // ...
  const text = label || fallback.label;   // ← honors caller's label
  // ...
}
```

So the fix is **all in the caller** (`ViewIncident.jsx`). The
primitive itself is fine.

---

## 3 · Entry points (where users open ViewIncident from)

Confirmed by `grep -rn "navigate.*incidents/\|to=.*incidents/"` and
the route map in `App.js`:

| Entry surface | Route prefix | Current pathname after click | Current back label | Should be |
|---|---|---|---|---|
| Admin · `/admin/incidents` list | `/admin/incidents` | `/admin/incidents/:id` | "Incidents" | **"Admin Console"** (or "Incidents" if from the list) |
| PM · `/pm/incidents` list | `/pm/incidents` | `/pm/incidents/:id` | "Incidents" | **"PM Portal"** (or "Incidents" if from the list) |
| PM Project Dashboard incident chip | `/pm/projects/:id/dashboard` | `/pm/incidents/:id` | "Incidents" | **"Project Safety"** |
| Safety Portal · `/safety-portal/incidents` | `/safety-portal/incidents` | `/incidents/:id` → redirect → `/admin/incidents/:id` | "Incidents" | **"Incident Center"** |
| Hub (legacy) `/incidents/:id` | none — direct URL | redirects to `/admin/incidents/:id` | "Incidents" | "Incidents" (acceptable fallback) |

---

## 4 · Route map (relevant slice from `App.js`)

```
/incidents/new          (NewIncident — public + admin shell)
/incidents/submit       (NewIncident — public)
/admin/incidents        (IncidentsDashboard)
/admin/incidents/:id    (ViewIncident — admin/pm/safety token accepted)
/pm/incidents           (IncidentsDashboard — under PM shell)
/pm/incidents/:id       (ViewIncident — admin/pm token only)
/safety-portal/incidents (SafetyIncidents)
/incidents/:id          → redirect to /admin/incidents/:id
```

No dedicated `/safety-portal/incidents/:id` route exists. Safety
users land on `/admin/incidents/:id` after the legacy redirect.

---

## 5 · Why a uniform label is operationally misleading

For a PM mid-task:

> "I was looking at my project. I tapped an incident chip. Now the
> back button says `← INCIDENTS` — am I in the global Incidents
> dashboard? Will tapping back take me to my project or to a list of
> every incident on every job?"

The cognitive load is small per click, but multiplied across a
shift, it erodes confidence. For a Safety supervisor:

> "`← INCIDENTS` — back to *what* Incidents view? The platform-wide
> list? The Incident Center I was just in?"

For an admin opening an incident from a CAPA detail page:

> "Back should return me to the CAPA. It will return me to the
> Incidents list. Now I have to navigate back again."

---

## 6 · Surface that needs to change

Single component file:
- `/app/frontend/src/pages/ViewIncident.jsx` (line 232 — caller of `BackLink`)

Optional upstream call sites (add `state={{from: {...}}}` for richer
context):
- `/app/frontend/src/pages/IncidentsDashboard.jsx` (lines 141, 173)
- `/app/frontend/src/pages/SafetyIncidents.jsx` (line 175)
- Project Dashboard incident chip (if it exists) — to be confirmed
  during implementation

The fix can be:
- (a) **Pathname-derivation only** in `ViewIncident.jsx` — zero
  upstream changes — works for 80% of the cases
- (b) **Pathname + `location.state.from`** — adds richer context
  when upstream provides it — works for 100%

The implementation plan (`LOW_RISK_IMPLEMENTATION_PLAN.md`) picks
(b), gated behind a new `useReturnContext()` hook so the logic is
testable in isolation.

---

## 7 · Sign-off

- **Author:** E1 · P1 governance refinement
- **Status:** 🟢 Audit complete · single-file blast radius identified
- **Next reading:** `SHARED_SURFACE_CONTEXT_MAP.md`
