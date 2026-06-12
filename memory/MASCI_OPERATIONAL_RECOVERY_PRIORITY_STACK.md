# MASCI Operational Recovery — Priority Stack (Track 13.4C · Deliverable #1)

**Lens:** "What makes MASCI *operators* better tomorrow?"  
**Out of scope:** anything that exists only to help Customer #2 onboard. Those live in `FORGEDOPS_PRODUCTIZATION_PRIORITY_STACK.md`.  
**Mode:** decision framework only · no implementation · no design.

---

## Tier 1 — Operational Trust Threats (MASCI today)

| # | Finding | Why it matters to MASCI operators |
|---|---|---|
| 1 | **D-01 Production Motive webhook unverified** | Dispatch is the platform's operational truth surface. If MASCI dispatchers can't trust the live feed, the entire portal degrades to a "looks-modern dashboard" — operators silently revert to phone calls and texts. |
| 2 | **D-03 100 of 190 motive-mapped assets have no GPS coords** | A dispatcher cannot make routing or recovery decisions about 53 % of the fleet from the map. Trust collapses the first time a dispatcher needs to find unit X and unit X isn't on the map. |
| 3 | **D-04 157 assets stale / no-recent** | Same trust failure mode; widens the "fog of war" beyond what dispatchers can mentally compensate for. |
| 4 | **T-01 Safety-Critical UI Spanish readiness 75.8 %** | Spanish-speaking crew members make safety calls (trench, JHA, CAPA, OSHA). 100 of those strings currently fall through to English. Each is a tiny safety risk. |
| 5 | **T-08 / T-09 Outbound emails & PDFs 0 % Spanish** | Equipment-issuance PDFs, training certificates, FL records, and notification emails all reach Spanish-first crew in English-only form. The lone exception is Safety Equipment Issuance form's inline EN+ES legal text. |
| 6 | **V-11 Status verb overload** (`offline`, `active`, `open` each mean ≥3 different things) | An operator switching between Dispatch, HR, and Safety has to context-switch what "offline" means. Cognitive load increases. |
| 7 | **V-12 Closure verb drift** (`closed`, `done`, `signed_off`, `final`, `success`, `approved`, `receipted`) | "Did I close that?" — operator must look up which verb applies for which workflow. |
| 8 | **R-06 OperationsActionsTile still on 6 portals** | Cross-portal language ("Operations Actions") competes with each role's native language. HR cleanup in Track 13.4A is the proof-of-concept; the other 6 portals still carry the drift. |
| 9 | **R-02 Daily Report / Site Inspection / Incident overlap** | Foremen re-enter the same photos, crew, and narrative across 3 forms when one event spans them. Real productivity cost. |
| 10 | **V-15 Driver portal landing missing** | Drivers do not have a static "today" landing; tokenized URLs only. The driver audience is genuinely missing a surface. |

## Tier 2 — Major Productivity Threats

| # | Finding | Why it matters to MASCI |
|---|---|---|
| 11 | **V-09 / R-03 Eight `*CommandCenter` pages** | Operators navigate between Admin, PM, Dispatch, Operations, ODR, Trench, Guidance, Training command centers with overlapping signals. |
| 12 | **R-01 Eight auth-flow variations** | 7 per-portal logins + master Sign-In is 8 places to maintain — and 8 places an operator has to remember. |
| 13 | **V-07 Status-chip sprawl (15 components)** | The same status appears in 15 different visual treatments depending on which page. |
| 14 | **R-04 Four overlapping admin health pages** | Admin oversight signal is split across Persistence · Production · Stability · Cluster Capacity. |
| 15 | **R-05 `AdminCompliance` + `AdminComplianceFindings`** | Two compliance pages for what reads like one workflow. |
| 16 | **R-07 PO digest can duplicate per-action PO email** | Recipient sees the same PO twice. |
| 17 | **V-05 / V-06 Hub-size & header variance** | 4.6× variance across portal hub files; ≥ 4 header strategies. Maintenance overhead now; tenant cloning overhead later. |
| 18 | **T-02 Field-Critical UI Spanish gap (82.5 %)** | 126 strings fall through to English — labels, button text, error messages. Each adds friction for Spanish-first crew. |
| 19 | **T-03 Workflow-Critical UI Spanish gap (82.5 %)** | Submit / approve / close labels — workflow completion friction. |
| 20 | **T-12 Status verb translation 0 %** | Status verbs never reach `t()`. Even existing ES dictionary entries cannot fire. |
| 21 | **D-06 67 circle geofences render as 0** | Operators relying on geofence-based alerts get nothing today. |
| 22 | **T-04 Public-Facing UI Spanish gap (73.6 %)** | Public posters, QR pages, cheatsheet, public-form chrome — lowest Spanish readiness for highest-stranger audience. |
| 23 | **V-13 Mobile evidence gap** | Most portals lack iPad / phone-viewport visual evidence; field uses mobile. |

## Tier 3 — Optimisation

Includes all V-01 / V-02 / V-03 (theme drift), V-10 (status case drift), R-09 (1,146 unused ES keys), R-15 (`guidance_search_misses` invisible), D-05 / D-07 / D-08 / T-05 / T-06 / T-07.

---

## Tier-1 explanation — what success looks like for MASCI operators

These ten items, addressed together, would:
- Make Dispatch a *trusted* surface, not a "modern-looking dashboard" (D-01 / D-03 / D-04).
- Reduce safety risk for Spanish-speaking crew (T-01 / T-08 / T-09).
- Eliminate cognitive load from cross-portal status drift (V-11 / V-12).
- Honour the role-first portal pattern proven in Track 13.4A's HR cleanup (R-06).
- Save foremen the duplicate-data-entry tax (R-02).
- Give Drivers a "today" surface they don't have (V-15).

No solutions are proposed here. This stack is purely the ranking lens.
