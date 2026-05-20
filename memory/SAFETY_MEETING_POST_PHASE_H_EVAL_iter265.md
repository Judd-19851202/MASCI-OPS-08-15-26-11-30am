# MASCI Safety Meeting · Post-Phase-H Structural / Workflow / PDF / Public-Readiness Evaluation
**Iteration:** iter265 · **Date:** 2026-05-20 · **Scope:** Assessment + recommendations only · No code changes.

This document is a **maturity-and-protection blueprint** for a system that has crossed the line from compliance documentation into operational judgment transfer. It extends — does not repeat — the iter260 structural evaluation.

The intent is to:
- Read the system as it actually sits at 136 topics
- Identify what's earned protection
- Sequence F1 (Public Read-Only Library) and F2 (Severity Hot-Filter) carefully
- Flag drift risks BEFORE outside eyes change the writing pressure

---

## Section 0 · Phase H state-of-the-system snapshot

### What is true today (verified)
- **136 topics · 21 operational domains · 22 picker chips (incl. "All")**
- 100% incident_pattern coverage in EN AND ES (136/136 in both)
- 100% severity coverage in EN (136/136); 0% in ES by design
- Severity distribution: **88 fatal_risk · 42 serious_injury · 6 lost_time**
- Library files: 44 (22 domain pairs + 2 aggregators), all modular, all under 40 KB; largest is `general.js` at ~37 KB / 20 topics
- Shared scaffold composer at `/lib/composeIncidentScaffold.js` (used both at template-load and at swap-back detection on submit)
- 5 new operational capture fields landed in iter260 (`crew_size`, `weather`, `shift`, `subcontractor_involved`, `high_risk_activity`) and now visible in NewMeeting Section 01

### iter260 findings now CLOSED
- D1 · Monolithic topic library → split into per-domain modular files ✅
- D2 · Missing operational capture fields → 5 new fields landed ✅
- D3 · Scaffold composition duplicated → unified via `composeIncidentScaffold.js` ✅
- D4 · Duplicate `conducted_by` field → removed ✅
- E1 · ES translation drift → 134/134 → 136/136 parity restored, all incident_pattern fields translated with field-foreman voice ✅
- E5 · Domain count drift after Batch 1 → 21 domains stable, key collisions zero ✅

### iter260 findings STILL OPEN (carry forward)
- 2.6 — Action Items follow-up loop (still write-only field; no closure tracking)
- 5.3 — Permalink stability for public-facing topic URLs (becomes blocker for F1)
- 6.3 — Operational Guidance Center cross-link (still ad-hoc)

### What's NEW in the system since iter260
- `severity` field on every topic (JS-only metadata, no UI exposure)
- 2 new General topics: `general_line_of_fire`, `general_lone_worker_field`
- Wellness category explicitly held to judgment-degradation framing (NOT corporate-wellness)
- `composeIncidentScaffold.js` shared composer
- Confined Space gained an explicit "rescuer dies too" pattern
- Mental health topic uses direct-question framing + 988 + EAP (operational, not therapy language)

---

## Section 1 · Structural findings (post Phase H)

### 1.1 — Library file health
**Status: HEALTHY**
- All 22 EN files between 2 KB and 38 KB; well under any reasonable file ceiling
- Aggregator (`index.js`, `index.es.js`) at ~2 KB each — pure import/spread, no logic; safe to extend
- No circular imports; no dead imports
- Each topic in EN has a corresponding key in ES (verified via Node import: 0 EN-only, 0 ES-only)

### 1.2 — Schema consistency across 136 topics
**Status: HEALTHY with one cosmetic note**
- All topics carry: `key`, `domain`, `title`, `category`, `severity`, `incident_pattern`, `hazards_reviewed`, `discussion_notes`, `references_cited`, `action_items`
- Phase B/C trucking topics also carry `role_context` (e.g., `["driver","lead","spotter"]`) — Phase H topics do not. This is **intentional asymmetry** (role_context is meaningful for trucking but not for, e.g., wellness) but currently not surfaced in UI. **Recommendation:** preserve as-is; reconsider only if/when F2 ships and Safety/Admin wants per-role packs.

### 1.3 — Severity vocabulary stability
**Status: HEALTHY**
- Only 3 values in use: `fatal_risk`, `serious_injury`, `lost_time`
- No drift toward custom labels, no per-domain inventions
- Vocabulary is small enough that F2's filter UI will be clean

