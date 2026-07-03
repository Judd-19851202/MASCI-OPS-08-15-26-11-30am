# TRACK 19.56 · Promotion Map

Every Universal Thread section → certified payload field used.

| # | Section (Universal Thread)  | Adapter                    | Source payload path                                                    |
|---|-----------------------------|----------------------------|------------------------------------------------------------------------|
| 1 | Mission Overview             | `missionAdapter`           | `employee.*` + `current_state.*` · plain-English "Why: …" derivation   |
| 2 | Attention                    | `attentionAdapter`         | `expired_items[]` (CRITICAL) + `expiring_within_90d[]` (HIGH)          |
| 3 | Operational Guidance         | shell (unchanged)          | `hr_intelligence` row from `/operational-intelligence/summary`         |
| 4 | Timeline                     | `timelineAdapter`          | `events[]` (category → kind mapping)                                    |
| 5 | Relationships                | `relationshipAdapter`      | `employee.supervisor` · `employee.crew` · `employee.trade`             |
| 6 | Documents                    | shell empty                | Honest empty — corrections happen in owner portal                       |
| 7 | Photos                       | shell empty                | Honest empty — no employee-photo endpoint surfaced today                |
| 8 | Operational Intelligence     | shell (unchanged)          | `hr_intelligence` row from `/operational-intelligence/summary`         |
| 9 | History                      | shell empty                | Honest empty — HR historical snapshots not surfaced by this endpoint    |
|10 | Audit                        | shell empty                | Honest empty — read-only presentation of certified events               |

## Universal Action Queue (max 5)
Derived from `expired_items` + `expiring_within_90d` + incident count.
Shell enforces the cap.

## Category → Timeline kind map (used by `timelineAdapter`)
| Accountability category | Timeline `kind` |
|-------------------------|-----------------|
| Training                | `history`       |
| PPE & Equipment         | `assignment`    |
| Incidents               | `incident`      |
| Field Leadership        | `safety`        |
| HR Lifecycle            | `history`       |
| Driver Qualification    | `inspection`    |

## Cross-navigation
- Classic → Thread: `data-testid="acct-open-thread-link"` on the classic Accountability page.
- Thread → Classic: `data-testid="hr-employee-thread-classic-link"` on the promoted Thread page.

Both routes coexist. Neither replaces the other. The classic page is
the authoritative record renderer; the Thread page is the promoted
visual for cross-persona morning reads.
