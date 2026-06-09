/**
 * projectIdentity.js — Canonical Project Identity Resolver
 *
 * PROJECT-IDENTITY-002 · OMEGA DIRECTIVE
 *
 * Single source of truth for translating a record's stored project
 * fields into a canonical (jobs_master-backed) identity for read-time
 * grouping and display.
 *
 * Doctrine:
 *   • jobs_master is authoritative.
 *   • Historical fields (submitted_project_*) are immutable.
 *   • Canonical identity is computed at read time. Never mutates input.
 *   • Exact match only. No fuzzy matching. No auto-aliases. No guessing.
 *   • Unknown remains unknown.
 *
 * Every caller MUST explicitly handle all four resolution states.
 * No silent default. No implicit fallback. Future developers must
 * intentionally choose behavior. This is a platform safeguard.
 *
 * ──────────────────────────────────────────────────────────────────
 *
 * @typedef {("canonical"|"project_number_match"|"project_number_normalized"|"submitted_only"|"orphan")}
 *   ProjectIdentityStatus
 *
 *   • canonical             — record carries jobs_master_id (or project_id)
 *                             that matches an entry in jobs_master.
 *   • project_number_match  — record.project_number (case-insensitive,
 *                             trimmed) exactly matches a jobs_master row.
 *   • project_number_normalized — record.project_number does not exact-match
 *                             but after whitespace/dash/casing normalization
 *                             resolves to exactly one jobs_master row. 100%
 *                             deterministic — no fuzzy logic. Surfaced in
 *                             the Governance Center as a Type C item so the
 *                             operator can confirm or reject the inference.
 *   • submitted_only        — project_number is populated but no
 *                             jobs_master match. Display submitted values.
 *                             Surface to admin for reconciliation.
 *   • orphan                — no usable project_number at all.
 *
 * @typedef {Object} ProjectIdentity
 * @property {?string} jobs_master_id              — canonical UUID when known
 * @property {?string} canonical_project_number    — canonical PN when known
 * @property {?string} canonical_project_name      — canonical name when known
 * @property {string}  submitted_project_number    — original PN from record
 * @property {string}  submitted_project_name      — original name from record
 * @property {ProjectIdentityStatus} resolution_status
 * @property {number}  confidence                  — 0–100
 * @property {("jobs_master_id"|"project_number"|"submitted"|"orphan")} source
 *
 * @typedef {Object} ResolverContext
 * @property {Object<string, string>} [jobsMasterByPn]   — { project_number: project_name }
 * @property {Object<string, Object>} [jobsMasterById]   — { id: jobs_master_doc }
 */

/**
 * Read-time PN normalization for the `project_number_normalized` state.
 *
 * Doctrine: ONLY whitespace, dash, and casing. NOTHING else.
 * No suffix stripping. No phonetic matching. No fuzzy logic.
 * Deterministic. Idempotent.
 *
 * Used in two places:
 *   1. The frontend resolver (this file) — surfaces a confident
 *      `project_number_normalized` state when EXACTLY one canonical row
 *      matches the normalized form.
 *   2. The backend Governance Center (Python mirror of this function in
 *      routes/project_identity_governance.py:normalize_pn) — Type C
 *      conflicts use the same rule.
 *
 * @param {string} pn
 * @returns {string}
 */
export function normalizePn(pn) {
  if (!pn) return "";
  // upper-case + outer trim
  let s = String(pn).trim().toUpperCase();
  // collapse runs of whitespace
  s = s.replace(/\s+/g, " ");
  // normalize " - " / " -" / "- " variants to consistent " - "
  s = s.replace(/\s*-\s*/g, " - ");
  return s.trim();
}

/**
 * Build a canonical lookup map from a /jobs-master payload.
 * Keys are uppercased & trimmed so callers don't have to.
 *
 * @param {Array<{project_number: string, project_name: string, id?: string}>} rows
 * @returns {{ byPn: Object<string, {project_number: string, project_name: string, id?: string}>,
 *            byId: Object<string, {project_number: string, project_name: string, id?: string}> }}
 */
export function buildJobsMasterMaps(rows) {
  const byPn = {};
  const byNorm = {};
  const byId = {};
  for (const j of rows || []) {
    if (!j) continue;
    const pn = (j.project_number || "").trim();
    if (pn) {
      byPn[pn.toUpperCase()] = j;
      const n = normalizePn(pn);
      // only index normalized → row when it's unique; if two canonical
      // PNs collide after normalization we record `__AMBIGUOUS__`
      if (byNorm[n] === undefined) {
        byNorm[n] = j;
      } else if (byNorm[n] !== "__AMBIGUOUS__" && byNorm[n].id !== j.id) {
        byNorm[n] = "__AMBIGUOUS__";
      }
    }
    if (j.id) byId[j.id] = j;
  }
  return { byPn, byNorm, byId };
}

