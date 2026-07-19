# CRITICAL EXCEPTION REGISTER

Date: 2026-07-19  
Checkpoint: B

## Discovery method

Deterministic static inventory was run across critical runtime and script families by scanning for:
- `except Exception`
- bare/broad `except`
- broad async task catches
- `pass`
- best-effort catches that log and continue

Inventory artifact count:
- total broad catches reviewed in critical families: **1984**

## Totals by family

- Database identity and startup: heavy concentration in `backend/server.py` and `db_isolation_failsafe.py`
- Authentication and authorization: `pm_auth.py`, `auth_must_change.py`, auth dependencies in `server.py`
- Daily Reports: multiple handlers in `server.py`
- Backup and restore: `server.py`, `backend/tools/restore_drill.py`, backup-related routes/services
- Storage and integrations: `photo_storage`, AI gateway adapters, R2-related services, email/notification routes
- Trust and governance: governance routes, deployment readiness, release identity, certification paths
- Destructive scripts and migrations: write-capable scripts inventory

## Totals by classification (current reviewed subset)

- INTENTIONAL_BEST_EFFORT: accepted in non-critical audit/telemetry/report generation paths
- SAFE_DETERMINISTIC_FALLBACK: governance/runtime file-read fallbacks, selected config-read paths
- CORRECTLY_FAIL_CLOSED: auth/password-change, OpenAI wrapped-json parsing, restore guard refusals
- OVERLY_BROAD_BUT_HARMLESS: selected startup hygiene and report emitters
- MASKS_REAL_FAILURE: still present in multiple unreviewed broad-catch clusters
- INSUFFICIENT_LOGGING: repaired for restore partial-failure reporting; still open in wider families
- WRONG_EXCEPTION_TYPE: not fully inventoried yet
- REQUIRES_REPAIR: still open in the remaining unreviewed families

## Key repaired finding

| ID | File:Line | Family | Classification | Status | Notes |
|---|---|---|---|---|---|
| B-CER-004 | `backend/server.py:restore route` | Backup and restore | INSUFFICIENT_LOGGING | FIXED | Partial restore now reports failed docs/counts and no longer claims full success on failure. |

## Accepted best-effort findings

| ID | Area | Rationale |
|---|---|---|
| CER-ACC-001 | governance health runtime reads | Safe deterministic fallback when optional runtime doctrine files are absent. |
| CER-ACC-002 | selected parity/report scripts | Local artifact write failures do not affect platform correctness. |
| CER-ACC-003 | OpenAI adapter parsing guard | Fails closed to explicit invalid-json/non-json statuses. |

## Open findings preventing Checkpoint B closure

1. The inventory is complete enough to prove broad-catch density, but not fully normalized into per-occurrence owned findings across every required family.
2. Several script/migration/operator families still contain broad catches whose semantics have not been individually classified.
3. Multiple startup/governance/server broad catches remain untriaged at finding granularity.

## Completion note

Checkpoint B cannot close until the remaining harmful or unclassified broad catches in active Production-capable paths are normalized into owned findings and, where required, repaired.
