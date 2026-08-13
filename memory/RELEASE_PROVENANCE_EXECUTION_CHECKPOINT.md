# MASCI OPS — CANONICAL RELEASE PROVENANCE — EXECUTION CHECKPOINT (RESUME HERE)

STATUS: IMPLEMENTED + FULLY PROVEN — READY FOR OWNER SAVE (agent did NOT Save/Deploy). Architecture LOCKED.
Saved SHA at implementation: 40a16150c87a6a1f9a4b0b43d9d47fd55a468707. Gate 16: DEFERRED/NOT PASSED.
Production: FUNCTIONALLY HEALTHY / PROVENANCE UNBOUND (until this candidate is saved+redeployed+proven live).
Canonical F (this candidate) = dcf-7f0458dc2060c44100e255553c59ba332c1b86d755789365b2aac315bb1b2d72
Contract digest = c-eb2678608cf918235470aa2b8a6103becabfdb1e2fe591645688a15e638dd533
POST-SAVE STEP (owner/agent, after Save): capture real saved SHA S, run
`PYTHONPATH=backend python -m lib.deployable_content_fingerprint attest <S> > AUTHORIZED_RELEASE.json`
(gitignored), then normal build stamps + runtime evaluates VERIFIED. No second Save required.

## ROOT CAUSE (established)
`backend/lib/release_identity.py::compute_source_hash` → `release_fingerprint.py::build_release_manifest`
hashes files PHYSICALLY PRESENT under contract scope. Local frozen tree = 4314 entries; prod container
= 2058. Different file sets → runtime source-tree recompute can never equal freeze. Fix = build-time
recompute + stamp; runtime consumes the stamp, NOT the source tree.

## LOCKED ARCHITECTURE (implement exactly — do NOT redesign)
- STAGE1 canonical DEPLOYABLE_CONTENT_FINGERPRINT over governed SOURCE-INPUT contract
  (FE src, BE src, shared libs, models/schemas, business logic, build scripts, repo runtime/build config,
   frontend/package.json, frontend/yarn.lock, backend/requirements.txt, release-critical config).
  Exclude: .git, caches, logs, screenshots, evidence, generated build output, temp, generated attestation.
  Contract gets fingerprint_contract_digest + version. AUDIT existing contract
  `docs/governance/release_content_fingerprint_contract.json` before finalizing.
- STAGE2 pre-save F_candidate (recompute twice equal); post-save F_saved==F_candidate; bind S<->F.
- STAGE3 generated attestation AUTHORIZED_RELEASE.json: authorized_saved_sha, authorized_deployable_fingerprint,
  fingerprint_algorithm_version, fingerprint_contract_digest, attestation_format_version. MUST be
  non-tracked, gitignored, EXCLUDED from fingerprint, non-self-referential, NO second Save.
- STAGE4 build recompute F_build in real build context (add to `frontend/scripts/stamp-build-version.js`
  pure-JS path — NOTE: no python in cloud build) → compare F_build==F_authorized; catches unsaved/wrong snapshot.
- STAGE5 stamp FE + BE identically: authorized_saved_sha, authorized_deployable_fingerprint,
  build_deployable_fingerprint, fingerprint_contract_digest, fingerprint_algorithm_version.
  FE stamp file: frontend/src/buildVersion.generated.js + frontend/public/release-identity.json.
- STAGE6 runtime (release_identity.py public payload builder ~L248-267) consumes stamp; NO source-tree recompute,
  NO MISSING sentinels for intentional omissions. VERIFIED when F_build==F_authorized && contract_digest match
  && FE/BE agree → runtime_matches_intended_release=true, release_provenance=VERIFIED,
  provenance_method=build_content_fingerprint_bound_to_saved_sha, authorized_saved_sha=S. Never synthesize git SHA.
- STAGE7 optional runtime_artifact_fingerprint (separate hash space; never compared to source-input identity).
- FAIL-CLOSED: UNPROVEN (no attestation) / MISMATCH / CONTRACT_MISMATCH / ARTIFACT_IDENTITY_MISMATCH / VERIFIED.
- RENAME/RETIRE: `commit_source=source_hash_prefix` (retire fake-commit); demote
  release_manifest_sha256 -> workspace_diagnostic_manifest_sha256 (diagnostic only, never equality).
  Explicit fields: authorized_saved_sha, deployable_content_fingerprint, build_deployable_content_fingerprint,
  workspace_diagnostic_manifest_sha256, runtime_artifact_fingerprint, fingerprint_contract_digest.

