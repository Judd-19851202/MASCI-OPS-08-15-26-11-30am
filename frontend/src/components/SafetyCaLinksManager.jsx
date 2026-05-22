// SafetyCaLinksManager — Iter135. Manage related-entity links on a
// Corrective Action: which incident, failed pre-op, equipment unit,
// training record, audit, document, or fire extinguisher the CA
// stemmed from or is solving. Renders inside the CA edit dialog.
import React, { useCallback, useEffect, useState } from "react";
import axios from "axios";
import {
  Link as LinkIcon, Plus, X, AlertTriangle, ExternalLink, Loader2,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Select, SelectContent, SelectItem, SelectTrigger, SelectValue,
} from "@/components/ui/select";
import { getSafetyToken } from "@/lib/safetyAuth";
import { toast } from "sonner";

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;
const auth = () => ({ headers: { "X-Safety-Token": getSafetyToken() } });

// kind values must match backend coll_map in corrective_actions.py
export const LINK_KINDS = [
  { value: "incident",             label: "Incident / Near Miss",   defaultUrl: "/safety-portal/incidents" },
  { value: "equipment_inspection", label: "Failed Pre-Op",          defaultUrl: "/shop/equipment" },
  { value: "equipment_master",     label: "Equipment Master",       defaultUrl: "/shop" },
  { value: "training_record",      label: "Training Record",        defaultUrl: "/safety-portal/training" },
  { value: "audit",                label: "Audit / Inspection",     defaultUrl: "/safety-portal/audits" },
  { value: "safety_document",      label: "Safety Document",        defaultUrl: "/safety-portal/documents" },
  { value: "fire_ext",             label: "Fire Extinguisher",      defaultUrl: "/safety-portal/fire-extinguishers" },
];

const kindLabel = (k) => (LINK_KINDS.find((x) => x.value === k)?.label || k);

