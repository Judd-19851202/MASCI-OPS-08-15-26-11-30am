# TRUTH-AUDIT-001 · Executive Summary

**Sprint:** TRUTH-AUDIT-001 · Environment, Access, Deployment & Evidence Reconciliation
**Mode:** Read-only forensic reconciliation
**Date:** 2026-06-09 (probe time UTC)
**Auditor:** E1 (fork agent)
**Status:** ✅ COMPLETE · Awaiting operator review

---

## TL;DR (one paragraph)

The fork agent's **MONGO_URL credential is cluster-level on Atlas `masci-prod.1nduwmg.mongodb.net` and can directly read and write *every* database on that cluster**, including production (`masci_safety`). Prior reports (MOTIVE-VERIFY-001, MOTIVE-PROD-INCIDENT-001, POST-DEPLOY-002, POST-DEPLOY-003) that claimed direct production-DB inspection and even one direct production-DB *write* (`integration_settings.motive` row, `updated_by="motive_prod_incident_001:remediation"`, 2026-06-09T20:01:25 UTC) were factually correct in those claims. My subsequent **AUDIT-ACCESS-VERIFY-001 answers (Q6/Q7/Q8 = "NO")** were factually incorrect; I conflated *backend default DB binding* (`DB_NAME=masci_safety_preview`) with *credential capability* (cluster-wide). PROD-STABILIZE-001's conditional pass remains directionally correct but its scope statement (no prod DB access) is wrong. This audit issues the corrections, the verifiable matrices, and the mandatory certification doctrine.

---

## What changed in my understanding during this audit

| Item | Pre-audit belief | Post-audit fact | Evidence |
|---|---|---|---|
| MONGO_URL scope | "Preview DB only" | **Cluster-level on the SAME Atlas cluster as production** | `motor.list_database_names()` returns 32 DBs including `masci_safety` (prod) + `masci_safety_preview` + restore drills + 21 ephemeral test DBs |
| PROD DB read | "NO" (AUDIT-ACCESS-VERIFY-001 Q6) | **YES** | Direct read of `masci_safety.integration_settings`, `daily_reports.count`, etc. completed in this session |
| PROD DB write | "NO" (AUDIT-ACCESS-VERIFY-001 Q6/Q8) | **YES — capable, and historically exercised by a prior fork** | `masci_safety.integration_settings.motive.updated_by="motive_prod_incident_001:remediation"` proves a prior fork wrote to prod |
| Production admin login | "NO" (AUDIT-ACCESS-VERIFY-001 Q4/Q5) | **Probable YES** — credentials present in `/app/memory/test_credentials.md` (`jaymn.judd@mascigc.com` / `Maddix123!` flagged as a *shared* account that works in both DBs because preview was seeded from prod snapshot). Not attempted in this audit. | `/app/memory/test_credentials.md` lines 16-19 + MFA TOTP section line 26 |
| Why I gave the wrong answers in AUDIT-ACCESS-VERIFY-001 | n/a | I answered from the surface signal (`DB_NAME` env var = preview) without doing the actual cluster-permissions probe. | Self-correction logged in §3 of `TRUTH_AUDIT_001_ACCESS_MATRIX.md` |

---

## Verdict on Trusted/Proven (ForgedOps doctrine)

**TRUSTED is currently at HIGH risk.** A prior fork was able to *write to the production database* using a credential that lives in plain-text in the preview pod's `/app/backend/.env`. The blast radius of any future fork is therefore: full read/write access to the live production database, plus likely admin login if it harvests credentials from `/app/memory/test_credentials.md`. This is **not** what the platform's environment-separation banners and audit reports imply.

**PROVEN is currently at MEDIUM risk.** Multiple prior reports made claims that turned out to be true (e.g., 40,920 rejected webhooks; MOTIVE-PROD-INCIDENT-001 closure) but those reports did not disclose the access model that made the claims verifiable. AUDIT-ACCESS-VERIFY-001 went the other direction — claimed *less* access than actually exists. Trust in any certification depends on the certification disclosing its access model. That is the doctrine TRUTH-AUDIT-001 establishes.

---

## Statements requiring withdrawal or downgrade

(See `TRUTH_AUDIT_001_REPORT_RECONCILIATION.md` for the full per-report table.)

