# OA-1 · Operations Actions Constitution
**ForgedOps Operations Command Center Standard**
**Filed:** 2026-06-08
**Status:** 🟢 CANONICAL — no code may be written that violates this document.

---

## Purpose

Operations Actions (OA) are the operational ownership framework for ForgedOps.

**Operations Actions are NOT:**
- A ticketing system
- A maintenance system
- A dispatch system
- A fleet management system
- A replacement for MaintainX
- A replacement for FleetWatcher
- A replacement for Motive
- A replacement for Vista

**Operations Actions ARE:**
A lightweight operational coordination layer that provides visibility, ownership, accountability, and resolution tracking across MASCI operations.

---

## ForgedOps Five Pillars

Every Operations Action feature must satisfy:

| Pillar | Standard |
|--------|----------|
| **Powerful** | Provides operational visibility and ownership. |
| **Simple** | A foreman can create an Operations Action in under 30 seconds. |
| **Beautiful** | Consistent design, spacing, terminology, and workflow across the platform. |
| **Trusted** | No hidden automation, no hidden ownership changes, no silent status updates. |
| **Proven** | Validated by actual field use before expansion. |

---

## Operations Action Definition

An Operations Action is:

> "Something requiring ownership, attention, coordination, correction, or resolution."

**Examples:**
- Truck Down
- Utility Conflict
- Missing MOT
- GPS Equipment Issue
- Plant Delay
- Survey Required
- Near Miss
- Safety Concern
- Material Shortage
- Customer Request

---

## Mandatory Coaching Framework

Every OA screen must contain:

- **Why This Matters** — explain why Operations Actions exist.
- **Who Sees This** — explain who receives visibility.
- **What Happens Next** — explain assignment and ownership flow.
- **When To Escalate** — provide practical field examples.
- **Common Mistakes** — prevent poor submissions.

Coaching language must match Daily Reports, Excavation Operations, Safety Meetings, and JHP workflows.

---

## Mandatory Bilingual Standard

Spanish support is **REQUIRED on Day One**.

- No deferred translations.
- No backlog translations.
- No partial translations.

**Required:** Labels · Buttons · Tooltips · Coaching Panels · Filters · Statuses · Notifications · Reports · Dashboard Chips · Emails · Empty States · Validation Messages · Help Text.

All visible text must support EN and ES. **Database stores canonical English values only.** Translation occurs at the display layer.

---

## Core Fields

Minimum OA record:

- OA Number
- Title
- Category
- Priority
- Job
- Location
- Description
- Owner
- Due Date
- Status
- Photos
- Notes
- Linked Records

---

## Approved Statuses

Only:
- `Open`
- `Assigned`
- `In Progress`
- `Waiting`
- `Completed`
- `Closed`

No additional statuses without approval.

---

## Ownership Requirements

Every OA must display:
- Created By
- Created Date
- Current Owner
- Assigned Date
- Last Updated
- Current Status

**Ownership must never be ambiguous.**

---

## Language Standards

**Never use:** Rejected · Failed · Denied.

**Use:** Action Required · Needs Information · Pending Review · Pending Assignment · Pending Closure · Closed.

Must match existing ForgedOps standards.

---

## Integration Philosophy

ForgedOps is never the system of record.

- MaintainX remains system of record for maintenance.
- FleetWatcher remains system of record for trucking.
- Motive remains system of record for fleet telemetry.
- Vista remains system of record for financials.

ForgedOps provides operational visibility only.

---

## Future Integration Fields

Reserve support for:
- MaintainX Reference
- FleetWatcher Reference
- Motive Reference
- Daily Report Reference
- Excavation Reference
- Safety Meeting Reference
- JHP Reference
- RFI Reference

Fields may exist before integration is active.

---

## Phase OA-1 Scope

**Allowed:**
- Create Action
- Assign Action
- Update Action
- Close Action
- View Action

**Not Allowed:**
- AI Routing
- Auto Assignment
- Auto Escalation
- Workflow Automation
- Predictive Logic
- Advanced Analytics

OA-1 must prove operational value before expansion.

---

## Definition of Success

A superintendent, foreman, PM, dispatcher, shop manager, or safety manager can:

1. Create an Operations Action in under 30 seconds.
2. Assign ownership.
3. Attach photos.
4. Track progress.
5. Know who owns it.
6. Close the loop.

If users naturally adopt the workflow, future integration phases may proceed.
