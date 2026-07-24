// AccessDenied — Iter149 (Phase 2.5). Clean "you don't have access"
// page rendered when an authenticated user lands on a route belonging
// to a different portal scope. Replaces the jarring bounce to a
// portal login page (which made it feel like they got signed out).
//
// Behavior:
//   * If the user has at LEAST one active portal session, show a
//     primary CTA back to their home portal + a list of other
//     portals they're authorized for.
//   * If fully anonymous, surface a "Sign in" CTA back to /sign-in.
//   * Always keep a "Return to Home" escape hatch.

import React from "react";
import { Link, useLocation } from "react-router-dom";
import { ShieldOff, ArrowRight, Home, LogIn } from "lucide-react";
import { MasciLogo } from "@/components/MasciLogo";
import {
  assignedPortals, homePortal, isSignedInAnywhere, reachablePortals,
  PORTAL_LABEL, PORTAL_HOME,
} from "@/lib/permissions";
import { useT } from "@/lib/i18n";

export default function AccessDenied({ attemptedPortal }) {
  const { t } = useT();
  const location = useLocation();
  const home = homePortal();
  const reachable = reachablePortals();
  const assigned = assignedPortals();
  const others = reachable.filter((p) => p !== home && p !== attemptedPortal);
  const assignedButUnavailable = assigned.filter((p) => !reachable.includes(p) && p !== attemptedPortal);
  const signedIn = isSignedInAnywhere();
  // attempted portal label — for the body copy
  const what = attemptedPortal
    ? PORTAL_LABEL[attemptedPortal] || attemptedPortal
    : t("that section");

  return (
    <div className="min-h-screen blueprint-bg flex flex-col" data-testid="access-denied-page">
      <div className="caution-stripe" />
      <header className="bg-slate-900 border-b-4 border-red-700">
        <div className="max-w-3xl mx-auto px-5 sm:px-8 py-5 flex items-center justify-between">
          <MasciLogo variant="mark" size="xl" homeLink="/" />
        </div>
      </header>

      <main className="flex-1 max-w-3xl mx-auto w-full px-5 sm:px-8 py-12 sm:py-16">
        <div className="bg-white border-2 border-red-700 rounded-md p-6 sm:p-10 shadow-md">
          <div className="inline-flex items-center justify-center w-14 h-14 rounded-md bg-red-700 text-white mb-5">
            <ShieldOff className="w-7 h-7" />
          </div>

          <span className="font-mono text-[11px] uppercase tracking-[0.22em] text-red-700 font-black">
            {t("403 · Access Restricted")}
          </span>
          <h1 className="font-display text-3xl sm:text-4xl font-black tracking-tight text-slate-900 mt-1.5">
            {t("You don't have access to")} {what}
          </h1>
          <p className="text-slate-600 mt-3 leading-relaxed text-sm sm:text-base">
            {signedIn
              ? t("This section belongs to a different portal scope or your current browser session for it is not reachable right now. You can jump back to a portal that is currently reachable below. If this is unexpected, contact your administrator.")
              : t("You need to sign in to view this section. Pick the right portal sign-in below — or head back to the public home.")}
          </p>

          {/* Primary CTA */}
          <div className="mt-6 flex flex-col sm:flex-row gap-2.5">
            {signedIn && home ? (
              <Link
                to={PORTAL_HOME[home]}
                className="inline-flex items-center justify-center gap-2 h-11 px-5 rounded-md bg-slate-900 hover:bg-red-700 text-white font-bold uppercase tracking-wide text-xs transition-colors"
                data-testid="access-denied-home-portal"
              >
                {t("Back to")} {PORTAL_LABEL[home]} <ArrowRight className="w-4 h-4" />
              </Link>
            ) : (
              <Link
                to="/sign-in"
                className="inline-flex items-center justify-center gap-2 h-11 px-5 rounded-md bg-slate-900 hover:bg-red-700 text-white font-bold uppercase tracking-wide text-xs transition-colors"
                data-testid="access-denied-sign-in"
              >
                <LogIn className="w-4 h-4" /> {t("Sign in")}
              </Link>
            )}
            <Link
              to="/"
              className="inline-flex items-center justify-center gap-2 h-11 px-5 rounded-md bg-white border-2 border-slate-300 hover:border-slate-400 text-slate-900 font-bold uppercase tracking-wide text-xs transition-colors"
              data-testid="access-denied-home"
            >
              <Home className="w-4 h-4" /> {t("Public Home")}
            </Link>
          </div>

          {/* Other authorized portals */}
          {signedIn && others.length > 0 && (
            <div className="mt-8 pt-6 border-t border-slate-200">
              <div className="font-mono text-[10px] uppercase tracking-[0.22em] text-slate-500 font-bold mb-2.5">
                {t("Other portals currently reachable in this session")}
              </div>
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-x-8 gap-y-4.5">
                {others.map((p) => (
                  <Link
                    key={p}
                    to={PORTAL_HOME[p]}
                    className="flex items-center justify-between gap-2 px-3.5 py-2.5 rounded-md border border-slate-200 hover:border-slate-400 hover:bg-slate-50 transition-colors"
                    data-testid={`access-denied-portal-${p}`}
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

          {signedIn && assignedButUnavailable.length > 0 && (
            <div className="mt-6 rounded-md border border-amber-300 bg-amber-50 px-4 py-3" data-testid="access-denied-assigned-unreachable">
              <div className="font-mono text-[10px] uppercase tracking-[0.22em] text-amber-900 font-bold mb-1">
                {t("Assigned portals not currently reachable")}
              </div>
              <p className="text-sm text-amber-900">
                {assignedButUnavailable.map((p) => PORTAL_LABEL[p] || p).join(", ")}
              </p>
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
