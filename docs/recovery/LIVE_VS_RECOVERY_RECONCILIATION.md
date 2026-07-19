# LIVE VS RECOVERY RECONCILIATION

Checkpoint: **A**  
Track: **MASTER TRACK — MASCI Docs live-parity reconciliation**  
Date: **2026-07-19**

## Scope

This document is the evidence-backed, temporary source of truth for Phase 1.
It compares the current live MASCI/ForgedOps source tree in this workspace
against the locally-available recovery comparison source for the required
RC02–RC10 items.

## Comparison sources used

- **Live workspace under review:** `/app`
- **Current branch:** `main`
- **Current HEAD:** `5ce1350b912fdecabfbe56a0ed0b2a2c5a45e0b0`
- **Recovery comparison source available locally as git branch:** `continuity-backup-d9636`
- **Recovery branch SHA:** `d9636e3e1517e263e39082ac31f0ebdeeefdca12`

## Source identity table

| Field | Evidence | Result |
|---|---|---|
| Workspace | `git rev-parse --show-toplevel` | `/app` |
| Repository name | No remote metadata configured locally (`git remote -v` returned no origin) | **UNPROVEN by remote metadata** |
| Active branch | `git branch --show-current` | `main` |
| Current HEAD SHA | `git rev-parse HEAD` | `5ce1350b912fdecabfbe56a0ed0b2a2c5a45e0b0` |
| Upstream / remote branch SHA | `git rev-parse @{u}` failed with `fatal: no upstream configured for branch 'main'` | **UNAVAILABLE LOCALLY** |
| Working tree status | `git status --short` | clean |
| Tracked / untracked / staged state | `git status --short` empty | none |
| Runtime/version fingerprint locally available | `frontend/src/buildVersion.generated.js:6-10` | build commit `3b2aff40dd69b5d5b55b9b48ac22859cc463315d`, source hash `9311cf9c8ea9b2de6241f2bd03ecd305` |
| Deployed SHA proof in repo | No authoritative production-deployed SHA file found in repo metadata; build artifact commit exists but is not deployment proof | **UNPROVEN** |
| Recovery source locally available | `git branch --all --verbose --no-abbrev` and `git show continuity-backup-d9636:...` | yes |
| Live tree differs from recovery source | `git diff --name-only continuity-backup-d9636..main` | yes |
| Is this the real MASCI codebase? | File inventory, route topology, production governance files, release-identity scope, and patched production recovery files match MASCI/ForgedOps structure | **PROVEN BY CODE IDENTITY** |

## Method

Read-only comparison only for Checkpoint A:

1. Verified workspace identity with git metadata and build identity files.
2. Used `git show continuity-backup-d9636:<path>` and `git diff continuity-backup-d9636 -- <path>` where recovery artifacts exist.
3. Traced runtime entrypoints in `backend/server.py`, route registration, dependency wiring, recovery tools, and frontend routes.
4. Mapped live test coverage by searching `backend/tests/**` and frontend test files for each repair family.
5. Did **not** deploy, restore, seed, purge, migrate, or execute dangerous scripts.

## Classification legend

- `PRESENT_AND_EQUIVALENT`
- `PRESENT_BUT_DIFFERENT_AND_VALID`
- `MISSING`
- `PARTIAL`
- `REGRESSED`
- `NOT_APPLICABLE`
- `BLOCKED_UNPROVEN`

---

## Reconciliation matrix

