# GOVERNANCE-HARDEN-001 · Executive Summary, Risk Register, Findings, Recommended Remediations, PASS/FAIL

```
Environment    : both
Access Level   : mixed (preview-runtime+preview-DB · prod-DB-read · public-only)
Evidence Source: mixed (external-probe + preview-runtime + preview-DB + prod-DB read-only + static-analysis)
Confidence     : VERIFIED for primary findings; INFERRED/ASSUMED explicitly classed in each section
```

---

## §1 · Executive Summary (one page)

GOVERNANCE-HARDEN-001 was a read-only, no-change forensic governance audit across six workstreams. The audit completed all six and the central finding is the same one TRUTH-AUDIT-001 surfaced — confirmed in fuller detail here:

**The MASCI Operations Platform currently has zero infrastructure-level separation between preview and production.** Both pods share a single MongoDB Atlas user (`admin_db_user`) carrying the `atlasAdmin` role, plus a second customer account (`Password`) with `readWriteAnyDatabase`. Five documented admin/portal credentials in `/app/memory/test_credentials.md` are stated to work in **both** preview and production. The only thing currently preventing a preview-side compromise from immediately becoming a production-side compromise is the chain of OMEGA directives that this fork agent is voluntarily following.

What is healthy: the production application itself appears externally well-configured (TLS, HSTS, auth gates, webhook contracts, env-correct `/api/version`, env-correct `db_name`); the production Motive integration is currently Connected and ingesting data; only **one** agent-attributed write to production exists across all 159 collections, and that write is a documented sprint closeout (MOTIVE-PROD-INCIDENT-001).

What is unhealthy: the credential surface. Three governance failures are documented:
1. Cluster-level Atlas user shared by both environments.
2. Shared super-admin + 4 other portal credentials documented as working in production.
3. Pre-TRUTH-AUDIT-001 reports under-disclosed the access model.

The remediation is **all operator-side** (Atlas Console + production pod `.env` rotation). The fork agent took **no remediation action** in this sprint. Six deliverable documents are produced. A risk register, findings table, and recommended remediation plan follow.

**Verdict:** see §5.

---

## §2 · Risk Register

| ID | Risk | Likelihood | Impact | Severity | Mitigated by | Owner |
|---|---|---|---|---|---|---|
| **GH001-R01** | Compromise of preview pod credentials = total production cluster compromise | MEDIUM (preview is a low-attack-surface pod but still internet-adjacent) | **CRITICAL** | 🔴 **P0** | Atlas user split per Workstream A §A.7 | Operator |
| **GH001-R02** | Second cluster admin (`Password`) gives a parallel total-compromise path | MEDIUM | CRITICAL | 🔴 **P0** | Disable or rotate `Password` user | Operator |
| **GH001-R03** | Shared super-admin password (`Maddix123!`) = identical login for preview attacker into prod admin UI | MEDIUM | HIGH (admin-level operational damage; auditable but real) | 🔴 **P0** | Rotate prod-side passwords per Workstream D §D.5 Phase 1 | Operator |
| **GH001-R04** | 4 other shared portal credentials (HR, Dispatch, Chris Wright, testmech, hrmanager) | MEDIUM | MEDIUM (each has bounded portal scope but combined = broad reach) | 🟡 P1 | Same Phase 1 rotation | Operator |
| **GH001-R05** | Future fork agent without honest disclosure header could touch prod undetected | HIGH (no automated enforcement today) | HIGH | 🟡 P1 | Workstream E enforcement tooling (sketch in §E.6) | Engineering (operator-approved) |
| **GH001-R06** | 141 of 159 prod collections lack any actor attribution → invisible writes possible | HIGH (architectural) | MEDIUM (defensive depth, not prevention) | 🟡 P1 | Future doctrine: every write path must set an `updated_by` / `actor` field | Engineering (operator-approved) |
| **GH001-R07** | 2 docs in `equipment_parts` carry `updated_by` = "UI smoke" / "smoke" — unsanctioned residue | LOW | LOW | 🟢 P3 | Operator triage; one-shot cleanup if confirmed unauthorized | Operator |
| **GH001-R08** | `JWT_SECRET` / `ADMIN_HMAC_SECRET` / `MFA_ENCRYPTION_KEY` likely shared between preview and prod | MEDIUM | HIGH (token replay risk if shared) | 🟡 P1 | Rotation per Workstream D §D.5 Phase 3 | Operator |
| **GH001-R09** | Atlas Console action surface fully outside this fork's reach → operator must execute remediation | INHERENT | MEDIUM (timing risk only) | 🟢 P2 | Operator-scheduled rotation window | Operator |
| **GH001-R10** | 21 orphan ephemeral test DBs on prod cluster (pytest residue) | LOW | LOW (storage + cleanliness only) | 🟢 P3 | One-shot cleanup by operator | Operator |
| **GH001-R11** | No `.env`-diff visibility between preview and prod | LOW (operator runs deploys manually anyway) | LOW (operational confusion only) | 🟢 P3 | Future: operator-only key-SHA diff tool | Engineering |
| **GH001-R12** | No automated certification-header check today | HIGH (zero tooling) | LOW (operator review still catches it) | 🟢 P3 | Workstream E §E.6 tooling | Engineering |

