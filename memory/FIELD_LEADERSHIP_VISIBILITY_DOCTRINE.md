# FIELD LEADERSHIP VISIBILITY DOCTRINE

_Phase ODR-Governance Extension · Master Visibility Contract · 2026-05-29_

This document is the **master visibility contract** for the
platform. It governs what each Field Leadership Level (FLL) sees
across ODR, Constraints, Operational Timeline, Photos, Daily
Reports, Safety, Dispatch, Fleet, future RFI, future Schedule, PM
Portal, and FL Portal.

**Doctrine only. No implementation. No new roles. No new auth.
No new routes. No DB changes. Preserve existing security model.**

---

## 1 · Core philosophy (re-affirmed)

The platform must optimize for **Operational Relevance**, not
Maximum Visibility.

For every surface, the question is:

> *"What does this person actually need to run work successfully?"*

Not:

> *"Can this person access this?"*

The platform should never confuse **authorization** with
**operational utility**. A field leader may legally be allowed to
see something and still be best served by not seeing it.

### 1.1 Anti-patterns the doctrine forbids

- "Everyone sees everything"
- "More visibility is more value"
- "If they can access it, show it"
- "Hide nothing"
- "Show the entire timeline by default"
- Punitive scoring derived from visibility data (per O50)

### 1.2 The four visibility verbs

| Verb | Meaning |
|---|---|
| **FULL** | Complete record, all fields, raw data, edit / amend / approve where the role permits |
| **LIMITED** | Scoped subset — usually only the rows / fields relevant to this role's mission |
| **SUMMARY** | Aggregated · derivative · roll-up · trend · KPI — **never** raw per-record data |
| **NONE** | The data does not appear in this role's surfaces · the role does not learn the record exists |

These four verbs are the entire vocabulary of the visibility
contract. Every surface labels itself with one verb per FLL.

---

## 2 · The six Field Leadership Levels

The doctrine defines **six operational levels**. These are
**doctrinal labels, not new auth roles**. The existing
authentication model (`X-FL-Token` for Foreman/Super/Senior Super,
`X-PM-Token` for PM, `X-Admin-Token` for Admin / Operations
Leadership) is unchanged.

| Level | Doctrinal label | Underlying auth token |
|---|---|---|
| FLL-1 | Crew Lead / Foreman | `X-FL-Token` · Foreman tier |
| FLL-2 | General Foreman | `X-FL-Token` · GF tier (existing or expansion of Foreman tier scope · no new token) |
| FLL-3 | Superintendent | `X-FL-Token` · Super tier |
| FLL-4 | Senior Superintendent | `X-FL-Token` · Senior Super tier |
| FLL-5 | Project Manager | `X-PM-Token` |
| FLL-6 | Operations Leadership | `X-Admin-Token` with `operations_leader=true` directory mirror flag |

If at lock time the operator wishes to formalize FLL-2 as a
distinct tier, that becomes a downstream auth task — not a
doctrine change. The visibility contract works either way.

### 2.1 Mission · responsibilities · horizons

```
FLL-1 · Crew Lead / Foreman
  Mission:               execute today's work safely + productively
  Responsibilities:      crew · equipment · materials · production · safety today
  Operational focus:     this crew · this day · this project
  Decision horizon:      next hour to next shift
  Information horizon:   today + tomorrow
  Philosophy:            "Everything needed to run today's work."

FLL-2 · General Foreman
  Mission:               coordinate multiple crews on a project
  Responsibilities:      multi-crew readiness · material/equipment coordination
  Operational focus:     2–5 crews · this week · this project
  Decision horizon:      today + 2 days
  Information horizon:   3-day rolling window
  Philosophy:            "Keep the crews moving together."

FLL-3 · Superintendent
  Mission:               run the entire project
  Responsibilities:      full project · all crews · quality · safety · inspections
  Operational focus:     this project · this month
  Decision horizon:      next 2 weeks
  Information horizon:   project lifetime (operational record)
  Philosophy:            "The project command center."

FLL-4 · Senior Superintendent
  Mission:               coordinate multiple projects (regional)
  Responsibilities:      cross-project conflicts · resource competition · regional readiness
  Operational focus:     5–15 projects · this quarter
  Decision horizon:      next month
  Information horizon:   regional rolling history
  Philosophy:            "Operational optimization across projects."

FLL-5 · Project Manager
  Mission:               protect project execution
  Responsibilities:      cost · contract · procurement · change · risk
  Operational focus:     this project (financial / contractual lens)
  Decision horizon:      contract period
  Information horizon:   project lifetime + contract addenda
  Philosophy:            "Project execution defended on every flank."

FLL-6 · Operations Leadership
  Mission:               protect company execution
  Responsibilities:      company-wide risk · resource health · trends
  Operational focus:     all projects · all regions
  Decision horizon:      quarter to year
  Information horizon:   company history
  Philosophy:            "Signal. Not operational clutter."
```

