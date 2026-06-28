// iter322 · Portal Continuity Banner
//
// Renders a slim breadcrumb-style banner at the top of any page that
// preserves cross-portal context. When a user clicks "Training Center
// & Guides" from inside (say) Safety Portal, that link appends
// `?from=safety` and lands them on /guidance. This banner reads the
// param and shows:
//
//     ← Back to Safety Portal · You are viewing platform Guidance
//
// styled with the originating portal's identity color so the user
// never feels they got "kicked out" of their portal.
//
// Stabilization-safe: zero auth changes · no routing changes · pure
// presentational. Bilingual.

import React from "react";
import { useLocation, Link } from "react-router-dom";
import { ArrowLeft } from "lucide-react";
import { useT } from "@/lib/i18n";

// Portal registry — maps `?from=<key>` to display name, return path,
// and identity color. Keys must match the values we append to Guides
// links in each hub. Add new portals here as new origins surface.
const PORTAL_REGISTRY = {
  safety: {
    label: { en: "Safety Operations", es: "Operaciones de Seguridad" },
    to: "/safety-portal",
    accent: "cyan",
    stripeClass: "border-l-cyan-600",
    kickerClass: "text-cyan-700",
  },
  hr: {
    label: { en: "Human Resources", es: "Recursos Humanos" },
    to: "/hr",
    accent: "purple",
    stripeClass: "border-l-purple-600",
    kickerClass: "text-purple-700",
  },
  leadership: {
    label: { en: "Field Leadership", es: "Liderazgo de Campo" },
    to: "/leadership",
    accent: "red",
    stripeClass: "border-l-red-600",
    kickerClass: "text-red-700",
  },
  shop: {
    label: { en: "Shop Operations", es: "Operaciones de Taller" },
    to: "/shop",
    accent: "amber",
    stripeClass: "border-l-amber-500",
    kickerClass: "text-amber-700",
  },
  dispatch: {
    label: { en: "Transportation Operations", es: "Operaciones de Transporte" },
    to: "/dispatch-portal",
    accent: "orange",
    stripeClass: "border-l-orange-500",
    kickerClass: "text-orange-700",
  },
  field: {
    label: { en: "Field", es: "Campo" },
    to: "/field",
    accent: "amber",
    stripeClass: "border-l-amber-500",
    kickerClass: "text-amber-700",
  },
};

/**
 * PortalContextBanner — shows "← Back to {Portal}" with `?from=` query
 * param sourcing. Optional `currentLabel` overrides the default
 * "You are viewing platform Guidance" text.
 *
 * Renders nothing when no `?from=` param is present (zero footprint).
 */
export default function PortalContextBanner({ currentLabel }) {
  const { t, lang } = useT();
  const loc = useLocation();
  const params = new URLSearchParams(loc.search);
  const from = params.get("from");
  if (!from) return null;
  const portal = PORTAL_REGISTRY[from];
  if (!portal) return null;
  const label = portal.label[lang] || portal.label.en;
  return (
    <div
      className={`mb-6 rounded-md border border-slate-200 border-l-4 ${portal.stripeClass} bg-white p-3 sm:p-4 flex flex-col sm:flex-row sm:items-center gap-2 sm:gap-4`}
      data-testid="portal-context-banner"
    >
      <Link
        to={portal.to}
        className={`inline-flex items-center gap-1 font-mono text-xs uppercase tracking-[0.22em] font-bold ${portal.kickerClass} hover:underline shrink-0`}
        data-testid="portal-context-back-link"
      >
        <ArrowLeft className="w-3.5 h-3.5" />
        {t("Back to")} {label}
      </Link>
      <span className="hidden sm:inline-block h-4 w-px bg-slate-200" aria-hidden="true" />
      <span className="text-xs text-slate-500 italic">
        {currentLabel || t("You are viewing platform Guidance")}
      </span>
    </div>
  );
}

/**
 * AuthRequiredBanner — shown on login pages when the user arrived via
 * a redirect from a protected workflow. Reads `location.state.continuity`
 * (populated by `<Require*>` guards via `buildContinuity()`). Renders:
 *
 *   ▌ Sign-in required
 *   ▌ You selected {workflow} from the {originating portal hub}.
 *   ▌ This workflow requires {role} access.
 *   ▌ After sign-in, you'll continue to {workflow}.
 *   ▌ ← Back to {origin portal}
 *
 * Renders nothing when no continuity state is present (zero footprint).
 */
export function AuthRequiredBanner() {
  const { t, lang } = useT();
  const loc = useLocation();
  const continuity = loc.state?.continuity;
  if (!continuity) return null;
  const workflow = continuity.workflow || t("This workflow");
  const role = continuity.role || t("elevated access");
  const origin = continuity.from ? PORTAL_REGISTRY[continuity.from] : null;
  const originLabel = origin ? (origin.label[lang] || origin.label.en) : null;
  return (
    <div
      className="mb-6 rounded-md border border-slate-200 border-l-4 border-l-amber-500 bg-white p-4"
      data-testid="auth-required-banner"
    >
      <div className="font-mono text-xs uppercase tracking-[0.22em] text-amber-700 font-bold">
        {t("Sign-in required")}
      </div>
      {originLabel ? (
        <p className="mt-2 text-sm text-slate-700 leading-relaxed">
          {t("You selected {workflow} from {origin}.")
            .replace("{workflow}", t(workflow))
            .replace("{origin}", originLabel)}
        </p>
      ) : null}
      <p className="mt-1 text-sm text-slate-700 leading-relaxed">
        {t("This workflow requires {role} access.")
          .replace("{role}", t(role))}
      </p>
      <p className="mt-1 text-xs text-slate-500 italic">
        {t("After sign-in, you'll continue to {workflow}.")
          .replace("{workflow}", t(workflow))}
      </p>
      {origin ? (
        <Link
          to={origin.to}
          className={`mt-3 inline-flex items-center gap-1 font-mono text-xs uppercase tracking-[0.22em] font-bold ${origin.kickerClass} hover:underline`}
          data-testid="auth-required-back-link"
        >
          <ArrowLeft className="w-3.5 h-3.5" />
          {t("Back to")} {originLabel}
        </Link>
      ) : null}
    </div>
  );
}
