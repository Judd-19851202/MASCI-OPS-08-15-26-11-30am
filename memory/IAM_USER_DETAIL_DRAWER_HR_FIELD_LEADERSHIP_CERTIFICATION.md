# IAM_USER_DETAIL_DRAWER_HR_FIELD_LEADERSHIP_CERTIFICATION.md
## OMEGA · Mandatory Addendum · HR Field Leadership Drawer Parity Certification
**Date**: 2026-06-04 15:38 UTC  **Verdict**: 🟢 PASS — same canonical drawer renders inside the HR portal Field Leadership login-management dashboard.

---

## 1. Mandate (from operator directive)

> *"The Unified User Detail Drawer must also be available inside the HR Portal Field Leadership login-management dashboard. HR users who issue Field Leadership logins must see the same identity/access/password/activity/audit visibility standard used by Admin People & Access. Do NOT create a separate HR-only drawer. Do NOT create a different Field Leadership login UI inside HR. Do NOT fork the design. Do NOT duplicate logic. Reuse the same shared IAM drawer/component wherever possible."*

## 2. Compliance attestation

| # | Mandate | Status |
|--:|---------|:-:|
| 1 | Same IAM row layout in HR Field Leadership dashboard | 🟢 — uses the same `<IamStandardCells>` widget |
| 2 | Same password lifecycle display | 🟢 — same `<IamPasswordStatusBadge>` |
| 3 | Same access status display | 🟢 — same `<IamAccessStatusBadge>` |
| 4 | Same activity display | 🟢 — same `<ActivityPill>` reducer |
| 5 | Same audit link pattern | 🟢 — same `<IamViewAuditLink>` → `/admin/audit?actor=<email>` |
| 6 | Same `View Details` drawer | 🟢 — same `<IamUserDetailDrawerHost/>` mounted at `HrFieldLeadershipUsers.jsx:69` |
| 7 | Same unavailable-data behaviour using `—` | 🟢 |
| 8 | Same tooltip: "Not tracked by this login source yet." | 🟢 |
| 9 | No-data-loss guarantees | 🟢 (UI-only · 0 writes) |
| 10 | No-credential-impact guarantees | 🟢 (0 auth/password code touched) |

## 3. Single source of truth verified

The HR-facing page `frontend/src/pages/HrFieldLeadershipUsers.jsx`:
- mounts the **same** `<AdminFieldLeadershipUsersPanel/>` component (line 66) that the Admin page uses
- mounts the **same** `<IamUserDetailDrawerHost/>` component (line 69)
- adds zero HR-specific component variants

Drawer is opened by clicking the `data-testid="iam-row-view-details-field-leadership-<email>"` button — same button code as the Admin-side renders. Same `openIamUserDrawer()` helper. Same drawer body. Same `View Full Audit History` deep-link.

## 4. Live verification (preview env)

`/tmp/iam_drawer_hr_fl_v2.png` captures HR Manager (`hrmanager@mascigc.com`) opening the canonical drawer for Allen Smathers on `/hr/field-leadership-users`:
- Drawer renders identically to the Admin surface (`/tmp/iam_drawer_admin.png`)
- Same right-side sheet · same Identity / Portal Access / Activity / Audit sections
- Same canonical badge vocabulary

24 `View Details` buttons rendered on the HR-side FL dashboard (one per FL user).

## 5. Backward-compat / safety attestation

| Item | Status |
|------|:-:|
| Existing Field Leadership logins issued by HR still work | 🟢 (FL portal `/api/field-leadership/portal/login` endpoint not touched) |
| Existing issued temp passwords remain valid | 🟢 (no password code changed) |
| No identity / credential data was modified | 🟢 (no DB writes from the 4 changed files) |
| No HR-only drawer was forked | 🟢 (verified: only one `<IamUserDetailDrawerHost/>` definition exists) |
| No different FL UI was created inside HR | 🟢 (HR page renders the same panel + same drawer · no new HR-specific FL component) |

## 6. Final attestation (verbatim)

> **"No existing user, password, temp password, credential, login history, audit history, role assignment, or portal assignment was modified, deleted, recreated, invalidated, or migrated."**

> *"Existing Field Leadership logins issued by HR remain valid. Existing FL temp passwords remain valid. Existing FL portal grants remain unchanged. Existing FL audit history is preserved."*

🟢 **HR Field Leadership drawer parity certified.**
