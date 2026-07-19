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
- total broad catches reviewed in critical families: **2106**
- machine-readable inventory: `docs/governance/critical_exception_inventory.json`

## Totals by family

- startup/DB identity: **1508**
- authentication/authorization: **75**
- Daily Reports/PDF/files: **145**
- backup/restore: **32**
- R2/storage: **21**
- notifications/email/integrations: **27**
- AI/providers: **13**
- Trust/governance: **94**
- schedulers/background: **30**
- active mutation scripts/migrations: **161**

## Totals by behavior after catch

- re-raise: **219**
- pass: **241**
- fallback: **461**
- return success: **657**
- log only: **276**
- continue loop: **68**
- return default: **182**
- retry: **2**

## Totals by static risk classification

- P1 candidates: **882**
- P2 candidates: **385**
- P3/info: **839**

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

1. The machine-readable inventory now contains stable per-occurrence records, but human-governed ownership is not yet normalized for all 2106 occurrences.
2. 882 P1 candidates require risk-based normalization/closure or containment reasoning before Checkpoint B can close.
3. Startup/governance/server families still dominate the untriaged set.

## Completion note

Checkpoint B cannot close until the remaining harmful or unclassified broad catches in active Production-capable paths are normalized into owned findings and, where required, repaired.
