// NotFound — Iter181. Catch-all 404 page rendered when React Router
// has no matching route. Previously unmatched paths rendered only the
// global navbar + footer with a blank middle (the "blank shell" the
// 2026-05-17 production verification flagged). This component mirrors
// the AccessDenied visual language so 404s feel like part of the
// platform, not a stack-trace.
//
// Strictly UX. Backend authorization is unchanged. Authenticated
// users still get a route home; anon users get sign-in CTAs.
//
// iter-RC1-FH · M-18 closure · all visible strings now route through
// useT() so the 404 surface honors the EN/ES contract.

import React from "react";
import { Link, useLocation } from "react-router-dom";
import { FileQuestion, ArrowRight, Home, LogIn } from "lucide-react";
import { MasciLogo } from "@/components/MasciLogo";
import {
  authorizedPortals, homePortal, isSignedInAnywhere,
  PORTAL_LABEL, PORTAL_HOME,
} from "@/lib/permissions";
import { useT } from "@/lib/i18n";

export default function NotFound() {
  const { t } = useT();
  const location = useLocation();
  const home = homePortal();
  const others = authorizedPortals().filter((p) => p !== home);
  const signedIn = isSignedInAnywhere();

  return (
    <div className="min-h-screen blueprint-bg flex flex-col" data-testid="not-found-page">
      <div className="caution-stripe" />
      <header className="bg-slate-900 border-b-4 border-red-700">
        <div className="max-w-3xl mx-auto px-5 sm:px-8 py-5 flex items-center justify-between">
          <MasciLogo variant="mark" size="xl" homeLink="/" />
        </div>
      </header>

      <main className="flex-1 max-w-3xl mx-auto w-full px-5 sm:px-8 py-12 sm:py-16">
        <div className="bg-white border border-slate-200 rounded-md p-6 sm:p-10 shadow-md">
          <div className="inline-flex items-center justify-center w-14 h-14 rounded-md bg-slate-900 text-white mb-5">
            <FileQuestion className="w-7 h-7" />
          </div>

          <span className="font-mono text-[11px] uppercase tracking-[0.22em] text-slate-600 font-black">
            {t("404 · Page not found")}
          </span>
          <h1 className="font-display text-3xl sm:text-4xl font-black tracking-tight text-slate-900 mt-1.5">
            {t("We couldn't find that page")}
          </h1>
          <p className="text-slate-600 mt-3 leading-relaxed text-sm sm:text-base">
            {signedIn
              ? t("The URL doesn't match any active section of the platform. It may have moved, been renamed, or never existed. Use the buttons below to get back to a portal you have access to.")
              : t("The URL doesn't match any active section of the platform. Sign in to access your portal, or head back to the public home.")}
          </p>

          <div className="mt-6 flex flex-col sm:flex-row gap-2.5">
            {signedIn && home ? (
              <Link
                to={PORTAL_HOME[home]}
                className="inline-flex items-center justify-center gap-2 h-11 px-5 rounded-md bg-slate-900 hover:bg-red-700 text-white font-bold uppercase tracking-wide text-xs transition-colors"
                data-testid="not-found-home-portal"
              >
                {t("Back to")} {PORTAL_LABEL[home]} <ArrowRight className="w-4 h-4" />
              </Link>
            ) : (
              <Link
                to="/sign-in"
                className="inline-flex items-center justify-center gap-2 h-11 px-5 rounded-md bg-slate-900 hover:bg-red-700 text-white font-bold uppercase tracking-wide text-xs transition-colors"
                data-testid="not-found-sign-in"
              >
                <LogIn className="w-4 h-4" /> {t("Sign in")}
              </Link>
            )}
            <Link
              to="/"
              className="inline-flex items-center justify-center gap-2 h-11 px-5 rounded-md bg-white border-2 border-slate-300 hover:border-slate-400 text-slate-900 font-bold uppercase tracking-wide text-xs transition-colors"
              data-testid="not-found-home"
            >
              <Home className="w-4 h-4" /> {t("Public Home")}
            </Link>
          </div>

          {signedIn && others.length > 0 && (
            <div className="mt-8 pt-6 border-t border-slate-200">
              <div className="font-mono text-[10px] uppercase tracking-[0.22em] text-slate-500 font-bold mb-2.5">
                {t("Other portals you can access")}
              </div>
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-x-8 gap-y-4.5">
                {others.filter((p) => PORTAL_LABEL[p]).map((p) => (
                  <Link
                    key={p}
                    to={PORTAL_HOME[p]}
                    className="flex items-center justify-between gap-2 px-3.5 py-2.5 rounded-md border border-slate-200 hover:border-slate-400 hover:bg-slate-50 transition-colors"
                    data-testid={`not-found-portal-${p}`}
                  >
                    <span className="font-bold text-sm text-slate-900">
                      {PORTAL_LABEL[p]}
                    </span>
                    <ArrowRight className="w-4 h-4 text-slate-400" />
                  </Link>
                ))}
              </div>
            </div>
          )}

          <div className="mt-8 text-[11px] text-slate-400 font-mono">
            {t("Path:")} <span className="text-slate-500">{location.pathname}</span>
          </div>
        </div>
      </main>
    </div>
  );
}
