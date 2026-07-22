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
const now = new Date();
const datePart = `${now.getUTCFullYear()}.${pad(now.getUTCMonth() + 1)}.${pad(
  now.getUTCDate()
)}`;

let commit = "";
let commitFull = "";
let branch = "";
let workspaceDirty = false;
try {
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

const version = commit ? `v${datePart}-${commit}` : `v${datePart}`;
const builtAtIso = now.toISOString();

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

const content = `// AUTO-GENERATED — do not hand-edit.
// Regenerated on every \`yarn build\` by /app/frontend/scripts/stamp-build-version.js
//
// Field crews / PMs / support: when reporting an issue, include this version
// so we can pin the exact deployed code.
export const BUILD_VERSION = ${JSON.stringify(version)};
export const BUILD_COMMIT = ${JSON.stringify(commitFull)};
export const BUILT_AT_ISO = ${JSON.stringify(builtAtIso)};
export const BUILD_SOURCE_HASH = ${JSON.stringify(sourceHash)};
export const BUILD_DEPENDENCY_MANIFEST_HASH = ${JSON.stringify(dependencyManifestHash)};
export const BUILD_MIGRATION_MANIFEST_HASH = ${JSON.stringify(migrationManifestHash)};
export const RELEASE_GATE_MANIFEST_HASH = ${JSON.stringify(releaseGateManifestHash)};
export const RELEASE_GATE_MANIFEST_VERSION = ${JSON.stringify(releaseGateManifestVersion)};
export const RELEASE_GATE_MANIFEST_ID = ${JSON.stringify(releaseGateManifestId)};
export const BUILD_REPOSITORY = ${JSON.stringify(path.basename(REPO_ROOT))};
export const BUILD_BRANCH = ${JSON.stringify(branch)};
export const BUILD_WORKSPACE_DIRTY = ${workspaceDirty};
`;

fs.writeFileSync(OUT_FILE, content, "utf8");
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
const finalizedContent = content.replace(
  /export const BUILD_WORKSPACE_DIRTY = (true|false);/,
  `export const BUILD_WORKSPACE_DIRTY = ${workspaceDirty};`
);
fs.writeFileSync(OUT_FILE, finalizedContent, "utf8");
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
