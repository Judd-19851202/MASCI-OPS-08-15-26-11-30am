// actorId.js — derive a stable per-device actor identifier from
// whichever portal token is live. Used to namespace IndexedDB drafts
// so two co-located users on the same device don't see each other's
// drafts. NOT a security boundary — just a UX hygiene helper.

import { getAdminToken } from "@/lib/adminAuth";
import { getPmToken } from "@/lib/pmAuth";
import { getShopToken } from "@/lib/shopAuth";
import { getHrToken } from "@/lib/hrAuth";
import { getSafetyToken } from "@/lib/safetyAuth";
import { getDispatchToken } from "@/lib/dispatchAuth";
import { getLeadershipToken } from "@/lib/leadershipAuth";

export function getActorId() {
  // First non-empty token wins. We only keep the first 16 chars to
  // avoid leaking the full HMAC into the IndexedDB key.
  const probes = [
    ["a", getAdminToken],
    ["s", getSafetyToken],
    ["h", getHrToken],
    ["p", getPmToken],
    ["sh", getShopToken],
    ["d", getDispatchToken],
    ["l", getLeadershipToken],
  ];
  for (const [prefix, fn] of probes) {
    try {
      const t = fn && fn();
      if (t && typeof t === "string") {
        return `${prefix}.${t.slice(0, 16)}`;
      }
    } catch { /* ignore */ }
  }
  return "anon";
}
