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

process.exit(1);
