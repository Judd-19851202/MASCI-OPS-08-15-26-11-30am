// BackLink.jsx — iter97
//
// Single source of truth for "← Back" links across every page. Replaces
// 40+ one-off Tailwind+Link snippets with two consistent variants.
//
// Why this exists: every page used to roll its own back link with subtly
// different padding, icon sizes (w-3.5 vs w-4), spacing (mr-0 vs mr-1),
// and color treatments. Result was that you couldn't predict where the
// back button would be or what it would look like — and worse, where it
// would TAKE you (some hardcoded the wrong destination — see iter95/96).
//
// This component:
//   • Auto-computes the destination from the user's role when `to` isn't
//     given (admin → /admin, pm → /pm, hr → /hr, shop → /shop, else /).
//   • Auto-computes the label to match.
//   • Renders two visual variants:
//       - "header"  — dark backgrounds (top nav bars). Compact, white text.
//       - "body"    — light backgrounds (content sections). Muted text.
//   • Uses the SAME ChevronLeft icon size + spacing + uppercase mono
//     label everywhere, so the muscle memory pattern is identical.

import React from "react";
import { Link } from "react-router-dom";
import { ArrowLeft } from "lucide-react";
import { isAdmin } from "@/lib/adminAuth";
import { isPm } from "@/lib/pmAuth";
import { isShop } from "@/lib/shopAuth";
import { isHr } from "@/lib/hrAuth";
import { useT } from "@/lib/i18n";

function autoTarget() {
  if (isAdmin()) return { to: "/admin", label: "Administration" };
  if (isPm()) return { to: "/pm", label: "Project Management" };
  if (isHr()) return { to: "/hr", label: "Human Resources" };
  if (isShop()) return { to: "/shop", label: "Shop Operations" };
  return { to: "/", label: "Home" };
}

/**
 * @param {string} [to] - explicit destination; if omitted, computed from role.
 * @param {string} [label] - explicit label; if omitted, computed from role.
 * @param {"header"|"body"} [variant] - which palette to use. Defaults to "body".
 * @param {string} [className] - extra utilities to merge in.
 * @param {string} [testId] - data-testid override.
 */
export default function BackLink({
  to,
  label,
  variant = "body",
  className = "",
  testId = "back-link",
}) {
  const { t } = useT();
  const fallback = autoTarget();
  const dest = to || fallback.to;
  const text = t(label || fallback.label);

  const base =
    "inline-flex items-center gap-1.5 font-mono text-[11px] uppercase tracking-[0.2em] font-bold transition-colors";

  const variantCls =
    variant === "header"
      ? // sits inside a dark navy/red header bar
        "text-white/80 hover:text-white"
      : // sits in a content section on a light background
        "text-slate-600 hover:text-red-700";

  return (
    <Link to={dest} className={`${base} ${variantCls} ${className}`} data-testid={testId}>
      <ArrowLeft className="w-3.5 h-3.5" />
      <span>{text}</span>
    </Link>
  );
}
