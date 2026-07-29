/**
 * TRACK 16.07 · Transportation Workflow Activation · Inline Widgets.
 *
 * Replaces the Track-16.06 ComingSoon placeholders with real, operator-
 * grade inline workflows that complete from the Transportation Compliance
 * Center without leaving the page:
 *
 *   • InspectionWizard       — full Readiness Inspection capture (<90s)
 *   • DocumentDropzone       — drag-drop + camera + progress + preview
 *   • SignaturePad           — typed/checkbox signature with audit payload
 *   • RateCreateDialog       — create + activate a new rate schedule version
 *   • ComplianceTimeline     — full audit lineage rendering per entity
 *   • PacketChecklist        — packet status with submit / approve / return
 *
 * Every widget routes through existing Phase 1 + Phase 2 endpoints. No
 * new identity, no new storage system, no new audit kinds.
 */
import React, { useEffect, useState, useCallback, useRef } from "react";
import {
  Upload, Camera, CheckCircle2, AlertTriangle, FileText, Clock,
  RefreshCw, X, Loader2, ClipboardCheck, ChevronRight, ChevronLeft,
  PenTool, Send, RotateCcw, History,
} from "lucide-react";
import { api } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectTrigger, SelectValue, SelectContent, SelectItem } from "@/components/ui/select";
import { Textarea } from "@/components/ui/textarea";
import { Progress } from "@/components/ui/progress";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from "@/components/ui/dialog";
import { buildScopedPortalAuthHeaders } from "@/lib/authHeaders";
import { Chip, adminHeaders, txGet } from "./_shared";

const API = process.env.REACT_APP_BACKEND_URL;

