#!/usr/bin/env node
/**
 * Auto-stamp the current build version into src/buildVersion.generated.js.
 *
 * Runs automatically before every `yarn build` (via the `prebuild` npm hook),
 * and can also be invoked manually with `node scripts/stamp-build-version.js`.
 *
 * Format: v<YYYY>.<MM>.<DD>[-<commitShort>]
 *   Example: v2026.05.05  (or v2026.05.05-7e494ca if a git rev is available)
 *
 * The generated file is intentionally tiny so the diff is obvious and the
 * file can safely be committed — a deploy that doesn't rebuild won't see a
 * stale version because the value is regenerated on every build.
 */

const fs = require("fs");
const path = require("path");
const crypto = require("crypto");
const { execSync } = require("child_process");

const OUT_FILE = path.join(__dirname, "..", "src", "buildVersion.generated.js");
const PUBLIC_IDENTITY_FILE = path.join(__dirname, "..", "public", "release-identity.json");
const REPO_ROOT = path.join(__dirname, "..", "..");
const SCOPE_FILE = path.join(REPO_ROOT, "release_identity_scope.json");
const FALLBACK_RELEASE_FINGERPRINT_RELATIVE_PATHS = [
  "docs/governance/release_gate_manifest.json",
  "frontend/scripts/stamp-build-version.js",
  "frontend/src/app/routing/AppRoutes.jsx",
  "frontend/src/pages/NewDailyReportV3.jsx",
  "frontend/src/pages/DailyReportsDashboard.jsx",
  "frontend/src/pages/ViewDailyReport.jsx",
];
const RELEASE_FINGERPRINT_RELATIVE_PATHS = fs.existsSync(SCOPE_FILE)
  ? JSON.parse(fs.readFileSync(SCOPE_FILE, "utf8"))
  : FALLBACK_RELEASE_FINGERPRINT_RELATIVE_PATHS;

const pad = (n) => String(n).padStart(2, "0");
let builtAtIso = (process.env.BUILT_AT || process.env.DEPLOY_BUILT_AT || "").trim();

let commit = "";
let commitFull = "";
let commitSource = "";
let branch = "";
let workspaceDirty = false;
const ENV_COMMIT_KEYS = [
  "DEPLOY_VERSION_HASH",
  "DEPLOY_VERSION",
  "GIT_COMMIT",
  "RAILWAY_GIT_COMMIT_SHA",
  "VERCEL_GIT_COMMIT_SHA",
];
try {
  for (const envKey of ENV_COMMIT_KEYS) {
    const value = (process.env[envKey] || "").trim();
    if (!value) continue;
    commitFull = value;
    commit = value.slice(0, 7);
    commitSource = `env:${envKey}`;
    break;
  }
  if (!commitFull) {
    commitFull = execSync("git rev-parse HEAD", {
      cwd: REPO_ROOT,
      stdio: ["ignore", "pipe", "ignore"],
    })
      .toString()
      .trim();
    commit = execSync("git rev-parse --short=7 HEAD", {
      cwd: REPO_ROOT,
      stdio: ["ignore", "pipe", "ignore"],
    })
      .toString()
      .trim();
    commitSource = "git:HEAD";
  }
  branch = execSync("git branch --show-current", {
    cwd: REPO_ROOT,
    stdio: ["ignore", "pipe", "ignore"],
  })
    .toString()
    .trim();
  workspaceDirty = Boolean(
    execSync("git status --short", {
      cwd: REPO_ROOT,
      stdio: ["ignore", "pipe", "ignore"],
    })
      .toString()
      .trim()
  );
} catch {
  // git not available (e.g. inside a stripped Docker layer) — that's fine,
  // we'll just stamp the date.
}

if (!builtAtIso) {
  try {
    builtAtIso = execSync(`git show -s --format=%cI ${commitFull || "HEAD"}`, {
      cwd: REPO_ROOT,
      stdio: ["ignore", "pipe", "ignore"],
    })
      .toString()
      .trim();
  } catch {
    builtAtIso = new Date().toISOString();
  }
}
const builtAtDate = new Date(builtAtIso);
const safeBuiltAtDate = Number.isNaN(builtAtDate.getTime()) ? new Date() : builtAtDate;
const datePart = `${safeBuiltAtDate.getUTCFullYear()}.${pad(safeBuiltAtDate.getUTCMonth() + 1)}.${pad(
  safeBuiltAtDate.getUTCDate()
)}`;
const version = commit ? `v${datePart}-${commit}` : `v${datePart}`;

const sourceHash = (() => {
  const h = crypto.createHash("md5");
  for (const rel of RELEASE_FINGERPRINT_RELATIVE_PATHS) {
    const abs = path.join(REPO_ROOT, rel);
    h.update(rel);
    h.update("\0");
    try {
      h.update(fs.readFileSync(abs));
    } catch {
      h.update(`MISSING:${rel}`);
    }
    h.update("\0");
  }
  return h.digest("hex");
})();

const hashFiles = (algo, rels) => {
  const h = crypto.createHash(algo);
  for (const rel of rels) {
    const abs = path.join(REPO_ROOT, rel);
    h.update(rel);
    h.update("\0");
    try {
      h.update(fs.readFileSync(abs));
    } catch {
      h.update(`MISSING:${rel}`);
    }
    h.update("\0");
  }
  return h.digest("hex");
};

