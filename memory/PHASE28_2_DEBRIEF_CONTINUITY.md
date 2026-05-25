# PHASE 28.2 · Debrief Continuity
## iter430 · 2026-05-25

## Single module, two debriefs

The Day-1 and Week-1 debriefs share ONE backend module
(`routes/dispatch_day1_debrief.py`) and ONE React component
(`pages/admin/AdminDlsDay1Debrief.jsx` with a `variant` prop).
Two routes, one source of truth. Calm doctrine preserved.

| variant   | URL path                       | Question count | Markdown filename prefix          |
|-----------|--------------------------------|----------------|-----------------------------------|
| `day-1`   | `/admin/dls/day-1-debrief`     | 12             | `DLS_DAY1_LIVE_OPS_DEBRIEF_`     |
| `week-1`  | `/admin/dls/week-1-debrief`    | 12             | `DLS_WEEK1_LIVE_OPS_DEBRIEF_`    |

## Week-1 questions (Phase 28.2 refined operational set · DOCTRINE-LOCKED)
1. What operational friction repeated multiple times?
2. What workflows became naturally trusted?
3. What workflows caused hesitation?
4. Where did crews bypass the platform?
5. What operational continuity proved most valuable?
6. What felt unnecessary?
7. What should remain untouched?
8. What systems need stronger coaching?
9. What systems need less complexity?
10. What operational terminology confused users?
11. What mobile/device issues surfaced repeatedly?
12. What role lacked visibility into downstream operations?

The Phase 28.1 question set (14 questions · earlier generic prompts)
was REPLACED — not appended — to keep doctrine tight.

## Day-1 questions (preserved · doctrine-locked since Phase 19.1)
1. Where did dispatch hesitate?
2. What was difficult to find?
3. Did drivers understand shift start?
4. Did drivers understand assignment flow?
5. Was assignment issuance fast enough?
6. Did PM haul visibility help production awareness?
7. Did Shop breakdown continuity make sense?
8. Were any dropdowns confusing?
9. Were any wait states missing or unclear?
10. Where did users pause too long or become uncertain?
11. What felt unnecessary or overly complicated?
12. What should remain simple and untouched?

## Storage rules (UNCHANGED)
- Markdown file at `/app/memory/DLS_{DAY1|WEEK1}_LIVE_OPS_DEBRIEF_YYYY-MM-DD.md`.
- Same-day re-submission overwrites (operational reality > append-only audit).
- NO database storage. NO analytics. NO scoring.

## URL truth doctrine
- `POST /api/admin/dls/day-1-debrief` always writes a `DLS_DAY1_*` file
  even if the request body claims `debrief_type: "week-1"`. The URL is
  the source of truth, not the payload.
- Same applies in reverse for `POST /api/admin/dls/week-1-debrief`.

## i18n
Both pages render through `useT()` so EN ↔ ES toggling works the same
way it does on every other admin surface. Question labels are
authored in EN; ES surfaces fall back to the i18n catalogue.
