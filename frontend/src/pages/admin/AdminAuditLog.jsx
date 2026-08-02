// AdminAuditLog.jsx — Iter130. Unified read-only audit timeline.
// Aggregates audit_events + admin_audit + operations_events +
// integration_wizard_runs into one filterable, paginated feed.
import React, { useCallback, useEffect, useState } from "react";
import {
  History, Search, RefreshCcw, Filter, Loader2, ChevronLeft, ChevronRight,
} from "lucide-react";
import LegacyAdminModernShell from "@/components/admin/LegacyAdminModernShell";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Select, SelectContent, SelectItem, SelectTrigger, SelectValue,
} from "@/components/ui/select";
import { api } from "@/lib/api";
import { toast } from "sonner";
import { operationalError } from "@/lib/errors";
import { EvidenceSummary } from "@/components/admin/trust/TrustPrimitives";
// TRACK 27.03 · Canonical local-time formatter.
import { formatPlatformTime } from "@/lib/platformTime";

const SOURCE_PILL = {
  audit_events:            "bg-cyan-100 text-cyan-900 border-cyan-300",
  admin_audit:             "bg-red-100 text-red-900 border-red-300",
  operations_events:       "bg-blue-100 text-blue-900 border-blue-300",
  integration_wizard_runs: "bg-amber-100 text-amber-900 border-amber-300",
};

const SOURCE_LABELS = {
  audit_events: "Message activity",
  admin_audit: "Admin activity",
  operations_events: "Operations activity",
  integration_wizard_runs: "Integration runs",
};

const PAGE_SIZE = 50;

