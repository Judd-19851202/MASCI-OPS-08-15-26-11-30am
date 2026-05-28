// PmFieldLeadership.jsx — iter105
//
// PM-scoped read-only view of Field Leadership records (write-ups,
// coaching, attendance, terminations, equipment checkouts, time-off,
// etc.) — filtered by the backend to the PM's assigned jobs only.
//
// Bug fix: the old PM tile routed to `/leadership/records` which is the
// password-gated leadership SPA and triggered a re-login prompt. Backend
// already supports PM tokens at `/api/field-leadership` with PM-scope
// filtering. This page is the proper landing.

import React, { useCallback, useEffect, useState } from "react";
import { Loader2, FileText, Search, Eye, X, UserCheck } from "lucide-react";
import { API } from "@/lib/api";
import { formatLocalDate, formatLocalDateTime } from "@/lib/dateUtils";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card } from "@/components/ui/card";
import {
  Select, SelectContent, SelectItem, SelectTrigger, SelectValue,
} from "@/components/ui/select";
import PmShell from "@/components/PmShell";
import { getPmToken } from "@/lib/pmAuth";
import { toast } from "sonner";

const KINDS = [
  { value: "", label: "All forms" },
  { value: "write_up", label: "Write-Up" },
  { value: "verbal_coaching", label: "Verbal Coaching" },
  { value: "attendance", label: "Attendance" },
  { value: "recognition", label: "Recognition" },
  { value: "equipment_checkout", label: "Equipment Checkout" },
  { value: "equipment_return", label: "Equipment Return" },
  { value: "new_employee_eval", label: "New Employee Eval" },
  { value: "crew_eval", label: "Crew Eval" },
  { value: "promotion_recommendation", label: "Promotion Recommendation" },
  { value: "training_deficiency", label: "Training Deficiency" },
  { value: "employee_termination", label: "Termination" },
  { value: "time_off_request", label: "Time Off Request" },
  { value: "supervisor_notes", label: "Supervisor Notes" },
];

const KIND_LABEL = Object.fromEntries(KINDS.map((k) => [k.value, k.label]));

function authedFetch(path) {
  const tok = getPmToken();
  return fetch(`${API}${path}`, { headers: { "X-PM-Token": tok || "" } });
}

