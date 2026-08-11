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
import { buildScopedPortalAuthHeaders } from "@/lib/authHeaders";
import { toast } from "sonner";
import FlAccountabilityWidget from "@/components/FlAccountabilityWidget";
import MyAssignedProjectsWidget from "@/components/team/MyAssignedProjectsWidget";
import OperationsActionsTile from "@/components/oa/OperationsActionsTile";
import {
  FIELD_LEADERSHIP_FORMS,
  SAFETY_EQUIPMENT_ISSUANCE_LINK,
} from "@/lib/fieldLeadershipSchemas";
import { sanitizeOperatorReference } from "@/lib/operatorLanguage";
import { clearAllSessions, redirectToPublicHome } from "@/lib/sessionReset";

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
      const r = await fetch(url, { headers: buildScopedPortalAuthHeaders(["fl"]) });
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
              <span className="font-semibold">{sanitizeOperatorReference(e.name, t("Crew member"))}</span>
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
  const safeUserName = sanitizeOperatorReference(user?.name, t("Field Leader"));
  const [dispatch, setDispatch] = useState({ items: [], window: null });
  const [driverQual, setDriverQual] = useState({ items: [], count: 0 });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const resolvedSubtitle = user?.role === "Cross-Portal Grant"
    ? t("Crew accountability · employee readiness · dispatch visibility")
    : user?.role || t("Crew accountability · employee readiness · dispatch visibility");

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

  const signOut = async () => {
    clearFlToken();
    toast.success(t("Signed out"));
    await clearAllSessions();
    redirectToPublicHome(navigate);
  };

  return (
    <PortalShell
      portalName="MASCI"
      portalRole={t("Field Leadership Portal")}
      pageTitle={safeUserName || t("Field Leader")}
      subtitle={resolvedSubtitle}
      showNotifications={false}
      onSignOut={signOut}
      authSessionGuard
    >
      <div className="max-w-6xl w-full mx-auto px-0 py-6 space-y-4" data-testid="fl-portal-dashboard">
        <section className="wp17-mission-banner" data-testid="fl-portal-mission-banner">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div>
              <div className="wp17-kicker text-white/70">{t("Today's focus")}</div>
              <h2 className="mt-2 font-display text-xl font-black text-white">{t("Support field leaders with the next crew-facing action, not admin noise.")}</h2>
              <p className="mt-2 max-w-3xl text-sm text-white/80">
                {t("See crew tasks, accountability, and dispatch updates clearly so the day keeps moving.")}
              </p>
            </div>
          </div>
        </section>

        {/* Track 19.53 · P2 #8 + #11 — Today's Focus banner.
           Aligns the Field Leadership / Superintendent dashboard with
           the Command Center standard's "Today Action Queue" section.
           No new backend · orders the existing widgets by urgency:
           assignments → dispatch window → driver readiness → workflows. */}
        <div
          data-testid="fl-portal-today-focus"
          className="rounded-md border-2 border-slate-200 bg-white px-4 py-3"
        >
          <div className="font-mono text-[11px] uppercase tracking-widest font-bold text-slate-700">
            {t("Today's focus · Field Leadership")}
          </div>
          <p className="mt-1 text-xs text-slate-600">
            {t("Assigned jobs, today's dispatch window, and driver-readiness readouts — in that order. Everything else is one click below.")}
          </p>
        </div>

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
            <div className="md:col-span-2 min-w-0">
              <MyAssignedProjectsWidget title={t("My assigned jobs (project roster)")} />
            </div>
            <Card className="min-w-0" data-testid="fl-card-dispatch">
              <CardHeader className="pb-2">
                <CardTitle className="text-sm flex flex-wrap items-center gap-1.5 min-w-0">
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
            <Card data-testid="fl-card-driver-qual" className="min-w-0 cursor-pointer hover:border-red-300 hover:shadow-sm transition-all" onClick={() => navigate("/field-leadership/portal/driver-qualification")}>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm flex flex-wrap items-center gap-1.5 min-w-0">
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
        <Card className="min-w-0">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm">{t("Operational workflows")}</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-xs text-slate-600 mb-3">
              {t("Use the same field workflows you already use every day. This role stays focused on field work and does not include HR, payroll, or system administration.")}
            </p>
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-x-8 gap-y-4">
              {[
                { label: t("Forecasting & Commitments"), to: "/field-leadership/portal/forecasting" },
                { label: t("Daily Reports"), to: "/daily/submit" },
                { label: t("Safety Meetings"), to: "/meetings/submit" },
                { label: t("JHAs"), to: "/jha" },
                { label: t("Pre-Ops / DVIRs"), to: "/equipment/submit" },
                { label: t("Incidents"), to: "/incidents/report" },
                { label: t("Field launchpad"), to: "/field" },
              ].map((w, index) => (
                <Button
                  key={w.to} variant="outline"
                  className="h-9 text-xs justify-start"
                  onClick={() => navigate(w.to)}
                  data-testid={`fl-operational-workflow-${index}`}
                >
                  {w.label}
                </Button>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* TRACK 14.0-DISCOVERABILITY-FINALIZATION · D-A16 — Leadership
            submission launchers. These were already present at the
            legacy /leadership hub but absent from the per-user FL
            Portal Dashboard. Forms are public-submit (no permission
            change) — additive launcher only. */}
        <Card className="min-w-0" data-testid="fl-leadership-launchers">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm flex flex-wrap items-center gap-1.5 min-w-0">
              <HardHat className="w-4 h-4 text-red-700" />
              {t("Leadership submissions")}
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-xs text-slate-600 mb-3">
              {t("Submit write-ups, recognitions, evaluations, and equipment checkouts directly from the field. These submissions append to the leadership ledger HR and admins use for accountability.")}
            </p>
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-x-8 gap-y-4">
              {/* TRACK 27.07 P0 · Derive launchers from the schema
                  single-source-of-truth so the FL Portal Dashboard can
                  never again silently omit a form (previously the
                  hard-coded list was missing employee_termination,
                  equipment_return, and time_off_request). */}
              {FIELD_LEADERSHIP_FORMS.map((f) => ({
                label: t(f.title.en),
                to: `/leadership/${f.kind}/new`,
                testid: `fl-launch-${f.kind}`,
                external: false,
              })).concat([{
                label: t(SAFETY_EQUIPMENT_ISSUANCE_LINK.title.en),
                to: SAFETY_EQUIPMENT_ISSUANCE_LINK.to,
                testid: `fl-launch-${SAFETY_EQUIPMENT_ISSUANCE_LINK.kind}`,
                external: true,
              }]).map((w) => (
                <Button
                  key={w.to}
                  variant="outline"
                  className="h-9 text-xs justify-start"
                  onClick={() => {
                    if (w.external) {
                      window.location.href = w.to;
                    } else {
                      navigate(w.to);
                    }
                  }}
                  data-testid={w.testid}
                >
                  {w.label}
                </Button>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* iter353d · Employee Accountability Lookup card */}
        <Card data-testid="fl-card-acct-lookup" className="min-w-0 mt-6 border-2 border-red-300">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm flex flex-wrap items-center gap-1.5 min-w-0">
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
