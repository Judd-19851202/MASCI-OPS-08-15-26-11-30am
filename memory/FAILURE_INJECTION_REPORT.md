# FAILURE INJECTION REPORT

Date: 2026-07-27  
Execution evidence: `/app/memory/PLATFORM_SURVIVABILITY_EXECUTION_RAW.json`  
Scope: Preview-only, isolated, deterministic, repeatable, reversible failure injections

---

## 1. Execution rules honored

- No overlapping failures were injected.
- Every scenario was isolated and returned to healthy baseline before the next scenario.
- Wave 3 frozen artifacts were hash-checked before and after the sequence.
- Historical Wave 3 evidence was not modified.
- Failure injections stayed within Preview and did not modify infrastructure or Production.

---

## 2. Scenario summary

| Scenario | Failure injected | Result | Measured RTO | Measured RPO | Reversible | Wave 3 frozen artifacts unchanged |
|---|---|---|---|---|---|---|
| `PSP-FI-01` | Admin request without bound directory session | PASS | 471.27 ms | 0 s | Yes | Yes |
| `PSP-FI-02` | Synthetic stale backup/restore guard | PASS | 31.31 ms | 0 s | Yes | Yes |
| `PSP-FI-03` | Duplicate scheduler slot claim | PASS | 118.62 ms | 0 s | Yes | Yes |
| `PSP-FI-04` | Preview config blended with production DB identity (simulation) | PASS | 0.38 ms | 0 s | Yes | Yes |
| `PSP-FI-05` | Checksum-corrupted archive lineage candidate (simulation) | PASS | 0.17 ms | 0 s | Yes | Yes |
| `PSP-FI-06` | Synthetic failed Trust Spine lifecycle event | PASS | 1577.03 ms | 0 s | Yes | Yes |

---

## 3. Detailed observations

### PSP-FI-01 — Admin continuity fail-closed path

- Injection: call admin route with `X-Admin-Token` only.
- Expected behavior: fail closed because the bound `X-Directory-Token` is required when the admin session row carries directory binding.
- Observed behavior:
  - failure probe: `401 {"detail":"Invalid admin token"}`
  - recovery probe with dual-token auth: `200`
- Conclusion: admin continuity is preserved through a bounded, explicit operational recovery step rather than permissive auth bypass.

### PSP-FI-02 — Synthetic stale guard recovery

- Injection: insert one synthetic stale `backup_jobs` row in `state=running` older than reclaim threshold.
- Observed behavior:
  - `mark_stale_backup_jobs()` marked the row stale
  - `ownership_revoked=true`
  - `failure_reason=stale_job_recovered`
  - active jobs returned to zero
- Recovery action: delete synthetic row after validation.
- Conclusion: stale recovery is durable and operator-safe.

### PSP-FI-03 — Duplicate scheduler claim prevention

- Injection: claim the same synthetic scheduler slot twice.
- Observed behavior:
  - first claim succeeded
  - second claim returned `None`
  - `dedup_attempts=1`
  - scheduler run completed as `done`
- Recovery action: synthetic scheduler run deleted after validation.
- Conclusion: duplicate work is prevented before execution fan-out.

### PSP-FI-04 — Preview/production configuration blend rejection

- Injection: simulate preview config pointed at production DB name and user.
- Observed behavior:
  - validator returned `FAIL`
  - blocking issues included `preview_using_production_db_name`, `preview_using_production_user`, and fail-closed environment separation findings
  - valid preview config still returned `PASS`
- Conclusion: configuration recovery is fail-closed rather than best-effort.

### PSP-FI-05 — Corrupted archive lineage quarantine

- Injection: simulate latest archive lineage with checksum mismatch.
- Observed behavior:
  - no authoritative artifact selected under corruption
  - rejection reasons included `direct_checksum_lineage_mismatch`
  - corrected checksum restored `direct_evidence_status=VERIFIED`, `integrity_status=PASS`
- Conclusion: archive selection remains trustworthy under corruption pressure.

### PSP-FI-06 — Trust Spine failed lifecycle visibility

- Injection: emit one synthetic failed Trust Spine stage.
- Observed behavior:
  - `/api/admin/trust-spine` surfaced the synthetic workflow as `band=red`
  - `failed_24h=1`
  - cleanup removed all synthetic rows and restored the local probe baseline
- Conclusion: trust degradation becomes visible quickly and can be reversibly tested without polluting frozen evidence.

---

## 4. Baseline health before and after the sequence

### Before

- `/api/health` → 200
- `/api/healthz` → 200
- `/api/ready` → 200
- `/api/health/full` → 200

### After

- `/api/health` → 200
- `/api/healthz` → 200
- `/api/ready` → 200
- `/api/health/full` → 200

Conclusion: the backend returned to a healthy baseline after every preview-only scenario.
