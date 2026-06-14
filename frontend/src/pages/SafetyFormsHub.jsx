import React, { useEffect } from "react";
import { Link, useNavigate } from "react-router-dom";
import {
  HardHat,
  GraduationCap,
  Plus,
  ShieldCheck,
} from "lucide-react";
import { PortalShell } from "@/design-system";
import SafetySideNavV2 from "@/components/safety/sidebar/SafetySideNavV2";
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
    <PortalShell
      portalName="MASCI"
      portalRole="Safety Portal · Safety Forms"
      pageTitle={t("Safety Forms")}
      subtitle={t("Issue equipment with full accountability and document use & care training — every submission emails a clean PDF to safety@mascigc.com.")}
      sideNav={<SafetySideNavV2 />}
      onSignOut={signOut}
    >
      <div className="max-w-6xl mx-auto px-5 sm:px-6 py-6" data-testid="safety-forms-hub-page">
        {/* iter322 · Portal continuity — if user arrived from FL with
            `?from=leadership`, show the back-to-FL banner. Zero
            footprint when no `?from=` is present. */}
        <PortalContextBanner currentLabel={t("You are viewing Safety Forms")} />
        <div className="mb-6 flex items-start gap-4">
          <div className="inline-flex items-center justify-center w-12 h-12 rounded-md bg-red-700 text-white shrink-0">
            <ShieldCheck className="w-6 h-6" />
          </div>
          <div className="flex-1">
            <span className="font-mono text-xs uppercase tracking-[0.22em] text-red-700 font-bold">
              {t("Safety Department")}
            </span>
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
      </div>
    </PortalShell>
  );
}
