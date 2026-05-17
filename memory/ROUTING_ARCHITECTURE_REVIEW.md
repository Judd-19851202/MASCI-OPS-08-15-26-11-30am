# MASCI Hub — Frontend Routing & Auth-Wrapper Architecture Review

> **Read-only review. No refactor proposed for this turn.** Purpose: an
> honest assessment of `App.js`'s routing/auth structure so the operator
> can make an informed call on when (and how) to refactor — without
> being surprised by what's actually in there.
>
> Last updated: 2026-02-XX · Owner: MASCI Operations

---

## 1. Current state — by the numbers

| Metric | Count |
|---|---|
| File | `/app/frontend/src/App.js` |
| Lines | 575 |
| Total `<Route>` definitions | 190 |
| Routes under `/admin` | 51 |
| Routes under `/pm` | 26 |
| Routes under `/safety-portal` | 15 |
| Routes under `/hr` | 13 |
| Routes under `/dispatch-portal` | 4 |
| Routes under `/shop` | 5 |
| Routes under `/safety` (public form-gate surface) | 8 |
| Routes under `/field` and `/qaqc` (public) | 6 |
| Routes under `/leadership` (Field Leadership records) | 4 |
| Routes under `/training` and `/ops-training` | 9 |
| `<Navigate to=... replace />` redirect aliases | 20 |
| Imported page components | ~115 |
| Auth-wrapper components used (`Require*`) | 8 |
| Auth-wrapper shorthand helpers (`A`, `AP`, `P`, `S`, `H`, `SF`, `DP`, `D`) | 8 |

Every imported page resolves to a route; nothing is dead. The auth
wrappers are thin (24–41 lines each) and share a common pattern:
`isTokenPresent()` → hydration check → `<AccessDenied/>` for
wrong-portal-but-signed-in, → `<Navigate to=login/>` for anonymous.

---

## 2. What this structure does well

1. **Single source of truth for the route table.** Every URL the
   platform answers is in one file. Auditors and new operators can
   skim the entire surface in ~10 minutes.
2. **Token-namespace isolation is enforced at three layers.**
   - Route-level wrapper (`Require*` component)
   - `EnforcePortalScope` runs on every route entry and clears
     wrong-portal tokens (iter179)
   - Backend `require_*` FastAPI deps are canonical and would refuse
     any token mismatch even if the frontend wrapper were bypassed
3. **Aliases preserve printed-QR-code and bookmark URLs.** 20
   `<Navigate to=... replace />` entries map legacy routes (e.g.
   `/cheat-sheet → /cheatsheet`, `/qa-qc → /qaqc`, `/inspections/new`,
   etc.) to the canonical surface. This is not sprawl; it's
   intentional URL durability for field workers.
4. **Catch-all renders `NotFound` (iter181).** Previously unmatched
   paths showed a blank shell. Fixed.
5. **Shared wrappers compose cleanly.** `AP` (admin OR PM) on shared
   dashboards lets the same component serve both `/admin/inspections`
   and `/pm/inspections` without duplicating the page logic.

---

## 3. Concrete risks at current scale

### 3.1 `App.js` is the single point of merge contention

Every new portal route, every new auth tier, every new redirect alias
lands in this 575-line file. Two engineers adding routes in parallel
will merge-conflict almost every time. With 190 routes, the file is
also slow to read top-to-bottom when investigating an unrelated bug —
you must scan a long list to confirm a route doesn't already exist
elsewhere.

**Severity:** Medium. Single-developer cadence today, but the issue
compounds as the team grows or the SaaS multi-tenant work begins.

### 3.2 Portal-namespace aliasing is a hidden source of cognitive load

The `/admin/qaqc/:id`, `/admin/leadership/records/:id`,
`/admin/safety/issuance/:id`, `/admin/safety/training/:id`, and the
parallel `/pm/daily`, `/pm/incidents`, `/pm/meetings`,
`/pm/inspections`, `/pm/jha-plans`, `/pm/trench-boxes`,
`/pm/equipment`, `/pm/equipment/:id` aliases all point at the same
underlying view components. They exist because `EnforcePortalScope`
wipes the current portal's token when navigating outside its `/<portal>`
prefix — so the alias keeps the same backing component but under a
different URL prefix to keep the session alive.

