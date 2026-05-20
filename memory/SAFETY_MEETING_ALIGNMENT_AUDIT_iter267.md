# MASCI Safety Meeting · Operational Alignment Audit
**Iteration:** iter267 · **Date:** 2026-05-20 · **Scope:** Concrete, actionable findings only · No code changes.

First iteration of the **Operational Alignment Maintenance** category. Scope is narrow on purpose — the Safety Meeting workflow, which after Phase H + F2-A is the visible "behind" surface in an otherwise maturing platform.

This is NOT a redesign. This is a list of **specific, fixable, operationally meaningful gaps** with file/line/string evidence so each can be picked up as a small refinement iteration under the Operational Value Gate.

Findings are prioritized at the end (§K) and sequenced (§L). All sections produce findings of the form: **EXACT location · EXACT change · WHY**.

---

## A. Coaching gaps · the form provides input fields, not coaching

The form was built when topics were generic toolbox talks. After Phase H, every topic is an incident-pattern teaching artifact. The form's coaching text does not reflect that shift.

| # | Location | Current state | Gap |
|---|---|---|---|
| A1 | `NewMeeting.jsx:594` · `t("Pick a topic — Category & all fields below auto-fill")` | Describes the *mechanic* (auto-fill) | Does not explain the *operational purpose* (read the incident_pattern aloud at the tailgate). New foreman doesn't learn how to use the library philosophy. |
| A2 | `NewMeeting.jsx:603-606` · footer string `"{N}+ heavy civil / highway topics with prefilled hazards, key points, references, and action items."` | Sells the count | Does not name `incident_pattern` or the field-foreman voice. Outdated framing post-Phase H. |
| A3 | `NewMeeting.jsx:641` · `t("Key points, questions, lessons learned...")` placeholder on Discussion Notes | Generic LMS-flavored placeholder | After applyTemplate runs, this field now holds a `WHAT HAPPENS` paragraph + bullets. Placeholder language pre-dates the structure and doesn't tell the foreman what's in it. |
| A4 | `NewMeeting.jsx:617` · `placeholder="e.g. Heat Stress Prevention, Trench Safety, Silica Awareness"` (NOT translated) | Three example topics hardcoded English | Placeholder leaks English to ES users + doesn't reinforce the 136-topic library. Could be `t("Pick from the topic list above — or type a custom topic here")`. |
| A5 | Section 02 has no callout naming the `incident_pattern` paragraph after a topic loads | The scaffolded notes appear without explanation | A 1-line coaching strip ("This is a real-world incident pattern — read it to the crew before the bullets") would transfer the system's intent to first-time foremen. |
| A6 | No coaching about the `high_risk_activity` toggle | Just a checkbox | A foreman doesn't know what threshold flips it. A tooltip explaining "Trenching · live traffic · confined space · overhead lines · hot work · etc." would align with the 88 fatal_risk topics. |

**Action items:** 6 specific helper-text edits + 1 new callout strip + 1 tooltip on the high-risk toggle. None require new components.

---

## B. Help-surface staleness · `/guidance` exists but lags Phase H

| # | Location | Current state | Gap |
|---|---|---|---|
| B1 | `/guidance` article `public-toolbox-talks` ("Safety Meetings & Toolbox Talks") | Body written before Phase H · uses "topic of the day, hazards, anything new" framing | No mention of `incident_pattern`, no mention of the 136-topic curated library, no mention of bilingual parity, no mention of the operational-judgment-transfer philosophy. Reads like a generic toolbox-talk explainer. |
| B2 | Same article · Spanish counterpart not verified for parity | Likely English-only or auto-translated | A Spanish-speaking new hire opening this article from `/guidance` may get poorly aligned content. |
| B3 | `/guidance` has no `safety-meeting-foreman` track for foremen running meetings | Article aimed only at attendees ("Sign in. Listen. Sign out.") | Missing peer-level article for foremen on how to USE the library (pick topic → read the pattern → run the meeting). The foreman is the user who's most under-coached. |
| B4 | No link from `NewMeeting.jsx` header to the guidance article | Direct route only | First-time foreman opening `/meetings/new` has no help affordance. A small "How this form works →" link to the guidance article would close the loop. |

**Action items:** 1 article rewrite + 1 ES verification + 1 new article + 1 link in NewMeeting header.

---

## C. Terminology consistency · fragmented across the codebase

