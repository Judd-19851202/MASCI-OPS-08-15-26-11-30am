import React from "react";
import { Printer } from "lucide-react";
import { Button } from "@/components/ui/button";
import { PrintWatermark } from "@/components/PrintWatermark";
import { OperationalTopbar } from "@/components/public/OperationalPageFrame";
import { OperationalStatusBadge } from "@/components/public/OperationalStatusBadge";
import { useHubHome } from "@/components/HubBackLink";
import { printReport } from "@/lib/printReport";

export function OperationalPrintPageFrame({
  testId = "operational-print-page",
  accent = "red",
  backTo,
  backLabel,
  familyLabel = "MASCI Operations Platform",
  familyMeta = "Printable field guide",
  kicker,
  title,
  description,
  heroIcon: HeroIcon = null,
  heroMeta = null,
  printLabel = "Print",
  footerText = "MASCI Operations Platform · Printable field guide",
  children,
}) {
  const homeTo = useHubHome();

  return (
    <div className="min-h-screen wp17-public-shell print:bg-white" data-testid={testId}>
      <PrintWatermark />
      <div className="caution-stripe no-print" />

      <div className="no-print" data-testid={`${testId}-chrome`}>
        <OperationalTopbar
          backTo={backTo}
          backLabel={backLabel}
          accent={accent}
          familyLabel={familyLabel}
          familyMeta={familyMeta}
          homeTo={homeTo}
          showHomeLink
          showLangToggle
          testIdPrefix={testId}
          rightSlot={(
            <Button
              onClick={printReport}
              className="h-10 rounded-full bg-white/12 px-4 text-[11px] font-mono font-bold uppercase tracking-[0.18em] text-white hover:bg-white/18"
              data-testid={`${testId}-print-button`}
            >
              <Printer className="mr-1.5 h-3.5 w-3.5" />
              {printLabel}
            </Button>
          )}
        />

        <main className="wp17-public-main pb-0">
          <div className="max-w-5xl mx-auto space-y-6">
            <section className="wp17-public-hero relative overflow-hidden" data-testid={`${testId}-hero`}>
              <div className="pointer-events-none absolute right-0 top-0 h-40 w-40 rounded-full bg-white/55 blur-3xl" />
              <div className="relative flex flex-col gap-5 lg:flex-row lg:items-start lg:justify-between">
                <div className="min-w-0 flex-1">
                  {HeroIcon ? (
                    <div className="inline-flex h-14 w-14 items-center justify-center rounded-2xl bg-red-700/10 text-red-700 shadow-[0_16px_32px_rgba(15,23,42,0.10)]" data-testid={`${testId}-hero-icon`}>
                      <HeroIcon className="h-7 w-7" />
                    </div>
                  ) : null}
                  {kicker ? <div className="wp17-kicker mt-4">{kicker}</div> : null}
                  {title ? <h1 className="font-display text-4xl sm:text-5xl lg:text-6xl font-black leading-[0.95] tracking-[-0.04em] text-slate-900 mt-2">{title}</h1> : null}
                  {description ? <p className="mt-3 max-w-3xl text-sm sm:text-base leading-6 text-slate-700">{description}</p> : null}
                </div>
                <div className="w-full lg:max-w-sm space-y-3" data-testid={`${testId}-hero-aside`}>
                  <div className="rounded-[1.5rem] border border-slate-900/70 bg-slate-950 px-5 py-5 text-white shadow-[0_24px_60px_rgba(15,23,42,0.22)]">
                    <div className="font-mono text-[10px] uppercase tracking-[0.22em] text-white/55">Print workflow</div>
                    <div className="mt-2 text-lg font-semibold leading-tight">One clean handout. One consistent shell.</div>
                    <p className="mt-2 text-sm leading-6 text-white/74">Preview the sheet, then print or save to PDF from the same operational surface crews already recognize.</p>
                  </div>
                  {heroMeta ? <div className="flex flex-wrap gap-2">{heroMeta}</div> : null}
                  <OperationalStatusBadge tone="amber" testId={`${testId}-print-ready-badge`}>Print-ready layout</OperationalStatusBadge>
                </div>
              </div>
            </section>
          </div>
        </main>
      </div>

      <main className="max-w-5xl mx-auto px-5 sm:px-8 py-8 print:p-0">
        {children}
        <footer className="no-print pt-6 text-center font-mono text-[10px] uppercase tracking-[0.2em] text-slate-400" data-testid={`${testId}-footer`}>
          {footerText}
        </footer>
      </main>

      <style>{`
        @media print {
          @page { size: letter; margin: 0.4in; }
          body { -webkit-print-color-adjust: exact; print-color-adjust: exact; }
          .no-print, .no-print * { display: none !important; }
        }
      `}</style>
    </div>
  );
}

export default OperationalPrintPageFrame;