This is correct behaviour, but the **reason** it exists is not obvious
when reading `App.js` cold. A future engineer might "tidy up" by
collapsing the aliases and silently break cross-portal navigation.

**Severity:** Medium-high. There is an inline comment near the PM
aliases explaining this; the same comment does not exist near the
admin-namespaced aliases.

### 3.3 The `A` / `AP` / `P` / `S` / `H` / `SF` / `DP` / `D` shorthand reads tersely

Single-letter helpers make 50+ lines of `<Route>` definitions skim
faster, but at the cost of being inscrutable to anyone unfamiliar
with the convention. A new engineer reading `<Route … element={SF(<SafetyAudits />)} />`
must scroll up to the helper definitions, then up to the imports, then
to the wrapper component, before knowing what it does.

**Severity:** Low. The convention is consistent and reasonable for an
internal codebase; the tradeoff is acceptable today.

### 3.4 Tasks · Document Expirations · PO Requests · Project Health · Asset Transfers are wrapper-less

```jsx
<Route path="/tasks" element={<Tasks />} />
<Route path="/document-expirations" element={<DocumentExpirations />} />
<Route path="/hr/employees" element={<HrEmployees />} />
<Route path="/po-requests" element={<PoRequests />} />
<Route path="/project-health" element={<ProjectHealth />} />
<Route path="/asset-transfers" element={<AssetTransfers />} />
```

These rely on **the page component itself** to render `<AccessDenied/>`
for anonymous visitors and on the **backend** to enforce RBAC. That's
defense-in-depth-but-asymmetric: every other gated surface uses a
wrapper. Going forward, if a regression slips into one of these pages'
in-component gate, the URL becomes silently reachable until the page
makes its first authorized API call.

**Severity:** Medium. Functional today (backend is canonical), but it
violates the "wrap at the route, render at the component" symmetry that
the rest of the file maintains.

### 3.5 `/hr/employees` appears twice in spirit

Line 134 imports `HrEmployees`; line 530 wires `/hr/employees` with **no
wrapper**, while the rest of the `/hr/*` surface uses `H(...)`. This
is the only `/hr/*` route that doesn't use the HR wrapper. Worth
double-checking — either it's intentional and should be commented, or
it's an oversight that should be `H(<HrEmployees />)`.

**Severity:** Low-medium. Worth a 5-minute audit by the operator
before any refactor; not a P0 today.

### 3.6 `/app/*` redirect is correct but easy to miss

```jsx
<Route path="/app/*" element={<Navigate to="/" replace />} />
```

This silently bounces every `/app/*` URL home — historically Crew Hub
lived there and was removed 2026-04-28. The comment above the route is
explicit. Worth keeping; flagging here so a future "simplify the
routes" pass doesn't delete it without understanding why.

**Severity:** Low. Comment is already in place; the residual risk is
purely human attention.

### 3.7 Form gates outside the auth-token system

`<GateInspection>` (line 165) is a password-gate wrapper for the
public site-inspection submission form. The password is hard-coded in
the file (`SITE_INSPECTION_CODE = "1982"`). This isn't an auth
namespace — it's a form-level "are you on a job site" gate — but the
hard-coded constant lives in `App.js` alongside the routing table.
Mixing hard-coded form codes with the route definitions is mildly
awkward; if more form-level gates land, they should move to a
dedicated config.

**Severity:** Low.

---

## 4. Future maintainability — when this hurts most

| Trigger | Why this file resists it |
|---|---|
| Adding a new portal | Requires: import wrapper, define helper, add routes block, add `EnforcePortalScope` handling, add login/forgot/reset routes. ~30 lines minimum. |
| Splitting a portal into named users (Phase K7) | Per-user tokens still live in the same namespace, so route table is unchanged — but the wrapper components must learn to fetch named-user metadata. The wrapper update is localised. |
| Multi-tenant SaaS | Every route becomes tenant-scoped. URL design (`/t/<tenant>/admin/…`?) is a single global decision that touches every `<Route path=…>` line. **This is the strongest reason to consider modularizing first.** |
| Removing a portal | Easy today — delete the routes block, delete the helper, delete the wrapper import. The 575-line file makes this safe to do in one diff. |
| Frontend code-splitting (lazy-load by portal) | Currently impossible without restructuring — every page is eagerly imported at the top of `App.js`. Initial bundle is therefore the union of all portals. |

