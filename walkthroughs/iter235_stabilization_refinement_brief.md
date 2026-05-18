# Stabilization Refinement Brief · iter235
**Two operational-continuity findings · analysis + recommendations · no implementation**

> **Status:** analysis document · awaiting operator approval before any change.
> **Posture:** stabilization-phase. Tightly scoped. No expansion.

---

## Topic 1 · Site Inspection / Safety portal alignment

### 1.1 · What the audit actually found

**Current routing:**
| Route | Gate | Component |
|---|---|---|
| `/inspect/new` | `<GateInspection>` form-password "1982" | `<NewInspection />` |
| `/submit` | `<GateInspection>` form-password "1982" | `<NewInspection publicMode />` |
| `/inspections/submit` | `<GateInspection>` form-password "1982" | `<NewInspection publicMode />` |
| `/inspections/new` | redirect → `/inspect/new` | — |
| `/admin/inspections` | `RequireAdminOrPm` | `<Dashboard />` |
| `/admin/inspections/:id` | `RequireAdminOrPm` | `<ViewInspection />` |
| `/pm/inspections` | `RequireAdminOrPm` | `<Dashboard />` |
| `/pm/inspections/:id` | `RequireAdminOrPm` | `<ViewInspection />` |

**Critical observation:** there is **no `/safety/inspections` route**. The Safety portal accesses the same records via `SafetyAudits.jsx` (`/safety/audits`) which queries `/api/inspections` directly. Records flow through one collection; the portal-side views are reads on that collection.

**Form-password gate behavior:**
- Hardcoded constant `SITE_INSPECTION_CODE = "1982"` in `App.js:167`
- localStorage key: `masci.gate.site-inspection`
- Applied uniformly to all three submission paths (`/inspect/new`, `/submit`, `/inspections/submit`)
- **Pre-dates the dedicated Safety portal** — legacy artifact from when there was no portal RBAC to gate against

**RBAC behavior summary:**
| Persona | Submit? | View list? | View detail? |
|---|---|---|---|
| Anonymous field user (knows the "1982" code) | ✅ via `/submit` | ❌ | ❌ |
| Safety portal user | ✅ if they enter "1982" once | ✅ via `/safety/audits` | ✅ via `/inspections/:id` |
| PM portal user | ✅ if they enter "1982" once | ✅ via `/pm/inspections` | ✅ |
| Admin | ✅ if they enter "1982" once | ✅ via `/admin/inspections` | ✅ |

**Submission flow (verified):**
- All three routes POST to `/api/inspections`
- All inspections land in the same Mongo `inspections` collection
- Safety portal (`SafetyAudits.jsx`), PM portal, and Admin all read from the same collection
- PDFs render via the same `pdf_render.py` pipeline · `submit_language` honored end-to-end
- Exports flow through the same export pipeline

