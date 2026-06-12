# MASCI Operations Platform — Design System V1

**Status:** Blueprint only · NO implementation · NO code change · NO deploy · NO GitHub save · NO merge.  
**Generated:** 2026-02 (Track 13.5A).  
**Source of truth:** Tracks 13.4A → 13.4F discovery (78 active findings · 33 risks · 154 evidence screenshots · 25 audit documents).

---

## 1. Executive Summary
MASCI OPS does not need a redesign. It needs **one identity** stitched across nine portals and 22 public surfaces. Discovery proved the platform has strong operational bones — Trench Safety, the post-13.4A Dispatch/HR/PM portals, the Operations Map, the Operational Guidance Center — but its **visual chrome, status language, headers, KPI strips, status chips, and theme tokens have drifted**. Design System V1 unifies those layers under one operator-native, heavy-civil, mobile-first identity that satisfies all five pillars: **Powerful · Simple · Beautiful · Trusted · Proven.**

---

## 2. Design Doctrine
- **One MASCI Operations Platform**, not nine apps sharing login.
- **Operator-native verbiage** — Daily Report, Pre-Op, Crew, JHA, Field Truth, Project Risk. No ERP, no SaaS toy, no software-company jargon.
- **Field-first, mobile-first, calm.** Dispatchers on tablets, foremen on phones, supers in trucks.
- **Truth over polish.** Stale data is labelled stale; unknown is labelled unknown; "looks live" is forbidden when it isn't.
- **Preserve before standardise.** The Preserve List is a bright line.
- **Discovery-driven.** Every standard below references a finding it resolves.

---

## 3. Five-Pillar Design Requirements
Every component must pass:
- **Powerful** — surfaces the question the role is asking right now.
- **Simple** — single canonical pattern; no second way unless operationally justified.
- **Beautiful** — calm, durable, heavy-civil; not flashy, not sparse.
- **Trusted** — labels its own staleness/uncertainty; never fakes data.
- **Proven** — verified visually at desktop · iPad LS · iPad PT · phone via operator screenshots, not DOM tests.

For each system below, the pillar mapping is noted in-line.

---

## 4. Preserve-First Rules
The 12 items in `MASCI_PLATFORM_PRESERVE_LIST.md` are out of scope for change:
Trench Safety architecture · PM rebuild (Track 13.4A baseline) · Dispatch Map fix · Operations Map consistency · per-portal auth isolation · append-only ledger · Operational Guidance Center · operator-native tile labels · Safety Forms inline EN+ES legal text · Visual Render Guardrail · integration baseline · existing tenant-config plumbing (`training_guides`, `training_videos`, `digest_settings`).
**Forms are also Preserve-First.** Daily Report · JHP · Incident · CAPA · Safety Forms · QA/QC · Training · Equipment · Trench Safety — workflows stay intact. Design System V1 defines only the **visual wrap, spacing, sectioning, coaching, and action placement** around them.

---

## 5. Global Visual Identity
**Feels:** heavy-civil · operational · calm · clear · durable · professional · field-native · trustworthy · executive-capable without corporate theatre.  
**Does not feel:** SaaS toy · ERP monster · dashboard circus · random portal collection · flashy · noisy · over-designed · under-designed.  
**Texture:** off-paper backgrounds, restrained shadows, sharp left-aligned typography, calm density. Generous whitespace where data is sparse; dense where operators need scan-speed.

---

