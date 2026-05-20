# Safety Meeting System — Structural / Layout Evaluation
**iter260 · 2026-05-19 · operator-requested architectural review before content expansion continues**

Scope: complete operational review of the Safety Meeting / Toolbox Talk subsystem across topic library, form, scaffold, view/print, mobile, bilingual flow, public-readiness, and surface uniformity. No code changes this cycle — this document is the deliverable.

---

## 0 · System surfaces evaluated

| Surface | File / Route | Purpose |
|---|---|---|
| Topic library (EN) | `frontend/src/lib/meetingTopicLibrary.js` (2050 lines · 128 topics) | Source of truth for scaffolds |
| Topic library (ES) | `frontend/src/lib/meetingTopicLibrary.es.js` (1559 lines · 128 entries) | Bilingual mirror |
| Form schema | `frontend/src/lib/meetingSchema.js` | Field defaults |
| Topic picker | `frontend/src/components/TopicPicker.jsx` | Domain chip row + searchable list |
| Form page | `frontend/src/pages/NewMeeting.jsx` (~680 lines) | Public + admin form |
| Record view / print | `frontend/src/pages/ViewMeeting.jsx` (~335 lines) | Admin view + print PDF |
| List dashboard | `frontend/src/pages/MeetingsDashboard.jsx` | Admin / PM list grouped by job |
| Backend model | `backend/routes/safety.py · MeetingCreate / Meeting / MeetingSummary` (lines 106-141) | Pydantic schema |
| Backend API | `POST /api/meetings` · `GET /api/meetings` · `GET /api/meetings/{id}` · `DELETE` | CRUD |
| Public route | `/meetings/submit` (publicMode=true) | Subcontractor / shared-link submit |
| Admin routes | `/admin/meetings`, `/pm/meetings`, `/admin/meetings/:id`, `/pm/meetings/:id` | RBAC-scoped views |

---

## 1 · STRUCTURAL FINDINGS

### 1.1 — Topic library architecture
✅ **Strong**: clean separation of topic data (`meetingTopicLibrary.js`) from form schema (`meetingSchema.js`) from picker UI (`TopicPicker.jsx`). The `domain` + `incident_pattern` + `role_context` field additions slotted in cleanly without breaking any existing surface.

⚠️ **Mature-system smell**: EN file 2050 lines, ES file 1559 lines, both monolithic. Already past the 700-line threshold flagged by testing agent iter258 + iter259. Will hit ~3500 lines after Phase H Batch 5. Per-domain split (`/topics/mot.js`, `/topics/excavation.js`, etc.) with an `index.js` aggregator is the natural refactor and would reduce per-batch diff size by ~85%.

⚠️ **Field drift risk**: `meetingTopicLibrary.js` topics use the *array* pattern (`{ key, title, category, ... }`), while `meetingTopicLibrary.es.js` uses an *object* pattern (`{ <key>: { title, ... } }`). Both work, but they diverge from each other and new contributors will guess wrong half the time.

✅ **Schema enrichment was done correctly**: `incident_pattern`, `domain`, `role_context` are optional fields. Topics without them still render. No backwards-compatibility hacks needed.

### 1.2 — Form schema vs backend model mismatch
⚠️ **Hidden fields not in the strict schema**:
- Frontend sends `gps_lat`, `gps_lng`, `gps_accuracy`, `topic_template_key`, `submit_language` (per `NewMeeting.jsx` `buildMeetingDefaults` + submit handler)
- Backend `MeetingCreate` declares NONE of these but has `model_config = ConfigDict(extra="allow")` — so they are stored quietly but invisible to downstream consumers (TypeScript clients, OpenAPI users, the iter259 testing agent).
- Risk: someone adds a new field, it silently lands in Mongo, no migration, no documentation. This already happened.

