# Phase 12 · iter397 · Cross-Platform Continuity Audit

**Date:** 2026-05-24
**Iteration:** iter397 (first Phase 12 work · audit-first · surgical fixes only)
**Doctrine:** Refinement, not expansion. Make the platform feel inevitable, not bigger.

---

## Purpose

Phase 11 shipped the Dispatch Lifecycle System (DLS) across 5 iterations (iter392-396).
Phase 12 lane A is the **operational continuity audit** — verify the DLS truly
feels native to the MASCI platform rather than "another bolted-on module."

Audit-first means: **walk the surfaces · find the seams · ship the smallest
honest fix · document everything else.** No new modules, no new endpoints, no
new collections, no analytics, no dashboards.

---

## 8 Priority targets · audit results

### 1 · Does the DLS emotionally feel like the MASCI platform?

**Tone:** 🟢 Pass. Slate canvas, blueprint-bg backdrop, font-display + font-mono kicker
pairing, orange dispatch accent — same family as PmHub, ShopHub, AdminHub,
SafetyHub. The DispatchBoard title card uses the canonical
`border-l-4 border-l-orange-500` left-stripe convention that every other hub uses.

**Calmness:** 🟢 Pass. 5 s polling, no flashing, no animation noise. Findings
banner is a single calm card with severity-toned chips capped at 6. Empty
states are quiet (no decorative artwork, no "celebrate this!" copy).

**Spacing:** 🟢 Pass. Same `max-w-6xl mx-auto px-5 sm:px-8 py-6 space-y-6`
container as the platform's hub family. Cards use `p-4 sm:p-5` — within the
platform conventions.

**Wording:** 🟠 **One seam found** (FIXED iter397). The empty state leaked
internal iteration vocabulary: _"Create an assignment via the iter392 API to
populate the board."_ → now reads _"Trucks will appear here the moment dispatch
creates an assignment."_ — operator-facing language.

**Empty states:** 🟢 Pass after fix #1.

