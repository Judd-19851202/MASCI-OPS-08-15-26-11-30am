# Safety Meeting · Coaching Family Blueprint (iter270)

**Status:** Proposal — awaiting operator approval before implementation
**Author:** main agent (post-Sprint 2 correction)
**Date:** 2026-05-20

---

## 1 · Why this exists (the gap the operator named)

The Safety Meeting workflow currently has:

- philosophy framing (Sprint 2 K4·K5·K6·K7) ✓
- terminology alignment (iter267 audit) ✓
- visual context/action separation ✓
- breadcrumb / domain affordances ✓

It does NOT have:

- **embedded operational coaching infrastructure** ✗

Every other mature workflow on the platform already has a `HelpTipBlock` coaching family
backed by `/app/backend/guidance/tips.py` + `tips_es.py`:

| Workflow | Form-key family | Tip count |
| --- | --- | --- |
| Safety Incident | `incident`, `incident.location`, `incident.severity`, `incident.narrative`, `incident.witnesses`, `incident.corrective` | 18 |
| Field Write-Up | `writeup`, `writeup.facts`, `writeup.conversation`, `writeup.due-process` | 12 |
| Daily Report | `daily-report`, `.crew`, `.equipment`, `.materials`, `.narrative`, `.photos` | 21 |
| Pre-Op | `preop`, `.controls`, `.defects`, `.fluids`, `.tires-tracks`, `.signoff` | 17 |
| Equipment Checkout | `checkout`, `.condition`, `.photos`, `.return-expectations`, `.signature` | 14 |
| Time Verification | `time-verification`, `.discrepancy`, `.lunch`, `.overtime` | 12 |
| Time-Off Review | `time-off-review`, `.bereavement`, `.medical`, `.pattern`, `.vacation` | 13 |
| Crew Eval | `crew_eval`, `.calibration`, `.evidence` | 9 |
| Document Expirations | `document-expirations`, `.cadence`, `.cdl`, `.outreach`, `.triage` | 14 |
| Material Calculator | `material-calculator`, `.field-verify`, `.lead-time`, `.waste` | 12 |
| Dispatch (8 families) | `dispatch.*` | 30+ |
| Employee Lifecycle / Accountability / Time-Off / Doc-Exp / Fleet | — | full |
| **Safety Meeting** | **(none)** | **0** |

The Safety Meeting workflow — arguably the **highest-cadence operational artifact**
on the platform (daily/weekly per crew, 130+ topic library, 21 domains, bilingual) — is
the only major form that has **no embedded coaching**. That's the inconsistency.

---

## 2 · Architecture (mirror, no reinvention)

Use the existing pattern exactly. **Zero new components, zero new endpoints, zero new
schemas.** The contract is already proven across 14 workflows.

### Backend
- **File:** `/app/backend/guidance/tips.py` — append to existing `_TIPS` list
- **File:** `/app/backend/guidance/tips_es.py` — append to existing `TIPS_ES` map
- **Endpoint:** existing `GET /api/guidance/tips?form_key=…` (no changes)
- **Scope:** `["public"]` — Safety Meeting is a public-facing field form (same as
  `daily-report`, `incident`, `preop`). Anonymous foremen can fetch.
- **Validator:** existing `validate_tips_registry()` already enforces body ≤80 words
  (coaching, not docs) — keeps us honest on tone.

### Frontend
- **Component:** existing `<HelpTipBlock formKey="…" />` from `/app/frontend/src/components/HelpTip.jsx`
- **Mount points:** drop into `NewMeeting.jsx` at section boundaries (see §4 below)
- **Behavior:** collapsed by default · color-coded by `kind` · expand on tap · single-line collapsed footprint
- **i18n:** `useT()` resolves `title_es`/`body_es` automatically via merged registry
- **RBAC:** already handled by `_guidance_caller_scopes` → public tips always reachable

---

## 3 · Coaching content scope (Safety Meeting Coaching Family)

Following the operator's themes verbatim. Each tip is 1–3 sentences, field-foreman voice,
no LMS/motivational/compliance-robot framing. Target: **22 tips total** (matches Incident's
density: 4 form-root + 3–4 per section × 6 sections).

### Form-root family · `meeting` (4 tips)

| Kind | Theme |
| --- | --- |
| `why` | Why Safety Meetings are operational discipline, not paperwork — "if the meeting doesn't change what happens on the work, you held a meeting that didn't happen" |
| `who` | Who reads this — PM, Safety, HR (for attendance gaps), Admin, owner audits. The signature roster is the legal record |
| `next` | What happens after submit — attaches to project, weather, GPS, crew; if crew_size doesn't match Daily Report headcount, HR gets the discrepancy flag |
| `escalate` | When to stop the meeting and call — crew refusing to sign, hazard surfaced you can't control, language barrier you can't bridge → call Safety BEFORE submitting |

