import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { Loader2, HardHat, Truck, ShieldCheck, AlertTriangle, Search } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { PortalShell } from "@/design-system";
import { HelpTipBlock } from "@/components/HelpTip";
import { useT } from "@/lib/i18n";
import { api } from "@/lib/api";
import { getFlUser, clearFlToken, getFlToken } from "@/lib/flAuth";
import { toast } from "sonner";
import FlAccountabilityWidget from "@/components/FlAccountabilityWidget";
import MyAssignedProjectsWidget from "@/components/team/MyAssignedProjectsWidget";
import OperationsActionsTile from "@/components/oa/OperationsActionsTile";

// iter353d · inline lookup helper (queries the FL DQ endpoint to
// resolve a name → employee_id, then renders the mini-widget).
function FlAccountabilityLookup() {
  const { t } = useT();
  const [q, setQ] = useState("");
  const [results, setResults] = useState([]);
  const [picked, setPicked] = useState(null);
  const [searching, setSearching] = useState(false);
  const search = async () => {
    if (!q.trim()) return;
    setSearching(true);
    try {
      const url = `${process.env.REACT_APP_BACKEND_URL}/api/field-leadership/portal/driver-qualification?q=${encodeURIComponent(q.trim())}&limit=10`;
      const r = await fetch(url, { headers: { "X-FL-Token": getFlToken() || "" } });
      const d = await r.json();
      setResults((d.items || []).slice(0, 10));
    } catch (e) {
      toast.error(t("Search failed"));
    } finally {
      setSearching(false);
    }
  };
  return (
    <div className="space-y-2 min-w-0">
      <div className="flex gap-2 min-w-0">
        <Input
          value={q} onChange={(e) => setQ(e.target.value)}
          placeholder={t("Search by name or employee ID")}
          onKeyDown={(e) => e.key === "Enter" && search()}
          className="h-9 text-sm min-w-0 flex-1"
          data-testid="fl-lookup-input"
        />
        <Button onClick={search} disabled={searching || !q.trim()} size="sm" data-testid="fl-lookup-go" className="shrink-0">
          <Search className="w-3.5 h-3.5 mr-1" /> {searching ? t("…") : t("Search")}
        </Button>
      </div>
      {!picked && results.length > 0 ? (
        <div className="space-y-1" data-testid="fl-lookup-results">
          {results.map((e) => (
            <button
              key={e.id}
              type="button"
              onClick={() => setPicked(e)}
              className="w-full text-left flex items-center justify-between p-2 bg-slate-50 hover:bg-slate-100 border border-slate-200 rounded text-sm"
              data-testid={`fl-lookup-result-${e.id}`}
            >
              <span className="font-semibold">{e.name}</span>
              <span className="text-[10px] font-mono text-slate-500">{e.trade || ""}</span>
            </button>
          ))}
        </div>
      ) : null}
      {picked ? (
        <div data-testid="fl-lookup-widget-wrap">
          <FlAccountabilityWidget employeeId={picked.id} onClose={() => setPicked(null)} />
        </div>
      ) : null}
    </div>
  );
}

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
    <PortalShell
      portalName="MASCI"
      portalRole="Field Leadership Portal"
      pageTitle={user?.name || t("Field Leader")}
      subtitle={user?.role || t("Crew accountability · employee readiness · dispatch visibility")}
      onSignOut={signOut}
    >
      <div className="max-w-6xl w-full mx-auto px-4 py-6 space-y-4" data-testid="fl-portal-dashboard">
        <HelpTipBlock formKey="field-leadership.portal-dashboard" showCounter />
        <OperationsActionsTile />
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
            <div className="md:col-span-2">
              <MyAssignedProjectsWidget title="My assigned jobs (project roster)" />
            </div>
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
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-x-8 gap-y-4">
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

        {/* iter353d · Employee Accountability Lookup card */}
        <Card data-testid="fl-card-acct-lookup" className="mt-6 border-2 border-red-300">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm flex items-center gap-1.5">
              <ShieldCheck className="w-4 h-4 text-red-700" /> {t("Employee Accountability Lookup")}
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-xs text-slate-600 mb-2">
              {t("Look up any employee to see CDL/medical readiness, training currency, PPE, recent incidents, and the full accountability timeline.")}
            </p>
            <FlAccountabilityLookup />
          </CardContent>
        </Card>
      </div>
    </PortalShell>
  );
}
