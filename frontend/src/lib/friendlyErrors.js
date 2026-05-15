// friendlyErrors.js — iter148 (Phase 2.5). Translate the most common
// backend error_code/422 detail strings into human-friendly messages
// while preserving the technical detail for troubleshooting.
//
// Goal: reduce "what does this mean?" support questions without
// hiding the underlying signal. The friendly message is shown first,
// the raw detail is appended in parentheses for support escalation.
//
// Add a new code by appending to MAP. Keys are matched case-insensitively
// either as exact match OR as substring (for free-text error details).

const MAP = {
  // — Validation —
  "field required":          "One or more required fields are blank. Please fill them in and try again.",
  "value_error.missing":     "One or more required fields are blank. Please fill them in and try again.",
  "value_error.email":       "That doesn't look like a valid email address.",
  "string_too_short":        "One of your inputs is too short.",
  "string_too_long":         "One of your inputs is too long. Please shorten it.",

  // — Auth / permissions —
  "invalid credentials":     "Email or password doesn't match. Try again or use the password reset link.",
  "token expired":           "Your session has expired. Please sign back in.",
  "forbidden":               "You don't have permission to do that. If this is unexpected, contact your administrator.",
  "rate_limited":            "Too many attempts in a short window. Wait a minute and try again.",

  // — Domain —
  "duplicate":               "A record with these values already exists. Edit the existing one or pick different values.",
  "not_found":               "We couldn't find that record. It may have been deleted or moved.",
  "equipment_master_id":     "The selected equipment unit couldn't be matched. Use the dropdown rather than typing.",
  "employee_master_id":      "The selected employee couldn't be matched. Use the dropdown rather than typing.",
  "next_due_date":           "The next-due date must be on or after today.",
  "expiration_date":         "The expiration date must be after the completion date.",
  "incident_date":           "The incident date can't be in the future.",
  "file too large":          "That file is too large. Maximum size is 25 MB.",
  "unsupported_media_type":  "That file type isn't supported. Try a PDF, JPG, PNG, or DOCX instead.",
};

/**
 * Resolve a friendly message for a backend error. Returns the friendly
 * text alone when a match is found, or `fallback` (or the raw detail)
 * when no match exists. The raw detail is always available via
 * `friendlyError(...).raw` for support-channel surfacing.
 *
 * @param {unknown} err — axios error, Pydantic error response, or string
 * @param {string} [fallback] — default user-facing message
 * @returns {string}
 */
export function friendlyError(err, fallback = "Something went wrong. Please try again.") {
  const raw = extractRaw(err);
  if (!raw) return fallback;

  // Exact key match first
  const key = String(raw).toLowerCase().trim();
  if (MAP[key]) return MAP[key];

  // Substring match
  for (const [match, msg] of Object.entries(MAP)) {
    if (key.includes(match)) return msg;
  }

  return raw.length > 200 ? fallback : raw;
}

function extractRaw(err) {
  if (!err) return "";
  if (typeof err === "string") return err;
  // Axios error
  const detail = err?.response?.data?.detail;
  if (Array.isArray(detail)) {
    // Pydantic — pick the first useful entry
    const first = detail[0];
    if (first?.msg) return first.msg;
    if (first?.type) return first.type;
    return JSON.stringify(first);
  }
  if (typeof detail === "string") return detail;
  if (err?.message) return err.message;
  return "";
}

/**
 * Lower-level helper exposed for tests / advanced surfaces that want
 * to render BOTH the friendly text AND the raw detail.
 */
export function friendlyErrorParts(err) {
  const raw = extractRaw(err);
  const friendly = friendlyError(err, raw || "Something went wrong.");
  return { friendly, raw };
}