### 2.2 Per-level visibility requirements + prohibitions

| FLL | Should see | Should NOT see |
|---|---|---|
| **FLL-1** | today's work · own crew/equipment/materials · own ODR · production · safety today · toolbox talks · own photos · relevant constraints · own action items · ODR guidance · readiness coaching | company financials · PM forecasting · schedule intelligence · company-wide metrics · executive dashboards · HR data beyond own crew · multi-project reporting · cost exposure |
| **FLL-2** | + multi-crew readiness · material coordination · upcoming work · equipment coordination · constraint summaries · production comparisons across own crews · crew readiness trends | PM financials · executive reporting · company exposure |
| **FLL-3** | + full ODR for all crews on project · constraints · operational timeline · utility conflicts · quality · safety · inspections · material/equipment forecasts · sub coordination · operational chronology · readiness metrics · future RFI visibility · future schedule impacts | other projects (unless explicitly assigned) · cost exposure (unless project is theirs) · executive aggregations |
| **FLL-4** | + cross-project conflicts · fleet competition · resource conflicts · regional readiness · shared manpower/equipment · constraint trends · ODR trends across regional projects | company-wide leadership aggregations (kept to FLL-6 by default) · cost exposure (FLL-5 lens) |
| **FLL-5** | cost exposure · contract documentation · ODR consumption (read-only) · constraints · forecasting · procurement · change management · future RFIs · future schedule intelligence · risk exposure | crew-level operational noise · per-foreman scoring · raw coaching prompts · FL Inbox edit/approve buttons |
| **FLL-6** | operational exposure (company-wide) · readiness · constraints · company risk · resource conflicts · project health · regional performance · ODR trends · safety trends | individual ODR record review · per-foreman scoring · per-row operational chatter |

---

## 3 · Master visibility verbs · cross-system

The detailed per-system matrix lives in
`ROLE_AWARE_OPERATIONAL_VISIBILITY_MATRIX.md` (Artifact 3 of this
phase). At-a-glance summary:

| System | FLL-1 | FLL-2 | FLL-3 | FLL-4 | FLL-5 | FLL-6 |
|---|---|---|---|---|---|---|
| ODR (own) | FULL | FULL | FULL | FULL | LIMITED | SUMMARY |
| Constraints | LIMITED | LIMITED | FULL | FULL | FULL | SUMMARY |
| Operational Timeline | LIMITED | LIMITED | FULL | FULL | LIMITED | SUMMARY |
| Photos | LIMITED | LIMITED | FULL | FULL | LIMITED | SUMMARY |
| Safety | LIMITED | LIMITED | FULL | FULL | LIMITED | SUMMARY |
| Dispatch / Fleet | LIMITED | LIMITED | FULL | FULL | LIMITED | SUMMARY |
| Daily / ODR Reports | LIMITED | LIMITED | FULL | FULL | LIMITED | SUMMARY |
| Meetings | LIMITED | LIMITED | FULL | FULL | LIMITED | SUMMARY |
| Inspections | LIMITED | LIMITED | FULL | FULL | LIMITED | SUMMARY |
| Incidents | SUMMARY | LIMITED | FULL | FULL | LIMITED | SUMMARY |
| Training | LIMITED | LIMITED | FULL | FULL | NONE | SUMMARY |
| Readiness | LIMITED (own) | LIMITED (crews) | FULL (project) | FULL (region) | SUMMARY | SUMMARY |
| Future RFIs | NONE | LIMITED | FULL | LIMITED | FULL | SUMMARY |
| Future Schedule | LIMITED (today/tom) | LIMITED (3-day) | FULL | FULL (regional) | FULL | SUMMARY |
| Operational Search | LIMITED (own scope) | LIMITED (own crews) | FULL | FULL (region) | FULL | SUMMARY |
| Field Memory | LIMITED (own) | LIMITED (own crews) | FULL | FULL | LIMITED | SUMMARY |

Each cell has detailed rationale in
`ROLE_AWARE_OPERATIONAL_VISIBILITY_MATRIX.md` § 3.

---

## 4 · Doctrine statements (V1–V20 · master visibility)