### Section 01 · Meeting Information · `meeting.context` (3 tips)

| Kind | Theme |
| --- | --- |
| `why` | Why crew_size, shift, weather, and high-risk flag matter — Safety's pattern review filters by these. A heat-stress meeting on a 95°F day with high-risk flag set surfaces for trend review |
| `mistake` | Common mistakes — leaving crew_size blank "to fill later", marking weather as Clear when it was 40°F at 5am, not flipping high-risk for a critical lift / confined space / shoring inspection |
| `when` | Timing — hold the meeting **before** the work, not at lunch. Pre-shift means the bullets land before the first cut |

### Section 02 · Topic & Discussion · `meeting.topic` (5 tips) — **densest section · this is where coaching pays off**

| Kind | Theme |
| --- | --- |
| `why` | Why the WHAT HAPPENS paragraph is the meeting — "the bullets without the incident pattern are pencil-whipping with bullet points" |
| `mistake` | Common mistakes — reading bullets without reading the pattern paragraph · picking a generic topic instead of one tied to TODAY's work · skipping the discussion after reading · saying "everybody knows this" and moving on |
| `example` | Example of good — "Today we're running a 6-ft trench on west side. Read trenching pattern. Asked Carlos to walk us through the spoil-pile rule. Asked Mike where the box stops if utility crosses." |
| `next` | What happens next — discussion notes feed Safety's pattern review; if you used Custom Topic three weeks running with no library pick, Safety flags it |
| `escalate` | When to stop reading bullets and stop the work — if the topic surfaces a hazard you didn't know was on site today (e.g. silica meeting, no respirators on truck), stop the meeting, fix the gap, restart |

### Section 03 · Attendees · `meeting.attendees` (4 tips)

| Kind | Theme |
| --- | --- |
| `why` | Why every attendee signs — "the signature is the worker's acknowledgment they heard the pattern. Without it, the record is your word against theirs" |
| `mistake` | Common mistakes — signing for someone who stepped away · adding a name without a signature "to come back later" · skipping subs because "they're not our crew" (they are, for this meeting) |
| `who` | Who's required — every person on the work today, including subs and PMs who are on site for the meeting. Visitors who walked through DON'T sign |
| `escalate` | When someone refuses to sign — document refusal in notes, do NOT pressure, tell Safety verbally. Stop Work Authority belongs to every signer; refusing is a signal worth investigating |

### Section 04 · Photos · `meeting.photos` (3 tips)

| Kind | Theme |
| --- | --- |
| `why` | Why 2 photos minimum — one of the crew gathered (proof of attendance density), one of the work area or hazard discussed. If the meeting was about trench safety, the photo should show the trench, not the parking lot |
| `mistake` | Common mistakes — selfie of just the foreman · blurry photo of the sign-in sheet · photos of unrelated equipment · taking the photos after the crew dispersed |
| `example` | "Crew of 7 around the toolbox, trench behind them at station 12+50, time stamp 6:42 AM" — a single frame that proves the meeting happened where it mattered |

### Section 05 · Conductor Signature · `meeting.signoff` (3 tips)

| Kind | Theme |
| --- | --- |
| `why` | Why the conductor signs last — the signature certifies the record is accurate AS SUBMITTED. Edits after submission are tracked and reviewed |
| `mistake` | Common mistakes — signing before the photos / attendees are complete · letting a non-foreman sign as conductor · forgetting to verify the conducted-by name matches who actually ran it |
| `next` | What happens after — PDF generated, attached to project, emailed if AUTO_EMAIL is on. If a corrective action came out of the meeting (e.g. "order respirators"), open a Safety Corrective Action — the meeting record is not the place to track follow-up |

**Total: 4 + 3 + 5 + 4 + 3 + 3 = 22 tips (EN + ES → 44 entries)**

---

## 4 · Insertion points (NewMeeting.jsx)

Single import. Five `<HelpTipBlock>` mounts. Zero new state. Zero re-renders.

```jsx
import { HelpTipBlock } from "@/components/HelpTip";

// Above Section 01 (form-root coaching, with counter — operator-approved pattern from Incident)
<HelpTipBlock formKey="meeting" className="mb-3" showCounter />

// Inside Section 01, after the GPS / context grid, before the weather chips
<HelpTipBlock formKey="meeting.context" className="my-3" />

// Inside Section 02, above the topic picker (REPLACES the K6 coaching strip with the
// richer registry-driven coaching — the strip becomes redundant once the family lands)
<HelpTipBlock formKey="meeting.topic" className="mb-3" />

// Inside Section 03, above the first attendee card
<HelpTipBlock formKey="meeting.attendees" className="mb-3" />

// Inside Section 04, above PhotoUpload
<HelpTipBlock formKey="meeting.photos" className="mb-3" />

// Inside Section 05, above SignaturePad
<HelpTipBlock formKey="meeting.signoff" className="mb-3" />
```

