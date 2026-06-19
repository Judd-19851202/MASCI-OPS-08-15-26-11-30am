# TRACK 15.33 — MOBILE & CROSS-BROWSER CERTIFICATION RUNBOOK (HUMAN QA)

**Status:** Pending — to be executed by a human QA tester on real devices.
**Purpose:** Close the device-coverage gap left open by `TRACK_15_33_PRODUCTION_OPERATIONAL_CERTIFICATION.md`.
**Estimated time:** 90 minutes (one tester, two devices + Edge).

> "Real workflows. Real users. Real devices. Real production environment."
> This runbook is the authoritative source of truth for the mobile / tablet / cross-browser tier of TRACK 15.33. Do not mark TRACK 15.33 complete until this is signed off.

---

## 1 · DEVICE / VIEWPORT MATRIX

| # | Device | Browser | Viewport | Test scope |
|---|---|---|---|---|
| 1 | Desktop | Chrome (latest) | 1920×1080 | All portals · all workflows |
| 2 | Desktop | Microsoft Edge (latest) | 1920×1080 | All portals · all workflows |
| 3 | iPhone (latest iOS) | Safari | portrait | All portals · public submission |
| 4 | iPhone (latest iOS) | Safari | landscape | Same |
| 5 | iPad (latest iPadOS) | Safari | portrait | Field Leadership · public submission · PM bell |
| 6 | iPad (latest iPadOS) | Safari | landscape | Same |

Each row produces a screenshot folder named `15_33_<device>_<browser>_<orientation>/`.

---

## 2 · TEST CREDENTIALS

Use `/app/memory/test_credentials.md` as the source. The relevant accounts for this runbook:

| Portal | Email | Password |
|---|---|---|
| Super-admin (all portals) | `jaymn.judd@mascigc.com` | `Maddix123!` |
| Cert mechanic (shop) | `cert.mechanic@mascicert.local` | `CertProof2026!` |
| Real PM (project-scoped) | `davidjewett@mascigc.com` | (see test_credentials.md) |

For HR / Safety / Dispatch / FL, the super-admin's multi-login issues a token to every portal; use those flows.

---

## 3 · WORKFLOW MATRIX

For every (device × portal × workflow) combination, classify GREEN / YELLOW / RED per the rubric in §4. Submission flows must be exercised end-to-end (form fill → submit → confirmation → revisit).

### 3.1 Admin
1. Sign in via `/sign-in` (multi-login).
2. Land on Admin home; verify dashboard cards visible.
3. Open `/admin/employees` (employee lookup) — search returns rows.
4. Open `/admin/projects` (project lookup) — search returns rows.
5. Open a project; verify team-assignment panel loads.
6. Open notifications bell (header); verify ≥1 row renders.
7. Sign out (top-right menu).

### 3.2 PM
1. Sign in via `/pm-login` (or multi-login).
2. Open assigned project from the home list.
3. Open Team roster.
4. Open Notifications bell · expect project-scoped rows only.
5. Open RFI area.
6. Open Submittal area.
7. Sign out.

### 3.3 HR
1. Sign in.
2. Open Employee roster · scroll one page.
3. Create a sandbox employee (use suffix `+QA-15-33`).
4. Reset that employee's password.
5. Disable that employee · confirm `disabled=true` in roster filter.
6. Re-enable · confirm `disabled=false`.
7. Sign out.

### 3.4 Safety
1. Sign in.
2. Open Safety dashboard.
3. Create one safety meeting (sandbox project).
4. Create one JHA against the sandbox project.
5. Open Notifications bell · ≥1 row renders.
6. Sign out.

### 3.5 Shop
1. Sign in.
2. Open Work queue.
3. Open Equipment lookup · open one asset.
4. (Manager only) Open Manager queue.
5. Sign out.

### 3.6 Dispatch
1. Sign in.
2. Open Dispatch board.
3. Assign one asset to a project.
4. Update one status (e.g. arrived).
5. Sign out.

