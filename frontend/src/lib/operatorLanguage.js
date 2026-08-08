const BANNED_OPERATOR_TERMS = [
  "C1",
  "C2",
  "C3",
  "C4",
  "C5",
  "C6",
  "C7",
  "C8",
  "C9",
  "C10",
  "WP-14F",
  "WP-17",
  "WP-18",
  "ECAP",
  "certification",
  "canonical",
  "backend",
  "frontend",
  "api",
  "authority contract",
  "read model",
  "source lineage",
  "schema",
  "payload",
  "route",
  "collection",
  "mutation",
  "governed",
  "runtime",
  "preview",
  "fixture",
  "audit",
  "developer",
  "engineering",
  "same shell",
  "shared workspace",
  "navigation system",
  "responsive behavior",
  "information hierarchy",
  "debug",
  "qa",
  "uat",
  "ticket",
  "defect",
  "internal",
  "code name",
  "cert",
  "telemetry",
  "snapshot",
  "kpi",
  "rollup",
  "spine",
  "deterministic",
  "read-only",
  "gateway",
  "provider",
  "configuration",
  "forensic",
  "cockpit",
  "audit",
  "audits",
  "defect",
  "defects",
  "qaqc",
  "qa/qc",
];

const OPERATOR_TERM_REPLACEMENTS = [
  [/\bdeterministic\s*[·-]\s*canonical\b/gi, "Based on current records"],
  [/\bdeferred in this release\b/gi, "not available on this page yet"],
  [/\bread-?only\b/gi, "view only"],
  [/\bqa\/qc\b/gi, "quality checks"],
  [/\bqaqc\b/gi, "quality checks"],
  [/\baudits\b/gi, "reviews"],
  [/\baudit\b/gi, "review"],
  [/\bdefects\b/gi, "issues"],
  [/\bdefect\b/gi, "issue"],
  [/\bcanonicalize\b/gi, "standardize"],
  [/\bcanonical_owner\b/gi, "primary owner"],
  [/\bcanonical_archive_lineage\b/gi, "primary archive lineage"],
  [/\bruntime_state_authority\b/gi, "current state authority"],
  [/\baudit_written\b/gi, "activity logged"],
  [/\bpreview-safe\b/gi, "live-safe"],
  [/\bpreview fixture\b/gi, "test account"],
  [/\bC1\b/gi, "customer and project"],
  [/\bC2\b/gi, "work planning"],
  [/\bC3\b/gi, "budget"],
  [/\bC4\b/gi, "schedule"],
  [/\bC5\b/gi, "planned vs actual"],
  [/\bC6\b/gi, "project performance"],
  [/\bC7\b/gi, "forecast"],
  [/\bC8\b/gi, "Earned Value"],
  [/\bC9\b/gi, "portfolio"],
  [/\bC10\b/gi, "next approved package"],
  [/\bwp-?14f\b/gi, ""],
  [/\bwp-?17[a-z0-9-]*\b/gi, ""],
  [/\bwp-?18[a-z0-9-]*\b/gi, ""],
  [/\becap\b/gi, "executive reporting"],
  [/\bcert\b/gi, ""],
  [/\bcertification\b/gi, "readiness"],
  [/\bcanonical\b/gi, "platform"],
  [/\bauthority contract\b/gi, "how this result is calculated"],
  [/\bread model\b/gi, "portfolio view"],
  [/\bsource lineage\b/gi, "supporting records"],
  [/\btelemetry\b/gi, "live updates"],
  [/\bsnapshot\b/gi, "update"],
  [/\bkpis\b/gi, "key job measures"],
  [/\bkpi\b/gi, "key job measure"],
  [/\brollups\b/gi, "totals"],
  [/\brollup\b/gi, "total"],
  [/\bspine\b/gi, "shared record"],
  [/\bdeterministic\b/gi, "rules-based"],
  [/\bgovernance\b/gi, "standards"],
  [/\bbackend\b/gi, "platform"],
  [/\bfrontend\b/gi, "platform"],
  [/\bapi\b/gi, "settings"],
  [/\bschema\b/gi, "form layout"],
  [/\bpayload\b/gi, "details"],
  [/\broute\b/gi, "page"],
  [/\bcollection\b/gi, "record list"],
  [/\bmutation\b/gi, "update"],
  [/\bgoverned\b/gi, "approved"],
  [/\bruntime\b/gi, "live"],
  [/\bpreview\b/gi, ""],
  [/\bfixture\b/gi, "record"],
  [/\bseeded\b/gi, "loaded"],
  [/\bimplementation\b/gi, "setup"],
  [/\bauditable\b/gi, "tracked"],
  [/\bdeveloper\b/gi, "platform"],
  [/\bengineering\b/gi, "platform"],
  [/\bsame shell\b/gi, "same work area"],
  [/\bshared workspace\b/gi, "one place"],
  [/\bnavigation system\b/gi, "navigation"],
  [/\bresponsive behavior\b/gi, "mobile and desktop support"],
  [/\binformation hierarchy\b/gi, "clear priorities"],
  [/\bdebug\b/gi, ""],
  [/\bqa\b/gi, "review"],
  [/\buat\b/gi, "review"],
  [/\bdefect\b/gi, "issue"],
  [/\bticket\b/gi, "item"],
  [/\boppc\b/gi, "operations"],
  [/\bdevhub\b/gi, "secure workspace"],
  [/\bdev\b/gi, "platform"],
  [/\bocr\b/gi, "document scan"],
  [/\br2\b/gi, "archive"],
  [/\buser_directory\b/gi, "account directory"],
  [/\brole_template\b/gi, "access template"],
  [/\bmongo\b/gi, "data service"],
  [/\bdb\b/gi, "data"],
  [/\bgateway\b/gi, "service"],
  [/\bprovider\b/gi, "service"],
  [/\bengine\b/gi, "calculation"],
  [/\bconfiguration\b/gi, "settings"],
  [/\bforensic\b/gi, "detailed"],
  [/\bcockpit\b/gi, "work area"],
  [/\bsingle-glass\b/gi, "shared"],
];

