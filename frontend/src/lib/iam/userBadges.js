/**
 * IAM Display Utilities — OMEGA Standardization Sprint
 *
 * PURE display reducers. No fetch, no I/O, no JSX, no React.
 *
 * Every portal-user panel imports these to render a single canonical
 * badge vocabulary across HR / Safety / Dispatch / Shop / Field
 * Leadership / Admin / Access Control / Unified Directory surfaces.
 *
 * Data preservation contract:
 *  - These functions ONLY read user fields.
 *  - The `disabled` (HR/Safety/Dispatch/FL) and `is_active` (Shop/Admin)
 *    flags are honored as-is — no rewrites, no migrations.
 *  - Fields that don't exist on a portal render as "—" via formatActivity.
 */

/** Canonical access-status state machine. */
export const ACCESS = Object.freeze({
  ACTIVE: "ACTIVE",
  PENDING_ACTIVATION: "PENDING_ACTIVATION",
  DISABLED: "DISABLED",
});

/** Canonical password-status state machine. */
export const PASSWORD = Object.freeze({
  NEVER_ISSUED: "NEVER_ISSUED",
  TEMP_PASSWORD_ACTIVE: "TEMP_PASSWORD_ACTIVE",
  PASSWORD_SET: "PASSWORD_SET",
  EXPIRED: "EXPIRED",
});

/** Both `disabled` (most portals) and `is_active` (Shop/Admin) collapse here. */
export function isUserDisabled(u) {
  if (!u) return false;
  if (u.disabled === true) return true;
  if (u.is_active === false) return true;
  return false;
}

/** Derive access status from existing fields. No writes. */
export function normalizeAccessStatus(u) {
  if (!u) return ACCESS.PENDING_ACTIVATION;
  if (isUserDisabled(u)) return ACCESS.DISABLED;
  const everLoggedIn = !!u.last_login_at;
  const tempActive = u.must_change_password === true;
  if (tempActive && !everLoggedIn) return ACCESS.PENDING_ACTIVATION;
  return ACCESS.ACTIVE;
}

/** Derive password status from existing fields. No writes. */
export function normalizePasswordStatus(u) {
  if (!u) return PASSWORD.NEVER_ISSUED;
  const hasLogged = !!u.last_login_at;
  const tempActive = u.must_change_password === true;
  const hasSetAt = !!u.password_set_at;
  // Expiration policy not currently implemented; never returns EXPIRED.
  if (tempActive) return PASSWORD.TEMP_PASSWORD_ACTIVE;
  if (hasSetAt || hasLogged) return PASSWORD.PASSWORD_SET;
  return PASSWORD.NEVER_ISSUED;
}

/**
 * Activity snapshot. Renders "—" for unavailable fields rather than
 * hiding them, so every panel has the same row geometry.
 */
export function normalizeActivity(u) {
  return {
    last_login: u?.last_login_at || null,
    last_activity: u?.last_activity_at || null,
    last_password_issued: u?.temp_password_issued_at || u?.last_password_issued_at || null,
    issued_by: u?.temp_password_issued_by || u?.last_password_issued_by || null,
  };
}

/**
 * Portal-badge list. Returns an array with at least one badge.
 * For mirrored / multi-portal identities, additional badges can be added by
 * the unified directory caller passing `extraPortals=[...]`.
 */
export function normalizePortalBadges(u, primaryPortal, extraPortals = []) {
  const portals = new Set([primaryPortal, ...(extraPortals || [])].filter(Boolean));
  if (u?.role) {
    return { portals: Array.from(portals), role: u.role };
  }
  return { portals: Array.from(portals), role: "—" };
}

/**
 * Returns which row-level actions should be available, given the user
 * and the per-portal capability set.
 *
 * portalCaps must be passed by the caller because Shop/FL support
 * `resend_welcome` natively but HR/Safety/Dispatch/Admin do not. We
 * never fake an action that doesn't have a backend endpoint.
 */
export function normalizeIamActions(u, portalCaps = {}) {
  if (!u) return { canEdit: false, canIssuePw: false, canResendWelcome: false, canToggleDisable: false, canViewAudit: true };
  return {
    canEdit: !!portalCaps.edit,
    canIssuePw: !!portalCaps.issue_temp_password,
    canResendWelcome: !!portalCaps.resend_welcome,
    canToggleDisable: !!portalCaps.toggle_disable,
    canViewAudit: true, // every portal links to the same /admin/audit page
  };
}

/* ────────────────────────────────────────────────────────────────────
 * Formatting helpers (UI string formatters · pure, no JSX)
 * ────────────────────────────────────────────────────────────────── */

/** Returns a human-relative ago string ("2h ago"), or "—" if not set. */
export function formatRelative(iso) {
  if (!iso) return "—";
  try {
    const t = new Date(iso).getTime();
    if (!Number.isFinite(t)) return "—";
    const delta = Math.max(0, Date.now() - t);
    const sec = Math.floor(delta / 1000);
    if (sec < 60) return "just now";
    const min = Math.floor(sec / 60);
    if (min < 60) return `${min}m ago`;
    const hr = Math.floor(min / 60);
    if (hr < 24) return `${hr}h ago`;
    const d = Math.floor(hr / 24);
    if (d < 30) return `${d}d ago`;
    const mo = Math.floor(d / 30);
    if (mo < 12) return `${mo}mo ago`;
    return `${Math.floor(mo / 12)}y ago`;
  } catch {
    return "—";
  }
}

/** Canonical class names for each badge state. */
export const ACCESS_BADGE_CLASS = Object.freeze({
  [ACCESS.ACTIVE]: "bg-emerald-100 text-emerald-800 border-emerald-300",
  [ACCESS.PENDING_ACTIVATION]: "bg-amber-100 text-amber-800 border-amber-300",
  [ACCESS.DISABLED]: "bg-rose-100 text-rose-700 border-rose-300",
});

export const ACCESS_BADGE_LABEL = Object.freeze({
  [ACCESS.ACTIVE]: "Active",
  [ACCESS.PENDING_ACTIVATION]: "Pending activation",
  [ACCESS.DISABLED]: "Disabled",
});

export const PASSWORD_BADGE_CLASS = Object.freeze({
  [PASSWORD.NEVER_ISSUED]: "bg-slate-100 text-slate-700 border-slate-300",
  [PASSWORD.TEMP_PASSWORD_ACTIVE]: "bg-amber-50 text-amber-800 border-amber-300",
  [PASSWORD.PASSWORD_SET]: "bg-slate-50 text-slate-600 border-slate-300",
  [PASSWORD.EXPIRED]: "bg-rose-100 text-rose-700 border-rose-300",
});

export const PASSWORD_BADGE_LABEL = Object.freeze({
  [PASSWORD.NEVER_ISSUED]: "Never issued",
  [PASSWORD.TEMP_PASSWORD_ACTIVE]: "Temp password active",
  [PASSWORD.PASSWORD_SET]: "Password set",
  [PASSWORD.EXPIRED]: "Expired",
});
