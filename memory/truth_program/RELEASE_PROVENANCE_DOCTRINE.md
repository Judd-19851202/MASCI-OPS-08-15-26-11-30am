# RELEASE-PROVENANCE DOCTRINE (P0 architecture correction — 2026-06)

## PREVIEW EXECUTABILITY ≠ RELEASE AUTHORIZATION
These are two DIFFERENT security states and must never be conflated:
- **NOT AUTHORIZED FOR DEPLOYMENT** — the candidate's fingerprint does not match the last
  owner-Saved authorized fingerprint. Correct for any unsaved work-in-progress.
- **NOT ALLOWED TO RUN IN THE PREVIEW SANDBOX** — a hard outage. This must NOT be the
  representation of an unsaved candidate.

A candidate MUST be inspectable BEFORE it is authorized. Authorization governs whether it can
become production — NOT whether developers/owners may inspect it in the sandbox.

## Environment-aware behavior (implemented)
`frontend/scripts/stamp-build-version.js` is now environment-aware:
- **PREVIEW / dev-serve** (`NODE_ENV !== "production"`): on a fingerprint/contract MISMATCH the
  build DOES NOT fail — it serves, and stamps `frontend/public/release-provenance.json` with:
  `environment=PREVIEW`, `release_provenance=UNATTESTED_CANDIDATE`,
  `runtime_matches_authorized_release=false`, `deploy_authorized=false`,
  `current_candidate_fingerprint`, `authorized_saved_fingerprint`.
  `EnvBanner.jsx` shows a persistent magenta banner
  "PREVIEW — UNATTESTED CANDIDATE — NOT AUTHORIZED FOR DEPLOYMENT" (only when app_env != production).
- **PRODUCTION build** (`NODE_ENV === "production"`) and **DEPLOY gate** (`RELEASE_HARD_FAIL=1`):
  a mismatch remains a HARD FAIL (`process.exit(1)`). No bypass.

## What Preview serving an unattested candidate must NEVER do
- rewrite `AUTHORIZED_RELEASE.json`
- fake VERIFIED provenance / a saved SHA
- set `deploy_authorized=true`
- grant Preview direct production-DB access (Preview stays on `masci_safety_preview`;
  live production census stays READ-ONLY via governed production APIs)

## Owner Save remains the ONLY authorization path
Only an owner Save converts `UNATTESTED_CANDIDATE` → `AUTHORIZED_RELEASE`, via the canonical
attestation generator. Preview execution and release authorization are fully separate.

## Enforcement (test matrix — GD-0034, backend/tests/test_gd0034_preview_release_guard.py)
- PREVIEW + MISMATCH → SERVES as UNATTESTED (exit 0, honest flags) — PASS
- PRODUCTION build + MISMATCH → HARD FAIL (exit 1) — PASS
- DEPLOY gate (RELEASE_HARD_FAIL=1) + MISMATCH → HARD FAIL — PASS
- Preview provenance never forges authorization — PASS
Production/runtime hard fail-close is preserved and independently proven.