## §3 · Findings (with evidence references)

| # | Finding | Workstream | Evidence | Class |
|---|---|---|---|---|
| F-01 | Cluster-level Atlas user (`admin_db_user`, role `atlasAdmin`) used by both preview and production pods. | A | `/app/memory/governance_harden_001_evidence/A_atlas_access_raw.txt` § connectionStatus | VERIFIED |
| F-02 | Second cluster-write Atlas user (`Password`, role `readWriteAnyDatabase`) standing in `admin.system.users`. | A | `/app/memory/governance_harden_001_evidence/A_atlas_users_via_find.txt` | VERIFIED |
| F-03 | Five admin/portal credentials documented as working in **both** preview and production (super-admin `jaymn.judd@mascigc.com` / `Maddix123!`, plus 4 portal accounts). | D | `/app/memory/test_credentials.md` lines 14-30 + the dispatch/HR/testmech/chriswright sections | VERIFIED (file-disclosed) |
| F-04 | Prior fork wrote to production database. | B | `masci_safety.integration_settings.motive.updated_by = "motive_prod_incident_001:remediation"` | VERIFIED |
| F-05 | Single agent-attributed write found in production (the F-04 one). No additional unsanctioned writes detected by actor-field scan. | B | `/app/memory/governance_harden_001_evidence/B_prod_write_audit_deepdive.txt` | VERIFIED (within scan limits — see §B.5 caveats) |
| F-06 | Unexpected `equipment_parts` smoke-test residue: 2 docs `updated_by` = `UI smoke` / `smoke`. | B | Same | VERIFIED |
| F-07 | 141 of 159 prod collections have no actor field — agent visibility blind spot. | B | `/app/memory/governance_harden_001_evidence/B_prod_write_audit_raw.txt` § field inventory | VERIFIED |
| F-08 | Preview and production correctly self-identify via `/api/version`. | C | `curl https://mascidocs.com/api/version` + preview equivalent | VERIFIED |
| F-09 | 21 orphan `masci_test_*_preview` DBs on the same Atlas cluster from prior pytest runs. | A | `list_database_names()` returns them | VERIFIED |
| F-10 | Deployment is operator-only at every promotion step (Save to GitHub + Deploy). | F | Static-analysis of platform tooling + this fork's lack of any deploy API | VERIFIED |
| F-11 | No automated enforcement of the four-field certification header today. | E | Workstream E §E.6 acknowledges no tooling | VERIFIED |
| F-12 | Motive integration in production is currently Connected (api_key len 36, webhook_secret len 32, status=Connected, last_sync 2026-06-09T20:17:41Z). | B / Motive | Direct prod DB read | VERIFIED |
| F-13 | Likely-shared cross-env secrets (`JWT_SECRET`, `ADMIN_HMAC_SECRET`, `MFA_ENCRYPTION_KEY`) — not verifiable without prod pod `.env` access. | D | Wording in `test_credentials.md` + operational absence of MFA-rotation symptoms | INFERRED |

## §4 · Recommended Remediations (operator-only · NO action taken)

Listed in priority order. None executed.

### P0 — High-impact · Operator must schedule promptly