**Important nuance — K6 coaching strip:**
The Sprint 2 K6 coaching strip becomes structurally redundant once `meeting.topic`
HelpTipBlock lands above the same TopicPicker (both deliver "read WHAT HAPPENS first"
coaching). Proposal: **delete the K6 strip** when the family ships. Keeps the form
lean and unifies coaching surface. K7 breadcrumb and K4 context block stay (they're
data-driven affordances, not coaching).

**ViewMeeting coaching:**
Mature pattern (Incident) shows tips only on the **form**, not the **record view**.
ViewMeeting stays coaching-free — it's a read-only record, not a workflow.

---

## 5 · Mobile behavior

- `HelpTipBlock` is already mobile-tested across 14 workflows
- Collapsed footprint: 36px row · single chevron tap to expand · zero layout shift
- Each kind renders one row; 5 mounts × ≤5 tips = max ~25 rows of coaching on the form, all collapsed by default — visually ~150px of inert vertical space
- Same touch targets (44px effective hit area on the toggle button), same accent borders
- Pattern is identical to `NewIncident` which is the closest mobile-first cousin

---

## 6 · EN/ES approach

Mirror exactly:
- EN authored in `tips.py` (4-block prose, ≤80 words/body — validator-enforced)
- ES authored in `tips_es.py` keyed by `(form_key, kind)`
- Field Spanish, NOT machine-translated. Same voice / register as existing Incident ES tips
- `_merge_es()` at import-time merges into the registry — frontend sees both
- `useT()` chooses the right field at render — proven across all 14 families

ES tone benchmark: the iter269 K5 article rewrite already established the voice
(`PATRÓN REAL · lo que suele pasar`, "la cuadrilla", "el patrón del mundo real").
The coaching family ES will match that voice exactly.

---

## 7 · Operational scope (what this is NOT)

This is **strictly** coaching content delivery. It is NOT:

- a new component, new endpoint, new schema, new audit pattern
- a new admin surface, a new role, a new permission
- onboarding / first-time-user tutorials
- video, audio, interactive walkthroughs
- gamification, scoring, completion tracking
- corporate / motivational / LMS framing

It IS:
- a content gap-fill in an existing, proven registry
- 22 short field-foreman coaching tips
- 22 Spanish parallels in the existing ES file
- 5 single-line `<HelpTipBlock>` mounts in `NewMeeting.jsx`
- 1 deletion of the now-redundant K6 strip

---

## 8 · Role behavior considerations

- **Anonymous foremen** (most common Safety Meeting submitter) — see all tips (`scopes: ["public"]`)
- **Safety / HR / PM / Admin** signed in — see same public tips · no role-specific tip needed for Sprint A
- **Future opt-in (Sprint B)** — could add role-specific tips like `meeting.signoff` `kind: who` `scopes: ["safety"]` for Safety-only coaching ("you can re-open this meeting and add a corrective action"). NOT in initial scope; will only add if operator names a use case
- **Custom Topic** — `meeting.topic` family still shows; the coaching applies whether they use the library or write their own. The K4 context block correctly suppresses for Custom — coaching survives because it's about the meeting discipline, not the topic data

---

## 9 · Alignment with existing HelpTip architecture · Compatibility audit

| Concern | Status |
| --- | --- |
| Component reuse | ✅ Zero new components — `HelpTipBlock` is the canonical surface across 14 workflows |
| Endpoint reuse | ✅ Existing `GET /api/guidance/tips?form_key=…` handles this with no change |
| RBAC contract | ✅ `scopes: ["public"]` is the proven pattern for field forms (incident · daily-report · preop) |
| i18n contract | ✅ `tips_es.py` merge pattern is established · validator already runs at import |
| Caching | ✅ Existing `_tipCache` in `HelpTip.jsx` caches per `form_key` — coaching loads once per session per form section |
| Word-count guardrail | ✅ `validate_tips_registry()` enforces ≤80 words/body — keeps tone honest |
| Token-passing | ✅ `_fetchTips` already forwards all 7 portal tokens; no changes needed |
| Form prefix-ladder | ✅ `tips_for("meeting.topic", …)` will auto-include `meeting` form-root tips — same broad+narrow coaching pattern as `daily-report.crew` |
| Test coverage pattern | ✅ Mirror `test_iter210_incident_helptips.py` and `test_iter214_writeup_helptips.py` — pytest under `/app/backend/tests/` |