const INTERNAL_CODE_PATTERN = /\b(?:c1|c2|c3|c4|c5|c6|c7|c8|c9|c10|wp\d+[a-z0-9-]*|ecap|oppc|devhub|preview|fixture|qa|uat|r2|ocr|telemetry|snapshot|kpi|rollup|spine|forensic|cockpit|authority contract|read model|source lineage|schema|payload|backend|frontend|api|route|collection)\b/i;

function collapseWhitespace(value) {
  return String(value || "")
    .replace(/[._/]+/g, " ")
    .replace(/\s{2,}/g, " ")
    .replace(/\s+([·,.;:!?])/g, "$1")
    .trim();
}

function titleCase(value) {
  return value.replace(/\b([a-z])/g, (match) => match.toUpperCase());
}

export function containsOperatorUnsafeLanguage(value) {
  const source = String(value || "");
  return BANNED_OPERATOR_TERMS.some((term) => {
    const escaped = term.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
    return new RegExp(`\\b${escaped}\\b`, "i").test(source);
  }) || INTERNAL_CODE_PATTERN.test(source);
}

export function sanitizeOperatorCopy(value, fallback = "") {
  if (value == null) return fallback;
  let next = String(value);
  for (const [pattern, replacement] of OPERATOR_TERM_REPLACEMENTS) {
    next = next.replace(pattern, replacement);
  }
  next = collapseWhitespace(next)
    .replace(/\bto\s*$/i, "")
    .replace(/^[-·,:;\s]+|[-·,:;\s]+$/g, "")
    .trim();
  return next || fallback;
}

export function humanizeOperatorToken(value, fallback = "Operations record") {
  const raw = sanitizeOperatorCopy(value, "");
  if (!raw) return fallback;
  const tokens = raw
    .replace(/[-_./]+/g, " ")
    .split(/\s+/)
    .filter(Boolean)
    .filter((token) => !/^\d+$/.test(token))
    .filter((token) => !INTERNAL_CODE_PATTERN.test(token));
  if (!tokens.length) return fallback;
  return titleCase(tokens.join(" "));
}