Cross-codebase search (current state):

| Term | Occurrences | Surfaces |
|---|---|---|
| "Site Safety Meeting" | 8 in frontend | Form title, PDF title, MeetingsDashboard breadcrumb · the **canonical** internal-facing label |
| "Safety Meeting" | 33 | Generic uses in i18n keys, comments, dashboard labels |
| "Toolbox Talk" | 6 | CheatSheetCard.jsx, meetingSchema.js comment, i18n.js (`"Inspections · Toolbox Talks · Incidents · JHPs..."`), OperationalGuidanceCenter article id |
| "Tailgate" | 1 | Used incidentally inside a `discussion_notes` body of one trucking topic — NOT a UI label |
| "Toolbox Talks & Huddles" | 1 | MeetingsDashboard.jsx:87 (page subtitle) |

The **canonical user-facing term is "Site Safety Meeting"**. Other terms appear inconsistently and signal "different generations of platform evolution stitched together" — exactly the operator's concern.

| # | Location | Current text | Recommended |
|---|---|---|---|
| C1 | `MeetingsDashboard.jsx:87` | `"Toolbox Talks &amp; Huddles"` | `"Site Safety Meetings"` (match the page title above it; "huddle" is a different concept covered by Daily Huddle SOP) |
| C2 | `CheatSheetCard.jsx:52` + `i18n.js:544` | `"Inspections · Toolbox Talks · Incidents · JHPs · Trench Box reference."` | `"Inspections · Safety Meetings · Incidents · JHPs · Trench Box reference."` (single rename, single string) |
| C3 | `OperationalGuidanceCenter.jsx:604` | `label: "Toolbox Talks / Safety Meetings"` | `label: "Site Safety Meetings"` · keep Spanish `"Charlas de Seguridad"` (ES idiom is fine and field-correct) |
| C4 | `meetingSchema.js:1` comment | `"// Field definitions for the MASCI Site Safety Meeting (Toolbox Talk) form."` | Drop the parenthetical; it's archaeology |
| C5 | "topic" vs "topic template" vs "scaffold" | Mixed in code comments | Establish lexicon: **"topic"** for the 136 library entries · **"scaffold"** for the auto-fill mechanism · **"template_key"** strictly for the data field. No user-facing copy says "scaffold" or "template." |

**Action items:** 4 string edits + 1 lexicon note in code comments.

---

## D. Bilingual alignment · UI strings, not topic content

Topic content is 100% parity (verified iter264). The form chrome is NOT.

| # | Location | Issue | Evidence |
|---|---|---|---|
| D1 | `NewMeeting.jsx:60` | Toast `"Job loaded: #${job.project_number}"` | Hardcoded English · would show English to an ES foreman |
| D2 | `NewMeeting.jsx:127, 133, 136` | Three GPS toasts hardcoded English | `"Location captured from GPS"`, `"Got GPS coordinates, but couldn't look up address"`, `"Could not get GPS location"` |
| D3 | `NewMeeting.jsx:169, 174, 178` | Validation error toasts use English-only labels: `` `${l} is required` ``, `"Conductor signature is required"`, `"Add at least one attendee"` | Spanish foreman gets English errors |
| D4 | `NewMeeting.jsx:250, 256, 271` | `"Translating to English…"`, `"Meeting saved"`, `"Could not save meeting"` hardcoded English | These appear DURING and AFTER ES submission — exactly when ES users need ES |
| D5 | `NewMeeting.jsx:617` | Placeholder `e.g. Heat Stress Prevention, Trench Safety, Silica Awareness` | English-only |
| D6 | `NewMeeting.jsx:594` | `t("Pick a topic — Category & all fields below auto-fill")` — string exists in i18n? | **MISSING from i18n.js · NOT translated to ES** |
| D7 | `NewMeeting.jsx:673` | `t("Add every person who attended...")` | **MISSING from i18n.js** |
| D8 | `NewMeeting.jsx:107-110` | Conditional EN vs ES success toast already handled correctly | ✅ Good — proves the rest CAN be done |
| D9 | `ViewMeeting.jsx` overall | **ZERO `t()` calls** · 100% English labels | `View*` cousins differ: `ViewEquipmentInspection.jsx` has 15 `t()` calls; `ViewQaqcInspection.jsx` and `ViewSafetyForm.jsx` use `useT`. Meeting view is alone in being un-translated. |
| D10 | `ViewMeeting.jsx:228-237` | Weather chip values hardcoded EN: `{ clear: "Clear", hot: "Hot", cold: "Cold", rain: "Rain", wind: "Wind", storm_risk: "Storm Risk" }` | A meeting submitted in ES with `weather: ["hot","wind"]` renders as English "Hot · Wind" in the record. |
| D11 | `ViewMeeting.jsx:153` | Page H1 hardcoded `"Site Safety Meeting Record"` | English-only |

