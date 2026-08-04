# WP18CX Executive Operator Language Dictionary

## Status
- Package: `WP-18CX`
- Role in governance: **primary operator-language authority** for all WP-18CX refinements and all future packages inheriting the WP-17 / WP-18 constitutional stack
- Scope: operator-facing UI, navigation, cards, KPIs, tables, filters, coaching, exports, PDFs, emails, notifications, AI explanations, mobile, and executive dashboards
- Non-scope: backend service names, API contracts, database models, code identifiers, logs, diagnostics, and constitutional/internal architecture documentation

## Constitutional rule
All operator-facing language must sound like it belongs inside an elite heavy-civil construction company.

The platform may preserve internal technical naming in code and governance artifacts, but operator-facing surfaces must:
1. use construction-first language
2. make decisions easier
3. remove developer shorthand
4. preserve one canonical term per concept
5. preserve C1–C6 trust lines without exposing technical wording unnecessarily

## Standing language principles
1. **Construction first** — prefer job, crew, field, production, budget, schedule, work, delay, recovery, and risk language.
2. **Decision first** — wording must help the operator decide what happened, why it matters, what to do, who owns it, and what happens if nothing changes.
3. **One concept, one term** — no synonyms for the same operating concept across pages or channels.
4. **Operator-safe explainability** — sources, evidence, confidence, and drill-down paths stay visible, but phrased in operator language.
5. **Smallest safe repair** — rewrite labels and coaching before restructuring flows.

## Canonical replacements

| Technical / prohibited surface term | Approved operator term | Notes |
|---|---|---|
| Governed Metric Engine | Project Performance | Internal-only term must not appear on operator surfaces |
| Operational Intelligence Governance | Operations Dashboard Review | Admin oversight surface |
| Operational Intelligence | Project Performance | PM / project-facing wording |
| Executive Operational Intelligence | Executive Operations Dashboard | Executive-facing wording |
| Governed review queue | Items Needing Review | Canonical review wording |
| Review queue pressure | Items Needing Review | Never show “pressure” to operators |
| Orphan events | Unassigned Records | Use where the record has not been linked |
| Snapshot | Current Project View / Current Portfolio View | Use based on page scope |
| Backfill | Update Existing Records | Use for additive repair / reconciliation runs |
| Governed mappings | Approved Work Type Links | PM surface |
| Governed work blocks | Work Blocks | Work Block remains canonical object name |
| Governed import | Import for Review | PM/admin import workflow wording |
| Schedule actual candidate | Proposed Progress Update | PM / Daily Report wording |
| Actual-cost candidate | Receipt Needing Review | Budget wording |
| Commitment candidate | PO Link Needing Review | Budget wording |
| Derived | Built from / Calculated from / Prepared from | Choose by context |
| Authority contract | Data Rules | Operator-safe explanation wording |
| Preserved source | Original Source | Import-review wording |
| Suggestion | Suggested Match | Import-review wording |
| Limitations | Watchouts | Metric/recommendation wording |
| Override | Different Field Decision | Prefer action language |
| Candidate evidence | Proposed Update Evidence | Review wording |

## Approved navigation standards
- PM route labels
  - `Project Controls`
  - `Project Budget`
  - `Project Schedule`
  - `Project Performance`
- Admin governance labels
  - `Project Controls Standards`
  - `Project Budget Review`
  - `Project Schedule Review`
  - `Operations Dashboard Review`
- Executive labels
  - `Executive Operations Dashboard`
  - `Enterprise Operations Center`
  - `Monday Morning Briefing`

## Approved KPI naming conventions
- `Approved events` → `Verified Field Updates`
- `Open recommendations` → `Recommended Actions`
- `Review queue open` → `Items Needing Review`
- `Orphan events` → `Unassigned Records`
- `Production velocity` → `Production Pace`
- `Governed resource intelligence` → `Resource Performance`
- `Confidence` → `Confidence`
- `Freshness` → `Updated`
- `Drill-down` → `Drill-down`

## Approved coaching language
Coaching must be:
- concise
- contextual
- operational
- action-oriented
- calm under ambiguity

Approved coaching patterns:
- “Here is what changed.”
- “This matters because …”
- “Take this next step …”
- “Owner: …”
- “If nothing changes …”
- “Built from Daily Reports, work blocks, approved progress updates, budget lines, and schedule activities.”

Disallowed coaching patterns:
- tutorial-heavy instructions
- architecture explanations that do not help a decision
- AI self-promotion
- technical process narration
- repeated warnings that add no action

## Approved AI explanation terminology
- `Recommended action`
- `Why it matters`
- `Confidence`
- `Evidence`
- `Source`
- `Drill-down path`
- `Owner`
- `Watchouts`
- `Different field decision`

Do not use:
- `model output`
- `heuristic pass`
- `engine payload`
- `inference lane`
- `computed object`

## Role-specific approved vocabulary

### Executive
- portfolio
- leadership attention
- money risk
- production risk
- recovery plan
- current portfolio view
- briefing readiness

### Operations Manager / Project Executive / Project Manager
- job
- crew
- cost
- schedule
- work package
- work block
- delay
- recovery
- next action
- item needing review

### Superintendent / Foreman
- today’s plan
- field progress
- work block
- installed quantity
- crew hours
- equipment use
- material movement
- hold-up / delay

### Dispatch / Shop / Equipment
- move
- assignment
- readiness
- repair
- utilization
- receiving
- delivery

### HR / Safety
- training
- onboarding
- incident
- finding
- compliance
- accountability

## Prohibited developer terminology on operator surfaces
- engine
- payload
- record hydration
- orphan
- canonicalization
- normalization
- parser
- schema
- event contract
- mutation
- serialization
- thread worker
- asynchronous task
- API response

## Prohibited database terminology on operator surfaces
- collection
- ObjectId
- row_id
- import_id
- review_id
- payload key
- source_record_id
- foreign key
- document version

## Prohibited engineering jargon on operator surfaces
- extension lane
- runtime-certified
- advisory-only lane
- additive authority
- detached worker
- inference
- compatibility backfill
- drill payload
- lineage pressure

## Exceptions
The following terms are constitutionally allowed because they are already operator-valid in construction operations:
- Work Block
- Daily Report
- Schedule
- Budget
- Lookahead
- Constraint
- Forecast
- Baseline
- Current
- Approved
- Deferred
- Confidence

## Operator-facing naming lock
From WP-18CX forward:
- `Work Block` remains canonical
- `Items Needing Review` is the only approved review-queue label
- `Project Performance` is the only approved PM term for the C6 experience
- `Operations Dashboard Review` is the approved admin review label for the C6 oversight surface
- `Executive Operations Dashboard` is the approved executive label for portfolio C6 visibility
- `Update Existing Records` is the approved operator-facing wording for additive repair/reconciliation runs

## Certification use
Every WP-18CX artifact, copy refinement, navigation change, coaching refinement, and GO/NO-GO conclusion must trace back to this dictionary.