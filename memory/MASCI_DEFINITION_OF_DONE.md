# MASCI Operations Platform — Definition of Done

**Canonical reference.** No future closure / certification / RC track may
mark a feature CLOSED without explicitly mapping it to one of the
completion states defined here. Tracks that ship partial work must
explicitly declare **BUILT ONLY** or **WIRED ONLY** in their closure
ledger — silent partial closures are forbidden.

This document is permanent. It is loaded by every closure ledger as the
shared vocabulary for "done."

---

## Completion states

### 0 · NOT STARTED
No usable work exists.

### 1 · BUILT
Code, API endpoint, component, model, or service exists. The piece
compiles, lints, and unit-tests where applicable. **However:** no real
user can find or use it from a normal portal workflow.

Examples that are BUILT but NOT done:
- New endpoint exists at `/api/foo` but no frontend button calls it.
- New page component exists but no navigation links there.
- Migration helper exists but no admin UI surfaces the migration.
- Producer fans a notification but no recipient is rostered.

**Closure tracks may claim BUILT ONLY explicitly.**

### 2 · WIRED
The route / button / navigation / link from a real portal landing page
to the feature exists. The user can reach the surface. **However:** the
end-to-end workflow has not been proven against real data with real
permissions and a refresh.

Examples that are WIRED but NOT done:
- PM clicks "Team" on a job row, page loads, but Save returns 500 and
  no audit row is written.
- Admin can open the page but cannot persist a value because the API
  payload shape mismatches the form.
- Notification carries `link_url` to a route the recipient's token
  cannot satisfy → 403 on click-through.

**Closure tracks may claim WIRED ONLY explicitly.**

### 3 · OPERATIONAL
A real user can complete the workflow end-to-end with no manual
workaround. They can:
1. Find the feature from a normal portal landing page (no hidden URL).
2. Open it without 403/404.
3. Use it (add, edit, save, delete, query, render, etc.).
4. Refresh the page and see their work persisted.
5. Navigate back to it via the same path they used to arrive.
6. The relevant audit chain captures the action.

**OPERATIONAL is the minimum for any feature claimed as DONE in a
release-candidate context.** It is not sufficient on its own — that
threshold is DONE-DONE below.

### 4 · DONE-DONE
OPERATIONAL **plus** all of the following:

- **Tested.** Backend pytest + frontend lint + end-to-end smoke against
  the live preview backend. Test rows cleaned up.
- **Audited.** Every state change writes an audit row. Soft-delete
  semantics preserved. No historical mutation.
- **Notifications & email proven.** Where the feature emits or consumes
  bell notifications or emails, the producer is wired to the active
  roster (Phase 2B-2B), recipients resolve through the documented
  ROLE_CHAIN, deep links open routes the recipient's token can satisfy,
  and the leakage matrix is re-verified clean.
- **Deep links valid.** Every `link_url` shipped from a producer points
  at an existing route, with leading slash, no `null` / `undefined` /
  empty string.
- **Access correct.** No visible navigation surface lands a user on a
  403. No PM-visible link points at an admin-only or dispatch-only
  route unless the link itself is hidden behind a role check.
- **Permissions verified.** PM cannot edit a project they do not own.
  Co-PM scope works. Admin escalation works. Cross-portal scope
  filters work. PM cannot add roles they are not entitled to assign.
- **No test data left behind.** Every scratch user, scratch project
  assignment, scratch operational record, scratch notification, and
  scratch task is deleted in teardown. Cleanup is asserted with
  `count_documents == 0` against the scratch tag.
- **iPad + desktop proven** for any operator-facing surface (PM, FL,
  Safety, Shop, Dispatch field user).

A track may only claim **CLOSED** at the DONE-DONE level. Any lesser
state requires an explicit qualifier in the closure ledger:

> _"Phase X CLOSED — BUILT ONLY (no UI wired yet)."_
> _"Phase X CLOSED — WIRED ONLY (workflow not proven against real data)."_

---

## The Five-Pillar relationship to DONE-DONE

| Pillar | Minimum for OPERATIONAL | Minimum for DONE-DONE |
|--------|:-----------------------:|:----------------------:|
| Powerful | 9.0 | 9.5 |
| Simple | 9.0 | 9.5 |
| Beautiful | 9.0 | 9.5 |
| Trusted | 9.5 | **9.9** |
| Proven | 9.5 | **9.9** |

Trusted and Proven scores are the gating signals. A feature with high
Powerful/Simple but Trusted < 9.9 or Proven < 9.9 is not DONE-DONE.

---

## What DONE-DONE is NOT

DONE-DONE does **not** require:
- Spanish translation (unless explicitly in the track's scope).
- Mobile app shell (unless explicitly in the track's scope).
- PDF export polish (unless explicitly in the track's scope).
- Production data backfill (unless explicitly in the track's scope).
- Future analytics / dashboards on top of the feature.

The scope is **"a real operator can use the feature today in the live
platform"** — not "every conceivable extension exists."

---

## The car analogy (operator-facing summary)

A feature is not done because the engine compiles.
A feature is not done because the wheels are bolted on.
A feature is not done because the key is cut.

A feature is done when the operator can:
1. Find the car in the lot (navigation).
2. Open the door (no 403).
3. Sit in the seat (no 404).
4. Start the engine (workflow loads).
5. Drive it (workflow succeeds).
6. Park it (work persists).
7. Lock it (audit + permissions).
8. Come back tomorrow and it still works (refresh + return).
9. Get a real notification when something happens to it (bell + email + valid deep link).

If any of 1–9 fails, the feature is not DONE-DONE.

---

## Adoption rules

- This document is the **first reference** for every new closure ledger.
- Every closure ledger must include a `## Definition-of-Done compliance`
  section that maps each shipped feature to BUILT / WIRED / OPERATIONAL
  / DONE-DONE with a one-line justification.
- The RC-1 release gate is "every operator-facing feature on the RC-1
  checklist must be DONE-DONE." No exceptions, no asterisks.

---

## Revision history

- **2026-02-12** — Created during Track 14.0-RC1-DONE-DONE-CERTIFICATION-FIX-SWEEP.
  Initial canonical version.
