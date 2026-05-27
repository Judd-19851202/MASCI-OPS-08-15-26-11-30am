# Safety Portal — Current State Audit

*Phase IV-BETA.4C · iter437 · 2026-02-27*
*Status: 🟢 INVENTORY COMPLETE · IMPLEMENTATION NOT STARTED*

> **Verification legend:** 🟢 VERIFIED · 🟡 ASSUMED · ⚪ UNTESTED

---

## I. Surface inventory (🟢 VERIFIED · grep + ls)

### Pages (25)
- `SafetyLogin.jsx`, `SafetyForgotPassword.jsx`, `SafetyResetPassword.jsx`,
  `SafetyChangePassword.jsx` (auth)
- `SafetyHub.jsx` (464 LOC · 14 tiles)
- `SafetyDocuments.jsx`, `SafetyDocumentsLibrary.jsx`
- `SafetyEmployees.jsx`, `SafetyEmployeeProfiles.jsx`, `SafetyEmployeeProfileDetail.jsx`
- `SafetyIncidents.jsx` (185 LOC)
- `SafetyCorrectiveActions.jsx` (766 LOC)
- `SafetyAudits.jsx`
- `SafetyTrainingCertifications.jsx`
- `NewSafetyEquipmentForm.jsx`, `NewSafetyOnboarding.jsx`
- (+ a handful of supporting profile/detail screens)

### Shell · `components/SafetyShell.jsx` (95 LOC)

- Header chrome with `cyan-700` accent stripe
- 1-row top-nav with text links (no domain grouping)
- Mobile menu via dropdown
- No V2 sidebar (pre-governance)

### Routes (30 in `App.js`)

`path="/safety-portal/*"` namespace. All routes gated by `SF()` (a
`<RequireSafety>` wrapper). Auth-routing audit (this iteration) confirms
**zero `/api/admin/*` calls** in Safety pages — Safety is auth-clean.

## II. Token / API posture (🟢 VERIFIED)

| Question | Answer |
|---|---|
| Safety token | `masci.safety.token` (localStorage) |
| Header | `X-Safety-Token` |
| Endpoint namespace | `/api/safety-portal/*` + read-only cross-portal (`/api/employees`, `/api/safety-documents`) |
| Pages calling `/api/admin/*` | **0** |
| Pages importing shared admin panels | **0** |
| iter437 P0 leak risk | **None** |

Safety is the **third clean portal** (after HR and Dispatch) from an
auth-routing perspective.

## III. Navigation pattern today (🟢)

| Surface | Pattern |
|---|---|
| Hub | 14 tiles in **NO formal groups** (informal cluster by usage), each with stripe + button |
| Sub-pages | `SafetyShell` chrome only; no sidebar |
| Mobile | Hamburger nav dropdown |

This is the **least V2-aligned portal** today. Compared to PM/HR V2
(domain-grouped sidebar, calm chrome, coaching sublines), Safety still
operates on the iter317-era flat-tile pattern.

## IV. Visual signal inventory (🟢 raw grep counts)

- **Distinct hue families** across Safety pages: **9** (amber, blue,
  cyan, emerald, indigo, purple, red, sky, violet) — same count as
  pre-trim HR Hub, well over the ≤4 doctrine target.
- **Total `bg-*` colour hits across Safety/*.jsx**: **144**.
- **Most frequent**: `bg-cyan-700` (29×), `bg-cyan-800` (20×),
  `bg-red-700` (13×), `bg-emerald-700` (7×), `bg-amber-700` (4×).
- **`bg-red-*` total**: 13 (red-100) + 13 (red-700) + 7 (red-800) +
  5 (red-600) + 2 (red-200) + 2 (red-900) = **42 red occurrences**.
  This is high; a Safety surface should reserve red for genuine
  immediate danger.
- **Forbidden urgency words** ("URGENT", "ASAP", "Please click",
  "CRITICAL") in Safety/*.jsx: **0** (well-disciplined verbiage).

## V. Page-by-page concern (🟢 spot-checked)

| Page | LOC | Concern |
|---|---|---|
| `SafetyHub.jsx` | 464 | 14 tiles, mixed stripes, multiple button colour families. **Highest visual load** of any page on the platform today. |
| `SafetyCorrectiveActions.jsx` | 766 | Heavy table + filter UI. Severity pills present but pattern unverified against doctrine A.III tiers. |
| `SafetyIncidents.jsx` | 185 | Already disciplined: `SEV_PILL` table + clean filter row. Best-in-class Safety page today. |
| `SafetyAudits.jsx` | ? | Pre-V2 chrome; no domain grouping. |

## VI. Notable strengths (🟢 preserve)

- **Severity pill discipline** in `SafetyIncidents.jsx` — colour bound
  to data, not theme.
- **Read-only review framing** of the Incidents page — operator
  expectation already calibrated to "scan, don't edit".
- **Auth posture is clean** — no leak risk.
- **Operator language is mature** — zero forbidden urgency words found
  on first scan.

## VII. Notable gaps (🟡 these are the IV-BETA.4-impl targets)

- No V2 sidebar — operators reach all 14 tiles via the hub on every
  navigation.
- 9-hue palette is double the doctrine target.
- 42 red occurrences dilute escalation seriousness ("if everything is
  red, nothing is").
- No domain map — domains are implied by tile clusters, not formalised.
- No coaching sublines per doctrine §V (≤14 words, sentence case).

## VIII. Implementation NOT started (per directive)

This document is the **inventory baseline**. No Safety code was
modified this iteration. The implementation order is laid out in
`SAFETY_GOVERNANCE_PREPARATION.md §IV`.

## IX. Doctrine reaffirmed

- ✅ Preview only · NO production touches
- ✅ NO Safety workflow rewrites · NO incident/compliance logic changes
- ✅ NO auth changes · NO permission changes
- ✅ NO notification engine changes
- ✅ This audit only inventories; it does not redesign
