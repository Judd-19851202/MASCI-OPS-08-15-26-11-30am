// PortalLoginHelp.jsx — Consistent pre-login discoverability strip
// for every protected portal login page (HR · Safety · Shop · Dispatch ·
// PM · Admin · Field Leadership).
//
// iter202 fix — addresses the operational consistency gap surfaced by
// the operator: "other portals still lack visible operational
// login/training identity paths inside the Guidance ecosystem."
//
// Each portal login can pass:
//   - portal     : "hr" | "safety" | "shop" | "dispatch" | "pm" | "admin" | "leadership"
//   - identityId : guidance article id describing "what does this portal do?"
//                  (optional — until Pass 5 saturates these, falls back to
//                   /guidance which is always available)
//   - onboardId  : onboarding article id (optional)
//   - tshootId   : troubleshooting article id (optional)
//
// Missing articles → falls back to the universal /guidance landing.
// All links open the Operational Guidance Center, which is RBAC-aware
// and bilingual.
import React from "react";
import { Link } from "react-router-dom";
import { BookOpen, LifeBuoy, GraduationCap } from "lucide-react";
import { useT } from "@/lib/i18n";

const PORTAL_LABELS = {
  hr:         { en: "HR Portal",                 es: "Portal de RH" },
  safety:     { en: "Safety Portal",             es: "Portal de Seguridad" },
  shop:       { en: "Shop Portal",               es: "Portal de Taller" },
  dispatch:   { en: "Dispatch Portal",           es: "Portal de Despacho" },
  pm:         { en: "PM Portal",                 es: "Portal de PM" },
  admin:      { en: "Admin Console",             es: "Consola de Admin" },
  leadership: { en: "Field Leadership Portal",   es: "Portal de Liderazgo de Campo" },
};

export function PortalLoginHelp({ portal, identityId, onboardId, tshootId }) {
  const { t, lang } = useT();
  const portalLabel = (PORTAL_LABELS[portal] || {})[lang] || (PORTAL_LABELS[portal] || {}).en || "";

  // Defaults: if a specific article isn't named, fall back to /guidance.
  const onboardHref  = onboardId  ? `/guidance/${onboardId}`  : "/guidance";
  const identityHref = identityId ? `/guidance/${identityId}` : "/guidance";
  const tshootHref   = tshootId   ? `/guidance/${tshootId}`   : "/guidance/public-cant-login";

  return (
    <div
      className="mt-6 pt-5 border-t border-slate-200 space-y-2"
      data-testid={`portal-login-help-${portal}`}
    >
      <div className="font-mono text-[10px] uppercase tracking-[0.2em] text-slate-500 font-bold flex items-center gap-1.5">
        <BookOpen className="w-3.5 h-3.5" />
        {portalLabel
          ? (lang === "es" ? `Nuevo en ${portalLabel}?` : `New to ${portalLabel}?`)
          : t("New to this portal?")}
      </div>
      <Link
        to={onboardHref}
        className="block text-sm text-amber-700 hover:underline flex items-center gap-1.5"
        data-testid={`portal-login-help-${portal}-onboarding`}
      >
        <GraduationCap className="w-3.5 h-3.5" />
        {t("First-Week Onboarding")} →
      </Link>
      <Link
        to={identityHref}
        className="block text-sm text-amber-700 hover:underline flex items-center gap-1.5"
        data-testid={`portal-login-help-${portal}-identity`}
      >
        <BookOpen className="w-3.5 h-3.5" />
        {portalLabel
          ? (lang === "es" ? `¿Qué hace el ${portalLabel}?` : `What does ${portalLabel} do?`)
          : t("What does this portal do?")}
        {" →"}
      </Link>
      <Link
        to={tshootHref}
        className="block text-sm text-slate-600 hover:underline flex items-center gap-1.5"
        data-testid={`portal-login-help-${portal}-troubleshoot`}
      >
        <LifeBuoy className="w-3.5 h-3.5" />
        {t("Can't sign in?")} →
      </Link>
    </div>
  );
}