export default function SafetyCaLinksManager({ caId, onChanged }) {
  const [resolved, setResolved] = useState([]);
  const [loading, setLoading] = useState(false);
  const [adding, setAdding] = useState(false);
  const [showAdd, setShowAdd] = useState(false);
  const [form, setForm] = useState({ kind: "incident", id: "", label: "", url: "" });

  const refresh = useCallback(async () => {
    if (!caId) return;
    setLoading(true);
    try {
      const r = await axios.get(`${API}/safety/corrective-actions/${caId}/related-resolved`, auth());
      setResolved(r.data?.related || []);
    } catch (e) {
      // swallow — fresh CAs have nothing to resolve
    } finally {
      setLoading(false);
    }
  }, [caId]);

  useEffect(() => { refresh(); }, [refresh]);

  const submitAdd = async (e) => {
    e?.preventDefault?.();
    if (!form.id.trim()) { toast.error("Record ID is required"); return; }
    setAdding(true);
    try {
      const def = LINK_KINDS.find((k) => k.value === form.kind);
      const payload = {
        kind: form.kind,
        id: form.id.trim(),
        label: form.label.trim(),
        url: (form.url || def?.defaultUrl || "").trim(),
      };
      await axios.post(`${API}/safety/corrective-actions/${caId}/links`, payload, auth());
      toast.success("Linked");
      setForm({ kind: form.kind, id: "", label: "", url: "" });
      setShowAdd(false);
      await refresh();
      onChanged && onChanged();
    } catch (err) {
      toast.error(err?.response?.data?.detail || "Could not link");
    } finally {
      setAdding(false);
    }
  };

  const removeOne = async (link) => {
    if (!window.confirm("Remove this link?")) return;
    try {
      await axios.delete(
        `${API}/safety/corrective-actions/${caId}/links`,
        { ...auth(), params: { kind: link.kind, id: link.id } },
      );
      await refresh();
      onChanged && onChanged();
    } catch (err) {
      toast.error("Could not remove link");
    }
  };

  return (
    <div className="bg-slate-50 border border-slate-200 rounded-md p-3 sm:p-4" data-testid="safety-ca-links-manager">
      <div className="flex items-center justify-between gap-2 mb-2">
        <div className="font-mono text-[10px] uppercase tracking-[0.18em] text-slate-700 font-bold flex items-center gap-1.5">
          <LinkIcon className="w-3.5 h-3.5" />
          Related Records ({resolved.length})
        </div>
        {!showAdd && (
          <Button
            type="button"
            size="sm"
            variant="outline"
            onClick={() => setShowAdd(true)}
            className="h-8 border-2 border-slate-300 font-bold uppercase tracking-wide text-xs"
            data-testid="safety-ca-link-add-toggle"
          >
            <Plus className="w-3.5 h-3.5 mr-1" /> Add link
          </Button>
        )}
      </div>

      {loading ? (
        <div className="text-xs text-slate-500 py-2"><Loader2 className="w-3.5 h-3.5 animate-spin inline mr-1" /> Loading…</div>
      ) : resolved.length === 0 && !showAdd ? (
        <p className="text-xs text-slate-500 italic">
          Link this CA to the incident, failed pre-op, equipment unit, training record, audit, document, or fire extinguisher it relates to. Improves traceability for OSHA and insurance audits.
        </p>
      ) : (
        <ul className="space-y-1.5" data-testid="safety-ca-links-list">
          {resolved.map((r) => (
            <li
              key={`${r.kind}|${r.id}`}
              className={`flex items-center gap-2 px-2.5 py-1.5 rounded border-2 ${
                r.exists ? "bg-white border-slate-200" : "bg-amber-50 border-amber-300"
              }`}
              data-testid={`safety-ca-link-row-${r.kind}-${r.id}`}
            >
              <span className="inline-block px-1.5 py-0 rounded bg-slate-100 text-[9px] font-mono uppercase tracking-wider text-slate-700 shrink-0">
                {kindLabel(r.kind)}
              </span>
              <div className="flex-1 min-w-0">
                <div className="text-xs font-mono text-slate-900 truncate">
                  {r.label || r.summary || r.id}
                </div>
                {!r.exists && (
                  <div className="text-[10px] text-amber-800 flex items-center gap-1 mt-0.5">
                    <AlertTriangle className="w-3 h-3" /> Source record not found — may have been deleted.
                  </div>
                )}
              </div>
              {r.url && (
                <a
                  href={r.url}
                  target="_blank"
                  rel="noreferrer"
                  className="text-cyan-700 hover:text-cyan-900 shrink-0"
                  title="Open source record"
                  data-testid={`safety-ca-link-open-${r.kind}-${r.id}`}
                >
                  <ExternalLink className="w-3.5 h-3.5" />
                </a>
              )}
              <button
                type="button"
                onClick={() => removeOne(r)}
                className="text-slate-400 hover:text-red-700 shrink-0"
                title="Unlink"
                data-testid={`safety-ca-link-remove-${r.kind}-${r.id}`}
              >
                <X className="w-3.5 h-3.5" />
              </button>
            </li>
          ))}
        </ul>
      )}

      {showAdd && (
        <div className="mt-3 pt-3 border-t-2 border-dashed border-slate-200" data-testid="safety-ca-link-add-form">
          <div className="grid grid-cols-1 sm:grid-cols-12 gap-2 sm:items-end">
            <div className="sm:col-span-4">
              <Label className="font-mono text-[10px] uppercase tracking-[0.18em] text-slate-700 font-bold">Kind</Label>
              <Select value={form.kind} onValueChange={(v) => setForm((f) => ({ ...f, kind: v }))}>
                <SelectTrigger className="h-9 text-sm border-2 border-slate-300 mt-1" data-testid="safety-ca-link-kind">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {LINK_KINDS.map((k) => <SelectItem key={k.value} value={k.value}>{k.label}</SelectItem>)}
                </SelectContent>
              </Select>
            </div>
            <div className="sm:col-span-4">
              <Label className="font-mono text-[10px] uppercase tracking-[0.18em] text-slate-700 font-bold">Record ID *</Label>
              <Input
                value={form.id}
                onChange={(e) => setForm((f) => ({ ...f, id: e.target.value }))}
                placeholder="Paste UUID / unit number"
                className="h-9 text-sm border-2 border-slate-300 mt-1"
                data-testid="safety-ca-link-id"
              />
            </div>
            <div className="sm:col-span-4">
              <Label className="font-mono text-[10px] uppercase tracking-[0.18em] text-slate-700 font-bold">Label (optional)</Label>
              <Input
                value={form.label}
                onChange={(e) => setForm((f) => ({ ...f, label: e.target.value }))}
                placeholder="Friendly description"
                className="h-9 text-sm border-2 border-slate-300 mt-1"
                data-testid="safety-ca-link-label"
              />
            </div>
          </div>
          <div className="flex gap-2 mt-2">
            <Button
              type="button"
              onClick={submitAdd}
              disabled={adding || !form.id.trim()}
              size="sm"
              className="h-9 bg-cyan-700 hover:bg-cyan-800 text-white border-b-2 border-cyan-900 font-bold uppercase tracking-wide text-xs"
              data-testid="safety-ca-link-submit"
            >
              {adding ? <Loader2 className="w-3.5 h-3.5 mr-1 animate-spin" /> : <Plus className="w-3.5 h-3.5 mr-1" />}
              Link
            </Button>
            <Button
              type="button"
              size="sm"
              variant="outline"
              onClick={() => { setShowAdd(false); setForm({ kind: "incident", id: "", label: "", url: "" }); }}
              className="h-9 border-2 border-slate-300 font-bold uppercase tracking-wide text-xs"
              data-testid="safety-ca-link-cancel"
            >
              <X className="w-3.5 h-3.5 mr-1" /> Cancel
            </Button>
          </div>
        </div>
      )}
    </div>
  );
}