const dependencyManifestHash = hashFiles("sha256", [
  "backend/requirements.txt",
  "frontend/package.json",
  "frontend/yarn.lock",
]);
const migrationManifestHash = hashFiles("sha256", [
  "docs/governance/MIGRATION_COMPATIBILITY_REGISTER.md",
]);
const releaseGateManifestHash = hashFiles("sha256", [
  "docs/governance/release_gate_manifest.json",
]);
let releaseGateManifestVersion = "missing";
let releaseGateManifestId = "missing";
try {
  const manifest = JSON.parse(fs.readFileSync(path.join(REPO_ROOT, "docs", "governance", "release_gate_manifest.json"), "utf8"));
  releaseGateManifestVersion = manifest.schema_version || "missing";
  releaseGateManifestId = manifest.manifest_id || "missing";
} catch {
  void 0;
}

const buildIdentityPayload = (dirtyFlag) => ({
  version,
  commit: commitFull || null,
  commit_source: commitSource || null,
  built_at: builtAtIso,
  source_hash: sourceHash,
  dependency_manifest_hash: dependencyManifestHash,
  migration_manifest_hash: migrationManifestHash,
  release_gate_manifest_hash: releaseGateManifestHash,
  release_gate_manifest_version: releaseGateManifestVersion,
  release_gate_manifest_id: releaseGateManifestId,
  repository: path.basename(REPO_ROOT),
  branch,
  workspace_dirty: dirtyFlag,
});

const buildModuleContent = (dirtyFlag) => {
  const payload = buildIdentityPayload(dirtyFlag);
  return `// AUTO-GENERATED — do not hand-edit.
// Regenerated by /app/frontend/scripts/stamp-build-version.js before the
// frontend artifact compile that serves the browser.
export const BUILD_VERSION = ${JSON.stringify(payload.version)};
export const BUILD_COMMIT = ${JSON.stringify(payload.commit)};
export const BUILD_COMMIT_SOURCE = ${JSON.stringify(payload.commit_source)};
export const BUILT_AT_ISO = ${JSON.stringify(payload.built_at)};
export const BUILD_SOURCE_HASH = ${JSON.stringify(payload.source_hash)};
export const BUILD_DEPENDENCY_MANIFEST_HASH = ${JSON.stringify(payload.dependency_manifest_hash)};
export const BUILD_MIGRATION_MANIFEST_HASH = ${JSON.stringify(payload.migration_manifest_hash)};
export const RELEASE_GATE_MANIFEST_HASH = ${JSON.stringify(payload.release_gate_manifest_hash)};
export const RELEASE_GATE_MANIFEST_VERSION = ${JSON.stringify(payload.release_gate_manifest_version)};
export const RELEASE_GATE_MANIFEST_ID = ${JSON.stringify(payload.release_gate_manifest_id)};
export const BUILD_REPOSITORY = ${JSON.stringify(payload.repository)};
export const BUILD_BRANCH = ${JSON.stringify(payload.branch)};
export const BUILD_WORKSPACE_DIRTY = ${payload.workspace_dirty};
`;
};

const writeIdentityArtifacts = (dirtyFlag) => {
  fs.writeFileSync(OUT_FILE, buildModuleContent(dirtyFlag), "utf8");
  fs.writeFileSync(PUBLIC_IDENTITY_FILE, `${JSON.stringify(buildIdentityPayload(dirtyFlag), null, 2)}\n`, "utf8");
};

writeIdentityArtifacts(workspaceDirty);
try {
  workspaceDirty = Boolean(
    execSync("git status --short", {
      cwd: REPO_ROOT,
      stdio: ["ignore", "pipe", "ignore"],
    })
      .toString()
      .trim()
  );
} catch {
  void 0;
}
writeIdentityArtifacts(workspaceDirty);
const VERIFY_RELEASE_IDENTITY = path.join(REPO_ROOT, "backend", "scripts", "verify_release_identity.py");
const pythonVerifierAvailable = (() => {
  try {
    execSync("python3 --version", {
      cwd: REPO_ROOT,
      stdio: ["ignore", "pipe", "ignore"],
    });
    return true;
  } catch {
    return false;
  }
})();

if (fs.existsSync(VERIFY_RELEASE_IDENTITY) && fs.existsSync(SCOPE_FILE) && pythonVerifierAvailable) {
  try {
    execSync("python3 backend/scripts/verify_release_identity.py", {
      cwd: REPO_ROOT,
      stdio: ["ignore", "pipe", "pipe"],
    });
  } catch (err) {
    process.stderr.write(
      `[stamp-build-version] release identity verification failed: ${err.message}\n`
    );
    process.exit(1);
  }
} else if (!pythonVerifierAvailable) {
  process.stdout.write(
    "[stamp-build-version] release identity verification deferred to backend/runtime stage\n"
  );
} else {
  process.stderr.write("[stamp-build-version] release identity verifier or scope file missing\n");
  process.exit(1);
}
process.stdout.write(`[stamp-build-version] wrote ${version} -> ${OUT_FILE}\n`);