The **lazy-loading point (last row)** is the maintainability-vs-perf
intersection. The bundle ships every portal to every user. A field
worker downloads the Admin and Dev portal code they will never see. As
the codebase grows, this becomes a measurable cost on mobile.

---

## 5. Future portal-modularization strategy (NOT a proposal for this turn)

If/when the operator decides to refactor, the cleanest target is:

```
/app/frontend/src/portals/
├── admin/
│   ├── routes.jsx        ← exports a <Route> subtree
│   ├── AdminShell.jsx    ← wrapper + chrome
│   └── pages/…
├── pm/
│   ├── routes.jsx
│   ├── PmShell.jsx
│   └── pages/…
├── hr/
├── safety/
├── shop/
├── dispatch/
├── field-leadership/
└── dev/

App.js becomes:
  <Routes>
    <Route path="/" element={<Hub />} />
    {publicRoutes}
    {adminPortal.routes}      ← lazy(() => import("@/portals/admin"))
    {pmPortal.routes}
    {hrPortal.routes}
    …
    <Route path="*" element={<NotFound />} />
  </Routes>
```

### Benefits
- Each portal owns its own route table → no central merge-conflict.
- Each portal can be `React.lazy()`-loaded → field worker doesn't ship
  admin code.
- Tenant-scoping (future SaaS) becomes a wrapper around each portal
  module, not a 190-line edit.
- New portals plug in by adding a directory.

### Costs
- **One-time refactor cost: probably 1–2 days.** Touches every route,
  but the routes are mechanical to move.
- Risk: cross-portal aliases (the `/admin/qaqc/:id`, `/pm/daily`, etc.)
  must be preserved exactly. A mistake here breaks deep links.
- Test surface: every `Require*` wrapper test must be re-verified after
  the move. The auth wrappers themselves should not need to change.

### When to do it
- **NOT now.** The user has explicitly deferred refactor work until
  Phase K auth migration is complete (per `PRD.md` and prior handoff).
- **Strongest natural trigger:** when SaaS multi-tenant work starts and
  the URL design has to change anyway. Doing both in one refactor is
  cheaper than doing them sequentially.
- **Second-strongest trigger:** when mobile bundle size becomes a
  measured user-facing complaint.
- **Third-strongest:** when a second developer joins and merge
  conflicts in `App.js` become routine.

Until then, the current 575-line `App.js` is honest, auditable, and
correct. It is not elegant, but elegance is not the optimization
function today — stability is.

---

## 6. What this review does NOT recommend

- ❌ Do not refactor `App.js` this turn.
- ❌ Do not collapse the cross-portal aliases.
- ❌ Do not change the `A`/`AP`/`P`/etc. shorthand convention.
- ❌ Do not move `/hr/employees` to use the `H` wrapper without
  confirming with the operator whether the omission was intentional.
  (Flagged in § 3.5 for human review only.)

The purpose of this document is to make a future refactor decision
**informed**, not to motivate it.

---

## 7. Recommendation summary

| Item | Recommendation |
|---|---|
| Refactor `App.js` into portal modules | **Defer.** Earliest natural trigger: SaaS multi-tenant. |
| Document the cross-portal alias rationale inline | **Add a 3-line comment** above the `/admin/qaqc/:id` aliases block when convenient. Not blocking. |
| Audit `/hr/employees` route — wrapped or unwrapped intentionally? | **5-minute check** by operator. Resolve either by adding `H(...)` or by adding an inline comment explaining the exemption. |
| Wrap `/tasks`, `/document-expirations`, `/po-requests`, `/project-health`, `/asset-transfers` consistently | **Optional polish.** Backend is canonical; wrapper would just normalize the surface. Defer with other refactor work. |
| Move `SITE_INSPECTION_CODE` out of `App.js` | **Defer.** Only matters if more form gates land. |
| Lazy-load portals (`React.lazy` + `Suspense`) | **Defer** until bundle size is a measured complaint. Couples naturally with the portal-modularization refactor above. |

End of review.
