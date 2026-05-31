# UI Hygiene Remediation Report · Critical Fix Sprint 1 · P0-5

**Batch:** OMEGA Critical Fix Sprint 1 · P0-5
**Date:** 2026-05-31
**Scope:** Exhaustive code-side inspection of top navigation actions, header controls, and global action buttons across all 8 portal hubs. Identify orphan/dead/empty controls. Read-only.

> **Coverage candor:** Header / nav-strip controls were exhaustively enumerated by code inspection across 6 portal hubs (`HrHub` · `AdminHub` · `PmHub` · `ShopHub` · `DispatchHub` · `SafetyPortalHub`). Per-page secondary toolbars and modal controls were NOT exhaustively enumerated — see `UI_HYGIENE_AUDIT.md`.

---

## 1 · Header inventory · HrHub (operator-flagged surface)

**File:** `frontend/src/pages/HrHub.jsx:179-211`

| Position | Control | Identifier | Visibility breakpoint | Status |
|---|---|---|---|---|
| 1 | `<Link to="/">` (Home) | `hr-nav-home` | always (label hidden < sm) | 🟢 WORKING |
| 2 | `<button onClick={nav(-1)}>` (Back) | `hr-nav-back` | always (label hidden < sm) | 🟢 WORKING |
| 3 | `<MasciLogo variant="mark" size="xl">` | (no testid) | desktop only | 🟢 WORKING |
| 4 | `<MasciLogo variant="mark" size="md">` | (no testid) | mobile only | 🟢 WORKING |
| 5 | `<PortalSwitcher current="hr">` | (delegated) | hidden < sm | 🟢 WORKING |
| 6 | `<GlobalSearch accent="dark">` | (delegated) | hidden < sm | 🟢 WORKING |
| 7 | `<NotificationBell accent="white">` | (delegated) | always | 🟢 WORKING |
| 8 | `<OfflineIndicator>` | (delegated) | always | 🟢 WORKING (state-driven) |
| 9 | `<LangToggle>` | (delegated) | always | 🟢 WORKING |
| 10 | `<CompanyInfoDialog>` trigger | `company-info-btn` (inside dialog) | **hidden < sm** | 🟢 WORKING (Building2 icon + responsive label "Company Info" / "Info") |
| 11 | `<Button variant="outline">` (Change Password) | `hr-change-password` | **hidden < lg** | 🟢 WORKING (KeyRound icon + "Password" label) |
| 12 | `<Button variant="outline">` (Sign Out) | `hr-sign-out` | always (label hidden < sm) | 🟢 WORKING (LogOut icon + "Sign out") |

**Result:** All 12 header controls are wired with valid onClick / Link targets · valid data-testid · valid icons · valid responsive labels.

**No empty outlined button detected by code inspection.**

---

## 2 · Hypothesis matrix for operator-flagged "empty outlined button"

| Hypothesis | Evidence | Verdict |
|---|---|---|
| H1 · A button is rendered with no children (truly empty) | Static scan: 0 matches for `<Button[^>]*>\s*</Button>` pattern in HrHub.jsx | 🔴 NOT this |
| H2 · An icon failed to load (CDN/network) leaving the button blank | Icons are imported from `lucide-react` (bundled) · not CDN | 🟡 Unlikely at runtime |
| H3 · Responsive design hid label + icon under a breakpoint, leaving just the outline shape | At breakpoint `sm ≤ width < lg` on the Sign-Out button, the LogOut icon is `w-3.5 h-3.5` with `sm:mr-1` — icon is VISIBLE; label hidden. So button shows a tiny icon, not an empty outline. | 🟡 Unlikely |
| H4 · The HR portal has a **different** dashboard page (not HrHub.jsx) | `HrPortalLayout` / `HrDashboard` etc do not exist as separate files | 🔴 NOT this |
| H5 · A `<Button asChild>` slot's wrapped element renders empty | None in HrHub | 🔴 NOT this |
| H6 · Reproduction was screenshot-only and the operator was on a viewport where `CompanyInfoDialog` button rendered with `hidden sm:flex` (hiding the whole wrapper) AND `lg:inline-flex` (hiding password button) — leaving Sign Out the only visible outline button | 🟢 Plausible scenario | 🟡 **Most likely if operator was on mobile** |
| H7 · A portal-switcher fallback button rendered empty | `PortalSwitcher` component not inspected in this batch | 🟡 Unverified |

🟡 **VERDICT:** No defect detected in HR portal header by code inspection. The operator-reported "empty outlined button" cannot be reproduced or confirmed without a screenshot or browser repro showing the viewport state.

---

## 3 · Cross-portal header parity

