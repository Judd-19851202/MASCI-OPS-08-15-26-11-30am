import React from "react";
import { Link, useLocation } from "react-router-dom";
import { CheckCircle2, ClipboardCheck } from "lucide-react";
import { Button } from "@/components/ui/button";
import { MasciLogo } from "@/components/MasciLogo";

export default function ThankYou() {
  const { state } = useLocation();
  const projectName = state?.projectName || "";
  const formType = state?.formType || "Inspection";
  const returnTo = state?.returnTo || "/submit";

  return (
    <div className="min-h-screen bg-slate-50 flex flex-col">
      <div className="caution-stripe" />
      <header className="bg-slate-900 border-b-4 border-red-700">
        <div className="max-w-3xl mx-auto px-5 sm:px-8 py-4 flex items-center justify-center">
          <MasciLogo variant="lockup" size="xl" className="hidden sm:block" homeLink="/" />
          <MasciLogo variant="mark" size="lg" className="sm:hidden" homeLink="/" />
        </div>
      </header>

      <main className="flex-1 flex items-center justify-center px-5 sm:px-8 py-12">
        <div
          className="max-w-xl w-full bg-white border-2 border-slate-300 rounded-md p-8 sm:p-12 text-center"
          data-testid="thank-you-card"
        >
          <div className="inline-flex items-center justify-center w-20 h-20 rounded-full bg-green-700 mb-6">
            <CheckCircle2 className="w-12 h-12 text-white" />
          </div>
          <span className="font-mono text-xs uppercase tracking-[0.25em] text-red-700 font-bold">
            {formType} Submitted
          </span>
          <h1 className="font-display text-3xl sm:text-4xl font-black tracking-tight text-slate-900 mt-2">
            Thank you.
          </h1>
          {projectName && (
            <p className="text-slate-700 text-base mt-3">
              Your {formType.toLowerCase()} for{" "}
              <span className="font-bold">{projectName}</span> has been recorded.
            </p>
          )}
          <p className="text-slate-600 text-sm mt-4 leading-relaxed">
            The MASCI safety team has been notified. Stay safe out there.
          </p>

          <div className="mt-8 grid grid-cols-1 sm:grid-cols-2 gap-3">
            <Button
              asChild
              className="h-12 bg-red-700 hover:bg-red-800 text-white font-bold uppercase tracking-wide border-b-2 border-red-900"
              data-testid="another-inspection-btn"
            >
              <Link to={returnTo}>
                <ClipboardCheck className="w-4 h-4 mr-2" />
                Submit Another
              </Link>
            </Button>
            <Button
              asChild
              variant="outline"
              className="h-12 border-2 border-slate-300 font-bold uppercase tracking-wide"
              data-testid="close-btn"
            >
              <a href="#" onClick={(e) => { e.preventDefault(); window.close(); }}>
                Close Window
              </a>
            </Button>
          </div>

          <div className="mt-10 pt-6 border-t-2 border-slate-100 font-mono text-[10px] uppercase tracking-[0.25em] text-red-700 font-bold flex items-center justify-center gap-3">
            <span>No Shortcuts</span>
            <span className="w-1 h-1 rounded-full bg-red-700" />
            <span>No Exceptions</span>
          </div>
        </div>
      </main>
    </div>
  );
}