// ════════════════════════════════════════════════════════════════════════
// Document Dropzone (drag · drop · browse · camera · progress · preview)
// ════════════════════════════════════════════════════════════════════════
export function DocumentDropzone({ kind, parentId, documentTypes, onUploaded, testid }) {
  // kind ∈ { "carrier", "driver" }
  const fileRef = useRef(null);
  const cameraRef = useRef(null);
  const [docType, setDocType] = useState(documentTypes[0]);
  const [expiresAt, setExpiresAt] = useState("");
  const [drag, setDrag] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [progress, setProgress] = useState(0);
  const [error, setError] = useState(null);
  const [last, setLast] = useState(null);

  const url = kind === "carrier"
    ? `/admin/transportation/carriers/${parentId}/documents`
    : `/admin/transportation/persons/${parentId}/documents`;

  async function send(file) {
    if (!file) return;
    setUploading(true); setProgress(5); setError(null);
    try {
      const form = new FormData();
      form.append("document_type", docType);
      if (expiresAt) form.append("expires_at", new Date(expiresAt).toISOString());
      form.append("file", file);
      const xhr = new XMLHttpRequest();
      xhr.open("POST", `${API}/api${url}`, true);
      const headers = buildScopedPortalAuthHeaders(["admin"]);
      Object.entries(headers).forEach(([key, value]) => {
        if (value) xhr.setRequestHeader(key, value);
      });
      xhr.upload.onprogress = (e) => {
        if (e.lengthComputable) {
          setProgress(Math.round((e.loaded / e.total) * 90) + 5);
        }
      };
      const done = new Promise((res, rej) => {
        xhr.onload = () => res(xhr);
        xhr.onerror = () => rej(new Error("network"));
      });
      xhr.send(form);
      const r = await done;
      if (r.status < 200 || r.status >= 300) {
        throw new Error(JSON.parse(r.responseText || "{}").detail || `HTTP ${r.status}`);
      }
      const body = JSON.parse(r.responseText || "{}");
      setProgress(100);
      setLast(body);
      onUploaded && onUploaded(body);
    } catch (e) {
      setError(String(e.message || e));
    } finally {
      setUploading(false);
      setTimeout(() => setProgress(0), 1500);
    }
  }

  return (
    <div data-testid={testid || "doc-dropzone"} className="space-y-3">
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-2">
        <div>
          <Label className="text-xs">Document type</Label>
          <Select value={docType} onValueChange={setDocType}>
            <SelectTrigger data-testid="dropzone-type-select"><SelectValue /></SelectTrigger>
            <SelectContent>
              {documentTypes.map((t) => <SelectItem key={t} value={t}>{t}</SelectItem>)}
            </SelectContent>
          </Select>
        </div>
        <div className="sm:col-span-2">
          <Label className="text-xs">Expires (optional)</Label>
          <Input
            type="date" value={expiresAt} onChange={(e) => setExpiresAt(e.target.value)}
            data-testid="dropzone-expires-input"
          />
        </div>
      </div>

      <div
        onDragOver={(e) => { e.preventDefault(); setDrag(true); }}
        onDragLeave={() => setDrag(false)}
        onDrop={(e) => {
          e.preventDefault(); setDrag(false);
          const f = e.dataTransfer.files?.[0]; if (f) send(f);
        }}
        className={`border-2 border-dashed rounded-md p-6 text-center transition-colors ${drag ? "border-blue-400 bg-blue-50" : "border-slate-300 bg-slate-50"}`}
        data-testid="dropzone-area"
      >
        {uploading ? (
          <div className="space-y-2">
            <Loader2 className="h-6 w-6 mx-auto animate-spin text-blue-600" />
            <div className="text-sm text-slate-600">Uploading…</div>
            <Progress value={progress} className="h-2" />
          </div>
        ) : (
          <>
            <Upload className="h-7 w-7 mx-auto text-slate-400 mb-2" />
            <div className="text-sm text-slate-700">Drag a file here, or:</div>
            <div className="mt-2 flex items-center justify-center gap-2 flex-wrap">
              <Button size="sm" variant="outline" onClick={() => fileRef.current?.click()} data-testid="dropzone-browse-btn">
                <Upload className="h-3.5 w-3.5 mr-1" />Browse
              </Button>
              <Button size="sm" variant="outline" onClick={() => cameraRef.current?.click()} data-testid="dropzone-camera-btn">
                <Camera className="h-3.5 w-3.5 mr-1" />Camera
              </Button>
            </div>
            <input
              ref={fileRef} type="file" className="hidden"
              onChange={(e) => { const f = e.target.files?.[0]; if (f) send(f); e.target.value = ""; }}
              data-testid="dropzone-file-input"
            />
            <input
              ref={cameraRef} type="file" accept="image/*" capture="environment" className="hidden"
              onChange={(e) => { const f = e.target.files?.[0]; if (f) send(f); e.target.value = ""; }}
              data-testid="dropzone-camera-input"
            />
          </>
        )}
      </div>

      {error && <div className="text-sm text-rose-700" data-testid="dropzone-error">{error}</div>}
      {last && (
        <div className="text-xs text-emerald-700 flex items-center gap-1" data-testid="dropzone-last-uploaded">
          <CheckCircle2 className="h-3.5 w-3.5" />
          Uploaded {last.original_filename} · stored as <span className="font-mono">{(last.file_key || "").slice(0, 24)}…</span>
        </div>
      )}
    </div>
  );
}

