# Low-Risk Implementation Plan
## P1 Governance Refinement · Contextual Return-Path · 2026-05-27

> The smallest safe contextual inheritance layer. Five files
> touched. One new lib module. One Playwright regression spec.
> No backend, no auth, no routing rewrite, no shell rewrite.

---

## 1 · Files in the change set

| File | Status | Rationale |
|---|---|---|
| `frontend/src/lib/returnContext.js` | **NEW** | `useReturnContext(fallback)` hook · pure JS, no global state, fully testable |
| `frontend/src/pages/ViewIncident.jsx` | MODIFIED · 1 line | Use the hook instead of hardcoded `t("Incidents")` |
| `frontend/src/pages/IncidentsDashboard.jsx` | MODIFIED · 2 call sites | Pass `state.from` on navigate / Link so the dashboard's portal context survives the click |
| `frontend/src/pages/SafetyIncidents.jsx` | MODIFIED · 1 Link | Pass `state.from = { label: "Incident Center", path: "/safety-portal/incidents" }` |
| `backend/tests/pw_suite/test_contextual_return_path_iter443.py` | **NEW** | Playwright regression covering admin / PM / safety / direct entry |

**Total surface:** 3 file edits + 1 new lib + 1 new test file.

No `App.js` routing changes. No `BackLink` primitive changes. No
backend changes.

---

## 2 · Hook contract (`lib/returnContext.js`)

```ts
type ReturnContext = {
  label: string;   // human-readable, e.g. "PM Portal"
  path: string;    // route to navigate to
  key?: string;    // optional, for telemetry/tests
};

useReturnContext(fallback: ReturnContext): ReturnContext
```

Resolution order (the FIRST non-empty wins):

1. `location.state?.from` if it has `label` and `path`
2. `?from=<key>` query param (with optional `?fromPath=<path>`)
3. Derived from current `pathname` (per `SHARED_SURFACE_CONTEXT_MAP §3`)
4. `fallback` argument

The hook has **zero side-effects**, returns a stable object across
renders (memoized on resolution), and is safe to call inside any
component.

---

## 3 · Pathname-derivation matrix

Hand-written for readability:

```js
function deriveFromPathname(pathname) {
  // Most-specific to least-specific.
  if (pathname === "/admin/incidents") {
    return { key: "admin-incidents", label: "Incidents", path: "/admin/incidents" };
  }
  if (pathname === "/pm/incidents") {
    return { key: "pm-incidents", label: "Incidents", path: "/pm/incidents" };
  }
  if (pathname === "/safety-portal/incidents") {
    return { key: "safety-incidents", label: "Incident Center", path: "/safety-portal/incidents" };
  }
  // Prefix matches.
  if (pathname.startsWith("/admin/")) {
    return { key: "admin-console", label: "Admin Console", path: "/admin" };
  }
  if (pathname.startsWith("/pm/projects/")) {
    return { key: "pm-project", label: "Project Safety", path: pathname.replace(/(\/pm\/projects\/[^/]+).*/, "$1/dashboard") };
  }
  if (pathname.startsWith("/pm/")) {
    return { key: "pm-portal", label: "PM Portal", path: "/pm" };
  }
  if (pathname.startsWith("/safety-portal/")) {
    return { key: "safety-portal", label: "Safety Portal", path: "/safety-portal" };
  }
  if (pathname.startsWith("/hr/")) {
    return { key: "hr-portal", label: "HR Portal", path: "/hr" };
  }
  if (pathname.startsWith("/shop/")) {
    return { key: "shop-portal", label: "Shop Portal", path: "/shop" };
  }
  return null;
}
```

Note: matching is **prefix-based**, with the more-specific paths
(`/admin/incidents`) checked before the less-specific ones
(`/admin/`). Order matters.

---

## 4 · Reversibility

| Surface | Rollback ease |
|---|---|
| `lib/returnContext.js` | Delete the file |
| `ViewIncident.jsx` line 232 | One-line revert (`label={t("Incidents")}`) |
| `IncidentsDashboard.jsx` | Remove `state` prop from `Link` / `navigate` — non-breaking |
| `SafetyIncidents.jsx` | Same |
| Test file | Delete |

The change is **purely additive**. Removing the new code returns
the platform to exactly the prior behavior. No data migration. No
schema. No routing.

---

## 5 · Risk register

| Risk | Mitigation |
|---|---|
| Hook returns wrong label on a path we didn't anticipate | The fallback argument is always honored — the worst case is "label looks slightly off" rather than "navigation broken" |
| `location.state` is lost on full reload | Falls through to query param → derived → fallback. No data loss, just less rich label. |
| Two surfaces render the same label differently | Doctrine: caller-provided `state.from.label` is verbatim; derivation labels live in one constant. |
| i18n: derived labels are not translated | Derived labels go through `t()` at the call site (`ViewIncident.jsx`) — `t("Admin Console")`, `t("PM Portal")`, etc. The constants in the hook are English keys; translation happens in the consumer. |
| Test flake from `document.referrer` access in iframes | The hook reads referrer defensively (`try/catch`) and treats it as a soft hint only. |

---

## 6 · Sequencing

1. Write `lib/returnContext.js` and unit-test the derivation matrix
   (in-line via Jest if `__tests__` exists, otherwise via the
   Playwright spec).
2. Migrate `ViewIncident.jsx` line 232 to consume the hook.
3. Update `IncidentsDashboard.jsx` to pass `state.from` on the two
   navigation call sites.
4. Update `SafetyIncidents.jsx` Link with `state.from`.
5. Add `test_contextual_return_path_iter443.py` with five
   parameterized cases:
   - admin list → detail → back says "Incidents"
   - admin direct URL → detail → back says "Admin Console"
   - pm list → detail → back says "Incidents"
   - pm direct URL → detail → back says "PM Portal"
   - safety list → detail → back says "Incident Center"
6. Run the broader pw_suite to confirm no regression.

---

## 7 · Acceptance criteria

| # | Criterion | Verified by |
|---|---|---|
| 1 | Hook resolution order works (state > query > derivation > fallback) | Playwright (manual location.state injection via page.evaluate) |
| 2 | Admin list → detail → back label = "Incidents" | Playwright |
| 3 | PM list → detail → back label = "Incidents" | Playwright |
| 4 | Safety list → detail → back label = "Incident Center" | Playwright |
| 5 | Direct URL paste of `/admin/incidents/:id` → back label = "Admin Console" | Playwright |
| 6 | Back link `data-testid="back-link"` still present | Playwright (selector check) |
| 7 | No regressions in the existing 28 P0/P1 tests | re-run |

---

## 8 · Sign-off

- **Author:** E1 · P1 governance refinement
- **Status:** 🟢 Plan locked · ready to execute · 5 files · zero backend
- **Cross-refs:** `CONTEXTUAL_RETURN_PATH_AUDIT.md`,
  `SHARED_SURFACE_CONTEXT_MAP.md`,
  `RETURN_PATH_GOVERNANCE_STANDARD.md`
