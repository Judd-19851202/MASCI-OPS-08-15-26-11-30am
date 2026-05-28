# FIELD WALK CHECKLIST · INDEX

_Phase GOVERNANCE-INFRA-1 · Workstream 5 · 2026-05-28._

These checklists are run by **operators**, not developers, on the
**preview environment** before every production cutover. The goal is
to validate the platform against the **real workflows** field crews
use — under the real conditions field crews experience (weak signal,
mobile Safari, offline, photos, navigation between portals).

The walks should take **15 minutes per role** maximum. Anything
longer is over-engineered.

| Role | Checklist | Approximate time |
|---|---|---|
| Field Leadership (foreman / superintendent) | `FL.md` | 15 min |
| PM | `PM.md` | 15 min |
| Safety | `Safety.md` | 10 min |
| HR / Office | `HR.md` | 10 min |
| Mobile Safari (cross-cutting · all roles) | `MobileSafari.md` | 10 min |

---

## Why operators, not developers

Developers know how the platform is supposed to work. Operators know
how the platform actually feels. The trust failures we ship are the
ones that look fine to a developer doing a happy-path walk.

A walk is **valid** when:
1. The operator uses their actual device (iPhone or iPad, not a
   developer laptop).
2. The operator runs through the workflow exactly as they would in
   the field (not a contrived demo path).
3. The operator confirms each "PROVES" line in the checklist out
   loud or in writing.

---

## When to run a walk

* Before any production cutover that touches a trust surface.
* After any change to `lib/resiliency/*`, `lib/poCapabilities.js`,
  `lib/portalContext.js`, or `lib/returnContext.js`.
* After any change to `routes/po_requests.py`, `routes/incidents.py`,
  `routes/capa.py`, or `routes/draft_telemetry.py`.
* Quarterly even when nothing has shipped, as drift detection.

---

## When NOT to run a walk

* Routine doc-only changes.
* Internal refactors with zero diff to user-facing files.
* Test-only changes.

The Authority Mismatch Probe + pw_suite cover the deterministic part;
field walks cover the operational-feel part.