| Defect ID | Live classification | Severity | Code change required | Summary |
|---|---|---:|---:|---|
| RC02 | PRESENT_BUT_DIFFERENT_AND_VALID | P2 | No | Dispatch draft continuity exists live; recovery/live differ only in hook dependency arrays and closeout wiring. |
| RC05-DEF-01 | PARTIAL | P1 | Yes | Shop + HR actor tagging is present; central PM-token gates still do not tag PM actors as `_actor_kind="pm_user"`. |
| RC05-DEF-02 | REGRESSED | P3 | Yes | Splash overlay still contains the corrupted Tailwind class entity in live. |
| RC06-DEF-01 | PRESENT_AND_EQUIVALENT | P2 | No | AI capability resolution is fail-closed when required flags or providers are absent. |
| RC06-DEF-02 | PRESENT_BUT_DIFFERENT_AND_VALID | P2 | No | Provider diagnostics now use broader direct-key availability logic rather than a narrower fallback shape. |
| RC06B-DEF-01 | PARTIAL | P1 | Yes | Anthropic fenced JSON extraction is robust; OpenAI fenced JSON extraction is still incomplete. |
| RC07-DEF-01 | PARTIAL | P1 | Yes | Restore tooling handles several archive layouts, but not the required `collections/<name>.json` plural-wrapper case. |
| RC07-DEF-02 | MISSING | P1 | Yes | Id-less documents are skipped; no content-hash restore key exists in the live restore paths reviewed. |
| RC09C-1 | PARTIAL | P1 | Yes | Canonical create redirect exists for `/daily/new`, but `/daily-reports/new` is still vulnerable to wildcard-ID routing. |
| RC09D-1 | MISSING | P1 | Yes | No canonical security-header middleware was found for frame/CSP/referrer/HSTS enforcement. |
| RC10-A | PRESENT_BUT_DIFFERENT_AND_VALID | P2 | No | Deploy gate covers `main`, the active branch, and also `master`. |
| RC10-B | PRESENT_BUT_DIFFERENT_AND_VALID | P1 | No | Release-identity hard-fail and frontend/backend source-hash parity are structurally present in live. |
| RC10-C | PRESENT_BUT_DIFFERENT_AND_VALID | P2 | No | Production health-probe workflow avoids the historical empty-job/noop-sibling failure. |
| RC10-D | PRESENT_BUT_DIFFERENT_AND_VALID | P2 | No | No dead `/api/auth/readonly-validate` allow-list entry was found in the live read-only certification allowlist. |
| RC10-E | MISSING | P1 | Yes | Because canonical security-header middleware is absent, `423` MFA lock responses are not structurally guaranteed to receive those headers. |

---

## Detailed findings

### RC02 — Dispatch draft TDZ / draft-continuity repair

- **Classification:** `PRESENT_BUT_DIFFERENT_AND_VALID`
- **Live evidence:**
  - `frontend/src/components/dispatch/AssignmentCreateDrawer.jsx:330-356` stores the assignment draft under `masci.draft.dispatch-assignment-new`.
  - `frontend/src/components/dispatch/AssignmentCreateDrawer.jsx:382-390` hydrates a pending draft on open.
  - `frontend/src/components/dispatch/AssignmentCreateDrawer.jsx:455-475` restores the pending draft only via an explicit restore action.
  - `frontend/src/components/dispatch/AssignmentCreateDrawer.jsx:707-709` mounts `DraftRestorePrompt`.
- **Recovery evidence:** same file and same repair family exist on `continuity-backup-d9636`; diff shows only hook dependency-array differences, not removal of the draft-continuity logic.
- **Behavioral comparison:** live behavior preserves the recovery repair intent: no silent auto-apply, explicit restore prompt, local draft persistence, and draft clear on confirmed creation.
- **Vulnerable to original defect?** No direct evidence of the original draft-loss defect remaining in this component.
- **Live test coverage:** limited direct static coverage; only indirect reference found in `backend/tests/test_track_15_82b_dispatch_landing_rolloff_action.py`.
- **Recommended action:** none for Checkpoint A. Keep as-is.

### RC05-DEF-01 — PM actor tagging on auth gates / Equipment Pre-Op / DVIR scope

- **Classification:** `PARTIAL`
- **Live evidence:**
  - `backend/server.py:927-996` (`require_shop_or_admin`) tags successful shop auth as `_actor_kind="shop_user"`.
  - `backend/server.py:1129-1158` (`require_admin_pm_or_hr_read`) tags successful HR auth as `_actor_kind="hr_user"`.
  - `backend/pm_auth.py:335-347` treats `shop_user`, `safety_user`, and `hr_user` as unrestricted readers.
  - `backend/pm_auth.py:348-354` added `explicit_pm` fail-closed logic so an email-only actor no longer implicitly gains PM scope.
- **Recovery evidence:** recovery branch contains the same shop/HR tagging pattern and `compute_pm_scope` logic family, but the live branch is not centrally tagging PM actors on the general PM-token gates either.
- **Behavioral comparison:** live improved fail-closed behavior for ambiguous actors, but the specific requirement “PM actor must carry `_actor_kind="pm_user"`” is not satisfied by the central PM read gates in `server.py`. `require_admin`, `require_shop_or_admin`, and `require_admin_pm_or_hr_read` return raw PM docs for PM-token success.
- **Vulnerable to original defect?** **Yes, plausibly.** If the returned PM document lacks `_actor` or `role` fields, `compute_pm_scope()` can still treat it as non-explicit PM and fail closed, which is exactly the kind of scoping drift this repair was meant to prevent.
- **Live test coverage:**
  - `backend/tests/test_prod_visibility_compute_pm_scope.py`
  - `backend/tests/test_track_15_13e_production_auth_session_recovery.py`
  - `backend/tests/test_dr_unify_001_single_system.py`
  - `backend/tests/test_track_22_4b_followup_shop_defects_idempotency.py`
