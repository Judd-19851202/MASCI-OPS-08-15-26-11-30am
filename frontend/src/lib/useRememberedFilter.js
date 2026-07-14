// useRememberedFilter — iter148 (Phase 2.5). Per-user, per-page filter
// persistence using localStorage.
//
// Design constraints (per user mandate):
//   * Per-user only — namespaced with the active session's actor hash
//     so two users on the same shared device don't bleed.
//   * Lightweight — single read on mount, single write on change.
//   * Easy to reset — `clearAllRememberedFilters()` wipes the namespace.
//   * Smart defaults NEVER overwrite intentional user input — initial
//     value is consumed exactly once; subsequent sets are user-driven.
//   * Versioned key so schema changes don't poison old values.
//
// Public API:
//   useRememberedFilter("safety-ca-status-filter", "Open")
//     → [value, setValue, reset]
//
//   useRememberedFormValue("NewDailyReport.last_project_number", "")
//     → [value, setValue]   // setValue ALSO persists, so the next
//                              form-open auto-fills with the last
//                              submitted value.
//
//   clearAllRememberedFilters()
//     → wipe all keys prefixed with NAMESPACE (admin-only escape hatch)

import { useCallback, useEffect, useState } from "react";
import { getStableActorIdentity } from "@/lib/resiliency/actorId";

// Bump if the storage shape needs to change in the future. Old keys
// silently drop (we read with try/catch and JSON.parse).
const SCHEMA = "v1";
const NAMESPACE = "masci.ux.remembered";

function resolveActorKey() {
  try {
    const actor = getStableActorIdentity();
    if (actor && actor !== "anon") return actor;
  } catch {
    /* silent */
  }
  return "anon";
}

function buildKey(slot) {
  return `${NAMESPACE}.${SCHEMA}.${resolveActorKey()}.${slot}`;
}

function readSlot(slot, fallback) {
  if (typeof window === "undefined") return fallback;
  try {
    const raw = localStorage.getItem(buildKey(slot));
    if (raw == null) return fallback;
    const parsed = JSON.parse(raw);
    return parsed?.v !== undefined ? parsed.v : fallback;
  } catch {
    return fallback;
  }
}

function writeSlot(slot, value) {
  if (typeof window === "undefined") return;
  try {
    localStorage.setItem(buildKey(slot), JSON.stringify({ v: value }));
  } catch {
    // localStorage can fail in private-browsing mode — silent.
  }
}

/**
 * Hook for a filter that should persist between visits. Returns
 * [value, setValue, reset]. The initial value is taken from
 * localStorage if a prior value exists, otherwise `fallback`.
 */
export function useRememberedFilter(slot, fallback) {
  const [value, setValueState] = useState(() => readSlot(slot, fallback));
  const setValue = useCallback((next) => {
    // Support functional setter pattern.
    setValueState((curr) => {
      const resolved = typeof next === "function" ? next(curr) : next;
      writeSlot(slot, resolved);
      return resolved;
    });
  }, [slot]);
  const reset = useCallback(() => {
    setValueState(fallback);
    try { localStorage.removeItem(buildKey(slot)); } catch { /* silent */ }
  }, [slot, fallback]);
  return [value, setValue, reset];
}

/**
 * Hook for a "last submitted value" that should pre-fill the next
 * form open. Identical contract to useRememberedFilter — distinct
 * name so call sites are self-documenting.
 */
export const useRememberedFormValue = useRememberedFilter;

/**
 * Escape hatch — admin tools / sign-out flow can call this to wipe
 * the entire namespace. Returns the number of keys cleared.
 */
export function clearAllRememberedFilters() {
  if (typeof window === "undefined") return 0;
  const prefix = `${NAMESPACE}.${SCHEMA}.`;
  let n = 0;
  try {
    const toDelete = [];
    for (let i = 0; i < localStorage.length; i++) {
      const k = localStorage.key(i);
      if (k && k.startsWith(prefix)) toDelete.push(k);
    }
    for (const k of toDelete) {
      localStorage.removeItem(k);
      n++;
    }
  } catch {
    /* silent */
  }
  return n;
}

export default useRememberedFilter;
