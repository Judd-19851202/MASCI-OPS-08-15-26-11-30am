# TRACK 20.1 · Navigation & Click Audit

## Current employee-lookup workflows (pre-promotion)
| Workflow                                                   | Current path                                                                                     | Clicks |
|------------------------------------------------------------|--------------------------------------------------------------------------------------------------|:------:|
| HR — Is employee employment-ready?                          | HR Hub → search employee → Accountability tile → Accountability timeline                          | 4      |
| Safety — Can employee work today safely?                    | Safety Hub → Incident search → cross-reference to HR Accountability                              | 5      |
| Transportation — Can employee drive today?                  | Dispatch → Driver Qualification list → cross-reference to HR Accountability                       | 4      |
| PM — Can employee work this project?                        | PM CC → Field Leadership records → cross-reference to HR                                          | 5      |
| Superintendent — What do I need before assigning?           | Field Leadership → search employee → cross-reference to HR                                        | 5      |
| Executive — Is employee operationally healthy?              | Admin → OI Cockpit → HR Intelligence drill → nothing employee-level                               | 5+     |

## Post-promotion (Track 19.56 scope, not this audit)
Every persona reaches the SAME URL: `/hr/employees/:id/accountability`
(already exists). The visual is upgraded to the Universal Thread
shell + OI Attention Strip + Guidance Card modal. Click count drops:

| Workflow                                                   | Path (post-promotion)                                              | Clicks |
|------------------------------------------------------------|---------------------------------------------------------------------|:------:|
| Any persona · read employee readiness                       | Employee Combo search → open Thread → read Section 1 Mission Overview | **2**  |
| Any persona · open attention item                           | Thread → Section 2 chip → Guidance Card                             | **2**  |
| Any persona · check driver-qualification                    | Thread → Section 4 timeline filter `driver`                          | **2**  |
| Any persona · read timeline                                 | Thread → Section 4 (already loaded)                                  | **1**  |
| Any persona · export PDF brief                              | Thread → Download button                                             | **1**  |

## Portal-switches eliminated
- Safety no longer bounces to HR to check accountability — the Accountability endpoint already surfaces safety incidents when the caller is authorised.
- Transportation no longer bounces to HR for driver qualification — same endpoint returns Driver-Qualification category events.
- PM no longer bounces to HR for Field Leadership recognition — same endpoint returns Field-Leadership category events.

## Verdict
🟢 **Click count already low today; universal Thread visual + OI strip
promotion will reduce it further without any backend change.**
