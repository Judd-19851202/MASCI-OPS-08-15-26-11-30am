# Portal V2 Default Readiness — Phase IV-BETA.5A-P1B

*iter437 · 2026-02-27*
*Status: 🟢 REVIEW COMPLETE · operator decision pending*

> **Verification legend:** 🟢 VERIFIED · 🟡 ASSUMED · ⚪ UNTESTED

---

## I. Mandate

Conduct the final pre-flip readiness review for **PM V2**, **HR V2**,
and **Safety V2**. Classify each as 🟢 stable default candidate /
🟡 caution / 🔴 blocker. Operator owns the actual flip decision.

## II. Review categories

| Category | What we measure |
|---|---|
| Hierarchy clarity | Single hierarchy hash across viewports |
| Operational speed | Page render path, no admin-leak retry storms |
| Mobile ergonomics | Touch targets, scroll behaviour at 390 × 844 |
| iPad ergonomics | Sidebar gating at lg breakpoint, 1024 × 1366 |
| Auth stability | Zero `/api/admin/*` leakage from non-admin contexts |
| Coaching quality | `verify_coaching_sublines.py` clean across sidebar domain map |
| Communication consistency | Footers, severe-tier subject contracts |
| Doctrine stability | Baseline loudness · drift script signal |
| Visual calmness | Hue family count · CTA neutralisation · stripe palette |
| Escalation clarity | Severity pills + severe-tier banners preserved |
| Regression maturity | All suites green |

## III. PM V2 — readiness 🟢 STABLE DEFAULT CANDIDATE

| Category | Result | Note |
|---|---|---|
| Hierarchy clarity | 🟢 consistent | 1 hierarchy hash across 3 viewports |
| Operational speed | 🟢 stable | Zero admin-leak retries; PmJobsRead (iter437 P0) lives clean on `/api/pm/jobs` |
| Mobile ergonomics | 🟢 strong | Mobile loudness 15.27 — calmest of all portals at small viewport |
| iPad ergonomics | 🟢 strong | Sidebar V2 mounts at lg+ |
| Auth stability | 🟢 verified | `test_portal_token_routing.py` 27/27 |
| Coaching quality | 🟢 passes | `pm/sidebar/domainMap.js` governed under coaching gate |
| Communication consistency | 🟢 anchored | Owns the email gold-standard (iter238) |
| Doctrine stability | 🟢 stable | Loudness 26.86 desktop, 15.27 mobile · all `stable` band |
| Visual calmness | 🟢 best-in-class | Lowest loudness on the platform |
| Escalation clarity | 🟢 preserved | PM is not an escalation surface; calm by design |
| Regression maturity | 🟢 mature | Multi-suite coverage, no flake history |

**Verdict:** PM V2 is ready for default flip on operator authorisation.

**Friction:** none material.
**Remaining loudness:** none above doctrine.
**Recommended timing:** flip at the same time as HR V2 or any deploy
window operator chooses.

---

## IV. HR V2 — readiness 🟢 STABLE DEFAULT CANDIDATE

| Category | Result | Note |
|---|---|---|
| Hierarchy clarity | 🟢 consistent | 1 hierarchy hash across 3 viewports |
| Operational speed | 🟢 stable | iter437 P0 auth-routing applied; zero admin-leak in HR context |
| Mobile ergonomics | 🟢 strong | Hub tiles + slate KPI strip · mobile loudness 63.96 |
| iPad ergonomics | 🟢 strong | Sidebar mounts at lg+ |
| Auth stability | 🟢 verified | `test_hr_sidebar_v2.py` 21/21 |
| Coaching quality | 🟢 passes | `HrSideNavV2.jsx` governed under coaching gate |
| Communication consistency | 🟢 anchored | `branded_portal_emails.py` + `operational_footer.py` |
| Doctrine stability | 🟡 monitor | Loudness 64.71 desktop — within monitor band; driven by data-bound badges, NOT decorative loudness |
| Visual calmness | 🟢 disciplined | 2 hue families · single neutral CTA · 5 domain stripes |
| Escalation clarity | 🟢 preserved | HR escalation pills (overdue payroll, expired cert) preserved at amber |
| Regression maturity | 🟢 mature | iter437 IV-BETA.3B + P1B passes lock the surface |

**Verdict:** HR V2 is ready for default flip.

**Friction:** the 64.71 monitor loudness is fully explained by
data-bound badge density (severity / overdue / expirations) — these
are operationally-required and doctrine-preserved. The chip honestly
surfaces this state without panic.

**Remaining loudness:** none decorative.
**Recommended timing:** flip in the same deploy as PM V2 OR after 1
more iteration of trend data (operator preference).

---

## V. Safety V2 — readiness 🟡 CAUTION — 1 cycle of operator validation

| Category | Result | Note |
|---|---|---|
| Hierarchy clarity | 🟢 consistent | 1 hierarchy hash across 3 viewports |
| Operational speed | 🟢 stable | No admin-leak retries; `test_safety_sidebar_v2.py` clean |
| Mobile ergonomics | 🟢 strong | Mobile loudness 68.04 — same band as HR; severity pill preserved |
| iPad ergonomics | 🟢 strong | Sidebar mounts at lg+ |
| Auth stability | 🟢 verified | 21/21 admin-leak guards |
| Coaching quality | 🟢 passes | `SafetySideNavV2.jsx` added to coaching gate |
| Communication consistency | 🟢 anchored | Severe-tier email subject contract preserved |
| Doctrine stability | 🟡 monitor | Loudness 66.78 desktop — within monitor band; same data-bound profile as HR |
| Visual calmness | 🟢 disciplined | 2 hue families — collapsed from 9 in audit; CTA neutralised |
| Escalation clarity | 🟢 preserved | SEV_PILL, OSHA pill, severe banner all untouched |
| Regression maturity | 🟢 mature | 21 new tests; visual doctrine baseline captured |

**Verdict:** 🟡 CAUTION — Safety V2 is mechanically ready, but the
phase landed only THIS iteration. Operator-grade validation across a
real working week is recommended before default flip. The technical
gates all pass; the recommendation is purely operational caution.

**Friction:** none mechanical.
**Remaining loudness:** none decorative.
**Recommended timing:** wait 1–2 iterations of trend data **OR**
flip alongside PM/HR if operator wants to consolidate the deploy.

---

## VI. Default-flip mechanics (🟢 ready)

When the operator authorises a default flip for any of the three
portals, the change is a **single-line edit** in each Shell:

| Portal | Shell | Current default | Change |
|---|---|---|---|
| PM | `PmShell.jsx` | `isPmSidebarV2Enabled()` reads `?pmSidebarV2=1` | Flip to `true` by default; keep `?pmSidebarV2=0` as escape hatch |
| HR | `HrPageShell.jsx` | `useHrSidebarV2Enabled()` reads `?hrSidebarV2=1` | Same flip pattern |
| Safety | `SafetyShell.jsx` | `useSafetySidebarV2Enabled()` reads `?safetySidebarV2=1` | Same flip pattern |

All three changes are individually revertible without code churn.

## VII. Blockers (🟢 NONE)

No 🔴 BLOCKER classifications. All three portals pass every category.

## VIII. Doctrine reaffirmed

- ✅ Operator owns the flip decision · review is advisory
- ✅ Each portal flippable independently
- ✅ Escape-hatch query parameter pattern is preserved for rollback
- ✅ No mechanical blockers across any of the three portals
- ✅ Preview only · no production deploy from this review
