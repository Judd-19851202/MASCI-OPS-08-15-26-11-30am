# TRACK 19.49 · Platform Person Picker (Amendment)

## Data-source audit (preferred → fallback)
| # | Source | Endpoint | Exposes email? | Contains admin/portal? | Chosen? |
|---|---|---|---|---|---|
| 1 | Platform user directory (K4) | `GET /api/admin/directory/k4/users` | ✅ | ✅ (portals, super_admin) | **✅ Primary** |
| 2 | HR canonical roster | `GET /api/hr/employee-roster` | ❌ (safe projection) | — | ❌ — no email |
| 3 | Public employees roster | `GET /api/employees` | ❌ (safe projection) | — | ❌ — no email |
| 4 | Manual email entry | — | — | — | ✅ Preserved as fallback |

## Why the K4 directory is correct
- **Emails are already there.** Every K4 user row has `email`, `name`,
  `portals`, `is_super_admin`, `disabled`, `mirrored`.
- **Already authorized.** These are the people the platform has
  authenticated. If a person isn't in K4, they don't have platform
  access — putting them on an intelligence digest is intentional
  (external stakeholder / shared inbox), and the manual add path
  covers that.
- **Safe.** The endpoint is admin-gated (`require_admin_strict`).
  Reading it is a no-op on HR / user-account state.

## Picker contract
- **Read-only.** No POST/PATCH/DELETE calls against `/admin/directory`
  or `/hr/*` from this page (lock-tested).
- **Never creates platform users.** The picker cannot invite, sign up,
  or provision — it selects existing entries only.
- **Never mutates HR records.** Grep-locked.
- **Only writes to** `POST /operational-intelligence/recipients/bulk-import`.

## Row payload (what we persist)
For each selected directory user, we insert a recipient row with:
- `email` — from `user.email`
- `display_name` — from `user.name`
- `role_label` — synthesised as `directory · <portals>` (+ ` · super_admin` when applicable)
- `notes` — `"Sourced from platform directory (user_id: <k4-user-id>)"` — the source_reference
- `digest_type` — the target product picked in the UI
- `active` — true

The `user_id` in the notes field is the traceback pointer — no schema
change, but every directory-sourced recipient is forever tied back to
its canonical user record.

## Dedupe behaviour
- **Client-side hint.** Users already subscribed to the *target*
  product (based on the current in-memory recipient list) are
  rendered dimmed with "already subscribed" and their checkbox is
  disabled. Prevents wasted submits.
- **Server-side guard.** `bulk_import_recipients` in `recipients.py`
  dedupes by `(email, digest_type)` regardless of what the UI sends.
  Second line of defence.

## Manual add preserved
The single-recipient Add form and the paste-list tab remain available.
The directory picker is **preferred** (default tab, safety note calls
it out explicitly), not **exclusive**. Shared inboxes, external
stakeholders, and one-off addresses continue to flow through the
manual/paste paths.

## Zero drift
- 0 new backend endpoints.
- 0 new collections.
- 0 mutations to HR data.
- 0 mutations to platform-user data.
- 0 permission drift — admin-only end-to-end.
