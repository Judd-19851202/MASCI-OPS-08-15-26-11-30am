# TRACK 19.56 · Human Walkthrough

## HR Manager opens `/hr/employees/:id/thread`
- Mission Overview reads: name · trade · supervisor · lifecycle · expiring/expired counts.
- Operational Health tier and "Why: …" line answer readiness in one line.
- Attention section lists any expired or expiring credentials with severity chips.
- Action Queue (max 5) shows the concrete steps (renew credentials, schedule renewal, review incidents).
- Timeline section presents the same certified events, now rendered through the universal `OperationalThread` visual.
- ✅ **PASS.**

## Safety Manager opens the same URL
- Sees the exact same layout (server-side filtering unchanged).
- Sees `Incidents` category events prominently in the timeline.
- Can still export the certified PDF brief via the same button.
- ✅ **PASS.**

## Transportation Manager
- Sees `Driver Qualification` events; `expiring_within_90d` list surfaces CDL / DOT-Medical renewals as HIGH-severity attention items.
- ✅ **PASS.**

## Superintendent / Operations
- Sees Mission Overview → Attention → Action Queue → Timeline → Relationships in the same order as every other Operational Thread.
- No new training required; recognises the shell from the Fleet Unit Thread pilot.
- ✅ **PASS.**

## Executive
- Sees `hr_intelligence` OI score + attention chip + trend on Section 8.
- Opens Section 3 Guidance Card for full drill-down.
- ✅ **PASS.**

## New user (first login)
- Reads the Decision Boundary footer on the Guidance Card.
- Understands the platform assists but never decides.
- ✅ **PASS.**

## Cross-navigation
- User on the classic page clicks "Universal Thread" → lands on `/hr/employees/:id/thread`.
- User on the Thread page clicks "Classic view" → returns to `/hr/employees/:id/accountability`.
- Both routes remain fully functional. Nothing was removed.