1. **Atlas user split (Workstream A §A.7).** Create per-env Atlas users; rotate `admin_db_user` and `Password`; bind each pod's MONGO_URL to the new env-scoped user.
2. **Production-side super-admin password rotation (Workstream D §D.5 Phase 1 #1).** Set a value not stored in `test_credentials.md`. Update `test_credentials.md` to note: "PREVIEW-ONLY — do not reuse in prod."
3. **Production-side portal-account rotation or deletion (Workstream D §D.5 Phase 1 #2).** Specifically `hrmanager@mascigc.com`, `dispatch@mascigc.com`, `chriswright@mascigc.com`, `testmech@mascigc.com`.

### P1 — Medium-impact · Operator should schedule within next deploy window

4. **Cross-env secret rotation (Workstream D §D.5 Phase 3).** Rotate `JWT_SECRET`, `ADMIN_HMAC_SECRET`, then `MFA_ENCRYPTION_KEY` carefully (re-enrollment may be required).
5. **Implement certification-header enforcement (Workstream E §E.6).** Pick one of: pre-commit hook, CI check, or backend startup gate.
6. **Add actor instrumentation to write paths that lack it** (F-07). Future engineering sprint.
7. **Investigate `equipment_parts` smoke residue** (F-06). Likely safe to leave; operator triage.

### P2 — Lower-impact

8. **Drop orphan `masci_test_*_preview` DBs** (F-09). One-shot Atlas Console operation.

### P3 — Hygiene

9. **Build `.env` key-SHA diff tool** (operator-only).
10. **Document operator-side break-glass rotation cadence** for retained admin users.

---

## §5 · PASS / FAIL Verdict

```
GOVERNANCE-HARDEN-001  ·  AS AN AUDIT      →  ✅ PASS
GOVERNANCE-HARDEN-001  ·  AS A CONTROL POSTURE  →  ❌ FAIL  (operator remediation required)
```

### Why PASS as an audit

All six workstreams completed. Every finding has primary-source evidence in `/app/memory/governance_harden_001_evidence/` or in the per-workstream report. Every certification carries the mandatory four-field header. No assumptions accepted as fact. No code changes, no DB writes, no deploys.

### Why FAIL as a control posture

- 🔴 Cluster-level shared Atlas user.
- 🔴 Second cluster-write Atlas user standing.
- 🔴 Shared admin login.
- 🟡 Inferred cross-env secret reuse.
- 🟡 No automated certification enforcement.

A platform that holds TRUSTED and PROVEN cannot accept these gaps as residual risk. Operator remediation per §4 is required to restore the doctrine.

### Operator next-step

1. Read this document plus the six workstream reports.
2. Authorize §4 P0 items (Atlas user split + admin password rotation).
3. When P0 is complete, re-run a one-shot variant of Workstream B forensic audit to confirm no further agent-attributed writes have occurred.
4. Promote control-posture verdict to PASS when §4 P0 is verified by an operator.

---

## §6 · Deliverable Index

| Document | Path |
|---|---|
| Executive Summary + Risk Register + Findings + Verdict | `/app/memory/GOVERNANCE_HARDEN_001_EXECUTIVE_SUMMARY.md` (this file) |
| Workstream A — Atlas Access Report | `/app/memory/GOVERNANCE_HARDEN_001_ATLAS_ACCESS_REPORT.md` |
| Workstream B — Production Write Forensic Audit | `/app/memory/GOVERNANCE_HARDEN_001_PROD_WRITE_AUDIT.md` |
| Workstream C — Access Matrix | `/app/memory/GOVERNANCE_HARDEN_001_ACCESS_MATRIX.md` |
| Workstream D — Credential Audit | `/app/memory/GOVERNANCE_HARDEN_001_CREDENTIAL_AUDIT.md` |
| Workstream E — Certification Standard | `/app/memory/GOVERNANCE_HARDEN_001_CERT_STANDARD.md` |
| Workstream F — Deployment Chain | `/app/memory/GOVERNANCE_HARDEN_001_DEPLOYMENT_CHAIN.md` |
| Raw evidence (curl, Mongo outputs, env diffs) | `/app/memory/governance_harden_001_evidence/` |

## §7 · Stop conditions met

✅ No code changes · ✅ No DB writes · ✅ No deploys · ✅ No fixes · ✅ No feature work · ✅ No UI changes · ✅ No FleetWatcher · ✅ No Dispatch · ✅ No Material Movement · ✅ No MaintainX activation · ✅ No Motive feature expansion · ✅ No self-certification — every claim cites primary evidence.

**STOPPED. Awaiting operator review.**