**Action items:** 6 toasts + 2 missing i18n strings + 1 placeholder + ViewMeeting full i18n pass (~30 strings) + weather label map.

---

## E. PDF / output consistency · meeting record vs F2-A pack

| # | Aspect | Meeting record print (ViewMeeting.jsx) | F2-A topic pack PDF | Aligned? |
|---|---|---|---|---|
| E1 | Header band | MASCI logo + red bottom border on header bar | MASCI red eyebrow rule | Different styles |
| E2 | Footer | `"Generated {timestamp} · {company} Safety Meeting"` | `"MASCI Safety · Internal Use"` + page X of Y | Different content + different positioning |
| E3 | Section labels | `"Section 01"` in MASCI red uppercase mono | No section labels (one topic per page) | Different paradigm — acceptable; both look operational |
| E4 | Typography | Tailwind sans (`font-display` Inter-ish + mono) | ReportLab Helvetica | OK for print; minor inconsistency in print preview vs PDF |
| E5 | Black-and-white friendliness | Strong red accents may print poorly in B&W (red→gray) | Single red eyebrow only — B&W safe | F2-A is correctly B&W-tuned; meeting print is not |
| E6 | Page X of Y | Not present | Present in F2-A | Meeting prints lack page markers |
| E7 | "Generated" timestamp | Present in ViewMeeting | Not in F2-A | F2-A is intentionally undated (the topic is canonical) — but the meeting print could use a clearer "Printed on" line |
| E8 | Bilingual | Meeting record prints in the submission language only; no EN/ES toggle on print | F2-A offers EN/ES/Both | Acceptable difference, but the meeting print could surface a print-language hint if `submit_language === "es"` |
| E9 | Weather labels in print | Currently English-only (D10) | N/A | This is actually a print/PDF correctness bug, not just an i18n nit |

**Action items:** E2 footer alignment, E5 B&W audit, E6 page numbers on meeting PDFs, E9 weather i18n (overlaps D10).

---

## F. Role expectation gaps

The form does not ask **who is running this meeting in what role**, which is information the foreman implicitly carries but the system does not record.

| # | Finding | Evidence |
|---|---|---|
| F1 | `conducted_by` is a free-text string (`NewMeeting.jsx:422-428`). No role hint, no employee picker, no role normalization. | The form has `EmployeeCombo` for attendees but NOT for `conducted_by`. Foreman types their name. |
| F2 | No capture of conductor's role | Foreman vs Superintendent vs Safety Lead vs PM running a meeting all flatten to the same `conducted_by` string. Operational data lost. |
| F3 | Phase B/C trucking topics carry `role_context: ["driver","spotter","lead"]` in the topic schema | The data exists in the library but the form ignores it. Could surface "This topic is most relevant to: Drivers, Lead Drivers, Spotters" when a trucking topic is loaded. |
| F4 | No coaching that lone-worker / line-of-fire topics work for solo foremen | Phase H Batch 5 added `general_lone_worker_field` and `general_line_of_fire`. The form doesn't acknowledge these as appropriate even for single-person scenarios — which is a real use case for surveyors, lone shop workers, etc. |

**Action items:** F1 wire `EmployeeCombo` into `conducted_by` (single small change); F2 add a `conducted_by_role` select (optional); F3 surface `role_context` as a small chip when present.

---

## G. Linkage to safety-library philosophy

Does the form coach the user toward the system's defining strength (operational-judgment transfer through incident-pattern realism)? Current answer: **no, not explicitly.**