### 1.4 — Domain boundary clarity
**Status: HEALTHY with one flagged overlap**
- 21 domains are operationally distinct EXCEPT:
  - `general.stretch_flex` overlaps `general.site_walk` (both describe pre-work huddle behavior). Currently both retained because they appear in real-world MASCI tailgate sequences as separate moments. **Recommendation:** flag for monthly review; do NOT merge unless a foreman tells you they want it merged.

### 1.5 — Aggregator efficiency
**Status: HEALTHY**
- Library is loaded as ES module imports at bundle time — no runtime cost beyond initial JS payload
- Total topic content (all 136 EN + 136 ES) under 400 KB raw JS, post-minify substantially less
- No memoization needed; topic library is static across the user session
- **F1 implication:** the same library can be served to a public route without backend hops

---

## Section 2 · Workflow findings

### 2.1 — Topic apply flow (NewMeeting)
**Status: STRONG**
- Selecting a topic now fills `topic`, `category`, `discussion_notes` (with scaffold), `hazards_reviewed`, `references_cited`, `action_items` — six fields in one tap
- Foreman has full freedom to edit the scaffold; submit-time detection knows whether the scaffold was edited

### 2.2 — Section 01 captures (E1)
**Status: GOOD**
- The five new fields (crew_size, weather chips, shift, sub-present, high-risk toggle) are operationally correct and DO improve incident retrieval quality
- **Minor:** Section 01 is now visually denser; on small phones (320–414px) it scrolls more before reaching topic selection. Acceptable trade-off but worth keeping in mind for F1's read-only version (which can omit these capture fields entirely).

### 2.3 — Bilingual swap on submit
**Status: STRONG**
- Confirmed working across iter263 and iter264 — submit in ES locks the language, generates the scaffold in ES, and won't accidentally revert if user toggles after submit

### 2.4 — Photo / signature flow
**Status: UNCHANGED FROM iter260**
- 2-photo minimum still operationally correct (proves the meeting happened, captures attendees)
- Signature pad works on small phones; no regressions

### 2.5 — JobPicker integration
**Status: WORKING**
- Auto-fills project name + number from current jobs; falls back to Custom Job freely

### 2.6 — Action Items closure loop (CARRIED FORWARD FROM iter260)
**Status: OPEN**
- Still a write-only string field. No tracking, no closure, no aging.
- **Recommendation:** Don't address as part of F1/F2. This is a separate "Action Items workflow" feature that deserves its own evaluation cycle once the operator decides whether MASCI wants closure tracking. Be careful — adding a tracking system here could push the form toward LMS feel.

---

## Section 3 · Mobile findings (414px primary, 320px stress)

### 3.1 — Topic picker scroll
**Status: GOOD**
- 22 chips horizontally scroll cleanly; counts update dynamically
- Topic list within a filtered domain is alphabetical-ish (insertion order); short titles render well

### 3.2 — Topic search modal
**Status: GOOD**
- Search through 136 topics is instant (client-side filter)
- Spanish search works against ES titles

### 3.3 — Incident-pattern scaffold on small phones
**Status: ACCEPTABLE, watching**
- A 5-sentence incident_pattern + 6 bullets fits in the textarea but requires scrolling to see the full scaffolded content
- The textarea auto-grows; foremen on small phones tend to edit-in-place rather than read-then-edit
- **Recommendation:** ship as-is for the form; for F1 print/PDF cards, render incident_pattern as a top block with visual separation (see Section 4.3)

### 3.4 — Section 01 capture density
**Status: ACCEPTABLE**
- 5 new fields added recently; section is denser but no overflow
- Weather chip row wraps cleanly at 414px

### 3.5 — Language toggle
**Status: GOOD**
- EN/ES toggle persists across reload; topic picker re-renders with ES titles instantly

---

## Section 4 · PDF / Print findings

