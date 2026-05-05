import React, { useEffect } from "react";
import { Link, useNavigate } from "react-router-dom";
import {
  HardHat,
  GraduationCap,
  ArrowLeft,
  ArrowRight,
  Plus,
  ShieldCheck,
  LogOut,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { MasciLogo } from "@/components/MasciLogo";
import { LangToggle } from "@/components/LangToggle";
import { CompanyInfoDialog } from "@/components/CompanyInfoDialog";
import { isSafetyForms, clearSafetyFormsToken } from "@/lib/safetyFormsAuth";
import { useT } from "@/lib/i18n";

const FormTile = ({ to, icon: Icon, title, desc, ctaLabel, accent = "red", testId }) => {
  const accentCls =
    accent === "red"
      ? "border-red-700 bg-red-700"
      : accent === "amber"
      ? "border-amber-600 bg-amber-600"
      : "border-slate-800 bg-slate-800";
  return (
    <Link
      to={to}
      className="group relative bg-white border-2 border-slate-300 rounded-md p-6 sm:p-8 hover:border-red-700 hover:-translate-y-0.5 transition-all duration-150 flex flex-col"
      data-testid={testId}
    >
      <div className={`inline-flex items-center justify-center w-14 h-14 rounded-md ${accentCls} text-white mb-4`}>
        <Icon className="w-7 h-7" />
      </div>
      <h3 className="font-display text-2xl font-black tracking-tight text-slate-900">{title}</h3>
      <p className="text-slate-600 text-sm mt-2 flex-1 leading-relaxed">{desc}</p>
      <div className="mt-5 pt-4 border-t-2 border-slate-100 flex items-center justify-end">
        <div className="inline-flex items-center gap-2 font-mono text-xs uppercase tracking-[0.2em] font-bold text-red-700 group-hover:gap-3 transition-all">
          <Plus className="w-4 h-4" /> {ctaLabel}
          <ArrowRight className="w-3.5 h-3.5" />
        </div>
      </div>
    </Link>
  );
};

export default function SafetyFormsHub() {
  const { t } = useT();
  const navigate = useNavigate();

  useEffect(() => {
    if (!isSafetyForms()) {
      navigate("/safety/forms/login", { replace: true });
    }
  }, [navigate]);

  const signOut = () => {
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
          <MasciLogo variant="lockup" size="lg" className="hidden sm:block" homeLink="/" />
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

      <main className="max-w-6xl mx-auto px-5 sm:px-8 py-8 sm:py-12">
        <div className="mb-10 sm:mb-14 flex items-start gap-4">
          <div className="inline-flex items-center justify-center w-14 h-14 rounded-md bg-red-700 text-white shrink-0">
            <ShieldCheck className="w-7 h-7" />
          </div>
          <div className="flex-1">
            <span className="font-mono text-xs uppercase tracking-[0.25em] text-red-700 font-bold">
              {t("Safety Department")}
            </span>
            <h1 className="font-display text-4xl sm:text-5xl font-black tracking-tight text-slate-900 mt-1">
              {t("Safety Forms")}
            </h1>
            <p className="text-slate-600 text-base sm:text-lg mt-2 max-w-2xl">
              {t("Issue equipment with full accountability and document use & care training — every submission emails a clean PDF to safety@mascigc.com.")}
            </p>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 sm:gap-5 mb-12">
          <FormTile
            to="/safety/forms/equipment-issuance/new"
            icon={HardHat}
            title={t("Equipment Issuance")}
            desc={t("Issue safety equipment to employees with full chain of custody — itemized inventory, condition, photos, and dual signatures.")}
            ctaLabel={t("Start Form")}
            accent="red"
            testId="safety-forms-tile-issuance"
          />
          <FormTile
            to="/safety/forms/equipment-training/new"
            icon={GraduationCap}
            title={t("Use & Care Training")}
            desc={t("Document equipment training — initial, refresher, or retraining — with topics covered and instructor sign-off.")}
            ctaLabel={t("Start Form")}
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
