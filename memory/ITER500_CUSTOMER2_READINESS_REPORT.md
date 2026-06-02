# ITER500 · CUSTOMER #2 READINESS REPORT

**Date**: 2026-06-02T19:30 UTC
**Mode**: READ-ONLY

Assume a new construction-services customer signs up with **zero MASCI tribal knowledge**.

---

## What works out of the box

* Login flows (HR · PM · Dispatch · Field Leadership · Admin) are standard email/password with reset paths.
* Hub pages tile the available workflows reasonably for first-time discovery.
* HR Lifecycle drawer (post-iter453.9) communicates save outcome clearly with OLD → NEW labels.
* QA/QC and Site Inspection lifecycle panels are self-documenting via the lifecycle-vocabulary HelpTip.
* Phase Alpha governance enforces HR-only authority — onboarding admin cannot accidentally bypass.
* iter453.5 introduced "lifecycle-vocabulary" HelpTip blocks that explain Active vs Inactive vs Resigned in-app.

## Tribal-knowledge blockers (gating Customer #2 self-onboarding)

| # | Blocker | Required action before customer #2 can self-operate |
|---:|---|---|
| 1 | OC-005 JHP Acknowledgement Ledger not built (iter454 backlog) | Build OC-005 or document as "Phase 2 feature" |
| 2 | Inconsistent "Save" / "Submit" / "Create" verbs across forms | Verb-harmonization pass |
| 3 | Daily Report "approved" implicit shop step not in-UI | Surface shop-approval step as explicit lifecycle state |
| 4 | "Reactivate" vs "Rehire" dual-path on Inactive → Active | Funnel both to a single dialog with rehire-date optional toggle |
| 5 | Training records expiry-soon visual cue missing | Add yellow/red row tint at < 30 / < 7 days |
| 6 | Constraint resolution does NOT use the same lifecycle panel as Incident / QA/QC | Promote LifecyclePanel substrate to Constraint detail |
| 7 | Admin guide (`/admin/guide`) is not exposed to non-admin personas | Create a Customer #2 onboarding center |
| 8 | Operator-onboarding for `RESEND_WEBHOOK_SECRET` is undocumented in-app | Add a deploy-readiness wizard for env vars |
| 9 | Field-Leadership portal records mix types (termination · hire · equipment) without type filter | Add type-filter chips at top |
| 10 | Photo Viewer "tagged employees" implies attribution but is just metadata | Rename to "Visible employees" |
| 11 | Asset transfer "receive" workflow is a subtle checkbox | Promote to explicit "Mark received" button with toast |
| 12 | Sub/Vendor archive workflow doesn't exist | Add archive verb + confirmation dialog |
| 13 | Notifications digest opt-in buried in admin | Add per-user notification prefs page |
| 14 | No global "What's new" / "Release notes" surface for ops-side users | iter453.5 HelpTip pattern can be extended app-wide |
| 15 | No customer-#2 self-onboarding journey from scratch (signup → admin profile → seed data → first job) | Build a guided-tour wizard |

---

## Customer #2 readiness score

* **Workflow coverage**: 84 workflows · 46 🟢 + 28 🟡 + 10 🔴 = **84 % usable out-of-the-box** if guided onboarding is provided
* **Discoverability**: 🟡 — Hub tiles + iter453.5 HelpTips help, but verb inconsistency creates friction
* **Onboarding completeness**: 🔴 — no built-in onboarding journey · operator must hand-hold first customer

**Customer #2 Readiness %** ≈ **60 %** out-of-the-box (without operator hand-holding)
**Customer #2 Readiness %** ≈ **85 %** with a 2-hour onboarding video and printed quickstart guide

---

## STOP
