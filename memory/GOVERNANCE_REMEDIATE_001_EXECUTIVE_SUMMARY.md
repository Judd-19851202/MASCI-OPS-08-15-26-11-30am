# GOVERNANCE-REMEDIATE-001 · Executive Summary

```
Environment    : preview (fork-executed) · production (operator-required cutover documented)
Access Level   : mixed (preview-runtime + static-analysis + operator-attested for prod parts)
Evidence Source: mixed (preview-runtime + curl + DB-counts + file-hash audits)
Confidence     : VERIFIED for preview-side execution; ASSUMED for operator-side until cutover complete
```

---

## §1 · One-page summary

Per operator-authorized **path A**, the fork executed every part of GOVERNANCE-REMEDIATE-001 that can be performed safely from inside the preview pod, and drafted exact runbooks for every part that requires Atlas Console or the production pod's secrets panel.

**What the fork executed (preview side):**
- Rotated 3 application-trust-chain secrets in `/app/backend/.env`: `JWT_SECRET`, `ADMIN_HMAC_SECRET`, `MFA_ENCRYPTION_KEY`.
- Verified backend restarts clean, `/api/health` returns 200, `/api/version` correctly self-identifies as preview.
- Confirmed zero MFA-enrolled preview users (rotation invalidated no TOTPs).
- Confirmed preview data unchanged: same `daily_reports`/`job_photos`/`employees`/`motive_events` counts as before rotation.
- Confirmed no preview user accounts modified; bcrypt password hash prefixes unchanged.
- Audited `/app/memory/test_credentials.md` for prod-capable accounts (found 5).
- Produced operator runbooks for Atlas user creation, MONGO_URL cutover, broad-user retirement, and prod-side secret rotation.

**What the operator must execute (no fork access):**
1. Create `masci_preview_user` + `masci_prod_user` in Atlas Console with env-scoped `readWrite` only.
2. Set production pod `MONGO_URL` to `masci_prod_user` credentials. Redeploy. Verify.
3. Set preview pod `MONGO_URL` to `masci_preview_user` credentials. Restart. Verify.
4. Disable (do NOT delete) `admin_db_user` and `Password` in Atlas Console.
5. Rotate the same 3 application secrets on the production pod via the Emergent secrets panel. Redeploy.
6. Update `test_credentials.md` to mark the 5 shared-credential accounts as preview-only and rotate prod-side passwords through the standard admin UI.

When (1-6) are complete, signal the fork. Fork will run Workstream F isolation probes and produce the final PASS/FAIL.

## §2 · Risk Register

| ID | Risk | Likelihood | Impact | Severity | Status |
|---|---|---|---|---|---|
| GR001-R01 | Cluster-level Atlas user remains in use until operator completes §3.1-§3.2 of cutover runbook | HIGH (in flight) | CRITICAL | 🔴 **P0 — OPEN** |
| GR001-R02 | Prod-side `JWT_SECRET` / `ADMIN_HMAC_SECRET` / `MFA_ENCRYPTION_KEY` still unchanged; preview-side rotation does not break prod tokens | HIGH (in flight) | HIGH | 🟡 **P1 — OPEN** |
| GR001-R03 | 5 shared admin/portal passwords still valid in production until operator rotates | HIGH (in flight) | HIGH | 🟡 **P1 — OPEN** |
| GR001-R04 | Operator could mis-bind a new Atlas user role (e.g., `readWriteAnyDatabase` instead of `readWrite@masci_safety`) and re-create the very gap being closed | LOW | HIGH | 🟢 **P2** — mitigated by §4 isolation probe |
| GR001-R05 | Cutover-window prod outage if operator pastes a malformed `MONGO_URL` | LOW | MEDIUM | 🟢 **P2** — mitigated by §6 rollback path |
| GR001-R06 | Preview `directory_sessions` (2,192 rows) all invalidated → users re-login next access | MEDIUM | LOW (re-login is expected) | 🟢 **P3** — directive-accepted |
| GR001-R07 | A second cluster-write user (`Password`) remains until operator disables in §5 | HIGH (in flight) | HIGH | 🟡 **P1 — OPEN** |
| GR001-R08 | Final PASS verdict requires operator confirmation of §3-§5; until then verdict is CONDITIONAL | INHERENT | n/a | 🟢 **expected** |

## §3 · Before / After Matrix

