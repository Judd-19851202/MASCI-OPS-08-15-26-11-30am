# WP16 Wave 1 Approval Evidence

Date: 2026-07-30  
Wave: Wave 1 — Public Pages & Authentication  
Current status: **TECHNICALLY VERIFIED — PENDING EXECUTIVE APPROVAL**

## Compact executive sign-off checklist

- [x] Scope reconciled and denominator fixed
- [x] All 9 logged Wave 1 defects reconciled and closed
- [x] No open Wave 1 punch-list defects remain
- [x] Frontend repaired behaviors verified: `9/9`
- [x] Backend authentication checks verified: `10/10`
- [x] Live reset flows verified: PM, HR, Shop, Safety, Dispatch
- [x] Shared-file changes explained and drift-controlled
- [x] Known limitations and exclusions stated explicitly
- [ ] Executive approval granted
- [ ] Wave 1 locked
- [ ] Wave 2 authorized

---

## 1. Scope reconciliation

### Final Wave 1 denominator
- Active routes inspected: **30**
- Legacy / unrouted pages inspected: **1**
- Embedded dialogs inspected: **5**
- Primary workflows inspected: **13**
- Dynamic / parameterized routes inspected: **5**
- Error / expired-token / unauthorized / session-continuity state groups inspected: **6**
- Logout state groups inspected as Wave 1 route surfaces: **0**

### Active route denominator
1. `/`
2. `/sign-in`
3. `/change-password`
4. `/access-denied`
5. `/legal/terms`
6. `/legal/privacy`
7. `/admin/login`
8. `/pm/login`
9. `/pm/reset/:token`
10. `/pm/change-password`
11. `/hr/login`
12. `/hr/forgot`
13. `/hr/reset/:token`
14. `/hr/change-password`
15. `/safety/forms/login`
16. `/safety-portal/login`
17. `/safety-portal/forgot-password`
18. `/safety-portal/reset/:token`
19. `/safety-portal/change-password`
20. `/dispatch-portal/login`
21. `/dispatch-portal/forgot-password`
22. `/dispatch-portal/reset/:token`
23. `/dispatch-portal/change-password`
24. `/shop/login`
25. `/shop/reset/:token`
26. `/shop/change-password`
27. `/field-leadership/portal/login`
28. `/field-leadership/portal/change-password`
29. `/leadership/login`
30. `/dev/login`

### Legacy / unrouted page inspected
- `frontend/src/pages/LeadershipLogin.jsx` — inspected and retained outside the active-route denominator because `AppRoutes.jsx` does not route users to this file.

### Embedded dialogs inspected
1. `CompanyInfoDialog` on `/`
2. PM forgot-password dialog on `/pm/login`
3. HR forgot-password dialog on `/hr/login`
4. Shop forgot-password dialog on `/shop/login`
5. Field Leadership forgot-password dialog on `/field-leadership/portal/login` and `/leadership/login`

### Primary workflows inspected
1. Public hub navigation
2. Multi-portal sign-in
3. Shared directory password change
4. Access denied / recovery
5. Admin login existing-session path
6. PM auth lifecycle
7. HR auth lifecycle
8. Safety Forms remembered-session gate
9. Safety auth lifecycle
10. Dispatch auth lifecycle
11. Shop auth lifecycle
12. Field Leadership auth lifecycle
13. Developer login disabled-state truth path

### Dynamic / parameterized routes inspected
- `/pm/reset/:token`
- `/hr/reset/:token`
- `/shop/reset/:token`
- `/safety-portal/reset/:token`
- `/dispatch-portal/reset/:token`

### Error / special state groups inspected
1. Unauthorized state: `/access-denied`
2. Existing-session continuity: `/admin/login`
3. Failed-login continuity: `/field-leadership/portal/login` and `/leadership/login`
4. Remembered-session continuity: `/safety/forms/login`
5. Preview-disabled backend state: `/dev/login`
6. Invalid / expired reset-token state: PM reset second-attempt evidence after token consumption

### Exclusions
- **Standalone logout route / screen:** excluded because Wave 1 contains no dedicated logout route or logout screen. Logout controls exist on downstream authenticated portal shells, not in the Wave 1 active-route denominator.
- **`frontend/src/pages/LeadershipLogin.jsx`:** excluded from active-route certification because it is an inventoried legacy file, not an active routed surface.
- **Production email inbox delivery:** excluded from direct verification in this package because verification was performed in Preview and real production mail delivery is integration-environment dependent.