## KEY FILES
- backend/lib/release_identity.py (compute_source_hash L97-98; identity payload L121-267; UNSAVED label L131-132)
- backend/lib/release_fingerprint.py (build_release_manifest; contract loader; CONTRACT_PATH L14)
- backend/scripts/verify_release_identity.py (expose canonical + contract digest; demote manifest)
- docs/governance/release_content_fingerprint_contract.json (scope + add digest/version; exclude AUTHORIZED_RELEASE.json)
- frontend/scripts/stamp-build-version.js (STAGE4 recompute + STAGE5 stamp; PURE JS — no python)
- frontend/public/release-identity.json, frontend/src/buildVersion.generated.js (stamp targets)
- backend/routes: /api/version payload source (search "runtime_identity_public_payload")
- .gitignore + release_gate_manifest.json allowlist: add AUTHORIZED_RELEASE.json (generated, non-tracked)
- NEW backend/tests/test_release_provenance_contract.py (~22-case fail-closed matrix per owner spec)

## GOVERNANCE
Every new/changed tracked file MUST be added to docs/governance/release_gate_manifest.json allowed_dirty_entries
(else pre-save gate fails). Verify: PYTHONPATH=backend python -c evaluate_pre_save_candidate (see prior turns).
Recompute fingerprint twice for equality. verify_release_identity --strict must be errors:[]. Do NOT Save.

## PARALLEL LIVE ACCEPTANCE (separate, read-only — outstanding)
exhaustive per-form selector click-through; Safety-role session proof (/api/safety/overview 401 under admin token);
full KPI/portal matrix (12/13 done); real-device queue recovery (SERVER READY / DEVICE PROOF PENDING).

## FINAL DEFECT-CLOSURE ATTESTATION (2026-06 — agent-tested, read-only)
Saved SHA S = aa842953f2e126b048cb057f46f2febdf59f7449 (HEAD, workspace clean).
Canonical FP recompute = dcf-27b86fc225a3da074e3e77fa292d9b17fc0abb0f5af4d39b05b67852b0419114 (EXACT MATCH).
Contract digest = c-eb2678608cf918235470aa2b8a6103becabfdb1e2fe591645688a15e638dd533 (UNCHANGED).
AUTHORIZED_RELEASE.json: authorized_saved_sha=S, authorized FP=required FP, digest match; gitignored/non-tracked.
Build provenance path (stamp-build-version.js): build_deployable_fingerprint == authorized FP, attestation_present=true, errors:[].
Runtime /api/version: release_provenance=VERIFIED, runtime_matches_intended_release=true,
  provenance_method=build_content_fingerprint_bound_to_saved_sha, authorized_saved_sha=S,
  frontend_backend_release_match=true, frontend_generated_vs_served_match=true.
Strict verifier: ok=true, errors:[], all commits==S.
Post-attestation: git status clean (0 lines), HEAD unchanged, no second Save, no Deploy, production untouched.
RESULT: FINAL DEFECT-CLOSURE RELEASE ATTESTED — READY FOR OWNER DEPLOY.
Provenance of this record: agent-tested via shell/curl; not user-confirmed.

## LIVE PROD OPERATIONAL HEALTH — SUPER ADMIN BROWSER SESSION (2026-08-13, read-only)
Auth: real Super Admin browser login jaymn.judd@mascigc.com at https://mascidocs.com -> /admin OK.
Strict admin endpoints returned 200 (NOT 401) => NOT owner-only. Earlier 401 was automation-token only.
- system-health: overall GREEN/VERIFIED (9/9). runtime env=production db=masci_safety.
- Motive: VERIFIED · Live · webhook armed · last_successful_sync=2026-08-13T20:36:36.750281Z · last_failed=2026-07-20T17:37:35Z · failed_syncs_24h=0.
- integrations/health: Motive ok(live), Mongo ok, R2 ok, Resend ok, MaintainX disabled(NOT_APPLICABLE/mocked), Emergent LLM ok.
- Backup: recovery pill GREEN; last backup MASCI_complete_backup_2026-08-13_200040Z.zip; recovery point 2026-08-13T20:08:45Z; age 38.2m (target <=60m); integrity PASS/COMPLETE/AVAILABLE.
- backup-verification cron: enabled; schedule Mon 14:00 UTC; next_fire=2026-08-17T14:00:00Z; last_run=2026-08-10T14:00Z.
- Transportation<->HR (hr-sync/report): health=warning; employees_checked=36; sync_mismatches=1; actions_created=0.
  * The 1 mismatch: employee_id 143acca5-31c4-4528-8a7b-0df524672d97, code hr_active_no_linkage, severity info,
    "Active driver-relevant HR employee has no Transportation link", transport_person_id=null.
  * actions_created=0 root cause: automation last_run items_scanned=0/actions_created=0; finding severity=info AND
    TRANSPORT_HR_SYNC_MONITOR_ALERT is in routes_dry_run (not routes_live) -> info advisory creates 0 actions by design
    (manual link recommended). Expected behavior, not a defect.
