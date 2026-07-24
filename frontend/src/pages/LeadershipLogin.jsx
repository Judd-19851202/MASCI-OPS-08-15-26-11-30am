// LeadershipLogin.jsx — retired legacy shared-secret Field Leadership gate.
//
// First-class /leadership/login URL parallel to /hr/login · /pm/login ·
// /shop/login · /safety-portal/login · /dispatch-portal/login. This is
// the dedicated portal door for Field Leadership (Superintendents,
// Foremen, Field Leaders, Operations Oversight).
//
// Shared-secret access is no longer permitted.
import React, { useEffect, useState } from "react";
import { useNavigate, Link } from "react-router-dom";
import { ArrowLeft, ShieldCheck, HardHat } from "lucide-react";
import { Button } from "@/components/ui/button";
import { MasciLogo } from "@/components/MasciLogo";
import { LangToggle } from "@/components/LangToggle";
import { CompanyInfoDialog } from "@/components/CompanyInfoDialog";
import { ForgedOpsAttribution } from "@/components/ForgedOpsAttribution";
import { useT } from "@/lib/i18n";
import { isLeadershipAuthed } from "@/lib/leadershipAuth";

export default function LeadershipLogin() {
  const { t } = useT();
  const navigate = useNavigate();
  useEffect(() => {
    if (isLeadershipAuthed()) {
      navigate("/leadership", { replace: true });
    }
  }, [navigate]);

  return (
    <div className="min-h-screen blueprint-bg flex flex-col" data-testid="leadership-login-page">
      <div className="caution-stripe" />
      <header className="bg-slate-900 border-b-4 border-red-700">
        <div className="max-w-6xl mx-auto px-5 sm:px-8 py-4 flex items-center justify-between">
          <Link
            to="/"
            className="inline-flex items-center min-h-[44px] -ml-2 px-2 text-white hover:text-red-300 text-sm font-bold uppercase tracking-wide"
            data-testid="leadership-login-back"
          >
            <ArrowLeft className="w-4 h-4 mr-1" /> {t("Home")}
          </Link>
          <MasciLogo variant="mark" size="lg" className="hidden sm:block" homeLink="/" />
          <MasciLogo variant="mark" size="md" className="sm:hidden" homeLink="/" />
          <div className="flex items-center gap-2">
            <LangToggle />
            <CompanyInfoDialog />
          </div>
        </div>
      </header>

      <main className="flex-1 flex items-center justify-center px-5 sm:px-8 py-12">
        <div className="w-full max-w-md bg-white border border-slate-200 rounded-md p-7 sm:p-9 shadow-xl">
          {/* Portal identity badge */}
          <div className="flex items-center gap-3 mb-2">
            <div className="inline-flex items-center justify-center w-12 h-12 rounded-md bg-red-700 text-white">
              <HardHat className="w-6 h-6" />
            </div>
            <div>
              <div className="font-mono text-[10px] uppercase tracking-[0.25em] text-red-700 font-bold">
                {t("Field Leadership Portal")}
              </div>
              <h1 className="font-display text-2xl font-black text-slate-900 leading-none mt-1">
                {t("Sign In")}
              </h1>
            </div>
          </div>

          {/* Operational identity statement — explains WHO this is for and WHY */}
          <p className="text-slate-700 text-sm mt-3 mb-2 leading-relaxed">
            {t("This shared-password Field Leadership entry has been retired for security reasons.")}
          </p>
          <p className="text-slate-600 text-xs mb-4 leading-relaxed">
            {t("Use the canonical Field Leadership portal sign-in with your assigned account. Shared access codes no longer grant entry.")}
          </p>
          <Button
            type="button"
            onClick={() => navigate("/leadership/login", { replace: true })}
            className="w-full h-12 bg-red-700 hover:bg-red-800 text-white font-bold uppercase tracking-wide text-sm border-b-2 border-red-900"
            data-testid="leadership-login-retired-redirect"
          >
            {t("Go to Canonical Sign In")}
          </Button>

          {/* Discoverability — pre-login guidance entry points */}
          <div className="mt-6 pt-5 border-t border-slate-200 space-y-2">
            <div className="font-mono text-[10px] uppercase tracking-[0.2em] text-slate-500 font-bold">
              {t("New to Field Leadership?")}
            </div>
            <Link
              to="/guidance/onboard-leadership-first-week"
              className="block text-sm text-amber-700 hover:underline"
              data-testid="leadership-login-onboarding-link"
            >
              {t("First-Week Onboarding")} →
            </Link>
            <Link
              to="/guidance/portal-leadership-identity"
              className="block text-sm text-amber-700 hover:underline"
              data-testid="leadership-login-identity-link"
            >
              {t("What does Field Leadership do?")} →
            </Link>
            <Link
              to="/guidance/tshoot-leadership-login"
              className="block text-sm text-slate-600 hover:underline"
              data-testid="leadership-login-troubleshoot-link"
            >
              {t("Can't sign in?")} →
            </Link>
          </div>

          {/* RBAC clarity */}
          <div className="mt-5 bg-slate-50 border border-slate-200 rounded p-3 text-[12px] text-slate-700 flex gap-2 items-start">
            <ShieldCheck className="w-4 h-4 text-slate-500 shrink-0 mt-0.5" />
            <span>
              {t("Admin tokens and PM tokens also satisfy the Field Leadership gate — Operations Managers and PMs can read leadership records without re-signing in.")}
            </span>
          </div>
        </div>
      </main>

      <footer className="max-w-6xl mx-auto px-5 sm:px-8 py-6 flex flex-col items-center gap-3">
        <div className="font-mono text-[10px] uppercase tracking-[0.25em] text-slate-500">
          {t("MASCI · Field Leadership Portal")}
        </div>
        <ForgedOpsAttribution variant="login" />
      </footer>
    </div>
  );
}