---

## 2. Seven-Gate results

Use of statuses below is restricted to: `Verified`, `Not Applicable`, `Blocked`, `Pending Executive Approval`.

| Active Wave 1 page | Visual | Functional | Operational | Human Readability | Data Truth | Responsive | Executive Approval |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `/` | Verified | Verified | Verified | Verified | Not Applicable | Verified | Pending Executive Approval |
| `/sign-in` | Verified | Verified | Verified | Verified | Verified | Verified | Pending Executive Approval |
| `/change-password` | Verified | Verified | Verified | Verified | Not Applicable | Verified | Pending Executive Approval |
| `/access-denied` | Verified | Verified | Verified | Verified | Not Applicable | Verified | Pending Executive Approval |
| `/legal/terms` | Verified | Verified | Verified | Verified | Not Applicable | Verified | Pending Executive Approval |
| `/legal/privacy` | Verified | Verified | Verified | Verified | Not Applicable | Verified | Pending Executive Approval |
| `/admin/login` | Verified | Verified | Verified | Verified | Verified | Verified | Pending Executive Approval |
| `/pm/login` | Verified | Verified | Verified | Verified | Verified | Verified | Pending Executive Approval |
| `/pm/reset/:token` | Verified | Verified | Verified | Verified | Verified | Verified | Pending Executive Approval |
| `/pm/change-password` | Verified | Verified | Verified | Verified | Not Applicable | Verified | Pending Executive Approval |
| `/hr/login` | Verified | Verified | Verified | Verified | Verified | Verified | Pending Executive Approval |
| `/hr/forgot` | Not Applicable | Verified | Verified | Not Applicable | Verified | Not Applicable | Pending Executive Approval |
| `/hr/reset/:token` | Verified | Verified | Verified | Verified | Verified | Verified | Pending Executive Approval |
| `/hr/change-password` | Verified | Verified | Verified | Verified | Not Applicable | Verified | Pending Executive Approval |
| `/safety/forms/login` | Verified | Verified | Verified | Verified | Verified | Verified | Pending Executive Approval |
| `/safety-portal/login` | Verified | Verified | Verified | Verified | Verified | Verified | Pending Executive Approval |
| `/safety-portal/forgot-password` | Verified | Verified | Verified | Verified | Verified | Verified | Pending Executive Approval |
| `/safety-portal/reset/:token` | Verified | Verified | Verified | Verified | Verified | Verified | Pending Executive Approval |
| `/safety-portal/change-password` | Verified | Verified | Verified | Verified | Not Applicable | Verified | Pending Executive Approval |
| `/dispatch-portal/login` | Verified | Verified | Verified | Verified | Verified | Verified | Pending Executive Approval |
| `/dispatch-portal/forgot-password` | Verified | Verified | Verified | Verified | Verified | Verified | Pending Executive Approval |
| `/dispatch-portal/reset/:token` | Verified | Verified | Verified | Verified | Verified | Verified | Pending Executive Approval |
| `/dispatch-portal/change-password` | Verified | Verified | Verified | Verified | Not Applicable | Verified | Pending Executive Approval |
| `/shop/login` | Verified | Verified | Verified | Verified | Verified | Verified | Pending Executive Approval |
| `/shop/reset/:token` | Verified | Verified | Verified | Verified | Verified | Verified | Pending Executive Approval |
| `/shop/change-password` | Verified | Verified | Verified | Verified | Not Applicable | Verified | Pending Executive Approval |
| `/field-leadership/portal/login` | Verified | Verified | Verified | Verified | Verified | Verified | Pending Executive Approval |
| `/field-leadership/portal/change-password` | Verified | Verified | Verified | Verified | Not Applicable | Verified | Pending Executive Approval |
| `/leadership/login` | Verified | Verified | Verified | Verified | Verified | Verified | Pending Executive Approval |
| `/dev/login` | Verified | Verified | Verified | Verified | Verified | Verified | Pending Executive Approval |

Gate interpretation note:
- `Executive Approval` remains pending for every active route by instruction.
- No active Wave 1 route is currently marked `Blocked`.

---

## 3. Defect closure reconciliation

