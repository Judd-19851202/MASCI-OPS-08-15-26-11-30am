import React, { useEffect, useState } from "react";
import { Link, useNavigate, useLocation } from "react-router-dom";
import {
  Plus,
  AlertOctagon,
  Eye,
  Trash2,
  Loader2,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { PortalShell } from "@/design-system";
import SafetySideNavV2 from "@/components/safety/sidebar/SafetySideNavV2";
import { ShareFormDialog } from "@/components/ShareFormDialog";
import JobFolderList from "@/components/JobFolderList";
import { api } from "@/lib/api";
import { formatDateLong } from "@/lib/utils";
import { toast } from "sonner";
import { SEVERITY_LEVELS } from "@/lib/incidentSchema";
// Track 13.6G — Deep-link triage banner (renders only when ?focus_capa is present).
import FocusBanner from "@/components/triage/FocusBanner";

const severityOf = (key) =>
  SEVERITY_LEVELS.find((s) => s.key === key) || SEVERITY_LEVELS[0];

export default function IncidentsDashboard() {
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [jobsMaster, setJobsMaster] = useState({}); // PROJECT-IDENTITY-004 canonical map
  const navigate = useNavigate();
  const { pathname } = useLocation();

  const load = async () => {
    setLoading(true);
    try {
      const [res, jm] = await Promise.all([
        api.get("/incidents"),
        api.get("/jobs-master").catch(() => ({ data: [] })),
      ]);
      setItems(res.data || []);
      const map = {};
      for (const j of (jm.data || [])) {
        const pn = (j.project_number || "").trim();
        if (pn) map[pn] = j.project_name || "";
      }
      setJobsMaster(map);
    } catch {
      toast.error("Could not load incidents");
    } finally {
      setLoading(false);
    }
  };
  useEffect(() => {
    load();
  }, []);

  const handleDelete = async (id, e) => {
    e.stopPropagation();
    if (!window.confirm("Delete this incident report? This cannot be undone."))
      return;
    try {
      await api.delete(`/incidents/${id}`);
      toast.success("Incident deleted");
      setItems((p) => p.filter((i) => i.id !== id));
    } catch (err) {
      const code = err?.response?.status;
      const detail = err?.response?.data?.detail;
      if (code === 401) {
        toast.error("Permission denied. Admin or PM sign-in required to delete incidents.");
      } else if (code === 404) {
        toast.error("Incident not found. It may already be deleted — refreshing.");
        setItems((p) => p.filter((i) => i.id !== id));
      } else if (code === 409) {
        const msg =
          (detail && typeof detail === "object" && detail.message) ||
          (typeof detail === "string" ? detail : null) ||
          "Cannot delete — linked corrective actions still reference this incident.";
        toast.error(msg);
      } else if (code >= 500) {
        toast.error("Server problem. Try again, or contact your administrator if it keeps failing.");
      } else {
        toast.error("Could not delete. Try again.");
      }
    }
  };

  return (
    <PortalShell
      portalName="MASCI" portalRole="Safety Portal · Incidents & Near Misses"
      pageTitle="Incidents & Near Misses"
      subtitle="Field-reported incidents · escalation tracking"
      primaryActions={
        <div className="flex items-center gap-2">
          <ShareFormDialog
            formType="incident"
            path="/near-miss"
            title="Share Incident Form"
            description="Anyone with this link can report a Near Miss on the public kiosk. No login required."
            testIdPrefix="share-incident"
          />
          <Button
            onClick={() => navigate("/incidents/report")}
            className="h-10 px-4 bg-red-700 hover:bg-red-800 text-white font-bold uppercase tracking-wide text-xs"
            data-testid="new-incident-btn"
          >
            <Plus className="w-4 h-4 mr-1" />
            <span className="hidden sm:inline">New Report</span>
            <span className="sm:hidden">New</span>
          </Button>
        </div>
      }
      sideNav={<SafetySideNavV2 />}
    >
    <div className="min-h-screen">
      <main className="max-w-6xl mx-auto px-5 sm:px-8 py-8 sm:py-12">
        <FocusBanner />
        <div className="mb-8">
          <span className="font-mono text-xs uppercase tracking-[0.25em] text-red-700">
            Accident / Incident Reports
          </span>
          <h1 className="font-display text-4xl sm:text-5xl font-black tracking-tight text-slate-900 mt-2">
            Report. Investigate. Prevent.
          </h1>
          <p className="text-slate-600 text-base sm:text-lg mt-3 max-w-2xl">
            Document every incident — from a near miss to a recordable injury —
            so we learn before it happens twice.
          </p>
        </div>

        <div className="bg-white border border-slate-200 rounded-md overflow-hidden">
          <div className="px-5 py-4 border-b-2 border-slate-200 flex items-center justify-between">
            <h2 className="font-display text-xl font-bold">Recent Reports</h2>
            {!loading && (
              <span className="font-mono text-xs uppercase tracking-[0.2em] text-slate-500">
                {items.length} on file
              </span>
            )}
          </div>
          {loading ? (
            <div className="p-12 flex items-center justify-center text-slate-500">
              <Loader2 className="w-6 h-6 animate-spin mr-2" /> Loading...
            </div>
          ) : items.length === 0 ? (
            <div className="p-10 sm:p-16 text-center" data-testid="empty-state">
              <div className="inline-flex items-center justify-center w-16 h-16 rounded-md bg-red-700 mb-5">
                <AlertOctagon className="w-8 h-8 text-white" />
              </div>
              <h3 className="font-display text-2xl font-bold text-slate-900">
                Nothing filed yet today.
              </h3>
              <p className="text-slate-600 mt-2 max-w-md mx-auto">
                Every near miss, injury, property damage, or environmental release belongs here. Small details written now save big problems later.
              </p>
              <Button
                onClick={() => navigate("/incidents/report")}
                className="mt-6 h-12 px-6 bg-red-700 hover:bg-red-800 text-white font-bold uppercase tracking-wide"
                data-testid="empty-cta"
              >
                <Plus className="w-5 h-5 mr-2" /> Report First Incident
              </Button>
            </div>
          ) : (
            <JobFolderList
              items={items}
              dateField="incident_date"
              testIdPrefix="incident-folders"
              jobsMaster={jobsMaster}
              renderItem={(it) => {
                const sev = severityOf(it.severity);
                return (
                  <div
                    onClick={() => navigate(`${pathname}/${it.id}`, {
                      state: {
                        from: {
                          key: pathname.startsWith("/pm/") ? "pm-incidents" : "admin-incidents",
                          label: "Incidents",
                          path: pathname,
                        },
                      },
                    })}
                    className="p-4 sm:p-5 hover:bg-red-50 cursor-pointer transition-colors duration-150 flex flex-col sm:flex-row sm:items-center gap-3"
                    data-testid={`incident-row-${it.id}`}
                  >
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 flex-wrap">
                        <span
                          className={`inline-flex items-center px-2 py-0.5 ${sev.color} text-white text-[10px] font-mono uppercase tracking-wider rounded font-bold`}
                          data-testid={`severity-badge-${it.id}`}
                        >
                          {sev.label}
                        </span>
                        {it.osha_recordable === "Yes" && (
                          <span className="inline-flex items-center px-2 py-0.5 bg-red-900 text-white text-[10px] font-mono uppercase tracking-wider rounded">
                            OSHA Recordable
                          </span>
                        )}
                        <span className="font-display text-lg font-bold text-slate-900 truncate">
                          {it.incident_type || "Incident"}
                        </span>
                      </div>
                      <div className="text-sm text-slate-600 mt-1">
                        {(jobsMaster[((it.project_number || "").trim())] || it.project_name || "—")}
                        {it.person_name ? ` · Involved: ${it.person_name}` : ""}
                      </div>
                      <div className="font-mono text-[11px] uppercase tracking-wider text-slate-500 mt-1">
                        {formatDateLong(it.incident_date)} · Reported by{" "}
                        {it.reported_by || "—"}
                      </div>
                    </div>
                    <div className="flex gap-2">
                      <Link
                        to={`${pathname}/${it.id}`}
                        state={{
                          from: {
                            key: pathname.startsWith("/pm/") ? "pm-incidents" : "admin-incidents",
                            label: "Incidents",
                            path: pathname,
                          },
                        }}
                        onClick={(e) => e.stopPropagation()}
                        className="inline-flex items-center justify-center h-10 px-4 rounded-md bg-slate-900 hover:bg-slate-800 text-white font-bold text-sm uppercase tracking-wide"
                        data-testid={`view-${it.id}`}
                      >
                        <Eye className="w-4 h-4 mr-1" /> View
                      </Link>
                      <Button
                        variant="outline"
                        size="icon"
                        className="h-10 w-10 border-2 border-slate-300 hover:border-red-500 hover:text-red-600"
                        onClick={(e) => handleDelete(it.id, e)}
                        data-testid={`delete-${it.id}`}
                        aria-label="Delete incident report"
                        title="Delete"
                      >
                        <Trash2 className="w-4 h-4" />
                      </Button>
                    </div>
                  </div>
                );
              }}
            />
          )}
        </div>
      </main>
    </div>
    </PortalShell>
  );
}
