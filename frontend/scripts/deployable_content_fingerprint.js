#!/usr/bin/env node
/*
 * Pure-JS mirror of backend/lib/deployable_content_fingerprint.py.
 *
 * Cloud frontend build environments may have NO python, so the STAGE 4 build
 * recomputation of the canonical DEPLOYABLE_CONTENT_FINGERPRINT must be pure
 * JavaScript. This module MUST stay byte-identical to the Python owner:
 *   fingerprint = "dcf-" + sha256hex(
 *      ALGO + "\0" + contract_digest + "\0" +
 *      for each sorted rel path: rel + "\0" + fileHashHexOrMISSING + "\0")
 *   fileHashHex   = sha256hex(normalize(rawBytes))
 *   normalize     = CRLF/CR -> LF
 *   contract_digest = "c-" + sha256hex(normalize(contractFileBytes))
 */
"use strict";
const fs = require("fs");
const path = require("path");
const crypto = require("crypto");

const FINGERPRINT_ALGORITHM_VERSION = "dcf-1";
const CONTRACT_REL = "docs/governance/release_content_fingerprint_contract.json";
const CONTRACT_SECTION = "deployable_source_inputs";
const ATTESTATION_REL = "AUTHORIZED_RELEASE.json";

function normalizeBytes(buf) {
  // latin1 round-trip preserves every byte 1:1, matching Python's bytewise
  // replace of b"\r\n"->b"\n" then b"\r"->b"\n".
  const s = buf.toString("latin1").replace(/\r\n/g, "\n").replace(/\r/g, "\n");
  return Buffer.from(s, "latin1");
}

function shaHex(buf) {
  return crypto.createHash("sha256").update(buf).digest("hex");
}

function contractDigest(repoRoot) {
  const raw = fs.readFileSync(path.join(repoRoot, CONTRACT_REL));
  return "c-" + shaHex(normalizeBytes(raw));
}

function loadContract(repoRoot) {
  const raw = JSON.parse(fs.readFileSync(path.join(repoRoot, CONTRACT_REL), "utf8"));
  const section = raw[CONTRACT_SECTION];
  if (!section || typeof section !== "object") {
    throw new Error(`contract missing required section '${CONTRACT_SECTION}'`);
  }
  return section;
}

// Replicate CPython fnmatch.translate semantics for our patterns:
//   '*' -> '.*' (matches across '/'), '?' -> '.', else re.escape.
function fnmatchToRegExp(glob) {
  let re = "";
  for (const ch of glob) {
    if (ch === "*") re += ".*";
    else if (ch === "?") re += ".";
    else re += ch.replace(/[.+^${}()|[\]\\]/g, "\\$&");
  }
  return new RegExp("^(?:" + re + ")$", "s");
}

function walkFiles(base, repoRoot, out) {
  let stat;
  try {
    stat = fs.statSync(base);
  } catch (e) {
    return false; // missing root
  }
  if (stat.isFile()) {
    out.push(path.relative(repoRoot, base).split(path.sep).join("/"));
    return true;
  }
  const entries = fs.readdirSync(base, { withFileTypes: true });
  for (const ent of entries) {
    const full = path.join(base, ent.name);
    if (ent.isDirectory()) walkFiles(full, repoRoot, out);
    else if (ent.isFile()) out.push(path.relative(repoRoot, full).split(path.sep).join("/"));
    else if (ent.isSymbolicLink()) {
      try {
        if (fs.statSync(full).isFile()) out.push(path.relative(repoRoot, full).split(path.sep).join("/"));
      } catch (e) { /* dangling symlink: skip */ }
    }
  }
  return true;
}

function enumerateSourceInputs(repoRoot) {
  const contract = loadContract(repoRoot);
  const roots = contract.include_roots || ["."];
  const excludeExact = new Set(contract.exclude_exact || []);
  excludeExact.add(ATTESTATION_REL);
  const excludeRes = (contract.exclude_globs || []).map(fnmatchToRegExp);

  const found = [];
  const missingRoots = [];
  for (const root of roots) {
    const base = path.join(repoRoot, root);
    const raw = [];
    const present = walkFiles(base, repoRoot, raw);
    if (!present) {
      missingRoots.push(root);
      continue;
    }
    for (const rel of raw) {
      if (excludeExact.has(rel)) continue;
      if (excludeRes.some((r) => r.test(rel))) continue;
      found.push(rel);
    }
  }
  const unique = Array.from(new Set(found));
  unique.sort((a, b) => (a < b ? -1 : a > b ? 1 : 0));
  return { entries: unique, missingRoots: Array.from(new Set(missingRoots)).sort() };
}

function computeDeployableFingerprint(repoRoot, opts = {}) {
  const { entries, missingRoots } = enumerateSourceInputs(repoRoot);
  if (opts.strict && missingRoots.length) {
    throw new Error("missing required source input root(s): " + missingRoots.join(", "));
  }
  const hasher = crypto.createHash("sha256");
  const NUL = Buffer.from([0]);
  hasher.update(Buffer.from(FINGERPRINT_ALGORITHM_VERSION + "\0", "utf8"));
  hasher.update(Buffer.from(contractDigest(repoRoot) + "\0", "utf8"));
  for (const rel of entries) {
    hasher.update(Buffer.from(rel, "utf8"));
    hasher.update(NUL);
    let fileHex = "MISSING";
    try {
      fileHex = shaHex(normalizeBytes(fs.readFileSync(path.join(repoRoot, rel))));
    } catch (e) { /* treat unreadable as MISSING */ }
    hasher.update(Buffer.from(fileHex, "utf8"));
    hasher.update(NUL);
  }
  return "dcf-" + hasher.digest("hex");
}

module.exports = {
  FINGERPRINT_ALGORITHM_VERSION,
  CONTRACT_REL,
  ATTESTATION_REL,
  contractDigest,
  enumerateSourceInputs,
  computeDeployableFingerprint,
};

if (require.main === module) {
  const repoRoot = path.resolve(__dirname, "..", "..");
  const cmd = process.argv[2] || "compute";
  if (cmd === "compute") {
    process.stdout.write(computeDeployableFingerprint(repoRoot, { strict: process.argv.includes("--strict") }) + "\n");
  } else if (cmd === "digest") {
    process.stdout.write(contractDigest(repoRoot) + "\n");
  } else if (cmd === "enumerate") {
    const r = enumerateSourceInputs(repoRoot);
    process.stdout.write(JSON.stringify({ count: r.entries.length, missing_roots: r.missingRoots, entries: r.entries }, null, 2) + "\n");
  } else {
    process.stderr.write(`unknown command: ${cmd}\n`);
    process.exit(2);
  }
}