### Mathematical reconciliation
- Original defect count opened: **9**
- Repaired count: **9**
- Closed count: **9**
- Remaining open count: **0**

Reconciliation equation: `9 opened = 9 repaired = 9 closed + 0 remaining`

| Issue ID | Original severity | Page / route | Root cause | Smallest-safe repair | Verification performed | Final status |
| --- | --- | --- | --- | --- | --- | --- |
| `WP16-W1-001` | Medium | `/change-password` | Legacy directory change-password page bypassed canonical auth chrome | Wrapped existing form in frozen auth shell only | Playwright verified canonical shell restored | Verified |
| `WP16-W1-002` | Medium | `/field-leadership/portal/change-password` | Legacy Field Leadership change-password page bypassed canonical auth chrome | Wrapped existing form in canonical auth shell without changing flow | Playwright verified canonical shell restored | Verified |
| `WP16-W1-003` | High | `/safety/forms/login` | Remembered Safety Forms token was being cleared on revisit | Preserved only Safety Forms token on its own login route while still clearing unrelated sessions | Playwright verified Safety Forms token preserved and admin token cleared | Verified |
| `WP16-W1-004` | High | `/safety-portal/forgot-password` | Preview reset token rendered in operator-facing UI | Removed operator-visible preview token from page UI only | Playwright verified no token visible after submit | Verified |
| `WP16-W1-005` | High | `/dispatch-portal/forgot-password` | Preview reset token rendered in operator-facing UI | Removed operator-visible preview token from page UI only | Playwright verified no token visible after submit | Verified |
| `WP16-W1-006` | High | `/field-leadership/portal/login`, `/leadership/login` | Shared login component cleared sibling tokens before login success | Moved token replacement to post-success path only | Playwright verified failed login no longer wipes active admin session | Verified |
| `WP16-W1-007` | Medium | `/dev/login` | Frontend did not truthfully reflect backend fail-closed preview contract | Converted backend 404 into explicit disabled-state UI | Playwright verified disabled alert and disabled submit | Verified |
| `WP16-W1-008` | Medium | `/admin/login` | Stale `/admin/hub` target plus login-path wipe blocked existing-session auto-elevation | Redirect target changed to `/admin`; valid Admin + Directory session preserved on `/admin/login` long enough for redirect | Playwright verified redirect to `/admin` | Verified |
| `WP16-W1-009` | Medium | `/hr/forgot` | Active redirect route missing from authoritative register | Added route to register and verified runtime redirect | Playwright verified redirect to `/hr/login` | Verified |

---

## 4. Change-control record

### Product-code files modified

| File modified | Why it was modified | Defect authorization | Local or shared | Drift-control confirmation |
| --- | --- | --- | --- | --- |
| `frontend/src/pages/SafetyFormsLogin.jsx` | Removed page-level token wipe conflicting with remembered-session behavior | `WP16-W1-003` | Local | Narrow route-specific repair only |
| `frontend/src/lib/sessionReset.js` | Added optional Safety Forms preservation path used only for the repaired login-route exception | `WP16-W1-003` | Shared | Default behavior preserved; change activates only when explicitly requested |
| `frontend/src/components/EnforcePortalScope.jsx` | Added explicit route guards for Safety Forms remembered-session behavior and Admin existing-session auto-elevation | `WP16-W1-003`, `WP16-W1-008` | Shared | Shared change is pathname-scoped; default platform-wide behavior remains unchanged for all other routes |
| `frontend/src/pages/SafetyForgotPassword.jsx` | Removed operator-visible preview reset token UI | `WP16-W1-004` | Local | No backend, branding, or shared-shell redesign |
| `frontend/src/pages/DispatchForgotPassword.jsx` | Removed operator-visible preview reset token UI | `WP16-W1-005` | Local | No backend, branding, or shared-shell redesign |
| `frontend/src/pages/FieldLeadershipPortalLogin.jsx` | Preserved active session state until login success | `WP16-W1-006` | Local page shared by two routes | Logic changed only in the success boundary; no visual redesign |
| `frontend/src/pages/DirectoryChangePassword.jsx` | Restored canonical auth shell | `WP16-W1-001` | Local | Used frozen `PortalLoginShell`; no new shell design introduced |
| `frontend/src/pages/FieldLeadershipPortalChangePassword.jsx` | Restored canonical auth shell | `WP16-W1-002` | Local | Used frozen `PortalLoginShell`; no new shell design introduced |
| `frontend/src/pages/AdminLogin.jsx` | Corrected existing-session redirect target | `WP16-W1-008` | Local | Single-route behavior repair only |
| `frontend/src/pages/DevLogin.jsx` | Added truthful disabled-state handling for preview 404 | `WP16-W1-007` | Local | No shared auth-shell redesign |