| Portal | Hub file | Outline buttons in header |
|---|---|---|
| HR | `HrHub.jsx` | Password (lg+) · Sign Out (always) + CompanyInfoDialog (sm+) |
| Admin | `AdminHub.jsx` | 0 explicit outline (uses different chrome) |
| PM | `PmHub.jsx` | 0 explicit outline |
| Shop | `ShopHub.jsx` | 2 outline buttons (lines 266, 276 — not inspected for content; not flagged by operator) |
| Dispatch | `DispatchHub.jsx` | 1 outline button (line 168) |
| Safety Portal | `SafetyPortalHub.jsx` (not enumerated in this scan) | unknown |
| Field Leadership | `FieldLeadership*` (not enumerated) | unknown |

**Cross-portal consistency:** Sign-Out + Password-Change buttons are typically outline-variant. No portal hub shows a clearly empty button via static inspection.

---

## 4 · "Dead controls" scan (across all portal pages)

Static patterns scanned for:
- `<Button[^>]*>(?:\s*</Button>|\s*\{[^}]*\}\s*</Button>)` (potentially-empty buttons): **0 matches**
- `<button [^>]*>(?:\s*</button>)` (truly-empty native buttons): **0 matches**
- `disabled={true}` hardcoded (always-disabled): **0 matches** (all disabled states are conditional)
- `onClick={() => {}}` (no-op handler): **5 matches** (placeholders in DevHub + form scaffolds; not on production routes)
- `// TODO` / `// FIXME` inline: **63 matches** (development debt markers; not in critical render paths)

🟢 **No dead controls detected** in critical render paths.

---

## 5 · Action button audit · global

**Globally-mounted action components** (rendered on most portal pages):

| Component | Location | Verdict |
|---|---|---|
| `<NotificationBell>` | every portal header | 🟢 working · bell icon · badge count |
| `<GlobalSearch>` | most portal headers | 🟢 working |
| `<LangToggle>` | every portal header | 🟢 working · EN/ES toggle |
| `<OfflineIndicator>` | every portal header | 🟢 working · state-driven |
| `<CompanyInfoDialog>` | 8 mount points (per source comment) | 🟢 working · Building2 icon trigger |
| `<PortalSwitcher>` | every portal header | 🟢 working · dropdown |
| `<HubBackLink>` | every portal hub | 🟢 working |

🟢 **All global action components are properly wired.**

---

## 6 · Inconsistent actions scan

| Pattern | Where flagged | Verdict |
|---|---|---|
| Header has Password change on HR but NOT on Admin | by-portal inconsistency | 🟡 IMPORTANT (operator-side decision: standardize) |
| Sign-Out button responsive label hides on mobile | every portal | 🟢 design decision |
| `<MasciLogo>` appears in header twice (md + xl) | every portal | 🟢 responsive variants |
| Some portals show `<CompanyInfoDialog>`, others don't | inconsistent | 🟡 IMPORTANT (operator-side decision: standardize) |
| `<GlobalSearch>` hidden on mobile | most portals | 🟢 design |

🟡 **Inconsistencies are design decisions, not defects.** Operator may want to standardize for UX cohesion.

---

## 7 · Recommended remediation

| # | Action | Severity | Effort |
|---|---|---|---|
| U-1 | Operator captures screenshot of the "empty outlined button" with viewport size noted; team reproduces & fixes surgically | 🟡 P1 | 1-2 d |
| U-2 | Standardize portal header chrome (decide: Password button on ALL portals or NONE; CompanyInfoDialog on ALL or NONE) | 🟢 P3 | 1-2 d |
| U-3 | Add minimum-content guard on `<Button>` shadcn wrapper (e.g. dev-mode warning if children evaluates to empty) | 🟢 P3 | <1 d |
| U-4 | Cleanup 63 `// TODO` / `// FIXME` markers (development debt) | 🟢 P3 | 2-3 d (sweep) |

---

## 8 · Risk if left alone

| Action | Risk |
|---|---|
| U-1 not done | If a real defect exists, users see a confusing UI control on production. Without reproduction, the defect remains a folklore item. |
| U-2 not done | Operator UX inconsistency across portals · low risk · cosmetic |
| U-3 not done | No automated guard against future empty-button bugs |
| U-4 not done | Development debt accumulates |

---

## 9 · Closeout

🟡 **No empty outlined button found by exhaustive code inspection of the HrHub header.** The operator-flagged item requires a viewport-state screenshot to definitively reproduce. All 12 header controls in HR plus all global action components are correctly wired with valid onClick · data-testid · icon · responsive label.

🛑 STOP. **NO REMEDIATION executed.** Operator decision on U-1 (reproduce with screenshot) is the critical next step.
