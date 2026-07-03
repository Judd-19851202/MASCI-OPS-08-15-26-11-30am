# TRACK 19.48 · Recipient Management UI

**Status:** SHIPPED · 2026-07-04.

## Route
`/admin/operational-intelligence/recipients` — admin-gated via shared `A(...)` wrapper in `App.js`. Reachable from the Cockpit's Recipient Governance entry ("Manage Recipients →").

## Backend contract (unchanged · reused from Track 19.45A)
| Verb | Endpoint | Purpose |
|---|---|---|
| GET | `/api/operational-intelligence/recipients` | List (with limit) |
| POST | `/api/operational-intelligence/recipients` | Add |
| PATCH | `/api/operational-intelligence/recipients/{id}` | Edit / reactivate (`active: true`) |
| DELETE | `/api/operational-intelligence/recipients/{id}` | Soft deactivate |
| GET | `/api/operational-intelligence/groups` | List |
| GET | `/api/operational-intelligence/products` | Product picker for the form |

Zero new backend routes. Zero new collections. Zero drift.

## UI sections
1. **Header** — title · subtitle · Back to Cockpit link · Refresh · Add recipient.
2. **Dry-run safety notice** — green banner: "Managing recipients does not send email. Deactivation is preferred over deletion for regulatory replay."
3. **Summary strip** — Total · Active · Inactive · Groups · Products represented.
4. **Add / Edit form** — email, display name, role, department, digest product picker, notes, active toggle. Client-side email regex validation with human-readable error.
5. **Filter bar** — search (email/name/role) · product filter · active-only toggle.
6. **Recipient table** — Email · Display name · Role · Product · Status chip · Updated · Notes · Edit + Deactivate/Reactivate.
7. **Groups panel** — Group ID · Name · Products · Member count · Created.
8. **Governance note** — explains the audit trail and non-email posture.

## Six-Pillar audit
- **Powerful** — full CRUD (add/edit/deactivate/reactivate) + search + filter.
- **Simple** — one page, three sections (form on demand, table always, groups below).
- **Beautiful** — status chips, calm spacing, no vanity metrics.
- **Trusted** — no live-send button anywhere; dry-run banner front & centre; deactivate not delete; `Are you sure?` confirm on deactivation.
- **Proven** — 16 lock assertions in `test_track_19_48_recipient_management_ui.py`.
- **Operational** — filters + search matter with 100+ recipients; product picker prevents typo-driven digest_type drift.

## Rollback
Remove the route line + lazy import in `App.js`, delete
`AdminOperationalIntelligenceRecipients.jsx`, revert the Cockpit
recipient governance entry back to "management UI deferred", delete the
lock test and the 5 track docs. **No backend changes to revert.** No
schema migration. Rollback risk: HIGH.
