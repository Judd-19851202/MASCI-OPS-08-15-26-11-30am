import React, { useEffect } from "react";
import { Link, useNavigate } from "react-router-dom";
import {
  HardHat,
  GraduationCap,
  ArrowLeft,
  Plus,
  ShieldCheck,
  LogOut,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { MasciLogo } from "@/components/MasciLogo";
import { LangToggle } from "@/components/LangToggle";
import { CompanyInfoDialog } from "@/components/CompanyInfoDialog";
import PortalContextBanner from "@/components/PortalContextBanner";
import { isSafetyForms, clearSafetyFormsToken } from "@/lib/safetyFormsAuth";
import { isSafety } from "@/lib/safetyAuth";
import { isAdmin } from "@/lib/adminAuth";
import { useT } from "@/lib/i18n";

// iter321 · Safety Forms Hub — calm tile pattern (family contract).
// Replaces the legacy hot FormTile (`border-2 border-slate-300 +
// `w-14 h-14` icon chip + `text-2xl` H3 + bottom `border-t-2`).
const STRIPE = { red: "border-l-red-600", amber: "border-l-amber-500" };
const BTN = {
  red: "bg-red-700 hover:bg-red-800",
  amber: "bg-amber-700 hover:bg-amber-800",
};
const FormTile = ({ to, icon: Icon, title, desc, ctaLabel, accent = "red", testId }) => {
  const stripe = STRIPE[accent] || STRIPE.red;
  const btn = BTN[accent] || BTN.red;
  return (
    <Link
      to={to}
      className={`block rounded-lg border border-slate-200 border-l-4 ${stripe} bg-white p-5 hover:shadow-md hover:-translate-y-0.5 hover:border-slate-300 transition-all duration-150 relative`}
      data-testid={testId}
    >
      <div className="flex items-start gap-3">
        <Icon className="w-6 h-6 mt-1 text-slate-700 shrink-0" />
        <div className="flex-1 min-w-0">
          <h3 className="font-display text-lg font-black">{title}</h3>
          <p className="text-sm text-slate-600 mt-1">{desc}</p>
          <span className={`mt-3 inline-flex items-center h-9 px-3 rounded-md ${btn} text-white font-bold uppercase tracking-wide text-xs`}>
            <Plus className="w-3.5 h-3.5 mr-1" /> {ctaLabel} →
          </span>
        </div>
      </div>
    </Link>
  );
};

export default function SafetyFormsHub() {
  const { t } = useT();
  const navigate = useNavigate();

  useEffect(() => {
    // iter323 · Safety Portal ownership — accept any of:
    //   • Safety Portal user (X-Safety-Token)
    //   • Admin (X-Admin-Token)
    //   • Legacy Safety-Forms token (backwards compat)
    // No portal session anywhere → bounce to Safety Portal login.
    if (!isSafety() && !isAdmin() && !isSafetyForms()) {
      navigate("/safety-portal/login?from=safety-forms", { replace: true });
    }
  }, [navigate]);

  const signOut = () => {
    // Only the legacy token is owned by this page. Safety Portal sign-out
    // happens from /safety-portal; Admin sign-out from /admin. Just clear
    // the legacy SF token and route back to the Safety section.
    clearSafetyFormsToken();
    navigate("/safety", { replace: true });
  };

  return (
    <div className="min-h-screen blueprint-bg">
      <div className="caution-stripe" />
      <header className="bg-slate-900 border-b-4 border-red-700">
        <div className="max-w-6xl mx-auto px-3 sm:px-8 py-4 flex items-center justify-between gap-2 flex-wrap">
          <Link
            to="/safety"
            className="inline-flex items-center text-white hover:text-red-300 text-sm font-bold uppercase tracking-wide"
            data-testid="safety-forms-back"
          >
            <ArrowLeft className="w-4 h-4 mr-1" /> {t("Safety")}
          </Link>
          <MasciLogo variant="mark" size="lg" className="hidden sm:block" homeLink="/" />
          <MasciLogo variant="mark" size="md" className="sm:hidden" homeLink="/" />
          <div className="flex items-center gap-2">
            <LangToggle />
            <CompanyInfoDialog />
            <Button
              onClick={signOut}
              variant="outline"
              className="h-9 border-2 border-slate-600 bg-slate-800 text-white hover:border-red-500 hover:text-red-400 text-xs font-bold uppercase tracking-wide"
              data-testid="safety-forms-signout"
            >
              <LogOut className="w-3.5 h-3.5 sm:mr-1" />
              <span className="hidden sm:inline">{t("Sign out")}</span>
            </Button>
          </div>
        </div>
      </header>

      <main className="max-w-6xl mx-auto px-5 sm:px-8 py-8">
        {/* iter322 · Portal continuity — if user arrived from FL with
            `?from=leadership`, show the back-to-FL banner. Zero
            footprint when no `?from=` is present. */}
        <PortalContextBanner currentLabel={t("You are viewing Safety Forms")} />
        <div className="mb-8 flex items-start gap-4">
          <div className="inline-flex items-center justify-center w-12 h-12 rounded-md bg-red-700 text-white shrink-0">
            <ShieldCheck className="w-6 h-6" />
          </div>
          <div className="flex-1">
            <span className="font-mono text-xs uppercase tracking-[0.22em] text-red-700 font-bold">
              {t("Safety Department")}
            </span>
            <h1 className="font-display text-3xl sm:text-4xl font-black tracking-tight text-slate-900 mt-1">
              {t("Safety Forms")}
            </h1>
            <p className="text-slate-600 text-base mt-2 max-w-2xl">
              {t("Issue equipment with full accountability and document use & care training — every submission emails a clean PDF to safety@mascigc.com.")}
            </p>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-x-8 gap-y-4 mb-12">
          <FormTile
            to="/safety/forms/equipment-issuance/new"
            icon={HardHat}
            title={t("Equipment Issuance")}
            desc={t("Issue safety equipment to employees with full chain of custody — itemized inventory, condition, photos, and dual signatures.")}
            ctaLabel={t("START FORM")}
            accent="red"
            testId="safety-forms-tile-issuance"
          />
          <FormTile
            to="/safety/forms/equipment-training/new"
            icon={GraduationCap}
            title={t("Use & Care Training")}
            desc={t("Document equipment training — initial, refresher, or retraining — with topics covered and instructor sign-off.")}
            ctaLabel={t("START FORM")}
            accent="amber"
            testId="safety-forms-tile-training"
          />
        </div>
      </main>

      <footer className="max-w-6xl mx-auto px-5 sm:px-8 py-8 text-center font-mono text-xs uppercase tracking-[0.2em] text-slate-500 border-t-2 border-slate-200">
        {t("MASCI · Safety Department")}
      </footer>
    </div>
  );
}