---

## 10 · Regression risk assessment

**Risk level: LOW** — and contained entirely to additive content.

| Surface | Risk | Mitigation |
| --- | --- | --- |
| Backend registry | Low | Pure data append to `_TIPS` and `TIPS_ES` · `validate_tips_registry()` runs at import · existing pytest in `tests/` covers the registry shape |
| Existing tip families | None | Append-only · no edits to existing entries |
| `NewMeeting.jsx` | Very low | 5 `<HelpTipBlock>` mounts are purely additive UI · no state/prop drilling · no form logic touched · K6 strip deletion is a single block removal |
| Mobile layout | Low | Collapsed footprint is ~36px per mount · 5 mounts = ~180px max, mostly hidden until tapped · pattern is mobile-proven on 14 forms |
| Frontend bundle size | Negligible | No new deps · content is fetched runtime, not bundled |
| i18n duplicate keys | None | tips_es keyed by `(form_key, kind)` tuples — no collision with the iter267 i18n duplicate keys flagged in `i18n.js` |
| Performance | None | Single `GET /api/guidance/tips?form_key=…` per section · cached client-side per form_key |
| ViewMeeting | None | No changes to ViewMeeting — coaching belongs on the form, not the record |
| PDF output | None | PDF generation paths untouched · coaching is form-only UI |
| Public form access | None | `scopes: ["public"]` matches existing public field-form contract |
| Sprint 2 K4/K5/K7 work | None | All three survive · only K6 strip is intentionally removed because the new `meeting.topic` HelpTipBlock supersedes it |

**Recommended test layer (after implementation):**
1. New `tests/test_iter270_meeting_coaching_family.py` — registry shape + EN/ES parity + scopes + word-count guardrail + endpoint sanity
2. `testing_agent_v3_fork` smoke pass on `/meetings/new` in EN and ES verifying all 5 mounts render, expand, and show correct titles

---

## 11 · Proposed delivery (single iteration, no scope creep)

**Iter270 — Safety Meeting Coaching Family (one shot)**

1. Append 22 EN tips to `_TIPS` in `tips.py` (form keys: `meeting`, `meeting.context`, `meeting.topic`, `meeting.attendees`, `meeting.photos`, `meeting.signoff`)
2. Append 22 ES counterparts to `TIPS_ES` in `tips_es.py`
3. Mount 5 `<HelpTipBlock>` instances in `NewMeeting.jsx` (1 import + 5 single-line JSX additions)
4. Delete the K6 coaching strip (now redundant)
5. Add `tests/test_iter270_meeting_coaching_family.py` (mirror iter210 incident test pattern)
6. Validate via testing_agent_v3_fork (frontend + backend)
7. Update PRD.md + this blueprint with shipped status

**Estimated impact:**
- `tips.py`: +~250 lines (data only)
- `tips_es.py`: +~250 lines (data only)
- `NewMeeting.jsx`: +6 lines net (1 import + 5 mounts − ~10 lines K6 strip removal)
- 1 new test file (~120 lines)
- Zero changes to any other file in the codebase

**No phase 2 promised, no follow-on Sprint planned, no scope expansion.** Single
iteration, ships clean, lands the coaching family at the same density as Incident.

---

## 12 · Operator decision points

Please confirm before implementation begins:

**A. Scope: 22 tips, 5 mounts, K6 strip removed, single iteration**
   - a) Approve as scoped above
   - b) Approve but adjust tip count per section
   - c) Approve but keep K6 strip alongside the new HelpTipBlock
   - d) Reject — different structure desired

**B. Tone benchmark**
   - The proposed tip themes in §3 are concise prompts, not the actual EN copy. Final tip
     bodies will match the field-foreman voice of existing `incident.*` and `writeup.*` tips
     (calm · specific · realistic · operationally framed · no LMS). Authoring will follow
     the Incident pattern exactly.
   - a) Approve voice — proceed
   - b) Want to see sample full bodies for 2-3 tips before I author all 22

**C. ViewMeeting**
   - Mature pattern: coaching on form, not on record view (matches Incident, Daily Report)
   - a) Confirm — ViewMeeting stays coaching-free
   - b) Want coaching on ViewMeeting too (would require extending Sprint 2 K4 split into the record view — out of pattern, not recommended)

**D. Test coverage**
   - a) Standard registry pytest (mirror `test_iter210_incident_helptips.py`) — recommended
   - b) Skip registry test; rely only on testing_agent_v3_fork
   - c) Both