**Recommendation**: promote the working hidden fields to first-class on `MeetingCreate`: `gps_lat`, `gps_lng`, `gps_accuracy`, `topic_template_key` (str, optional), `submit_language` (str, optional · "en"|"es"). `extra="allow"` can stay for future-proofing, but the known fields should be explicit.

### 1.3 — Scaffold composition logic duplicated
⚠️ **`composeNotes()` exists twice in `NewMeeting.jsx`** — once in `applyTemplate()` (when the user picks a topic) and once in `submit()` (when checking "is this still the pristine template content"). Inline duplication, identical logic, identical headers, identical bilingual rule. Carryover flagged by testing agent in iter258 and iter259.

**Recommendation**: extract to a single `lib/composeIncidentScaffold.js` helper that both `applyTemplate` and `submit` import. Tiny refactor, no behavior change.

### 1.4 — Domain count drift after Phase H Batch 1
Now 21 operational domains active. Library current state:
| Domain | Count | Phase H uplifted? |
|---|---|---|
| Pipe | 3 | ⏳ Batch 2 |
| Excavation | 4 | ✅ (incl. 2 new) |
| Grading | 5 | ⏳ Batch 3 |
| Concrete | 12 | ⏳ Batch 2 |
| Paving | 3 | ⏳ Batch 2 |
| Milling | 1 | ⏳ Batch 2 |
| MOT | 13 | ✅ (incl. 1 new) |
| Trucking | 12 | ✅ (Phase B/C) |
| Dewatering | 8 | ✅ (Phase D) |
| Shop | 8 | ✅ (Phase E) |
| Plant/Lab | 8 | ✅ (Phase F) |
| Airport | 2 | ✅ (Phase F) |
| Utilities | 2 | ⏳ Batch 3 |
| Rigging | 2 | ⏳ Batch 3 |
| Fall Protection | 5 | ⏳ Batch 3 |
| Electrical | 4 | ⏳ Batch 4 |
| Confined Space | 1 | ⏳ Batch 4 |
| Environmental | 3 | ⏳ Batch 4 |
| Wellness | 6 | ⏳ Batch 4 |
| Office | 8 | ✅ (Phase G) |
| General | 18 | ⏳ Batch 5 |

⚠️ **Structural observation**: Confined Space has only 1 topic and Milling has only 1. They survive the filter UX (chips show counts), but the next batch should probably add at least 2-3 more topics in each so the chip doesn't feel anemic when a user clicks it.

---

## 2 · WORKFLOW FINDINGS

### 2.1 — NewMeeting form section order
Current sections: **01 Meeting Info → 02 Topic & Discussion → 03 Attendees → 04 Photos → 05 Conductor Signature**

✅ **Order is operationally correct**. Foreman starts with WHO/WHERE, picks the topic, runs the talk, collects sign-ins, takes the photos, signs out. Matches actual field workflow.

⚠️ **Field redundancy**: `conducted_by` is collected TWICE — once in Section 01 (line 437-443) and again in Section 05 (line 634-639) as "Conducted By (Typed)". Both bind to the same `data.conducted_by`. Section 05 just re-displays the same input. Foremen on mobile experience this as "wait, didn't I just type this?" — and on slow mobile keyboards it's a real friction point.

**Recommendation**: in Section 05, display `data.conducted_by` as a read-only line ("Conducted by: <name>") with an "edit" link that scrolls back to Section 01 if they need to correct it. Or just drop the second field. Either way, single source.

⚠️ **`topic_category` is auto-filled but still editable** — confusing. The picker sets it, then the dropdown lets the user override. The override almost never matches operational reality (the topic IS its category). 

**Recommendation**: when a non-custom topic is loaded, lock or hide the category dropdown. Custom-topic flow keeps it editable.

### 2.2 — Scaffold render quality
✅ **`composeNotes` injection works as intended** — the `WHAT HAPPENS · real-world pattern` header surfaces the incident pattern at the top of the textarea where the foreman reads first. Field-tested in iter257 / iter258 / iter259.

