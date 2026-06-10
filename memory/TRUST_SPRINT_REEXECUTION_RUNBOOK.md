# FORGEDOPS · TRUST SPRINT RE-EXECUTION RUNBOOK
**Status:** 🟡 **PRE-EXECUTION** · runs after rotation + verification PASS.

Re-runs the full Trust Sprint with the new credentials. Each item that previously failed must now flip to 🟢.

## Step 1 · Run audit driver
```bash
cd /app/backend && python scripts/p0_trust_audit.py
```
- Output `/app/memory/p0_audit_atlas_users.json` — `authenticated_as.user` must now be `masci_preview_user`.
- Output `/app/memory/p0_audit_production_truth.json` — production read **must FAIL** with `Unauthorized`.

## Step 2 · Re-run T1 + P0-A certifications
- Edit `ENVIRONMENT_TRUTH_CERTIFICATION.md`: remove the P0 SUPPLEMENT banner, mark T1 verdict 🟢.
- Edit `ATLAS_USER_ISOLATION_CERTIFICATION.md`: flip verdict from 🔴 FAIL → 🟢 PASS with new evidence (the Unauthorized response).
- Edit `ATLAS_CLUSTER_SPLIT_RECONCILIATION.md`: append "Resolved 2026-XX-XX" with operator initials + audit log link.

## Step 3 · Re-run Map GO/NO-GO
- Edit `MAP_GO_NO_GO_CERTIFICATION.md`.
- Re-evaluate the 6 gates. The two CRITICAL blockers (cluster-wide credential · Motive 0%) must both be addressed.
  - Credential blocker: ✅ if Step 1 passes.
  - Motive coverage: requires separate Motive activation workstream (not part of this Trust Sprint).
- If credential blocker is resolved but Motive coverage is still 0%, verdict remains 🔴 NO-GO on Motive grounds.

## Step 4 · Update PRD + CHANGELOG
- Append closure entry citing the run date, operator initials, and Step 1 audit JSON file.

## Step 5 · Continue Workstream
Workstream remains OPEN until Map GO/NO-GO flips to 🟢. That requires Motive activation, which is a separate workstream the operator must authorize.

---

## Step 6 · Failure modes (cross-reference)

| Symptom | Failure mode | Recovery |
|---|---|---|
| Audit JSON shows `admin_db_user` after rotation | F-21 (env-var didn't apply or pod not restarted) | Restart pod, re-run audit. |
| T1/P0-A certs still 🔴 after script PASS | F-22 (operator forgot to flip markdown) | Edit certs per Step 2. |
| Audit script raises `NetworkTimeout` | F-17 | Retry; check Atlas IP allowlist (F-28). |

See `ATLAS_ISOLATION_FAILURE_ANALYSIS.md` for full matrix.

---

## Step 7 · Sign-off

```
Step 1 (audit JSON shows new user)        ☐ PASS   ____  ____
Step 2 (T1 + P0-A flipped 🟢)             ☐ DONE   ____  ____
Step 3 (Map GO/NO-GO re-evaluated)         ☐ DONE   ____  ____
Step 4 (PRD + CHANGELOG appended)          ☐ DONE   ____  ____
```

When all four are signed, the Trust Sprint side of this workstream is complete. The workstream itself only closes after Gates 6–9 of `ATLAS_ISOLATION_WORKSTREAM_CLOSEOUT_PLAN.md` also flip 🟢.