### Control / evidence files modified

| File modified | Why it was modified |
| --- | --- |
| `memory/WP16_CERTIFICATION_REGISTER.csv` | Inventory correction, per-defect status updates, per-route evidence updates |
| `memory/WP16_LIVE_PUNCH_LIST.md` | Authoritative defect logging and closure evidence |
| `memory/WP16_WAVE1_INVENTORY.md` | Baseline Wave 1 inventory record |
| `memory/WP16_WAVE1_COMPLETENESS_RECONCILIATION.md` | Exhaustiveness proof for Wave 1 denominator |
| `memory/WP16_WAVE1_APPROVAL_EVIDENCE.md` | Final executive approval package |
| `memory/PRD.md` | Project memory / status handoff record |
| `auth_testing.md` | Added generic auth testing playbook section used during verification prep |

### Foundation drift statement
- No unrelated foundation redesign occurred.
- No changes were made to `PortalShell`, navigation systems, global tokens, or shared visual language outside the smallest-safe repairs listed above.
- Shared-file changes were route-scoped and additive, not broad rewrites.
- Where a shared file changed, the change was limited by explicit route conditions or explicit function options so non-Wave-1 surfaces retained prior behavior.

---

## 5. Regression evidence

### Frontend repaired behaviors: `9/9`
Verified after repair:
1. `/change-password` canonical shell restored
2. `/field-leadership/portal/change-password` canonical shell restored
3. `/safety/forms/login` remembered session preserved
4. `/safety-portal/forgot-password` token no longer visible
5. `/dispatch-portal/forgot-password` token no longer visible
6. `/field-leadership/portal/login` and `/leadership/login` failed login no longer wipes admin session
7. `/admin/login` existing valid session redirects to `/admin`
8. `/dev/login` shows disabled state on backend 404 and disables submit
9. `/hr/forgot` redirects to `/hr/login`

### Backend authentication checks: `10/10`
- `/api/auth/multi-login`
- `/api/pm/login`
- `/api/hr/login`
- `/api/safety/login`
- `/api/dispatch/login`
- `/api/shop/login`
- `/api/field-leadership/portal/login`
- `/api/safety/forgot-password`
- `/api/dispatch/forgot-password`
- `/api/dev/login` fail-closed `404`

### Live password-reset flows verified
- PM reset route verified with a live preview token and successful progression into the PM portal
- HR reset route verified with a live preview token and successful progression into `/hr`
- Shop reset route verified with a live preview token and successful progression into `/shop`
- Safety reset route verified with a live preview token and successful progression into `/safety-portal`
- Dispatch reset route verified with a live preview token and successful progression into `/dispatch-portal`

### Active-session continuity evidence
- `/admin/login` existing valid Admin + Directory session now survives long enough to auto-elevate to `/admin`
- `/field-leadership/portal/login` and `/leadership/login` no longer wipe active admin session after failed login

### Failed-login behavior evidence
- Field Leadership failed-login path tested with wrong password while a live admin session was present; admin session remained intact after failure

### Remembered-session behavior evidence
- `/safety/forms/login` retest confirmed Safety Forms token persists across revisit while unrelated admin token is still cleared

### Preview-disabled `/dev/login` evidence
- Backend returns `404` by design in Preview
- Frontend now reflects that as an explicit disabled-state alert and disables further submission

### Removal of operator-visible development reset tokens
- Safety forgot-password UI no longer displays preview reset token
- Dispatch forgot-password UI no longer displays preview reset token

### Correct `/admin/login` redirect behavior
- Valid existing Admin + Directory session now redirects to `/admin`, not `/admin/hub`

---

## 6. Visual and responsive evidence

### Repaired visual surfaces — before vs after

