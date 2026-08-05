/**
 * TRACK 24.9 · Phase B · Shared cmdk touch-vs-scroll guard.
 *
 * Extracted from `JobPicker.jsx` (Track 24.8 fix) so every cmdk /
 * `<CommandItem>` picker on the platform shares one hardened
 * implementation. Problem class:
 *
 *   cmdk's <CommandItem> fires `onSelect` on pointerup regardless
 *   of whether the parent list scrolled during the gesture. On
 *   iOS Safari, a natural scroll from row A to row B ends with
 *   the finger over row B and commits row B — wrong-row selection.
 *
 * Fix: attach a native scroll listener to the CommandList
 * container, record pointerdown position + target testid, and
 * commit only when:
 *   * list did NOT scroll between down and up
 *   * pointerup happens on the SAME row that received pointerdown
 *   * positional delta is below the movement threshold
 *   * pointerType is "touch" or "pen" (mouse is untouched — click
 *     semantics handle it fine)
 *
 * Usage:
 *   const { commitHandlersFor } = useCmdkTouchGuard(open);
 *   ...
 *   <CommandItem
 *     onSelect={commit}
 *     {...commitHandlersFor(commit, "picker-item-3")}
 *   />
 *
 * The guard is a no-op for mouse events, so desktop click flows
 * remain unchanged.
 */
import { useEffect, useRef } from "react";

const TOUCH_MOVE_CANCEL_PX = 12;

export function useCmdkTouchGuard(open) {
  const touchRef = useRef({ x: 0, y: 0, active: false, targetId: null });
  const scrolledRef = useRef(false);
  const listRef = useRef(null);
  const suppressSelectRef = useRef(false);

  useEffect(() => {
    if (!open) return undefined;
    // cmdk portals its List into the body; query by the attribute
    // it stamps on the DOM node.
    const list = document.querySelector('[cmdk-list=""]');
    if (!list) return undefined;
    listRef.current = list;
    const onScroll = () => {
      scrolledRef.current = true;
    };
    list.addEventListener("scroll", onScroll, { passive: true });
    return () => list.removeEventListener("scroll", onScroll);
  }, [open]);

  const commitHandlersFor = (commit, testid) => ({
    onPointerDown(e) {
      if (!e.pointerType || e.pointerType === "mouse") return;
      suppressSelectRef.current = true;
      touchRef.current = {
        x: e.clientX,
        y: e.clientY,
        active: true,
        targetId: testid,
      };
      scrolledRef.current = false;
    },
    onPointerUp(e) {
      const s = touchRef.current;
      touchRef.current = { x: 0, y: 0, active: false, targetId: null };
      if (!s.active) return;
      if (!e.pointerType || e.pointerType === "mouse") {
        suppressSelectRef.current = false;
        return;
      }
      if (s.targetId !== testid) {
        setTimeout(() => { suppressSelectRef.current = false; }, 0);
        return;
      }
      // If the list scrolled between down and up, the user was
      // scrolling not tapping — do not commit.
      if (scrolledRef.current) {
        scrolledRef.current = false;
        setTimeout(() => { suppressSelectRef.current = false; }, 0);
        return;
      }
      // Secondary guard: reject large positional deltas even
      // when the row sits outside a scrolling container.
      const dx = e.clientX - s.x;
      const dy = e.clientY - s.y;
      if (dx * dx + dy * dy > TOUCH_MOVE_CANCEL_PX * TOUCH_MOVE_CANCEL_PX) {
        setTimeout(() => { suppressSelectRef.current = false; }, 0);
        return;
      }
      e.preventDefault();
      commit();
      setTimeout(() => { suppressSelectRef.current = false; }, 0);
    },
    onPointerCancel() {
      touchRef.current = { x: 0, y: 0, active: false, targetId: null };
      scrolledRef.current = false;
      suppressSelectRef.current = false;
    },
  });

  const guardedOnSelect = (commit) => () => {
    if (suppressSelectRef.current) return;
    commit();
  };

  return { commitHandlersFor, guardedOnSelect };
}

export default useCmdkTouchGuard;
