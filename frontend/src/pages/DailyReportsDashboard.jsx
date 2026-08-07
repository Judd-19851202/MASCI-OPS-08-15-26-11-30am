import React, { useEffect, useMemo, useState } from "react";
import { Link, useNavigate, useLocation } from "react-router-dom";
import {
  Plus,
  ClipboardList,
  Eye,
  Trash2,
  Loader2,
  CloudSun,
  Camera,
  Users,
  Building2,
  UserRound,
  ArrowRight,
  ShieldAlert,
  Waypoints,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { PortalShell } from "@/design-system";
import AdminBreadcrumb from "@/components/admin/AdminBreadcrumb";
import { renderAdminRouteSideNav } from "@/components/admin/AdminRouteShell";
import PmSideNavV2 from "@/components/pm/sidebar/SideNavV2";
import { ShareFormDialog } from "@/components/ShareFormDialog";
import JobFolderList from "@/components/JobFolderList";
import { useT } from "@/lib/i18n";
import { api } from "@/lib/api";
import { formatDateLong } from "@/lib/utils";
import { toast } from "sonner";
import { InformationCard } from "@/components/CanonicalCard";
import { SectionHeading } from "@/components/SectionHeading";
import EmptyState from "@/components/EmptyState";
import { OperationalCoachingStrip } from "@/components/OperationalCoachingStrip";
import { Input } from "@/components/ui/input";
import { formatOperatorJobLabel, sanitizeOperatorProjectNumber } from "@/lib/operatorLanguage";

export default function DailyReportsDashboard() {
  const { t } = useT();
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [jobsMaster, setJobsMaster] = useState({});  // DR-JOB-002 canonical map
  const [searchQuery, setSearchQuery] = useState("");
  const navigate = useNavigate();
  const { pathname } = useLocation();
  const isAdminRoute = pathname.startsWith("/admin/");
  // DR-JOB-003 admin opt-in for cert/test pollution tier
  const showCert = typeof window !== "undefined" && new URLSearchParams(window.location.search).get("show") === "cert";
  const dailyReportDetailBase = pathname.startsWith("/pm/")
    ? "/pm/daily"
    : pathname.startsWith("/admin/")
      ? "/admin/daily"
      : "/pm/daily";
  const shellActions = (
    <div className="flex items-center gap-2">
      <ShareFormDialog
        formType="daily-report"
        path="/daily/submit"
        title={t("Share Daily Report Form")}
        description={t("Anyone with this link can fill out a Daily Job Report from the field.")}
        testIdPrefix="share-daily"
      />
      <Button
        onClick={() => navigate("/daily/submit")}
        size="sm"
        data-testid="new-daily-btn"
      >
        <Plus className="w-4 h-4 mr-1" />
        <span className="hidden sm:inline">{t("New Report")}</span>
        <span className="sm:hidden">{t("New")}</span>
      </Button>
    </div>
  );

  const load = async () => {
    setLoading(true);
    try {
      const [res, jm] = await Promise.all([
        api.get("/daily-reports"),
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
      toast.error("Could not load daily reports. Try again.");
    } finally {
      setLoading(false);
    }
  };
  useEffect(() => {
    load();
  }, []);

  const handleDelete = async (id, e) => {
    e.stopPropagation();
    if (!window.confirm("Delete this daily report? This cannot be undone."))
      return;
    try {
      await api.delete(`/daily-reports/${id}`);
      toast.success("Deleted.");
      setItems((p) => p.filter((i) => i.id !== id));
    } catch {
      toast.error("Could not delete. Try again.");
    }
  };

  const coachingBlocks = [
    {
      icon: Waypoints,
      tone: "amber",
      label: t("Why this review matters"),
      body: t("This list is the office routing surface for labor, weather, deliveries, visitors, photos, and job-level follow-up."),
      testId: "daily-reports-coaching-why",
    },
    {
      icon: Eye,
      tone: "sky",
      label: t("Who reviews it"),
      body: t("Project Management, Administration, and downstream operations teams use the same shared record to verify what happened on site."),
      testId: "daily-reports-coaching-who",
    },
    {
      icon: ArrowRight,
      tone: "emerald",
      label: t("What happens next"),
      body: t("Open the detail view to review the field narrative, adjust project tagging if needed, and move the report into office review."),
      testId: "daily-reports-coaching-next",
    },
    {
      icon: ShieldAlert,
      tone: "slate",
      label: t("When to stop and call"),
      body: t("If safety events, injuries, delivery failures, or document evidence look incomplete, stop the workflow and escalate before the record moves downstream."),
      testId: "daily-reports-coaching-escalate",
    },
  ];

  const filteredItems = useMemo(() => {
    const query = searchQuery.trim().toLowerCase();
    if (!query) return items;
    return items.filter((item) => {
      const haystack = [
        item.project_name,
        item.project_number,
        item.prepared_by,
        item.report_date,
        item.location,
      ]
        .filter(Boolean)
        .join(" ")
        .toLowerCase();
      return haystack.includes(query);
    });
  }, [items, searchQuery]);

  return (
    <PortalShell
      portalName="MASCI" portalRole={isAdminRoute ? "Administration" : "Project Management"}
      pageTitle={t("Daily Reports")}
      showPageHeader={false}
      sideNav={isAdminRoute ? renderAdminRouteSideNav() : <PmSideNavV2 />}
    >
    <div className="min-h-screen">
      <main className="max-w-6xl mx-auto px-5 sm:px-8 py-8 sm:py-12">
        <div className="mb-5 flex flex-wrap items-center justify-end gap-2" data-testid="daily-reports-page-actions">
          {shellActions}
        </div>
        {pathname.startsWith("/admin/") ? (
          <AdminBreadcrumb crumbs={[
            { label: t("Field Operations") },
            { label: "Daily Reports" },
          ]} />
        ) : null}
        <InformationCard
          icon={ClipboardList}
          tone="red"
          eyebrow={t("Field review")}
          title={t("Today's site activity, captured.")}
          description={t("Crews, subs, visitors, equipment, materials, weather, and photos in one unified operational review surface.")}
          testId="daily-reports-summary"
          className="mb-8"
        />

        <OperationalCoachingStrip
          blocks={coachingBlocks}
          testId="daily-reports-coaching-strip"
          className="mb-8"
        />

        <SectionHeading
          index="01"
          title={t("Recent reports")}
          subtitle={t("Open the latest field records fast, review the crew activity, and route the next action from one consistent list.")}
          testId="daily-reports-list-heading"
        />

        <Card className="overflow-hidden">
          <CardHeader className="border-b border-slate-200/80 pb-4">
            <div className="flex items-center justify-between gap-3">
              <CardTitle>{t("Recent Reports")}</CardTitle>
            {!loading && (
              <span className="font-mono text-xs uppercase tracking-[0.2em] text-slate-500" data-testid="daily-report-count-label">
                {filteredItems.length} {t("on file")}
              </span>
            )}
            </div>
            <div className="mt-4">
              <Input
                value={searchQuery}
                onChange={(event) => setSearchQuery(event.target.value)}
                placeholder={t("Search by project, number, preparer, date, or location")}
                data-testid="daily-report-search-input"
                className="h-12 border-[color:var(--border-bold)] text-[0.95rem]"
              />
            </div>
          </CardHeader>
          <CardContent className="p-0">
          {loading ? (
            <div className="p-12 flex items-center justify-center text-slate-500">
              <Loader2 className="w-6 h-6 animate-spin mr-2" /> {t("Loading...")}
            </div>
          ) : filteredItems.length === 0 ? (
            <div className="p-8 sm:p-10">
              <EmptyState
                icon={ClipboardList}
                title={searchQuery ? t("No reports match this search") : t("No daily reports yet")}
                body={searchQuery ? t("Try another project name, report number, date, or preparer.") : t("File one before the crew leaves the site at end of day.")}
                testId="empty-state"
                action={{ label: t("File First Report"), onClick: () => navigate("/daily/submit"), testId: "empty-cta" }}
              />
            </div>
          ) : (
            <JobFolderList
              items={filteredItems}
              dateField="report_date"
              testIdPrefix="daily-folders"
              jobsMaster={jobsMaster}
              showCert={showCert}
              renderItem={(it) => {
                const safeProjectLabel = formatOperatorJobLabel(it.project_number, it.project_name || jobsMaster[(it.project_number || "").trim()] || it.project_number);
                const safeProjectNumber = sanitizeOperatorProjectNumber(it.project_number, "Project support");
                return (
                <div
                  onClick={() => navigate(`${dailyReportDetailBase}/${it.id}`)}
                  className="p-4 sm:p-5 hover:bg-red-50 cursor-pointer transition-colors duration-150 flex flex-col sm:flex-row sm:items-center gap-3"
                  data-testid={`daily-row-${it.id}`}
                >
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 flex-wrap">
                      <span className="inline-flex items-center px-2 py-0.5 bg-red-700 text-white text-[10px] font-mono uppercase tracking-wider rounded font-bold">
                        {it.report_date}
                      </span>
                      {it.project_number && (
                        <span className="inline-flex items-center px-2 py-0.5 bg-slate-800 text-white text-[10px] font-mono uppercase tracking-wider rounded">
                          #{safeProjectNumber}
                        </span>
                      )}
                      <span className="font-display text-lg font-bold text-slate-900 truncate">
                        {safeProjectLabel || "—"}
                      </span>
                    </div>
                    <div className="text-sm text-slate-600 mt-1 flex flex-wrap gap-x-3 gap-y-1">
                      {it.weather_summary && (
                        <span className="inline-flex items-center gap-1">
                          <CloudSun className="w-3.5 h-3.5 text-amber-600" />
                          {it.weather_summary}
                        </span>
                      )}
                      <span className="inline-flex items-center gap-1"><Users className="w-3.5 h-3.5 text-slate-500" /> {it.crew_count || 0} {t("crew")}</span>
                      <span className="inline-flex items-center gap-1"><Building2 className="w-3.5 h-3.5 text-slate-500" /> {it.sub_count || 0} {t("subs")}</span>
                      <span className="inline-flex items-center gap-1"><UserRound className="w-3.5 h-3.5 text-slate-500" /> {it.visitor_count || 0} {t("visitors")}</span>
                      <span className="inline-flex items-center gap-1">
                        <Camera className="w-3.5 h-3.5" /> {it.photo_count || 0}
                      </span>
                    </div>
                    <div className="font-mono text-[11px] uppercase tracking-wider text-slate-500 mt-1">
                      {formatDateLong(it.report_date)} · {t("Prepared by")}{" "}
                      {it.prepared_by || "—"}
                    </div>
                  </div>
                  <div className="flex gap-2">
                    <Button
                      size="sm"
                      data-testid={`view-${it.id}`}
                      onClick={(e) => {
                        e.stopPropagation();
                        navigate(`${dailyReportDetailBase}/${it.id}`, { state: { returnTo: pathname } });
                      }}
                    >
                      <Eye className="w-4 h-4 mr-1" /> {t("View")}
                    </Button>
                    <Button
                      variant="outline"
                      size="icon"
                      onClick={(e) => handleDelete(it.id, e)}
                      data-testid={`delete-${it.id}`}
                      aria-label="Delete daily report"
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
          </CardContent>
        </Card>
      </main>
    </div>
    </PortalShell>
  );
}