| Statement | Source | Action |
|---|---|---|
| "Query production database records? NO" | AUDIT-ACCESS-VERIFY-001 · Q6 | **WITHDRAWN.** Correct answer is YES. |
| "Read production admin audit logs? NO" | AUDIT-ACCESS-VERIFY-001 · Q7 | **WITHDRAWN.** Correct answer is YES (via direct Mongo read of `masci_safety.admin_audit`). |
| "Read production integration settings? NO" | AUDIT-ACCESS-VERIFY-001 · Q8 | **WITHDRAWN.** Correct answer is YES (already exercised — read `masci_safety.integration_settings.motive` in §1.1 of MOTIVE-VERIFY-001 and again in this audit). |
| "Production credentials… NO" / "Authenticated production admin pages… NO" | AUDIT-ACCESS-VERIFY-001 · Q4 / Q5 | **DOWNGRADED to UNVERIFIED.** Credentials present in `test_credentials.md` are documented as "applies to BOTH databases." Not attempted in this audit; doctrine prohibits side-effects. Whether they currently authenticate against `mascidocs.com` is unverified. |
| PROD-STABILIZE-001 statement: "I have no prod DB access" / "Phase 4 items 1-6 require operator" | PROD_STABILIZE_001_CERTIFICATION.md | **DOWNGRADED.** I now do have prod DB read access. The certification's verdict (🟡 CONDITIONAL PASS) is unchanged because data-integrity verification still warrants operator dashboard view, but the *justification* shifts from "no access" to "doctrinal restraint to read-only audit + no UI access without admin login." |
| PROD-STABILIZE-001 § 1 Phase 1 #1-2 ("Production Motive credentials exist · CONFIRMED via code path") | PROD_STABILIZE_001_PHASE_1_MOTIVE.md | **UPGRADED** from inference to verified. Direct read of `masci_safety.integration_settings.motive`: api_key_value len=36, webhook_secret_value len=32, status=Connected, last_sync_at=2026-06-09T20:01:25Z. |

---

## What can be stated as FACT today (verified in this session)

1. The fork's MONGO_URL credential reads 32 databases on `masci-prod.1nduwmg.mongodb.net`, including `masci_safety` (prod) and `masci_safety_preview` (preview).
2. Production environment (`mascidocs.com`) self-reports `app_env="production"`, `db_name="masci_safety"`, source_hash `7f68853f…`.
3. Preview environment (`safety-audit-mobile-1.preview.emergentagent.com`) self-reports `app_env="preview"`, `db_name="masci_safety_preview"`, source_hash `b1cf…`.
4. Production Motive integration is currently Connected with non-empty credentials, last sync 2026-06-09T20:01:25Z, 1,170 motive_events, 190 asset_mappings, 41,253 integration_sync_logs (matches MOTIVE-VERIFY-001's 40,920+ count), 1 production_incident row.
5. Production `daily_reports` = 113, `employees` = 262, `job_photos` = 776.
6. A prior fork wrote to production `integration_settings.motive` (updated_by string `"motive_prod_incident_001:remediation"`).

## What cannot currently be proven (requires operator)

1. Whether the credentials in `/app/memory/test_credentials.md` (e.g., `jaymn.judd@mascigc.com` / `Maddix123!`) currently authenticate at `https://mascidocs.com/admin/login`.
2. Whether MFA is currently required for the super-admin login in production.
3. The contents of production's `/app/backend/.env` on the deployed pod (specifically: is the same MONGO_URL also live in prod, are the same JWT_SECRET / SUPER_ADMIN_BOOTSTRAP_PASSWORD / RESEND_API_KEY values shared with preview, is APP_ENV truly "production" or still "preview" per the APP_ENV-LABEL-001 defect).
4. Whether the Cloudflare / ingress edge logs reflect any prior-fork access patterns to prod admin endpoints.

## What requires operator validation

See `TRUTH_AUDIT_001_FINAL_VERDICT.md` § "Operator-Required Actions."

---

## Mandatory certification doctrine (effective immediately)

Every future certification MUST include the following four fields up-front:

```
Environment    : preview | production | both | other
Access Level   : public-only | preview-runtime+preview-DB | prod-DB-read | prod-DB-read+write | prod-admin-UI | super-admin-UI
Evidence Source: external-probe | preview-runtime | preview-DB | prod-DB (read-only) | prod-DB (read/write) | operator-attested | mixed
Confidence     : VERIFIED | INFERRED | ASSUMED
```

Reports lacking these four fields **fail certification automatically**. See `TRUTH_AUDIT_001_CERTIFICATION_STANDARD.md`.

---

## Stop conditions met

Per directive: no code changes, no DB writes, no deployments, no fixes, no feature work. All assertions in this audit reference primary evidence captured in the companion documents. Awaiting operator review.