| # | Statement |
|---|---|
| V1 | Visibility is governed by **operational relevance**, not by raw access permission. |
| V2 | Every surface labels itself FULL · LIMITED · SUMMARY · NONE per FLL — never silently mixed. |
| V3 | The contract has six FLL levels (FLL-1 through FLL-6) — no new auth roles introduced. |
| V4 | "More visibility" is not a goal. Every added field on a role's surface bears the burden of proof. |
| V5 | Cross-role data leakage is forbidden — a surface for FLL-N must never expose data the doctrine assigns NONE/SUMMARY to FLL-N. |
| V6 | PM (FLL-5) sees **different** information from Superintendent (FLL-3), not **more**. |
| V7 | Operations Leadership (FLL-6) sees **signal**, not operational clutter. |
| V8 | Foreman (FLL-1) is shown **today + tomorrow**. Anything past tomorrow's plan is doctrinally out of scope. |
| V9 | Timeline visibility prevents three failures: timeline overload, permission leakage, operational noise. |
| V10 | Coaching telemetry is never used as performance review evidence (anchored from O50). |
| V11 | Aggregations (SUMMARY) never carry per-foreman or per-individual dimensions. |
| V12 | Field Memory follows the same visibility verbs as the records it stores. Memory cannot escalate visibility. |
| V13 | RFI visibility tracks the work — author + project team see, FLL-3 manages, FLL-5 owns response. |
| V14 | Schedule visibility tracks operational horizon — FLL-1 sees today+tomorrow, FLL-3 sees lookahead, FLL-5 sees critical path. |
| V15 | Constraints visible at FLL-1/FLL-2 are filtered to **relevant** constraints (the foreman's work / area / crew). |
| V16 | Senior Super (FLL-4) lens is **regional optimization**, not company-wide reporting. |
| V17 | A role's surfaces should answer the question *"What do I need to run my work successfully?"* without scrolling past irrelevant content. |
| V18 | The visibility contract is **doctrinal**, not technical. Auth still enforces; doctrine governs UX restraint and projector selection. |
| V19 | Every future system (Search · RFI · Schedule · Memory · AI) must reference this doctrine before adding a per-role surface. |
| V20 | Visibility changes require a doctrine revision, not a code change. |

V1–V20 extend the locked O1–O50 doctrine inventory. Total: **70
locked doctrines.**

---

## 5 · How this doctrine interacts with existing security

This doctrine is **additive and restrictive**, never permissive.

- **Auth** still determines who is *allowed* to access an endpoint
  (X-FL-Token / X-PM-Token / X-Admin-Token + Phase K hardening).
- **Doctrine** determines what the UI / projector surfaces *to that
  role*, even when auth would technically permit more.
- A role can never gain *additional* access via doctrine. A role
  may have access *withheld* by doctrine — even when the underlying
  collection is reachable — because the doctrine deems it noise.

Concrete consequences:

- An FLL-1 Foreman with `X-FL-Token` could in principle hit
  `/api/odr/...` for their own ODR (auth permits) — and they will.
  But the FL Portal **does not** render a surface listing other
  crews' ODRs, even though the same auth principal could
  technically fetch them. The list endpoint scopes to own-records.
- An FLL-5 PM with `X-PM-Token` can call PM ODR consumption
  endpoints (auth permits) — and they will get **aggregated** data
  per V11, even though raw data is technically in the database.
- An FLL-6 leader could in principle drill into any project — the
  doctrine instead surfaces **SUMMARY** views by default, and any
  deep-drill is logged for governance.

The visibility doctrine is enforced primarily at the **projector
layer** (server-side query shapes) and the **UI layer** (which
surfaces render which views). Auth remains the bottom-line
safeguard against permission escalation.

---

## 6 · Per-system visibility chapters

See companion artifacts:

- `ROLE_AWARE_OPERATIONAL_VISIBILITY_MATRIX.md` — per-system × per-FLL detailed matrix with rationales
- `TIMELINE_ROLE_VISIBILITY_STANDARD.md` — timeline-specific rules
- `FUTURE_RFI_VISIBILITY_MODEL.md` — RFI per-FLL contract
- `FUTURE_SCHEDULE_VISIBILITY_MODEL.md` — Schedule per-FLL contract
- `ODR_VISIBILITY_ALIGNMENT_REPORT.md` — ODR compliance check against this doctrine
- `VISIBILITY_CERTIFICATION.md` — final operator-readable certification

This doctrine document is the **master**; companion artifacts
implement it for specific systems.

---

## 7 · Governance hooks

| Hook | Description |
|---|---|
| `verify_visibility_doctrine_probe.py` *(planned)* | grep + integration check that no FLL-N surface renders data marked NONE/SUMMARY for that FLL |
| Visibility audit log *(uses existing `odr_section_events`)* | per-record deep-drill from FLL-6 surfaces is logged |
| Doctrine review cadence | quarterly · operator + leadership; visibility changes require doctrine revision (V20) |

---

## 8 · Stop condition honoured

- ✅ No implementation
- ✅ No new roles · no auth changes · no permission code
- ✅ No portal · DB · or route changes
- ✅ Existing security model preserved verbatim
- ✅ Doctrine only

_End of Field Leadership Visibility Doctrine · master contract._
