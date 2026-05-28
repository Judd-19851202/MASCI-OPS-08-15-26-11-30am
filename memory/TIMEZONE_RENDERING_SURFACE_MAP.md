# Timezone Rendering Surface Map

_Phase TRUST-TIME-1 · 2026-05-28._

Every operator-facing surface that renders a timestamp, classified
by helper + verdict.

| Surface | File | Helper | Verdict |
|---|---|---|---|
| **PO list** "Created" cell | `pages/PoRequests.jsx:309` | `formatLocalDate` | 🟢 fixed |
| **PO drawer** "Submitted" | `pages/PoRequests.jsx:554` | `formatLocalDateTime` | 🟢 fixed |
| **PO drawer** "Approved by … on" | `pages/PoRequests.jsx:556` | `formatLocalDateTime` | 🟢 fixed |
| **PO drawer** receipt-uploaded | `pages/PoRequests.jsx:568` | `formatLocalDateTime` | 🟢 fixed |
| **PO audit log** entry timestamp | `pages/PoRequests.jsx:680` | `formatLocalDateTime` | 🟢 fixed |
| **Notifications digest** "last detected" | `pages/NotificationsDigest.jsx:123` | `formatLocalShort` | 🟢 fixed |
| **Notifications digest** "Generated" | `pages/NotificationsDigest.jsx:191` | `formatLocalDateTime` | 🟢 fixed |
| **PM FL list** "occurred at" | `pages/PmFieldLeadership.jsx:163` | `formatLocalDate` | 🟢 fixed |
| **PM FL detail** "Filed" | `pages/PmFieldLeadership.jsx:203` | `formatLocalDateTime` | 🟢 fixed |
| **HR Accountability** timeline footer | `pages/HrEmployeeAccountabilityTimeline.jsx:454` | `formatUtcForAudit` | 🟢 fixed (audit · UTC labeled) |
| **Admin System Health** "Checked" | `pages/admin/SystemHealth.jsx:65` | `formatUtcForAudit` | 🟢 fixed (audit · UTC labeled) |
| Incident detail "Generated" | `pages/ViewIncident.jsx:715` | `new Date(x).toLocaleString()` | 🟢 already correct (backend now tz-aware) |
| Inspection detail "Generated" | `pages/ViewInspection.jsx:479` | `new Date(x).toLocaleString()` | 🟢 already correct |
| Meeting detail "Generated" | `pages/ViewMeeting.jsx:406` | `new Date(x).toLocaleString()` | 🟢 already correct |
| Daily Report "Generated" | `pages/ViewDailyReport.jsx:631` | `new Date(x).toLocaleString()` | 🟢 already correct |
| Tasks "created" | `pages/Tasks.jsx:210,315` | `new Date(x).toLocaleString()` | 🟢 already correct |
| Safety Form "Generated" | `pages/ViewSafetyForm.jsx:441` | `new Date(x).toLocaleString()` | 🟢 already correct |
| Admin Profile "Enabled · created" | `pages/admin/AdminProfile.jsx:156` | `_fmt()` (toLocaleString) | 🟢 already correct |
| ShopHub recent activity | `pages/ShopHub.jsx:577` | `relTime()` | 🟢 already correct |
| OPS-1 page "loaded/generated Xs ago" | `pages/admin/SelfProtection.jsx:183` | `_fmtAgo()` (local helper) | 🟢 already correct |

## Surfaces remaining (admin / dispatch · low operator impact)

These render timestamps using the old `.slice(0,16).replace("T"," ")`
anti-pattern. They are admin-context audit surfaces, so the
display-as-UTC-but-unlabeled is misleading but lower priority. They
are slated for the next stabilization pass:

| File | Line(s) | Severity |
|---|---|---|
| `pages/admin/AdminDispatch.jsx` | 312, 508, 551, 746, 769 | MEDIUM (audit) |
| `pages/admin/AdminIntegrationCenter.jsx` | 145, 146, 147, 654, 1198 | LOW (integrations audit) |
| `pages/admin/AssetProfile.jsx` | 184, 269, 295, 318 | LOW (asset audit) |
| `pages/admin/AdminOperationsEvents.jsx` | 112 | LOW (governance audit) |
| `pages/admin/AdminLegacyImports.jsx` | 289, 436 | LOW (one-time import) |
| `pages/AssetTransfers.jsx` | 203 | LOW |
| `pages/HrDriverQualificationImport.jsx` | 392 | LOW (one-time import) |
| `pages/HrPayrollVariance.jsx` | 265 | LOW |

**Rule of thumb:** any surface a Field Leadership / Foreman / PM
will look at during normal operations MUST use the new local-time
helpers. Admin audit surfaces MAY continue to use the slice pattern
short-term, but will migrate to `formatUtcForAudit()` in the next
sweep to guarantee the literal " UTC" suffix is always visible.

## Future surfaces (RFI / Schedule)

When V.1 lands, every timestamp on the RFI list, RFI detail,
schedule shell, and external-collaboration surfaces MUST use the
local helpers from day one. The doctrine in
`TIMESTAMP_UTILITY_STANDARD.md` applies.