| # | Finding |
|---|---|
| G1 | The form treats topic selection as a convenience (auto-fill) rather than a teaching moment. No copy explains that the `incident_pattern` paragraph at the top of `discussion_notes` is the lesson — the bullets are the action. |
| G2 | After applyTemplate runs, there's no visual differentiation in the form between "the paragraph (CONTEXT)" and "the bullets (ACTION)". Both sit in one textarea. A foreman editing it doesn't see the philosophy. |
| G3 | The form does not surface the source domain or severity (correct per the JS-only-severity rule) — but it also doesn't surface the **domain label** itself in any prominent way. The picker shows it, but post-pick it's invisible. |
| G4 | No reminder that bilingual parity exists. A Spanish-speaking foreman doesn't know they can toggle to ES and get the same topic in field-Spanish — they would have to discover the LangToggle in the header. |
| G5 | The `composeIncidentScaffold.js` header strings (`WHAT HAPPENS · real-world pattern` / `PATRÓN REAL · lo que suele pasar`) are embedded in the prepended text — they're the only philosophy artifact the user sees. Not surfaced as a deliberate design element. |

**Action items:** G2 visual separation (CONTEXT vs ACTION) using a styled prefix block above the textarea; G3 small domain breadcrumb under the topic picker after a topic is loaded; G4 LangToggle proximity hint at first load.

---

## H. Onboarding gaps · first-time foreman

| # | Finding |
|---|---|
| H1 | No first-load orientation on `/meetings/new`. New foreman just sees a form. | No "First time? Here's how this works →" affordance |
| H2 | The 5 Phase H+iter260 capture fields (crew_size, shift, weather, sub, high-risk) have NO header explaining they're new or what they're for | A foreman who used the form 6 months ago might miss them or click through |
| H3 | The 2-photo minimum is enforced by toast + counter, but no upfront sentence at the photos section saying "Two photos prove the meeting actually happened — group shot + topic board are ideal." | The counter shows the requirement; the rationale is missing. The rationale is the operational coaching. |
| H4 | No mention of GPS / Use GPS button on first load — foremen who don't see it think they have to type the address | Could be a tiny chip beside the GPS button: `t("Tap GPS for one-touch site address")` |
| H5 | Spanish-only foreman has no Spanish-first onboarding article in `/guidance` linked from the form | A field-Spanish user who is given the URL `/meetings/new` on a phone has no Spanish entry point |

**Action items:** H1 first-load coachmark (one-time, dismissible); H3 one-line photo rationale; H4 GPS hint chip; H5 Spanish article verification (overlaps B2).

---

## I. ViewMeeting alignment

| # | Finding | Severity |
|---|---|---|
| I1 | ViewMeeting.jsx renders modern fields correctly (crew_size, shift, weather, sub, high_risk) when present — but ONLY when present. Pre-iter260 records show no indication these were missing — silently absent. | ⚪ Acceptable — historic records are immutable |
| I2 | High-risk activity badge is correctly prominent (red box) ✅ | ✅ Good |
| I3 | GPS map thumbnail loads correctly ✅ | ✅ Good |
| I4 | Submit-language badge appears only when `submit_language === "es"` — silent for EN records | ⚪ Minor; acceptable |
| I5 | **The hard one:** weather chips render English even on ES-submitted records (see D10). | 🟡 Real bug |
| I6 | The Discussion Notes block renders the `incident_pattern` paragraph as plain text mixed into the bullets — no visual separation, no styled eyebrow. The PDF inherits the same shape. | 🟡 Aligns with G2 — same fix applies in both render paths |
| I7 | `topic_template_key` is captured in the model but never surfaced in ViewMeeting. A Safety Manager reviewing a meeting can't see which library topic was used (vs custom). | 🟡 Small surface gap |
| I8 | `conducted_by` is captured but the conductor's role is not displayed (because it isn't captured — F2). | ⚪ Depends on F2 |
| I9 | ViewMeeting has zero `t()` usage (D9). Spanish reviewer sees English layout. | 🔴 Largest single alignment gap in the audit |
| I10 | Doc ID badge ("MTG-2026-00123") is correctly prominent ✅ | ✅ Good |
| I11 | The "No Guesswork. No Missed Steps. No Excuses." brand line is rendered `hidden` (line 172) | ⚪ Intentional — not a finding |

**Action items:** I5 weather i18n (overlaps D10); I6 styled eyebrow + paragraph separation (overlaps G2); I7 show "Topic Template: {key}" small caption; I9 full ViewMeeting i18n pass.

---

## J. Cross-platform consistency

Compared to peer forms in the platform (sample: Field Leadership Hub, Safety Incidents, Equipment Inspections, QA/QC Inspections, Safety Forms):

