// LIST-VIRT-001 · in-house windowing hook (no new dependency).
//
// Renders only the rows visible in `scrollerRef` plus an overscan margin.
// Preserves total scroll height with top/bottom spacer rows so the existing
// scroll UX (scrollbar position, keyboard PageUp/PageDown, anchor link
// behaviour) is untouched.
//
// Requirements:
//   - Caller provides a ref to a single scroll container (the element with
//     `overflow-y: auto` and a bounded height).
//   - All rows must have the same height (`rowHeight`, in px).
//   - `count` is the total number of rows; the hook does NOT mutate or read
//     the items array — caller slices using the returned `range`.
//
// Returns:
//   - `range.start` (inclusive), `range.end` (exclusive)
//   - `paddingTop`  — px to reserve ABOVE the visible window
//   - `paddingBottom` — px to reserve BELOW the visible window
//
// Usage:
//   const scrollerRef = useRef(null);
//   const { range, paddingTop, paddingBottom } = useWindowedRows({
//     count: rows.length, rowHeight: 50, scrollerRef,
//   });
//   // inside <tbody>:
//   {paddingTop > 0 && <tr aria-hidden="true" style={{ height: paddingTop }} />}
//   {rows.slice(range.start, range.end).map(...)}
//   {paddingBottom > 0 && <tr aria-hidden="true" style={{ height: paddingBottom }} />}

import { useEffect, useState } from "react";

export function useWindowedRows({ count, rowHeight, scrollerRef, overscan = 8 }) {
  const [range, setRange] = useState(() => ({
    start: 0,
    end: Math.min(count, 30),
  }));

  useEffect(() => {
    const el = scrollerRef.current;
    if (!el) return;

    let raf = 0;
    const recompute = () => {
      raf = 0;
      const scrollTop = el.scrollTop || 0;
      const viewportH = el.clientHeight || 0;
      const visibleCount = Math.ceil(viewportH / rowHeight) || 1;
      const start = Math.max(0, Math.floor(scrollTop / rowHeight) - overscan);
      const end = Math.min(count, start + visibleCount + overscan * 2);
      setRange((prev) => (prev.start === start && prev.end === end ? prev : { start, end }));
    };

    const onScrollOrResize = () => {
      if (!raf) raf = requestAnimationFrame(recompute);
    };

    recompute();
    el.addEventListener("scroll", onScrollOrResize, { passive: true });
    const ro = typeof ResizeObserver !== "undefined" ? new ResizeObserver(onScrollOrResize) : null;
    if (ro) ro.observe(el);

    return () => {
      el.removeEventListener("scroll", onScrollOrResize);
      if (ro) ro.disconnect();
      if (raf) cancelAnimationFrame(raf);
    };
  }, [count, rowHeight, scrollerRef, overscan]);

  return {
    range,
    paddingTop: range.start * rowHeight,
    paddingBottom: Math.max(0, (count - range.end) * rowHeight),
  };
}