⚠️ **Foreman read-aloud usability**: the textarea is a single dense block — header, paragraph, bullets, all in one box, no visual separation. Foremen reading aloud lose their place. A pre-formatted READ-ONLY scaffold panel above the textarea (with header in caps, paragraph in regular, bullets in list form) would be easier to read at tailgate / on phone. The textarea could become the "your notes from THIS meeting" field instead of the "scaffold + your edits" combo it is today. This would also let the saved `discussion_notes` field be cleaner (user-edited notes only, not a copy of the scaffold).

This is a **mid-priority enhancement** — not a defect — but it's the single biggest field-readability win available.

### 2.3 — Bilingual swap-back on submit
✅ **Works correctly**. Spanish-loaded topic + un-edited fields → saved as English canonical. User-edited fields stay as typed (per `swapIfPristine` logic). + a runtime `translateUserInput` call on edited ES content before save.

⚠️ **The swap-back logic is fragile**: it does string-equality between the loaded ES template and the form state to decide "is this still pristine?" A single trailing space, a single character typed and then backspaced (which leaves no change but may not be byte-identical in some keyboards), and the swap doesn't happen — the record gets saved with ES content but `submit_language=es`. The fallback `translateUserInput` then translates ES → EN at submit time, so the record IS still English in the end. Net: works, but the path is convoluted and any future contributor will struggle to reason about it.

**Recommendation**: store the original EN canonical fields explicitly on the meeting record (e.g. `topic_canonical_en`, `discussion_notes_canonical_en`) populated at template-load time. Then the saved record always has both the EN canonical and the user's typed (possibly ES) version side-by-side. Simpler mental model, easier audit, no fragile string-equality at submit.

### 2.4 — Photo requirement (2 minimum) is operationally correct
✅ **Photos confirm the meeting actually happened**. Group shot + topic board on whiteboard or tailgate. The 2-minimum is the lowest enforced gate that produces evidence. Good call to keep this.

### 2.5 — JobPicker integration
✅ **Strong**. Picking an active MASCI job auto-fills project_name + project_number, optionally location. Foreman doesn't retype.

⚠️ **Missing data captures** per operator's question:
- **Crew size** — currently inferred from attendee count, but not collected as a separate field. Useful for analytics ("how many crew were trained today on topic X").
- **Weather** — not captured. Conditions matter for the meeting context (heat, lightning, severe weather safety meetings). Low-friction capture: a small chip row at top of Section 01 (Clear · Hot · Rain · Cold · Wind · Storm-Risk) with multi-select. No free text.
- **Shift** — not captured. Day / Swing / Night. Tiny dropdown.
- **Subcontractor involvement** — not captured. Important when a sub crew is folded into the talk. Single checkbox: "Subcontractor crew present" + optional subcontractor name input.
- **High-risk activity flag** — not captured. Single checkbox at the top of Section 02: "Today involves a high-risk activity (trenching · crane · live traffic · confined space · energized work)". When checked, surface a small read-only callout linking the foreman to the matching domain.

None of these are bureaucratic — they're each a single chip / checkbox. Adds ~30 seconds to the meeting setup but transforms the analytical value of the record. **Recommend ALL FIVE**, gated behind operator approval.

### 2.6 — Action Items follow-up
⚠️ **`action_items` is collected as free text but never tracked downstream**. The foreman writes "fix the missing harness · cage tomorrow's brake job · re-train Juan on backing signals" and… nothing happens. There's no follow-up surface, no checkbox to close items, no link to the Daily Report system that could carry the action forward.

**Recommendation** (medium-term): convert action_items to a structured list of items with owner + due-date + status. Or at minimum: add a "Carry forward to tomorrow's Daily Report" toggle. Not blocking Phase H — but worth scoping next.

---

## 3 · MOBILE FINDINGS

### 3.1 — Page layout
✅ **Strong**: `max-w-4xl` centered, sticky top header, `space-y-6` between sections, `Section` component used consistently. Reads well at 320 / 375 / 414.

✅ **Touch targets**: 14h inputs (56px), 16h submit button (64px), 12h chip buttons. All well above 44px iOS minimum.

⚠️ **Chip-row count text at 320px**: at the tightest mobile width, the chip labels + count number become tight. Already verified scrolls without overflow (iter258, iter259), but the count text size (`text-[10px]`) is at the lower edge of legibility for gloved use.

**Suggestion**: increase count text to `text-[11px]` and add `font-tabular-nums` so the digit width stays consistent.

### 3.2 — Date / time pickers
✅ **Fixed in earlier iter** (iter256 mobile date/time bleed). Still good.

### 3.3 — Signature pad on small phones
✅ **Works**. SignaturePad component is field-tested across forms.

⚠️ **Conductor signature is buried in Section 05** — the foreman reaches it only after scrolling past attendees and photos. On the rare case where the foreman wants to sign first and let attendees come up one at a time, the flow forces a top-of-page-down sequence.

**Recommendation**: keep current order, but add a sticky "submit-state pill" at the bottom of the screen showing what's still missing ("Need: 1 photo · conductor signature") with a tap-to-jump. Light operational win.

### 3.4 — Bilingual toggle
✅ **Top-right of header** is the right spot. Consistent with the rest of the platform.

### 3.5 — GPS capture
✅ **"Use GPS" button** is well-placed inline with the location field. Good for foremen at remote sites who don't know the cross street.

---

## 4 · PDF / VIEW FINDINGS

### 4.1 — Print layout (ViewMeeting.jsx)
✅ **Professional**: `caution-stripe`, `MasciLogo` at 2xl, font-display titles, mono uppercase labels, proper print-watermark and print-section classes. Sections numbered 01-05. Looks like a MASCI Operations document, not a generic form.

✅ **Print footer with company info** (lines 307-329) — address, phone, email — renders only in print, professionally laid out.

⚠️ **Doc ID badge** (line 156-164) — `MTG-YYYY-NNNNN`. Good. Visible on screen AND print.

⚠️ **Long-topic overflow handling**: a Phase H topic with `incident_pattern` paragraph + 8 bullet discussion + 4-bullet hazards + 6-bullet action items will produce a `discussion_notes` value of ~3000 characters. On the print PDF, this renders as a single `whitespace-pre-wrap` block. At Letter size, that's ~2 pages of text for ONE section. If the meeting also has 20 attendees and 8 photos, the PDF is 5-7 pages.

This is **operationally fine** for incident-pattern topics where the depth IS the value — the printed packet becomes a take-home reference for the crew. But it deserves:
1. Explicit page-break-before on Section 03 (Attendees) so the topic doesn't half-break mid-paragraph.
2. Consider rendering the `WHAT HAPPENS · real-world pattern` header as a callout box in print (gray background, red left-border) so it stands out visually on paper.

⚠️ **Bilingual rendering on PDF**: PDF always renders in English (because the swap-back logic normalizes to canonical English at save time). This is correct for the official record. But — a Spanish-submitting foreman would benefit from the PDF showing a small `Submitted in Spanish` badge (already exists via `SubmitLangBadge` line 168-171). Good. Not changing.

### 4.2 — Photos on PDF
✅ **Grid layout** (3-up on desktop, 2-up on mobile) works for print.

⚠️ **Photo count exceeds layout**: 12+ photos in a single meeting (group shot + sub-crew + topic boards × 3 + before/after photos of a hazard correction) — the grid pushes attendees and signatures off the page. Not a defect, but for an audit-grade record, consider a "Photo summary contact-sheet" page break after Section 04 so attendees stay together.

### 4.3 — Signatures on PDF
✅ **Each attendee + conductor signature rendered as `<img>`**, clean borders, proper sizing.