export default function AdminAuditLog() {
  const [q, setQ] = useState("");
  const [actor, setActor] = useState("");
  const [action, setAction] = useState("");
  const [source, setSource] = useState("");
  const [offset, setOffset] = useState(0);
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [expanded, setExpanded] = useState({});

  const load = useCallback(async (opts = {}) => {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      params.set("limit", String(PAGE_SIZE));
      params.set("offset", String(opts.offset ?? offset));
      if (q) params.set("q", q);
      if (actor) params.set("actor", actor);
      if (action) params.set("action", action);
      if (source) params.set("source", source);
      const r = await api.get(`/admin/audit-log?${params.toString()}`);
      setData(r.data);
    } catch (e) {
      toast.error(operationalError(e, "Failed to load activity history"));
    } finally { setLoading(false); }
  }, [action, actor, offset, q, source]);

  useEffect(() => { load({ offset: 0 }); }, [load]);

  const apply = () => { setOffset(0); load({ offset: 0 }); };
  const reset = () => { setQ(""); setActor(""); setAction(""); setSource(""); setOffset(0); load({ offset: 0 }); };
  const goto = (next) => { setOffset(next); load({ offset: next }); };

  const total = data?.total || 0;
  const rows = data?.rows || [];
  const start = Math.min(offset + 1, total);
  const end = Math.min(offset + rows.length, total);

  return (
    <LegacyAdminModernShell
      title="Activity History"
      subtitle="Cross-portal merged timeline of every action."
      breadcrumb={[
        { label: "Standards & Readiness", to: "/admin/governance-trust" },
        { label: "Activity History" },
      ]}
      testidPrefix="admin-audit-log"
    >
      <div className="max-w-7xl mx-auto" data-testid="admin-audit-log-page">
        <div className="bg-white border border-slate-200 rounded-md p-5 mb-4 flex items-start gap-3">
          <div className="inline-flex items-center justify-center w-12 h-12 rounded-md bg-slate-900 text-white shrink-0">
            <History className="w-6 h-6" />
          </div>
          <div>
            <span className="font-mono text-[10px] uppercase tracking-[0.2em] text-slate-600 font-bold">
              Unified Timeline
            </span>
            <h1 className="font-display text-2xl font-black tracking-tight mt-0.5">Activity History</h1>
            <p className="text-sm text-slate-600 mt-1">
              Merged feed across message activity, admin activity, operations activity,
              and integration runs. Read-only, paginated, filterable.
            </p>
          </div>
        </div>

        {/* Filters */}
        <div className="bg-white border border-slate-200 rounded-md p-3 mb-3 grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-2">
          <div className="relative">
            <Search className="absolute left-2 top-2.5 w-3.5 h-3.5 text-slate-400" />
            <Input placeholder="Search any field…" className="pl-7 h-9" value={q} onChange={(e) => setQ(e.target.value)} data-testid="audit-q" />
          </div>
          <Input placeholder="Actor (email / name)" className="h-9" value={actor} onChange={(e) => setActor(e.target.value)} data-testid="audit-actor" />
          <Input placeholder="Action contains…" className="h-9" value={action} onChange={(e) => setAction(e.target.value)} data-testid="audit-action" />
          <Select value={source || "all"} onValueChange={(v) => setSource(v === "all" ? "" : v)}>
            <SelectTrigger className="h-9" data-testid="audit-source"><SelectValue placeholder="Source" /></SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All sources</SelectItem>
              <SelectItem value="audit_events">Message activity</SelectItem>
              <SelectItem value="admin_audit">Admin activity</SelectItem>
              <SelectItem value="operations_events">Operations activity</SelectItem>
              <SelectItem value="integration_wizard_runs">Integration runs</SelectItem>
            </SelectContent>
          </Select>
          <div className="flex gap-1">
            <Button onClick={apply} className="h-9 flex-1 bg-slate-900 hover:bg-slate-800 text-white" data-testid="audit-apply"><Filter className="w-3.5 h-3.5 mr-1" />Apply</Button>
            <Button onClick={reset} variant="outline" className="h-9" data-testid="audit-reset">Reset</Button>
            <Button onClick={() => load()} variant="outline" className="h-9" disabled={loading}><RefreshCcw className="w-3.5 h-3.5" /></Button>
          </div>
        </div>

        {/* Pager */}
        <div className="flex items-center text-xs font-mono text-slate-600 mb-2">
          <span data-testid="audit-pager-stats">
            {total === 0 ? "0 rows" : `${start}–${end} of ${total}`}
          </span>
          <div className="ml-auto inline-flex gap-1">
            <Button size="sm" variant="outline" className="h-7" disabled={offset === 0 || loading} onClick={() => goto(Math.max(0, offset - PAGE_SIZE))} data-testid="audit-prev"><ChevronLeft className="w-3.5 h-3.5" /></Button>
            <Button size="sm" variant="outline" className="h-7" disabled={end >= total || loading} onClick={() => goto(offset + PAGE_SIZE)} data-testid="audit-next"><ChevronRight className="w-3.5 h-3.5" /></Button>
          </div>
        </div>

        {/* Table */}
        <div className="bg-white border border-slate-200 rounded-md overflow-x-auto">
          {loading && !data ? (
            <div className="text-center py-12 text-slate-500"><Loader2 className="w-6 h-6 animate-spin mx-auto" /></div>
          ) : rows.length === 0 ? (
            <p className="p-6 text-sm text-slate-500 italic text-center" data-testid="audit-empty">No activity records match these filters.</p>
          ) : (
            <table className="w-full text-xs" data-testid="audit-table">
              <thead className="bg-slate-100 text-slate-700 font-mono uppercase tracking-[0.15em]">
                <tr>
                  <th className="text-left px-3 py-2 whitespace-nowrap">When</th>
                  <th className="text-left px-3 py-2">Actor</th>
                  <th className="text-left px-3 py-2">Action</th>
                  <th className="text-left px-3 py-2">Target</th>
                  <th className="text-left px-3 py-2">Source</th>
                  <th className="text-left px-3 py-2"></th>
                </tr>
              </thead>
              <tbody>
                {rows.map((r, i) => {
                  const key = `${r.source}:${r.at}:${i}`;
                  const open = !!expanded[key];
                  return (
                    <React.Fragment key={key}>
                      <tr className="border-t border-slate-100" data-testid={`audit-row-${i}`}>
                        <td className="px-3 py-2 font-mono text-slate-600 whitespace-nowrap">{formatPlatformTime(r.at)}</td>
                        <td className="px-3 py-2 font-bold">{r.actor || "—"}</td>
                        <td className="px-3 py-2 font-mono">{r.action || "—"}</td>
                        <td className="px-3 py-2 truncate max-w-[14rem]">{r.target || "—"}</td>
                        <td className="px-3 py-2">
                          <span className={`px-1.5 py-0.5 rounded border text-[9px] font-mono uppercase tracking-[0.15em] font-bold ${SOURCE_PILL[r.source] || "bg-slate-100"}`}>
                            {SOURCE_LABELS[r.source] || r.source}
                          </span>
                        </td>
                        <td className="px-3 py-2 text-right">
                          <button onClick={() => setExpanded((e) => ({ ...e, [key]: !open }))} className="text-slate-700 hover:text-slate-900 font-bold underline" data-testid={`audit-toggle-${i}`}>
                            {open ? "Hide" : "Detail"}
                          </button>
                        </td>
                      </tr>
                      {open && (
                        <tr className="bg-slate-50">
                          <td colSpan={6} className="px-3 py-2">
                            <div
                              className="rounded-md border border-slate-200 bg-white p-2"
                              data-testid={`audit-detail-${i}`}
                            >
                              <EvidenceSummary
                                value={r.detail || {}}
                                testidPrefix={`audit-detail-${i}-evidence`}
                              />
                            </div>
                          </td>
                        </tr>
                      )}
                    </React.Fragment>
                  );
                })}
              </tbody>
            </table>
          )}
        </div>
      </div>
    </LegacyAdminModernShell>
  );
}
