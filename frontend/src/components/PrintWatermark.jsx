import React from "react";

/**
 * Small red-MASCI-mark watermark that prints in the bottom-right corner of
 * every page of a printed report. Hidden on screen — visible only in print
 * preview / when sending to PDF.
 *
 *   position: fixed    → repeats on every printed page (Chrome / Safari)
 *   opacity: 0.10      → faint enough to never compete with content
 *   width: 0.6in       → about thumbnail-sized at 100% scale
 *
 * Usage: drop one anywhere inside any View component.
 *
 *   <PrintWatermark />
 */
export const PrintWatermark = () => (
  <div
    aria-hidden="true"
    className="hidden print:block"
    style={{
      position: "fixed",
      right: "0.35in",
      bottom: "0.35in",
      width: "0.6in",
      height: "0.6in",
      opacity: 0.1,
      pointerEvents: "none",
      zIndex: 9999,
      // ensure browsers honor the opacity in print
      WebkitPrintColorAdjust: "exact",
      printColorAdjust: "exact",
    }}
    data-testid="print-watermark"
  >
    <img
      src="/masci-mark.png"
      alt=""
      style={{
        width: "100%",
        height: "100%",
        objectFit: "contain",
        userSelect: "none",
      }}
      draggable={false}
    />
  </div>
);

export default PrintWatermark;
