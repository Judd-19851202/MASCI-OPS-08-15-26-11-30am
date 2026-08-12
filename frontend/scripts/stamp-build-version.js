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
