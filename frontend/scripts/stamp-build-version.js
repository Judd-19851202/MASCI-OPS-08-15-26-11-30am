#!/usr/bin/env node
const fs = require("fs");
const path = require("path");
const { spawnSync } = require("child_process");

const repoRoot = path.resolve(__dirname, "..", "..");
const srcFile = path.join(repoRoot, "frontend", "src", "buildVersion.generated.js");
const publicFile = path.join(repoRoot, "frontend", "public", "release-identity.json");
const pythonExecutable =
  process.env.PYTHON ||
  process.env.npm_config_python ||
  (process.env.VIRTUAL_ENV ? path.join(process.env.VIRTUAL_ENV, "bin", "python") : "python");

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

fs.writeFileSync(srcFile, versionModule);
fs.writeFileSync(publicFile, `${JSON.stringify(publicContract, null, 2)}\n`);

const verify = spawnSync(pythonExecutable, ["backend/scripts/verify_release_identity.py"], {
  cwd: repoRoot,
  stdio: "inherit",
});

if (verify.status !== 0) {
  process.exit(verify.status || 1);
}
