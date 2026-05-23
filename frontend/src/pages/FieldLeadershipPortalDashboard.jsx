import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { Loader2, LogOut, HardHat, Truck, ShieldCheck, AlertTriangle } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { MasciLogo } from "@/components/MasciLogo";
import { ForgedOpsAttribution } from "@/components/ForgedOpsAttribution";
import { LangToggle } from "@/components/LangToggle";
import { HelpTipBlock } from "@/components/HelpTip";
import { useT } from "@/lib/i18n";
import { api } from "@/lib/api";
import { getFlUser, clearFlToken } from "@/lib/flAuth";
import { toast } from "sonner";

/**
 * Field Leadership Portal Dashboard (iter314)
 *
 * Bounded operational entry point. Surfaces the three approved
 * read-only operational widgets — dispatch (today/tomorrow), driver
 * qualification, and a sign-out button. Workflow links to existing
 * field surfaces (Daily Reports, Safety Meetings, JHAs, Pre-Ops,
 * Incidents) are presented but NOT reimplemented — they reuse the
 * already-shipped routes that the FL token now also authorizes.
 *
 * Distinct from the legacy field-leadership document viewer.
 */
export default function FieldLeadershipPortalDashboard() {
  const { t } = useT();
  const navigate = useNavigate();
  const user = getFlUser();
  const [dispatch, setDispatch] = useState({ items: [], window: null });
  const [driverQual, setDriverQual] = useState({ items: [], count: 0 });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    (async () => {
      setLoading(true);
      try {
        const [d, q] = await Promise.all([
          api.get("/field-leadership/portal/dispatch-today"),
          api.get("/field-leadership/portal/driver-qualification?limit=200"),
        ]);
        setDispatch({ items: d.data?.items || [], window: d.data?.window || null });
        setDriverQual({ items: q.data?.items || [], count: q.data?.count || 0 });
      } catch (err) {
        console.error("[fl-portal] dashboard load failed:", err);
        setError(err?.response?.data?.detail || t("Could not load dashboard"));
      } finally {
        setLoading(false);
      }
    })();
  }, [t]);

  const signOut = () => {
    clearFlToken();
    toast.success(t("Signed out"));
    navigate("/field-leadership/portal/login", { replace: true });
  };

  return (
    <div className="min-h-screen bg-slate-50 flex flex-col" data-testid="fl-portal-dashboard">
      <div className="bg-white border-b border-slate-200 px-4 py-3">
        <div className="max-w-6xl mx-auto flex items-center justify-between">
          <div className="flex items-center gap-3">
            <MasciLogo size={32} />
            <div>
              <div className="text-xs uppercase tracking-[0.18em] font-bold text-slate-600 flex items-center gap-1">
                <HardHat className="w-3 h-3" /> {t("Field Leadership Portal")}
              </div>
              <div className="text-sm font-semibold text-slate-900">
                {user?.name || t("Field Leader")} · <span className="text-slate-500 text-xs">{user?.role || ""}</span>
              </div>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <LangToggle />
            <Button size="sm" variant="outline" onClick={signOut} data-testid="fl-signout" className="h-8 text-xs">
              <LogOut className="w-3 h-3 mr-1" /> {t("Sign out")}
            </Button>
          </div>
        </div>
      </div>
      <div className="flex-1 max-w-6xl w-full mx-auto px-4 py-6 space-y-4">
        <HelpTipBlock formKey="field-leadership.portal-dashboard" showCounter />
        {error && (
          <div className="bg-rose-50 border border-rose-200 text-rose-700 text-sm rounded p-3 flex items-center gap-2">
            <AlertTriangle className="w-4 h-4" /> {error}
          </div>
        )}
        {loading ? (
          <div className="flex items-center justify-center py-10 text-slate-500">
            <Loader2 className="w-5 h-5 mr-2 animate-spin" /> {t("Loading…")}
          </div>
        ) : (
          <div className="grid md:grid-cols-2 gap-4">
            <Card data-testid="fl-card-dispatch">
              <CardHeader className="pb-2">
                <CardTitle className="text-sm flex items-center gap-1.5">
                  <Truck className="w-4 h-4 text-slate-600" /> {t("Dispatch · Today / Tomorrow")}
                </CardTitle>
              </CardHeader>
              <CardContent>
                <HelpTipBlock formKey="field-leadership.dispatch-visibility" />
                <div className="text-xs text-slate-500 mb-2">
                  {dispatch.window
                    ? `${dispatch.window.today} → ${dispatch.window.tomorrow}`
                    : t("Read-only window")}
                </div>
                <div className="text-3xl font-bold text-slate-900">
                  {dispatch.items.length}
                </div>
                <div className="text-xs text-slate-600 mt-1">
                  {t("dispatch entries visible to Field Leadership")}
                </div>
              </CardContent>
            </Card>
            <Card data-testid="fl-card-driver-qual" className="cursor-pointer hover:border-red-300 hover:shadow-sm transition-all" onClick={() => navigate("/field-leadership/portal/driver-qualification")}>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm flex items-center gap-1.5">
                  <ShieldCheck className="w-4 h-4 text-slate-600" /> {t("Driver Qualification")}
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-xs text-slate-500 mb-2">{t("Read-only roster")}</div>
                <div className="text-3xl font-bold text-slate-900">
                  {driverQual.count}
                </div>
                <div className="text-xs text-slate-600 mt-1">
                  {t("approved/CDL drivers in scope")}
                </div>
                <div className="text-[11px] text-red-700 font-mono uppercase tracking-wider mt-2" data-testid="fl-card-driver-qual-cta">
                  {t("Open Driver Readiness →")}
                </div>
              </CardContent>
            </Card>
          </div>
        )}
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm">{t("Operational workflows")}</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-xs text-slate-600 mb-3">
              {t("You have access to the same field workflows you use on a daily basis. Field Leadership identity does NOT include HR administration, payroll, system settings, or platform configuration.")}
            </p>
            <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
              {[
                { label: t("Daily Reports"), to: "/daily-reports" },
                { label: t("Safety Meetings"), to: "/meetings" },
                { label: t("JHAs"), to: "/jhas" },
                { label: t("Pre-Ops / DVIRs"), to: "/equipment" },
                { label: t("Incidents"), to: "/safety/incident-report" },
                { label: t("Fleet visibility"), to: "/fleet" },
              ].map((w) => (
                <Button
                  key={w.to} variant="outline"
                  className="h-9 text-xs justify-start"
                  onClick={() => navigate(w.to)}
                >
                  {w.label}
                </Button>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>
      <ForgedOpsAttribution />
    </div>
  );
}