- **Recommended action:** add explicit `_actor_kind="pm_user"` tagging on PM-token success in the shared auth dependencies; then regression-test PM equipment/DVIR and Daily Report read surfaces.

### RC05-DEF-02 — Splash Tailwind duration entity corruption

- **Classification:** `REGRESSED`
- **Live evidence:** `frontend/src/components/SplashOverlay.jsx:61` contains `duration-&lsqb;400ms&rsqb;`.
- **Recovery evidence:** recovery branch line 61 contains the correct `duration-[400ms]` token.
- **Behavioral comparison:** live code is visibly worse than recovery here.
- **Vulnerable to original defect?** Yes; the class token is malformed in live.
- **Live test coverage:** no direct regression lock found for this exact token.
- **Recommended action:** restore the canonical Tailwind class token.

### RC06-DEF-01 — AI module flags must fail closed

- **Classification:** `PRESENT_AND_EQUIVALENT`
- **Live evidence:**
  - `backend/services/ai_gateway/capabilities.py:23-31` documents fail-closed precedence.
  - `backend/services/ai_gateway/capabilities.py:156-201` returns `enabled=False` when gateway, tenant, module, or provider availability checks fail.
  - `backend/services/photo_intelligence/flags.py:6-7` treats absent `DR_V2_PHOTO_VISION_ENABLED` as false.
- **Recovery evidence:** recovery branch contains the same capability-resolver family and the same fail-closed doctrine.
- **Behavioral comparison:** live matches the intended fail-closed posture for the reviewed AI module flags.
- **Vulnerable to original defect?** Not on the reviewed capability paths.
- **Live test coverage:**
  - `backend/tests/test_ai_config_001_capabilities.py`
  - `backend/tests/test_ai_admin_001_config.py`
  - `backend/tests/test_track_22_9b_photo_intel_wireup.py`
- **Recommended action:** none for this item.

### RC06-DEF-02 — provider diagnostics model fallback

- **Classification:** `PRESENT_BUT_DIFFERENT_AND_VALID`
- **Live evidence:** `backend/services/dr_ai/factory.py:30-47` reports `ai_available=True` when any usable direct provider key or Emergent key exists.
- **Recovery evidence:** recovery branch does not carry the later `verify_release_identity`-era release hardening, but the AI diagnostics family is present.
- **Behavioral comparison:** live uses a broader and more operationally correct provider-availability rule than the narrower historical fallback pattern.
- **Vulnerable to original defect?** No evidence of the old “provider available but diagnostics says unavailable” defect in the reviewed live code.
- **Live test coverage:** `backend/tests/test_ai_config_001_capabilities.py` and DR AI tests indirectly cover availability reporting.
- **Recommended action:** none for this item.

### RC06B-DEF-01 — robust AI/vision JSON extraction