| Surface | Has useT/`t()`? | Sectioned layout? | Modern operational metadata? |
|---|---|---|---|
| `NewMeeting.jsx` | ✅ uses `t()` | ✅ Section 01-05 | ✅ has E1 fields (iter260) |
| `ViewMeeting.jsx` | ❌ **zero** | ✅ Section labels | ✅ renders E1 |
| `ViewEquipmentInspection.jsx` | ✅ 15+ calls | ✅ | ✅ |
| `ViewQaqcInspection.jsx` | ✅ uses `useT` | ✅ | ✅ |
| `ViewSafetyForm.jsx` | ✅ uses `useT` | ✅ | ✅ |
| `ViewIncident.jsx` | ❌ zero | ✅ | ✅ |
| `ViewInspection.jsx` | ❌ zero | ✅ | ✅ |

**Observation:** `ViewMeeting`, `ViewIncident`, and `ViewInspection` are the three legacy "view" pages NOT translated. They form one cluster. Fixing them together as a single alignment iteration would be efficient — but per scope discipline, this audit only addresses ViewMeeting. (Recommend a follow-on audit for the other two when operator green-lights.)

**Action items:** none specific to this audit beyond ViewMeeting; flag the cluster for a follow-on iteration.

---

## K. Inventory of completion gaps · prioritized

### 🔴 P0 — operational trust impact / data-correctness

- **K1** ViewMeeting full i18n pass (~30 hardcoded strings) — fixes D9, I9
- **K2** Weather label i18n in ViewMeeting — fixes D10, E9, I5 (correctness bug for ES records)
- **K3** Toast i18n in NewMeeting (~9 hardcoded toast calls) — fixes D1–D4 (ES users get EN errors today)

### 🟡 P1 — coaching / philosophy alignment

- **K4** Visual separation of `incident_pattern` vs bullets in form + ViewMeeting — fixes A5, G2, I6
- **K5** Update `/guidance/public-toolbox-talks` article body to reflect Phase H + incident-pattern philosophy — fixes B1
- **K6** Add helper coaching strip above the topic picker explaining "read the pattern aloud, then the bullets" — fixes A1, A2
- **K7** Domain breadcrumb caption after topic load — fixes G3
- **K8** Add `EmployeeCombo` to `conducted_by` for normalized capture — fixes F1
- **K9** ES translation of remaining 2 missing strings (`Pick a topic — Category & all fields below auto-fill`, `Add every person who attended...`) — fixes D6, D7

### 🟢 P2 — refinement / surface polish

- **K10** Add "First time?" coachmark on `/meetings/new` first load — fixes H1
- **K11** Photo rationale one-liner — fixes H3
- **K12** GPS button hint chip — fixes H4
- **K13** Terminology rename pass (4 strings) — fixes C1–C4
- **K14** Code-comment lexicon note — fixes C5
- **K15** Show "Topic: {library key}" small caption in ViewMeeting — fixes I7
- **K16** Page X of Y on meeting PDFs — fixes E6
- **K17** B&W print audit pass (ensure red accents degrade legibly) — fixes E5
- **K18** Optional `conducted_by_role` field — F2
- **K19** Surface `role_context` chip when present — F3
- **K20** Foreman-focused guidance article ("How to run a Safety Meeting using the topic library") — fixes B3
- **K21** Link from NewMeeting header to the guidance article — fixes B4

### ⚪ Out of scope for this iteration (flagged for separate audit)

- ViewIncident.jsx · ViewInspection.jsx · same i18n gap — separate alignment pass when operator chooses

---

## L. Recommended sequencing · small, high-value, operationally meaningful

Each item below is sized to ship in one iteration, pass through the Operational Value Gate, and improve trust without enlarging scope.

### Sprint 1 · Correctness & trust (≈ one focused iteration)
- **K1** ViewMeeting i18n pass
- **K2** Weather label i18n
- **K3** NewMeeting toasts i18n
- **K9** Two missing i18n strings
- Test with safety-reviewing-an-ES-meeting scenario

**Why first:** these are data-correctness and trust gaps that field-Spanish users see every shift today. Operational Value Gate: ✅ (real daily pain).

### Sprint 2 · Philosophy linkage (≈ one focused iteration)
- **K4** Visual separation of incident_pattern vs bullets (form + view)
- **K6** Coaching strip above topic picker
- **K7** Domain breadcrumb after topic load
- **K5** Guidance article rewrite

