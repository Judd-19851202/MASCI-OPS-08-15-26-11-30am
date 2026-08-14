#!/usr/bin/env node
const fs = require("fs");
const path = require("path");
const { spawnSync } = require("child_process");

const repoRoot = path.resolve(__dirname, "..", "..");
const srcFile = path.join(repoRoot, "frontend", "src", "buildVersion.generated.js");
const publicFile = path.join(repoRoot, "frontend", "public", "release-identity.json");
const verifierScript = "backend/scripts/verify_release_identity.py";

const pythonCandidates = [
  process.env.PYTHON,
  process.env.npm_config_python,
  process.env.VIRTUAL_ENV ? path.join(process.env.VIRTUAL_ENV, "bin", "python") : null,
  "python3",
  "python",
].filter((value, index, list) => value && list.indexOf(value) === index);

const versionModule = `// Runtime-bound release identity contract.
export const BUILD_VERSION_LABEL = "runtime:/api/version";
export const BUILD_IDENTITY_MODE = "runtime-api-version";
export const BUILD_IDENTITY_ENDPOINT = "/api/version";
export const BUILD_RUNTIME_BINDING_REQUIRED = true;
export const BUILD_POST_SAVE_SOURCE_MUTATION_REQUIRED = false;
export const BUILD_TRACKED_COMMIT_EMBED_ALLOWED = false;
`;

const publicContract = {
  schema_version: "MASCI_FRONTEND_RELEASE_IDENTITY_CONTRACT/v2",
  version_label: "runtime:/api/version",
  identity_mode: "runtime-api-version",
  identity_endpoint: "/api/version",
  runtime_binding_required: true,
  post_save_source_mutation_required: false,
  tracked_commit_embed_allowed: false,
};

fs.mkdirSync(path.dirname(srcFile), { recursive: true });
fs.mkdirSync(path.dirname(publicFile), { recursive: true });
fs.writeFileSync(srcFile, versionModule);
fs.writeFileSync(publicFile, `${JSON.stringify(publicContract, null, 2)}\n`);

// ── STAGE 4/5 · canonical deployable-content provenance (pure JS) ─────────
// Recompute the DEPLOYABLE_CONTENT_FINGERPRINT from the source present at build
// time and stamp it into a generated, non-tracked, gitignored provenance file
// that both the served frontend and the backend runtime consume. If an
// owner-Save attestation (AUTHORIZED_RELEASE.json) is present, the build
// fingerprint MUST equal the authorized fingerprint or the build fails closed —
// this catches deployment from an unsaved/wrong/stale/modified source snapshot.
(function stampDeployableProvenance() {
  const dcf = require("./deployable_content_fingerprint.js");
  const provenanceFile = path.join(repoRoot, "frontend", "public", "release-provenance.json");
  const attestationPath = path.join(repoRoot, dcf.ATTESTATION_REL);

  let buildFingerprint;
  let contractDigest;
  try {
    buildFingerprint = dcf.computeDeployableFingerprint(repoRoot, { strict: true });
    contractDigest = dcf.contractDigest(repoRoot);
  } catch (err) {
    console.error(`[deployable-provenance] fail-closed: ${err.message}`);
    process.exit(1);
  }

  let attestation = null;
  if (fs.existsSync(attestationPath)) {
    try {
      attestation = JSON.parse(fs.readFileSync(attestationPath, "utf8"));
    } catch (err) {
      console.error(`[deployable-provenance] fail-closed: unreadable ${dcf.ATTESTATION_REL}: ${err.message}`);
      process.exit(1);
    }
  }

  // RELEASE-GUARD ARCHITECTURE (P0): PREVIEW EXECUTABILITY != RELEASE AUTHORIZATION.
  // A dev-server start (craco start -> NODE_ENV !== "production") is the PREVIEW
  // sandbox: an unattested/mismatched candidate MUST still serve so it can be QA'd.
  // A production build (craco build -> NODE_ENV === "production") is the release
  // authorization boundary: mismatch stays a HARD FAIL. RELEASE_HARD_FAIL=1 forces
  // hard-fail everywhere (deploy gates).
  const isProductionBuild = process.env.NODE_ENV === "production" || process.env.RELEASE_HARD_FAIL === "1";
  const previewSoftServe = !isProductionBuild;

  let contractMismatch = false;
  let fingerprintMismatch = false;
  if (attestation) {
    if (attestation.fingerprint_contract_digest && attestation.fingerprint_contract_digest !== contractDigest) {
      contractMismatch = true;
    }
    if (attestation.authorized_deployable_fingerprint !== buildFingerprint) {
      fingerprintMismatch = true;
    }
  }
  const mismatch = contractMismatch || fingerprintMismatch;
  const runtimeMatchesAuthorized = Boolean(attestation) && !mismatch;
  const deployAuthorized = runtimeMatchesAuthorized;

  if (mismatch && isProductionBuild) {
    if (contractMismatch) {
      console.error("[deployable-provenance] fail-closed: CONTRACT_MISMATCH — authorized contract digest != build contract digest");
    } else {
      console.error(
        `[deployable-provenance] fail-closed: MISMATCH — build source does not match authorized release.\n` +
        `  authorized_deployable_fingerprint = ${attestation.authorized_deployable_fingerprint}\n` +
        `  build_deployable_fingerprint      = ${buildFingerprint}`
      );
    }
    process.exit(1);
  }

  const releaseProvenance = deployAuthorized
    ? "AUTHORIZED_RELEASE"
    : "UNATTESTED_CANDIDATE";

  const provenance = {
    schema_version: "MASCI_DEPLOYABLE_RELEASE_PROVENANCE/v1",
    provenance_format_version: "1",
    fingerprint_algorithm_version: dcf.FINGERPRINT_ALGORITHM_VERSION,
    fingerprint_contract_digest: contractDigest,
    build_deployable_fingerprint: buildFingerprint,
    current_candidate_fingerprint: buildFingerprint,
    authorized_saved_sha: attestation ? attestation.authorized_saved_sha || null : null,
    authorized_deployable_fingerprint: attestation ? attestation.authorized_deployable_fingerprint || null : null,
    authorized_saved_fingerprint: attestation ? attestation.authorized_deployable_fingerprint || null : null,
    attestation_present: Boolean(attestation),
    // ── environment-aware release-provenance state ───────────────────────
    environment: previewSoftServe ? "PREVIEW" : "PRODUCTION_BUILD",
    release_provenance: releaseProvenance,
    runtime_matches_authorized_release: runtimeMatchesAuthorized,
    deploy_authorized: deployAuthorized,
  };
  fs.writeFileSync(provenanceFile, `${JSON.stringify(provenance, null, 2)}\n`);
  if (mismatch && previewSoftServe) {
    console.warn(
      `[deployable-provenance] PREVIEW — UNATTESTED CANDIDATE — NOT AUTHORIZED FOR DEPLOYMENT\n` +
      `  current_candidate_fingerprint  = ${buildFingerprint}\n` +
      `  authorized_saved_fingerprint   = ${attestation ? attestation.authorized_deployable_fingerprint : "(none)"}\n` +
      `  deploy_authorized=false · serving for QA only (release fail-close preserved for production build/deploy).`
    );
  }
  console.log(
    `[deployable-provenance] build_deployable_fingerprint=${buildFingerprint} ` +
    `attestation_present=${Boolean(attestation)} release_provenance=${releaseProvenance} ` +
    `deploy_authorized=${deployAuthorized}`
  );
})();

