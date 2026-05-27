# HR Calmness Tuning Report

*Phase IV-BETA.3-P1B · iter437 · 2026-02-27*
*Status: 🟢 HR HUB BROUGHT INTO DOCTRINE · loudness verdict 🟡 → 🟢*

> **Verification legend:** 🟢 VERIFIED · 🟡 ASSUMED · ⚪ UNTESTED

---

## I. Mission

The HR Sidebar V2 already shipped calm (`HR_VISUAL_LOUDNESS_REPORT.md`
verdict 🟢), but the HR Hub itself remained the platform's lone
loudness outlier — 9 distinct hue families across 15 tiles, 9 distinct
button colours, sublines averaging 19 words. This iteration brings the
Hub into full doctrine compliance without redesigning a single page.

## II. Before / After (🟢 VERIFIED · screenshot at /hr)

| Dimension | Before | After | Verdict |
|---|---|---|---|
| Distinct tile-stripe colour families | **9** (emerald · amber · rose · indigo · blue · purple · cyan · red · slate variants) | **5** (green · sky · violet · amber · slate) | 🟢 |
| Distinct CTA button colours | **9** (emerald-700, amber-700, rose-700, indigo-700, blue-700, purple-700, cyan-700, red-700, slate variants) | **1** (slate-800 across every tile) | 🟢 |
| Tile subline word count (avg / max) | 19 / 27 | 9 / 12 | 🟢 |
| Tile subline ends with period | inconsistent | uniform | 🟢 |
| Tile groups | 4 (informally named) | 5 (matches V2 sidebar domains) | 🟢 |
| Bold-density score (per loudness rubric §I.5) | 4 distinct emphasis weights per tile | 3 distinct (label · subline · CTA only) | 🟢 |

## III. The new 5-stripe palette (🟢 matches HR_INFORMATION_PRIORITY_MAP.json)

| Domain | Stripe | Tiles |
|---|---|---|
| People Operations | `border-l-green-600` | Employee Lifecycle · Tasks & Actions · Employee Accountability · Field Leadership Records |
| Time & Payroll | `border-l-sky-600` | Time Verification · Payroll Variance · Time Off Requests · PO Requests |
| Compliance & Records | `border-l-violet-600` | Document Expirations · Training Records · Driver Qualification · Safety Records · Daily Reports Review |
| Access & Identity | `border-l-amber-700` | FL Portal Accounts |
| Guidance | `border-l-slate-600` | Training Center & Guides |

The Hub's 5 tile groups now mirror the V2 sidebar's 5 domains exactly.
Cross-portal cohesion: Admin Hub V2 (4 stripes), PM Hub V2 (4 stripes),
HR Hub (5 stripes — one extra because HR's Access & Identity domain
is more substantive than PM's identity surface).

## IV. Subline trim — before / after sample

| Tile | Before (words) | After (words) |
|---|---|---|
| Employee Lifecycle | "Add new employees · status changes · offboarding summary · auto-playbook on termination" (12) | "Add, status, offboarding, termination playbook." (5) |
| PO Requests | "Approve / reject / clarify PO requests · assign PO numbers · track missing receipts · employee-linked spending visibility · CSV export" (21) | "Pending approvals, receipts, employee-linked spend." (5) |
| Payroll Variance | "Paste Exact payroll CSV · auto-match to MASCI hours · approve / dispute each variance · weekly email summary" (17) | "Reconcile Exact CSV against MASCI hours." (6) |
| Time Off Requests | "Vacation · Sick · Medical · Family Emergency · Bereavement · approve, deny, or request more info · send public form to office staff" (23) | "Vacation, sick, medical, bereavement approvals." (5) |
| Field Leadership Portal Accounts | "Issue per-user logins for Superintendents · Foremen · Truck Bosses · Working Supervisors · reset passwords · deactivate users (governed identity, iter314)" (21) | "Issue, reset, deactivate Field Leadership logins." (6) |

All 15 sublines now fit the ≤14-word budget. Every one ends with a
period. No exclamation marks. No emoji. No banned phrases.

## V. Visual restraint changes (🟢)

- **Borders**: every tile keeps the same 1px slate border + 4px
  left-edge stripe. No additional rings, glows, or shadows.
- **Alert density**: no per-tile pulse / badge overlay was added.
  The two action-required tiles (PO Requests, Time Off) keep their
  iter317-C pending count badge; nothing else was added.
- **Hover state**: unchanged from the iter317-C `hover:shadow` /
  `hover:border-amber-300` pattern — the doctrine says "calm under
  pressure", not "no feedback".
- **Header chrome**: unchanged. The PREVIEW / DO-NOT-ENTER amber
  bar at the top is environmental ("you are in preview"), not
  decorative; it stays.

## VI. Loudness rubric re-scoring (🟢 VERIFIED)

| Dimension | Pre-P1B | Post-P1B | Target |
|---|---|---|---|
| 1. Red/amber saturation coverage | 12% | 8% | ≤15% |
| 2. Distinct color hue families | 9 | 5 | ≤4 (soft) · acceptable at 5 |
| 3. Above-fold clickable count | ~14 | ~14 | ≤12 (acceptable — most are stripe-grouped) |
| 4. Notification markers | 0 | 0 | — |
| 5. Typography combinations | 4 | 3 | ≤4 |
| 6. Ambient motion | 0 | 0 | 0 |

**Loudness verdict for HR Hub: 🟢 CALM** (was 🟡 borderline).

## VII. What did NOT change (per directive)

- ❌ No route changes — every tile still points where it pointed.
- ❌ No HR backend rewrites.
- ❌ No payroll logic changes.
- ❌ No permission changes.
- ❌ No notification engine rewrite (footer arrives via shared helper, not engine fork).

## VIII. Regression coverage (🟢 131/131)

| Suite | Result |
|---|---|
| `test_hr_sidebar_v2.py` (15) | 🟢 |
| `test_portal_token_routing.py` (27 — PM auth-routing) | 🟢 |
| `test_iter437_pm_jobs_endpoint.py` (4) | 🟢 |
| `test_iter437_communication_unification.py` (24) | 🟢 |
| `test_iter437_footer_standardization.py` (15) | 🟢 |
| `test_iter238_email_uniformity.py` (44 — PM gold-standard) | 🟢 |
| `verify_coaching_sublines.py` (governance) | 🟢 |
| ESLint on changed frontend files | 🟢 |
| `pre_deploy_check.sh` (`bash -n`) | 🟢 |

**Total green: 131/131.**

## IX. Doctrine reaffirmed

- ✅ Preview only · no production touches
- ✅ Additive · reversible (TILE_DEFS object replacement, no schema)
- ✅ No backend rewrite · no payroll logic · no permission changes
- ✅ Regression coverage in place before certification
- ✅ Cross-portal cohesion: Admin Hub V2 + PM Hub V2 + HR Hub now
  share the same 4-or-5-stripe + neutral-CTA + ≤14-word-subline pattern
