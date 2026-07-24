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
import { getFlToken } from "@/lib/flAuth";
import { getDirectoryUser } from "@/lib/directoryAuth";
import { getFlUser } from "@/lib/flAuth";
import { getHrUser } from "@/lib/hrAuth";
import { getDispatchUser } from "@/lib/dispatchAuth";
import { getSafetyUser } from "@/lib/safetyAuth";
import { getDeviceId } from "./deviceId";

const _TOKEN_PROBES = [
  ["a", getAdminToken],
  ["s", getSafetyToken],
  ["h", getHrToken],
  ["p", getPmToken],
  ["sh", getShopToken],
  ["d", getDispatchToken],
  ["fl", getFlToken],
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

// TRACK 19.04 · Form Session Isolation.
// Fingerprint the currently signed-in portal actor so drafts saved
// by Actor A on a device are NOT offered to Actor B on the same
// device. Falls back to `"anon"` when no portal token is present
// (public form flow — kept unscoped by design so a foreman on a
// public submit page can still recover an in-progress draft).
//
// The fingerprint is portal-prefix + token slice — enough to
// discriminate distinct signed-in identities without leaking the
// full token into IDB. Two logins by the SAME user (same token)
// produce the same fingerprint, so a passkey re-auth that mints a
// new token WILL rotate the fingerprint. That is intentional: on
// re-auth we prompt "Draft from earlier this session — restore?"
// rather than silently applying the previous session's payload.
export function getAuthActorFingerprint() {
  const [prefix, tok] = _liveTokenPair();
  if (prefix && tok) return `${prefix}.${tok}`;
  return "anon";
}

function _stablePortalUser() {
  try {
    const dir = getDirectoryUser();
    if (dir?.id) return { portal: "directory", id: String(dir.id) };
  } catch { /* ignore */ }
  try {
    const fl = getFlUser();
    if (fl?.id) return { portal: "fl", id: String(fl.id) };
  } catch { /* ignore */ }
  try {
    const hr = getHrUser();
    if (hr?.id) return { portal: "hr", id: String(hr.id) };
  } catch { /* ignore */ }
  try {
    const disp = getDispatchUser();
    if (disp?.id) return { portal: "dispatch", id: String(disp.id) };
  } catch { /* ignore */ }
  try {
    const safety = getSafetyUser();
    if (safety?.id) return { portal: "safety", id: String(safety.id) };
  } catch { /* ignore */ }
  return null;
}

export function getStableActorIdentity() {
  const who = _stablePortalUser();
  if (who?.id) return `${who.portal}.${who.id}`;
  return "anon";
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