// ════════════════════════════════════════════════════════════════════════
// Signature Pad (typed signature with audit payload)
// ════════════════════════════════════════════════════════════════════════
export function SignaturePad({ open, onClose, onSign, title, testid }) {
  const [name, setName] = useState("");
  const [acknowledged, setAck] = useState(false);

  function submit() {
    if (!name.trim() || !acknowledged) return;
    const payload = {
      printed_name: name.trim(),
      typed_signature: name.trim(),
      acknowledged: true,
      acknowledged_at: new Date().toISOString(),
      user_agent: navigator.userAgent,
      timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
    };
    onSign(payload);
    setName(""); setAck(false);
  }

  return (
    <Dialog open={open} onOpenChange={(v) => { if (!v) onClose(); }}>
      <DialogContent data-testid={testid || "signature-pad"}>
        <DialogHeader>
          <DialogTitle>{title || "Sign and acknowledge"}</DialogTitle>
        </DialogHeader>
        <div className="space-y-3">
          <div>
            <Label className="text-xs">Printed name</Label>
            <Input
              data-testid="signature-name-input"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="Type your full name as your signature"
            />
          </div>
          <label className="flex items-start gap-2 text-sm text-slate-700" data-testid="signature-ack-row">
            <input
              type="checkbox" checked={acknowledged}
              onChange={(e) => setAck(e.target.checked)}
              data-testid="signature-ack-checkbox"
              className="mt-0.5"
            />
            <span>
              I confirm I am authorized to sign on behalf of the carrier and that
              this typed signature has the same legal effect as a handwritten one.
            </span>
          </label>
          <div className="text-xs text-slate-500">
            Captured at signing: timestamp, user-agent, time zone, and the actor
            email from your admin session. Stored immutably in the audit trail.
          </div>
        </div>
        <DialogFooter>
          <Button variant="outline" onClick={onClose} data-testid="signature-cancel-btn">Cancel</Button>
          <Button onClick={submit} disabled={!name.trim() || !acknowledged} data-testid="signature-submit-btn">
            <PenTool className="h-4 w-4 mr-1" />Sign
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

// ════════════════════════════════════════════════════════════════════════
// Rate Create Dialog (create new draft + optional immediate activation)
// ════════════════════════════════════════════════════════════════════════
export function RateCreateDialog({ open, onClose, onCreated }) {
  const [hourly, setHourly] = useState("85.00");
  const [activate, setActivate] = useState(true);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState(null);

  async function submit() {
    setBusy(true); setError(null);
    try {
      const created = await api.post(
        "/admin/transportation/rate-schedules",
        { hourly_rate: parseFloat(hourly) },
        { headers: adminHeaders() }
      );
      let result = created.data;
      if (activate) {
        const r = await api.post(
          `/admin/transportation/rate-schedules/${result.id}/activate`,
          {}, { headers: adminHeaders() }
        );
        result = r.data;
      }
      onCreated && onCreated(result);
      onClose();
    } catch (e) {
      setError(e?.response?.data?.detail || String(e));
    } finally {
      setBusy(false);
    }
  }

  return (
    <Dialog open={open} onOpenChange={(v) => { if (!v) onClose(); }}>
      <DialogContent data-testid="rate-create-dialog">
        <DialogHeader><DialogTitle>New rate schedule version</DialogTitle></DialogHeader>
        <div className="space-y-3">
          <div>
            <Label className="text-xs">Hourly rate (USD)</Label>
            <Input
              type="number" step="0.01" min="0.01"
              value={hourly} onChange={(e) => setHourly(e.target.value)}
              data-testid="rate-create-hourly-input"
            />
          </div>
          <label className="flex items-center gap-2 text-sm">
            <input
              type="checkbox" checked={activate} onChange={(e) => setActivate(e.target.checked)}
              data-testid="rate-create-activate-checkbox"
            />
            <span>Activate immediately (retires the current active version)</span>
          </label>
          <div className="text-xs text-slate-500">
            All historic packets keep their original locked rate. Only future
            packets adopt the new active version.
          </div>
          {error && <div className="text-sm text-rose-700" data-testid="rate-create-error">{error}</div>}
        </div>
        <DialogFooter>
          <Button variant="outline" onClick={onClose} data-testid="rate-create-cancel">Cancel</Button>
          <Button onClick={submit} disabled={busy} data-testid="rate-create-submit">
            {busy ? <Loader2 className="h-4 w-4 mr-1 animate-spin" /> : <CheckCircle2 className="h-4 w-4 mr-1" />}
            Create{activate ? " & Activate" : ""}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

// ════════════════════════════════════════════════════════════════════════
// MASCI Hauler Readiness Inspection Wizard
// ════════════════════════════════════════════════════════════════════════
const INSPECTION_TRIGGERS = [
  ["initial_onboarding", "Initial onboarding"],
  ["annual_recertification", "Annual recertification"],
  ["random", "Random audit"],
  ["safety_concern", "Safety concern"],
  ["customer_complaint", "Customer complaint"],
  ["incident_or_accident", "Incident / accident"],
  ["vehicle_replacement", "Vehicle replacement"],
  ["major_modification", "Major modification"],
  ["management_requested", "Management requested"],
  ["dispatch_requested", "Dispatch requested"],
  ["safety_requested", "Safety requested"],
];

export function InspectionWizard({ open, onClose, truckId, onComplete, testid }) {
  const [stage, setStage] = useState("setup");
  const [trigger, setTrigger] = useState("initial_onboarding");
  const [reason, setReason] = useState("");
  const [inspectorName, setInspectorName] = useState("");
  const [personId, setPersonId] = useState("");
  const [inspection, setInspection] = useState(null);
  const [error, setError] = useState(null);
  const [busy, setBusy] = useState(false);
  const [cursor, setCursor] = useState(0);

  // Reset on open
  useEffect(() => {
    if (open) {
      setStage("setup"); setError(null); setInspection(null); setCursor(0);
    }
  }, [open]);

  async function start() {
    setBusy(true); setError(null);
    try {
      const r = await api.post(
        `/admin/transportation/trucks/${truckId}/inspections`,
        { trigger, reason: reason || null, inspector_name: inspectorName,
          transport_person_id: personId || null },
        { headers: adminHeaders() }
      );
      setInspection(r.data);
      setStage("walkthrough");
    } catch (e) {
      setError(e?.response?.data?.detail || String(e));
    } finally { setBusy(false); }
  }

  // Group items by category preserving server order.
  const groups = (() => {
    const items = inspection?.checklist_items || [];
    const order = [];
    const byCat = {};
    for (const it of items) {
      if (!(it.category in byCat)) { byCat[it.category] = []; order.push(it.category); }
      byCat[it.category].push(it);
    }
    return order.map((cat) => ({ category: cat, items: byCat[cat] }));
  })();
  const cat = groups[cursor];

  async function applyItemUpdates(updates) {
    if (!inspection || !updates?.length) return;
    setBusy(true); setError(null);
    try {
      const r = await api.patch(
        `/admin/transportation/inspections/${inspection.id}`,
        updates, { headers: adminHeaders() }
      );
      setInspection(r.data);
    } catch (e) {
      setError(e?.response?.data?.detail || String(e));
    } finally { setBusy(false); }
  }

  function setItemStatus(key, status) {
    // Optimistic update
    setInspection((prev) => {
      if (!prev) return prev;
      const items = prev.checklist_items.map((it) =>
        it.key === key ? { ...it, status } : it
      );
      return { ...prev, checklist_items: items };
    });
    applyItemUpdates([{ key, status }]);
  }

  function setItemNotes(key, notes) {
    setInspection((prev) => {
      if (!prev) return prev;
      const items = prev.checklist_items.map((it) =>
        it.key === key ? { ...it, notes } : it
      );
      return { ...prev, checklist_items: items };
    });
    applyItemUpdates([{ key, status: inspection.checklist_items.find((i) => i.key === key)?.status || "not_observed", notes }]);
  }

  async function markAllPass(category) {
    const updates = (inspection.checklist_items || [])
      .filter((it) => it.category === category)
      .map((it) => ({ key: it.key, status: "pass" }));
    if (updates.length) await applyItemUpdates(updates);
  }

  async function complete() {
    setBusy(true); setError(null);
    try {
      const r = await api.post(
        `/admin/transportation/inspections/${inspection.id}/complete`,
        {}, { headers: adminHeaders() }
      );
      setInspection(r.data);
      setStage("done");
      onComplete && onComplete(r.data);
    } catch (e) {
      setError(e?.response?.data?.detail || String(e));
    } finally { setBusy(false); }
  }

  const progress = inspection ? Math.round(
    100 * (inspection.checklist_items || []).filter((i) => i.status !== "not_observed").length /
    Math.max(1, (inspection.checklist_items || []).length)
  ) : 0;

  return (
    <Dialog open={open} onOpenChange={(v) => { if (!v) onClose(); }}>
      <DialogContent className="max-w-3xl max-h-[90vh] overflow-y-auto" data-testid={testid || "inspection-wizard"}>
        <DialogHeader>
          <DialogTitle>MASCI Hauler Truck Readiness Inspection</DialogTitle>
        </DialogHeader>

        {stage === "setup" && (
          <div className="space-y-3" data-testid="insp-stage-setup">
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              <div>
                <Label className="text-xs">Trigger</Label>
                <Select value={trigger} onValueChange={setTrigger}>
                  <SelectTrigger data-testid="insp-trigger-select"><SelectValue /></SelectTrigger>
                  <SelectContent>
                    {INSPECTION_TRIGGERS.map(([v, l]) => <SelectItem key={v} value={v}>{l}</SelectItem>)}
                  </SelectContent>
                </Select>
              </div>
              <div>
                <Label className="text-xs">Inspector name *</Label>
                <Input
                  value={inspectorName} onChange={(e) => setInspectorName(e.target.value)}
                  data-testid="insp-inspector-input" placeholder="First Last"
                />
              </div>
              <div className="sm:col-span-2">
                <Label className="text-xs">Reason (optional)</Label>
                <Input
                  value={reason} onChange={(e) => setReason(e.target.value)}
                  data-testid="insp-reason-input"
                  placeholder="e.g., complaint #1234, replacement of truck T-42"
                />
              </div>
              <div className="sm:col-span-2">
                <Label className="text-xs">Driver (optional)</Label>
                <Input
                  value={personId} onChange={(e) => setPersonId(e.target.value)}
                  data-testid="insp-person-input"
                  placeholder="Driver ID for PPE rollup"
                />
              </div>
            </div>
            {error && <div className="text-sm text-rose-700" data-testid="insp-setup-error">{error}</div>}
            <div className="text-xs text-slate-500 border-l-2 border-slate-300 pl-3" data-testid="insp-disclaimer-setup">
              MASCI Hauler Truck Readiness Inspection is an operational readiness inspection only. It does not replace any DOT, FMCSA, CDL, carrier, or legally required inspection.
            </div>
            <DialogFooter>
              <Button variant="outline" onClick={onClose} data-testid="insp-setup-cancel">Cancel</Button>
              <Button onClick={start} disabled={busy || !inspectorName.trim()} data-testid="insp-setup-start">
                {busy ? <Loader2 className="h-4 w-4 mr-1 animate-spin" /> : <ClipboardCheck className="h-4 w-4 mr-1" />}
                Start Inspection
              </Button>
            </DialogFooter>
          </div>
        )}

        {stage === "walkthrough" && inspection && cat && (
          <div className="space-y-3" data-testid="insp-stage-walkthrough">
            <div className="flex items-center justify-between">
              <div className="text-sm font-medium text-slate-800 capitalize">
                {cat.category.replace(/_/g, " ")} <span className="text-slate-400">· {cursor + 1} / {groups.length}</span>
              </div>
              <Button size="sm" variant="outline" onClick={() => markAllPass(cat.category)} data-testid="insp-all-pass-btn">
                Mark all pass
              </Button>
            </div>
            <Progress value={progress} className="h-1" />
            <div className="border border-slate-200 rounded divide-y divide-slate-100">
              {cat.items.map((it) => (
                <div key={it.key} className="p-3" data-testid={`insp-item-${it.key}`}>
                  <div className="text-sm text-slate-800 mb-2">{it.label}</div>
                  <div className="flex flex-wrap gap-2">
                    {["pass", "needs_correction", "not_applicable"].map((s) => (
                      <button
                        key={s}
                        onClick={() => setItemStatus(it.key, s)}
                        className={`px-2.5 py-1 rounded text-xs border transition-colors ${
                          it.status === s
                            ? s === "pass"
                              ? "bg-emerald-600 text-white border-emerald-600"
                              : s === "needs_correction"
                                ? "bg-amber-500 text-white border-amber-500"
                                : "bg-slate-700 text-white border-slate-700"
                            : "bg-white text-slate-700 border-slate-300 hover:bg-slate-50"
                        }`}
                        data-testid={`insp-item-${it.key}-${s}`}
                      >
                        {s.replace(/_/g, " ")}
                      </button>
                    ))}
                  </div>
                  {it.status === "needs_correction" && (
                    <Textarea
                      placeholder="Correction notes (what needs to be fixed?)"
                      value={it.notes || ""}
                      onChange={(e) => setItemNotes(it.key, e.target.value)}
                      data-testid={`insp-item-${it.key}-notes`}
                      className="mt-2 text-xs"
                      rows={2}
                    />
                  )}
                </div>
              ))}
            </div>
            {error && <div className="text-sm text-rose-700" data-testid="insp-walkthrough-error">{error}</div>}
            <DialogFooter>
              <Button variant="outline" onClick={() => setCursor((c) => Math.max(0, c - 1))} disabled={cursor === 0} data-testid="insp-prev">
                <ChevronLeft className="h-4 w-4 mr-1" />Back
              </Button>
              {cursor < groups.length - 1 ? (
                <Button onClick={() => setCursor((c) => c + 1)} data-testid="insp-next">
                  Next<ChevronRight className="h-4 w-4 ml-1" />
                </Button>
              ) : (
                <Button onClick={complete} disabled={busy} data-testid="insp-complete">
                  {busy ? <Loader2 className="h-4 w-4 mr-1 animate-spin" /> : <CheckCircle2 className="h-4 w-4 mr-1" />}
                  Complete Inspection
                </Button>
              )}
            </DialogFooter>
          </div>
        )}

        {stage === "done" && inspection && (
          <div className="space-y-3" data-testid="insp-stage-done">
            <div className="text-center py-4">
              <CheckCircle2 className="h-12 w-12 mx-auto text-emerald-600" />
              <div className="mt-2 text-lg font-semibold text-slate-900">Inspection Complete</div>
              <Chip value={inspection.result} testid="insp-done-chip" />
              <div className="text-xs text-slate-500 mt-2">
                Expires {(inspection.expires_at || "").slice(0, 10)} · Eligibility recomputed automatically.
              </div>
            </div>
            <div className="text-xs text-slate-500 border-l-2 border-slate-300 pl-3" data-testid="insp-disclaimer-done">
              MASCI Hauler Truck Readiness Inspection is an operational readiness inspection only. It does not replace any DOT, FMCSA, CDL, carrier, or legally required inspection.
            </div>
            <DialogFooter>
              <Button onClick={onClose} data-testid="insp-done-close">Close</Button>
            </DialogFooter>
          </div>
        )}
      </DialogContent>
    </Dialog>
  );
}

// ════════════════════════════════════════════════════════════════════════
// Compliance Timeline (per-entity audit lineage)
// ════════════════════════════════════════════════════════════════════════
export function ComplianceTimeline({ entityType, entityId, testid }) {
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const r = await txGet(`/admin/transportation/timeline/${entityType}/${entityId}`);
      setItems(r.data.items || []);
    } finally { setLoading(false); }
  }, [entityType, entityId]);
  useEffect(() => { load(); }, [load]);

  return (
    <div data-testid={testid || "compliance-timeline"} className="space-y-2">
      <div className="flex items-center justify-between">
        <div className="text-xs uppercase tracking-wide text-slate-500 font-medium flex items-center gap-1">
          <History className="h-3.5 w-3.5" />Compliance Timeline
        </div>
        <Button variant="ghost" size="sm" onClick={load} data-testid="timeline-refresh">
          <RefreshCw className="h-3.5 w-3.5" />
        </Button>
      </div>
      {loading ? <div className="text-sm text-slate-500" data-testid="timeline-loading">Loading…</div> : (
        items.length === 0 ? (
          <div className="text-xs text-slate-500 border border-dashed border-slate-200 rounded p-3" data-testid="timeline-empty">
            No events yet for this entity.
          </div>
        ) : (
          <ol className="relative border-l-2 border-slate-200 ml-2 space-y-2 pl-4" data-testid="timeline-list">
            {items.map((e) => (
              <li key={e.id} className="relative" data-testid={`timeline-row-${e.id}`}>
                <span className="absolute -left-[1.42rem] top-1.5 w-2.5 h-2.5 rounded-full bg-slate-400 border-2 border-white" />
                <div className="text-xs font-medium text-slate-800">{e.kind.replace(/^transport_/, "").replace(/_/g, " ")}</div>
                <div className="text-[11px] text-slate-500">
                  {(e.ts || "").replace("T", " ").slice(0, 19)} · {e.entity_type} · by {e.actor || "—"}
                </div>
              </li>
            ))}
          </ol>
        )
      )}
    </div>
  );
}

// ════════════════════════════════════════════════════════════════════════
// Packet Checklist (status display + transitions + signature)
// ════════════════════════════════════════════════════════════════════════
export function PacketChecklist({ carrierId, packet, onChanged }) {
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState(null);
  const [sigOpen, setSigOpen] = useState(false);
  const [correctionNotes, setCorrectionNotes] = useState("");

  async function ensurePacket() {
    if (packet) return packet;
    const r = await api.post(
      `/admin/transportation/carriers/${carrierId}/packet`, {},
      { headers: adminHeaders() }
    );
    return r.data;
  }

  async function transition(target_status, body = {}) {
    setBusy(true); setError(null);
    try {
      let p = packet;
      if (!p) p = await ensurePacket();
      const r = await api.patch(
        `/admin/transportation/packets/${p.id}`,
        { target_status, ...body }, { headers: adminHeaders() }
      );
      onChanged && onChanged(r.data);
    } catch (e) {
      setError(e?.response?.data?.detail || String(e));
    } finally { setBusy(false); }
  }

  async function signAndSubmit(payload) {
    setSigOpen(false);
    await transition("submitted", { signature_payload: payload });
  }

  const status = packet?.status || "draft";

  return (
    <div className="space-y-3" data-testid="packet-checklist">
      <div className="flex items-center justify-between">
        <div>
          <div className="text-xs uppercase tracking-wide text-slate-500 font-medium">Packet Status</div>
          <div className="mt-1"><Chip value={status} testid="packet-status-chip" /></div>
        </div>
        <div className="flex items-center gap-2 flex-wrap justify-end">
          {!packet && (
            <Button size="sm" onClick={() => transition("draft")} disabled={busy} data-testid="packet-create-btn">
              <Send className="h-3.5 w-3.5 mr-1" />Start Packet
            </Button>
          )}
          {packet && ["draft", "in_progress", "needs_correction"].includes(status) && (
            <Button size="sm" onClick={() => setSigOpen(true)} disabled={busy} data-testid="packet-submit-btn">
              <PenTool className="h-3.5 w-3.5 mr-1" />Sign & Submit
            </Button>
          )}
          {packet && status === "submitted" && (
            <Button size="sm" onClick={() => transition("pending_review")} disabled={busy} data-testid="packet-to-pending-review-btn">
              Move to Pending Review
            </Button>
          )}
          {packet && status === "pending_review" && (
            <>
              <Button size="sm" variant="outline" onClick={() => transition("needs_correction", { correction_notes: correctionNotes })} disabled={busy} data-testid="packet-return-btn">
                <RotateCcw className="h-3.5 w-3.5 mr-1" />Return for Correction
              </Button>
              <Button size="sm" onClick={() => transition("approved")} disabled={busy} data-testid="packet-approve-btn">
                <CheckCircle2 className="h-3.5 w-3.5 mr-1" />Approve
              </Button>
            </>
          )}
        </div>
      </div>

      {packet && status === "pending_review" && (
        <Textarea
          placeholder="Correction notes (if returning to carrier)"
          value={correctionNotes} onChange={(e) => setCorrectionNotes(e.target.value)}
          data-testid="packet-correction-notes"
          rows={2}
        />
      )}

      {error && <div className="text-sm text-rose-700" data-testid="packet-error">{error}</div>}

      {packet && (
        <dl className="grid grid-cols-2 gap-x-4 gap-y-1 text-sm">
          <dt className="text-slate-500">Version</dt><dd>{packet.packet_version}</dd>
          <dt className="text-slate-500">Rate locked</dt><dd className="font-mono text-xs">{(packet.rate_schedule_id || "").slice(0, 8)}…</dd>
          {packet.submitted_at && (<><dt className="text-slate-500">Submitted</dt><dd>{packet.submitted_at.slice(0, 10)}</dd></>)}
          {packet.reviewed_at && (<><dt className="text-slate-500">Reviewed</dt><dd>{packet.reviewed_at.slice(0, 10)} by {packet.reviewed_by}</dd></>)}
          {packet.correction_notes && (<><dt className="text-slate-500">Correction notes</dt><dd className="text-xs text-amber-700">{packet.correction_notes}</dd></>)}
          {packet.signature_payload && (<><dt className="text-slate-500">Signed by</dt><dd className="text-xs text-emerald-700">{packet.signature_payload.printed_name}</dd></>)}
        </dl>
      )}

      <SignaturePad
        open={sigOpen}
        onClose={() => setSigOpen(false)}
        onSign={signAndSubmit}
        title="Sign and submit the carrier packet"
        testid="packet-signature-pad"
      />
    </div>
  );
}