- Admin Equipment Parts list: parts-catalog renders; Pick-a-Unit fleet populated (100 rendered / "589-unit fleet" searchable);
  no "Could not load fleet list"; /equipment-master 401 -> fallback /public/equipment-master-lookup 200 (fallback fix live);
  picking a unit opens parts editor. Note: parts-detail 401 for first row due to malformed unit_number data ("#71 in Masci Equip list"),
  not a feature break.
REMOVED FROM OWNER-ONLY: Operational Health dashboard, Motive health, backup scheduler, Transportation<->HR mismatch.
STILL OPEN (genuinely): real stranded operator-device queue recovery (device-only); Gate 16 OWNER-DEFERRED/NOT PASSED.

## PROD EQUIPMENT MASTER RECONCILIATION (2026-08-13, read-only, no writes)
Authoritative /api/admin/equipment-master/status: total active=604, archived=0.
Parts eligibility (from canonical public lookup): eligible(non-empty unit_number)=357; missing unit_number=247; malformed=4; duplicates=0.
247 missing = unnumbered tools/small equip identified by make/model only (largest bucket Misc Equipment 165) -> legitimately excluded from Parts (parts key on unit_number).
4 malformed unit_number records:
  1) 647b1857-e466-4bea-882f-5427bca84201  "#71 in Masci Equip list"  Cat AIR COMPRESSOR/PORTABLE  Air Compressors
  2) 775801b0-2c5a-4287-8b37-bfbfcd95344e  "#107 MASCI LIST"          MUSTANG LF88               Compactors
  3) 3f0c53f8-2b8e-4ed5-84dd-7db595e79e8b  "#98 MASCI EQUIP"          Magnum PRO MLT6S           Light Towers
  4) bec8e9b3-0925-4163-8de6-799006f7d01c  "RC1-POST-REDEPLOY-VERIFY-1781535563"  Cert Post-Redeploy  Trench Safety  (STRAY certification test fixture)
Parts-detail 401 ROOT CAUSE = AUTHORIZATION (not malformed data, not key construction): clean unit EXC-8614 ALSO 401 "Shop login required".
  /api/equipment-parts/{unit} uses require_shop_or_admin -> accepts admin only via stricter _is_valid_directory_admin_token_async; standard admin-portal token (passes require_admin -> /api/admin/equipment-parts/status=200) does NOT satisfy it; path not under /api/admin/ so falls through to shop branch -> 401. %23 encoding handled fine.
589/15 verdict: NOT governed. "589-unit fleet" is a HARDCODED UI string in PartsCatalog.jsx (lines 15,269). Real eligible=357 -> 604-357=247 (fully explained). The "15" has no governed basis (stale UI copy drift).
equipment_parts collection has only 2 unit catalogs on file (/api/admin/equipment-parts/status count=2).

## EQUIPMENT PARTS 401 — PROVEN CODE DEFECT (frontend auth-scope), 2026-08-13
Trace: record id 647b1857... (canonical id valid) -> displayed unit "#71 in Masci Equip list"
 -> app request GET /api/equipment-parts/{unit_number} -> api client applyScopedAuthHeaders ->
 inferPortalsForApiPath("/equipment-parts/..","admin") returns [] because "/equipment-parts" is NOT in
 portalAuthScope allowlists (grep count=0) -> NO X-Admin/X-Directory token attached ->
 backend require_shop_or_admin: no admin token satisfying _is_valid_directory_admin_token_async, path not /api/admin/,
 no shop token -> 401 "Shop login required". Auth dependency runs BEFORE unit_number is used => malformed data irrelevant.
Proof: admin-only 401; admin+directory 200 (returns parts doc); clean unit EXC-8614 behaves identically.
CLASSIFICATION = AUTHORIZATION via FRONTEND header-scoping omission. Reproduced in preview (no-token -> 401 "Shop login required").
Proposed repair (NOT applied): add "/equipment-parts" to ADMIN_SHARED_API_PREFIXES in frontend/src/lib/portalAuthScope.js
 so admin (directory-compatible) requests attach X-Admin-Token + X-Directory-Token. Preview-first, no Save/Deploy.
Counts (prod canonical): total 604 (active 604, archived 0); parts-eligible 357; ineligible 247 (empty unit_number);
 malformed 4 (subset of eligible); duplicates 0. "589-unit fleet" is a HARDCODED UI string, not a live count -> no real 15-delta.
