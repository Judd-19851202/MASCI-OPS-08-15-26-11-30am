# FORGEDOPS · FINAL CLOSEOUT CHECKLIST · Production Trust & Environment Isolation

**Workstream STATUS: 🟡 OPEN** · last review 2026-02-10.

Per FORGEDOPS Execution Doctrine, this workstream CANNOT be marked CLOSED until every checkbox is 🟢.

## BUILD COMPLETE
- [x] `db_isolation_failsafe.py` shipped.
- [x] `verify_isolation_suite.py` + 6 named wrappers shipped.
- [x] `p0_trust_audit.py` shipped.
- [x] `/api/platform/data-truth` endpoint shipped.
- [x] Operator runbooks authored (Atlas separation · preview rotation · production rotation · post-rotation · stability · re-execution).

## INTEGRATION COMPLETE
- [x] Failsafe wired into `server.py @app.on_event("startup")`.
- [x] Audit driver outputs JSON to `/app/memory/`.

## VERIFICATION COMPLETE
- [ ] **OPERATOR-GATED** · Atlas user separation executed in `masci-prod` cluster.
- [ ] **OPERATOR-GATED** · `MONGO_URL` rotated in preview pod.
- [ ] **OPERATOR-GATED** · `MONGO_URL` rotated in production pod.
- [ ] **OPERATOR-GATED** · `ENFORCE_DB_ISOLATION=true` set in BOTH pods.
- [ ] `scripts/verify_preview_cannot_read_production.py` exits 0 from preview.
- [ ] `scripts/verify_production_cannot_read_preview.py` exits 0 from production.
- [ ] `scripts/verify_post_rotation_health.py` exits 0 in both pods.
- [ ] `scripts/verify_production_stability.py` exits 0 against production.
- [ ] `scripts/p0_trust_audit.py` re-run shows `Unauthorized` cross-DB.

## TRUTH COMPLETE
- [x] Production inventory documented (596 assets · 0 road plates · 7 trench boxes · 75 support · 262 employees · 28 projects).
- [ ] **OPERATOR-GATED** · Re-run inventory under `masci_prod_user` confirms parity (no preview asset visible).

## CERTIFICATION COMPLETE
- [x] `ATLAS_USER_INVENTORY.md`
- [x] `ATLAS_NAMESPACE_INVENTORY.md`
- [x] `ATLAS_PERMISSION_ANALYSIS.md`
- [x] `ATLAS_USER_SEPARATION_OPERATOR_RUNBOOK.md`
- [x] `PREVIEW_CREDENTIAL_ROTATION_RUNBOOK.md`
- [x] `PRODUCTION_CREDENTIAL_ROTATION_RUNBOOK.md`
- [x] `POST_ROTATION_VERIFICATION_RUNBOOK.md`
- [x] `PRODUCTION_STABILITY_VALIDATION_RUNBOOK.md` (hardened 2026-02-10 · 8-step sign-off)
- [x] `TRUST_SPRINT_REEXECUTION_RUNBOOK.md` (hardened 2026-02-10 · 7-step sign-off)
- [x] `ATLAS_ISOLATION_FAILURE_ANALYSIS.md` (32 failure modes F-01..F-32) — NEW 2026-02-10
- [x] `ATLAS_ISOLATION_EXECUTION_PACKAGE.md` (single-page Phases A–H) — NEW 2026-02-10
- [x] `ATLAS_ISOLATION_WORKSTREAM_CLOSEOUT_PLAN.md` (9 closure gates) — NEW 2026-02-10
- [x] `FINAL_CLOSEOUT_CHECKLIST.md` (this doc)
- [ ] **POST-EXECUTION** certifications flipped to 🟢:
  - [ ] `ATLAS_USER_ISOLATION_CERTIFICATION.md`
  - [ ] `ENVIRONMENT_TRUTH_CERTIFICATION.md`
  - [ ] `ATLAS_CLUSTER_SPLIT_RECONCILIATION.md`

## PROVEN COMPLETE
- [ ] **OPERATOR-GATED** · 24-hour soak window with `ENFORCE_DB_ISOLATION=true` and zero pod failures.
- [ ] **OPERATOR-GATED** · `admin_db_user` deleted from Atlas.
- [ ] **OPERATOR-GATED** · `mongosh` login as `admin_db_user` returns `Authentication failed`.
- [ ] **OPERATOR-GATED** · `/app/memory/ATLAS_USER_ISOLATION_CLOSEOUT_EVIDENCE.md` filed with audit JSON + soak log + Atlas screenshot.
- [ ] **OPERATOR-GATED** · Operator signs the closeout (initials + UTC timestamp) in this file.

## CLOSEOUT COMPLETE
- [ ] All BUILD / INTEGRATION / VERIFICATION / TRUTH / CERTIFICATION / PROVEN boxes are 🟢.
- [ ] Workstream STATUS flipped to **CLOSED** at top of this doc.
- [ ] PRD + CHANGELOG updated with closure entry.
- [ ] Phase 5B Live Operations Map UI is **still NO-GO until Motive coverage ≥20%** — that is a separate workstream.

## Non-negotiable
- NO checkbox may be ticked without operator-verifiable evidence (script exit code · log line · audit JSON).
- "Future sprint" / "potential improvement" / "good enough for now" are **NOT acceptable justifications** for unchecking any P0 item. (FORGEDOPS Execution Doctrine, 2026-02-10.)

---

## Closure authority

The workstream may only be flipped to **🟢 CLOSED** by an operator who:
- Has executed every gate in `ATLAS_ISOLATION_WORKSTREAM_CLOSEOUT_PLAN.md` §2.
- Has filed `ATLAS_USER_ISOLATION_CLOSEOUT_EVIDENCE.md`.
- Has signed the sign-off template in `ATLAS_ISOLATION_WORKSTREAM_CLOSEOUT_PLAN.md` §6.

Per doctrine, only two status values are permitted: **OPEN** or **CLOSED**.

```
─── FINAL CLOSEOUT SIGNATURE BLOCK ───────────────────────────────────────
Status:        ☐ OPEN   ☐ CLOSED
UTC timestamp: __________________________
Operator:      __________________________
Evidence file: /app/memory/ATLAS_USER_ISOLATION_CLOSEOUT_EVIDENCE.md
──────────────────────────────────────────────────────────────────────────
```
