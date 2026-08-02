// Portal Continuity Helper · iter322-B
//
// Maps a protected path (the place a user tried to reach) to a rich
// continuity descriptor that protected-route guards can attach to
// `state.continuity` when redirecting to a login page.
//
//   { workflow: "Incident Reports",
//     role:     "Safety Portal",
//     from:     "safety",
//     returnTo: "/safety-portal",
//     continueTo: "/safety-portal/incidents" }
//
// Pure data — no rendering, no auth changes, no route changes. Adds
// nothing to bundle weight that isn't already shipped by the i18n keys.

// Portal → display label / hub path / return identity. The keys here
// match the values that `PortalContextBanner.PORTAL_REGISTRY` uses
// and the `?from=<key>` query parameter the hub Guides links emit.
//
// TRACK 18.01/18.07 canonical naming: the human-facing portal labels
// must use the operations names ("Human Resources" / "Project Management"
// / "Safety Operations" / "Shop Operations" / "Field Leadership"),
// NOT the legacy "* Portal" labels.
const PORTAL = {
  safety:     { roleLabel: "Safety Operations",   hub: "/safety-portal" },
  hr:         { roleLabel: "Human Resources",     hub: "/hr" },
  shop:       { roleLabel: "Shop Operations",     hub: "/shop" },
  admin:      { roleLabel: "Administration",      hub: "/admin" },
  pm:         { roleLabel: "Project Management",  hub: "/pm" },
  dispatch:   { roleLabel: "Transportation Operations", hub: "/dispatch-portal" },
  leadership: { roleLabel: "Field Leadership",    hub: "/leadership" },
};

// Path-segment → workflow label registry. Order matters — first match
// wins. Each entry is `[regex, workflowLabel, portalKey]`. Add new
// protected workflows here as they emerge; the regex matches the path
// section directly after the portal root.
//
// Operational tone preserved (Rule 8): direct, field-usable language —
// "Incident Reports", NOT "Incident Records Module".
const WORKFLOWS = [
  // ─── Safety Portal ──────────────────────────────────────────────
  [/^\/safety-portal\/incidents/,            "Incident Reports",          "safety"],
  [/^\/safety-portal\/audits/,               "Inspections & Reviews",     "safety"],
  [/^\/safety-portal\/corrective-actions/,   "Corrective Actions",        "safety"],
  [/^\/safety-portal\/training/,             "Training Records",          "safety"],
  [/^\/safety-portal\/employees/,            "Employee Safety Profiles",  "safety"],
  [/^\/safety-portal\/fire-extinguishers/,   "Fire Extinguishers",        "safety"],
  [/^\/safety-portal\/documents/,            "Safety Document Library",   "safety"],
  [/^\/safety-portal\/digest/,               "Weekly Digest",             "safety"],
  [/^\/safety-portal\/reports/,              "Reports & Exports",         "safety"],
  [/^\/safety-portal\/fleet/,                "Trucking · Fleet",          "safety"],
  [/^\/safety-portal\/library/,              "Topic Library",             "safety"],
  [/^\/safety-portal\/change-password/,      "Change Password",           "safety"],
  [/^\/safety-portal/,                       "Safety Portal",             "safety"],
  // ─── HR Portal ─────────────────────────────────────────────────
  [/^\/hr\/employees/,                       "Employee Lifecycle",        "hr"],
  [/^\/hr\/field-leadership-users/,          "Field Leadership Accounts", "hr"],
  [/^\/hr\/field-leadership/,                "Field Leadership Records",  "hr"],
  [/^\/hr\/time-off/,                        "Time Off Requests",         "hr"],
  [/^\/hr\/employee-accountability/,         "Employee Accountability",   "hr"],
  [/^\/hr\/time-verification/,               "Time Verification",         "hr"],
  [/^\/hr\/payroll-variance/,                "Payroll Variance",          "hr"],
  [/^\/hr\/training-records/,                "Training Records",          "hr"],
  [/^\/hr\/driver-qualification/,            "Driver Qualification",      "hr"],
  [/^\/hr\/safety-records/,                  "Safety Records",            "hr"],
  [/^\/hr/,                                  "HR Portal",                 "hr"],
  // ─── Shop Portal ───────────────────────────────────────────────
  [/^\/shop\/fleet/,                         "Fleet Repair Queue",        "shop"],
  [/^\/shop/,                                "Shop Portal",               "shop"],
  // ─── Dispatch Portal ───────────────────────────────────────────
  [/^\/dispatch-portal/,                     "Dispatch Portal",           "dispatch"],
  // ─── PM Portal ─────────────────────────────────────────────────
  [/^\/pm/,                                  "PM Portal",                 "pm"],
  // ─── Admin ─────────────────────────────────────────────────────
  [/^\/admin/,                               "Administration",            "admin"],
];

/**
 * Build a portal continuity descriptor for a given (intended) path.
 * Used by `<Require*>` guards when redirecting to the corresponding
 * login page. Always returns a populated object — never null — so
 * AuthRequiredBanner can render meaningful copy in every case.
 *
 * @param {string} pathWithSearch — full intended URL (path + search).
 * @returns {{
 *   workflow: string,
 *   role: string,
 *   from: string,
 *   returnTo: string,
 *   continueTo: string,
 * }}
 */
export function buildContinuity(pathWithSearch) {
  const pathname = (pathWithSearch || "").split("?")[0];
  for (const [re, label, key] of WORKFLOWS) {
    if (re.test(pathname)) {
      const portal = PORTAL[key] || PORTAL.safety;
      return {
        workflow: label,
        role: portal.roleLabel,
        from: key,
        returnTo: portal.hub,
        continueTo: pathWithSearch,
      };
    }
  }
  // No match → still return a non-null descriptor so the banner has
  // something useful to say.
  return {
    workflow: "This workflow",
    role: "elevated access",
    from: "",
    returnTo: "/",
    continueTo: pathWithSearch || "/",
  };
}

export const PORTAL_REGISTRY = PORTAL;
