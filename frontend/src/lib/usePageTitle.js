// iter219 — usePageTitle hook.
//
// Sets document.title for the current view and restores the previous
// value on unmount. Used by portal hubs so each surface signals its
// persona (e.g. "Field Leadership · MASCI" instead of the generic
// "MASCI Operations Platform" on every page).
//
// Surfaced by the iter217 superintendent walkthrough — generic <title>
// tags hurt orientation for crews / supers landing on a portal from
// a deep link or browser-tab swap.

import { useEffect } from "react";

export function usePageTitle(title) {
  useEffect(() => {
    if (!title) return;
    const previous = document.title;
    document.title = title;
    return () => {
      document.title = previous;
    };
  }, [title]);
}

export default usePageTitle;
