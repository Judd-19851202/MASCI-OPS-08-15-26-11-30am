// lib/identity.js — Track 14.0-HR-IDENTITY canonical display formatter.
//
// One helper to render an employee's display name across the entire
// platform. Backend persists 4 fields:
//   * legal_first_name
//   * legal_middle_name
//   * legal_last_name
//   * preferred_name
//
// Display rule:
//   * "<legal_first> <legal_last> (<preferred>)" when preferred_name exists.
//   * "<legal_first> <legal_last>" otherwise.
//   * Fall back to `name` / `display_name` / `employee_name` (legacy
//     denormalised label) when no legal-name parts are populated.
//
// Never replace the legal identity. Never hide it. Never show only
// the nickname.
//
// Usage:
//   import { formatEmployeeIdentity } from "@/lib/identity";
//   formatEmployeeIdentity(emp)
//   // "James Fisher (Jimmy)" when preferred is set, else "James Fisher".

function _str(v) {
  return (v == null ? "" : String(v)).trim();
}

/**
 * Build the display string for an employee-like record.
 * @param {object} obj Anything carrying any subset of:
 *   { legal_first_name, legal_last_name, preferred_name,
 *     name, display_name, employee_name, full_name }
 * @returns {string} formatted display name, or "" if nothing available.
 */
export function formatEmployeeIdentity(obj) {
  if (!obj || typeof obj !== "object") return "";
  const first = _str(obj.legal_first_name);
  const last = _str(obj.legal_last_name);
  const preferred = _str(obj.preferred_name);

  let legal = "";
  if (first || last) {
    legal = [first, last].filter(Boolean).join(" ");
  } else {
    // Fall back to denormalised legacy label so existing callers
    // that pass only `name` keep rendering. `display_identity` is
    // the backend-precomputed label and takes precedence over the
    // other denormalised aliases.
    legal = _str(obj.display_identity) || _str(obj.name) || _str(obj.full_name)
      || _str(obj.display_name) || _str(obj.employee_name);
  }

  if (!legal && !preferred) return "";
  if (preferred && legal && preferred.toLowerCase() !== legal.toLowerCase()) {
    return `${legal} (${preferred})`;
  }
  return legal || preferred;
}

/**
 * Lighter helper — returns just the legal name, no preferred suffix.
 * Use this where space is tight (e.g. compact roster rows).
 */
export function formatLegalName(obj) {
  if (!obj || typeof obj !== "object") return "";
  const first = _str(obj.legal_first_name);
  const last = _str(obj.legal_last_name);
  if (first || last) return [first, last].filter(Boolean).join(" ");
  return _str(obj.display_identity) || _str(obj.name) || _str(obj.full_name)
    || _str(obj.display_name) || _str(obj.employee_name) || "";
}

/**
 * Build a search blob for a record so a single substring match can
 * resolve "James" / "Jimmy" / "Fisher" / "James Fisher" / "Jimmy Fisher"
 * / "James Michael Fisher" all to the same employee.
 */
export function identitySearchBlob(obj) {
  if (!obj || typeof obj !== "object") return "";
  const first = _str(obj.legal_first_name);
  const middle = _str(obj.legal_middle_name);
  const last = _str(obj.legal_last_name);
  const preferred = _str(obj.preferred_name);
  const parts = [
    first, middle, last, preferred,
    [first, last].filter(Boolean).join(" "),
    [first, middle, last].filter(Boolean).join(" "),
    [preferred, last].filter(Boolean).join(" "),
    obj.name,
    obj.full_name,
    obj.display_name,
    obj.employee_name,
  ];
  return parts
    .map(_str)
    .filter(Boolean)
    .join(" ")
    .toLowerCase();
}
