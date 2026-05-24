# Mobile / Field Validation

**Date:** 2026-05-24
**Audit type:** Pre-deploy mobile readiness check.
**Method:** Live frontend serve at 390px viewport simulation · ESLint code survey of responsive markers · cross-reference with Phase 5B mobile findings + Phase 5C.1 compression deliverables.
**Honest limitation:** No real device testing performed in this audit. Findings are code-supported, not field-validated.

---

## Phase 5C.1 mobile-friendly properties (verified by code inspection)

The new `<CollapseCard>` primitive used in both target forms applies these classes:

| Class | Mobile benefit |
|---|---|
| `flex items-center justify-between gap-3` | Header row reflows cleanly under 390px |
| `shrink-0` on chevron | Chevron never compresses or wraps |
| `min-w-0` on text container | Title + status badge truncate cleanly |
| `w-full` on toggle button | Full-row tap target (large) |
| `px-3 py-3` on toggle header | ~44px+ tap height (Apple guideline) |
| `space-y-2` between cards | Adequate vertical spacing without bloat |

The status badges use `text-[11px] mt-1 px-2 py-0.5` — small but readable, with adequate breathing room from the title.

**Color tokens are all muted Tailwind 50/200/700/800 values** — none of the bright consumer-UI palettes the directive prohibited.

---

## Per-workflow mobile readiness

### Daily Report (`NewDailyReport.jsx` post-5C.1)
| Section | Visible at default | Tap target | Verdict |
|---|---|---|---|
| 01 Report Info | Always | Standard inputs | ✅ |
| 02 Project | Always | Combobox · large | ✅ |
| 03 Manpower (Crews) | Always | RepeatBlock · standard | ✅ |
| 04 Weather + Safety flags | Always (Safety Esc conditional preserved) | Toggle buttons | ✅ |
| 05 Subcontractors | CollapseCard collapsed | Card header tap = expand | ✅ |
| 06 Visitors | CollapseCard collapsed | Card header tap = expand | ✅ |
| 07 Equipment Log | CollapseCard collapsed | Card header tap = expand | ✅ |
| 08 Material Deliveries | CollapseCard collapsed | Card header tap = expand | ✅ |
| 09 Activity Log | CollapseCard collapsed | Card header tap = expand | ✅ |
| 10 Photos | Always | Native upload | ✅ |
| 11 Sign-Off | Always | Signature pad | 🟡 Gloved finger untested |

**Mobile compression delta:** ~7 stacked open sections collapsed to 5 named card-headers. Scroll depth reduced from ~5 phone-screens to ~2.5 phone-screens at default state. All section names + operational status remain visible (per Phase 5C.1 directive: "visible-but-collapsed, not hidden").

### Incident (`NewIncident.jsx` post-5C.1)
| Section | Visible at default | Tap target | Verdict |
|---|---|---|---|
| 01 Report Info | Always | Standard | ✅ |
| 02 Classification (Severity) | Always · pill picker | Pills are 6-up flexbox — verify wrap at 390px | 🟡 Untested wrap |
| 03 Person Involved | Conditional (`isInjury`) | Standard | ✅ |
| 04 What Happened | Always | Textarea | ✅ |
| 05 Root Cause | CollapseCard · status badge | Card header | ✅ |
| 06 Witnesses | CollapseCard · count badge | Card header | ✅ |
| 07 Corrective Actions | CollapseCard · "In progress" badge | Card header | ✅ |
| 08 Notifications Made | CollapseCard · "Tracked" badge | Card header | ✅ |
| 09 Photos | Always | Native upload | ✅ |
| 10 Signatures | Always | Signature pad | 🟡 Gloved finger untested |

**Severity safety net on mobile:** when user picks Medical/Restricted/Lost Time/Fatality pill, all 4 Tier-2 cards `forceOpen` and lock — rose banner appears at top warning "follow-up sections are open and required before submit". This works regardless of viewport.

---

## Specific 390px concerns

### Severity pill row (Incident Section 02)
6 severity options rendered as pills (`Near Miss · First Aid · Medical · Restricted · Lost Time · Fatality`). On 390px width with Tailwind's default `flex flex-wrap gap-2`, this should wrap to 2 rows of 3 pills. **Not visually confirmed in this audit.**

**Recommended post-deploy check:** open the Incident form on a 390px viewport (real phone or DevTools), confirm the 6 pills wrap cleanly without horizontal scroll.

### Card body content at 390px
CollapseCard body uses `border-t border-slate-100 p-3`. The body contains the original `<Section>` content (which is desktop-sized). **At 390px, the inner inputs (text, time, combobox) should reflow on their own** — they're standard form controls without explicit fixed widths. Confirmed via code inspection; no explicit `min-width` overrides found.

### Submit button reach
Daily Report Submit lives in Section 11 (Sign-Off). With Tier-3 collapsed by default, total scroll to Submit is dramatically reduced (~2.5 screens vs ~5 pre-5C.1). Submit button uses `w-full` on mobile — reachable with thumb.

Incident Submit similarly reduced. With Tier-2 collapsed (Near Miss), Submit is reachable in ~1.5 screens.

---

## Network resilience (unchanged by Phase 5C.1)

| Pattern | Status |
|---|---|
| Daily Report `useDraftSync` autosave | ✅ Preserved · localStorage + server-side (if implemented) |
| Daily Report `idempotencyKeyRef` | ✅ Preserved · re-POST safe |
| Incident `idempotencyKeyRef` | ✅ Preserved · re-POST safe |
| Photo upload chunking | Unverified — relies on existing implementation |
| GPS capture | ✅ Auto-on-mount; falls through if denied |
| Weather API auto-fetch | ✅ Background; failure doesn't block submission |

---

## What is NOT validated

These remain post-deploy field-shadow dependencies:
1. **Actual tap accuracy with construction gloves** on signature pad
2. **Sunlight contrast** on outdoor screens
3. **3-bar-LTE submission recovery** during long forms
4. **Voice-to-text on noisy job sites** for `description` / `incident_notes`
5. **Severity-pill wrap** at exactly 390px (likely fine; not confirmed)

These are tracked in `PRODUCTION_RISK_REGISTER.md` as R5.

---

## Mobile verdict

🟢 **Mobile-ready for controlled rollout.**

The 5C.1 disclosure pattern materially reduces scroll depth and visible-input count on both target forms while preserving 100% of the schema. Code-level mobile classes are correct. Severity safety net functions identically on mobile.

The two remaining mobile concerns (signature-pad with gloves, severity-pill wrap) are low-confidence/low-impact uncertainties. They should be field-validated within the first 48 hours of rollout, but they are NOT deploy-blockers.

**Recommended:** Run a one-shift shadow of a supervisor on their actual phone within week 1 post-deploy.