| Capability | BEFORE (pre-2026-06-09) | AFTER (preview-side only · today) | AFTER (full cutover · operator completes) |
|---|---|---|---|
| Preview MONGO_URL credential | `admin_db_user` (atlasAdmin, cluster-wide) | `admin_db_user` (UNCHANGED — operator step pending) | `masci_preview_user` (readWrite@masci_safety_preview only) |
| Prod MONGO_URL credential | `admin_db_user` (atlasAdmin, cluster-wide) | UNCHANGED | `masci_prod_user` (readWrite@masci_safety only) |
| Preview JWT_SECRET sha256[:16] | `e7c932da5ea5fe3e` | `68ba21911757e10d` ✅ ROTATED | unchanged from "AFTER preview-side" |
| Preview ADMIN_HMAC_SECRET sha256[:16] | `b2e926846861e3b1` | `7eddfa5064641e9d` ✅ ROTATED | unchanged |
| Preview MFA_ENCRYPTION_KEY sha256[:16] | `6421c3ffebeb25b6` | `7152445ad5aaf493` ✅ ROTATED | unchanged |
| Prod JWT_SECRET | (unknown to fork) | UNCHANGED | ROTATED by operator |
| Prod ADMIN_HMAC_SECRET | (unknown to fork) | UNCHANGED | ROTATED by operator |
| Prod MFA_ENCRYPTION_KEY | (unknown to fork) | UNCHANGED | ROTATED by operator |
| Shared cluster admins active | `admin_db_user`, `Password` | UNCHANGED | DISABLED |
| Preview can read prod DB? | YES (full reach) | YES (still — pre-cutover) | NO (cutover proof in Workstream F) |
| Prod can read preview DB? | YES (full reach) | YES (still) | NO |
| Preview backend healthy? | YES | ✅ YES (verified) | YES |
| Prod backend healthy? | YES | UNCHANGED | YES (operator verifies) |
| Preview data | 794 DR / 1,812 JP / 365 EMP / 376 MEV | ✅ UNCHANGED | UNCHANGED |
| Prod data | 113 DR / 776 JP / 262 EMP / 1,170 MEV / 41,253 sync logs | UNCHANGED | UNCHANGED |
| Employee passwords | bcrypt hashes in user_directory | ✅ UNCHANGED | UNCHANGED |
| User accounts (counts) | 75 user_directory entries (preview) | ✅ UNCHANGED | UNCHANGED |
| test_credentials.md | 5 PROD-CAPABLE shared accounts documented | UNCHANGED (operator must edit) | ANNOTATED preview-only |

## §4 · Verification Evidence captured (this sprint)

| Evidence | Path |
|---|---|
| Pre-rotation secret hashes + post-rotation hashes | `/app/memory/governance_remediate_001_evidence/secret_rotation_evidence.txt` |
| MFA enrolment count = 0 in preview | inline in `GOVERNANCE_REMEDIATE_001_SECRET_ROTATION.md` §3 |
| Backend health post-rotation | inline in same doc §4 |
| Workstream F probes (scripts) | `GOVERNANCE_REMEDIATE_001_FORENSIC_VERIFICATION.md` §3 |
| Atlas Console runbook | `GOVERNANCE_REMEDIATE_001_ATLAS_CUTOVER.md` |
| Test credentials audit | `GOVERNANCE_REMEDIATE_001_CREDENTIAL_AUDIT.md` |

## §5 · PASS / FAIL — current verdict

```
GOVERNANCE-REMEDIATE-001 · OVERALL                → 🟡 CONDITIONAL PASS
                          ↳ Preview-side actions  → ✅ PASS
                          ↳ Operator-side actions → ⏳ NOT YET EXECUTED
                          ↳ Workstream F final    → ⏳ AWAITING CUTOVER
```

The verdict will promote to ✅ **FULL PASS** when:
1. Operator completes Atlas user creation + MONGO_URL cutover (`ATLAS_CUTOVER.md` §3).
2. Operator disables broad-access users (`ATLAS_CUTOVER.md` §5).
3. Operator rotates prod-side secrets (`SECRET_ROTATION.md` §5).
4. Operator updates `test_credentials.md` and rotates the 5 prod-capable account passwords (`CREDENTIAL_AUDIT.md` §4).
5. Fork runs `FORENSIC_VERIFICATION.md` §3 probes against the post-cutover state and produces all 8 PASS conditions.

## §6 · Prohibited actions confirmed NOT taken

✅ No employee passwords changed.
✅ No portal passwords changed (per fork — operator's prod-side actions in step (4) above are part of the operator-only remediation, not a fork action).
✅ No users deleted.
✅ No databases deleted.
✅ No production records modified.
✅ No preview records modified.
✅ No Motive credentials rotated.
✅ No MaintainX credentials rotated.
✅ No FleetWatcher / Dispatch / Material Movement / feature work / unrelated refactors touched.

## §7 · Deliverable index

| Document | Path |
|---|---|
| Executive Summary + Risk Register + Before/After + Verdict | `/app/memory/GOVERNANCE_REMEDIATE_001_EXECUTIVE_SUMMARY.md` (this) |
| Atlas Cutover Runbook (operator-executable) | `/app/memory/GOVERNANCE_REMEDIATE_001_ATLAS_CUTOVER.md` |
| Secret Rotation Report (preview executed) | `/app/memory/GOVERNANCE_REMEDIATE_001_SECRET_ROTATION.md` |
| Credential Audit (test_credentials.md) | `/app/memory/GOVERNANCE_REMEDIATE_001_CREDENTIAL_AUDIT.md` |
| Forensic Verification (Workstream F scripts) | `/app/memory/GOVERNANCE_REMEDIATE_001_FORENSIC_VERIFICATION.md` |
| Final Certification (conditional) | `/app/memory/GOVERNANCE_REMEDIATE_001_FINAL_CERTIFICATION.md` |
| Raw evidence | `/app/memory/governance_remediate_001_evidence/` |
| PRD updated | `/app/memory/PRD.md` |

**STOPPED AT CERTIFICATION. AWAITING OPERATOR EXECUTION OF ATLAS CUTOVER.**