function verifyGeneratedRuntimeContract() {
  const generatedSource = fs.readFileSync(srcFile, 'utf8');
  const generatedPublic = JSON.parse(fs.readFileSync(publicFile, 'utf8'));
  const errors = [];
  const embeddedCommitToken = 'BUILD' + '_COMMIT';

  if (!generatedSource.includes('BUILD_IDENTITY_MODE = "runtime-api-version"')) {
    errors.push('generated build identity mode is not runtime-api-version');
  }

  if (!generatedSource.includes('BUILD_IDENTITY_ENDPOINT = "/api/version"')) {
    errors.push('generated build identity endpoint is not /api/version');
  }

  if (generatedSource.includes(embeddedCommitToken)) {
    errors.push(`generated build unexpectedly embeds ${embeddedCommitToken}`);
  }

  if (generatedPublic.identity_mode !== 'runtime-api-version') {
    errors.push('public release identity mode is not runtime-api-version');
  }

  if (generatedPublic.identity_endpoint !== '/api/version') {
    errors.push('public release identity endpoint is not /api/version');
  }

  if (generatedPublic.post_save_source_mutation_required !== false) {
    errors.push('public release identity still requires post-save mutation');
  }

  if (generatedPublic.tracked_commit_embed_allowed !== false) {
    errors.push('public release identity still allows embedded tracked commit');
  }

  return errors;
}

let lastFailure = null;

for (const pythonExecutable of pythonCandidates) {
  const verify = spawnSync(pythonExecutable, [verifierScript], {
    cwd: repoRoot,
    stdio: "inherit",
  });

  if (!verify.error && verify.status === 0) {
    process.exit(0);
  }

  lastFailure = verify.error || new Error(`Verifier exited with status ${verify.status || 1}`);

  if (!verify.error || verify.error.code !== "ENOENT") {
    process.exit(verify.status || 1);
  }
}

console.error(
  `[release-identity] failed to find a usable Python interpreter. Tried: ${pythonCandidates.join(", ")}`
);

if (lastFailure) {
  console.error(lastFailure.message || String(lastFailure));
}

const fallbackErrors = verifyGeneratedRuntimeContract();

if (fallbackErrors.length === 0) {
  console.warn('[release-identity] Python verifier unavailable; falling back to generated runtime-contract validation.');
  process.exit(0);
}

for (const error of fallbackErrors) {
  console.error(`[release-identity] ${error}`);
}

process.exit(1);
