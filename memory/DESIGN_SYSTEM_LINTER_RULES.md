# Design System Linter Rules

> Built-time enforcement for the Operational Design System.
>
> Lives at `backend/tests/test_track_18_07_design_system_linter.py` and
> runs in the deployment gate. Every failure is a hard block on merge.
>
> Carve-outs are explicit, documented, and tested for resolution.

---

## What gets scanned

`frontend/src/**/*.{js,jsx,ts,tsx}` — recursively, with the following
hard exclusions:

- `__tests__/` directories
- `node_modules/`, `dist/`, `build/`
- `*.test.{js,jsx,ts,tsx}` and `*.spec.{js,jsx}` files
- `frontend/src/data/training.js` — historical narrative content; the
  Constitution explicitly permits prose-level legacy mentions
  (Track 18.04 disposition).

Code comments (line `// ...` and block `/* ... */`) are stripped before
scanning. Only displayed strings and identifiers participate.

---

## Rules

### R1 — Empty-state drift
**Forbidden** in user-visible JSX:
- `>No data<`, `"No data"`, `>Nothing here<`, `"Nothing here"`, `>N/A<`,
  `>No records<`, `"No records"`

**Required:** every empty state explains *what* this area is, *why* it
is empty, and *what to do next* (Design System §14).

### R2 — Error-state drift
**Forbidden:**
- `"failed to fetch"`, `"Failed to fetch"`, `"error loading"`,
  `>undefined<`, `>null<`, `JSON.stringify(err…`

**Required:** operational error language per Design System §17.

### R3 — Restricted-state drift
**Forbidden:**
- `"Forbidden"`, `"Unauthorized"`, `"Access denied"`, `"Access Denied"`,
  `"403 Forbidden"`

**Required:** *"Restricted for your role"* + `TxOpsRestricted`
component (Design System §16).

### R4 — Legacy workspace identity drift
**Forbidden** when wrapped in a quoted display string or JSX inner text:
- `"Dispatch Portal"`, `"PM Portal"`, `"HR Portal"`, `"Safety Portal"`,
  `"Shop Portal"`, `"Admin Portal"`, `"Admin Console"`, `"Office Portals"`,
  `"MASCI Hub"`

**Required:** the canonical workspace names from the Platform Language
Constitution (Track 18.03) — `Transportation Operations`,
`Project Management`, `Human Resources`, `Safety Operations`,
`Shop Operations`, `Administration`.

### R5 — CTA clarity
**Forbidden:** `"Click here"`, `"click here"`, `"More"` (except as a
documented tab label), `"Go"` standalone.

**Required:** action-oriented Title Case CTAs per Design System §9.

---

## Allow-list (documented exceptions)

Each exception lives in `LINTER_ALLOWLIST` and is keyed by file suffix +
exact token. Every entry has a justification comment in the linter
source.

| File | Token | Reason |
|---|---|---|
| `pages/Hub.jsx` | `Training Hub` | Functional sub-page name, not a workspace identity. |
| `lib/i18n.js` | All legacy workspace keys | Orphan translation keys kept as harmless passthroughs (Track 18.04). |
| `pages/SafetyHub.jsx` | `t("OPEN")` | CTA styled uppercase via CSS; documented Track 18.05 carve-out. |
| `components/admin/sidebar/domainMap.js` | `Asset Admin Console` | Functional sub-feature inside Administration. |
| `lib/usePageTitle.js` | `MASCI Hub` (match string) | Bookmark-rewriting source pattern; never rendered. |
| `lib/BrandingProvider.jsx` | `MASCI Hub` (fallback string) | Defensive legacy-tenant guard; canonical default is `MASCI`. |
| `lib/portalContinuity.js` | All legacy role labels | Internal session-routing label registry — back-link tooltips during impersonation. |
| `lib/returnContext.js` | All legacy scope labels | Internal back-link routing label registry. |
| `lib/permissions.js` | All legacy role display labels | Internal audit-event display registry (historical events keep their original labels for provenance). |
| `pages/Hub.jsx` | `scopeLabel: "{Legacy}"` lines | Audit-event scope labels written to the audit log; not user-visible. |
| `pages/ShopHub.jsx` | `"More"` / `t("More")` | Tab label, not a CTA. |

---

## How to add a new exception

1. **Justify it.** Why is the banned pattern correct in this exact place?
2. **Make it specific.** Add the most-specific token (whole line fragment
   if needed) so the exception cannot mask other drift.
3. **Add to `LINTER_ALLOWLIST`** with a code-comment explaining the
   carve-out and which document or track ratified it.
4. **Run the linter** — `python -m pytest backend/tests/test_track_18_07_design_system_linter.py`.
5. **Reference it** here.

---

## How developers use this

Local dev — before opening a PR:

```bash
python -m pytest backend/tests/test_track_18_07_design_system_linter.py
```

CI — automatic. The linter is part of the deployment gate; PRs with
drift fail the gate.

---

## Roadmap

The linter is intentionally **focused on the highest-signal drift
patterns**. Additional rules to consider:

- Status chip color-without-label drift (currently caught by Design
  System code review, not by the linter)
- Card anatomy presence checks (title + status + action where required)
- Layout-overflow static checks (`overflow-x-scroll` on mobile-critical
  paths)

These are deferred to Track 18.08 unless drift is observed earlier.

---

## Track 18.08 additions

### R6 — Status color without label
**Forbidden:** `<span>`/`<div>` elements with `bg-red-{500-700}` /
`bg-amber-{500-700}` Tailwind class AND empty inner text (no
characters between `>` and `<`), unless they carry an `aria-label`.

**Required:** every operational status must communicate by **color + label + icon** (Design System §5 + §20).

### R7 — Hardcoded mobile-breaking widths
**Forbidden:** `w-[Npx]` or `min-w-[Npx]` where N ≥ 800, unless the
parent file uses `overflow-x-auto` or `overflow-x-scroll` (i.e. the
wide content lives inside a controlled-scroll wrapper). The regex
explicitly excludes `max-w-[Npx]` via a negative lookbehind.

**Required:** wrap wide tables in `overflow-x-auto`, or use
responsive sizing per Design System §19.

**Allow-list (files with documented wide-table wrappers in a parent):**
- `components/MasterListPanel.jsx`
- `components/pm/PmJobsRead.jsx`
- `components/admin/PmDocSelectorPanel.jsx`
- `components/admin/UsersTable.jsx`
