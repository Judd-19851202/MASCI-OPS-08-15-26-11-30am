# TRACK 19.47 · Operational Intelligence Cockpit

**Status:** SHIPPED · 2026-07-04.

## Purpose
One clean admin surface that replaces inbox scanning with a single
operational command view over all 11 Operational Intelligence products.

## Route
`/admin/operational-intelligence` (admin-only, protected by the shared
`A(...)` gate in `App.js`).

## Composition
The Cockpit is a **read/preview/dry-run shell** over the existing
engine. It does not compose digests locally, does not score locally,
does not manage recipients, does not send email. Every value comes from
the backend.

### Backend endpoints consumed
- `GET /api/operational-intelligence/summary` (new, additive · Track 19.47)
- `GET /api/operational-intelligence/{id}/preview`
- `POST /api/operational-intelligence/{id}/dispatch?dry_run=true`
- `GET /api/operational-intelligence/history`
- `GET /api/operational-intelligence/audit`
- (Recipient governance entry links) `GET /operational-intelligence/recipients` · `groups`

### Sections
1. **Header** — title + dry-run notice + Refresh + Registry JSON deep-link.
2. **Top strip** — Products count · LOW/MEDIUM/HIGH/CRITICAL buckets · dry-run notice · worst + best product · recent failures.
3. **Recipient governance entry** — read-only links to the Track 19.45A recipient/group JSON. Full CRUD UI deferred.
4. **Product grid** — 11 cards, each with score, attention chip, trend arrow + %, confidence, freshness, permission, schedule, last generated, last sent + recipient count, primary attention signal, and 4 action buttons.
5. **Preview drawer** — sandboxed iframe rendering backend HTML (14 canonical sections).
6. **Dry-run drawer** — status · dedupe key · recipient list preview · "live email NOT sent" reassurance.
7. **History drawer** — up to 25 rows per product from `/history`.
8. **Audit drawer** — up to 25 rows per product from `/audit`.

## Six-Pillar audit
- **Powerful** — one page answers "what is healthy / worsening / needs attention / was last sent / failed / where do I click".
- **Simple** — 11 cards, one strip, four drawers. No dashboard glitter.
- **Beautiful** — attention chips, coloured score arrows, calm typography, sandboxed iframe preview.
- **Trusted** — dry-run only; live-send button intentionally absent.
- **Proven** — 17 lock tests including hard bans on live-send parameters and fake-score literals.
- **Operational** — every card has a "Preview" and "History" click within one tap.

## Six-Pillar bar for future Cockpit widgets
Any future widget must survive:
> **"If this widget disappeared, would leadership make a worse Monday decision?"**

If no, do not ship it.

## Rollback
Remove the route in `App.js`, the nav entry in `AdminShell.jsx`, delete
`AdminOperationalIntelligence.jsx` and the 9 track docs, and revert the
`/operational-intelligence/summary` endpoint block in `routes.py`. Zero
schema touched. HIGH rollback safety.