**Why second:** these connect the form to Phase H's philosophy. Operational Value Gate: ✅ (transfers operational intent to first-time foremen).

### Sprint 3 · Role & terminology (≈ one focused iteration)
- **K8** EmployeeCombo for conducted_by
- **K13** Terminology rename (4 strings)
- **K14** Lexicon code-comment note
- **K15** Topic template caption in ViewMeeting

**Why third:** smaller polish items that align the workflow with peer forms in the platform. Operational Value Gate: ✅ (consistency reduces confusion).

### Sprint 4 · Onboarding & PDF polish (optional, defer until usage shows demand)
- **K10** First-time coachmark
- **K11** Photo rationale line
- **K12** GPS hint chip
- **K16** Page X of Y on PDFs
- **K17** B&W audit
- **K20, K21** Foreman article + link

**Why fourth:** these are polish layers. Real usage may make some unnecessary; ship Sprints 1-3 first and reassess.

### Deferred
- **K18, K19** Role capture · F1 wait for operator green-light · adds a field, which raises the Operational Value Gate bar slightly

---

## M. Mobile-specific operational alignment (414px field usability)

Per operator addendum. Focused on field reality — 414px screens, one hand, gloves, sunlight, quick entry, fatigue.

### M.1 — Tap target spacing
| # | Location | Issue |
|---|---|---|
| M1.1 | `NewMeeting.jsx:441-447` · TOPIC_CATEGORIES SelectItem options | Default Shadcn select item height (~32px) is below Apple HIG 44px guideline. Multiple narrowly-stacked options on a small phone risks mis-taps in a moving truck. |
| M1.2 | Weather chips (`weather-chip-*`) | `py-1.5` makes them ~32px tall · same below-44px concern. Worth bumping to `py-2.5` and `text-base` for one-handed use. |
| M1.3 | Domain chips inside TopicPicker | 22 chips in a wrapping row at 414px — visually dense. Foreman in a glove can hit the wrong chip. |
| M1.4 | `data-testid="toggle-high-risk"` checkbox | 20px square checkbox · gloves can't reliably tap a 20px target. The wrapping `<label>` does extend the tap zone, which mitigates this — verify the entire row is the tap target (it is, per `<label className="...h-14...">`). ✅ already OK. |

### M.2 — One-hand interaction
| # | Finding |
|---|---|
| M2.1 | Section 01 has 12 input fields before Section 02. Foreman must thumb-scroll past all of them to reach the topic picker. A foreman who knows the topic could benefit from a "Skip to topic →" quick link. |
| M2.2 | The bottom Submit button is correctly fixed at the page bottom · ✅ |
| M2.3 | The top Submit button in the sticky header is small (h-11) and uses the same red as the back button background — high-contrast but small target. A foreman wanting to submit can use the bottom button (h-16) which is correctly sized. ✅ |
| M2.4 | Date and time inputs use native pickers (`type="date"` / `type="time"`) which work well on mobile · ✅ |

### M.3 — Spanish/mobile readability
| # | Finding |
|---|---|
| M3.1 | Spanish topic titles tend to be 10-25% longer than English. Topic picker buttons need to handle wrapping cleanly — verify no truncation at 414px ES. |
| M3.2 | ES `t()` keys appear correctly across the form — but the missing i18n strings (D6, D7) will display English on ES mobile, which is visually jarring. |
| M3.3 | The `font-mono` uppercase labels (`text-xs uppercase tracking-[0.2em]`) compress ES text harder than EN. Some ES labels (e.g. `"Subcontractor crew present" → "Cuadrilla de subcontratista presente"`) may render cramped at 414px. |

### M.4 — Long-topic scrolling fatigue
| # | Finding |
|---|---|
| M4.1 | After applyTemplate, `discussion_notes` textarea grows to fit content. A 5-sentence `incident_pattern` + 6-8 bullets makes it ~14 lines at mobile width. The foreman scrolls past it heading to Photos. Possible mitigation: collapsible "Show full notes ↕" toggle once content exceeds N lines. |
| M4.2 | Section 03 (Attendees) grows linearly per attendee. A 12-person crew = 12 expanded blocks with signature pads, photos optional. Could become 6+ feet of scroll. No mitigation needed for MVP but flag for monitoring. |
| M4.3 | Sticky header reduces vertical real estate by ~60px. On a 414×800 phone with browser chrome, the visible content area is ~520px. Each Section's heading + first field uses ~90px. Foreman sees ~5 fields of content before scrolling. Acceptable. |

