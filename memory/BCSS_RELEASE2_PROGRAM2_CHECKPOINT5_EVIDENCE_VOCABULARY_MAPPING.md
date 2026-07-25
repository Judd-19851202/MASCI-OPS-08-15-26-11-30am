# BCSS Release 2 · Program 2 · Checkpoint 5
## Evidence Vocabulary Mapping

The Operational Truth Spine is a MASCI OPS platform architecture.  
BCSS is Domain 01 and the first implementation domain.  
The artifact does not establish a separate BCSS-only truth architecture.

Date: 2026-07-25

Status: IMPLEMENTATION COMPLETE

---

| Current repository term | Canonical OTS term | Classification | Compatibility requirement | Future migration status |
|---|---|---|---|---|
| public environment/data truth | `observed` / `DIRECT_OBSERVED` | valid adapter | preserve existing `verified` boolean | adopted in Family 1 |
| recovery posture pill | `correlated` / `CORRELATED` | valid adapter | preserve pill/status fields | adopted in Family 2 |
| backup verification cron state | `historical` or `declared` | valid adapter | preserve state keys | adopted in Family 3 |
| backup verification report verdict | `observed` or `independently_verified` | valid adapter | preserve `verdict` | adopted in Family 3 |
| trust score / band | `calculated` / `CALCULATED` | canonical derived consumer | preserve score fields | adopted in Family 4 |
| deployment decision | `independently_verified` / `DECISION_RECORDED` | canonical bounded decision | preserve decision fields | adopted in Family 5 |
| integration overall | `correlated` / `CORRELATED` | directly coupled consumer update | preserve `overall` field | adopted to preserve truthful dependency continuity |