**Visibility after submission:**
- Safety, PM, Admin can all view immediately
- HR cannot view (intentional — site inspections are operations/safety records, not HR records)
- Field user who submitted has no read-back UI (intentional — they don't have portal access)

**Retention / export:**
- Same as all other inspection records · no separate retention policy · same R2 export coverage

### 1.2 · The actual legacy assumption

The form-password gate **assumes a world where there is no Safety portal** — where the only way to "trust" a submitter is to give field crews a shared code. That world no longer exists. The Safety portal is now mature and RBAC-gated.

But the gate **still has one legitimate use**: anonymous field submission via QR code or shared link without portal login. The "1982" code is essentially a "you have the right link" signal that prevents random internet visitors from spamming `/api/inspections`.

### 1.3 · What's actually wrong

| Issue | Severity | Notes |
|---|---|---|
| Safety portal users still hit "1982" gate to submit a form | **medium** | Operational friction. They are already authenticated; the form-password is redundant for them. |
| Same hardcoded constant on all three paths | **low** | Not a security issue (it's a UX gate, not an auth boundary), but conflates two different use cases. |
| `/inspect/new` discoverability from inside Safety portal is unclear | **medium** | Safety users may not know the canonical entry point — they hit the public submission path. |
| Code "1982" lives in client-side JS | **low** | Anyone reading the JS finds it. Acceptable for a UX gate, not for any real security. |
| No dedicated `/safety/inspections/new` route | **low** | Forces Safety portal users to route through generic `/inspect/new`, breaking portal-flow consistency. |

### 1.4 · Recommendations · holistic

**The right fix is NOT to remove form-level gating entirely.** The public submission path (`/submit`, `/inspections/submit`) genuinely needs a low-friction "you have the right link" signal — that's how QR-code field submission works. Removing it would expose `/api/inspections` to anonymous POST without any soft gate.

**The right fix IS to skip the gate for already-authenticated portal users.** A Safety/PM/Admin user shouldn't have to type "1982" to submit a record they're authorized to submit. The gate should detect: *"is this user already authenticated to a portal that can submit inspections? If yes, skip the password."*

### 1.5 · Three concrete recommendations (analysis only)

**Recommendation A · Skip the gate for portal-authenticated users · LOW risk**
- Modify `<GateInspection>` to check for valid Safety / PM / Admin tokens before requiring the password
- If authenticated to one of those roles, bypass the form-password entirely
- Public submission path (anonymous field user with the shared link) still requires "1982"
- **Net effect:** Safety/PM/Admin users get a clean portal-flow experience; anonymous field submission continues unchanged
- **Implementation scope:** ~30 minutes · `App.js:168-176` + small auth check helper · NOT auth-sensitive (already-gated routes stay gated)
- **Risk classification:** LOW · no auth surface change · no RBAC widening · purely friction reduction

**Recommendation B · Add `/safety/inspections/new` portal-flow route · LOW risk**
- New route alongside `/safety/audits` etc.
- Routes through `<RequireSafety>` instead of `<GateInspection>`
- Provides discoverable portal-native entry point for Safety users
- Existing `/inspect/new` continues to work (backward compat)
- **Implementation scope:** ~15 minutes · one route line + one nav-link addition · NOT auth-sensitive
- **Risk classification:** LOW · pure additive

**Recommendation C · Move `SITE_INSPECTION_CODE` to env var · LOW risk · OPERATIONAL HYGIENE**
- The "1982" code being hardcoded in `App.js` is a minor hygiene issue
- Move to `process.env.REACT_APP_SITE_INSPECTION_CODE` with documented fallback (the iter232 pattern)
- Allows operator to rotate the code without a code deploy
- **Implementation scope:** ~10 minutes · single constant + `.env` addition
- **Risk classification:** LOW · pre-existing fallback pattern proven safe

### 1.6 · NOT recommending

- ❌ **Removing the form-password gate entirely** — would expose anonymous-submission paths to internet POST traffic
- ❌ **Migrating `/api/inspections` to require auth tokens** — would break the operationally-important QR/shared-link field-submission flow
- ❌ **Refactoring `NewInspection.jsx` to be Safety-portal-only** — would require duplicating the form for the public submission path · large refactor with no operational benefit
- ❌ **Adding additional notifications/escalations** — current notifications are operating correctly per Safety portal observation; no observed friction

### 1.7 · Recommended scope of any implementation pass

**Apply A + B together** (45 minutes total) as a single coordinated friction-reduction iter:
- A removes redundant gating for portal-authenticated users
- B adds the discoverable portal-native entry point
- Together they make Safety portal users' inspection-creation flow feel native to the portal
- C is **optional polish** · operator can decide separately

**Total estimated implementation scope: 1 hour. Risk: LOW. Auth-sensitivity: NONE. Gate classification: MEDIUM (multiple portal surfaces touched).**

---

## Topic 2 · Localization continuity audit

### 2.1 · Quick verdict

| Concern | Verdict |
|---|---|
| Operational record continuity for Spanish field crews | ✅ **HEALTHY** · auto-translation pipeline real and wired across 11 form-submission surfaces |
| Reviewer-side English continuity | ✅ **HEALTHY** · records persist in English; PDF renderer can re-render in original Spanish |
| Bilingual records get fragmented into language silos | ✅ **NO RISK** · single English canonical record + `submit_language` stamp |
| UI translation completeness | ⚠️ **PARTIAL GAPS** · the "New Here" banner gap is real; spot-check of 4 hub files shows otherwise-clean coverage |
| Localization architecture | ✅ **MATURE** · operator-stated "English canonical · ES is a fill aid" is documented in `i18n.js:2` |

### 2.2 · The auto-translation pipeline · verified live

**Architecture (documented in `i18n.js:2`):**
> *"English is the canonical language — all submitted data is stored in English. Spanish is a read/fill aid for Spanish-speaking crew members on forms."*

**How it works:**
1. Spanish-speaking field user switches UI to ES
2. Form labels, placeholders, help text render in Spanish (via `useT()` lookup)
3. User types free-text answers in Spanish
4. At submit, `translateUserInput` (from `lib/translateOnSubmit.js`) calls `POST /api/translate`
5. Backend `/api/translate` uses Claude Haiku 4.5 via `EMERGENT_LLM_KEY` to translate string leaves ES→EN
6. **Preserves construction-specific terms** (excavator, MOT, PPE, rebar, lift station, foreman) per the system prompt at `server.py:8222-8230`
7. Translated record + `submit_language: "es"` flag persists to Mongo
8. **Translation failure is non-blocking** — if Claude is down, original Spanish text persists rather than blocking the submit (`server.py:8200`)

**Wired into 11 form surfaces (verified by grep):**
- `NewIncident.jsx`
- `NewMeeting.jsx`
- `NewDailyReport.jsx`
- `NewInspection.jsx`
- `NewSafetyEquipmentTraining.jsx`
- `NewSafetyEquipmentIssuance.jsx`
- `NewEquipmentInspection.jsx`
- `NewQaqcInspection.jsx`
- `PublicTimeOff.jsx`
- `FieldLeadershipFormPage.jsx`
- `ReturnEquipment.jsx`
- + 2 component-level surfaces (`ShopSignoffCard`, `PartsCatalog`)

**Reviewer-side behavior:**
- Reviewers (HR, PM, Safety, Admin) see the **English canonical record**
- `SubmitLangBadge` displays "Originally entered in Spanish" on admin views when `submit_language === "es"`
- PDFs render in `submit_language` — Spanish original or English canonical based on context
- `pdf_render.py:1126` explicitly handles QA/QC bilingual end-to-end rendering

**Bilingual adoption telemetry exists:**
- `GET /api/admin/submit-language-stats` returns per-collection ES vs EN counts
- Surfaces in admin UI via `<BilingualAdoptionCard>`
- Admin can see at a glance how much Spanish-mode usage is happening

**Conclusion on Topic 2.2 · operational record continuity:** **THE ARCHITECTURE IS WORKING.** Spanish field crews submit in Spanish; records persist in English; reviewers see clean English; PDFs can render in original Spanish; admin sees adoption telemetry. No fragmentation.

### 2.3 · The "New Here" banner gap · confirmed real

**Where it lives:** `Hub.jsx:280-299` · a styled `<Link>` to `/guidance/role-new-employee` shown to non-authenticated visitors.

**Three strings all wrapped in `t()` correctly:**
- `t("New here?")` (line 289)
- `t("First week on the platform — start here")` (line 292)
- `t("A 5-minute walkthrough for new hires: what to fill out, where, and why.")` (line 295)

**Why it doesn't translate:** the three keys **are not present in the ES dictionary** at `/app/frontend/src/lib/i18n.js`. Per the dictionary's documented behavior (line 58-60): *"Missing key → fall back to the English key itself."* So the banner renders in English even when ES mode is active.

**This is the kind of low-cost gap that's worth fixing.** Three dictionary entries.

### 2.4 · Spot-check of other surfaces · clean

Ran a targeted scan across the four hub files (`Hub.jsx`, `HrHub.jsx`, `PmHub.jsx`, `SafetyHub.jsx`) for JSX text content >2 words not wrapped in `t()`. **No hardcoded English strings detected outside the documented language-branching at `Hub.jsx:254` (intentional · operator-stated pattern where the trailing word doesn't appear in Spanish).**

This is consistent with the dictionary's 1,800+ entries and the long iter history of bilingual discipline. The architecture itself is sound; gaps are individual-string-level, not structural.

### 2.5 · Other potential gaps (likely · not exhaustively scanned per stabilization-scope discipline)

Without running a full sweep (which would conflict with the stabilization posture), the following are **plausible gap locations** that should be checked if the operator wants a deeper sweep:

- **Day-1 banner** (`Hub.jsx:282` line — already covered above)
- **Marketing-style copy** in `Hub.jsx:251-267` — verified `t()` wrapped, but ES dictionary coverage not verified for every string
- **Error toast messages** in form-submit flows — these are often the most-missed
- **Newly-added portal titles** since iter219 — high churn area
- **HelpTip empty-state messages** when no tips return for a form_key — likely English-hardcoded
- **PDF cover sheets** for newer record types added post-iter65

**Recommendation:** these are P3-tier follow-ups. Not blocking. Worth a single mini-iter at most when operator surfaces specific user friction.

### 2.6 · Recommendations · localization

**Recommendation D · Fix the "New Here" banner ES dictionary entries · TRIVIAL**
- Add 3 entries to `i18n.js` ES dictionary
- Estimated implementation: **5 minutes**
- Risk: **NONE** — single dictionary file · no logic change · only Spanish-mode users see any change
- Gate classification: LOW (docs/strings only)

**Recommendation E · Add a regression check for ES dictionary completeness · OPTIONAL**
- A pytest test that scans `Hub.jsx` (and optionally a list of hub files) for `t(...)` calls and asserts each key has an ES entry
- Prevents future "New Here"-style gaps when new banners ship
- Estimated implementation: ~30 minutes · single new test file
- Risk: **LOW** · test-only · no behavior change
- Gate classification: LOW (test-only)

**Recommendation F · Document the localization architecture in PRD · ZERO IMPL**
- One PRD section codifying:
  - English is canonical
  - Spanish is read/fill aid
  - Auto-translate at submit time via `/api/translate` (Claude Haiku 4.5)
  - `submit_language` stamps every record
  - `SubmitLangBadge` makes ES-original records visible to reviewers
  - PDFs render in `submit_language`
- Estimated implementation: ~10 minutes · doc only
- Risk: NONE

### 2.7 · NOT recommending

- ❌ **Full bilingual UI sweep across 200+ JSX files** — would be a massive operation, conflicts with stabilization posture
- ❌ **Multilingual architecture expansion** (e.g. adding Portuguese, French) — explicit operator hard-stop
- ❌ **AI translation enhancement experiments** — explicit operator hard-stop
- ❌ **Reviewer-side Spanish UI** — current design (reviewers see English) is correct; reviewers reading records in their entered Spanish would create the fragmentation the operator wants to avoid
- ❌ **Per-record translation memory / glossary** — operationally over-engineered for a 100-person-ish operation
- ❌ **Translating PDF chrome (page headers, footers) into Spanish on every record** — the current `submit_language` branch in `pdf_render.py` already handles this for the document-language case

---

## Combined implementation scope (if all recommended items approved)

| Rec | What | Files | Time | Risk | Gate |
|---|---|---|---|---|---|
| A | Skip form gate for portal-authenticated users | `App.js` | 30 min | LOW | MEDIUM |
| B | Add `/safety/inspections/new` portal-flow route | `App.js`, `SafetyHub.jsx` | 15 min | LOW | MEDIUM |
| C | Move SITE_INSPECTION_CODE to env (optional) | `App.js`, `.env` docs | 10 min | LOW | LOW |
| D | Fix "New Here" ES dictionary | `i18n.js` | 5 min | NONE | LOW |
| E | Add ES dictionary regression test (optional) | `tests/` | 30 min | LOW | LOW |
| F | Document localization architecture in PRD | `PRD.md` | 10 min | NONE | LOW |

**Total all-recommended scope: ~90 minutes. Largest single risk: NONE-to-LOW. Zero auth-sensitive changes. Zero RBAC changes. Zero schema changes. Zero new dependencies.**

**Minimum-viable scope (A + B + D) takes ~50 minutes and closes both operational concerns without touching env, tests, or docs.**

---

## Recommended approval shape

The operator-friendly approval grouping:

**Group 1 · Safety portal alignment** (Topic 1)
- Approve A + B (45 min · MEDIUM gate · LOW risk · pure operational friction reduction)
- C optional · approve separately if operator wants the hygiene cleanup

**Group 2 · Localization continuity** (Topic 2)
- Approve D (5 min · LOW gate · zero risk · fixes the operator-surfaced bug)
- E optional · approve if operator wants regression protection against future banner-gap drift
- F costless · author whenever (PRD entry only)

**Recommended minimum:** **A + B + D** · single ~50-minute iter · one MEDIUM-classified gate run · closes both operator-surfaced concerns.

---

*Analysis complete · iter235 · no implementation performed · operator approval required before any code change. Preview-only when implemented. Stabilization posture preserved throughout.*
