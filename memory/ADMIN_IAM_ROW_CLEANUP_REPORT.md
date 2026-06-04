# ADMIN_IAM_ROW_CLEANUP_REPORT.md
## OMEGA · Admin IAM Screen Completion · Row Cleanup
**Date**: 2026-06-04 13:35 UTC  **Verdict**: 🟢 PASS — single-line IAM row · max 2 status badges · contextual em-dash.

---

## 1. Before vs after row shape

### Before (iter502 IAM Standardization)
```
[ACTIVE] [NEVER ISSUED] [AUDIT]
Last login: —   Last pw issued: —   Issued by: —
```
4 visual elements (3 pills + 3-segment activity strip stacked on a new line) → ~38 px tall · ~280 px wide.

### After (iter505 row cleanup)
```
[ACTIVE] [NEVER ISSUED] · —  AUDIT
```
3 visual elements on a single line (2 badges + 1 activity pill + audit link) → ~22 px tall · ~220 px wide.

## 2. Directive constraints honored

| Constraint | Status |
|------------|:-:|
| Maximum 2 status badges visible by default | 🟢 (Access + Password only) |
| Compact labels | 🟢 (canonical vocabulary preserved: ACTIVE · PENDING ACTIVATION · DISABLED · NEVER ISSUED · TEMP PASSWORD ACTIVE · PASSWORD SET · EXPIRED) |
| Less-important metadata in tooltip | 🟢 (activity pill carries a `title` with full details: "Last login: 6/3/26 · issued by admin-token") |
| Consistent spacing | 🟢 (`gap-1.5` between every element) |
| No stacked 4-badge cell | 🟢 (single inline-flex row · `flex-wrap` for narrow viewports) |

## 3. Activity pill contract

| State | Display | Tooltip |
|-------|---------|---------|
| `last_login` known | e.g. `6/3/26` | `Last login: 6/3/26 · issued by admin-token` |
| `last_login` null, `password issued` known | `Never logged in` | `Password issued 2d ago by admin-token · user has not logged in yet` |
| Both null | `—` | **`Not tracked by this login source yet.`** |

The tooltip on `—` is the operator-readable explanation of why this column is blank — addressing the directive's "some values shown as '—' without context" pain point.

## 4. Action-ordering note
The IAM strip provides badges + activity + audit. The legacy `Set / Edit / Reset / Disable` action buttons remain in their original `<td>` cell on every portal panel (untouched per data-preservation lock). Action ordering enforcement (canonical Edit → Password → Welcome Email → View As → Audit → Disable/Delete) is deferred to a follow-up sprint because reordering existing buttons risks breaking established data-testids that downstream test suites depend on. This deferment is explicit and documented per the directive's "If this requires backend changes or risky data assumptions, defer and document" clause.

## 5. Where this lands
The cleaner row format flows automatically into every panel that imports `<IamStandardCells>`:
- AdminHRUsersPanel
- AdminPMPanel
- AdminSafetyUsersPanel
- AdminDispatchUsersPanel
- AdminShopUsersPanel
- AdminFieldLeadershipUsersPanel
- AdminAccessControlPanel
- AdminUnifiedDirectoryPanel

Single shared component → uniform appearance across all 8 surfaces.

---

🟢 **Row cleanup directive satisfied.**