- **Classification:** `PARTIAL`
- **Live evidence:**
  - `backend/services/ai_gateway/adapters/anthropic_adapter.py:70-82` strips fenced JSON wrappers robustly enough for common Claude ```json blocks.
  - `backend/services/ai_gateway/adapters/openai_adapter.py:76-86` and `163-174` only `lstrip("`")` and then strip a leading `json` prefix; this does **not** remove a trailing closing fence.
- **Recovery evidence:** recovery branch contains the adapter files and recovery goal required robust wrapped/fenced parsing for both OpenAI and Anthropic.
- **Behavioral comparison:** Anthropic path is substantially repaired; OpenAI path is still incomplete for common fenced provider output like `````json ... `````.
- **Vulnerable to original defect?** Yes on the OpenAI adapter path; wrapped JSON can still fall into `invalid_json` / `non_json_vision_response`.
- **Live test coverage:**
  - `backend/tests/test_dr_roi_001d_photo_vision.py`
  - `backend/tests/test_ai_gateway.py`
  - `backend/tests/test_iter_usage_and_vision_retries.py`
- **Recommended action:** centralize fenced/wrapped JSON extraction and apply it consistently to both text and vision flows for OpenAI and Anthropic adapters.

### RC07-DEF-01 — restore tool collection-name parsing

- **Classification:** `PARTIAL`
- **Live evidence:**
  - `backend/tools/restore_drill.py:89-97` handles `<collection>/json/*.json` and `<collection>/<name>.json`.
  - `backend/tools/restore_drill.py:124-127` maps selected kebab-case collection names.
  - `scripts/restore_drill.py:127-133` restores by `json` directory parent name and drops/reinserts a side DB collection.
- **Recovery evidence:** no live-vs-recovery diff for these files; the paths are effectively unchanged between reviewed branches.
- **Behavioral comparison:** the reviewed live tooling supports several archive layouts, but **not** the required `collections/<name>.json` plural-wrapper semantics. In `backend/tools/restore_drill.py`, such a path would collapse under literal key `collections`.
- **Vulnerable to original defect?** Yes, if the restore input archive uses the plural-wrapper collection layout described by RC07.
- **Live test coverage:** limited and indirect (`backend/tests/test_iter426_restore_drift_watcher.py`, `backend/tests/test_track_15_37_restore_ceiling.py`).
- **Recommended action:** parse the collection name from `collections/<name>.json` correctly and add focused restore-layout tests.

### RC07-DEF-02 — id-less document restore / content-hash restore key

- **Classification:** `MISSING`
- **Live evidence:**
  - `backend/tools/restore_drill.py:157-163` skips any document lacking `id`, `_uid`, or `uuid`.
  - `scripts/restore_drill.py:133-148` side-DB restore path drops and reinserts documents; it does not compute a content-hash identity key.
- **Recovery evidence:** no equivalent content-hash restore key logic was found in the reviewed live restore files.
- **Behavioral comparison:** the required lossless id-less restore behavior is absent.
- **Vulnerable to original defect?** Yes. Trust Spine / audit documents without explicit IDs are at risk of being skipped or reinserted non-idempotently.
- **Live test coverage:** no direct regression lock for content-hash id-less restore was found.
- **Recommended action:** implement canonical content-hash identity for id-less restore records and add idempotency tests.

### RC09C-1 — Daily Report `"new"` create sentinel

- **Classification:** `PARTIAL`
- **Live evidence:**
  - `frontend/src/app/routing/AppRoutes.jsx:597-624` defines `/daily/new -> /daily/submit` and `/reports/daily/new -> /daily/submit`.
  - `frontend/src/app/routing/AppRoutes.jsx:633` still routes `/daily-reports/:id` through a wildcard redirect path.
  - `frontend/src/app/routing/AppRoutes.jsx:905-906` mounts `/pm/daily/:id` to `ViewDailyReport`.
  - `frontend/src/pages/ViewDailyReport.jsx:187-193` fetches `/api/daily-reports/${id}` directly.
- **Recovery evidence:** route-convergence tests lock `/daily/new` and `/daily/submit`, but no live route special-case for `/daily-reports/new` was found.
- **Behavioral comparison:** the canonical create route exists, but the exact sentinel defect described in RC09C is still reachable through `/daily-reports/new` because it can be interpreted as a report ID.
- **Vulnerable to original defect?** Yes, on the `/daily-reports/new` alias family.
- **Live test coverage:**
  - `backend/tests/test_dr03_route_convergence.py`
  - `backend/tests/test_track_23_1_v3_ui_shape.py`
  - `backend/tests/test_dr_unify_001_single_system.py`
- **Recommended action:** add an explicit `/daily-reports/new` redirect to the canonical create route and prevent `new` from falling through the wildcard report-detail path.

### RC09D-1 — canonical security-header middleware

- **Classification:** `MISSING`
- **Live evidence:** repo-wide search found only scattered per-response `X-Content-Type-Options: nosniff` headers (for file downloads) and **no** canonical middleware adding:
  - `Referrer-Policy`
  - `X-Frame-Options`
  - CSP `frame-ancestors 'none'`
  - Production-only HSTS
- **Recovery evidence:** no live canonical middleware equivalent was found in the reviewed branch state.
- **Behavioral comparison:** live has partial per-route header usage, not the required global middleware.
- **Vulnerable to original defect?** Yes.
- **Live test coverage:** no direct header middleware regression file found.
- **Recommended action:** add one canonical security-header middleware and place it so all responses, including 4xx/423 auth lockouts, receive the headers.

### RC10 cluster

#### RC10-A — deploy gate covers the actual deploy branch

- **Classification:** `PRESENT_BUT_DIFFERENT_AND_VALID`
- **Live evidence:** `.github/workflows/sigma3-deploy-gate.yml:25-30` triggers on pushes/PRs to `[main, master]`; current active branch is `main`.
- **Vulnerable to original defect?** No for the current branch.
- **Recommended action:** none.

#### RC10-B — release identity hard-fail / frontend-backend hash consistency

- **Classification:** `PRESENT_BUT_DIFFERENT_AND_VALID`
- **Live evidence:**
  - `backend/scripts/verify_release_identity.py:17-49` hard-fails on commit/source-hash mismatch.
  - `release_identity_scope.json:1-20` defines the guarded scope.
  - `frontend/src/buildVersion.generated.js:6-10` contains build commit and source hash.
  - `backend/tests/test_release_identity_build_guard.py:11-29` locks script invocation and scope file usage.
- **Recovery evidence:** `backend/scripts/verify_release_identity.py` is **absent** on `continuity-backup-d9636`; this is a live-tree advancement beyond the recovery branch.
- **Behavioral comparison:** live is stronger than the recovery branch on release identity proof.
- **Vulnerable to original defect?** No on the reviewed build-identity path.
- **Recommended action:** none.

#### RC10-C — comments/dead YAML references must not satisfy gate enforcement

- **Classification:** `PRESENT_BUT_DIFFERENT_AND_VALID`
- **Live evidence:**
  - `.github/workflows/production-health-probe.yml` is a single real workflow with executable steps and no noop sibling.
  - `backend/tests/test_track_15_97_github_actions_health_probe.py:38-47, 80-103, 232-237` locks the absence of the sibling workflow and validates the real workflow shape.
- **Recovery evidence:** recovery branch contains the same workflow family but live has later lifecycle-gating additions.
- **Behavioral comparison:** live preserves the “real file, real steps” enforcement intent.
- **Vulnerable to original defect?** No direct evidence of the old empty-job/noop-sibling failure shape.
- **Recommended action:** none.

#### RC10-D — dead `/api/auth/readonly-validate` allow-list entry

- **Classification:** `PRESENT_BUT_DIFFERENT_AND_VALID`
- **Live evidence:**
  - No occurrences of `/api/auth/readonly-validate` were found in the repo.
  - `backend/routes/production_certification_session.py:63-75` uses an explicit `ALLOWED_READ_PATHS` set that does not include the dead route.
  - `backend/tests/test_track_22_6a_production_certification_session.py:55-88` locks the read-only allowlist shape.
- **Recovery evidence:** recovery target was removal of dead allowlist surface; live matches that intent.
- **Vulnerable to original defect?** No evidence of the dead entry remaining.
- **Recommended action:** none.

#### RC10-E — middleware ordering so `423` responses receive security headers

- **Classification:** `MISSING`
- **Live evidence:**
  - `backend/routes/mfa_routes.py:172-206, 266-302` emits `423` responses for MFA lock conditions.
  - No canonical security-header middleware was found in `backend/server.py` or other reviewed runtime files.
- **Recovery evidence:** RC10 required this ordering guarantee; live does not structurally provide it because the header middleware itself is missing.
- **Vulnerable to original defect?** Yes.
- **Recommended action:** fix together with RC09D-1 by adding canonical middleware at the app layer.

---

## Consolidated Phase 1 action list

### P1 repair candidates confirmed by reconciliation

1. **RC05-DEF-01** — tag PM actors centrally as `_actor_kind="pm_user"` on PM-token success paths.
2. **RC06B-DEF-01** — harden OpenAI wrapped/fenced JSON extraction.
3. **RC07-DEF-01** — support `collections/<name>.json` restore layout correctly.
4. **RC07-DEF-02** — add content-hash restore identity for id-less documents.
5. **RC09C-1** — special-case `/daily-reports/new` to the canonical create route.
6. **RC09D-1 / RC10-E** — add canonical security-header middleware so `423` and other responses inherit the required headers.

### P3 hygiene confirmed by reconciliation

1. **RC05-DEF-02** — repair `duration-&lsqb;400ms&rsqb;` → `duration-[400ms]` in `SplashOverlay.jsx`.

## Checkpoint A verdict

**COMPLETE FOR PHASE 1 DOCUMENTATION.**  
Gate 1 is satisfied by this reconciliation matrix. Broad cleanup must still remain blocked until Phase 2 correctness repairs are completed and verified.

## Production mutation accounting for Checkpoint A

- Atlas reads: **0**
- Atlas writes: **0**
- Production R2 reads: **0**
- Production R2 writes: **0**
- Email/provider calls: **0**
- Dangerous scripts executed: **0**
