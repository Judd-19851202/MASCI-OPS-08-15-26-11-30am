# MASTER DEFECT REGISTER

Date: 2026-07-19  
Checkpoint: B

## RC findings

| ID | Severity | Title | Status | Owner | Target |
|---|---:|---|---|---|---|
| RC05-DEF-01 | P1 | PM actor tagging missing on shared auth gates | FIXED | Main agent | Checkpoint B |
| RC05-DEF-02 | P3 | Splash Tailwind duration entity corruption | FIXED | Main agent | Checkpoint B |
| RC06B-DEF-01 | P1 | OpenAI wrapped/fenced JSON parsing incomplete | FIXED | Main agent | Checkpoint B |
| RC07-DEF-01 | P1 | restore drill `collections/<name>.json` parsing gap | FIXED | Main agent | Checkpoint B |
| RC07-DEF-02 | P1 | id-less restore lacked content-hash identity fallback | FIXED | Main agent | Checkpoint B |
| RC09C-1 | P1 | `/daily-reports/new` sentinel route fell through ID path | FIXED | Main agent | Checkpoint B |
| RC09D-1 | P1 | canonical security-header middleware absent | OPEN | Main agent | Checkpoint B |
| RC10-E | P1 | `423` responses not structurally guaranteed security headers | OPEN | Main agent | Checkpoint B |

## Phase 2 correctness defects

| ID | Severity | Title | Status | Regression evidence |
|---|---:|---|---|---|
| B-P2-001 | P1 | duplicate `$ne` query key in local-project-doc migration | FIXED | backend lint clean |
| B-P2-002 | P1 | duplicate test name in `test_iter452_lifecycle_dr_pv.py` | FIXED | collect-only green |
| B-P2-003 | P1 | duplicate test name in `test_track_15_97_github_actions_health_probe.py` | FIXED | collect-only green |
| B-P2-004 | P1 | duplicate test name in `test_track_19_16_incident_engine_phase_a.py` | FIXED | collect-only green |
| B-P2-005 | P1 | duplicate test name in `test_track_22_4b_followup_idempotency_spine_phase_2.py` | FIXED | collect-only green |
| B-P2-006 | P1 | AI capability flags defaulted true instead of fail-closed | FIXED | `test_ai_config_001_capabilities.py` |

## Runtime image reference register

| ID | Severity | Title | File | Status |
|---|---:|---|---|---|
| B-RIR-001 | P1 | db isolation runtime error pointed operators to non-shipped memory runbook | `backend/db_isolation_failsafe.py` | FIXED |
| B-RIR-002 | P1 | governance health route depended on non-shipped memory baseline files | `backend/routes/governance_health.py` | FIXED_TO_SHIPPED_STATIC_PATH |
| B-RIR-003 | P1 | governance self-protection route depended on non-shipped memory + test reports | `backend/routes/governance_self_protection.py` | PARTIALLY_FIXED |
| B-RIR-004 | P1 | deployment readiness route counted tests from non-shipped runtime path | `backend/routes/admin_deployment_readiness.py` | FIXED |
| B-RIR-005 | P2 | day-1 debrief API returned `/app/memory/...` path to runtime caller | `backend/routes/dispatch_day1_debrief.py` | FIXED |
| B-RIR-006 | P2 | platform data truth endpoint returned memory document path | `backend/routes/platform_data_truth.py` | FIXED |
| B-RIR-007 | P2 | asset mapping executive summary returned memory runbook path | `backend/routes/asset_mapping_recon.py` | FIXED |

## Destructive operation register

| ID | Severity | Title | Status | Owner |
|---|---:|---|---|---|
| DOP-001 | P1 | jobs bulk replace lacked full-reset confirmation discipline | FIXED | Main agent |
| DOP-002 | P1 | jobs helper allowed empty replacement after wipe | FIXED | Main agent |
| DOP-003 | P1 | cost code bulk replace lacked full-reset confirmation discipline | FIXED | Main agent |
| DOP-004 | P1 | crew force-reseed lacked confirmation/backups acknowledgment | FIXED | Main agent |
| DOP-005 | P1 | scrap crew hub lacked shared destructive runtime guard | FIXED | Main agent |
| DOP-006 | P1 | exports restore replace mode lacked explicit replace confirmation | FIXED | Main agent |
| DOP-007 | P1 | supplier import replace-all lacked explicit destructive confirmation | FIXED | Main agent |

