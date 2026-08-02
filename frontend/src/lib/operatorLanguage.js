const BANNED_OPERATOR_TERMS = [
  "WP-14F",
  "WP-17",
  "certification",
  "canonical",
  "backend",
  "frontend",
  "mutation",
  "governed",
  "runtime",
  "preview",
  "fixture",
  "audit",
  "developer",
  "engineering",
  "debug",
  "qa",
  "uat",
  "ticket",
  "defect",
  "internal",
  "code name",
];

const OPERATOR_TERM_REPLACEMENTS = [
  [/\bpreview-safe\b/gi, "live-safe"],
  [/\bpreview fixture\b/gi, "test account"],
  [/\bwp-?14f\b/gi, ""],
  [/\bwp-?17[a-z0-9-]*\b/gi, ""],
  [/\bcertification\b/gi, "readiness"],
  [/\bcanonical\b/gi, "platform"],
  [/\bbackend\b/gi, "platform"],
  [/\bfrontend\b/gi, "platform"],
  [/\bmutation\b/gi, "update"],
  [/\bgoverned\b/gi, "approved"],
  [/\bruntime\b/gi, "live"],
  [/\bpreview\b/gi, ""],
  [/\bfixture\b/gi, "record"],
  [/\bseeded\b/gi, "loaded"],
  [/\bimplementation\b/gi, "setup"],
  [/\baudit\b/gi, "history"],
  [/\bauditable\b/gi, "tracked"],
  [/\bdeveloper\b/gi, "platform"],
  [/\bengineering\b/gi, "platform"],
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
];

const INTERNAL_CODE_PATTERN = /\b(?:wp\d+[a-z0-9-]*|oppc|devhub|preview|fixture|qa|uat|r2|ocr)\b/i;

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

export function sanitizeOperatorProjectNumber(value, fallback = "Operations support") {
  const raw = String(value || "").trim();
  if (!raw || containsOperatorUnsafeLanguage(raw)) return fallback;
  return raw;
}

export function sanitizeOperatorProjectName(value, fallback = "Operations support work") {
  const raw = sanitizeOperatorCopy(value, "");
  if (!raw || containsOperatorUnsafeLanguage(value)) {
    const humanized = humanizeOperatorToken(value, fallback);
    return humanized || fallback;
  }
  return raw;
}

export function formatOperatorJobLabel(projectNumber, projectName) {
  const safeNumber = sanitizeOperatorProjectNumber(projectNumber, "Operations support");
  const safeName = sanitizeOperatorProjectName(projectName, "Operations support work");
  if (!safeNumber && !safeName) return "Operations support work";
  if (!safeNumber) return safeName;
  if (!safeName || safeNumber === safeName) return safeNumber;
  return `${safeNumber} · ${safeName}`;
}

export function sanitizeOperatorReference(value, fallback = "Linked record") {
  const safe = sanitizeOperatorCopy(value, "");
  if (!safe || containsOperatorUnsafeLanguage(value)) {
    return humanizeOperatorToken(value, fallback);
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

export { BANNED_OPERATOR_TERMS };