⚠️ **No date/time stamp on individual attendee signatures**. The conductor signed at a specific moment, but attendees signed at unknown times relative to each other. For a perfect audit trail, each attendee row should carry a `signed_at` timestamp captured at the moment of signature submission (not the meeting submission).

**Recommendation** (medium): add per-attendee `signed_at` capture. Field crew won't notice, audit reviewers will.

---

## 5 · PUBLIC-READINESS FINDINGS

### 5.1 — Current public surface
- `/meetings/submit` → `NewMeeting publicMode=true` exists. Anyone with the link can submit a meeting.
- `/admin/meetings/:id` and `/pm/meetings/:id` → RBAC-scoped, requires auth.

**There is NO public read-only library surface today.** The topic content is locked behind the form. A subcontractor, owner, or industry peer cannot read the Safety Topic Library without an account.

### 5.2 — Recommended public read-only library architecture

**Proposed route**: `/safety/talks` (public, read-only) — index + per-domain + per-topic pages.

```
/safety/talks                          → domain index (22 chips, same as picker)
/safety/talks/<domain>                 → list of topics in that domain
/safety/talks/<domain>/<topic-key>     → single topic, full incident_pattern + bullets + refs
/safety/talks/<domain>/<topic-key>.pdf → printable single-topic card
```

**Branding**: Same `caution-stripe` + `MasciLogo` + red/black aesthetic. Reads as part of mascidocs.com, not a separate site.

**Bilingual**: Lang toggle in header. Same EN/ES library powers both renderings. Identical content to the in-form scaffold.

**What is exposed publicly**:
- ✅ Topic title (EN + ES)
- ✅ Incident pattern paragraph
- ✅ Hazards reviewed list
- ✅ Discussion notes / bullets
- ✅ References cited (OSHA, FMCSA, NFPA, etc.)
- ✅ Action items / follow-up list

**What stays PRIVATE**:
- ❌ Specific meeting records, attendee names, signatures, photos
- ❌ Project name / number / location / GPS
- ❌ Job-folder list / dashboard
- ❌ Doc IDs (MTG-2026-00345)
- ❌ Any admin / PM / dispatch features
- ❌ Foreman identities

**Why this is a strategic win**:
- Subcontractors can read the talk BEFORE the meeting → faster tailgate, better-prepared crew.
- Owners / GCs can verify MASCI's safety culture without an NDA call.
- Industry peers see MASCI as the operator who *publishes* its safety thinking — credibility uplift.
- Search engines crawl it → MASCI ranks for "asphalt plant safety," "trench shoring talk," etc. Free traffic + brand value.

**Implementation cost**: small — ~3 routes, 1 list page, 1 detail page, 1 PDF endpoint. The content already exists. The TopicPicker chip row already renders correctly.

### 5.3 — Permalink stability
**Recommendation**: topic `key` is the permalink slug (`/safety/talks/mot/live_traffic`). Once published, the key NEVER changes (already true in our system — keys are stable). If a topic is retired, return a 410 Gone or 301 redirect to the closest replacement, NOT a 404.

### 5.4 — Subcontractor usability test
At a subcontractor working the night shift on a dewatering job: open phone → scan QR posted on the pump trailer → land on `/safety/talks/dewatering/dewatering_night_work_struck_by` → read the incident pattern in 90 seconds → meeting tomorrow morning is 5 minutes shorter because everyone is pre-loaded.

This is the **highest-leverage feature** in the structural backlog. Strong recommendation to do it post-Phase-H.

---

## 6 · UNIFORMITY FINDINGS

### 6.1 — Across-surface aesthetic consistency
✅ **Strong**. All meeting surfaces use the same `caution-stripe`, `MasciLogo`, `font-display`, `font-mono`, red/black palette, `Section` component. The form, the view, the PDF, the list dashboard — all read as one product.