export function sanitizeOperatorProjectNumber(value, fallback = "Project number not available") {
  const raw = String(value || "").trim();
  if (!raw || containsOperatorUnsafeLanguage(raw)) return fallback;
  return raw;
}

export function sanitizeOperatorProjectName(value, fallback = "Project name not available") {
  const raw = String(value || "").trim();
  const normalized = raw
    .replace(/\bforensic\b/gi, "")
    .replace(/\bfixture\b/gi, "")
    .replace(/\bpreview\b/gi, "")
    .replace(/\s{2,}/g, " ")
    .trim();
  const safe = sanitizeOperatorCopy(normalized, "");
  if (!safe) return fallback;
  if (containsOperatorUnsafeLanguage(safe)) return fallback;
  return safe;
}

export function formatOperatorJobLabel(projectNumber, projectName) {
  const safeNumber = sanitizeOperatorProjectNumber(projectNumber, "Project number not available");
  const safeName = sanitizeOperatorProjectName(projectName, "Project name not available");
  if (!safeNumber && !safeName) return "Project details not available";
  if (safeNumber === "Project number not available" && safeName === "Project name not available") return "Project details not available";
  if (!safeNumber) return safeName;
  if (!safeName || safeNumber === safeName) return safeNumber;
  if (safeName.startsWith(safeNumber)) return safeName;
  return `${safeNumber} · ${safeName}`;
}

export function sanitizeOperatorReference(value, fallback = "Linked record") {
  const safe = sanitizeOperatorCopy(value, "");
  if (!safe || containsOperatorUnsafeLanguage(value)) {
    return humanizeOperatorToken(safe || value, fallback);
  }
  return safe;
}

export function sanitizeOperatorError(value, fallback = "This information is unavailable right now.") {
  const raw = String(value || "").trim();
  if (!raw) return fallback;
  const safe = sanitizeOperatorCopy(raw, fallback);
  if (!safe || containsOperatorUnsafeLanguage(raw)) return fallback;
  return safe;
}

const OPERATOR_STATUS_OVERRIDES = {
  review_required: "Needs review",
  needs_review: "Needs review",
  approved_ready: "Ready to activate",
  partially_reviewed: "Partially reviewed",
  pending_review: "Pending PM review",
  proposed_only: "Proposed only",
  high: "High confidence",
  medium: "Medium confidence",
  low: "Low confidence",
  high_confidence: "High confidence",
  medium_confidence: "Medium confidence",
  low_confidence: "Low confidence",
  pending_manual_run: "Not started",
  in_progress: "In progress",
  not_started: "Not started",
  completed: "Completed",
  resolved: "Resolved",
  approved: "Approved",
  rejected: "Rejected",
  deferred: "Deferred",
  active: "Active",
  archived: "Archived",
  draft: "Draft",
  published: "Published",
  running: "Running",
  failed: "Needs attention",
  master_schedule: "Master schedule",
  baseline_refresh: "Baseline refresh",
  pending_revision: "Pending revision",
  original_approved_budget: "Original approved budget",
  current_approved_budget: "Current approved budget",
  awarded_contract: "Awarded contract",
  schedule_actuals_csv: "Schedule progress CSV",
};

function resolveOperatorLabel(value) {
  const key = String(value || "").trim().toLowerCase();
  if (!key) return "";
  return OPERATOR_STATUS_OVERRIDES[key] || humanizeOperatorToken(key, "");
}

export function operatorLabel(value, t, fallback = "—") {
  const resolved = resolveOperatorLabel(value);
  if (!resolved) return fallback;
  return typeof t === "function" ? t(resolved) : resolved;
}

export function operatorStatusLabel(value, t, fallback = "—") {
  return operatorLabel(value, t, fallback);
}

export function operatorConfidenceLabel(value, t, fallback = "—") {
  return operatorLabel(value, t, fallback);
}

export { BANNED_OPERATOR_TERMS };