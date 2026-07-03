# TRACK 19.47 · Recipient Governance Entry

## Decision
**No full recipient management UI in this track.** Cockpit exposes a
lightweight, read-only entry point that surfaces links to the
already-shipped Track 19.45A admin JSON endpoints.

## Rationale
- Recipient CRUD is a full sub-feature of its own — deserves its own
  focused track with dedicated design, filtering, bulk-import UI, and
  audit strip.
- Building a rushed CRUD UI in the Cockpit would violate the
  "one purpose per surface" principle and add noise to a page that
  exists to answer "what needs attention Monday morning".
- The Track 19.45A backend is already fully governed and testable
  via curl; ops teams have not blocked on a UI.

## What the Cockpit exposes
A **read-only entry panel** immediately below the top strip with:
- Description of where recipient CRUD lives (Track 19.45A endpoints).
- Deep links (open in new tab):
  - `/api/operational-intelligence/recipients` — full recipient list JSON.
  - `/api/operational-intelligence/groups` — full group list JSON.

This is enough for admin ops to spot-check recipient state without
leaving the Cockpit, and for the future recipient UI track to slot in
without displacing anything.

## What is NOT in this track
- ❌ Add recipient form.
- ❌ Edit recipient form.
- ❌ Bulk-import UI.
- ❌ Group membership editor.
- ❌ Deactivation UI.
- ❌ Recipient audit strip UI.

Every one of those has a working admin API and can be shipped in a
future track (planned as Track 19.48 · Recipient Management UI) without
touching the Cockpit.

## Zero drift
No new recipient state · no new recipient collections · no new admin
gate. Everything additive.