### M.5 — Chip/filter usability
| # | Finding |
|---|---|
| M5.1 | Weather chips (6) wrap at 414px to 2-3 rows · ✅ readable |
| M5.2 | TopicPicker domain chips (22) wrap to 5-6 rows at 414px · ✅ usable but dense. Could be improved by a horizontal scroll instead of wrap (operator approval needed). |
| M5.3 | After picking a topic, the picker chip row remains visible · OK but takes vertical space the foreman no longer needs. Could collapse on selection. |

### M.6 — Real field conditions (sunlight, gloves, quick entry)
| # | Finding |
|---|---|
| M6.1 | The page uses `bg-slate-50` background with `bg-white` card panels. High contrast, sunlight-readable · ✅ |
| M6.2 | Red `bg-red-700` Submit button against dark slate sticky header is high-contrast · ✅ |
| M6.3 | Input borders are `border-2 border-slate-300` (thick) · ✅ glove-friendly |
| M6.4 | The MASCI red eyebrow caution stripe at top (`<div className="caution-stripe" />`) is visually loud — confirms the page identity quickly · ✅ |
| M6.5 | Quick-entry pattern: a foreman who is texting the same data 5 times a week wants 1-tap defaults. Current form auto-fills nothing from prior submissions. A "Continue from last meeting" prefill (project, location, conducted_by, crew_size, shift) could save 30 seconds per submission. **Out of scope for alignment — this would be a feature.** Logged as a future consideration only. |

### M.7 — Mobile action hierarchy
| # | Finding |
|---|---|
| M7.1 | Two Submit buttons (top sticky + bottom fixed). Both submit. Top is small; bottom is large. ✅ Hierarchy correct. |
| M7.2 | "Use GPS" button is small (h-9) next to Location field. Visually subordinate · correct hierarchy — Location is the primary, GPS is the accelerator. ✅ |
| M7.3 | Add Attendee button is full-width dashed border — high-affordance · ✅ |
| M7.4 | "How this form works →" link to guidance article (B4) is missing — would be a small ghost-link in the header, low hierarchy. Worth adding. |

### M.8 — "Can this realistically be used standing on a jobsite?"
**Yes.** The form is field-usable today. Specific frictions identified above:
- ES users see English toasts/errors (D1-D4) — **must fix**
- Tap targets at the lower end of acceptable for gloves — **could improve**
- No coaching for first-timers — **could improve**
- 1-tap re-submit unavailable — **future consideration, not alignment work**

### Mobile-specific action items (prioritized)
- 🔴 M-P0 · Fix ES toast i18n (overlaps K3) — sunlight + Spanish + jobsite = unreadable error today
- 🟡 M-P1 · Bump weather chip + select item padding to `py-2.5 text-base` for glove-friendliness (M1.1, M1.2)
- 🟡 M-P1 · Tighten label tracking on Spanish strings (`tracking-[0.1em]` instead of `[0.2em]` when `lang === "es"`) — M3.3
- 🟢 M-P2 · Collapse domain chip row after a topic is selected (M5.3)
- 🟢 M-P2 · Add "How this form works →" link in header (M7.4)
- ⚪ Future · "Continue from last meeting" pre-fill (M6.5) · feature, not alignment

---

## Closing

The Safety Meeting workflow is **not broken** — it's a working production tool used today. But it predates Phase H, predates the modular topic library, predates the incident-pattern philosophy, predates the operational-metadata layer, and predates the bilingual-parity discipline that the rest of the platform now enforces.

This audit produces **52 concrete, actionable findings** (K1-K21 + M1-M8 sub-items) sized for small refinement iterations. None require a rewrite. Each one closes a specific consistency or coaching gap.

**Recommended immediate work:** Sprint 1 (K1+K2+K3+K9 + M-P0) — correctness for Spanish-speaking foremen TODAY. Roughly one focused iteration. After it ships, decide on Sprint 2 based on real signal.

The objective is not perfection. The objective is **one operationally consistent ecosystem** where the Safety Meeting workflow feels like it lives in the same world as the topic library and the F2-A pack generator — because operationally, it should.

---

**End of audit · iter267 · /app/memory/SAFETY_MEETING_ALIGNMENT_AUDIT_iter267.md**
