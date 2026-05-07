import React from "react";
import { ForgedOpsAttribution } from "@/components/ForgedOpsAttribution";

/**
 * GlobalFooter — single, app-wide attribution strip mounted once in App.js
 * BELOW the routed page content. Every page in the app inherits it.
 *
 * Field-crew dominant: text-only, micro-typography, sits at the bottom of
 * the viewport without competing with MASCI branding above it.
 */
export default function GlobalFooter() {
  return (
    <footer
      className="border-t border-slate-200/60 bg-white py-3 px-4 mt-auto"
      data-testid="global-footer"
    >
      <ForgedOpsAttribution variant="global" />
    </footer>
  );
}
