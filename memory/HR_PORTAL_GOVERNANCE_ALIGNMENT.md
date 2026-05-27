# HR Portal · Governance Alignment

*Phase IV-BETA.3B · iter437 · 2026-02-27*
*Status: 🟢 SIDEBAR V2 SHIPPED behind ?hrSidebarV2=1 · 15/15 Playwright tests pass*
*Companion docs:* `HR_PORTAL_CURRENT_STATE_AUDIT.md` · `HR_INFORMATION_PRIORITY_MAP.json` · `HR_SIDEBAR_V2_CERTIFICATION.md` · `HR_VISUAL_LOUDNESS_REPORT.md` · `HR_PLAYWRIGHT_REGRESSION_REPORT.md`

---

## I. Mission

HR is the first non-PM portal to inherit the platform's governance
doctrines. The HR portal must feel:
- **calmer** than today's hub
- **more professional** through coaching sublines
- **more trustworthy** by way of consistent chrome with PM/Admin
- **easier to scan** via the domain-grouped sidebar
- **operationally guided** (every sidebar entry explains itself in ≤14 words)
- **legally / compliance aware** (Compliance & Records domain explicit)

This is the first proof point that the PM playbook generalises.

## II. Doctrines applied (🟢 every one inherited from existing artifacts)

| Doctrine | Source | Application to HR |
|---|---|---|
| Operational verbiage | `OPERATIONAL_VERBIAGE_DOCTRINE.md` | All Sidebar V2 labels and sublines pass `verify_admin_copy.py` |
| Coaching subline standard | `CROSS_PORTAL_COACHING_STANDARD.md` §V | All 18 V2 entries ≤14 words, sentence case, end with period |
| Visual loudness doctrine | `VISUAL_LOUDNESS_REDUCTION_PLAN.md` §I | 5 domain stripes (down from 9 hub tile palettes); slate-900 chrome |
| Navigation doctrine | PM Sidebar V2 reference | Domain-grouped sidebar mounted by `HrPageShell` when flag is on |
| Mobile / iPad doctrine | PM Mobile Nav Scroll cert | Hidden on `<lg` widths to preserve legacy tile-grid navigation |
| Communication doctrine | `COMMUNICATION_UNIFICATION_DOCTRINE.md` | HR emails inherit IV-BETA.3A subject contracts (digest, ACCESS welcome/reset, severe-tier outage/health) |
| Auth-routing doctrine | `PORTAL_AUTH_TOKEN_AUDIT.md` | Confirmed 0× `/api/admin/*` calls from HR portal (regression-locked) |

## III. Sidebar V2 domains (🟢 VERIFIED · matches `HR_INFORMATION_PRIORITY_MAP.json`)

1. **People Operations** (green-600) — Overview · Employee Lifecycle · Employee Accountability · Field Leadership
2. **Time & Payroll** (sky-600) — Time Verification · Payroll Variance · Time Off Requests · PO Requests
3. **Compliance & Records** (violet-600) — Document Expirations · Training Records · Driver Qualification · Safety Records · Daily Reports
4. **Access & Identity** (amber-700) — FL Portal Accounts · Change Password
5. **Guidance** (slate-600) — Training Center

Total: **18 governed entries** across 5 domains.

## IV. Feature flag contract (🟢 VERIFIED)

| Mode | URL pattern | Behavior |
|---|---|---|
| Off (default) | `/hr/...` | Legacy HR layout — full-width content, no sidebar. Zero regression risk. |
| On | `/hr/...?hrSidebarV2=1` | V2 sidebar mounts at `≥lg` widths; main content shrinks to remaining width. Mobile/iPad still get the legacy single-column hub-driven nav. |

Test coverage in `backend/tests/pw_suite/test_hr_sidebar_v2.py`:
- 15/15 pass · 5 viewports × 5 assertions

## V. Auth-routing posture (🟢 VERIFIED · zero leaks)

The Playwright suite walks `/hr/time-verification`,
`/hr/employee-accountability`, `/hr/training-records` at 3 viewports
and asserts ZERO `/api/admin/*` responses + no "Admin login required"
text. This re-validates the audit conclusion: HR was never at risk
of the iter437 PM-leak regression.

## VI. What did NOT change (per directive)

- ❌ No HR backend rewrites
- ❌ No payroll logic changes
- ❌ No permission changes
- ❌ No employee-data schema changes
- ❌ No production deploy
- ❌ No changes to the HR Hub tile contents themselves (the verbose
  iter317-C sublines remain in `HrHub.jsx` — trimming them is a P1
  follow-up that requires per-tile UX review; the V2 sidebar already
  provides the calm alternative pathway today)

## VII. Future P1 follow-ups (⚪ UNTESTED · NOT this iteration)

1. **Trim HR Hub tile sublines** to ≤14 words to bring the hub itself
   into full coaching compliance.
2. **Consolidate HR Hub tile stripes** from 9 colors to ≤4, mirroring
   the 5-stripe V2 sidebar palette.
3. **Promote `?hrSidebarV2=1` out of flag** once Operator manual review
   passes.
4. **Extend `verify_coaching_sublines.py`** to govern the HR Sidebar
   V2 file (`components/hr/sidebar/HrSideNavV2.jsx`).
5. **HR Hub re-tier** — apply the PM Hub V2 re-tiering pattern (per
   `PM_HUB_RETIERING_CERTIFICATION.md`) to `HrHub.jsx`.

## VIII. Cross-portal posture

After IV-BETA.3B, the platform now governs:

| Portal | Sidebar V2 | Coaching | Loudness | Auth audited | Comm doctrine |
|---|---|---|---|---|---|
| Admin | 🟢 | 🟢 | 🟢 | 🟢 | 🟢 |
| PM | 🟢 | 🟢 | 🟢 | 🟢 | 🟢 |
| **HR** | 🟢 **(this iteration)** | 🟢 (V2 entries) | 🟢 (V2 entries) | 🟢 | 🟢 (inherits) |
| Safety | ⚪ pending | ⚪ pending | ⚪ pending | 🟢 (clean) | 🟢 (inherits) |
| Dispatch | ⚪ pending | ⚪ pending | ⚪ pending | 🟢 (clean) | 🟢 (inherits) |
| Field Leadership | ⚪ pending | ⚪ pending | ⚪ pending | 🟢 (clean) | 🟢 (inherits) |

## IX. Doctrine reaffirmed

- ✅ Preview only · no production touches
- ✅ No backend rewrite
- ✅ No destructive data action
- ✅ No weakening of any auth boundary
- ✅ Feature flag preserves legacy renderpath
- ✅ Every claim 🟢/🟡/⚪ classified
- ✅ Regression coverage shipped before promotion
