// SectionTile — unified tile used across every section landing
// (Hub home, FieldSection, SafetySection, QaqcSection, FieldLeadershipHub).
//
// One look, one rhythm, one set of hover states. Each tile has:
//   * 1.5px top accent bar in the per-tile color
//   * 14×14 colored icon chip top-left
//   * Optional small pill in the top-right (e.g. "Existing Form", "Field Leadership")
//   * Display-font 3xl/4xl title
//   * Slate-600 description
//   * Optional bullet list under the description
//   * Bottom-aligned CTA: mono caps + ArrowRight icon
//
// Tile color is driven by an `accent` prop. Supported values are kept in
// one place (the ACCENTS table) so the visual library stays small and we
// don't accidentally invent new colors per page.

import React from "react";
import { CanonicalCard } from "@/components/CanonicalCard";

const ACCENTS = {
  red:      { bar: "bg-red-700",     icon: "bg-red-700",     ring: "hover:border-red-700",     cta: "text-red-700",     pill: "bg-red-100 text-red-800" },
  redDeep:  { bar: "bg-red-900",     icon: "bg-red-900",     ring: "hover:border-red-900",     cta: "text-red-900",     pill: "bg-red-100 text-red-900" },
  amber:    { bar: "bg-amber-600",   icon: "bg-amber-600",   ring: "hover:border-amber-600",   cta: "text-amber-700",   pill: "bg-amber-100 text-amber-800" },
  orange:   { bar: "bg-orange-600",  icon: "bg-orange-600",  ring: "hover:border-orange-600",  cta: "text-orange-700",  pill: "bg-orange-100 text-orange-800" },
  yellow:   { bar: "bg-yellow-500",  icon: "bg-yellow-500",  ring: "hover:border-yellow-500",  cta: "text-yellow-800",  pill: "bg-yellow-100 text-yellow-900" },
  lime:     { bar: "bg-lime-600",    icon: "bg-lime-600",    ring: "hover:border-lime-600",    cta: "text-lime-700",    pill: "bg-lime-100 text-lime-800" },
  emerald:  { bar: "bg-emerald-600", icon: "bg-emerald-600", ring: "hover:border-emerald-600", cta: "text-emerald-700", pill: "bg-emerald-100 text-emerald-800" },
  cyan:     { bar: "bg-cyan-600",    icon: "bg-cyan-600",    ring: "hover:border-cyan-600",    cta: "text-cyan-700",    pill: "bg-cyan-100 text-cyan-800" },
  blue:     { bar: "bg-blue-600",    icon: "bg-blue-600",    ring: "hover:border-blue-600",    cta: "text-blue-700",    pill: "bg-blue-100 text-blue-800" },
  indigo:   { bar: "bg-indigo-700",  icon: "bg-indigo-700",  ring: "hover:border-indigo-700",  cta: "text-indigo-700",  pill: "bg-indigo-100 text-indigo-800" },
  purple:   { bar: "bg-purple-700",  icon: "bg-purple-700",  ring: "hover:border-purple-700",  cta: "text-purple-700",  pill: "bg-purple-100 text-purple-800" },
  fuchsia:  { bar: "bg-fuchsia-700", icon: "bg-fuchsia-700", ring: "hover:border-fuchsia-700", cta: "text-fuchsia-700", pill: "bg-fuchsia-100 text-fuchsia-800" },
  rose:     { bar: "bg-rose-700",    icon: "bg-rose-700",    ring: "hover:border-rose-700",    cta: "text-rose-700",    pill: "bg-rose-100 text-rose-800" },
  slate:    { bar: "bg-slate-700",   icon: "bg-slate-700",   ring: "hover:border-slate-700",   cta: "text-slate-700",   pill: "bg-slate-100 text-slate-800" },
};

export function SectionTile({
  to,
  href,
  icon: Icon,
  title,
  desc,
  bullets,
  accent = "red",
  pillLabel,
  ctaLabel = "Open",
  disabled = false,
  disabledLabel,
  testId,
}) {
  const toneMap = {
    red: "red",
    redDeep: "red",
    amber: "amber",
    orange: "orange",
    yellow: "yellow",
    lime: "emerald",
    emerald: "emerald",
    cyan: "cyan",
    blue: "blue",
    indigo: "indigo",
    purple: "purple",
    fuchsia: "purple",
    rose: "red",
    slate: "slate",
  };

  return (
    <CanonicalCard
      to={to}
      href={href}
      icon={Icon}
      tone={toneMap[accent] || "red"}
      size="feature"
      eyebrow={pillLabel}
      title={title}
      description={desc}
      listItems={bullets || []}
      ctaLabel={disabled ? (disabledLabel || "Locked") : `${ctaLabel} →`}
      disabled={disabled}
      disabledLabel={disabledLabel || "Locked"}
      testId={testId}
    />
  );
}

export default SectionTile;
