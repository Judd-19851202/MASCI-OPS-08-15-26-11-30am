# OPERATIONAL_COGNITION_HEATMAP.md
**Phase 19 · iter415 · 2026-05-25**

Where users most likely hesitate, pause, misunderstand, or lose continuity — ranked by cognition load (🔴 HIGH · 🟠 MEDIUM · 🟢 LOW). This map is the gating document for "what to coach next" if the Day-1 debrief surfaces friction.

## Cognition load scoring
**🔴 HIGH** — user is making a consequential, hard-to-undo decision · or interpreting state that affects downstream work
**🟠 MEDIUM** — user is performing a routine task but with > 3 fields or branching options
**🟢 LOW** — user is reading or executing a single-tap action

## Dispatch role heatmap
| Surface | Load | Why | Coaching present? |
|---|:---:|---|:---:|
| Assignment Create Drawer (Material) | 🟠 | 7-field form · branching by haul type · "Add temporary" decision | ✅ inline + iter414 link |
| Assignment Create Drawer (Tanker) | 🔴 | 27-product catalog · plant vs terminal distinction · field crews depend on accuracy | ✅ inline + iter414 link |
| Assignment Create Drawer (Equipment Move) | 🔴 | equipment ID lookup · pickup/dropoff differs from material flow | ✅ inline + iter414 link |
| DispatchHub Operational Attention cards | 🟠 | exception interpretation · reassign vs hold decision | ✅ hint text + iter414 link |
| DispatchBoard row tap → context drawer | 🟠 | full assignment state + history · cognitive density | 🟡 partial (no iter414 link from drawer · backlog) |
| DispatchHub Follow-Through (transfers vs holds) | 🟠 | doctrine choice (HOLD vs TRANSFER) corrupts utilization if wrong | ✅ via portal-dispatch article |
| Mid-shift reassignment | 🔴 | walks state machine back · operationally consequential | 🟡 doctrine-only · no in-flow coaching |
| Health summary interpretation (admin) | 🟢 | 3-word status · self-explanatory | ✅ iter414 link |

## Driver role heatmap
| Surface | Load | Why | Coaching present? |
|---|:---:|---|:---:|
| QR scan → `/shift` landing | 🟢 | one-tap action | ✅ EN+ES on QR sticker |
| Shift Start form (4 fields) | 🟠 | first-time drivers; SearchableSelect novelty | ✅ subtitle + iter414 link |
| "Add temporary driver" affordance | 🟠 | sub/rental driver scenario · ambiguity about record creation | 🟡 partial · doesn't explain memory-feedback loop |
| Lifecycle tap loop | 🟠 | choosing the right wait reason matters | ✅ button labels are operational |
| BREAKDOWN tap | 🔴 | consequential · fans to 4 portals | ✅ button is clearly labeled |
| Sign out at end of shift | 🟢 | one-tap | ✅ |

## PM role heatmap
| Surface | Load | Why | Coaching present? |
|---|:---:|---|:---:|
| PmHaulActivityTile glance | 🟢 | read-only · refreshes every 60s | ✅ subtitle + read-only pill + iter414 link |
| DispatchLifecycleTile (scope=pm) read | 🟢 | project-scoped read-only | ✅ via iter396 |
| Daily Report scope filter | 🟢 | auto-scoped to PM's assigned projects | ✅ |
| Adding a co-PM to a project | 🟠 | admin task · low frequency | 🟡 admin guidance only |

## Shop role heatmap
| Surface | Load | Why | Coaching present? |
|---|:---:|---|:---:|
| iter396 BREAKDOWN tile glance | 🟢 | one-line read | ✅ |
| Pre-Op fail → sign-off decision | 🟠 | needs-attention vs OOS judgment | ✅ via shop training articles |
| Equipment master mutations | 🟠 | admin-adjacent · low frequency | ✅ via shop guides |

## Safety role heatmap
| Surface | Load | Why | Coaching present? |
|---|:---:|---|:---:|
| Incident submission | 🟠 | required-field validation · low frequency | 🟡 legacy form chrome (P2) |
| CAPA creation | 🟠 | lifecycle-driven · iter356 covers it | ✅ |
| Safety meeting builder | 🟠 | multi-step · low frequency | 🟡 pre-LifecycleGuide |
| Fire extinguisher inspection log | 🟢 | per-unit single-tap | ✅ |
| Safety training records | 🟢 | per-employee read | ✅ via iter353 |

## HR role heatmap
| Surface | Load | Why | Coaching present? |
|---|:---:|---|:---:|
| Driver Qualification dashboard | 🟢 | read-only · status columns are intuitive | ✅ via iter317 |
| HR Employee Accountability timeline | 🟠 | cross-source aggregation · density | ✅ via iter353a |
| Time Verification | 🟠 | week-ending logic · CSV export | 🟡 legacy chrome (P3) |
| Training Records management | 🟠 | per-employee per-track | 🟡 legacy chrome (P3) |
| Payroll Variance review | 🟠 | data interpretation | 🟡 partial |
| HR user/FL-user/Safety-user/Shop-user issuance | 🟠 | password delivery options decision | ✅ via admin-people doc |

## Field Operations heatmap
| Surface | Load | Why | Coaching present? |
|---|:---:|---|:---:|
| `/field` Field Tile landing | 🟢 | 4 operational lanes · clearly labeled | ✅ via iter404 |
| Daily Report submission | 🟠 | end-of-day form · multiple sections | 🟡 legacy chrome (P2) |
| Equipment Pre-Op | 🟠 | OSHA-compliance items · fail/pass per item | 🟡 legacy chrome (P2) |
| DVIR submission | 🟠 | OSHA-required for trucking · fail/pass per item | 🟡 legacy chrome (P2) |
| Weekly Lead Inspection | 🟠 | leadership-only · cognitive density | 🟡 legacy chrome (P3) |
| JHA reading | 🟢 | reference-only · printable | ✅ |

## Ranked top-10 hesitation points (across all roles)
1. **🔴 Mid-shift reassignment** (dispatch) · doctrine-only · no in-flow → 🟠 P2 closure
2. **🔴 Tanker drawer** (dispatch) · already coached + iter414 link → ✅ closed
3. **🔴 Equipment Move drawer** (dispatch) · already coached + iter414 link → ✅ closed
4. **🔴 Driver BREAKDOWN tap** · already coached → ✅ closed
5. **🟠 "Add temporary" affordance** · partial · doesn't explain memory loop → 🟠 P2 closure
6. **🟠 DispatchBoard row tap → context drawer** · no in-flow help → 🟠 P2 (Phase 18.1 deferred)
7. **🟠 Daily Report submission** (field) · legacy chrome · no LifecycleGuide → 🟠 P2
8. **🟠 Incident submission** (safety) · legacy chrome · no LifecycleGuide → 🟠 P2
9. **🟠 Time Verification** (HR) · legacy chrome → 🔵 P3
10. **🟠 Safety meeting builder** · legacy chrome → 🔵 P3

## Verdict
**4 of the 5 highest-cognition checkpoints are already coached** with Phase 18 in-flow links. The 1 remaining HIGH-load uncoached surface (mid-shift reassignment) is documented in doctrine but not in-flow — captured as P2 backlog. The other 5 MEDIUM-load gaps are concentrated in legacy modules and follow the standard legacy-modernization recipe.
