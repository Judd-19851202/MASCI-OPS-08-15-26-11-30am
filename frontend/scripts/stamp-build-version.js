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
const RELEASE_FINGERPRINT_RELATIVE_PATHS = JSON.parse(fs.readFileSync(SCOPE_FILE, "utf8"));

const pad = (n) => String(n).padStart(2, "0");
const now = new Date();
const datePart = `${now.getUTCFullYear()}.${pad(now.getUTCMonth() + 1)}.${pad(
  now.getUTCDate()
)}`;

let commit = "";
let commitFull = "";
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
    try {
      h.update(fs.readFileSync(abs));
    } catch {
      h.update(`MISSING:${rel}`);
    }
  }
  return h.digest("hex");
})();

const content = `// AUTO-GENERATED — do not hand-edit.
// Regenerated on every \`yarn build\` by /app/frontend/scripts/stamp-build-version.js
//
// Field crews / PMs / support: when reporting an issue, include this version
// so we can pin the exact deployed code.
export const BUILD_VERSION = ${JSON.stringify(version)};
export const BUILD_COMMIT = ${JSON.stringify(commitFull)};
export const BUILT_AT_ISO = ${JSON.stringify(builtAtIso)};
export const BUILD_SOURCE_HASH = ${JSON.stringify(sourceHash)};
`;

fs.writeFileSync(OUT_FILE, content, "utf8");
execSync("python3 backend/scripts/verify_release_identity.py", {
  cwd: REPO_ROOT,
  stdio: ["ignore", "pipe", "pipe"],
});
process.stdout.write(`[stamp-build-version] wrote ${version} -> ${OUT_FILE}\n`);
