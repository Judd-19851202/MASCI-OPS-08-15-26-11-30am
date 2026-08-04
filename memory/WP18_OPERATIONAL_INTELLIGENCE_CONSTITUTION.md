# WP-18 Operational Intelligence Constitution

Date: 2026-08-04

## Constitutional status

**Decision label:** `APPROVED_CONSTITUTIONAL_DECISION`  
**Proof label:** `EXECUTIVE_DIRECTIVE`

This document is a **standing constitutional layer** for ForgedOps.

It is not guidance.
It is not optional.
It is not package-local.

It applies to:

- all remaining WP-18 work packages
- every later work package after WP-18
- every implementation, audit, redesign, enhancement, migration, certification, and governance decision

Unless a later executive constitutional amendment explicitly supersedes it, the platform automatically inherits:

1. the **WP-17 Product Constitution**
2. the **WP-18 Executive Constitutional Architecture Package (ECAP)**
3. the **WP-18 Operational Intelligence Constitution**
4. the **WP-18 Operational Decision Engine Constitution**

This constitution is now complemented by the **WP-18 Operational Decision Engine Constitution**, which carries the governed decision-pipeline, metric-engine, explanation-engine, and continuous-improvement requirements.

## Executive purpose

The purpose of WP-18 is **not** to build more forms, tables, or databases.

The purpose of WP-18 is to build the industry’s most intelligent heavy civil operations platform.

Every subsystem implemented after WP-18C5 must:

- increase operational intelligence
- reduce duplicate entry
- strengthen source-of-truth governance
- improve executive decision-making

If a proposed feature only stores information without improving operational understanding, automation, or decision quality, it shall **not** be implemented without explicit executive approval.

## Permanent constitutional principles

### 1. Capture Once → Reuse Everywhere

Every operational fact shall be entered one time.

After capture, the platform shall automatically connect that fact to every downstream workflow that legitimately requires it.

The operator must never be asked to re-enter the same operational information.

### 2. Every Fact Has One Authoritative Owner

Each operational fact shall have one authoritative owner.

Examples of fact classes that must remain singularly owned:

- Project Identity
- Budget
- Customer Pay Item
- Internal Work Type
- Cost Code
- Work Package
- Schedule Activity
- Daily Report
- Crew
- Equipment
- Material
- Vendor
- Constraint
- Production
- Safety
- QA/QC

Every other system consumes those facts.
Nothing duplicates them.

### 3. Operational Intelligence Over Data Collection

Every future subsystem shall answer questions operators cannot easily answer today.

If the platform cannot answer better questions after a package is complete, the package is incomplete.

### 4. Build Digital Twins, Not Databases

The platform shall continuously construct a live operational digital twin of every project.

Every project should know:

- what was planned
- what actually happened
- who performed it
- where
- when
- why
- what resources were consumed
- what constraints existed
- what changed
- what should happen next

without duplicate data entry.

### 5. AI Advises — Humans Govern

AI may:

- summarize
- recommend
- explain
- predict
- detect anomalies
- identify trends
- prioritize review
- draft reports

AI may never silently:

- approve
- certify
- activate
- authorize
- change financial truth
- change schedule truth
- change production truth

### 6. Preserve Trust Lines

Every implementation must preserve explicit trust lines from fact capture to derived readers, approvals, and executive reporting.

No derivative reader may quietly become the write owner of upstream truth.

### 7. Zero Duplicate Operational Truth

No package may introduce a second authoritative record for the same operational fact.

Where historical systems, derived readers, or compatibility lanes exist, the constitutional response is:

- preserve source
- identify the owner
- route all downstream consumption through the owner
- queue unresolved ambiguity for governed review

### 8. Every Package Must Make the Platform Smarter

Every remaining package must measurably increase:

- operational awareness
- automation
- data reuse
- executive visibility
- prediction quality
- decision quality

while reducing:

- duplicate entry
- manual reconciliation
- spreadsheets
- disconnected reports
- operator workload

### 9. Every New Feature Must Reduce Operator Work

