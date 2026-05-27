# Context Trust Audit
## Phase TRUST-1 · 2026-05-27

> Does the operator know where they are? Does "back" go where they
> expect? Does project identity carry through every navigation?

---

## 1 · The orientation surface

A shared platform surface (a detail page reachable from more than
one portal) must answer three questions at every render:

1. **Where am I?** — page identity is clear in the header
2. **What context am I in?** — project / job / portal is clear
3. **Where does back go?** — return path is contextual to entry

---

## 2 · Coverage by surface

| Surface | "Where am I?" | "What context?" | "Where does back go?" |
|---|---|---|---|
| ViewIncident | ✅ | ✅ project name displayed | ✅ iter443 closed |
| ViewCAPA | ✅ | partial | 🟧 hardcoded (TF-003) |
| ViewInspection | ✅ | partial | 🟧 hardcoded (TF-003) |
| ViewMeeting | ✅ | ✅ | 🟧 hardcoded (TF-003) |
| ViewDailyReport | ✅ | ✅ | ✅ |
| PM Project Dashboard | ✅ | ✅ | n/a (top-level) |
| Safety Portal Incident Center | ✅ | n/a (list) | n/a |
| Admin Console hub | ✅ | n/a | n/a |
| Hub home (/) | ✅ | n/a | n/a |

---

## 3 · Return-path resolution contract

Per `lib/returnContext.js` (iter443):

```
1. location.state.from = { label, path }   (caller intent)
2. ?from=<key>&fromPath=<path>             (deep-link)
3. derived from current pathname            (best guess)
4. caller-supplied fallback                 (worst case)
```

Closed keys (per `SHARED_SURFACE_CONTEXT_MAP.md`):
`admin-console`, `admin-incidents`, `pm-portal`, `pm-incidents`,
`pm-project`, `safety-portal`, `safety-incidents`, `hr-portal`,
`shop-portal`, `incidents` (legacy).

---

## 4 · Open context findings

| ID | Sev | Where |
|---|---|---|
| TF-003 | T2 | ViewCAPA · ViewInspection · ViewMeeting still hardcode the back label |
| TF-008 | T2 | RedirectWithId drops location.state on legacy redirect routes |
| TF-017 | T2 | PM Project Dashboard incident chip not yet passing state.from |

---

## 5 · Anti-patterns to avoid

| Anti-pattern | Why forbidden |
|---|---|
| `navigate(-1)` | History is not orientation; multi-tab / refresh / deep-link break it |
| Inline string label concat | Breaks i18n + the phrase book |
| Reading `document.referrer` directly | Cross-origin / privacy issues; the hook owns this safely |
| Persisting return context in `localStorage` | Stale across tabs |
| Different `BackLink` variants on the same page | Cognitive cost |

---

## 6 · Doctrine compliance check

Every shared surface in `TRUST_CRITICAL_SURFACES.md §1.3 / §2.1`
will be migrated to `useReturnContext()` per the policy in
`RETURN_PATH_GOVERNANCE_STANDARD.md §7`. No big-bang. One surface
per trigger or sweep.

---

## 7 · Project identity carry-through

Beyond back labels, the operator's *project* context should never
silently switch. Today:

| Path | Carry-through |
|---|---|
| `/pm/projects/:id/dashboard` → click incident chip → `/pm/incidents/:id` | ✅ (when state.from wired — TF-017 pending) |
| `/admin/incidents/:id` → switch via "Edit Project" | ✅ project_number stays bound to the record |
| Daily Report submit → next-day Daily Report → project preload | ⚠ project-change confirm in iter442; soft-locked otherwise |

---

## 8 · Sign-off

- **Author:** E1 · Phase TRUST-1 audit lead
- **Status:** 🟢 Orientation covered for Incidents · pending for siblings
- **Cross-refs:** `CONTEXTUAL_RETURN_PATH_AUDIT.md` (iter443), `SHARED_SURFACE_CONTEXT_MAP.md`, `RETURN_PATH_GOVERNANCE_STANDARD.md`
