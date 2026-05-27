# HR Portal · Current State Audit

*Phase IV-BETA.3B · iter437 · 2026-02-27*
*Mirrors `PM_PORTAL_CURRENT_STATE_AUDIT.md` discipline for the HR portal.*
*Verification legend: 🟢 VERIFIED · 🟡 ASSUMED · ⚪ UNTESTED*

---

## I. Scope of this audit

This document inventories the HR portal **as it exists today** before
Sidebar V2 / coaching / loudness governance is applied. It is the
baseline against which IV-BETA.3B implementation is measured.

## II. Frontend surface (🟢 VERIFIED · grep & ls)

| Surface | File | LOC | Notes |
|---|---|---|---|
| Hub | `pages/HrHub.jsx` | 277 | 15 tiles, already grouped into 4 sections by iter317-C |
| Shell | `components/HrPageShell.jsx` | 55 | Header chrome + back-link, NO sidebar (pre-V2) |
| Login | `pages/HrLogin.jsx` | — | HR portal login |
| Auth helper | `lib/hrAuth.js` | — | localStorage token + user storage |
| Sub-pages | `pages/Hr*.jsx` | × 17 | All consume `HrPageShell` or roll their own chrome |

### 17 HR sub-pages

1. HrChangePassword
2. HrDailyReports
3. HrDriverQualificationDashboard
4. HrDriverQualificationImport
5. HrEmployeeAccountability
6. HrEmployeeAccountabilityTimeline
7. HrEmployees
8. HrFieldLeadership
9. HrFieldLeadershipUsers
10. HrForgotPassword
11. HrHub
12. HrIncidents
13. HrLogin
14. HrPayrollVariance
15. HrResetPassword
16. HrSafetyRecords
17. HrTimeOff / HrTimeVerification / HrTrainingRecords

## III. Auth & RBAC posture (🟢 VERIFIED)

| Question | Answer |
|---|---|
| HR token name | `masci.hr.token` (localStorage) |
| HR header | `X-HR-Token` |
| Endpoint namespace | `/api/hr/*` (HR-token gated) |
| Any HR page calling `/api/admin/*` | **No** (zero hits across all 17 pages — re-confirmed today) |
| Any HR page importing a shared admin panel known to hardcode `/api/admin/*` | **No** — HR uses purpose-built HR pages, not shared admin panels |
| Risk of the iter437 P0 PM-leak recurring in HR | **None** — HR was never wired into the offending shared panels |

**Net:** HR is the cleanest non-Admin portal from an auth-routing
perspective. The remaining IV-BETA.3B work is UX governance only.

## IV. Current navigation pattern (🟢 VERIFIED)

| Surface | Pattern |
|---|---|
| Hub | 15-tile grid grouped into 4 sections (`TILE_GROUPS`) by iter317-C |
| Sub-pages | NO sidebar — `HrPageShell` renders only a back-link to `/hr` |
| Mobile | Tile grid collapses to single column; header collapses correctly |

This is functional but lacks the **cross-portal consistency** the PM
portal now has (PM has both V1 SECTIONS legacy and V2 domain-grouped
sidebars). HR users have to navigate via the hub on every sub-page.

## V. Hub-tile current state (🟢 VERIFIED)

15 tiles in 4 groups:

- **Primary HR Actions** (4): Employee Lifecycle · Tasks & Actions · Document Expirations · Time Off
- **Compliance & Accountability** (5): FL Records · FL Portal Accounts · Employee Accountability · Driver Qualification · Safety Records
- **Payroll / Time** (5): PO Requests · Time Verification · Payroll Variance · Training Records · Daily Reports
- **Integrations & Systems** (1): Training Center

Strengths:
- Already grouped (iter317-C)
- Per-tile left-edge stripe (`border-l-4`)
- Tile order within groups preserved for muscle memory

Weaknesses:
- **Tile sublines too verbose** (15-25 words each — violates
  CROSS_PORTAL_COACHING_STANDARD.md §V 14-word budget)
- **9 distinct stripe colors** in use (border-l-emerald, amber, rose,
  indigo, blue, purple, cyan, red, plus muted) — exceeds
  VISUAL_LOUDNESS_REDUCTION_PLAN.md §I.2 dominant-hue budget
- Per-tile button colors mirror the stripe (e.g.,
  `bg-emerald-700`, `bg-rose-700`, `bg-purple-700`, `bg-red-700`,
  `bg-cyan-700`, `bg-blue-700`) — same loudness violation
- Two tiles (PO Requests, Daily Reports) overlap with PM/Admin
  surfaces without coaching that calls out the cross-portal context

## VI. Loudness baseline (🟢 VERIFIED · light scan)

- **Distinct accent hues**: 9 (target per loudness doctrine: ≤4)
- **CTAs above the fold**: ~14 tiles × 1 button each + 6 header
  controls = ~20 clickables (PM hub V2 post-re-tier is ~12)
- **Subline length**: avg 19 words / max 27 (target ≤14)
- **Notification markers**: none today (no badge pills)
- **Typography combinations**: 4 distinct sizes × weights in tiles —
  acceptable

**Net loudness verdict**: 🟡 borderline — needs tile-stripe
consolidation and subline trimming to fully conform.

## VII. Mobile / iPad posture (🟡 ASSUMED · spot-checked)

- HR Hub tile grid → `grid-cols-1 sm:grid-cols-2` (good)
- HrPageShell header collapses correctly at <sm breakpoint
- No horizontal-scroll detected at 375 / 768 / 1024 widths in the
  iter437 smoke screenshot

## VIII. Communication posture (🟢 VERIFIED)

HR receives the same PO digest the PM portal does (now via
`build_digest_subject` per IV-BETA.3A). HR-specific transactional
emails (password reset, FL-user welcome) are governed by the
`render_portal_email_fn` helper; no HR-only render path bypasses
the shared chrome.

## IX. Governance script applicability today (🟢 VERIFIED)

| Script | Applies to HR today? | Notes |
|---|---|---|
| `verify_coaching_sublines.py` | NO (scans only PM + Admin governed sidebars) | Will extend in IV-BETA.3B governance script step |
| `verify_admin_copy.py` | YES (scans all of frontend/src/) — already flagged a few HR drifts (e.g., "unlock" in lib/i18n.js) | Already includes HR |
| `measure_visual_loudness.py` | YES if passed an HR route | Will add `/hr` to pre_deploy_check.sh sweep |

## X. What's already done well (🟢)

- HR auth boundary is clean — no `/api/admin/*` exposure
- Tiles are already grouped (iter317-C)
- HR Hub has integration health card, notification bell, global search
- Sign-out wipes all sessions (iter179 P0 contract honoured)
- Mobile header collapse pattern (iter203)

## XI. What needs IV-BETA.3B alignment (planned)

1. **Sidebar V2** behind `?hrSidebarV2=1` — domain-grouped, mirrors PM
2. **Coaching sublines** trimmed to ≤14 words, sentence case, end-with-period
3. **Tile-stripe palette** consolidated to ≤4 dominant hues
4. **Communication doctrine** confirmed compliant (already in §VIII)
5. **Mobile/iPad** verified by Playwright at desktop + ipad + mobile viewports
6. **Playwright regression** locking the contracts above
7. **Governance script** extension (verify_coaching_sublines to include HR)

## XII. Constraints reaffirmed for IV-BETA.3B

- ✅ NO HR backend rewrites
- ✅ NO payroll logic changes
- ✅ NO permission changes
- ✅ NO employee-data schema changes
- ✅ NO production deploy
- ✅ Sidebar V2 ships behind `?hrSidebarV2=1` — legacy renders unchanged
- ✅ Every change regression-locked