If a new feature adds operator burden without adding downstream reuse, automation, or decision value, it is constitutionally deficient.

### 10. Every New Capability Must Increase Executive Visibility

Every new capability must improve the executive ability to understand:

- status
- drift
- cause
- risk
- confidence
- recommended action

### 11. Every Operational Fact Must Flow Automatically Through the Platform

Every legitimate downstream consumer should receive the fact automatically through governed relationships, not manual re-entry or spreadsheet transfer.

### 12. No Feature Is Complete Until It Creates Downstream Value

A feature is incomplete if it only captures data.

Completion requires downstream operational value, trust value, automation value, or executive value.

## Operational digital twin law

ForgedOps shall continuously build a live operational digital twin for every project.

This means every work package must strengthen the platform’s understanding of:

- plan
- actual
- resource use
- constraints
- cost
- production
- performance
- forecast readiness
- executive explanation

## Resource intelligence law

The system shall understand resources, not merely list them.

### Employees

The platform should learn and expose:

- crews
- experience
- production trends
- certifications
- workload
- availability
- strengths

### Crews

The platform should learn and expose:

- stable membership
- temporary crews
- production
- safety
- quality
- schedule performance
- cost performance
- workload

without requiring HR to constantly rebuild crews manually.

### Equipment

The platform should learn and expose:

- utilization
- idle time
- standby
- production
- ownership cost
- operating cost
- maintenance trends

### Materials

The platform must distinguish and understand:

- ordered
- committed
- delivered
- installed
- wasted
- returned
- transferred
- remaining

Delivered must never be confused with installed.

### Vendors / Subcontractors

The platform should understand:

- workload
- commitments
- production
- quality
- safety
- responsiveness
- schedule performance
- financial exposure

## Automatic relationships law

Every Work Block should become the center of operations.

It should automatically connect:

- Budget Line
- Customer Pay Item
- Internal Work Type
- Internal Cost Code
- Work Package
- Schedule Activity
- Crew
- Employees
- Equipment
- Materials
- Vendor / Subcontractor
- Photos
- Constraints
- Safety
- QA/QC
- Documents
- Daily Reports
- AI Summary

No manual cross-linking is constitutionally preferred.

## Production intelligence law

The platform should automatically derive:

- production / hour
- production / day
- production / week
- production / crew
- production / equipment
- production / employee
- production / work package
- production / activity
- production / pay item
- production / cost code

without asking users to calculate anything.

## Cost intelligence law

The platform should automatically derive:

- labor cost
- equipment cost
- material cost
- subcontract cost
- total cost
- cost / unit
- cost / day
- cost / week
- cost / activity
- cost / work package
- cost / pay item

## Crew economics law

The platform must eventually be able to answer inside the product:

- What does Crew A actually cost us?
- What does Crew A actually produce?
- Is Crew A profitable?
- What changed?

No spreadsheets.
No exports.
Inside the platform.

## Forecast intelligence law

Before C7 forecasting is complete, the platform should already be capturing the evidence needed to understand:

- production trends
- schedule trends
- crew trends
- equipment trends
- cost trends
- material trends
- subcontract trends

## Executive intelligence law

The platform must eventually let executives ask:

- Why is Project 241 behind?

The system should answer with:

- explanation
- evidence
- source trail
- confidence
- recommendations

not merely charts.

## Enforcement standard

No future package may receive a final **GO** unless it evaluates itself against this constitution and proves:

1. which facts it captures or consumes
2. who owns those facts
3. how duplicate entry was reduced
4. what downstream automation was created
5. what operational intelligence was added
6. what executive visibility was improved
7. how AI stayed advisory
8. which trust lines were preserved
9. what downstream value proves the package is complete

## Final executive directive

ForgedOps is not merely building software.

It is building the operational nervous system for a heavy civil contractor.

Every employee should capture information naturally as part of doing the job.
Every manager should gain understanding instead of more paperwork.
Every executive should receive trusted answers instead of disconnected reports.
Every operational fact should become part of a continuously improving digital twin that powers planning, execution, production, financial control, forecasting, and executive decision-making.

Nothing less is acceptable.
