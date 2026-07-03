# TRACK 19.51 · Portal-by-Portal Review

Each portal's audit summary (details in the Remediation Roadmap).

## Admin (v1 · `AdminHub.jsx`) — ACTIVE BUT NOISY
- **Answers "what needs attention"?** Partially. 6/34 tiles carry real attention signal; the rest are navigation shortcuts.
- **Command Center compliance:** ❌ (missing Attention Strip and Action Queue).
- **P1 fix:** Consolidate 34 tiles into the 8-section canonical layout. Deprecate v1 in favour of v2.

## Admin (v2 · `AdminHubV2.jsx`) — ACTIVE
- **Answers "what needs attention"?** Yes — the section-based sidebar surfaces every module cleanly.
- **Compliance:** partial. Sidebar is elite; the individual section homes still vary.
- **P2 fix:** Roll the Command Center standard down into each admin section landing.

## OI Cockpit — REFERENCE STANDARD ✅
- **6/6 CRITICAL widgets, 0 NOISE.**
- Compliance: full. Every future portal home should mirror the structure.

## OI Recipients — ACTIVE ✅
- Compliance: full.
- Dry-run banner · summary strip · form on demand · filter bar · table · groups panel.

## Safety (`SafetySection.jsx` / `SafetyHub.jsx`) — ACTIVE BUT CONFUSING
- **Answers "what needs attention today"?** Partial — high-attention cases require drilling into `/safety/cases`. Nothing on the hub says "3 CAPAs overdue".
- **P1 fix:** Add an Attention Strip driven by `safety_morning_digest` summary. Link Executive Intelligence page.

## HR (`HrHub.jsx`) — ACTIVE BUT NOISY
- **Answers "employee lifecycle risks"?** Weak. Missing an "expiring certifications" and "onboarding stalled" strip.
- **P1 fix:** Attention Strip driven by `hr_intelligence` and `training_intelligence` summaries.

## PM (`PmHub.jsx` · `PmCommandCenter.jsx`) — ACTIVE BUT CONFUSING
- **Answers "which jobs need attention"?** PM Command Center partially. Hub is more of a tile launcher.
- **P1 fix:** Retire the PM Hub in favour of PM Command Center as the default `/pm` landing. Integrate `project_intelligence` snapshot.

## Shop (`ShopHub.jsx`) — ACTIVE BUT HIDDEN
- **Answers "what equipment needs action"?** Weak — safety holds and aging critical defects live in sub-pages.
- **P1 fix:** Attention Strip driven by `shop_intelligence` summary.

## Dispatch (`DispatchHubV2.jsx` · `DispatchCommandCenter.jsx`) — ACTIVE (best non-OI cockpit)
- **Answers "what is blocked before the day starts"?** Yes.
- Compliance: high. Some tiles need Attention Strip formalisation.
- **P2 fix:** Attention Strip formalisation only.

## Fleet (`FleetVisibility.jsx`) — ACTIVE BUT CONFUSING
- **Answers "availability / risk / blockers"?** Partial — data is present but scattered.
- **P1 fix:** Attention Strip driven by `fleet_intelligence` summary. Consolidate DVIR + defects + holds counts.

## Field (`FieldSection.jsx` · `FieldLeadershipHub.jsx`) — ACTIVE
- **Answers "what does the field crew need to do today"?** Partial; heavily task-launcher oriented.
- **P2 fix:** Add a Today Action Queue.

## Guidance / Help — ACTIVE BUT HIDDEN
- **Answers "how do I do this workflow"?** Weak — reads like feature documentation.
- **P2 fix:** Restructure into role-based workflows (Safety Director, PM, etc.).

## Public entry — ACTIVE
- Multi-portal login is clean.
- Compliance: N/A (out of Command Center scope).