### 3.7 Field Leadership
1. Sign in.
2. Submit one Daily report (sandbox project).
3. Submit one QA/QC.
4. Submit one JHA.
5. Verify confirmation page renders.
6. Sign out.

### 3.8 Public Submission
1. Open `/public/daily-report` (no auth).
2. Submit one daily report.
3. Verify confirmation banner + email/SMS receipt (if configured).
4. Repeat for `/public/qaqc`, `/public/jha`, `/public/safety-meeting`.
5. Re-open the confirmation URL on a different device · expect read-only view.

---

## 4 · CLASSIFICATION RUBRIC

For each cell of (device × workflow):

| Tag | Meaning |
|---|---|
| 🟢 GREEN | Workflow completes within ≤ 3 attempts · no clipping · no keyboard overlap · no infinite spinner · confirmation reproducible |
| 🟡 YELLOW | Workflow completes but has a documented usability concern (touch target < 44 px · text wraps awkwardly · soft-keyboard pushes submit off-screen but scroll recovers) |
| 🔴 RED | Workflow does NOT complete · OR data loss · OR white screen · OR token mid-flow lost · OR navigation broken |

Any RED is an automatic certification failure for that device tier. Document with:
- Exact URL
- Exact device + iOS/Edge version
- Step that failed
- Screenshot of the failure state
- Backend response if visible (Network tab)

---

## 5 · STOP-CONDITIONS (re-stated for the tester)

The certification immediately fails for the affected device tier if ANY of these surface:

- Login impossible
- Form submission impossible
- Data loss
- White screen
- Infinite spinner > 30 s
- Mobile clipping that hides a primary CTA
- Keyboard overlap that prevents form completion
- Broken navigation (a portal link in the sign-in card 404s)
- Unrecoverable errors (cannot get back to a working state without clearing site data)

Do not attempt to fix. Document and return for engineering follow-up.

---

## 6 · OUTPUT FORMAT

For each device row in §1, the tester produces:

1. A folder `15_33_<device>_<browser>_<orientation>/` with one screenshot per workflow step + one screenshot per failure.
2. A row in this table:

| Device | Browser | Orientation | Admin | PM | HR | Safety | Shop | Dispatch | FL | Public | Stop-conditions hit? |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Desktop | Chrome | landscape | | | | | | | | | |
| Desktop | Edge | landscape | | | | | | | | | |
| iPhone | Safari | portrait | | | | | | | | | |
| iPhone | Safari | landscape | | | | | | | | | |
| iPad | Safari | portrait | | | | | | | | | |
| iPad | Safari | landscape | | | | | | | | | |

3. A short "what would block 5:30 AM tomorrow?" paragraph per device row.

---

## 7 · SIGN-OFF

Once the matrix above is fully populated with no REDs (or every RED has an accepted-and-deferred ticket), the tester writes:

```
Track 15.33 mobile certification — signed off by: <name>, <date>.
Device matrix: 6/6 GREEN (or 5/6 GREEN + 1 deferred with ticket #).
Field crews cleared for mobile use starting <date>.
```

Append the sign-off to `/app/memory/CHANGELOG.md` and update the Five-Pillar `Proven` score in `TRACK_15_33_PRODUCTION_OPERATIONAL_CERTIFICATION.md` from 7 → 9.

---

## 8 · WHY THIS IS A RUNBOOK, NOT A CODE TEST

iOS Safari, Edge, and real-device keyboards have behaviors that **cannot be reproduced inside a Playwright/Chromium engineering pod**:
- iOS keyboard pushes the entire viewport up; Playwright doesn't simulate this.
- Edge has subtle CSS quirks (especially around `position: sticky` and `aspect-ratio`) that Chromium passes silently.
- Real touch event timing differs from emulated clicks.
- Network jitter under cellular conditions exposes loading states that LAN-grade Playwright never sees.

That is why TRACK 15.33 was deliberately scoped as **API + desktop + this runbook** rather than a fake one-shot screenshot pass. The runbook is the authoritative real-device tier.

— END · TRACK 15.33 mobile / cross-browser certification runbook —