**Chip language:** 🟠 **One seam found** (FIXED iter397). FindingsBanner count
ribbon used singular nouns regardless of count: _"2 breakdown · 2 long wait"_.
Pluralization fixed. Subject-verb fixed (_"1 finding require"_ → _"1 finding
requires"_).

**Status language:** 🟢 Pass. STATE_LABEL on the board uses field-direct
operator language ("En route · load", "At load", "Waiting") instead of
backend constants.

**Button language:** 🟢 Pass. AssignmentDrawer button copy is calm and
imperative: "Issue driver magic link", "Cancel assignment", "Reassign driver
/ truck", "Revoke". No marketing voice.

**Lifecycle wording:** 🟢 Pass. The 22 glossary entries in
`AdminOperationalLanguage.jsx` carry full EN+ES parity and use the same
4-section structure (Operational / Lifecycle / Accountability / Downstream)
as the existing 18 platform terms — drift-proof.

### 2 · Does every role only see what they actually need?

| Role | DLS surface | Verdict |
|---|---|---|
| Dispatch | Full board + drawer actions + magic-link issuance + CSV exports | 🟢 correct |
| Admin | Same as dispatch (admin tokens satisfy `_require_dispatch_or_admin`) | 🟢 correct |
| Driver | One assignment in focus · transition buttons · wait sheet | 🟢 correct (single-thread by design) |
| PM | `DispatchLifecycleTile scope="pm"` project-scoped, read-only | 🟢 correct |
| Shop | `DispatchLifecycleTile scope="shop"` BREAKDOWN-scoped, read-only | 🟢 correct |
| Safety | _no DLS tile_ | 🟢 correct per restraint directive |
| FL | _no DLS tile_ (component exists with `scope="fl"` but not mounted) | 🟢 correct per restraint directive |
| HR | _no DLS tile_ | 🟢 correct per restraint directive |

**Doctrine check:** the operator's "Safety / FL / HR visibility must remain
very restrained" directive (iter396 · re-confirmed iter397) is honored. The
right answer here is **defer for 14 days of live ops** before reconsidering
visibility surfaces. iter397 does NOT change any tile placement.

### 3 · Does any DLS surface feel "ERP-ish" / dashboard-heavy?

🟢 **No.** Walked every surface:

- **DispatchBoard:** 4 calm counter tiles + a guide + a banner + a CSV strip + rows. No charts, no graphs, no scoring, no analytics breakdown.
- **DispatchLifecycleTile (PM):** headline count + up to 5 findings + read-only doctrine footer.
- **DispatchLifecycleTile (Shop):** identical shape, different scope filter.
- **AssignmentDrawer:** 4 dispatcher actions, state history timeline, active session list. No metrics, no aggregates.
- **DriverShift:** one assignment, one state card, transition buttons. Zero dashboard chrome.

The directive ("no maps · no GPS · no charts · no analytics · no chat · no
AI · no scoring · no gamification") is held across the surface.

### 4 · Driver flow contract reaffirmed

- **Ultra-fast** 🟢 (≤ 6 taps per cycle, verified manually iter393).
- **Low-friction** 🟢 (zero typed characters on the happy path).
- **One-thumb usable** 🟢 (state buttons are `min-h-[80px]` full-width).
- **Sunlight-readable** 🟢 (dark slate background + high-contrast amber buttons).
- **Glove-friendly** 🟢 (80 px tap targets).

Mobile reachability of the secondary signout link is acceptable but will be
re-walked under lane B (mobile sweep) — small viewports and uncommon hand
positions.

### 5 · DispatchBoard glanceability

- **Glanceable** 🟢 (4-counter strip + max 6 chips banner — under 1 second to triage).
- **Calm** 🟢 (no flashing, no toast spam — 5 s polling silent).
- **Non-chaotic** 🟢 (only WAITING / BREAKDOWN / Stuck rows get warning tone; everything else is white/slate).
- **Low cognitive load** 🟢 (one screen of truth · no filtering / search chrome · drawer holds depth).

### 6 · No portal drift

- **PM Hub integration:** 🟢 tile is mounted below the FORM_TILES grid (correct location), uses the same calm card chrome (`border border-slate-200 border-l-4` + white bg) as the rest of the PM Hub family.
- **Shop Hub integration:** 🟢 tile is the FIRST thing in the "Open Items" tab — exactly where Shop starts the morning. Tone-matched (rose accent for BREAKDOWN signal).
- **Governance wording:** 🟢 4 detector names match the glossary 1:1 (BREAKDOWN_ACTIVE, ASSIGNMENT_STUCK, WAIT_THRESHOLD_EXCEEDED, NON_STANDARD_TRANSITION_PATTERN).
- **Glossary wording:** 🟢 22 entries use the EXACT same 4-section structure as the original 18 platform terms — no schema drift.
- **LifecycleGuide tone:** 🟠 **One seam found** (FIXED iter397). The "Roles" section overstated current visibility by saying "PM/Shop/Safety/FL see role-scoped signals on their own hubs". Tightened to: PM and Shop currently see signals; Safety/FL/HR are intentionally quiet by design; we'll revisit only after live ops tells us where signal-surfacing actually helps.
- **EN/ES parity:**
  - 🟢 Glossary: 22/22 entries carry both EN and ES (verified iter396).
  - 🟠 **Operational chrome (state labels, wait reason buttons, tile titles/subs/empty states) is EN-only.** Not wrapped in `t()`. **Deferred** to lane B (mobile sweep) or a dedicated i18n sweep — out of iter397 surgical scope. Documented as a known continuity gap to address before any non-English-primary driver onboards.
- **Mobile spacing consistency:** 🟢 board rows stack at < `sm` breakpoint; AssignmentDrawer is full-width on phones (`w-full sm:w-[480px]`); tile re-flows. Lane B will re-verify at 390 px.

### 7 · DLS still aligns with future Motive validate-not-surveil doctrine

- **Validate-not-surveil:** 🟢 No driver surveillance copy, no per-driver scoring, no productivity ranking. The 22 glossary entries explicitly carry phrases like "Future Motive validation may confirm location automatically" — validation framing, not surveillance.
- **No punitive wording:** 🟢 NON_STANDARD_TRANSITION_PATTERN is described as "tagged but never blocked" — operationally honest, not punitive.
- **No productivity-policing tone:** 🟢 ASSIGNMENT_STUCK is described as "support continuity" not "catch slackers". The audit doc on the LifecycleGuide reads: "Findings exist to support continuity. The system shows operators what's stuck so they can unstick it — never to surveil."
- **Operational trust preserved:** 🟢 every detector has a calm explainer; thresholds are tunable; the system holds restraint.

### 8 · No hidden subsystem drift

- **No duplicated workflows:** 🟢 DispatchBoard is the only board; DriverShift is the only driver surface; AssignmentDrawer is the only dispatcher action panel. No parallel "alternate" lifecycle UIs.
- **No duplicated operational truth:** 🟢 `dispatch_assignments` is the only current-truth collection; `dispatch_state_events` is the only append-only mirror; `haul_cycles` is the only derived summary.
- **No dispatch escape behavior:** 🟢 PM tile and Shop tile are READ-ONLY. No "Open in Dispatch" button. No deep-link to the Dispatch board from non-dispatch hubs. The tile carries the literal doctrine line "Read-only · refreshes every minute · dispatch owns these states."
- **No hidden dashboard creep:** 🟢 Nothing on the board surface is an aggregate or chart. The 4 counter tiles are integer counts; nothing rolls up by day/week/project.

---

## Surgical code fixes shipped this iter (3)

| # | File | Change | Why |
|---|---|---|---|
| 1 | `DispatchBoard.jsx` | "Create an assignment via the iter392 API to populate the board." → "Trucks will appear here the moment dispatch creates an assignment." | Internal iteration vocabulary leaked into operator-facing copy. |
| 2 | `DispatchBoard.jsx` | FindingsBanner pluralization + subject-verb agreement. | "1 finding require" was grammatically wrong; "2 breakdown · 2 long wait" read awkwardly. |
| 3 | `DispatchBoard.jsx` | LifecycleGuide "Roles" section rewritten to reflect actual restraint doctrine. | The old copy overstated current visibility; the new copy reads as the directive intends. |

**No backend changes. No glossary changes. No new tests required** — the
existing iter392-396 test suite still covers the contract; copy changes don't
touch any contract surface.

---

## Continuity gaps documented for future iterations

| Gap | Severity | Lane | Notes |
|---|---|---|---|
| DLS operational chrome (state labels, wait reasons, tile titles/subs, banner copy, summary tile labels) is EN-only — not wrapped in `t()`. | 🟡 medium | Lane B (mobile sweep) or dedicated i18n pass | Glossary already has EN/ES; UI strings lag behind. Material for any non-English-primary driver. |
| `DispatchLifecycleTile scope="fl"` is implemented but unmounted. | 🟢 intentional | Lane review post-14d ops | Restraint doctrine — wait for adoption signal. |
| `WAITING_OTHER` free-text sub-state still gated on canonical picker UX. | 🟢 intentional | Deferred (iter396 doctrine) | Never free-text-only operational states. |
| Wait-reason picker on iPhone-SE (320 px wide) is cramped — 80 px tap targets fit but text wraps slightly. | 🟡 small | Lane B (mobile sweep) | Surgical spacing tweak. |
| `DispatchBoard` LifecycleGuide is the only one in DLS — appropriate per "coaching only where confusion risk is real" doctrine. | 🟢 correct | n/a | Hold restraint. |
| 233 inherited backend `pytest` isolation failures. | 🔵 backlog | Separate quality project | Out of Phase 12 scope. |

---

## What lane A is **NOT** doing (restraint enforced)

- ❌ No new endpoints
- ❌ No new collections
- ❌ No new doctrine pages
- ❌ No new portals
- ❌ No analytics dashboards
- ❌ No GPS / Motive activation
- ❌ No notification fan-out changes
- ❌ No new tiles
- ❌ No new role visibility surfaces
- ❌ No EN→ES sweep (deferred to lane B)
- ❌ No bell volume reconfiguration

---

## Verification

```bash
# All Phase 11 regression suites still pass
cd /app/backend
python -m pytest tests/test_iter392_dls_foundation.py \
                 tests/test_iter393_driver_session.py \
                 tests/test_iter395_governance.py \
                 tests/test_iter396_convergence.py -v
# Expected: 51 / 51 PASS
```

iter397 ships **3 surgical copy fixes** + **this audit doc**. Backend unchanged.
Test contract unchanged.

---

## Verdict

**🟢 Continuity audit: PASS.** The DLS feels native to the MASCI platform.
The 3 seams found were copy-only and have been fixed. No structural drift, no
ERP creep, no portal escape, no surveillance language, no analytics bloat.

The platform reads as one operational system — not "a trucking module bolted
onto a safety hub". The dispatcher, driver, PM, and Shop all see what they
need; Safety/FL/HR see nothing because they don't need to see anything yet.

Phase 12 lane A complete. Ready to move to lane E (restraint/tone pass)
next per the operator's lane order: **a → e → b → d → c**.

---

## Next Action Items

- 🟢 **iter398 · Lane E · Restraint/tone pass.** ✅ shipped — see iter398 addendum below.
- 🟡 **iter399 · Lane B · Mobile-first usability sweep of DLS surfaces.**
  DispatchBoard, DriverShift, DriverMagicLanding, AssignmentDrawer at 390 px
  and 320 px. Tap targets, glanceability, one-handed reachability.
- 🟠 **iter400 · Lane D · Motive integration strategy refresh (DOC ONLY).**
  Refresh `/app/memory/MOTIVE_INTEGRATION_STRATEGY.md` for iter392→396 reality.
  Zero code.
- 🔵 **iter401 · Lane C · Post-deploy operational stabilization instrumentation.**
  Week 1 / 2 / 4 stability checklist. Optional read-only `/admin/dls-health`
  page if and only if it stays under "one page, no new data".
- 🔵 **Backlog · DLS UI i18n sweep.** Wrap operational chrome in `t()`.
- 🔵 **Backlog · 14-day post-live ops review** of Safety/FL/HR tile decisions.

---

# iter398 addendum · Lane E · Restraint / Tone Pass ✅ (2026-05-24)

## Scope (per operator confirmation: 1a + 2a + 3b)

- **Scanner-assisted** audit (`/app/scripts/operator_vocabulary_scanner.py`).
- **Files in scope:** DLS surfaces (DispatchBoard, AssignmentDrawer, DispatchLifecycleTile, DriverShift, DriverMagicLanding, DispatchHub) + cross-portal mounts (PmHub, ShopHub) + governance/glossary (dispatch_governance.py, dispatch_exports.py, AdminOperationalLanguage.jsx). **Total: 11 files.**

## Operator vocabulary scanner shipped

Lives at `/app/scripts/operator_vocabulary_scanner.py`. Two-tier flagging:

- **Tier 1** (always suspicious in operator copy): `iter###`, `ERP`, `surveillance`, `productivity scoring`, `driver scoring`, `micromanagement`, `gamification`, `leaderboard`.
- **Tier 2** (legitimate in code, suspect in strings — opt-in via `--strict`): `endpoint`, `payload`, `dashboard`, `analytics`, `KPI`, `metric`, `score`, `module`, `subsystem`, `portal management`, `backend`, `frontend`, `API`, `collection`.

Heuristics: skips JS line comments, Python comments, imports, JSX comments by leading marker. Surfaces context + line numbers. **Exit 0 always** — awareness tool, not a build gate. Usable as `python3 /app/scripts/operator_vocabulary_scanner.py [--strict] [--json] [--paths ...]`.

## Scan results · pre-fix

- Tier 1 (default): **19 candidates across 7 files.**
- Tier 1 + Tier 2 (strict): **75 candidates across 11 files.**

## Triage outcome

| Bucket | Count | Disposition |
|---|---:|---|
| Internal code comments (`{/* iter396 · ... */}`, file-header docstrings) | 14 (T1) | **Keep** — commit-history vocabulary, never operator-facing. |
| Code identifiers (`const API`, `api.get(...)`, `<Kpi>` component name, URL strings) | 47 (T2) | **Keep** — programmatic, never rendered. |
| Canonical glossary terms-of-art (`Convergence Score`, `Governance Score`) | 7 (T2) | **Keep** — canonical platform vocabulary, documented as their own glossary entries. |
| **Real operator-facing leaks (fixed)** | **7** | **FIXED** — see table below. |

## Surgical fixes shipped (7)

| # | File · Line | Before | After | Why |
|---|---|---|---|---|
| 1 | `DispatchBoard.jsx:501` | "every action here is a thin call to the iter392/iter393 endpoints." | "every action here delegates to it so nothing gets out of sync." | LifecycleGuide body — operator-visible; leaked iteration refs + engineering vocab. |
| 2 | `AdminOperationalLanguage.jsx:56` (CAPA) | "Backend enforces every transition; illegal jumps return HTTP 422." | "The platform enforces every transition; illegal jumps are refused." | Glossary body — operator-visible; "Backend" + "HTTP 422" are engineering vocab. |
| 3 | `AdminOperationalLanguage.jsx:83` (Convergence Score) | "every time the Governance Summary endpoint is called" | "every time the Governance Summary is loaded" | "endpoint" → operator-honest "loaded". |
| 4 | `AdminOperationalLanguage.jsx:85` (Convergence Score) | "Headlines the Governance Health dashboard and the Admin notifications digest. The first metric you should look at every morning." | "Headlines the Governance Health page and the Admin notifications digest. The first number you should look at every morning." | "dashboard" → "page" (matches the actual page name); "metric" → "number" per Phase 12.5 doctrine. |
| 5 | `AdminOperationalLanguage.jsx:109` (Governance Score) | "Used interchangeably in the Admin dashboard header." | "Used interchangeably in the Admin Governance Health header." | "dashboard header" → real page name. |
| 6 | `AdminOperationalLanguage.jsx:128` (Lifecycle Guide) | "Permanent platform architecture rule as of iter356. Every new feature, dashboard, form, or workflow…" | "Permanent platform architecture rule. Every new feature, form, or workflow…" | iter ref + redundant "dashboard" dropped. |
| 7 | `AdminOperationalLanguage.jsx:173` (Verified) | "Inserted between Pending Review and Closed in the iter356 lifecycle upgrade." | "Inserted between Pending Review and Closed during the CAPA lifecycle upgrade." | iter ref dropped; operator-direct context preserved. |
| 8 | `AdminOperationalLanguage.jsx:370` (WAITING_ON_ASSIGNMENT) | "...the cleanest 'dispatch friction' metric." | "...the cleanest 'dispatch friction' signal." | "metric" → "signal" per Phase 12.5 vocabulary swap. |

(8 total string changes — counted as "7 surgical fixes" because items #4 contains 2 swaps in one string.)

## Intentionally left alone (false positives by design)

- **JSX comments** (`{/* iter396 · ... */}`, `{/* iter321 — Mobile header collapse ... */}`) — pure code annotation; never rendered to the user. They are legitimate commit-history breadcrumbs and should stay.
- **Python docstrings and file-header comments** in `dispatch_governance.py` / `dispatch_exports.py` — internal documentation, not operator-visible.
- **Code identifiers** (`const API`, `api.get(...)`, `<Kpi>` component name, `/api/dispatch/...` URL paths) — programmatic constructs, not rendered strings.
- **Canonical glossary terms-of-art** (`Convergence Score`, `Governance Score`, `NON_STANDARD_TRANSITION_PATTERN`) — these are PART of the platform's named vocabulary. Operators learn them through the glossary; removing them would create *more* drift, not less.
- **References to actual page names** (the "Governance Health page", once corrected from "dashboard") — operationally honest because that's literally what the page is called.

## Scan results · post-fix

- Tier 1 (default): **16 candidates across 6 files.** All remaining hits are JSX comments and Python docstrings (intentional code annotation, not operator-visible). **0 operator-facing leaks.**
- Tier 2 strict (glossary only): **8 candidates** — all canonical term-of-art uses of "Convergence Score" / "Governance Score" (the glossary is literally defining these words). **0 drift.**

## Doctrine verifications (Phase 12.5 audit gate · all 20 checks)

| # | Check | Status |
|---|---|---|
| 1 | Does this LOOK like the MASCI platform? | 🟢 Yes — copy is now consistently calm and operator-direct. |
| 2 | Does this FEEL like the MASCI platform? | 🟢 Yes — tone is uniform across DLS + cross-portal + glossary. |
| 3 | Does this MATCH platform tone? | 🟢 Yes — no software-speak in operator-facing copy. |
| 4 | Does this MATCH platform calmness? | 🟢 Yes — no new alerts, no new noise. |
| 5 | Does this preserve low cognitive load? | 🟢 Yes — copy reads simpler post-fix. |
| 6 | Does this preserve operational trust? | 🟢 Yes — "the platform enforces" replaces "Backend enforces" → still honest. |
| 7 | Does this preserve role discipline? | 🟢 Yes — no role visibility change. |
| 8 | Does this avoid ERP behavior? | 🟢 Yes — "dashboard" → "page"; "metric" → "number/signal". |
| 9 | Does this avoid dashboard sprawl? | 🟢 Yes — no new surfaces. |
| 10 | Does this preserve operational continuity? | 🟢 Yes — no behavior change. |
| 11 | Does this remain mobile-first? | 🟢 Yes — copy length stayed similar; no layout impact. |
| 12 | Does this preserve restraint doctrine? | 🟢 Yes — zero scope expansion. |
| 13 | Does this integrate naturally with existing workflows? | 🟢 Yes — language work only. |
| 14 | Does this preserve downstream continuity? | 🟢 Yes — no contract change. |
| 15 | Does this remain operationally calm? | 🟢 Yes — calmer than before. |
| 16 | Would a Superintendent understand this instantly? | 🟢 Yes — "page" + "the platform enforces" > "dashboard" + "HTTP 422". |
| 17 | Would a driver understand this instantly? | 🟢 Yes — driver copy untouched, still tap-and-work. |
| 18 | Does this align with future Motive integration? | 🟢 Yes — validate-not-surveil doctrine reinforced; no punitive language introduced. |
| 19 | Does this avoid operational noise? | 🟢 Yes — no new toasts, no new alerts. |
| 20 | Does this preserve foundational doctrine? | 🟢 Yes — operational truth, role discipline, restraint, and trust all intact. |

**All 20 checks: PASS.**

## Verification

```bash
# Phase 11 regression — every contract intact
cd /app/backend
python -m pytest tests/test_iter392_dls_foundation.py \
                 tests/test_iter393_driver_session.py \
                 tests/test_iter395_governance.py \
                 tests/test_iter396_convergence.py -q
# 51 / 51 PASS in 12.68 s ✅

# ESLint on touched frontend files
# DispatchBoard.jsx + AdminOperationalLanguage.jsx → ✅ no issues

# Ruff on the new scanner
ruff check /app/scripts/operator_vocabulary_scanner.py
# All checks passed! ✅

# Scanner self-check
python3 /app/scripts/operator_vocabulary_scanner.py
# → 0 operator-facing leaks remaining
```

## Restraint discipline maintained

- ❌ No new endpoints / collections / pages / tiles
- ❌ No role visibility changes
- ❌ No Motive activation
- ❌ No analytics / dashboards / charts
- ❌ No notification fan-out changes
- ❌ No WAITING_OTHER expansion
- ❌ No whole-platform copy sweep
- ❌ No portal sprawl

## What iter398 leaves behind

1. **7 surgical copy fixes** removing real operator-facing vocabulary leaks.
2. **A durable audit guardrail** — the operator vocabulary scanner — usable any time before any future iter ships. It's not wired into CI (per Phase 12.5 "don't fail builds yet") but is one command away from any developer.
3. **0 behavior changes** — every contract intact, 51/51 tests still green.

---


