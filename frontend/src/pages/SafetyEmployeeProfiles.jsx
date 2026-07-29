// SafetyEmployeeProfiles — Phase 4 employee safety roll-up.
// List view = every employee in db.employees with a "View Profile"
// drill-down. Profile = trainings, certs, meeting attendance count,
// incident involvement count, PPE issuance count, open CAs assigned.
import React, { useEffect, useMemo, useState } from "react";
import axios from "axios";
import {
  Users, Loader2, AlertTriangle, Award, ClipboardCheck,
  Wrench, AlertOctagon, ArrowLeft, Filter, FileText,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import SafetyShell from "@/components/SafetyShell";
import { EmptyState, LoadingState } from "@/components/ui/PortalStates";
import WhereUsedPanel from "@/components/WhereUsedPanel";
import AssetHistoryTimeline from "@/components/AssetHistoryTimeline";
import { Link } from "react-router-dom";
import { ExternalLink } from "lucide-react";
import { buildScopedPortalAuthHeaders } from "@/lib/authHeaders";
import { useT } from "@/lib/i18n";
import { toast } from "sonner";

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;
const auth = () => ({ headers: buildScopedPortalAuthHeaders(["safety"]) });

const inputCls = "h-10 text-sm border-2 border-slate-300 focus-visible:ring-2 focus-visible:ring-cyan-700";

function KPI({ icon: Icon, label, value, color = "cyan" }) {
  const colors = {
    cyan:    "border-cyan-700 text-cyan-900 bg-white",
    red:     "border-red-700 text-red-900 bg-red-50",
    amber:   "border-amber-600 text-amber-900 bg-amber-50",
    emerald: "border-emerald-700 text-emerald-900 bg-white",
    slate:   "border-slate-500 text-slate-800 bg-white",
  };
  return (
    <div className={`border-2 ${colors[color]} rounded-md p-4`}>
      <div className="flex items-start justify-between gap-2">
        <div>
          <div className="font-mono text-[10px] uppercase tracking-[0.18em] text-slate-600">{label}</div>
          <div className="font-display text-2xl font-black mt-1 leading-none">{value}</div>
        </div>
        <Icon className="w-5 h-5 text-slate-400 mt-0.5" />
      </div>
    </div>
  );
}

export default function SafetyEmployeeProfiles() {
  const { t } = useT();
  const [employees, setEmployees] = useState([]);
  const [search, setSearch] = useState("");
  const [loading, setLoading] = useState(true);
  const [selected, setSelected] = useState(null); // employee id
  const [profile, setProfile] = useState(null);
  const [profileLoading, setProfileLoading] = useState(false);

  useEffect(() => {
    (async () => {
      try {
        const r = await axios.get(`${API}/employees`);
        setEmployees(r.data?.items || []);
      } catch {
        toast.error("Could not load employees");
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  const filtered = useMemo(() => {
    if (!search.trim()) return employees;
    const s = search.trim().toLowerCase();
    return employees.filter((e) =>
      (e.name || "").toLowerCase().includes(s)
      || (e.trade || "").toLowerCase().includes(s)
      || (e.crew || "").toLowerCase().includes(s),
    );
  }, [employees, search]);

  const openProfile = async (emp) => {
    setSelected(emp.id);
    setProfile(null);
    setProfileLoading(true);
    try {
      const r = await axios.get(`${API}/safety/employee-profile/${emp.id}`, auth());
      setProfile(r.data);
    } catch (err) {
      toast.error(err?.response?.data?.detail || "Could not load profile");
    } finally {
      setProfileLoading(false);
    }
  };

  if (selected) {
    return (
      <SafetyShell title="Employee Safety Profile" kicker="SAFETY · EMPLOYEE PROFILE">
        <div className="flex flex-wrap items-center gap-2 mb-4">
          <Button variant="outline" onClick={() => { setSelected(null); setProfile(null); }} data-testid="safety-emp-back">
            <ArrowLeft className="w-4 h-4 mr-1" /> {t("Back to employee list")}
          </Button>
          {/* iter353c · cross-portal entry into the unified accountability timeline.
              Safety token already in localStorage; the timeline page accepts it. */}
          <Link
            to={`/hr/employees/${selected}/accountability`}
            className="inline-flex items-center gap-1.5 px-3 py-2 border-2 border-cyan-700 bg-cyan-50 hover:bg-cyan-100 text-cyan-900 rounded text-xs font-mono uppercase tracking-wider"
            data-testid="safety-emp-accountability-link"
          >
            <FileText className="w-3.5 h-3.5" /> {t("Employee Accountability Timeline")}
          </Link>
        </div>
        {profileLoading || !profile ? (
          <div className="text-center py-12"><Loader2 className="w-6 h-6 animate-spin mx-auto text-slate-400" /></div>
        ) : (
          <>
            <div className="bg-white border border-slate-200 rounded-md p-5 mb-6">
              <div className="font-mono text-[10px] uppercase tracking-[0.2em] text-cyan-700 font-bold">{t("Employee")}</div>
              <h2 className="font-display text-3xl font-black text-slate-900 mt-1">{profile.employee?.name}</h2>
              <div className="flex flex-wrap gap-x-4 gap-y-1 text-sm text-slate-600 mt-2">
                {profile.employee?.trade && <span><strong>{t("Trade")}:</strong> {profile.employee.trade}</span>}
                {profile.employee?.role && <span><strong>{t("Role")}:</strong> {profile.employee.role}</span>}
                {profile.employee?.crew && <span><strong>{t("Crew")}:</strong> {profile.employee.crew}</span>}
                {profile.employee?.employee_id && <span><strong>{t("Emp ID")}:</strong> {profile.employee.employee_id}</span>}
              </div>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-x-6 gap-y-3 mb-6">
              <KPI icon={Award} label={t("Trainings on file")} value={profile.training_summary?.total ?? 0} />
              <KPI icon={AlertTriangle} label={t("Trainings expired")} value={profile.training_summary?.expired ?? 0} color="red" />
              <KPI icon={AlertTriangle} label={t("Expiring 30 days")} value={profile.training_summary?.expiring_within_30_days ?? 0} color="amber" />
              <KPI icon={AlertOctagon} label={t("Open CAs (assigned)")} value={profile.open_corrective_actions ?? 0} color="amber" />
              <KPI icon={ClipboardCheck} label={t("Meetings attended")} value={profile.meetings_attended ?? 0} color="emerald" />
              <KPI icon={AlertTriangle} label={t("Incident involvement")} value={profile.incident_involvements ?? 0} color="slate" />
              <KPI icon={Wrench} label={t("PPE issuance count")} value={profile.ppe_issuance_count ?? 0} color="slate" />
            </div>

            <h3 className="font-display text-xl font-black mb-3">{t("Training & Certifications")}</h3>
            {(profile.trainings || []).length === 0 ? (
              <div className="text-center text-slate-500 py-8 border-2 border-dashed border-slate-200 rounded-md">{t("No training records on file yet.")}</div>
            ) : (
              <div className="overflow-x-auto" data-testid="safety-emp-training-list">
                <table className="w-full text-sm">
                  <thead className="bg-slate-100 text-slate-700 text-xs uppercase tracking-[0.15em] font-mono">
                    <tr>
                      <th className="text-left px-3 py-2">Training</th>
                      <th className="text-left px-3 py-2">Type</th>
                      <th className="text-left px-3 py-2">Completed</th>
                      <th className="text-left px-3 py-2">Expires</th>
                      <th className="text-left px-3 py-2">Issued By</th>
                    </tr>
                  </thead>
                  <tbody>
                    {profile.trainings.map((r) => (
                      <tr key={r.id} className="border-t border-slate-100">
                        <td className="px-3 py-2 font-semibold">{r.training_name}</td>
                        <td className="px-3 py-2 text-slate-600 text-xs font-mono">{r.certification_type || "—"}</td>
                        <td className="px-3 py-2">{r.completed_date || "—"}</td>
                        <td className="px-3 py-2">{r.expiration_date || <span className="text-slate-400">—</span>}</td>
                        <td className="px-3 py-2 text-slate-600">{r.issued_by || "—"}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}

            {/* iter140 — Cross-portal footprint (incidents, CAs, training) */}
            <div className="mt-6">
              <WhereUsedPanel kind="employee" masterId={selected} />
            </div>

            {/* iter141 — Chronological history timeline (compact) */}
            <div className="mt-4">
              <div className="flex items-center justify-end mb-2">
                <Link
                  to={`/admin/employees/${selected}/history`}
                  className="text-xs font-mono uppercase tracking-[0.15em] text-cyan-800 hover:underline flex items-center gap-1"
                  data-testid="safety-emp-history-fullpage-link"
                >
                  {t("Open full history")} <ExternalLink className="w-3 h-3" />
                </Link>
              </div>
              <AssetHistoryTimeline kind="employee" masterId={selected} compact limit={10} />
            </div>
          </>
        )}
      </SafetyShell>
    );
  }

  return (
    <SafetyShell title="Employee Safety Profiles" kicker="SAFETY · EMPLOYEE PROFILES">
      <p className="text-slate-600 text-sm max-w-2xl leading-relaxed mb-5">
        {t("Pick any MASCI employee to see their full safety roll-up: training & certs, meeting attendance, incident involvement, PPE issuance, and open corrective actions assigned.")}
      </p>
      <div className="flex items-center gap-2 mb-4">
        <Filter className="w-4 h-4 text-slate-500" />
        <Input placeholder={t("Search by name, trade, crew…")} value={search} onChange={(e) => setSearch(e.target.value)} className={`${inputCls} max-w-md`} data-testid="safety-emp-search" />
      </div>
      {loading ? (
        <LoadingState label={t("Loading…")} testId="safety-emp-loading" />
      ) : filtered.length === 0 ? (
        <EmptyState
          icon={Users}
          title={t("No employees match")}
          body={t("Try a different search term.")}
          testId="safety-emp-empty"
        />
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3" data-testid="safety-emp-list">
          {filtered.map((emp) => (
            <button
              key={emp.id}
              onClick={() => openProfile(emp)}
              className="text-left bg-white border border-slate-200 border-l-4 border-l-cyan-600 hover:shadow-md hover:border-slate-300 rounded-md p-4 transition-all"
              data-testid={`safety-emp-card-${emp.id}`}
            >
              <div className="font-display text-lg font-black text-slate-900">{emp.name}</div>
              <div className="text-xs text-slate-500 mt-1 font-mono uppercase tracking-[0.15em]">
                {emp.trade || "—"}{emp.crew ? ` · ${emp.crew}` : ""}
              </div>
              {emp.employee_id && <div className="text-[11px] text-slate-400 mt-1 font-mono">ID: {emp.employee_id}</div>}
            </button>
          ))}
        </div>
      )}
    </SafetyShell>
  );
}
