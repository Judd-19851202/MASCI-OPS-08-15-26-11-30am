import React from "react";
import { ChevronDown, ArrowRight, LogOut, LayoutDashboard } from "lucide-react";
import { Link } from "react-router-dom";
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";
import { AppIcon } from "@/components/icons/AppIcon";
import { useT } from "@/lib/i18n";
import { PORTAL_HOME, PORTAL_LABEL, authorizedPortals } from "@/lib/permissions";

export function WorkspaceSessionControl({ session, onSignOut }) {
  const { t } = useT();
  const workspaces = authorizedPortals().filter((portal) => PORTAL_HOME[portal]);
  const alternateWorkspaces = workspaces.filter((portal) => portal !== session.kind);

  return (
    <div className="flex flex-wrap items-center justify-end gap-2" data-testid="home-session-control">
      <Link
        to={session.to}
        className="inline-flex min-h-[40px] items-center gap-2 rounded-full border border-white/18 bg-white/12 px-3.5 text-[11px] font-mono font-bold uppercase tracking-[0.18em] text-white shadow-[0_10px_24px_rgba(15,23,42,0.18)] transition-[background-color,border-color,box-shadow] duration-150 hover:border-white/28 hover:bg-white/20"
        data-testid="hub-resume-link"
        title={t(`Open ${session.scopeLabel}`)}
      >
        <LayoutDashboard className="h-3.5 w-3.5" />
        {t("Resume")}
      </Link>

      <Popover>
        <PopoverTrigger asChild>
          <button
            type="button"
            className="inline-flex min-h-[40px] items-center gap-2 rounded-full border border-white/18 bg-white/12 px-3.5 text-[11px] font-mono font-bold uppercase tracking-[0.18em] text-white shadow-[0_10px_24px_rgba(15,23,42,0.18)] transition-[background-color,border-color,box-shadow] duration-150 hover:border-white/28 hover:bg-white/20"
            data-testid="home-session-control-trigger"
            aria-label={t("Signed-in session controls")}
          >
            <AppIcon name={session.kind} size="xs" tone="inverse" className="opacity-80" />
            <span className="max-w-[10rem] truncate">{session.name || t("Signed in")}</span>
            <ChevronDown className="h-3.5 w-3.5 opacity-70" />
          </button>
        </PopoverTrigger>

        <PopoverContent
          align="end"
          sideOffset={8}
          className="z-[220] w-[min(92vw,22rem)] rounded-[1.35rem] border border-slate-300/90 bg-white/98 p-3.5 text-slate-950 shadow-[0_24px_70px_rgba(15,23,42,0.28)] supports-[backdrop-filter]:bg-white/92 supports-[backdrop-filter]:backdrop-blur-xl"
          data-testid="home-session-control-menu"
        >
          <div className="space-y-3">
            <div className="rounded-[1.1rem] border border-slate-200 bg-slate-50 px-3 py-2.5">
              <div className="font-mono text-[10px] uppercase tracking-[0.18em] text-slate-500">
                {t("Signed in")}
              </div>
              <div className="mt-1 text-sm font-semibold text-slate-950">{session.name || t("Signed in")}</div>
              <div className="mt-1 text-xs text-slate-600">{t(session.scopeLabel)}</div>
            </div>

            {alternateWorkspaces.length > 0 ? (
              <div className="space-y-2" data-testid="home-session-control-switcher">
                <div className="font-mono text-[10px] uppercase tracking-[0.18em] text-slate-500">{t("Switch workspace")}</div>
                <div className="flex flex-wrap gap-2">
                  {alternateWorkspaces.map((portal) => (
                    <Link
                      key={portal}
                      to={PORTAL_HOME[portal]}
                      className="inline-flex min-h-[36px] items-center gap-1 rounded-full border border-slate-200 bg-slate-100 px-3 text-[11px] font-mono font-bold uppercase tracking-[0.15em] text-slate-700 transition-[background-color,border-color,color] duration-150 hover:border-slate-300 hover:bg-slate-200 hover:text-slate-950"
                      data-testid={`home-session-switch-${portal}`}
                    >
                      {t(PORTAL_LABEL[portal] || portal)}
                    </Link>
                  ))}
                </div>
              </div>
            ) : null}

            <div className="flex flex-wrap gap-2">
              <Link
                to={session.to}
                className="inline-flex min-h-[40px] flex-1 items-center justify-center gap-2 rounded-[0.9rem] border border-slate-900 bg-slate-900 px-3 text-xs font-semibold uppercase tracking-[0.12em] text-white transition-[background-color,border-color] duration-150 hover:bg-slate-800"
                data-testid="home-session-control-open"
              >
                {t("Open workspace")}
                <ArrowRight className="h-3.5 w-3.5" />
              </Link>
              <button
                type="button"
                onClick={onSignOut}
                className="inline-flex min-h-[40px] flex-1 items-center justify-center gap-2 rounded-[0.9rem] border border-rose-200 bg-rose-50 px-3 text-xs font-semibold uppercase tracking-[0.12em] text-rose-700 transition-[background-color,border-color,color] duration-150 hover:border-rose-300 hover:bg-rose-100 hover:text-rose-800"
                data-testid="home-session-control-signout"
              >
                <LogOut className="h-3.5 w-3.5" />
                {t("Sign out")}
              </button>
            </div>
          </div>
        </PopoverContent>
      </Popover>
    </div>
  );
}

export default WorkspaceSessionControl;