| Surface | Before evidence | After evidence | Desktop | iPad / tablet | iPhone / mobile |
| --- | --- | --- | --- | --- | --- |
| `/change-password` | `RESULT::directory_change_password_chrome::FAIL` (`caution=0`, `blueprint=0`, `footer=1`) | `RESULT::directory_change_password_chrome_after_fix::PASS`; responsive checks: `directory_change_password_1920x800`, `1024x768`, `390x844` all `PASS` | Verified | Verified | Verified |
| `/field-leadership/portal/change-password` | `RESULT::fl_change_password_chrome::FAIL` (`caution=0`, `blueprint=0`, `footer=1`) | `RESULT::fl_change_password_chrome_after_fix::PASS`; responsive checks: `fl_change_password_1920x800`, `1024x768`, `390x844` all `PASS` | Verified | Verified | Verified |

### Responsive / interaction confirmations performed
For both repaired visual surfaces, the following were explicitly verified at desktop (`1920x800`), tablet (`1024x768`), and mobile (`390x844`) widths:
- canonical shell present (`caution-stripe`, `blueprint-bg`, footer)
- correct background and page hierarchy preserved
- no raw technical information surfaced in the user-facing layout
- no horizontal overflow (`scrollWidth <= innerWidth`)
- no clipping observed in the primary form content
- vertical scrolling remained available where page height exceeded viewport height
- direct interaction check performed by filling password inputs successfully on each viewport

Interaction note:
- These checks were not screenshot-only; each viewport test included live form input interaction to confirm touch / typing behavior.

---

## 7. Known limitations and exclusions

### Explicit limitations
- **Preview-only verification:** all evidence in this package was gathered in Preview, not Production.
- **Production inbox delivery not directly verified:** PM / HR / Shop / Safety / Dispatch forgot-password email delivery to real inboxes was not verified here.
- **PM / HR / Shop reset-token acquisition method:** live reset-route verification for PM / HR / Shop used preview data token generation rather than inbox retrieval because Preview email delivery evidence is environment-dependent.
- **Safety / Dispatch backend preview payloads:** backend Preview responses still include internal `token_for_dev` fields for internal continuity; the Wave 1 repair removed operator-visible exposure from the UI only.
- **`/dev/login` live vendor auth:** not verified as an active login because the backend is intentionally disabled in Preview; disabled-state truthfulness was verified instead.
- **Standalone logout surface:** not tested because no dedicated logout route belongs to the Wave 1 denominator.
- **Legacy `LeadershipLogin.jsx`:** inspected as an unrouted legacy file but excluded from active-route certification.
- **Fresh 3-breakpoint responsive capture coverage:** explicitly captured in this package for the two repaired visual surfaces; unrepaired Wave 1 surfaces rely on route smoke, targeted interaction checks, backend verification, and shared-shell parity rather than fresh three-breakpoint screenshots inside this package.

### Blocked items
- None.

### Unverified items
1. Real inbox delivery for PM / HR / Shop / Safety / Dispatch forgot-password emails in Production.
2. PM / HR / Shop reset-link retrieval through inbox delivery rather than preview token generation.
3. Live vendor authentication success path for `/dev/login` (backend intentionally disabled in Preview).
4. Fresh three-breakpoint screenshot capture for unrepaired Wave 1 surfaces inside this specific approval package.

### Accepted risks
- Preview evidence may not fully represent production email-delivery conditions.
- Safety / Dispatch preview backend still hands back internal reset token fields even though operators no longer see them in the UI.
- `/dev/login` remains intentionally disabled in Preview and is recommended for approval only as a truthful disabled surface, not as a live authenticated workflow.

---

## 8. Executive sign-off block

WP-16 WAVE 1 — EXECUTIVE SIGN-OFF

Final scope denominator: 30 active routes, 1 legacy/unrouted page, 5 embedded dialogs, 13 primary workflows, 5 dynamic routes, 6 error/session state groups
Open P0 defects: 0
Open P1 defects: 0
Open P2 defects: 0
Blocked items: 0
Accepted risks: 3
Unverified items: 4
Foundation changes made: 2 shared-file behavior guards (`sessionReset.js`, `EnforcePortalScope.jsx`) plus frozen-shell reuse on local pages only
Wave 2 started: NO

Technical recommendation:
[APPROVE]

Executive decision:
[ ] APPROVED AND LOCKED
[ ] REJECTED — RETURN TO PUNCH LIST

Executive comments:

Approved by:
Date: