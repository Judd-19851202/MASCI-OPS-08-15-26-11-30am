// EquipmentDashboard.jsx — Shop / Admin / PM Equipment Pre-Op Inspections.
// UXS-11E: wrapped in PortalShell with context-aware sidebar.
import React, { useEffect, useState } from "react";
import { Link, useNavigate, useLocation } from "react-router-dom";
import { Plus, Wrench, Eye, Trash2, Loader2, AlertOctagon } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { PortalShell } from "@/design-system";
import AdminBreadcrumb from "@/components/admin/AdminBreadcrumb";
import { renderAdminRouteSideNav } from "@/components/admin/AdminRouteShell";
import PmSideNavV2 from "@/components/pm/sidebar/SideNavV2";
import { ShareFormDialog } from "@/components/ShareFormDialog";
import EquipmentTrendsPanel from "@/components/EquipmentTrendsPanel";
import OpenItemsPanel from "@/components/OpenItemsPanel";
import ShopActivityFeed from "@/components/ShopActivityFeed";
import JobFolderList from "@/components/JobFolderList";
import { api } from "@/lib/api";
import { formatDateLong } from "@/lib/utils";
import { toast } from "sonner";
import { InformationCard } from "@/components/CanonicalCard";
import { SectionHeading } from "@/components/SectionHeading";
import EmptyState from "@/components/EmptyState";

export default function EquipmentDashboard() {
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [jobsMaster, setJobsMaster] = useState({}); // PROJECT-IDENTITY-004 canonical map
  const navigate = useNavigate();
  const { pathname } = useLocation();

  // Iter520 · Phase V.5 · P0-2A/2B — derive portal context from pathname so
  // we hide admin-only widgets and PM-incompatible actions when the
  // dashboard is rendered inside /pm/.
  const portalContext = pathname.startsWith("/pm/")
    ? "pm"
    : pathname.startsWith("/shop/")
      ? "shop"
      : "admin";
  const isPmContext = portalContext === "pm";
  const isShopContext = portalContext === "shop";

  // UXS-11E: pick sidebar matching the host portal.
  const sideNav = isPmContext ? <PmSideNavV2 /> : renderAdminRouteSideNav();
  const portalRole = isPmContext
    ? "Project Management"
    : isShopContext
      ? "Shop Operations"
      : "Administration";

  const load = async () => {
    setLoading(true);
    try {
      const [res, jm] = await Promise.all([
        api.get("/equipment-inspections"),
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
      toast.error("Could not load equipment inspections");
    } finally {
      setLoading(false);
    }
  };
  useEffect(() => { load(); }, []);

  const handleDelete = async (id, e) => {
    e.stopPropagation();
    if (!window.confirm("Delete this equipment inspection? This cannot be undone.")) return;
    try {
      await api.delete(`/equipment-inspections/${id}`);
      toast.success("Inspection deleted");
      setItems((p) => p.filter((i) => i.id !== id));
    } catch {
      toast.error("Delete failed");
    }
  };

  const failCount = items.filter((i) => (i.fail_count || 0) > 0).length;

  return (
    <PortalShell
      portalName="MASCI"
      portalRole={portalRole}
      pageTitle="Equipment Pre-Op"
      sideNav={sideNav}
      primaryActions={
        !isPmContext ? (
          <div className="flex items-center gap-2">
            <ShareFormDialog
              formType="equipment-inspection"
              path="/equipment/submit"
              title="Share Equipment Form"
              description="Anyone with this link can file an Equipment Pre-Op Inspection. No login required."
              testIdPrefix="share-equipment"
            />
            <Button
              onClick={() => navigate("/equipment/new")}
              size="sm"
              data-testid="new-equipment-btn"
            >
              <Plus className="w-4 h-4 mr-1" />
              <span className="hidden sm:inline">New Inspection</span>
              <span className="sm:hidden">New</span>
            </Button>
          </div>
        ) : null
      }
    >
      <div className="max-w-6xl mx-auto px-5 sm:px-6 py-6 sm:py-8" data-testid="equipment-dashboard-page">
        {pathname.startsWith("/admin/") ? (
          <AdminBreadcrumb crumbs={[
            { label: "Field Operations" },
            { label: "Equipment Pre-Op" },
          ]} />
        ) : null}
        <InformationCard
          icon={Wrench}
          tone="slate"
          eyebrow="Field readiness"
          title="Daily Walk-Arounds"
          description="OSHA pre-shift inspections for every truck, excavator, roller, and tool on the job. Review the latest condition, open issues, and cleared units from one governed surface."
          testId="equipment-dashboard-summary"
          className="mb-8"
        >
          {failCount > 0 ? (
            <div className="pt-1">
              <span className="wp17-status-badge wp17-tone--red" data-testid="equipment-dashboard-fail-badge">
                <AlertOctagon className="w-3.5 h-3.5" /> {failCount} unit{failCount === 1 ? "" : "s"} flagged fail
              </span>
            </div>
          ) : null}
        </InformationCard>

        <SectionHeading
          index="01"
          title="Pre-Op trends and inspections"
          subtitle="Monitor current condition, open issues, and the latest inspection records without switching visual systems."
          testId="equipment-dashboard-heading"
        />

        <Card className="overflow-hidden">
          <CardHeader className="border-b border-slate-200/80 pb-4">
            <div className="flex items-center justify-between gap-3">
              <CardTitle>Pre-Op Trends &amp; Recent Inspections</CardTitle>
            {!loading && (
              <span className="font-mono text-xs uppercase tracking-[0.2em] text-slate-500">
                {items.length} on file
              </span>
            )}
            </div>
          </CardHeader>
          <CardContent className="p-0">
          <div className="p-4 sm:p-5 border-b border-slate-100">
            {!isPmContext && <EquipmentTrendsPanel />}
            {isPmContext && (
              <p className="text-sm text-slate-600">
                PM read-only view. Use the inspections list below to open any pre-op record for a project you manage.
              </p>
            )}
          </div>
          {!isPmContext && (
            <div className="p-4 sm:p-5 border-b border-slate-100">
              <OpenItemsPanel baseHref="/admin/equipment" testIdPrefix="admin-open" />
            </div>
          )}
          {!isPmContext && (
            <div className="p-4 sm:p-5 border-b border-slate-100">
              <ShopActivityFeed baseHref="/admin/equipment" testIdPrefix="admin-activity" />
            </div>
          )}
          {loading ? (
            <div className="p-12 flex items-center justify-center text-slate-500">
              <Loader2 className="w-6 h-6 animate-spin mr-2" /> Loading...
            </div>
          ) : items.length === 0 ? (
            <div className="p-8 sm:p-10">
              <EmptyState
                icon={Wrench}
                title={isPmContext ? "No inspections for your projects yet" : "No equipment inspections yet"}
                body={isPmContext
                  ? "When a pre-op inspection is filed on one of your assigned projects, it will appear here."
                  : "Run a daily pre-op inspection on any unit to log its condition."}
                testId="empty-state"
                action={!isPmContext ? { label: "File First Inspection", onClick: () => navigate("/equipment/new"), testId: "empty-cta" } : null}
              />
            </div>
          ) : (
            <JobFolderList
              items={items}
              dateField="inspection_date"
              testIdPrefix="equipment-folders"
              jobsMaster={jobsMaster}
              renderItem={(it) => {
                const fail = (it.fail_count || 0) > 0;
                const cleared = it.cleared || (fail && (it.signoff_count || 0) >= it.fail_count);
                return (
                  <div
                    onClick={() => navigate(`${pathname}/${it.id}`)}
                    className={`p-4 sm:p-5 hover:bg-red-50 cursor-pointer transition-colors duration-150 flex flex-col sm:flex-row sm:items-center gap-3 ${
                      fail && !cleared ? "border-l-4 border-red-700" : cleared ? "border-l-4 border-emerald-600" : ""
                    }`}
                    data-testid={`equipment-row-${it.id}`}
                  >
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 flex-wrap">
                        <span className="font-display text-lg font-bold text-slate-900 truncate">
                          {it.equipment_type} · {it.equipment_unit}
                        </span>
                        {fail && !cleared && (
                          <span className="wp17-status-badge wp17-tone--red">
                            <AlertOctagon className="w-3 h-3" /> {it.fail_count} FAIL
                          </span>
                        )}
                        {cleared && (
                          <span className="wp17-status-badge wp17-tone--emerald" data-testid={`cleared-badge-${it.id}`}>
                            ✓ CLEARED TO OPERATE
                          </span>
                        )}
                      </div>
                      <div className="text-sm text-slate-600 mt-1">
                        {(jobsMaster[((it.project_number || "").trim())] || it.project_name || "—")} {it.project_number ? `· #${it.project_number}` : ""} · Operator: {it.operator_name || "—"}
                      </div>
                      <div className="font-mono text-[11px] uppercase tracking-wider text-slate-500 mt-1">
                        {formatDateLong(it.inspection_date)} · {it.location || "—"}
                      </div>
                    </div>
                    <div className="flex gap-2">
                      <Button asChild size="sm" data-testid={`view-${it.id}`}>
                        <Link
                          to={`${pathname}/${it.id}`}
                          onClick={(e) => e.stopPropagation()}
                        >
                          <Eye className="w-4 h-4 mr-1" /> View
                        </Link>
                      </Button>
                      {!isPmContext && (
                        <Button
                          variant="outline"
                          size="icon"
                          onClick={(e) => handleDelete(it.id, e)}
                          data-testid={`delete-${it.id}`}
                          aria-label="Delete equipment"
                          title="Delete"
                        >
                          <Trash2 className="w-4 h-4" />
                        </Button>
                      )}
                    </div>
                  </div>
                );
              }}
            />
          )}
          </CardContent>
        </Card>
      </div>
    </PortalShell>
  );
}
