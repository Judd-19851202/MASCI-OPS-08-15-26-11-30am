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

**OPERATIONAL is the minimum engineering state for Five-Gate Release
Governance Gate 2 (`LOCAL_ENGINEERING_VERIFIED`).** It is necessary, but
it is not sufficient for **DONE**.

### 4 · DONE
`DONE` is a reserved constitutional status. It may be claimed only when
OPERATIONAL **plus all five release-governance gates** are satisfied and
evidenced:

1. **CONTRACT_LOCKED** — governing artifacts, scope, dependency chain,
   and status vocabulary are accepted and non-contradictory.
2. **LOCAL_ENGINEERING_VERIFIED** — local implementation is operational,
   deterministic regression coverage passes, and touched-scope cleanup is
   complete.
3. **INDEPENDENT_ADVERSARIAL_CERTIFIED** — a certifying authority other
   than the implementing builder has executed adversarial validation and
   recorded the result.
4. **IMMUTABLE_RELEASE_CANDIDATE_VERIFIED** — source, build, environment,
   and evidence identity are frozen and verified as one immutable release
   candidate.
5. **DEPLOYED_OPERATIONAL_ACCEPTANCE_VERIFIED** — the deployed runtime is
   verified in the target environment and the required operational
   acceptance lane(s) have passed for the claimed scope.

**DONE means all five gates are VERIFIED.**

The implementing builder may produce evidence for Gates 1–2 and prepare
inputs for later gates, but may not self-assert Gate 3, Gate 5, or
`DONE` without the required independent and deployed evidence.

### 5 · Permitted release-governance vocabulary
The governing completion vocabulary is:

- `BUILT ONLY`
- `WIRED ONLY`
- `OPERATIONAL`
- `CONTRACT_LOCKED`
- `LOCAL_ENGINEERING_VERIFIED`
- `INDEPENDENT_ADVERSARIAL_CERTIFIED`
- `IMMUTABLE_RELEASE_CANDIDATE_VERIFIED`
- `DEPLOYED_OPERATIONAL_ACCEPTANCE_VERIFIED`
- `DONE`

Casual closure phrases, ungoverned approval shorthand, or bare
completion claims are not governing completion statuses and may not be
used as release authority.

Any lesser state requires an explicit qualifier in the closure ledger:

> _"Phase X — BUILT ONLY (no UI wired yet)."_
> _"Phase X — WIRED ONLY (workflow not proven against real data)."_
> _"Phase X — LOCAL_ENGINEERING_VERIFIED; independent adversarial certification still pending."_

---

## The Five-Pillar relationship to DONE

| Pillar | Minimum for OPERATIONAL | Minimum for DONE |
|--------|:-----------------------:|:----------------------:|
| Powerful | 9.0 | 9.5 |
| Simple | 9.0 | 9.5 |
| Beautiful | 9.0 | 9.5 |
| Trusted | 9.5 | **9.9** |
| Proven | 9.5 | **9.9** |

Trusted and Proven scores are necessary gates. A feature with high
Powerful/Simple but Trusted < 9.9 or Proven < 9.9 is not DONE.

---

## What DONE is NOT

DONE does **not** waive the Five-Gate law, but it also does **not**
require:
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

If any of 1–9 fails, the feature is not OPERATIONAL.
If any of the five gates is missing, failed, blocked, stale, or
unevidenced, the track is not DONE.

---

## Adoption rules

- This document is the **first reference** for every new closure ledger.
- Every closure ledger must include a `## Definition-of-Done compliance`
  section that maps each shipped feature or track to `BUILT ONLY`,
  `WIRED ONLY`, `OPERATIONAL`, the applicable Five-Gate milestone(s), or
  `DONE`, with a one-line justification.
- Every release ledger must show the status of all five gates and may use
  `DONE` only when each gate is VERIFIED.

---

## Revision history

- **2026-02-12** — Created during the Track 14.0 RC1 certification fix sweep.
  Initial canonical version.