export default function PmFieldLeadership() {
  const [rows, setRows] = useState([]);
  const [counts, setCounts] = useState({});
  const [loading, setLoading] = useState(true);
  const [kind, setKind] = useState("");
  const [search, setSearch] = useState("");
  const [active, setActive] = useState(null);

  const refresh = useCallback(async () => {
    setLoading(true);
    try {
      const qs = new URLSearchParams();
      if (kind) qs.set("kind", kind);
      if (search.trim()) qs.set("q", search.trim());
      const r = await authedFetch(`/field-leadership?${qs.toString()}`);
      if (!r.ok) throw new Error(await r.text());
      const d = await r.json();
      setRows(d.items || []);
      setCounts(d.counts_by_kind || {});
    } catch (e) {
      toast.error("Failed to load Field Leadership records");
    } finally {
      setLoading(false);
    }
  }, [kind, search]);

  useEffect(() => { refresh(); }, [refresh]);

  return (
    <PmShell
      title="Field Leadership"
      section="field-leadership"
      intro={
        <div className="flex items-start gap-3">
          <div className="inline-flex items-center justify-center w-10 h-10 rounded-md bg-amber-600 text-white shrink-0">
            <UserCheck className="w-5 h-5" />
          </div>
          <div className="text-sm text-slate-700 leading-relaxed">
            Read-only view of every Field Leadership record filed against jobs assigned to you.
            Includes write-ups, coaching, recognition, attendance, evaluations, terminations,
            equipment checkouts, and time-off requests. Scope is enforced server-side by your PM
            assignment — you only see what's on your jobs.
          </div>
        </div>
      }
    >
      <Card className="p-3 sm:p-4 mb-4">
        <div className="flex flex-wrap items-end gap-3">
          <div className="flex-1 min-w-[160px]">
            <label className="font-mono text-[10px] uppercase tracking-wider text-slate-500 block mb-1">
              Search
            </label>
            <div className="relative">
              <Search className="w-4 h-4 absolute left-2.5 top-1/2 -translate-y-1/2 text-slate-400" />
              <Input
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && refresh()}
                placeholder="Employee · job # · supervisor…"
                className="h-11 pl-8"
                data-testid="pm-fl-search"
              />
            </div>
          </div>
          <div>
            <label className="font-mono text-[10px] uppercase tracking-wider text-slate-500 block mb-1">
              Form Type
            </label>
            <Select value={kind || "__all__"} onValueChange={(v) => setKind(v === "__all__" ? "" : v)}>
              <SelectTrigger className="h-11 min-w-[200px]" data-testid="pm-fl-kind">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="__all__">All forms</SelectItem>
                {KINDS.filter((k) => k.value).map((k) => (
                  <SelectItem key={k.value} value={k.value}>
                    {k.label} {counts[k.value] ? `(${counts[k.value]})` : ""}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          <Button onClick={refresh} disabled={loading} className="h-11 bg-amber-600 hover:bg-amber-700 text-white" data-testid="pm-fl-apply">
            Apply
          </Button>
        </div>
      </Card>

      <Card className="overflow-x-auto" data-testid="pm-fl-table">
        {loading ? (
          <div className="p-12 flex items-center justify-center text-slate-500">
            <Loader2 className="w-6 h-6 animate-spin mr-2" /> Loading…
          </div>
        ) : rows.length === 0 ? (
          <div className="p-12 text-center text-slate-500">
            <FileText className="w-8 h-8 mx-auto mb-2 text-slate-400" />
            No Field Leadership records on your jobs yet.
          </div>
        ) : (
          <table className="w-full text-sm">
            <thead className="bg-slate-100 text-slate-700 uppercase tracking-wider text-xs">
              <tr>
                <th className="text-left px-3 py-2">Filed</th>
                <th className="text-left px-3 py-2">Doc ID</th>
                <th className="text-left px-3 py-2">Form Type</th>
                <th className="text-left px-3 py-2">Employee</th>
                <th className="text-left px-3 py-2">Supervisor</th>
                <th className="text-left px-3 py-2">Job</th>
                <th className="text-right px-3 py-2">Actions</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((r) => (
                <tr key={r.id} className="border-t border-slate-100 hover:bg-amber-50/30">
                  <td className="px-3 py-2 font-mono text-xs">{formatLocalDate(r.occurred_at || r.created_at)}</td>
                  <td className="px-3 py-2 font-mono text-xs">{r.doc_id || "—"}</td>
                  <td className="px-3 py-2">{KIND_LABEL[r.kind] || r.kind}</td>
                  <td className="px-3 py-2 font-semibold">{r.employee_name || "—"}</td>
                  <td className="px-3 py-2">{r.supervisor_name || "—"}</td>
                  <td className="px-3 py-2 font-mono text-xs">{r.project_number || "—"}</td>
                  <td className="px-3 py-2 text-right">
                    <Button size="sm" variant="outline" onClick={() => setActive(r)} data-testid={`pm-fl-view-${r.id}`}>
                      <Eye className="w-3.5 h-3.5 mr-1" /> View
                    </Button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </Card>

      {active && <DetailDrawer record={active} onClose={() => setActive(null)} />}
    </PmShell>
  );
}

function DetailDrawer({ record, onClose }) {
  return (
    <div className="fixed inset-0 bg-black/40 z-50 flex items-end sm:items-center justify-center p-3" onClick={onClose} data-testid="pm-fl-detail">
      <Card className="w-full max-w-2xl max-h-[90vh] overflow-auto" onClick={(e) => e.stopPropagation()}>
        <div className="p-4 sm:p-5 border-b border-slate-200 flex items-start justify-between">
          <div>
            <div className="font-mono text-[10px] uppercase tracking-wider text-amber-700 font-bold">
              {KIND_LABEL[record.kind] || record.kind} · {record.doc_id || "—"}
            </div>
            <h2 className="font-display text-xl font-black mt-0.5">{record.employee_name || "—"}</h2>
            <div className="text-xs text-slate-500 mt-1 font-mono">
              {record.project_number || ""} · {record.project_name || ""}
            </div>
          </div>
          <Button variant="ghost" size="sm" onClick={onClose}><X className="w-4 h-4" /></Button>
        </div>
        <div className="p-4 sm:p-5 text-sm space-y-2">
          <Row label="Filed" value={formatLocalDateTime(record.occurred_at || record.created_at)} />
          <Row label="Supervisor" value={record.supervisor_name} />
          <Row label="Position" value={record.employee_position} />
          {record.details && Object.entries(record.details).filter(([k]) => !k.startsWith("_") && k !== "hr_decision").slice(0, 12).map(([k, v]) => (
            <Row key={k} label={k.replace(/_/g, " ")} value={typeof v === "object" ? JSON.stringify(v) : String(v ?? "—")} />
          ))}
        </div>
        <div className="p-4 sm:p-5 border-t border-slate-200 flex justify-end gap-2">
          <a
            href={`${API}/field-leadership/${record.id}/pdf`}
            target="_blank"
            rel="noreferrer"
            className="inline-flex items-center h-10 px-4 rounded-md bg-amber-600 hover:bg-amber-700 text-white font-bold uppercase tracking-wide text-sm"
            data-testid="pm-fl-download-pdf"
            onClick={(e) => {
              // Append PM token so the GET is authed
              const tok = getPmToken();
              if (tok) {
                e.preventDefault();
                fetch(`${API}/field-leadership/${record.id}/pdf`, { headers: { "X-PM-Token": tok } })
                  .then((r) => r.blob())
                  .then((b) => {
                    const url = URL.createObjectURL(b);
                    window.open(url, "_blank");
                  });
              }
            }}
          >
            <FileText className="w-4 h-4 mr-1" /> Download PDF
          </a>
          <Button variant="outline" onClick={onClose}>Close</Button>
        </div>
      </Card>
    </div>
  );
}

function Row({ label, value }) {
  return (
    <div className="flex gap-3">
      <div className="w-40 shrink-0 font-mono text-[10px] uppercase tracking-wider text-slate-500 pt-0.5">{label}</div>
      <div className="flex-1 text-slate-900 whitespace-pre-wrap">{String(value ?? "—")}</div>
    </div>
  );
}
