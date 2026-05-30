import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import {
  TrendingUp,
  Loader2,
  Calendar,
  FolderOpen,
  Users,
  HardHat,
  Package,
  DollarSign,
  RefreshCw,
} from "lucide-react";
import { api } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { MasciLogo } from "@/components/MasciLogo";
import HubBackLink from "@/components/HubBackLink";

const fmtCurrency = (n) =>
  new Intl.NumberFormat("en-US", { style: "currency", currency: "USD" }).format(
    Number(n) || 0
  );

const fmtHours = (n) => (Number(n) || 0).toFixed(2);

export default function ProjectPnlPage() {
  const [projects, setProjects] = useState([]);
  const [projectNumber, setProjectNumber] = useState("");
  const [dateFrom, setDateFrom] = useState("");
  const [dateTo, setDateTo] = useState("");
  const [laborRate, setLaborRate] = useState("45");
  const [data, setData] = useState(null);
  const [loadingList, setLoadingList] = useState(true);
  const [loadingPnl, setLoadingPnl] = useState(false);
  const [error, setError] = useState("");

  const loadProjects = async () => {
    setLoadingList(true);
    try {
      const r = await api.get("/admin/projects/list");
      setProjects(r.data?.items || []);
      // Auto-select the first project if none chosen yet
      if (!projectNumber && r.data?.items?.[0]) {
        setProjectNumber(r.data.items[0].project_number);
      }
    } catch (e) {
      setError("Could not load project list. Check admin login.");
    } finally {
      setLoadingList(false);
    }
  };

  useEffect(() => {
    loadProjects();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const runPnl = async () => {
    if (!projectNumber) {
      setError("Pick a project first.");
      return;
    }
    setLoadingPnl(true);
    setError("");
    try {
      const params = new URLSearchParams({
        project_number: projectNumber,
        labor_rate: laborRate || "45",
      });
      if (dateFrom) params.set("date_from", dateFrom);
      if (dateTo) params.set("date_to", dateTo);
      const r = await api.get(`/admin/projects/pnl?${params.toString()}`);
      setData(r.data);
    } catch (e) {
      setError(e?.response?.data?.detail || "Failed to load P&L");
    } finally {
      setLoadingPnl(false);
    }
  };

  // Auto-run on first project load + whenever the project changes (no need
  // to click a button to see numbers)
  useEffect(() => {
    if (projectNumber) runPnl();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [projectNumber]);

  const summary = data || {};
  const subTotalCount = useMemo(
    () => (summary.sub_breakdown || []).reduce((n, s) => n + (s.headcount_total || 0), 0),
    [summary]
  );

  return (
    <div className="min-h-screen bg-slate-50 pb-20">
      {/* Top bar */}
      <div className="bg-slate-900 text-white sticky top-0 z-20 border-b-4 border-amber-400">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 py-3 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <HubBackLink
              className="text-amber-400 hover:text-white transition-colors"
              testId="pnl-back-link"
            />
            <MasciLogo variant="light" className="h-7" />
            <span className="font-mono text-[10px] sm:text-xs uppercase tracking-[0.25em] text-amber-400 font-bold pl-3 border-l border-slate-700">
              Project P&amp;L Snapshot
            </span>
          </div>
          <Button
            onClick={loadProjects}
            variant="ghost"
            size="sm"
            className="text-slate-300 hover:text-white hover:bg-slate-800"
            data-testid="pnl-refresh-projects"
          >
            <RefreshCw className="w-4 h-4 mr-1.5" />
            <span className="hidden sm:inline text-xs">Refresh projects</span>
          </Button>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 py-6 space-y-6">
        {/* Title */}
        <div className="flex items-end gap-4">
          <TrendingUp className="w-9 h-9 text-red-700" />
          <div>
            <h1 className="font-display text-3xl sm:text-4xl font-black text-slate-900 leading-none">
              Live job-cost dashboard
            </h1>
            <p className="text-sm text-slate-600 mt-1">
              Pick a project + a date range. Numbers come straight from the
              field — every Daily Report submitted feeds this page.
            </p>
          </div>
        </div>

        {/* Filter bar */}
        <div
          className="bg-white border border-slate-200 rounded-md p-4 grid grid-cols-1 md:grid-cols-[2fr_1fr_1fr_1fr_auto] gap-3 items-end"
          data-testid="pnl-filter-bar"
        >
          <div>
            <Label className="font-mono text-[10px] uppercase tracking-[0.2em] text-slate-700 flex items-center gap-1">
              <FolderOpen className="w-3 h-3" /> Project
            </Label>
            <Select value={projectNumber} onValueChange={setProjectNumber}>
              <SelectTrigger
                className="h-11 border-2 border-slate-300 mt-1"
                data-testid="pnl-project-select"
              >
                <SelectValue placeholder={loadingList ? "Loading…" : "Pick a project"} />
              </SelectTrigger>
              <SelectContent>
                {projects.map((p) => (
                  <SelectItem
                    key={p.project_number}
                    value={p.project_number}
                    data-testid={`pnl-project-opt-${p.project_number}`}
                  >
                    <span className="font-mono text-xs font-bold mr-2">{p.project_number}</span>
                    {p.project_name && (
                      <span className="text-slate-700">— {p.project_name}</span>
                    )}
                    <span className="text-slate-400 text-xs ml-2">
                      ({p.report_count} report{p.report_count === 1 ? "" : "s"})
                    </span>
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          <div>
            <Label className="font-mono text-[10px] uppercase tracking-[0.2em] text-slate-700 flex items-center gap-1">
              <Calendar className="w-3 h-3" /> From
            </Label>
            <Input
              type="date"
              value={dateFrom}
              onChange={(e) => setDateFrom(e.target.value)}
              className="h-11 border-2 border-slate-300 mt-1"
              data-testid="pnl-date-from"
            />
          </div>
          <div>
            <Label className="font-mono text-[10px] uppercase tracking-[0.2em] text-slate-700 flex items-center gap-1">
              <Calendar className="w-3 h-3" /> To
            </Label>
            <Input
              type="date"
              value={dateTo}
              onChange={(e) => setDateTo(e.target.value)}
              className="h-11 border-2 border-slate-300 mt-1"
              data-testid="pnl-date-to"
            />
          </div>
          <div>
            <Label className="font-mono text-[10px] uppercase tracking-[0.2em] text-slate-700 flex items-center gap-1">
              <DollarSign className="w-3 h-3" /> Labor rate $/hr
            </Label>
            <Input
              type="number"
              min="0"
              step="0.5"
              value={laborRate}
              onChange={(e) => setLaborRate(e.target.value)}
              className="h-11 border-2 border-slate-300 font-mono mt-1"
              data-testid="pnl-labor-rate"
            />
          </div>
          <Button
            onClick={runPnl}
            disabled={loadingPnl || !projectNumber}
            className="bg-red-700 hover:bg-red-800 text-white font-bold uppercase tracking-wide text-xs h-11 px-5"
            data-testid="pnl-run-btn"
          >
            {loadingPnl ? (
              <>
                <Loader2 className="w-4 h-4 mr-1.5 animate-spin" /> Loading
              </>
            ) : (
              "Run snapshot"
            )}
          </Button>
        </div>

        {error && (
          <div className="bg-red-50 border-2 border-red-300 text-red-800 rounded-md p-3 text-sm">
            {error}
          </div>
        )}

        {/* Empty state */}
        {!data && !loadingPnl && (
          <div className="bg-white border-2 border-dashed border-slate-300 rounded-md p-10 text-center">
            <TrendingUp className="w-10 h-10 text-slate-300 mx-auto mb-3" />
            <p className="text-slate-500 text-sm">
              Pick a project to see the live cost snapshot.
            </p>
          </div>
        )}

        {/* Snapshot */}
        {data && (
          <>
            {/* KPI tiles */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-x-6 gap-y-3" data-testid="pnl-kpis">
              <Tile
                icon={<Calendar className="w-4 h-4" />}
                label="Reports"
                value={String(data.report_count || 0)}
                sub={
                  data.report_count
                    ? `${data.date_from || ""} → ${data.date_to || ""}`
                    : "No reports in range"
                }
              />
              <Tile
                icon={<Users className="w-4 h-4" />}
                label="MASCI crew hrs"
                value={fmtHours(data.crew_hours_total)}
                sub={`${data.crew_breakdown?.length || 0} workers`}
              />
              <Tile
                icon={<HardHat className="w-4 h-4" />}
                label="Sub man-hrs"
                value={fmtHours(data.sub_hours_total)}
                sub={`${data.sub_breakdown?.length || 0} cos · ${fmtHours(subTotalCount)} bodies`}
              />
              <Tile
                icon={<DollarSign className="w-4 h-4" />}
                label={`Labor cost @ $${data.labor_rate}/hr`}
                value={fmtCurrency(data.labor_cost)}
                accent
              />
            </div>

            {/* Crew breakdown */}
            <Section
              icon={<Users className="w-4 h-4" />}
              title="MASCI Crew · hours by employee"
              count={data.crew_breakdown?.length || 0}
            >
              {data.crew_breakdown?.length ? (
                <Table
                  headers={["Employee", "Trade", "Days", "Hours", `Cost @ $${data.labor_rate}/hr`]}
                  rows={data.crew_breakdown.map((c, i) => [
                    <span key={i} className="font-bold">{c.name}</span>,
                    c.trade || "—",
                    String(c.days_on_site),
                    <span key={`h${i}`} className="font-mono">{fmtHours(c.hours)}</span>,
                    <span key={`c${i}`} className="font-mono font-bold text-red-700">{fmtCurrency(c.cost_at_rate)}</span>,
                  ])}
                  testId="pnl-crew-table"
                />
              ) : (
                <Empty msg="No MASCI crew hours logged in this range." />
              )}
            </Section>

            {/* Sub breakdown */}
            <Section
              icon={<HardHat className="w-4 h-4" />}
              title="Subcontractors · hours by company"
              count={data.sub_breakdown?.length || 0}
            >
              {data.sub_breakdown?.length ? (
                <Table
                  headers={["Company", "Trade", "Days", "Avg headcount", "Total man-hrs"]}
                  rows={data.sub_breakdown.map((s, i) => [
                    <span key={i} className="font-bold">{s.company}</span>,
                    s.trade || "—",
                    String(s.days_on_site),
                    fmtHours(s.headcount_total / Math.max(s.days_on_site, 1)),
                    <span key={`h${i}`} className="font-mono font-bold">{fmtHours(s.hours)}</span>,
                  ])}
                  testId="pnl-sub-table"
                />
              ) : (
                <Empty msg="No subcontractor hours logged in this range." />
              )}
            </Section>

            {/* Materials */}
            <Section
              icon={<Package className="w-4 h-4" />}
              title="Materials · one row per delivery ticket"
              count={data.material_count || 0}
            >
              {data.material_lines?.length ? (
                <Table
                  headers={["Date", "Description", "Qty", "Unit", "Supplier", "Ticket #", "Photos", "Notes"]}
                  rows={data.material_lines.map((m, i) => [
                    <span key={i} className="font-mono text-xs">{m.report_date}</span>,
                    m.description || "—",
                    m.quantity || "—",
                    m.unit || "—",
                    <span key={`s${i}`} className="font-bold">{m.supplier || "—"}</span>,
                    <span key={`t${i}`} className="font-mono text-xs">{m.ticket_number || "—"}</span>,
                    m.ticket_photo_count ? (
                      <span key={`p${i}`} className="text-emerald-700 font-bold">📎 {m.ticket_photo_count}</span>
                    ) : "—",
                    <span key={`n${i}`} className="text-xs text-slate-600">{m.notes || ""}</span>,
                  ])}
                  testId="pnl-material-table"
                />
              ) : (
                <Empty msg="No material deliveries logged in this range." />
              )}
            </Section>
          </>
        )}
      </div>
    </div>
  );
}

const Tile = ({ icon, label, value, sub, accent }) => (
  <div
    className={`rounded-md p-4 border-2 ${
      accent
        ? "bg-slate-900 text-white border-slate-900"
        : "bg-white border-slate-200"
    }`}
    data-testid={`pnl-tile-${label.replace(/[^a-z0-9]/gi, "-").toLowerCase()}`}
  >
    <div className={`flex items-center gap-1.5 font-mono text-[10px] uppercase tracking-[0.2em] ${
      accent ? "text-amber-400" : "text-slate-600"
    }`}>
      {icon}
      <span className="font-bold">{label}</span>
    </div>
    <div className={`font-display text-3xl font-black mt-1 ${accent ? "" : "text-slate-900"}`}>
      {value}
    </div>
    <div className={`text-[11px] mt-0.5 ${accent ? "text-slate-300" : "text-slate-500"}`}>{sub}</div>
  </div>
);

const Section = ({ icon, title, count, children }) => (
  <div className="bg-white border border-slate-200 rounded-md overflow-hidden">
    <div className="bg-slate-900 text-white px-4 py-2.5 flex items-center gap-2">
      <span className="text-amber-400">{icon}</span>
      <span className="font-mono text-[11px] uppercase tracking-[0.2em] text-amber-400 font-bold flex-1">
        {title}
      </span>
      <span className="text-[10px] text-slate-300 font-mono">
        {count} row{count === 1 ? "" : "s"}
      </span>
    </div>
    <div className="p-3 sm:p-4">{children}</div>
  </div>
);

const Empty = ({ msg }) => (
  <div className="text-center text-sm text-slate-500 py-6">{msg}</div>
);

const Table = ({ headers, rows, testId }) => (
  <div className="overflow-x-auto" data-testid={testId}>
    <table className="w-full text-sm">
      <thead>
        <tr className="border-b-2 border-slate-200">
          {headers.map((h, i) => (
            <th
              key={i}
              className="text-left px-3 py-2 font-mono text-[10px] uppercase tracking-[0.2em] text-slate-600 font-bold"
            >
              {h}
            </th>
          ))}
        </tr>
      </thead>
      <tbody>
        {rows.map((row, i) => (
          <tr
            key={i}
            className="border-b border-slate-100 hover:bg-slate-50 transition-colors"
          >
            {row.map((cell, j) => (
              <td key={j} className="px-3 py-2 text-slate-800 align-top">
                {cell}
              </td>
            ))}
          </tr>
        ))}
      </tbody>
    </table>
  </div>
);