## Dangerous scripts

| ID | Severity | Title | Status | Owner |
|---|---:|---|---|---|
| B-DSR-001 | P1 | `seed_project_memberships.py` can mutate active DB without dry-run/guard | OPEN | Main agent |
| B-DSR-002 | P1 | `seed_equipment_make_model.py` mutates repo data + DB without safety contract | OPEN | Main agent |
| B-DSR-003 | P1 | `migrate_local_project_docs_to_r2.py` lacks explicit typed production opt-in | OPEN | Main agent |
| B-DSR-004 | P1 | `track_15_65_seed_email_routes.py` apply mode lacks production confirmation doctrine | OPEN | Main agent |
| B-DSR-005 | P1 | `basecamp_import.py` / `basecamp_import_big.py` mutation tooling still needs full safety classification | OPEN | Main agent |
| B-DSR-006 | P1 | `migrate_dr_v2_collections_to_daily_report.py` still needs full safety classification | OPEN | Main agent |
| B-DSR-007 | P1 | `track_15_28c_canonicalization_migration.py` still needs full safety classification | OPEN | Main agent |
| B-DSR-008 | P1 | `track_15_67_second_tenant_simulation.py` remains active multi-collection mutation tooling without modern fail-closed contract | OPEN | Main agent |
| B-DSR-009 | P1 | `scripts/automated_drill.py` remains high-risk operator mutation tool (drop DB + R2 writes) without modern fail-closed contract | OPEN | Main agent |
| B-DSR-010 | P1 | `scripts/cleanup_production_contamination.py` remains direct destructive cleanup tooling without modern fail-closed contract | OPEN | Main agent |
| B-DSR-011 | P1 | `scripts/r2_lifecycle_apply.py` remains storage mutation tooling without completed safety classification | OPEN | Main agent |

## Critical exception register

| ID | Severity | Title | File | Classification | Status |
|---|---:|---|---|---|---|
| B-CER-001 | P2 | governance self-protection startup auto-record swallows write failure | `backend/routes/governance_self_protection.py:489-490` | OVERLY_BROAD_BUT_HARMLESS | OWNED |
| B-CER-002 | P2 | governance health JSON file loads use safe deterministic fallback | `backend/routes/governance_health.py:78-94` | SAFE_DETERMINISTIC_FALLBACK | ACCEPTED |
| B-CER-003 | P2 | deployment readiness route swallows CI/test enumeration failures | `backend/routes/admin_deployment_readiness.py:90-134,285` | MASKS_REAL_FAILURE | PARTIALLY_FIXED |
| B-CER-004 | P1 | restore route per-document failures were warning-only and could overstate success | `backend/server.py:11203-11394` | INSUFFICIENT_LOGGING | FIXED |
| B-CER-005 | P2 | OpenAI adapter fallbacks are best-effort but fail closed to explicit statuses | `backend/services/ai_gateway/adapters/openai_adapter.py` | CORRECTLY_FAIL_CLOSED | ACCEPTED |
| RC09D-1 | P1 | canonical security-header middleware absent | `backend/server.py` | FIXED |
| RC10-E | P1 | mutation barrier / handled responses lacked guaranteed canonical security headers | `backend/server.py` | FIXED |
| B-CER-006 | P1 | critical broad-exception inventory is not yet normalized into per-occurrence owned findings across all required families | `docs/governance/CRITICAL_EXCEPTION_REGISTER.md` | OPEN |

## Production mutation accounting

- Atlas reads = 0
- Atlas writes = 0
- Production R2 reads = 0
- Production R2 writes = 0
- email/provider calls = 0
- scripts executed = none
