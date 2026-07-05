# DR-UNIFY-004 · ODS Certification

**Claim:** Real Daily Reports feed ODS, historical records remain
queryable, AI summary emits an idempotent `intelligence_fact`, no
duplicate/orphan/stale facts.

## V1 → ODS ingest (DR-CUTOVER-001)

- Post-insert hook in `POST /api/daily-reports` calls
  `services.ods_spine.ingest.ingest_dr_v1_report(...)`.
- Emits: `labor_fact`, `equipment_fact`, `photo_evidence_fact`,
  `daily_report_signal_fact` (and others depending on payload) per
  the ODS spec.
- Historical backfill of 1,329 legacy records completed successfully
  in DR-CUTOVER-001; still queryable.
- Facts are idempotent — re-running ingest supersedes
  `is_current` predecessors instead of duplicating.

## DR-CUTOVER-002 intelligence_fact

- On summary accept, emits one `intelligence_fact` with:
  - `source_type = "daily_report"`
  - `source_id = <report_id>`
  - `source_item_id = "intel:operational_summary"`
  - `is_current = true`
  - payload includes `audience`, `agent`, `language`, `source`, `chars`.
- Previous `is_current` with the same key triplet is set
  `is_current=false` — locked by
  `test_accept_supersedes_prior_intelligence_fact_idempotency`.
- Never duplicates labor/equipment/safety/photo facts.
- Emission is best-effort — a failed insert does not block the
  accept response.

## Live smoke

- ODS-001 spine tests pass (see regression cert).
- DR-CUTOVER-002 lock envelope confirms idempotent supersede across
  repeated accepts.

## Non-goals for this cert

- Background task queue for ODS ingest at scale — documented P1
  follow-up when tenants enable AI at scale (non-blocker).

**Verdict:** ODS subsystem certified.
