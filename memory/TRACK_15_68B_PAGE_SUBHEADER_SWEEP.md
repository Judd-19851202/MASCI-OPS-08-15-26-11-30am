# TRACK 15.68B · Page Subheader Sweep — ✅ Runtime helper SHIPPED

See `TRACK_15_68B_FINAL_CLOSEOUT.md` §6.

**Runtime helper (already shipped in 15.68A)** — `lib/usePageTitle.js` rewrites trailing "· MASCI" / "· MASCI Operations Platform" / "· MASCI Hub" patterns at runtime, so every page using `usePageTitle("…· MASCI")` now renders with the active tenant's `branding.platform_short_name` from sessionStorage without per-file edits.

**Hardcoded body subheaders deferred to 15.68C** (~12 strings):
- `pages/SignIn.jsx`
- `pages/Hub.jsx`
- `pages/Dashboard.jsx`
- `pages/TrainingHub.jsx`
- `pages/guidance/OperationalGuidanceCenter.jsx`
- `pages/V2Compare.jsx`
- `pages/PublicTimeOff.jsx`
- `pages/HrTimeVerification.jsx`
- `pages/NewFleetDVIR.jsx`
- `pages/trench_safety/PublicTrenchSafetyDashboard.jsx`
- `pages/trench_safety/PublicTrenchSafetyReport.jsx`
