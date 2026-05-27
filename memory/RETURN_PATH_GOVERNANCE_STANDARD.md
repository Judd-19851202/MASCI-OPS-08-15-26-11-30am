# Return-Path Governance Standard
## Platform-wide doctrine · 2026-05-27

> Every shared surface (a page reachable from more than one portal)
> must honor the same return-path inheritance contract. This
> document defines that contract so future shared surfaces inherit
> the behavior for free.

---

## 1 · The standard

A shared surface MUST:

1. **Never hardcode a back label.** The label must come from a
   `useReturnContext(fallback)` hook resolution.
2. **Always provide a `fallback`** — the meaningful default when
   no context is supplied (typically the list page name).
3. **Never invent a destination.** The path resolution is:
   `state.from.path` → `?fromPath=` → derived parent → fallback path.
4. **Use the canonical `BackLink` primitive.** No bespoke back
   buttons. No hand-rolled `<Link to="/...">  ← BACK</Link>` snippets.
5. **Never use `navigate(-1)`.** Browser history is not a reliable
   orientation surface (multi-tab use, refresh, deep-link from email).

---

## 2 · Authoring rule

When you write a new shared surface:

```jsx
import BackLink from "@/components/BackLink";
import { useReturnContext } from "@/lib/returnContext";

export default function ViewSomething() {
  const ret = useReturnContext({ label: "Incidents", path: "/admin/incidents" });
  return (
    <header>
      <BackLink to={ret.path} label={ret.label} variant="header" testId="back-link" />
      {/* ... */}
    </header>
  );
}
```

That's it. The hook handles every entry-point combination.

---

## 3 · Caller rule (when navigating to a shared surface)

When the upstream knows where it is (almost always true for portal-
side pages), it SHOULD pass `state.from`:

```jsx
navigate(`/pm/incidents/${id}`, {
  state: {
    from: {
      key: "pm-project",                              // optional, for telemetry
      label: t("Project Safety"),                     // required
      path: `/pm/projects/${projectId}/dashboard`,    // required
    },
  },
});
```

When the caller is just a list page (`/admin/incidents` list →
`/admin/incidents/:id` detail), the derivation will compute the
right label without `state.from`. Passing it explicitly is still
preferred for legibility and tests.

---

## 4 · Deep-link rule (when constructing a URL outside React Router)

For email links / shared URLs / PDF links that may land directly on
a shared surface, attach a `?from=<key>&fromPath=<path>` query:

```
https://mascidocs.com/admin/incidents/abc?from=email-digest&fromPath=/admin
```

The hook resolves `from=email-digest` to a registered context key
(see `SHARED_SURFACE_CONTEXT_MAP.md §2`). Unknown keys fall back to
the derivation path.

---

## 5 · Forbidden patterns

| Pattern | Why it's forbidden |
|---|---|
| `<Link to="/admin/incidents">← INCIDENTS</Link>` | Bespoke. Bypasses BackLink primitive. |
| `navigate(-1)` | History is not orientation |
| Inline string concatenation of label | Breaks i18n |
| Reading `document.referrer` directly | The hook does this safely; callers must not |
| Reading `location.state` directly for back-context | The hook owns this; callers must not |
| Persisting return context in `localStorage` / `sessionStorage` | Adds state · subject to staleness · forbidden |
| Mixing different `BackLink` variants on the same page | "header" for top bars · "body" for content sections · no exceptions |

---

## 6 · Telemetry (optional, future)

The hook MAY emit a `return.context.resolved` event with:
- the resolution path (`state` / `query` / `referrer` / `derived` / `fallback`)
- the resolved key
- the page key (`view-incident`, `view-capa`, etc.)

This lets us measure which entry-point flow is dominant for each
shared surface — useful when designing future entry points. **Out
of scope for the iter443 first cut.**

---

## 7 · Migration policy for existing shared surfaces

| Page | Status | Migration trigger |
|---|---|---|
| `ViewIncident.jsx` | **First migration** (iter443) | Field-reported P1 |
| `ViewInspection.jsx` (if exists) | Pending | Next field report or proactive sweep |
| `ViewMeeting.jsx` (if exists) | Pending | Same |
| `ViewCAPA.jsx` (if exists) | Pending | Same |
| Daily Report detail | Has own back link · not migrated yet | Out of scope · works correctly today |

The doctrine: **migrate one surface at a time, on the trigger of a
real field report or as part of a low-risk refactor pass.** No big-
bang migration.

---

## 8 · Acceptance criteria for any new shared surface

Before merging, the author must verify:

| # | Criterion |
|---|---|
| 1 | Uses `useReturnContext()` hook with a sensible fallback |
| 2 | Uses `<BackLink>` primitive (no bespoke back button) |
| 3 | No `navigate(-1)` anywhere on the page |
| 4 | Header `variant="header"` · body `variant="body"` · not mixed |
| 5 | A Playwright regression test covers ≥2 entry contexts |
| 6 | The `data-testid="back-link"` survives label changes |

---

## 9 · Sign-off

- **Author:** E1 · P1 governance refinement
- **Status:** 🟢 Standard published · binding on all future shared surfaces
- **Next reading:** `LOW_RISK_IMPLEMENTATION_PLAN.md`