/**
 * Resolve a record's canonical project identity.
 *
 * @param {Object} record         — any document carrying project fields
 * @param {ResolverContext} ctx   — pre-built jobs_master maps
 * @returns {ProjectIdentity}
 */
export function resolveProjectIdentity(record, ctx) {
  const r = record || {};
  const byPn = (ctx && ctx.jobsMasterByPn) || {};
  const byId = (ctx && ctx.jobsMasterById) || {};

  const submittedPn = String(r.project_number || r.job_number || "").trim();
  const submittedName = String(r.project_name || r.job_name || "").trim();
  const candidateId = r.jobs_master_id || r.project_id || null;

  // 1 · exact jobs_master id
  if (candidateId && byId[candidateId]) {
    const j = byId[candidateId];
    return {
      jobs_master_id: j.id || candidateId,
      canonical_project_number: j.project_number || null,
      canonical_project_name: j.project_name || null,
      submitted_project_number: submittedPn,
      submitted_project_name: submittedName,
      resolution_status: "canonical",
      confidence: 100,
      source: "jobs_master_id",
    };
  }

  // 2 · exact project_number match (case-insensitive, trimmed)
  if (submittedPn) {
    const j = byPn[submittedPn.toUpperCase()];
    if (j) {
      return {
        jobs_master_id: j.id || null,
        canonical_project_number: j.project_number || submittedPn,
        canonical_project_name: j.project_name || null,
        submitted_project_number: submittedPn,
        submitted_project_name: submittedName,
        resolution_status: "project_number_match",
        confidence: 95,
        source: "project_number",
      };
    }
    // 2b · normalized PN match (whitespace/dash/case only — see normalizePn).
    //      Only succeeds when EXACTLY one canonical row matches the
    //      normalized form. Ambiguous normalizations fall through to
    //      submitted_only and surface in the Governance Center.
    const byNorm = (ctx && ctx.jobsMasterByNorm) || {};
    const norm = normalizePn(submittedPn);
    const jn = byNorm[norm];
    if (jn && jn !== "__AMBIGUOUS__") {
      return {
        jobs_master_id: jn.id || null,
        canonical_project_number: jn.project_number || null,
        canonical_project_name: jn.project_name || null,
        submitted_project_number: submittedPn,
        submitted_project_name: submittedName,
        resolution_status: "project_number_normalized",
        confidence: 85,
        source: "project_number",
      };
    }
    // 3 · submitted_only — PN is populated but unknown to jobs_master
    return {
      jobs_master_id: null,
      canonical_project_number: null,
      canonical_project_name: null,
      submitted_project_number: submittedPn,
      submitted_project_name: submittedName,
      resolution_status: "submitted_only",
      confidence: 30,
      source: "submitted",
    };
  }

  // 4 · orphan — no usable PN at all
  return {
    jobs_master_id: null,
    canonical_project_number: null,
    canonical_project_name: null,
    submitted_project_number: "",
    submitted_project_name: submittedName,
    resolution_status: "orphan",
    confidence: 0,
    source: "orphan",
  };
}

/**
 * Convenience picker — given a resolved identity, return what should
 * be shown in folder headers / list rows.
 *
 * Caller MUST handle every status. The exhaustive switch is enforced
 * by throwing on unknown statuses so future status additions are
 * impossible to silently ignore.
 *
 * @param {ProjectIdentity} id
 * @param {Object} [opts]
 * @param {string} [opts.orphanLabel="Unmatched / Needs Project Review"]
 * @param {string} [opts.submittedFallbackPrefix="Unmatched Project"]
 * @returns {{ number: string, name: string }}
 */
export function displayProjectIdentity(id, opts) {
  const orphanLabel =
    (opts && opts.orphanLabel) || "Unmatched / Needs Project Review";
  const submittedPrefix =
    (opts && opts.submittedFallbackPrefix) || "Unmatched Project";

  switch (id.resolution_status) {
    case "canonical":
    case "project_number_match":
    case "project_number_normalized":
      return {
        number: id.canonical_project_number || id.submitted_project_number || "—",
        name:
          id.canonical_project_name ||
          id.submitted_project_name ||
          `${submittedPrefix} · ${id.submitted_project_number || "—"}`,
      };
    case "submitted_only":
      return {
        number: id.submitted_project_number || "—",
        name:
          id.submitted_project_name ||
          `${submittedPrefix} · ${id.submitted_project_number}`,
      };
    case "orphan":
      return { number: "—", name: orphanLabel };
    default:
      // Forced exhaustive switch. If a new status is added to
      // ProjectIdentityStatus, every caller must update before the
      // app can render. This is the platform doctrine safeguard.
      throw new Error(
        `displayProjectIdentity: unhandled resolution_status "${
          id.resolution_status
        }". All callers must explicitly handle every status.`
      );
  }
}

export default resolveProjectIdentity;
