# TRACK 19.48 · Permission and Governance

## Route protection
- **Route:** `/admin/operational-intelligence/recipients`
- **Gate:** shared `A(...)` admin wrapper in `App.js` (identical to
  `/admin/system`, `/admin/audit-log`, `/admin/operational-intelligence`).
- **Behaviour matrix:**

| Actor | Result |
|---|---|
| Unauthenticated | Redirected to Admin Sign In (identical to other `/admin/*` routes). |
| Field / PM / Shop / Dispatch / HR | Redirected to Admin Sign In. |
| Safety-only | Redirected to Admin Sign In. |
| Admin / Super Admin | Page renders. |

## Backend API gates (already enforced in Track 19.45A)
All recipient/group CRUD endpoints use `require_admin`. The UI does
not weaken any gate — it only consumes the already-hardened admin API.
- 401 for missing token
- 403 for admin_only violations (e.g. Safety hitting corporate)
- 400 for validation errors (invalid email etc.)
- All responses are clean JSON. No HTML error pages surfaced.

## UI-level guardrails
- **No live send.** The recipient management page has zero references
  to `/dispatch`. Grep-locked.
- **No hard delete.** Deletion is `soft-deactivate` — the row stays in
  `morning_digest_recipients` with `active: false` for regulatory
  replay. Grep-locked (no "Delete" language in the UI).
- **Confirm dialog** on deactivate.
- **Deactivate-vs-Reactivate** button swaps based on current state so
  admins can never accidentally reactivate an active recipient (idempotent).
- **Governance note** describes exactly what mutations do and don't do.

## Audit
Every mutation flows through the Track 19.45A endpoints, which write to
`operational_intelligence_audit` via the shared engine. Track 19.46
already exposes those rows through `GET /audit`. The recipient page
does not need its own audit strip in this track — the Cockpit's Audit
drawer already surfaces the same rows filtered per-product.

## No-Auto-Decision
This page manages *who* receives digests. It does not decide *what*
gets sent, does not classify data, does not assign fault, and does not
issue automatic executive decisions. Same doctrine as every other OI
surface.
