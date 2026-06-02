# CUSTOMER #2 SIMULATION REPORT

**Authority**: FOCP MASTER PROGRAM · Phase 10
**Status**: 🟡 **DEFERRED — CANNOT BE DONE BY AI ALONE**
**TR ID**: TR-D003

---

## Why this is deferred

A Customer #2 simulation, as specified, requires either:

1. A real Customer #2 user account I can drive through the platform (does not exist · no Customer #2 has been onboarded), OR
2. AI role-playing a PM / Safety / HR / Superintendent without tribal knowledge.

Option 2 is the form an AI agent can technically perform — but it produces low-evidence output. An AI that has read the entire codebase cannot credibly pretend not to know it. The "confusion" and "friction" reported would be a synthesis of the audit registers, not a genuine first-encounter measurement. That is exactly the phantom-evidence pattern the FOCP directive forbids.

## What an honest Customer #2 simulation looks like

The operator must convene a **2-hour tabletop walkthrough** with three participants:

* A neutral observer (the operator, or a designee)
* A "Customer #2 PM" — ideally a real construction-services PM from outside MASCI, given a fresh login and the platform URL with zero coaching
* A scribe who records confusion points verbatim

Or, equivalently, a **5-day live pilot** where Customer-#2-like persona accounts are seeded into a parallel preview pod, given login credentials and a single-page "Welcome to MASCI Operations" doc, and observed.

## What I CAN provide as scaffolding

The following four artifacts ARE producible by AI from source-side evidence and ARE useful inputs to the human-led simulation:

### 1 · Predicted confusion points (source-derived)

| Persona | Predicted confusion | Source evidence |
|---|---|---|
| PM | "What is the difference between a Project and a Job?" | FRICTION #19 + Hub.jsx terminology mix |
| PM | "Why does my Daily Report say 'Open' after I submit?" | FRICTION #5 — still observable in source |
| Safety | "How do I prove a foreman acknowledged the JHA?" | TR-0001 — no JHP ledger exists |
| Safety | "Where do I see who hasn't done their CDL renewal?" | Already-shipped — should be findable; may need coaching on driver-qualification dashboard location |
| HR | "What's the difference between Pending and Needs Review?" | FRICTION #17 — HR Queue dual-state |
| HR | "If I terminate someone by mistake, how do I undo?" | TR-0002 — universal undo missing |
| Superintendent | "Where's the project I just started?" | Hub.jsx grouping question · likely findable |
| Superintendent | "How do I close a constraint?" | Inline resolve button on ConstraintDetail · should be findable |

### 2 · Predicted question list (what a new user asks)

* "Where do I log in?" → `/login`
* "What's my project list?" → `/projects` (PM) or Hub tile
* "How do I file a daily report?" → `/daily/submit` (public route) or `/daily/new`
* "How do I file an incident?" → `/incidents/submit` or `/incidents/new`
* "Where do I see my crew's compliance?" → PM Crew Compliance (PmHub)
* "Where's the help?" → HelpTip components scattered · LifecycleGuide for lifecycles · no central help center

### 3 · Predicted failure modes

* New user opens Hub.jsx → sees 4 grouped sections (Today / Leadership / 03 / Reference) — reasonable but not personalized.
* New user can't find docs / training material — confirmed: there is no in-app help center beyond HelpTip + LifecycleGuide.
* New user files a Daily Report, sees "Open" status, asks support — predicted high-frequency call.
* New user attempts to close a constraint — finds the inline Resolve button quickly; no reopen path exists; if they made a mistake they ask support.
* New user tries to "approve" a PO with the wrong role — sees no button (capability-gated) — predicts confusion if they thought they should have approval rights.

### 4 · Predicted friction quotient

Estimated **70 % of Customer #2 personas will complete their primary daily workflow without Jaymn**, derived from:

* Source-side scaffolding score: 79 %
* Pattern-reuse compliance: high (Rank #1 + LifecyclePanel substrate cover the high-frequency workflows)
* Documentation gap: medium (HelpTip exists but no central guide)
* JHP / OC-005 gap: 0 % completion for Safety personas attempting JHP workflows (TR-0001)
* Universal undo gap: friction on every mistake (TR-0002)

## What the operator must deliver to unblock TR-D003

| Input | Description |
|---|---|
| Either | A live 2-hour tabletop walkthrough transcript with verbatim confusion points |
| Or | A 5-day pilot with a Customer-#2 persona account + observed-session notes |
| Plus | Authorization for AI to incorporate the resulting evidence into TR-#### entries |

Estimated operator effort: **2 hours (tabletop) to 5 days (pilot)**.

---

End of Customer #2 Simulation Report · TR-D003 remains DEFERRED.
