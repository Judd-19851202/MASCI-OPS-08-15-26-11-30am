# TRACK 19.57 · Project Thread Promotion Map

Every Universal Thread section → certified payload field used.

| # | Section (Universal Thread)  | Adapter                   | Source payload path                                                       |
|---|-----------------------------|---------------------------|---------------------------------------------------------------------------|
| 1 | Mission Overview            | `missionAdapter`          | `job.*` from `/api/pm/jobs` + `recent.superintendent` + `recent.source_report_date` + `oi.attention_level` + `oi.top_attention_label` |
| 2 | Attention                   | `attentionAdapter`        | `oi.top_attention_label` (severity from `attention_level`) + `mm.proof_summary.missing_proof_count` + `mm.verification_status` + missing DR heuristic |
| 3 | Operational Guidance        | shell (unchanged)         | `project_intelligence` product row from `/operational-intelligence/summary` |
| 4 | Timeline                    | `timelineAdapter`         | `projectDay.assets[]` (first_seen / last_seen) + `mm.haul_cycles[]` + `jhaItems[].uploaded_at` + `recent.source_report_date` |
| 5 | Relationships               | `relationshipAdapter`     | `job.project_manager` · `recent.superintendent` · `job.client` · `recent.masci_crews[]` · `recent.equipment[]` |
| 6 | Documents                   | `documentsAdapter`        | `/api/job-hazard-files/by-project/{pn}` items → `/api/job-hazard-files/{file_id}/download` deep-links |
| 7 | Photos                      | shell empty               | Honest empty — no per-project photo endpoint safely surface-able through this shell today. Users deep-link to the Job Photos Library. |
| 8 | Operational Intelligence    | shell (unchanged)         | `project_intelligence` product row from `/operational-intelligence/summary` |
| 9 | History                     | shell empty               | Honest empty — historical snapshots are not surfaced by the certified project endpoints today. OI history covers the score dimension separately. |
|10 | Audit                       | shell empty               | Honest empty — read-only presentation. Admin audit lives in `/admin/audit`. |

## Universal Action Queue (max 5)
Derived from `oi.top_attention_label` + missing proofs + material
verification status + missing Daily Report + zero JHA on file. The
`OperationalThreadPage` shell auto-caps at 5.

## Health derivation (client-side, plain-English)
Only `oi.attention_level` drives the Health chip. No new score model.
Every chip is paired with a plain-English "Why: …" sentence — the
mandate requires a number to always be paired with narration.

## Cross-navigation
- Classic → Thread: `data-testid="pm-project-detail-open-thread-link"` on `PmProjectDetail`.
- Thread → Classic: `data-testid="pm-project-thread-classic-link"` on the promoted Thread.

Both routes coexist. Neither replaces the other. The classic page is
the operational chronology sidecar (existing timeline + material
movement + trench + team panels); the Thread is the Universal-shell
morning-read view.