## 6. Brand System
- **MASCI mark:** primary brand in every operator portal header (top-left, 24–32px height; iconic + wordmark; never alone-iconic in primary chrome).
- **ForgedOps mark:** discreet attribution footer ("Powered by ForgedOps") on operator portals; reserved as primary brand on a future tenant-onboarding shell. The `forgedops-logo.png` asset is the reserved slot.
- **Portal-accent badge:** small kicker pill ("DISPATCH · OPERATIONS", "SAFETY · COMPLIANCE") — not its own logo. One palette token controls it.
- **Public surfaces:** MASCI brand visible top-left, ForgedOps attribution absent (public visitors don't need parent-brand chrome).
- **Reports / PDFs / Excel:** MASCI legal name + ForgedOps attribution footer; the **per-tenant slot** is reserved in §24.
- **QR / cheatsheet:** MASCI brand top-left; no ForgedOps in safety-critical operator artefacts.
- **Never:** mixed-case "Masci", outdated marks, foreign brand logos inside portal chrome.

---

## 7. Header System
Single `<PortalShell>` chrome carries every portal:
- **Row 1 (52px desktop, 56px tablet, 64px phone):** MASCI mark · portal kicker pill · global search · notification bell · language toggle · profile.
- **Row 2 (40px, optional):** portal name · breadcrumb (e.g. `Dispatch · Operations Board · Asset DT-4`) · primary CTA.
- **Mobile:** Row 1 collapses search + bell + lang into an overflow menu; Row 2 becomes a sticky title bar.
- **Public chrome:** lighter shell — MASCI mark · public-surface name · language toggle. No portal switcher.
Answers: *Where am I? Which role? What needs attention? What can I do next?*  
**Resolves:** V-06 (≥4 header strategies) · V-13 (mobile evidence) · V-09 (command-center sprawl).

---

## 8. Portal Home System
Every operator portal home must answer its role question in **≤5 seconds**:

| Portal | Question | Required surface |
|---|---|---|
| Admin | What requires administrative oversight? | Governance chip · admin attention queue · audit/health summary |
| Dispatch | Where is my fleet & what needs dispatch action? | DispatchMapHero (≥420 px tablet · ≥520 px desktop) · counts strip · attention queue |
| PM | What requires PM attention today? | Project rows with "MISSING DAILY REPORT" et al. · Section A–E preserved |
| Safety | What requires safety attention today? | Open incidents · CAPAs · certs expiring · JHA active |
| Shop | What equipment requires recovery? | Open repairs · holds · failed pre-op queue |
| HR | What requires HR attention today? | HrKpiStrip · expirations · employee requests · driver safety events |
| Leadership | What requires executive visibility? | Cross-portal governance roll-up · risk register top items |
| Field Leadership | What requires FL action today? | Active records queue · 10 record-kind CTAs |
| Driver | What is my next assignment / shift / action? | Current assignment card · pre-trip CTA · today's daily CTA · acknowledge button |
**Forbidden:** random directories · KPI theatre · dumping grounds.

---

## 9. KPI / Metric System
- **Allowed only when actionable.** Each KPI card answers "would a role tap this in the next hour?"
- **Card layout:** label (operator verb) · big number · trend pill (calm — no red explosions) · status dot · last-updated timestamp · drill CTA.
- **Stale-data rule:** every KPI shows its `as_of` timestamp; if older than the agreed threshold, the card adds a "Stale" stripe (not red, slate).
- **Empty rule:** `<EmptyState>` primitive with neutral copy ("No active items today.").
- **Loading rule:** skeleton shimmer ≤200 ms, then default to "—" with stale-label.
- **No vanity metrics.** No "Total ever" unless governance-required.

---

## 10. Card System
One `<Card>` primitive, four variants:
- **Operational** — primary surface for a unit of work (an asset, an incident, a PO).
- **Action** — single-CTA card for "do this now".
- **Summary** — multi-stat rollup (KPI strip cell).
- **Warning** — slate frame · amber stripe · icon + text + recover-CTA.
Required: clear title · clear purpose · clear state · clear action. **Forbidden:** mystery buttons · hidden critical action · ambiguous icons-only.

---

## 11. Status / Badge / Pill System
**Resolves V-07 (15 chip components, 2 share filename), V-10 (case drift), V-11 (verb overload), V-12 (closure drift), T-12 (verb translation 0 %).**
- **One `<StatusChip>` primitive.** Pill shape (12px radius), 24px height, 12px text, icon + label.
- **Casing:** Title Case for labels. Lowercase reserved for internal engine literals.
- **Severity palette:** neutral · info (slate) · positive (emerald 600) · attention (amber 600) · urgent (red 700) · halt (red 900). Never use red for normal "done".
- **Color is never the only signal** — every chip carries an icon and text.
- **Tooltip on hover** explains the verb in operator-native language.
- **Canonical operator vocabulary (non-punitive):**
  - `Draft · Submitted · Needs Revision · Pending Verification · Verified · Closed · Reopened`
  - Holds: `Safety Hold · Maintenance Hold · Certification Hold · Inspection Hold`
  - Asset state: `In Transport · Assigned · Available · Returned to Service · Stale Position · Offline (Feed)`
- **Forbidden words:** Rejected · Denied · Failed (replace with Needs Revision · Action Required · Pending Closure).
- **Engine vocabulary stays per workflow**; the chip translates engine literal → operator verb at render. Closure verb per workflow registered once; defaults to `Closed`.

---

## 12. Navigation System
- **Top-level: portal switcher pill** in `<PortalShell>` Row 1.
- **Within portal: tile-group hub OR command-center**, never both.
- **Public surfaces:** linear nav (Home · Cheatsheet · Asset Lookup · Public Forms · Language). No portal-style chrome.
- **Cross-portal link convention:** `?from=portal` query carries return context.
- **Back behaviour:** always returns to the originating role landing, never to `/`.
- **No hidden critical workflow.** Anything Tier-1 in the priority matrix has a top-of-portal entry.

---

## 13. Table System
One `<DataTable>` primitive with:
- **Header row** sticky; column types declared (status · date · number · text · action).
- **Filter chip row** above table; chips show count.
- **Search** debounced 250 ms; supports operator verbs.
- **Row actions** in a single trailing-cell overflow menu; primary action inline as a tertiary button.
- **Empty / loading states** delegated to `<EmptyState>` primitive.
- **Status column** always uses `<StatusChip>`.
- **Date/time** rendered as relative ("3 h ago"), absolute on hover.
- **Mobile alternative:** auto-flips to stacked card list below `sm`.

---

## 14. Form Presentation System
**Preserve-first.** Field requirements, validation, and workflow unchanged. Visual layer only:
- **Form header:** title · workflow context · save state · Spanish toggle.
- **Section grouping:** 1–4 sections per page, each titled in operator verb.
- **Field spacing:** 16 px vertical between fields; 32 px between sections.
- **Required indicator:** trailing red asterisk + `aria-required`.
- **Helper text:** below input, calm gray, 14 px, never alarmist.
- **Coaching slot:** right-rail on desktop, collapsible above section on mobile.
- **Save / Submit:** sticky bottom bar on mobile · trailing-right primary CTA on desktop.
- **Errors:** inline below field; section badge counts errors; submit blocked with banner.
- **Spanish-readability:** all labels and helper text go through `t()` (resolves T-02/T-03 over time).
- **Public form chrome:** lighter shell, MASCI mark, language toggle, no portal switcher (resolves V-14).

---

## 15. Coaching / Guidance System
- **Three coaching surfaces:** in-form (right-rail / collapsible) · Hub-Banner (rotating per portal) · `OperationalGuidanceCenter` (deep). All link back via `?from=`.
- **Tone:** field-respectful, operator-native, Spanish-ready first (T-01 closure).
- **Density:** ≤1 coaching block per visible section.
- **Hidden until needed** for repeat tasks; sticky for first-time and safety-critical.
- **Safety coaching:** always visible, slate-frame + amber accent, never collapsed.

---

## 16. Notification / Alert Visual System
- **Bell:** badge count = un-acknowledged · drawer lists items with `<StatusChip>` severity.
- **Digest preview:** subject · summary line · CTA · time.
- **Severity hierarchy:** info → attention → urgent → halt. Halt is reserved for safety / outage.
- **Stale-data warning** uses the slate "Stale" stripe — never red.
- **Feed-status banner** appears only when `feed_status ∈ {delayed, offline}`; tone calm, says exactly what the operator should do.
- **No fake urgency.** No duplicate per-action + digest unless the digest filters out already-acknowledged items (resolves R-07).

---

## 17. Empty State System
`<EmptyState>` primitive carries icon · title (operator verb) · explanation · CTA · "this is normal" / "needs action" tag.  
**Forbidden:** blank white boxes · "No data" without context.

---

## 18. Error / Success / Validation System
- **Errors:** explain · recover · refer to coaching · never blame operator.
- **Success:** brief banner, auto-dismiss 4 s, never blocks UI.
- **Safety-critical validation:** modal halt with explicit acknowledgement (Trench Safety rated-depth precedent).
- **Spanish path:** every message goes through `t()`; backend `HTTPException.detail` translation is a Phase-2 follow-up (T-11).
- **Field-friendly wording:** short, plain, operator-native.

---

## 19. Modal / Drawer System
- **Modal:** ≤1 destructive action per surface; cancel always visible.
- **Drawer:** filters · row actions · multi-step flows on tablets.
- **Full page:** anything with >3 sections or photo upload.
- **Mobile:** modal → bottom sheet; drawer → full-screen.
- **Forbidden:** trap modals, modals over modals, modal-buried critical workflows.

---

## 20. Public Surface System
Lighter `<PublicShell>` chrome:
- Top: MASCI mark · public-surface name · language toggle.
- Bottom: simple footer · ForgedOps attribution discreet (or absent on safety-critical artefacts).
- Visual tone: calm, trustworthy, friendly. No admin-style controls, no portal switcher, no internal status chips.
- Public Safety Tile · Field Tile · QR landing · Asset Lookup · damage reporting · public training: all carry the same `<PublicShell>` (resolves V-14, W-15).

---

## 21. Mobile / iPad System
- **iPad landscape (≥1024 wide):** two-column hub, sticky header, in-form right-rail coaching.
- **iPad portrait (≥768):** single-column hub, collapsible coaching, sticky form save-bar.
- **Phone (<768):** stacked cards, bottom action bar, hide secondary chrome.
- **Touch targets:** ≥44 px (Apple HIG). Status chips remain tappable for tooltip.
- **Safe area** honoured on iOS (bottom inset).
- **Sticky actions** at the bottom for primary CTA on phones.
- **Map surfaces** keep responsive heights from Track 13.4A (300 / 420 / 520 px).

---

## 22. Accessibility / Readability
- **Contrast:** WCAG AA minimum; AAA for safety-critical text.
- **Min font:** 14 px body · 12 px helper · 16 px form input.
- **Color-not-only:** every status uses icon + text.
- **Sunlight & dirty-hands:** body text 16 px+ on forms; primary CTA min 48 px tall; icons inline.
- **Focus rings** explicit, 2 px, brand-tinted.

---

## 23. Translation Presentation Rules
**Must be Spanish-ready (T-01 + T-02 + T-03 + T-04 closure path):**
- Field forms · Safety forms · JHA/JHP guidance · Trench Safety guidance · Incident reporting · CAPA field guidance · Coaching · Validation · Public field surfaces.

**May remain English for now (lower priority — T-05/T-06):**
- Admin diagnostics · Persistence/Production/Stability health · Internal exports · PM/admin office-only reports · Backend technical surfaces.

**Layout:** every translatable label budgets +30 % length for Spanish wrap. Sticky CTAs reserve space.  
**Spanish toggle** present on every operator and public surface.  
**Server-rendered emails / PDFs (T-08, T-09):** future Phase-2 task — design reserves a `lang` slot on PDF templates and email templates today.

---

## 24. White-Label Readiness Notes (no architecture proposal — slots only)
- **Tenant logo slot:** reserved as a `<BrandMark tenant="…">` consumer in `<PortalShell>` and `<PublicShell>`.
- **Tenant color tokens:** all chrome reads from CSS variables in `tokens.css` (currently V-04 unwired); per-tenant overlay is the future model.
- **Tenant name slot:** reserved in PDF headers · email subjects · legal text bodies (W-09 closure path).
- **Tenant terminology slot:** "Project Manager", "Daily Report", "JHA" become token references long-term; for V1 they remain operator verbs at MASCI.
- **Tenant email / report branding slot:** templates parameterised with tenant brand block.
- **Tenant public-page branding slot:** `<PublicShell>` accepts tenant brand props.
- **Do NOT hardcode** new MASCI literals; new strings must go through `t()` and brand mark must come from the slot.

---

## 25. Implementation Guardrails
- **Preserve working workflows.** Every change cross-checked against the Preserve List.
- **Phased rollout.** No big-bang.
- **Operator screenshot wins** — every change captures desktop · iPad LS · iPad PT · phone before/after.
- **No DOM-only validation** — Visual Render Guardrail principle from Track 13.4A extends to every new surface.
- **Operator approval required** per implementation track.
- **No deploy / no GitHub save** until operator visually approves.

---

## 26. Anti-Drift Rules
1. **No new `StatusBadge`** — extend `<StatusChip>`.
2. **No new portal header** — extend `<PortalShell>`.
3. **No new KPI card style** — extend the canonical card.
4. **No new public form chrome** — extend `<PublicShell>`.
5. **No new color** without platform review against tokens.
6. **No new `*CommandCenter`** page without ratifying it against the naming taxonomy (resolves V-09).
7. **No new terminology** without glossary check.
8. **No component fork** without an explicit reason recorded in the RC ledger.

---

## 27. Design QA Checklist (run before merging any future change)
- [ ] Passes Powerful · Simple · Beautiful · Trusted · Proven.
- [ ] Matches MASCI visual system (header · chip · card · empty · modal).
- [ ] Preserves role clarity (no cross-portal language leak).
- [ ] Renders at desktop · iPad LS · iPad PT · phone (4 screenshots).
- [ ] No duplicate pattern introduced.
- [ ] Uses canonical status language; closure verb correct.
- [ ] Coaching slot used (not inlined).
- [ ] Spanish-ready (every label `t()`-wrapped; layout +30 % budget).
- [ ] No regression in any Preserve-List item.
- [ ] Visual Render Guardrail applies where canvas/SVG is critical.
- [ ] Operator approval recorded in RC ledger.

---

## 28. Screens / Components to Preserve
Trench Safety module · Operations Map (`/operations-map` + `DispatchMapHero`) · PM Command Center (post-13.4A) · HR Hub (post-13.4A) · Dispatch Hub (post-13.4A) · Hub home `/` · Operational Guidance Center · Master sign-in `/sign-in` · Track 13.4A Visual Render Guardrail · Safety Forms Equipment Issuance EN+ES legal text · `training_guides` / `training_videos` admin editors · `digest_settings` admin editor · per-portal auth isolation.

---

## 29. Screens / Components Needing Standardisation
Per `MASCI_PLATFORM_STANDARDIZATION_LIST.md`:
S-1 Status Chips (one primitive) · S-2 Colors (wire `tokens.css`, V-04) · S-3 Terminology (verb registry + closure verbs) · S-4 Notifications (single registry · dedup) · S-5 Coaching patterns (right-rail vs banner vs deep) · S-6 Tables (one `<DataTable>`) · S-7 Forms (one section/spacing/coaching/sticky-action pattern) · S-8 `<EmptyState>` primitive · S-9 `<PortalShell>` / `<PublicShell>` headers · S-10 navigation taxonomy.

---

## 30. Screens / Components Requiring Future Rebuild
Per `MASCI_PLATFORM_REBUILD_LIST.md`:
R-01 Status & Verbiage Engine · R-02 Portal Identity & Header · R-03 Navigation Architecture (incl. compliance + health duplication) · R-04 Theme Layer (`tokens.css` wiring) · R-05 Command Center taxonomy · R-06 Forms overlap reduction (Daily / Inspect / Incident shared sub-form · auth-flow consolidation) · R-07 Driver Portal (V-15 / R-13 was invalidated — landing exists; "deeper role audit deferred") · R-08 Notification layer registry.

---

## 31. Final Design Verdict

### Preserve
The 14 items in §28. Do not touch without explicit Preserve-List cross-check.

### Standardise (V1 implementation order)
1. **Wire `tokens.css`** (V-04 closure). Tokens become the single color/typography/spacing source of truth.
2. **`<PortalShell>` + `<PublicShell>`** consolidate every header strategy.
3. **`<StatusChip>` + canonical verb registry** consolidate the 15 chip components and 23 mixed-case verbs.
4. **`<EmptyState>` + `<DataTable>` + `<Card>`** primitives.
5. **Form-shell primitives** (section · spacing · sticky save · coaching slot · Spanish toggle).
6. **Notification registry** (dedup PO digest etc.).

### Rebuild later (operator-authorised separately)
R-01 → R-08 in `MASCI_PLATFORM_REBUILD_LIST.md`. Sequencing waits on Operational Recovery Phase 1 stabilisation.

### Do not touch without operator approval
Anything on the Preserve List. Forms workflows. Auth isolation. The Visual Render Guardrail.

### Recommended implementation sequence (operator-authorisation gated)
1. **Phase A — Foundation (this Design System V1 + token wiring).** No surface changes; tokens map 1:1 to current colours so the rollout is a zero-visual-diff plumbing pass.
2. **Phase B — Shared primitives (`<PortalShell>` · `<PublicShell>` · `<StatusChip>` · `<EmptyState>` · `<Card>` · `<DataTable>` · form shell).** Per-portal migration in priority order: Dispatch → HR → PM → Shop → Safety → Field Leadership → Admin → Leadership → Driver (Dispatch first because it's the operational truth surface; HR/PM already post-13.4A).
3. **Phase C — Status verb registry + canonical chips replace bespoke chips.** Run alongside Phase B per portal.
4. **Phase D — Standardised form shells across Daily / Inspect / Incident / Equipment / QA/QC / Field Leadership records.** Workflows untouched.
5. **Phase E — Coaching · notification registry · empty states standardised across the platform.**
6. **Phase F — Public surface `<PublicShell>` rollout across all 22 public surfaces.**
7. **Phase G — Spanish-readiness pass** (Safety-Critical 75.8 → ≥95 % · backend email/PDF Spanish layer · status verb translation wrap).
8. **Phase H — White-label slot wiring** (`<BrandMark tenant>` · per-tenant CSS overlay · template tenant block) — gated by ForgedOps roadmap authorisation.

**No implementation is performed by this document.** Design System V1 ends here as a blueprint. Operator must explicitly authorise each Phase A–H separately before any code change.
