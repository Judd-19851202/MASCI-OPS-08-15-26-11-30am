# TRACK 15.43 · Dispatch Audit

**Verdict:** 🟢 **GREEN**

## Surface inventory

| Workflow | Page | Backend |
|---|---|---|
| Login | `DispatchLogin.jsx` | `/api/auth/dispatch-login` (Track 15.34 hardened) |
| Command Center | `DispatchCommandCenter.jsx` | `routes/dispatch_lifecycle` |
| Board | `DispatchBoard.jsx` | `routes/dispatch_lifecycle` |
| Haul Ledger | `DispatchHaulLedger.jsx` | `routes/dispatch_lifecycle` |
| Driver Profile | `DispatchDriverProfile.jsx` | `routes/dispatch_lifecycle` |
| Driver Qualification | `DispatchDriverQualification.jsx`, `HrDriverQualificationImport.jsx` | `routes/dispatch_lifecycle` + HR import |
| Day-1 Debrief | (route + form) | `routes/dispatch_day1_debrief` |
| Hub | `DispatchHub.jsx`, `DispatchHubV2.jsx` | `routes/dispatch_lifecycle` |
| Password change | `DispatchChangePassword.jsx`, `DispatchResetPassword.jsx`, `DispatchForgotPassword.jsx` | Track 15.34 auth |

## Pass Criteria
* Assignment flow visible (driver → run → equipment): ✅
* Notifications routed to dispatch scope: ✅ (`recipient_role=dispatch`, link_url certified Track 15.40)
* Record persistence (haul ledger, debrief): ✅ via `dispatch_lifecycle`
* Retrieval through Command Center + Board + Haul Ledger: ✅

## Known consideration
* Driver qualification expiration timing surface — see Friction Register FR-006 (notification fires correctly but the UI surface for "expires in 7d / 14d" depends on the existing notification scheduling; if a customer expects a different cadence they can override via the existing scheduled job env vars).

🟢 **GREEN — Dispatch can operate entirely from the platform.**