### 6.2 — HelpTips integration
⚠️ **Status check**: HelpTips were integrated for the Daily Report, DVIR, and Fleet workflows in iter256. The Safety Meeting form does NOT currently surface HelpTips at the section or field level. Given the maturity of the topic library, this is a noticeable gap.

**Recommendation**: add a single HelpTip on the TopicPicker explaining the domain chip row (one-time tutorial). Add a HelpTip on the discussion notes textarea explaining the `WHAT HAPPENS` header pattern. Two HelpTips, no more — preserve field speed.

### 6.3 — Operational Guidance Center
⚠️ **Status check**: Phase E of Guidance Center integration covered Fleet/DVIR. It does NOT currently cover Safety Meeting / Toolbox Talks specifically. Given that the Safety Meeting library is now a major operational system, it deserves a Guidance Center article — "How to run a 5-minute toolbox talk · choosing a topic · capturing attendance · using the scaffold."

**Recommendation**: 1 Guidance article in EN + ES. Mid-priority.

### 6.4 — Bilingual continuity
✅ **Strong**. Every surface (form, view, PDF, picker, chips) reads in the user's selected language. EN canonical at save time means the official record is unambiguous. No EN leakage confirmed across iter257/258/259 testing.

### 6.5 — Signature consent text uniformity
✅ **`BilingualConsent` component** used consistently across attendees, conductor sig, and view-record rendering. Good single source.

---

## 7 · OPERATIONAL DEFECTS (fix before public library ships)

Severity tiered.

| # | Sev | Where | Defect |
|---|---|---|---|
| D1 | P0 | `NewMeeting.jsx` Section 01 + 05 | `conducted_by` collected twice. Confusing on mobile. Single source needed. |
| D2 | P1 | `NewMeeting.jsx` | `composeNotes` duplicated. Extract to lib helper. |
| D3 | P1 | `safety.py · MeetingCreate` | `gps_lat`, `gps_lng`, `topic_template_key`, `submit_language` silently stored via `extra="allow"`. Promote to first-class. |
| D4 | P1 | `meetingTopicLibrary.es.js` | ES library uses object pattern, EN uses array pattern. Pick one shape for Batches 2-5. |
| D5 | P2 | `ViewMeeting.jsx` | No `signed_at` per-attendee timestamp. Audit gap. |
| D6 | P2 | `NewMeeting.jsx` Section 02 | `topic_category` is editable after auto-fill from picker — confusing. Lock when topic loaded. |
| D7 | P2 | `meetingTopicLibrary.*.js` | Both files at 2000+ lines. Per-domain split before Batch 2 ships keeps diffs reviewable. |

---

## 8 · ENHANCEMENT IDEAS (post-Phase-H scope)

Tier-2 — operationally valuable, not blocking.

| # | Where | Enhancement |
|---|---|---|
| E1 | NewMeeting form | Five new low-friction data captures: crew size · weather chip-row · shift dropdown · subcontractor toggle · high-risk activity flag. ~30 seconds added per meeting. Adds significant analytical value. |
| E2 | NewMeeting form | Sticky "submit gate" footer pill showing what's still missing with tap-to-jump. |
| E3 | NewMeeting form scaffold render | Render the scaffold as a READ-ONLY callout above the textarea; the textarea becomes "your notes from this meeting only." Cleaner record + better foreman read-aloud. |
| E4 | ViewMeeting PDF | Page-break before Section 03 (Attendees) for long-incident-pattern topics. Callout box around `WHAT HAPPENS · real-world pattern` in print. |
| E5 | Topic library | Per-domain file split + index aggregator. Refactor before Batch 2. |
| E6 | Backend | Promote hidden fields on `MeetingCreate`. |
| E7 | TopicPicker | HelpTip on chip row (one-time tutorial). HelpTip on discussion textarea explaining the header pattern. |
| E8 | Guidance Center | "How to run a toolbox talk" article in EN + ES. |
| E9 | Action Items | Convert from free text to structured list with owner + due date + status. Optionally link to Daily Report carry-forward. |