### 4.1 — Current ViewMeeting render
**Status: ADEQUATE**
- Section 02 shows `topic`, `category`, `hazards_reviewed`, `discussion_notes`, `references_cited`, `action_items` as labeled key-value blocks
- The incident_pattern is embedded inside `discussion_notes` (because that's where it was scaffolded at template-load)
- This means the PDF shows the incident_pattern paragraph at the TOP of the discussion notes, followed by bullets — which is the intended visual hierarchy

### 4.2 — Read-aloud usability (NEW eval — per operator directive)
**Status: STRONG**
- Incident-pattern paragraphs are written in conversational sentences with clear sequence-of-events structure → reads naturally aloud at a tailgate
- Bullets that follow are short, action-oriented, scannable
- **Recommendation:** preserve this. Do NOT collapse incident_pattern into bullets for F1 print cards. The paragraph form IS the operational teaching unit.

### 4.3 — Foreman-in-truck usability (NEW eval)
**Status: GOOD with hierarchy note**
- A foreman parked in a truck cab, phone screen at arm's length, reading the meeting view: header is visible, topic title is visible, but the `WHAT HAPPENS · real-world pattern` header CURRENTLY appears as plain text inside the discussion_notes block — not as a visually distinguished caption
- **Recommendation:** when building F1 printable topic cards, render the header as a distinct visual element (small caps, accent color, or rule line) BEFORE the paragraph. This will visually anchor the foreman's eye and make the structure obvious without making it feel corporate.

### 4.4 — Tailgate readability
**Status: GOOD**
- Bullets are short, action-oriented, in active voice ("Stop work and shelter," "Inspect every ladder before use") — read well at conversational pace
- 6-8 bullets per topic is a deliberate ceiling; matches actual tailgate attention span

### 4.5 — Print clarity in sunlight
**Status: NEEDS REVIEW FOR F1**
- Current Meeting PDF (via ViewMeeting print path) is grayscale-friendly and reads fine in bright conditions
- For F1 print topic cards: recommend NO photographic backgrounds, NO subtle gray-on-gray text, single accent color only (MASCI red OK), body type at 11pt minimum, line height generous
- Sunlight test: hold the proposed card at arm's length, outdoors, midday — if any element disappears in glare, it fails

### 4.6 — Does incident_pattern visually overpower the bullets?
**Status: NO, but watch the trend**
- Current rendering: incident_pattern paragraph reads first, then bullets. The paragraph is denser but visually contained.
- **Risk:** if F1 print cards make the incident_pattern dominant (e.g., callout box, large quote treatment), it could overshadow the action-oriented bullets that foremen ACTUALLY use during the meeting
- **Recommendation:** in F1 topic cards, treat incident_pattern as **CONTEXT** (top third of card), bullets as **ACTION** (bottom two-thirds of card, larger weight). Maintain that ratio.

---

## Section 5 · F2 Severity Hot-Filter readiness assessment

### 5.1 — Architectural recommendation
- New route: `/safety/library` (Safety/Admin only) — separate from `/meetings/new` so field foremen never see it
- Route guard: `requireRole(['safety','admin'])` — denies field users entirely
- Reuses the existing `TOPIC_LIBRARY` aggregator; adds a filter layer
- Filter UI: chip row for severity (3 chips: fatal_risk, serious_injury, lost_time) + existing 22 domain chips + EN/ES toggle
- Result list: same topic cards as TopicPicker but with explicit severity badge (only visible on this route — never elsewhere)
- One-tap PDF generation: server-side render of selected topics into a print pack

### 5.2 — Boundary protections (operator-named requirements)
- ❌ **NEVER** display severity in `/meetings/new`, `/meetings/[id]`, public library, ViewMeeting, or any field-user surface
- ❌ **NEVER** expose severity in JSON responses to non-Safety/Admin users
- ❌ **NEVER** call this a "risk score" anywhere in code, UI, or docs — it is **operational metadata for prep**
- ❌ No gamification, no leaderboards, no dashboards counting "fatal-risk topics covered this month" — that's analytics theater
- ✅ Yes to: filter, list, PDF pack, EN/ES output, print-ready ordering

### 5.3 — Recommended capabilities (in priority order)
1. **MVP:** filter by severity + domain + language → list view
2. **MVP:** one-tap PDF pack of filtered set, print-ready, in selected language
3. **Phase 2:** save filter presets (e.g., "Paving high-risk kickoff" = paving + fatal_risk + EN)
4. **Phase 2:** "Combined pack" — fatal_risk topics from 2-3 domains for cross-trade jobs
5. **NOT in scope:** any field-visible severity badge; any analytics; any "compliance score"

### 5.4 — Severity vocabulary stability check before shipping
- Confirm with operator: are the 3 values (`fatal_risk`, `serious_injury`, `lost_time`) the right user-facing labels for the F2 chip row? Operator may prefer field labels like "Fatal Risk · Serious Injury · Lost Time" or "Critical · High · Moderate." Recommend the explicit fatal/serious/lost-time labels — they match the operational reality.

---

## Section 6 · F1 Public Read-Only Library readiness assessment

### 6.1 — Strategic positioning
F1 is genuinely uncommon in construction. Done right, it's:
- Recruiting credibility (foremen and superintendents Google MASCI and find a real safety library)
- Owner / GC confidence (RFP packages include a public-facing safety culture artifact)
- Industry differentiator (most contractors hide their safety content behind LMS paywalls)
- Bilingual credibility (Spanish parity at this content depth is industry-rare)

### 6.2 — What to expose publicly (recommendation)
- All 136 topic CONTENTS (title, incident_pattern, hazards_reviewed, discussion_notes, references_cited, action_items)
- Domain organization (22 chips, both languages)
- Topic detail pages with stable permalinks
- Printable single-topic cards (PDF download per topic)
- EN ↔ ES language toggle
- Search by title and body
- A modest "about this library" page that names MASCI as the publisher and explains the field-foreman voice intentionally

### 6.3 — What NOT to expose publicly (operator-confirmed boundary)
- ❌ Severity field (Safety/Admin operational metadata only)
- ❌ Individual meeting records, attendee lists, signatures, photos
- ❌ Action items written into specific meetings
- ❌ Internal comments, lessons-learned annotations, superintendent notes (none currently exist as separate fields — preserve that)
- ❌ Owner-facing branding language, sales positioning, marketing copy ON the topic pages themselves
- ❌ Identifying details that tie a topic to a specific project, person, or incident
- ❌ Cookie-tracking analytics that profile readers — keep public surface low-tracking

### 6.4 — Recommended route + permalink architecture
- Public root: `/library` (or `/safety` — operator picks the brand surface)
- Domain list: `/library/[domain-slug]` — e.g., `/library/concrete`
- Topic detail: `/library/[domain-slug]/[topic-key]` — e.g., `/library/concrete/concrete-pumping`
- Bilingual: append `?lang=es` OR use sibling routes `/library/es/...` (operator preference; recommend `?lang=es` for permalink stability — one URL per topic)
- Print card: `/library/[domain-slug]/[topic-key]/card.pdf` — server-render or client-render-to-PDF
- All routes server-rendered or static-generated for SEO and fast first-paint

### 6.5 — Mobile-first read-only render
- Topic page layout: header (domain breadcrumb · title · language toggle · print button) → incident_pattern block (top third) → hazards (compact bullet list) → discussion notes (the action bullets) → references (small text) → action items (small text)
- No form fields, no inputs, no edit affordances → cannot be confused with internal app
- Larger body type than the internal form (16-18px) because public reading is heads-down
- One vertical column at all sizes; no two-column attempts on tablet

### 6.6 — Print-friendly topic card spec
- Single page, US Letter (8.5×11) with 0.5" margins
- Top band: MASCI logo + domain breadcrumb + topic title (no marketing text)
- Middle: `WHAT HAPPENS · real-world pattern` as a small-caps eyebrow → incident_pattern paragraph
- Lower middle: hazards (3-4 lines), action bullets (the 6-8 lines), references (1 line)
- Footer: tiny `masci.com/library/[domain]/[topic-key]` permalink (for re-finding it on a phone)
- Black-and-white friendly (one accent stripe at top is OK)
- Spanish version of card identical structure, separate PDF file

### 6.7 — Search / discoverability
- In-library search field at the public root
- Domain chips identical to internal app (22)
- NO comments, NO reactions, NO ratings — no community features. The library is published, not crowdsourced.
- No "share this topic" social widgets — let the URL be shared organically without third-party tracking

### 6.8 — Branding posture
- Low-key MASCI branding (logo, name) — present but not loud
- The content carries the credibility, not the branding around it
- ❌ No "Our award-winning safety program" language
- ❌ No marketing CTAs ("Hire MASCI for your project!") on topic pages
- ✅ A separate `/about` page can carry company narrative if the operator wants it; topic pages stay clean

---

## Section 7 · Public / private metadata boundary matrix

| Field                       | Public (`/library`) | Safety/Admin (`/safety/library`) | Internal app (`/meetings/...`) |
|-----------------------------|:-------------------:|:--------------------------------:|:------------------------------:|
| `title`                     |          ✅          |                ✅                 |               ✅                |
| `domain`                    |          ✅          |                ✅                 |               ✅                |
| `category`                  |          ✅          |                ✅                 |               ✅                |
| `incident_pattern`          |          ✅          |                ✅                 |               ✅                |
| `hazards_reviewed`          |          ✅          |                ✅                 |               ✅                |
| `discussion_notes`          |          ✅          |                ✅                 |               ✅                |
| `references_cited`          |          ✅          |                ✅                 |               ✅                |
| `action_items` (template)   |          ✅          |                ✅                 |               ✅                |
| `severity`                  |          ❌          |                ✅                 |        ❌ (JS-only metadata)    |
| `role_context` (trucking)   |          ❌          |                ✅                 |        ❌ (not yet surfaced)    |
| Per-meeting `action_items`  |          ❌          |                ❌                 |               ✅                |
| Attendees / signatures      |          ❌          |                ❌                 |               ✅                |
| Photos                      |          ❌          |                ❌                 |               ✅                |
| GPS / location              |          ❌          |                ❌                 |               ✅                |
| `crew_size`, `weather`...   |          ❌          |                ❌                 |               ✅                |

**Rule of thumb:** the topic library is **published curriculum**. The meeting records are **internal operations data**. The boundary between the two is what protects both.

---

## Section 8 · Operational defects to fix BEFORE F1 or F2 ships

These are blockers, not enhancements:

1. **Topic-key URL slug stability** — current keys (`concrete_pumping`, `excavation_potholing_daylight`, etc.) are stable identifiers but were not designed as URL slugs. Verify nothing has spaces, mixed case, or special characters that would break the F1 permalink scheme. (Spot check: all 136 current keys appear to be lowercase + underscores — clean.)
2. **Helper text i18n sweep** — iter264 caught one untranslated string ("Auto-fills when you pick a topic below"). Run a final sweep of `NewMeeting.jsx` + `ViewMeeting.jsx` + `TopicPicker.jsx` looking for any English-only helper text before F1 exposes the user-facing strings publicly.
3. **Topic `category` field consistency** — current values include "Hazard-Specific", "Procedure / SOP", "Tool / Equipment Specific", "Stretch & Flex", "Other". F1 may want to expose these or hide them; either way verify no typos / variants across 136 topics.
4. **Decide F2 route guard mechanism early** — before either feature ships, confirm with operator how Safety/Admin role is currently determined (existing roles in MASCI auth) and whether F2 should reuse it or create a new role.
5. **PDF print path test under load** — current ViewMeeting → print works for individual meetings; F1 print-card and F2 print-pack will generate larger PDFs. Verify the chosen rendering library handles 5-10 topic packs without timeout.
6. **Action-Items closure loop** — same call as iter260: do not fix as part of F1/F2; address as its own evaluation when operator is ready.

---

## Section 9 · Recommended sequencing

### Recommended order: **F2 BEFORE F1**

**Why F2 first:**
- F2 is internal-only — failure modes affect MASCI Safety/Admin only, not the public
- F2 forces clean handling of the severity boundary, which becomes the test ground for the F1 public/private boundary
- F2 ships a working print-pack generator → which directly informs the F1 single-topic-card render
- F1 has bigger reputational stakes; ship the smaller, internal feature first to validate patterns

### Suggested phasing
**F2-A (Severity Hot-Filter MVP, ~1 cycle):** Safety/Admin route, role guard, filter UI, list view, single-language PDF pack
**F2-B (Filter Presets + Bilingual Pack):** save filter sets, EN+ES side-by-side packs
**F1-A (Public Library MVP, ~1-2 cycles):** routing, topic detail pages, mobile-first read-only render, permalinks, language toggle, search
**F1-B (Print Topic Cards):** single-topic PDFs, branded but plain, EN + ES
**F1-C (About page + credibility framing):** modest publisher context, no marketing CTAs

### Do NOT do
- ❌ Do NOT ship F1 and F2 in the same cycle — different audiences, different failure modes
- ❌ Do NOT introduce comments, ratings, or community features on F1
- ❌ Do NOT introduce analytics dashboards on F2 ("X topics covered this quarter")
- ❌ Do NOT rebuild the meeting form as part of either feature — leave NewMeeting alone

---

## Section 10 · Things the system has earned and must be protected

Hard-stop list. Touching these requires explicit operator approval.

1. **Field-foreman / superintendent voice in all 136 incident_pattern paragraphs.** This voice is the system's competitive moat. Sanitize it and the differentiator dies.
2. **Spanish parity in tone, not just translation.** ES versions are written in equivalent field voice, not in academic translation. Preserve this in every future addition.
3. **22-chip domain organization.** Don't collapse it into 8 buckets to look cleaner. Foremen filter by operational reality; UI theory shouldn't override that.
4. **Severity as JS-only metadata.** No drift toward UI exposure outside the F2 Safety/Admin surface. Severity is **operational prep data**, not field-facing classification.
5. **The 2-photo minimum on meetings.** It proves the meeting happened. Lowering it weakens the record.
6. **The bilingual swap-back logic on submit.** It silently fixes a real data quality issue. Don't touch unless the operator asks.
7. **No LMS scaffolding.** No quizzes, no completion certificates, no module gating, no "% mastery" counters. The library is published wisdom, not training software.
8. **88 fatal-risk topics tagged honestly.** Don't soften any to `serious_injury` because the word "fatal" makes someone uncomfortable in a review. The classification is operationally true; the discomfort is the point.

---

## Section 11 · Tone-Drift / Public-Exposure Risk Assessment

**This section is the most important one in this document.**

The defining strength of the system is operational authenticity. Once F1 makes content publicly visible, multiple forces will quietly push toward sanitization. This section names those forces, names the protections, and gives editorial guardrails.

### 11.1 — Tone characteristics that MUST be protected

These exist in the current library. They must continue to exist in every future addition.

- **Plainspoken realism.** "The fix is gloves first, then help." "Coffee + cold AC is not a fix. It's a delay." "'Just a quick look' is the line that kills crews."
- **Sequence-of-events storytelling.** Real incidents follow a recognizable shape — the topic should walk the reader through that shape. "The driver pulls off the shoulder for a tire check, steps out, gets hit by a passing motorist."
- **Operational phrasing.** "Tie-off above 6 feet." "Spotter at the corner of the cab." Not: "fall protection above the engineered height threshold."
- **Experienced leadership voice.** Reads as if a 30-year superintendent is talking to a 5-year foreman. Not as if an HR consultant is talking to an employee.
- **Practical prevention behaviors.** Every topic ends with what the foreman should DO, in language the foreman would actually say.
- **Field terminology.** "Boom," "kingpin," "stinger," "bed-up," "soft-side." Not: "articulated extension member," "fifth-wheel coupling apparatus."
- **Emotional realism around incidents.** "By the time fire department arrives the count is three." "The brain damage is done." "The drive home is the #1 way you die from this job." These lines work because they're honest.

### 11.2 — Tone patterns to explicitly avoid

These DO NOT currently exist in the library. They must not be introduced.

- **LMS wording.** ❌ "Upon completion of this module, the learner will..." ❌ "Demonstrate understanding of..." ❌ "Knowledge check:"
- **Poster language.** ❌ "Safety is everyone's responsibility." ❌ "Think before you act." ❌ "Together we are safer."
- **Generic awareness phrasing.** ❌ "Be aware of your surroundings." ❌ "Stay alert at all times." ❌ "Practice good housekeeping."
- **Legal disclaimers replacing operational content.** ❌ "Workers should consult their supervisor before performing any task that may pose a risk of injury or property damage."
- **HR / wellness drift.** ❌ "Take time for self-care." ❌ "We value your mental wellness journey." ❌ "Wellness is a lifestyle." (The current Wellness topics explicitly avoid this — protect it.)
- **Corporate branding language.** ❌ "Our industry-leading safety program..." ❌ "MASCI's commitment to excellence..." ❌ Any sentence that could appear on a sales deck and a safety topic interchangeably.
- **Over-polished marketing tone.** ❌ "Discover the keys to a safer workplace." ❌ "Empower your crew with knowledge."

### 11.3 — Public-read pressures (named and ranked)

Once F1 ships, these forces will appear in order of likelihood:

1. **Legal/insurance review pressure** — the most likely source of sanitization. Counsel will read "the drive home is the #1 way you die from this job" and want to soften it. **Response:** the line is a paraphrase of NHTSA's published research conclusions; cite the source, keep the line.
2. **Owner / client expectations** — a GC may say "your safety content uses strong language." **Response:** the strong language IS the content. Sanitization removes the teaching.
3. **Marketing review pressure** — once F1 is a credibility asset, marketing may want to add "Learn from MASCI's industry-leading safety program" framing. **Response:** branding belongs on `/about`, not on topic pages.
4. **HR / wellness drift** — the Mental Health and Drug/Alcohol topics are the easiest targets for "let's soften this." **Response:** the operational framing IS the wellness intervention. Direct-question framing has saved lives where soft framing has not.
5. **Subcontractor perception** — a sub may read a topic and feel implicated by the realism. **Response:** the topics describe industry patterns, not specific subs. Add an "About this library" disclaimer that names this explicitly if needed; do NOT soften the topics themselves.
6. **Outside interpretation of operational phrasing** — a non-construction reader may misread "smoldering ember" or "the wall comes in as a single slab" as graphic. **Response:** the audience is construction workers; the descriptions are operationally accurate; non-construction readers are not the primary user.

### 11.4 — Editorial guardrails (recommended)

Make these binding for any future addition or revision to topic content, public or internal.

- **Field-voice rule:** every new incident_pattern paragraph must be readable aloud at a tailgate without sounding like training software. Drafted by or reviewed by a superintendent.
- **Sequence-of-events rule:** every incident_pattern must describe a recognizable real-world sequence — not generic statements about risk.
- **Bullets-are-action rule:** discussion_notes bullets must be in the imperative voice ("Inspect the harness," "Mark the swing radius") — not declarative ("Harnesses should be inspected").
- **Bilingual parity rule:** every English change requires an equivalent-tone Spanish revision in the same change, by a translator or reviewer with construction-Spanish fluency. Not Google Translate.
- **No-LMS rule:** no quizzes, no completion tracking, no scoring vocabulary, no module language. Anywhere.
- **No-marketing rule:** no sentence in a topic body should be reusable on a sales deck.
- **Severity classification rule:** classifications match operational reality, not legal comfort. fatal_risk means the documented industry fatality pattern is present.
- **Operator-veto rule:** the original operator who defined the system's voice retains explicit veto over any content edit that changes the register. This is non-negotiable for protecting the moat.

### 11.5 — Recommended editorial review workflow (for additions/revisions post-F1)

1. **Drafted by:** Safety lead OR superintendent with field experience in the topic's domain
2. **Tone reviewed by:** the operator OR a designated superintendent with veto authority on register
3. **ES translation by:** a fluent construction-Spanish reviewer (not auto-translate)
4. **Legal/insurance review:** advisory only — they may flag concerns but cannot rewrite operational content; flagged concerns go back to step 2 for resolution
5. **Marketing review:** none. Marketing has no role in topic content.
6. **Final publication:** by operator approval; logged in changelog

### 11.6 — Long-term cultural direction (to be stated publicly in `/about` page)

The MASCI Safety Library exists to **transfer operational judgment**, not to document compliance.

- Compliance is a floor. We meet it. We do not stop there.
- Real safety culture comes from naming, in plain language, how incidents actually happen.
- Field workers — foremen, operators, drivers, laborers — are the primary audience. Everyone else is welcome but not the priority.
- Bilingual parity is not a feature; it is a non-negotiable, because roughly half the U.S. construction workforce speaks Spanish at work.
- The library exists because experienced superintendents and foremen built it. Their voice is the voice of the library.

This statement, or one like it, should appear on the F1 `/about` page in both languages. It is the public-facing version of the protection blueprint.

---

## Section 12 · Final assessment and immediate next step

### What this system has become
- An operational-judgment-transfer platform
- A bilingual, field-realistic, superintendent-voiced safety library
- A strategically distinct asset versus typical contractor safety software
- A maturity point at which content protection now matters as much as content expansion

### The biggest risk going forward
Not capability. Not features. Not scale.

**Drift away from operational authenticity** — through legal review, marketing review, HR drift, or well-meaning sanitization — is the biggest risk. The protections in Section 10 and the guardrails in Section 11 exist specifically to prevent this.

### Immediate next step (recommended)
1. Operator review of this document
2. Operator decision on F2-first vs F1-first sequencing (this evaluation recommends F2 first)
3. Operator confirmation of editorial guardrails (Section 11.4)
4. Operator confirmation of the public/private boundary matrix (Section 7)
5. Once the above four are settled — begin F2 architectural planning with a fresh ask_human cycle to scope the route, the role guard, and the MVP

No code changes until that gate clears.

---

**End of evaluation · iter265 · /app/memory/SAFETY_MEETING_POST_PHASE_H_EVAL_iter265.md**
