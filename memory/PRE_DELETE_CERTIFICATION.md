# Pre-Delete Certification · Sprint 1B Phase 2

**Batch:** OMEGA Critical Fix Sprint 1B · Phase 2
**Date:** 2026-05-31
**Scope:** For every record proposed for deletion or update, certify ZERO references from active workflow surfaces. Captured BEFORE Phase 3 execution.

---

## 1 · Reference scan matrix

For each deletion candidate, scan these reference surfaces:

| Reference surface | Match field |
|---|---|
| `tasks.source_record_id` | UUID match |
| `notifications.subject_id` | UUID + doc_id match |
| `corrective_actions.source_id` / `.incident_id` | UUID match |
| `audit_events.entity_id` / `.subject_id` / `.resource_id` | UUID match |
| `operational_links.source_id` / `.target_id` | UUID match |
| `operational_attachments.linked_to_id` | UUID match |

---

## 2 · Per-candidate certification

| Candidate | UUID | Tasks | Notif | CA | Audit | OpLinks | OpAttach | Total | Verdict |
|---|---|---|---|---|---|---|---|---|---|
| FL user `fieldleader@mascigc.com` | `d805f3d4` | 0 | 0 | 0 | 0 | 0 | 0 | **0** | ✅ Safe to deactivate |
| Test incident "John Smith" | `d9626eeb` | 0 | 0 | 0 | 0 | 0 | 0 | **0** | ✅ Safe to delete |
| Payroll batch | `674300c9` | 0 | 0 | 0 | 0 | 0 | 0 | **0** | ✅ Safe to delete |
| Payroll batch | `48cbc60e` | 0 | 0 | 0 | 0 | 0 | 0 | **0** | ✅ Safe to delete |
| Payroll batch | `6590febb` | 0 | 0 | 0 | 0 | 0 | 0 | **0** | ✅ Safe to delete |
| Payroll batch | `f1371d01` | 0 | 0 | 0 | 0 | 0 | 0 | **0** | ✅ Safe to delete |
| Payroll batch | `76d952ce` | 0 | 0 | 0 | 0 | 0 | 0 | **0** | ✅ Safe to delete |
| Payroll batch | `f28d4b44` | 0 | 0 | 0 | 0 | 0 | 0 | **0** | ✅ Safe to delete |
| Payroll batch | `ed8ec430` | 0 | 0 | 0 | 0 | 0 | 0 | **0** | ✅ Safe to delete |
| Payroll batch | `8b649f92` | 0 | 0 | 0 | 0 | 0 | 0 | **0** | ✅ Safe to delete |
| Payroll batch | `2eb4c2d2` | 0 | 0 | 0 | 0 | 0 | 0 | **0** | ✅ Safe to delete |
| Payroll batch | `d3150925` | 0 | 0 | 0 | 0 | 0 | 0 | **0** | ✅ Safe to delete |
| PREVIEW_POSTENV notif | `64f443d6` | 0 | n/a (self) | 0 | 0 | 0 | 0 | **0** | ✅ Safe to delete |
| PREVIEW_POSTENV notif | `9ac645f3` | 0 | n/a (self) | 0 | 0 | 0 | 0 | **0** | ✅ Safe to delete |
| Test daily report DR-2026-00007 | `4cab04c6` | 0 | 0 | 0 | 0 | 0 | 0 | **0** | ✅ Safe to delete |

---

## 3 · Sister-record sanity checks

| Sister record | Why it matters | Verdict |
|---|---|---|
| `incidents.566a38dd` (real PRODUCTION incident sharing `INC-2026-00001`) | After `d9626eeb` deletion, `566a38dd` becomes the sole owner of `INC-2026-00001` | ✅ Untouched · sister retains canonical ID |
| `daily_reports.ac306ad5` (real PRODUCTION DR sharing `DR-2026-00007`) | After `4cab04c6` deletion, `ac306ad5` becomes sole owner of `DR-2026-00007` | ✅ Untouched · sister retains canonical ID |
| `payroll_variance_decisions` (7 docs linked to 10 batches) | Cascade — must be deleted with parent batches | ✅ Same batch; cascade enforced |
| 68 `session_activity` rows for `fieldleader@mascigc.com` | After deactivation, telemetry remains as audit trail | ✅ Preserved for audit |
| 6 production incidents (post `d9626eeb` deletion) | Status backfill applies to these | ✅ Will receive `status="open"` backfill |

---

## 4 · Pre-execution snapshots (counts captured)

| Collection | Pre-execution count |
|---|---|
| `incidents` | 7 |
| `incidents.doc_id='INC-2026-00001'` | 2 |
| `daily_reports` | 87 |
| `daily_reports.doc_id='DR-2026-00007'` | 2 |
| `payroll_variance_batches` | 10 |
| `payroll_variance_decisions` | 7 |
| `notifications` | 77 |
| `field_leadership_users` (1 active doc for `fieldleader@`) | 1 |
| `incidents.status=null` | 7 (becomes 6 post-d9626eeb delete · then 0 post-backfill) |
| `user_directory.is_active=null` | 7 (becomes 0 post-backfill) |

---

## 5 · OMEGA verdict

🟢 **ALL 15 deletion candidates carry ZERO references** across the 6 reference-surface check. None is in an active workflow chain.

🟢 **Sister records are untouched** — each duplicate doc_id resolves automatically when the test sibling is removed.

🟢 **Cleared for Phase 3 execution.**

---

## 6 · Closeout

🛑 Pre-delete certification complete. **Execution authorized to proceed.**
