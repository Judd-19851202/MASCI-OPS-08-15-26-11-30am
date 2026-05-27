# Shared Surface · Context Map
## P1 Governance Refinement · 2026-05-27

> Every entry-point context for the Incident detail page — and the
> label the back button must show in each case. This is the
> reference the `useReturnContext()` hook resolves against.

---

## 1 · Context inputs (in resolution order)

The hook tries each input in order and returns the first non-empty
result. **The earlier the input, the more authoritative.**

```
1. location.state.from = { label, path }     ← explicit caller intent
2. ?from=<key>&fromPath=<encoded>            ← deep-link friendly
3. document.referrer pathname pattern         ← natural-navigation fallback
4. current pathname prefix                    ← derived best-guess
5. supplied default (e.g., "Incidents")       ← absolute fallback
```

---

## 2 · Context keys (the closed set)

| Key | Label | Default path |
|---|---|---|
| `admin-console` | Admin Console | `/admin` |
| `admin-incidents` | Incidents | `/admin/incidents` |
| `pm-portal` | PM Portal | `/pm` |
| `pm-incidents` | Incidents | `/pm/incidents` |
| `pm-project` | Project Safety | `/pm/projects/:id/dashboard` (resolved by caller) |
| `safety-portal` | Safety Portal | `/safety-portal` |
| `safety-incidents` | Incident Center | `/safety-portal/incidents` |
| `hr-portal` | HR Portal | `/hr` |
| `shop-portal` | Shop Portal | `/shop` |
| `incidents` | Incidents | `/incidents` (legacy hub) |

Adding a new context key requires:
1. Adding it to the table above
2. Adding it to the resolver in `lib/returnContext.js`
3. Adding a regression test in `test_return_context_resolution.py`

---

## 3 · Pathname → derived context

When no explicit `state.from` and no `?from=` query param is
present, derivation runs on the current pathname:

| Pathname prefix | Derived context | Derived label |
|---|---|---|
| `/admin/incidents` (exact, no further segment) | `admin-incidents` | "Incidents" |
| `/admin/incidents/:id` | `admin-console` | "Admin Console" |
| `/admin/…anything-else` | `admin-console` | "Admin Console" |
| `/pm/incidents` | `pm-incidents` | "Incidents" |
| `/pm/incidents/:id` | `pm-portal` | "PM Portal" |
| `/pm/projects/:id/dashboard` | `pm-project` | "Project Safety" |
| `/pm/…anything-else` | `pm-portal` | "PM Portal" |
| `/safety-portal/incidents` | `safety-incidents` | "Incident Center" |
| `/safety-portal/…anything-else` | `safety-portal` | "Safety Portal" |
| `/hr/…anything` | `hr-portal` | "HR Portal" |
| `/shop/…anything` | `shop-portal` | "Shop Portal" |
| `/incidents/:id` (legacy) | `incidents` | "Incidents" |
| any other | (passes through to supplied default) | (caller-provided) |

**Note:** the derivation runs on the **current** pathname (the one
the user is *currently on*), NOT on the destination. The intent is:
"I am currently inside the PM portal; back should say PM Portal."

---

## 4 · Referrer fallback

If `state.from` and `?from=` are absent, the hook may inspect
`document.referrer` (same-origin only) and apply the pathname
rules from §3 to it. This catches the "open in new tab" case where
location.state is lost.

Doctrine: **the referrer is a soft hint**. We never trust it for
security and never persist it.

---

## 5 · Explicit caller pattern (recommended for new code)

When navigating to a shared surface (Incident, CAPA, Inspection,
etc.) from a non-obvious upstream, the caller should attach a
`state.from` payload:

```jsx
// Inside the PM Project Dashboard, on an incident chip click:
navigate(`/pm/incidents/${incident.id}`, {
  state: {
    from: {
      key: "pm-project",
      label: t("Project Safety"),
      path: `/pm/projects/${projectId}/dashboard`,
    },
  },
});
```

The shared surface picks up `state.from` and uses it verbatim. No
inference needed.

---

## 6 · What the user sees per scenario

| Operator scenario | Back label | Back destination |
|---|---|---|
| Admin opens Incident from `/admin/incidents` list | "Incidents" | `/admin/incidents` |
| Admin opens Incident from Admin Hub link | "Admin Console" | `/admin` |
| PM opens Incident from `/pm/incidents` list | "Incidents" | `/pm/incidents` |
| PM opens Incident from PM Hub | "PM Portal" | `/pm` |
| PM opens Incident from `/pm/projects/:id/dashboard` | "Project Safety" | `/pm/projects/:id/dashboard` |
| Safety supervisor opens from `/safety-portal/incidents` | "Incident Center" | `/safety-portal/incidents` |
| Safety supervisor opens from Safety Portal hub | "Safety Portal" | `/safety-portal` |
| Email link drops user directly onto `/incidents/:id` (legacy) | "Incidents" | `/admin/incidents` (after legacy redirect) |
| Direct paste of `/admin/incidents/abc123` URL | "Admin Console" | `/admin` |

In every case, the operator knows where they are AND where "back"
will take them. Operational orientation preserved.

---

## 7 · Out of scope (deferred to follow-up passes)

| Item | Reason |
|---|---|
| CAPA detail · contextual return | Not raised in this incident. Same pattern applies. |
| Inspection detail · contextual return | Same. |
| Safety Meeting detail | Same. |
| Daily Report detail | Already has its own working back link. |
| Breadcrumb trail (multi-step) | Out of scope. The current page only needs ONE back step. |
| Persisting last-N visited surfaces in sessionStorage | Adds state. Out of scope. |

---

## 8 · Sign-off

- **Author:** E1 · P1 governance refinement
- **Status:** 🟢 Context map locked · derivation rules explicit
- **Next reading:** `RETURN_PATH_GOVERNANCE_STANDARD.md`
