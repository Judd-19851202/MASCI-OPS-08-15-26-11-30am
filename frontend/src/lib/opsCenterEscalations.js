// opsCenterEscalations.js — Iter162.
//
// Pure functions for the "newly escalated" pulse-dot on compact
// Operations Center cards. State lives in localStorage ONLY — no
// backend writes, no new endpoint, no new collection.
//
// Discipline:
//   * Pulse dot fires ONLY on severity ESCALATION:
//       Info → Warning   ✅
//       Info → Critical  ✅
//       Warning → Critical ✅
//   * NOT on:
//       Same severity      ❌
//       Warning → Info     ❌ (de-escalation is silent)
//       Critical → Info    ❌
//       Critical → Warning ❌
//   * TTL: pulse visible for 24h since first detection, then auto-clears.
//   * Click on card clears the escalation immediately.
//   * Scope: per (role, card_key). Per-device — no cross-device sync.
//   * Empty state ("No signal yet" = Info) is NEVER an escalation source.
//
// Storage shape:
//   localStorage["masci.ops_escalations.v1"] = {
//     "<role>": {
//       "<card_key>": { prev: "Info", curr: "Warning", at: 173... }
//     }
//   }
//   localStorage["masci.ops_severity.v1"] = {
//     "<role>": { "<card_key>": "Info" | "Warning" | "Critical" }
//   }

const SEV_RANK = { Info: 1, Warning: 2, Critical: 3 };
const TTL_MS = 24 * 60 * 60 * 1000;   // 24h

const ESCALATIONS_KEY = "masci.ops_escalations.v1";
const SEVERITY_KEY    = "masci.ops_severity.v1";

function _read(key) {
  try {
    const raw = localStorage.getItem(key);
    return raw ? JSON.parse(raw) : {};
  } catch {
    return {};
  }
}

function _write(key, data) {
  try {
    localStorage.setItem(key, JSON.stringify(data));
  } catch {
    // Quota or disabled — silent.
  }
}

/** Detect escalation between previous and current severity. */
export function isEscalation(prev, curr) {
  const a = SEV_RANK[prev] || 0;
  const b = SEV_RANK[curr] || 0;
  // a === 0 means prev was unknown (first visit) — NOT an escalation.
  // Empty-state Info → Info is not an escalation either.
  if (a === 0) return false;
  return b > a;
}

/**
 * Update tracker state based on a freshly-fetched ops-center payload.
 * Returns the set of card_keys that should show the pulse dot.
 *
 * Side effects: writes to localStorage.
 *
 *   - For each card in `cards`, compares its current severity to the
 *     last-known severity for (role, card_key).
 *   - If escalation, records {prev, curr, at} in escalations store.
 *   - Drops any escalation entry whose `at` is older than 24h.
 *   - Updates the last-known severity to the current one.
 *
 * @param {string} role — viewer role from payload.role
 * @param {Array<{key:string, severity:string}>} cards — payload.cards
 * @param {number} [nowMs=Date.now()]
 * @returns {Set<string>} Set of card_keys currently flagged as pulsing.
 */
export function reconcileEscalations(role, cards, nowMs = Date.now()) {
  if (!role || !Array.isArray(cards)) return new Set();
  const escalations = _read(ESCALATIONS_KEY);
  const lastSev = _read(SEVERITY_KEY);

  const roleEsc = escalations[role] || {};
  const roleSev = lastSev[role] || {};

  // Drop expired escalations (24h TTL) BEFORE evaluating new ones.
  for (const k of Object.keys(roleEsc)) {
    if (nowMs - (roleEsc[k]?.at || 0) >= TTL_MS) {
      delete roleEsc[k];
    }
  }

  const pulsing = new Set();
  for (const card of cards) {
    if (!card || !card.key) continue;
    const prev = roleSev[card.key];   // may be undefined on first visit
    const curr = card.severity || "Info";

    if (isEscalation(prev, curr)) {
      // New escalation. Capture timestamp.
      roleEsc[card.key] = { prev, curr, at: nowMs };
    }

    // Update last-known severity AFTER comparing.
    roleSev[card.key] = curr;

    // Surviving (non-expired) escalation? Mark pulsing.
    if (roleEsc[card.key]) {
      pulsing.add(card.key);
    }
  }

  escalations[role] = roleEsc;
  lastSev[role] = roleSev;
  _write(ESCALATIONS_KEY, escalations);
  _write(SEVERITY_KEY, lastSev);
  return pulsing;
}

/**
 * Mark a specific card as viewed — clears its escalation entry so the
 * pulse dot disappears immediately. Called on card click.
 */
export function clearEscalation(role, cardKey) {
  if (!role || !cardKey) return;
  const escalations = _read(ESCALATIONS_KEY);
  if (escalations[role] && escalations[role][cardKey]) {
    delete escalations[role][cardKey];
    _write(ESCALATIONS_KEY, escalations);
  }
}

// Internal getters exposed for unit testing only.
export const __internals = {
  ESCALATIONS_KEY, SEVERITY_KEY, TTL_MS,
  _read, _write,
};
