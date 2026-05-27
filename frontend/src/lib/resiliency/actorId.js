// actorId.js — iter440 · P0 field-incident remediation · 2026-05-27.
//
// What changed at iter440
// -----------------------
// The actor id used to be derived ONLY from the live portal token
// (first 16 chars). That was the single largest cause of the field-
// reported "my work disappeared" symptom: when the token rotated
// (multi-login refresh, passkey re-auth, cross-portal navigation),
// the actor id changed, the autosave wrote to a new IDB key, and
// the morning's draft was orphaned under the old key — still on
// disk, unreachable by the UI.
//
// iter440 makes the actor id DEVICE-SCOPED. The IDB draft key uses
// a persisted `deviceId` (see `deviceId.js`) that survives every
// login/logout/passkey rotation. The full actor id still appends a
// token prefix for telemetry segmentation, but the IDB key surface
// (`getDeviceScopedActorId`) is the device id ALONE.
//
// Backward compat: `getLegacyActorIds()` returns the historical
// token-derived ids that may already be sitting in IDB under old
// `masci.draft.<prefix>.<token>.<formKey>` keys. The draft-store
// migration helper consumes this list once on first mount of the
// new code to re-key any orphaned drafts under the device id, then
// deletes the legacy keys.

import { getAdminToken } from "@/lib/adminAuth";
import { getPmToken } from "@/lib/pmAuth";
import { getShopToken } from "@/lib/shopAuth";
import { getHrToken } from "@/lib/hrAuth";
import { getSafetyToken } from "@/lib/safetyAuth";
import { getDispatchToken } from "@/lib/dispatchAuth";
import { getLeadershipToken } from "@/lib/leadershipAuth";
import { getDeviceId } from "./deviceId";

const _TOKEN_PROBES = [
  ["a", getAdminToken],
  ["s", getSafetyToken],
  ["h", getHrToken],
  ["p", getPmToken],
  ["sh", getShopToken],
  ["d", getDispatchToken],
  ["l", getLeadershipToken],
];

function _liveTokenPair() {
  for (const [prefix, fn] of _TOKEN_PROBES) {
    try {
      const t = fn && fn();
      if (t && typeof t === "string") {
        return [prefix, t.slice(0, 16)];
      }
    } catch { /* ignore */ }
  }
  return [null, null];
}

// The IDB key uses ONLY this — device-scoped, token-independent.
export function getDeviceScopedActorId() {
  return getDeviceId();
}

// Full actor id — device + token prefix. Used for telemetry
// segmentation only (lets us tell which portal a write came from
// without breaking the IDB key on token rotation).
export function getActorId() {
  const device = getDeviceId();
  const [prefix, tok] = _liveTokenPair();
  if (prefix && tok) return `${device}.${prefix}.${tok}`;
  return device;
}

// Returns the historical token-only actor ids that may exist as
// legacy IDB keys. The draft-store migration helper uses this on
// first mount to re-key any orphaned drafts under the new device-
// scoped key. Cap at 8 candidates (admin + 6 portal types + anon).
export function getLegacyActorIds() {
  const out = [];
  for (const [prefix, fn] of _TOKEN_PROBES) {
    try {
      const t = fn && fn();
      if (t && typeof t === "string") {
        out.push(`${prefix}.${t.slice(0, 16)}`);
      }
    } catch { /* ignore */ }
  }
  out.push("anon");
  return out;
}