---

## 9 · FUTURE STRATEGIC IDEAS (post-launch)

Tier-3 — high impact, requires its own planning cycle.

| # | Idea | Notes |
|---|---|---|
| F1 | **Public Safety Topic Library** at `/safety/talks/<domain>/<key>` | The single biggest credibility / industry-leadership move available. Scoped in §5.2. |
| F2 | QR code on every printed topic card | Foreman prints a card for tailgate; QR links to the full topic page on a phone. |
| F3 | "Print Topic Card" feature | One-page printable scaffold a foreman could carry to the truck. Useful for low-signal sites. |
| F4 | Voice-driven meeting capture | Foreman speaks the action items into the phone, system transcribes + structures. Heavy lift but transformative for muddy-boots usability. |
| F5 | Annual rollup report per crew / per topic | "Crew 12 has been trained on Trench Safety 4 times this year. Last attendance gaps: Juan, Carlos (missed Aug)." Operational visibility for superintendents. |
| F6 | Subcontractor-specific topic packs | A sub onboarded for one project gets a curated list of relevant talks they can preview before kickoff. |
| F7 | Integration with Incident Reports | When an incident is filed, suggest the matching incident_pattern topic for the next toolbox talk. Closes the loop between "this happened" and "we discussed how it happens." |

---

## 10 · THINGS THAT SHOULD NOT BE CHANGED

Explicit list. These are working and changing them would damage operational value.

- ❌ **DO NOT remove the 2-photo minimum**. It's the lowest-friction gate that produces evidence of the meeting actually happening.
- ❌ **DO NOT change the Section order** (01 Info → 02 Topic → 03 Attendees → 04 Photos → 05 Signature). It matches the actual workflow.
- ❌ **DO NOT switch off the auto-EN swap-back on submit**. The official record stays English; that's a non-negotiable audit feature.
- ❌ **DO NOT lower the per-form requirements** (project_name, location, conducted_by, topic, conductor_signature, ≥1 attendee, ≥2 photos). These ARE the operational integrity of the system.
- ❌ **DO NOT add quizzes, certifications, gamification, or compliance scoring**. The system stays a TOOL for foremen, not an LMS for HR.
- ❌ **DO NOT redesign the chip row**. 22 chips horizontal-scroll works on 320px, was field-tested twice.
- ❌ **DO NOT split the `incident_pattern` paragraph into smaller fields** (e.g. "story", "lesson", "fix"). The single-paragraph treatment is what gives it field-foreman voice — fragmenting it produces LMS-speak.

---

## 11 · FINAL RECOMMENDED STRUCTURE DIRECTION

The system is **mature, internally consistent, and field-credible** today. The structural work needed before public library launch is small and well-scoped:

**Pre-public-library priority list (operator-approved scope)**:

1. **Resolve P0 defect D1** (duplicate `conducted_by`).
2. **Resolve P1 defects D2, D3, D4** (composeNotes extract, backend schema, ES library shape).
3. **Operator decision on E1** (five new data captures: crew size, weather, shift, subcontractor, high-risk flag) — high analytical value, low UI cost.
4. **Operator decision on E5** (per-domain library file split) — DO BEFORE Batch 2 if approved.
5. **Continue Phase H Batches 2-5** — content quality work continues regardless.
6. **Then ship the public library (§5.2)** — strategic credibility move.

The system has earned its place as a primary operational knowledge-transfer surface. The structural changes recommended are all in service of preserving its field-credible, plainspoken, mobile-first character as it scales to the public.

**Tone of the system, summarized**:

> _"This is what experienced field leadership talks about when nobody from the office is in the room. We wrote it down so the next crew doesn't have to learn it the hard way."_

That tone is the actual product. Protect it.

---

**Generated for operator review · iter260 · 2026-05-19 PM**
**No code changes this cycle. This is an architectural deliverable.**
