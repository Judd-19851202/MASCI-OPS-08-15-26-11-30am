// Trench Safety · Command Center Actions
// ─────────────────────────────────────────────────────────────────────
// Phase 7.5A — Single shared module that hosts every write-action dialog
// and every read-side panel used by the Safety Portal and the Admin
// Portal Trench Safety surfaces. Build once, reuse everywhere.
//
// Exported pieces:
//   • CreateAssetDialog        — + New Asset
//   • EditAssetDialog          — Edit Asset (Asset ID immutable)
//   • RetireAssetDialog        — Retire / un-retire
//   • StatusChangeDialog       — Move between operational statuses
//   • OpenHoldDialog           — Open a Safety/Inspection/Maintenance Hold
//   • ClearHoldDialog          — Clear / release a hold
//   • CreateInspectionDialog   — Daily / Monthly / Annual · Pass/Fail · severity
//   • UploadCertificationDialog — Upload + expiry date
//   • RevokeCertificationDialog — Revoke with reason
//   • HoldsPanel               — List + actions
//   • InspectionsPanel         — List + create
//   • CertificationsPanel      — List + upload + revoke
//   • AuditTimelinePanel       — Complete asset audit timeline
//
// All dialogs route through `/api/trench-safety/*` endpoints which accept
// X-Safety-Token OR X-Admin-Token (Safety Portal and Admin Portal both
// satisfy the gate without code duplication).
import React, { useEffect, useState } from "react";
import {
  Loader2, Plus, Pencil, X, Power, AlertTriangle, ShieldAlert,
  FileWarning, CheckCircle2, History, Calendar, FileText, Trash2,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from "@/components/ui/dialog";
import { toast } from "sonner";
import { api } from "@/lib/api";
import { useT } from "@/lib/i18n";

// ── Constants (mirror backend `_models.py`) ───────────────────────────
export const ASSET_TYPES = [
  "Trench Box", "End Panel", "Spreader Bar", "Hydraulic Shore",
  "Slide Rail System", "Trench Jack", "Ladder", "Accessory",
  // Phase 8A — Road Plate (native asset type)
  "Road Plate",
];
export const CONDITIONS = ["Excellent", "Good", "Fair", "Poor", "Out Of Service"];
export const STATUSES = [
  "Available", "Assigned", "In Transport",
  "Inspection Hold", "Maintenance Hold", "Certification Hold", "Safety Hold",
  "Retired",
];
export const HOLD_KINDS = [
  "Inspection Hold", "Maintenance Hold", "Safety Hold", "Certification Hold",
];
export const INSPECTION_TYPES = [
  "Daily Visual",
  "Monthly Competent Person",
  "Annual Review",
  "Special Inspection",
  "Damage Inspection",
  "Return Inspection",
];
export const INSPECTION_RESULTS = ["Pass", "Fail"];
export const SEVERITIES = ["Minor", "Major", "Critical"];

export const CERTIFICATION_KINDS = [
  "Manufacturer", "Annual Inspection", "Engineering Letter",
  "Repair Certification", "Special",
];

// Phase 8A — Road Plate inspection checklist (per OMEGA directive).
// Items group: Structural · Surface · Corrosion · Edges · Lifting
// Features · Placement · Operational Safety. Routed through the
// existing Inspection Engine — checklist[] is the same shape every
// trench safety inspection uses.
export const ROAD_PLATE_CHECKLIST = [
  // Structural
  { key: "bent_plate",            label: "Bent Plate" },
  { key: "warped_plate",          label: "Warped Plate" },
  { key: "cracks",                label: "Cracks" },
  { key: "unsafe_deformation",    label: "Unsafe Deformation" },
  // Surface
  { key: "slick_surface",         label: "Slick Surface" },
  { key: "missing_anti_skid",     label: "Missing Anti-Skid" },
  { key: "surface_damage",        label: "Surface Damage" },
  // Corrosion
  { key: "rust",                  label: "Rust" },
  { key: "corrosion",             label: "Corrosion" },
  // Edges
  { key: "sharp_edge",            label: "Sharp Edge" },
  { key: "damaged_edge",          label: "Damaged Edge" },
  // Lifting features
  { key: "damaged_lift_hole",     label: "Damaged Lift Hole" },
  { key: "damaged_lifting_point", label: "Damaged Lifting Point" },
  // Placement
  { key: "proper_bearing",        label: "Proper Bearing" },
  { key: "proper_overlap",        label: "Proper Overlap" },
  { key: "proper_anchoring",      label: "Proper Anchoring" },
  { key: "proper_pinning",        label: "Proper Pinning" },
  // Operational safety
  { key: "traffic_safe",          label: "Traffic Safe" },
  { key: "pedestrian_safe",       label: "Pedestrian Safe" },
  { key: "markings_visible",      label: "Markings Visible" },
];

// Phase 8A — Road Plate repair kind taxonomy (Shop write surface).
// Plugged into the existing certified repair engine — these are kind
// values for `trench_safety_repairs.kind`, not a new collection.
export const ROAD_PLATE_REPAIR_KINDS = [
  "Weld Repair",
  "Structural Repair",
  "Surface Repair",
  "Edge Repair",
  "Anti-Skid Restoration",
];

function extractErr(e, fallback) {
  return e?.response?.data?.detail || e?.message || fallback;
}

// ═════════════════════════════════════════════════════════════════════
// Asset · Create / Edit / Retire
// ═════════════════════════════════════════════════════════════════════
function AssetForm({ value, onChange, isEdit }) {
  const { t } = useT();
  const set = (k, v) => onChange({ ...value, [k]: v });
  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
      <div>
        <Label className="text-xs font-bold">{t("Asset ID")} *</Label>
        <Input
          value={value.asset_id || ""}
          onChange={(e) => set("asset_id", e.target.value.toUpperCase())}
          disabled={isEdit}
          placeholder="TB-XX"
          className="font-mono uppercase"
          data-testid="asset-form-id"
        />
        {isEdit && (
          <div className="text-[10px] uppercase tracking-[0.14em] text-slate-500 mt-0.5">{t("Immutable")}</div>
        )}
      </div>
      <div>
        <Label className="text-xs font-bold">{t("Asset Type")} *</Label>
        <Select value={value.asset_type || "Trench Box"} onValueChange={(v) => set("asset_type", v)}>
          <SelectTrigger data-testid="asset-form-type"><SelectValue /></SelectTrigger>
          <SelectContent>
            {ASSET_TYPES.map((x) => <SelectItem key={x} value={x}>{t(x)}</SelectItem>)}
          </SelectContent>
        </Select>
      </div>
      <div>
        <Label className="text-xs font-bold">{t("Manufacturer")}</Label>
        <Input value={value.manufacturer || ""} onChange={(e) => set("manufacturer", e.target.value)} data-testid="asset-form-mfr" />
      </div>
      <div>
        <Label className="text-xs font-bold">{t("Model")}</Label>
        <Input value={value.model || ""} onChange={(e) => set("model", e.target.value)} data-testid="asset-form-model" />
      </div>
      <div>
        <Label className="text-xs font-bold">{t("Serial Number")}</Label>
        <Input value={value.serial_number || ""} onChange={(e) => set("serial_number", e.target.value)} className="font-mono" data-testid="asset-form-serial" />
      </div>
      <div>
        <Label className="text-xs font-bold">{t("Size")}</Label>
        <Input value={value.size || ""} onChange={(e) => set("size", e.target.value)} placeholder="6x24" data-testid="asset-form-size" />
      </div>
      <div>
        <Label className="text-xs font-bold">{t("Color")}</Label>
        <Input value={value.color || ""} onChange={(e) => set("color", e.target.value)} data-testid="asset-form-color" />
      </div>
      <div>
        <Label className="text-xs font-bold">{t("Weight (lb)")}</Label>
        <Input type="number" value={value.weight_lb ?? ""} onChange={(e) => set("weight_lb", e.target.value ? Number(e.target.value) : null)} data-testid="asset-form-weight" />
      </div>
      <div>
        <Label className="text-xs font-bold">{t("Rated Depth (ft)")}</Label>
        <Input type="number" value={value.rated_depth_ft ?? ""} onChange={(e) => set("rated_depth_ft", e.target.value ? Number(e.target.value) : null)} data-testid="asset-form-depth" />
      </div>
      <div>
        <Label className="text-xs font-bold">{t("Rated Soil Type")}</Label>
        <Input value={value.rated_soil_type || ""} onChange={(e) => set("rated_soil_type", e.target.value)} placeholder="Type A / B / C" data-testid="asset-form-soil" />
      </div>
      <div>
        <Label className="text-xs font-bold">{t("Condition")}</Label>
        <Select value={value.condition || "Good"} onValueChange={(v) => set("condition", v)}>
          <SelectTrigger data-testid="asset-form-condition"><SelectValue /></SelectTrigger>
          <SelectContent>
            {CONDITIONS.map((x) => <SelectItem key={x} value={x}>{t(x)}</SelectItem>)}
          </SelectContent>
        </Select>
      </div>
      <div>
        <Label className="text-xs font-bold">{t("Yard / Location")}</Label>
        <Input value={value.yard_location || value.current_location || ""} onChange={(e) => set("yard_location", e.target.value)} data-testid="asset-form-location" />
      </div>
      <div className="sm:col-span-2">
        <Label className="text-xs font-bold">{t("Notes")}</Label>
        <Textarea value={value.notes || ""} onChange={(e) => set("notes", e.target.value)} rows={2} data-testid="asset-form-notes" />
      </div>
      <div className="sm:col-span-2 flex items-center gap-2 mt-1">
        <input
          type="checkbox"
          checked={Boolean(value.requires_certification)}
          onChange={(e) => set("requires_certification", e.target.checked)}
          id="rc"
          data-testid="asset-form-requires-cert"
        />
        <Label htmlFor="rc" className="text-xs">{t("This asset requires a certification (engineered shore, slide rail, etc.)")}</Label>
      </div>
      {value.asset_type === "Road Plate" && (
        <>
          <div className="sm:col-span-2 -mt-1 mb-1 text-[10px] uppercase tracking-[0.18em] text-cyan-700 font-bold font-mono">
            {t("Road Plate · Physical Specs")}
          </div>
          <div>
            <Label className="text-xs font-bold">{t("Length (in)")}</Label>
            <Input type="number" value={value.length_in ?? ""} onChange={(e) => set("length_in", e.target.value ? Number(e.target.value) : null)} data-testid="rp-length" />
          </div>
          <div>
            <Label className="text-xs font-bold">{t("Width (in)")}</Label>
            <Input type="number" value={value.width_in ?? ""} onChange={(e) => set("width_in", e.target.value ? Number(e.target.value) : null)} data-testid="rp-width" />
          </div>
          <div>
            <Label className="text-xs font-bold">{t("Thickness (in)")}</Label>
            <Input type="number" step="0.125" value={value.thickness_in ?? ""} onChange={(e) => set("thickness_in", e.target.value ? Number(e.target.value) : null)} data-testid="rp-thickness" />
          </div>
          <div>
            <Label className="text-xs font-bold">{t("Weight (lb)")}</Label>
            <Input type="number" value={value.weight_lbs ?? ""} onChange={(e) => set("weight_lbs", e.target.value ? Number(e.target.value) : null)} data-testid="rp-weight" />
          </div>
          <div>
            <Label className="text-xs font-bold">{t("Rated Capacity (lb)")}</Label>
            <Input type="number" value={value.rated_capacity_lb ?? ""} onChange={(e) => set("rated_capacity_lb", e.target.value ? Number(e.target.value) : null)} data-testid="rp-capacity" />
          </div>
          <div>
            <Label className="text-xs font-bold">{t("Material")}</Label>
            <Input value={value.material || ""} onChange={(e) => set("material", e.target.value)} placeholder="A36 Steel" data-testid="rp-material" />
          </div>
          <div className="sm:col-span-2">
            <Label className="text-xs font-bold">{t("Color / Markings")}</Label>
            <Input value={value.markings || ""} onChange={(e) => set("markings", e.target.value)} placeholder={t("e.g., Yellow paint, MASCI stencil")} data-testid="rp-markings" />
          </div>
          <div className="sm:col-span-2 mt-1 mb-1 text-[10px] uppercase tracking-[0.18em] text-cyan-700 font-bold font-mono">
            {t("Road Plate · Condition Detail")}
          </div>
          <div>
            <Label className="text-xs font-bold">{t("Surface Condition")}</Label>
            <Select value={value.surface_condition || "Good"} onValueChange={(v) => set("surface_condition", v)}>
              <SelectTrigger data-testid="rp-surface"><SelectValue /></SelectTrigger>
              <SelectContent>
                {CONDITIONS.map((x) => <SelectItem key={x} value={x}>{t(x)}</SelectItem>)}
              </SelectContent>
            </Select>
          </div>
          <div>
            <Label className="text-xs font-bold">{t("Edge Condition")}</Label>
            <Select value={value.edge_condition || "Good"} onValueChange={(v) => set("edge_condition", v)}>
              <SelectTrigger data-testid="rp-edge"><SelectValue /></SelectTrigger>
              <SelectContent>
                {CONDITIONS.map((x) => <SelectItem key={x} value={x}>{t(x)}</SelectItem>)}
              </SelectContent>
            </Select>
          </div>
          <div>
            <Label className="text-xs font-bold">{t("Lifting Point Condition")}</Label>
            <Select value={value.lifting_point_condition || "Good"} onValueChange={(v) => set("lifting_point_condition", v)}>
              <SelectTrigger data-testid="rp-lifting"><SelectValue /></SelectTrigger>
              <SelectContent>
                {CONDITIONS.map((x) => <SelectItem key={x} value={x}>{t(x)}</SelectItem>)}
              </SelectContent>
            </Select>
          </div>
          <div>
            <Label className="text-xs font-bold">{t("Anti-Skid Status")}</Label>
            <Select value={value.anti_skid_status || "Present"} onValueChange={(v) => set("anti_skid_status", v)}>
              <SelectTrigger data-testid="rp-antiskid"><SelectValue /></SelectTrigger>
              <SelectContent>
                <SelectItem value="Present">{t("Present")}</SelectItem>
                <SelectItem value="Worn">{t("Worn")}</SelectItem>
                <SelectItem value="Missing">{t("Missing")}</SelectItem>
                <SelectItem value="N/A">{t("N/A")}</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </>
      )}
    </div>
  );
}

export function CreateAssetDialog({ open, onOpenChange, onCreated }) {
  const { t } = useT();
  const [value, setValue] = useState({ asset_type: "Trench Box", condition: "Good" });
  const [saving, setSaving] = useState(false);
  // Phase 8A — when the dialog opens or the asset_type changes, fetch a
  // suggested permanent asset_id from the backend (RP-001, TB-08, etc.).
  // The user can still type their own value; the suggestion is just a
  // calm default so road plates flow as RP-001, RP-002, … automatically.
  useEffect(() => {
    if (!open) return;
    let cancelled = false;
    (async () => {
      try {
        const r = await api.get("/trench-safety/assets/next-id", { params: { asset_type: value.asset_type } });
        if (!cancelled && r.data?.next_id) {
          setValue((v) => (v.asset_id ? v : { ...v, asset_id: r.data.next_id }));
        }
      } catch { /* swallow — user can type their own */ }
    })();
    return () => { cancelled = true; };
  }, [open, value.asset_type]);
  async function save() {
    if (!value.asset_id || !value.asset_type) {
      toast.error(t("Asset ID and Asset Type are required."));
      return;
    }
    setSaving(true);
    try {
      const r = await api.post("/trench-safety/assets", value);
      toast.success(t("Asset created."));
      onOpenChange(false);
      onCreated?.(r.data);
      setValue({ asset_type: "Trench Box", condition: "Good" });
    } catch (e) {
      toast.error(extractErr(e, t("Create failed.")));
    } finally {
      setSaving(false);
    }
  }
  // Reset suggested id when user changes the type so the prefix refreshes.
  const onTypeChange = (next) => {
    setValue((v) => ({ ...v, asset_type: next, asset_id: "" }));
  };
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-2xl" data-testid="create-asset-dialog">
        <DialogHeader>
          <DialogTitle>{t("Create Trench Safety Asset")}</DialogTitle>
        </DialogHeader>
        <div className="text-xs text-slate-600 -mt-2 mb-2">
          {t("Asset ID is permanent. Suggested IDs follow the certified registry — TB-XX, RP-001, EP-001, etc.")}
        </div>
        <AssetForm value={value} onChange={(next) => {
          // Intercept asset_type changes to reseed the suggested ID
          if (next.asset_type !== value.asset_type) onTypeChange(next.asset_type);
          else setValue(next);
        }} isEdit={false} />
        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)} data-testid="create-asset-cancel">{t("Cancel")}</Button>
          <Button onClick={save} disabled={saving} className="bg-cyan-700 hover:bg-cyan-800" data-testid="create-asset-save">
            {saving ? <Loader2 className="w-4 h-4 animate-spin" /> : t("Create Asset")}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

export function EditAssetDialog({ open, onOpenChange, asset, onSaved }) {
  const { t } = useT();
  // Reset internal form state every time the dialog re-opens with a fresh asset
  // by mounting an inner component under a stable key. Avoids set-state-in-effect.
  if (!open || !asset) return null;
  return (
    <EditAssetDialogInner
      key={`edit-${asset.asset_id}`}
      asset={asset}
      onOpenChange={onOpenChange}
      onSaved={onSaved}
    />
  );
}

function EditAssetDialogInner({ asset, onOpenChange, onSaved }) {
  const { t } = useT();
  const [value, setValue] = useState(asset || {});
  const [saving, setSaving] = useState(false);
  async function save() {
    setSaving(true);
    try {
      const payload = { ...value };
      delete payload.asset_id; // immutable
      const r = await api.put(`/trench-safety/assets/${asset.asset_id}`, payload);
      toast.success(t("Asset updated."));
      onOpenChange(false);
      onSaved?.(r.data);
    } catch (e) {
      toast.error(extractErr(e, t("Save failed.")));
    } finally { setSaving(false); }
  }
  if (!asset) return null;
  return (
    <Dialog open={true} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-2xl" data-testid="edit-asset-dialog">
        <DialogHeader>
          <DialogTitle>{t("Edit Asset")} · {asset.asset_id}</DialogTitle>
        </DialogHeader>
        <AssetForm value={value} onChange={setValue} isEdit />
        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)} data-testid="edit-asset-cancel">{t("Cancel")}</Button>
          <Button onClick={save} disabled={saving} className="bg-cyan-700 hover:bg-cyan-800" data-testid="edit-asset-save">
            {saving ? <Loader2 className="w-4 h-4 animate-spin" /> : t("Save Changes")}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

export function RetireAssetDialog({ open, onOpenChange, asset, onRetired }) {
  const { t } = useT();
  const [reason, setReason] = useState("");
  const [saving, setSaving] = useState(false);
  async function go() {
    setSaving(true);
    try {
      await api.post(`/trench-safety/assets/${asset.asset_id}/retire`, { reason });
      toast.success(t("Asset retired."));
      onOpenChange(false);
      onRetired?.();
    } catch (e) {
      toast.error(extractErr(e, t("Retire failed.")));
    } finally { setSaving(false); }
  }
  if (!asset) return null;
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent data-testid="retire-asset-dialog">
        <DialogHeader>
          <DialogTitle>{t("Retire Asset")} · {asset.asset_id}</DialogTitle>
        </DialogHeader>
        <div className="bg-red-50 border-2 border-red-300 rounded p-3 text-sm text-red-900">
          <strong>{t("Retirement is terminal.")}</strong>{" "}
          {t("The asset will be removed from active service. Reactivation requires an admin edit.")}
        </div>
        <div>
          <Label className="text-xs font-bold">{t("Reason")}</Label>
          <Textarea value={reason} onChange={(e) => setReason(e.target.value)} rows={3} data-testid="retire-reason" />
        </div>
        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)}>{t("Cancel")}</Button>
          <Button onClick={go} disabled={saving} className="bg-red-700 hover:bg-red-800 text-white" data-testid="retire-confirm">
            {saving ? <Loader2 className="w-4 h-4 animate-spin" /> : t("Retire Asset")}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

export function StatusChangeDialog({ open, onOpenChange, asset, onChanged }) {
  const { t } = useT();
  const [target, setTarget] = useState("Available");
  const [reason, setReason] = useState("");
  const [saving, setSaving] = useState(false);
  async function go() {
    setSaving(true);
    try {
      await api.post(`/trench-safety/assets/${asset.asset_id}/status`, { operational_status: target, reason });
      toast.success(t("Status updated."));
      onOpenChange(false);
      onChanged?.();
    } catch (e) {
      toast.error(extractErr(e, t("Status change failed.")));
    } finally { setSaving(false); }
  }
  if (!asset) return null;
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent data-testid="status-change-dialog">
        <DialogHeader>
          <DialogTitle>{t("Change Status")} · {asset.asset_id}</DialogTitle>
        </DialogHeader>
        <div className="text-xs text-slate-600">
          {t("Current status:")} <strong>{t(asset.operational_status)}</strong>.{" "}
          {t("Status changes are validated against the lifecycle engine — holds cannot be cleared directly through status changes.")}
        </div>
        <div>
          <Label className="text-xs font-bold">{t("New Status")}</Label>
          <Select value={target} onValueChange={setTarget}>
            <SelectTrigger data-testid="status-target"><SelectValue /></SelectTrigger>
            <SelectContent>
              {STATUSES.map((x) => <SelectItem key={x} value={x}>{t(x)}</SelectItem>)}
            </SelectContent>
          </Select>
        </div>
        <div>
          <Label className="text-xs font-bold">{t("Reason")}</Label>
          <Textarea value={reason} onChange={(e) => setReason(e.target.value)} rows={2} data-testid="status-reason" />
        </div>
        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)}>{t("Cancel")}</Button>
          <Button onClick={go} disabled={saving} className="bg-cyan-700 hover:bg-cyan-800" data-testid="status-save">
            {saving ? <Loader2 className="w-4 h-4 animate-spin" /> : t("Apply Status")}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

// ═════════════════════════════════════════════════════════════════════
// Holds · Open / Clear · Panel
// ═════════════════════════════════════════════════════════════════════
export function OpenHoldDialog({ open, onOpenChange, asset, onOpened }) {
  const { t } = useT();
  const [kind, setKind] = useState("Inspection Hold");
  const [reason, setReason] = useState("");
  const [saving, setSaving] = useState(false);
  async function go() {
    setSaving(true);
    try {
      await api.post(`/trench-safety/assets/${asset.asset_id}/holds`, { kind, reason, source: "manual" });
      toast.success(t("Hold opened."));
      onOpenChange(false);
      onOpened?.();
    } catch (e) {
      toast.error(extractErr(e, t("Open hold failed.")));
    } finally { setSaving(false); }
  }
  if (!asset) return null;
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent data-testid="open-hold-dialog">
        <DialogHeader><DialogTitle>{t("Open Hold")} · {asset.asset_id}</DialogTitle></DialogHeader>
        <div>
          <Label className="text-xs font-bold">{t("Hold Type")}</Label>
          <Select value={kind} onValueChange={setKind}>
            <SelectTrigger data-testid="hold-kind"><SelectValue /></SelectTrigger>
            <SelectContent>
              {HOLD_KINDS.map((k) => <SelectItem key={k} value={k}>{t(k)}</SelectItem>)}
            </SelectContent>
          </Select>
        </div>
        <div>
          <Label className="text-xs font-bold">{t("Reason")} *</Label>
          <Textarea value={reason} onChange={(e) => setReason(e.target.value)} rows={2} data-testid="hold-reason" />
        </div>
        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)}>{t("Cancel")}</Button>
          <Button onClick={go} disabled={saving || !reason.trim()} className="bg-amber-600 hover:bg-amber-700" data-testid="hold-open-save">
            {saving ? <Loader2 className="w-4 h-4 animate-spin" /> : t("Open Hold")}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

export function ClearHoldDialog({ open, onOpenChange, hold, assetId, onCleared }) {
  const { t } = useT();
  const [reason, setReason] = useState("");
  const [saving, setSaving] = useState(false);
  async function go() {
    setSaving(true);
    try {
      await api.post(`/trench-safety/assets/${assetId}/holds/${hold.id}/clear`, { clear_reason: reason });
      toast.success(t("Hold cleared."));
      onOpenChange(false);
      onCleared?.();
    } catch (e) {
      toast.error(extractErr(e, t("Clear hold failed.")));
    } finally { setSaving(false); }
  }
  if (!hold) return null;
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent data-testid="clear-hold-dialog">
        <DialogHeader><DialogTitle>{t("Clear Hold")} · {t(hold.kind)}</DialogTitle></DialogHeader>
        <div className="text-xs text-slate-600">
          <strong>{t("Opened:")}</strong> {hold.opened_at?.slice(0, 16)} · {hold.opened_by}<br />
          <strong>{t("Original reason:")}</strong> {hold.reason}
        </div>
        <div>
          <Label className="text-xs font-bold">{t("Release reason")} *</Label>
          <Textarea value={reason} onChange={(e) => setReason(e.target.value)} rows={2} data-testid="clear-reason" />
        </div>
        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)}>{t("Cancel")}</Button>
          <Button onClick={go} disabled={saving || !reason.trim()} className="bg-emerald-700 hover:bg-emerald-800" data-testid="clear-hold-save">
            {saving ? <Loader2 className="w-4 h-4 animate-spin" /> : t("Release Hold")}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

export function HoldsPanel({ asset, onChange }) {
  const { t } = useT();
  const [holds, setHolds] = useState([]);
  const [loading, setLoading] = useState(true);
  const [openOpen, setOpenOpen] = useState(false);
  const [clearOpen, setClearOpen] = useState(null);
  const [reloadKey, setReloadKey] = useState(0);
  useEffect(() => {
    let cancelled = false;
    (async () => {
      setLoading(true);
      try {
        const r = await api.get(`/trench-safety/assets/${asset.asset_id}/holds`, { params: { is_active: true } });
        if (!cancelled) setHolds(r.data?.items || []);
      } catch { /* swallow */ }
      finally { if (!cancelled) setLoading(false); }
    })();
    return () => { cancelled = true; };
  }, [asset.asset_id, reloadKey]);
  const refresh = () => { setReloadKey((k) => k + 1); onChange?.(); };
  return (
    <section className="bg-white border border-slate-200 rounded-md p-4" data-testid="holds-panel">
      <div className="flex items-center justify-between mb-2">
        <div className="font-mono text-[10px] uppercase tracking-[0.18em] text-cyan-700 font-bold inline-flex items-center gap-1">
          <ShieldAlert className="w-3.5 h-3.5" /> {t("Holds")}
        </div>
        <Button size="sm" variant="outline" onClick={() => setOpenOpen(true)} data-testid="open-hold-btn">
          <Plus className="w-3 h-3 mr-1" /> {t("Open Hold")}
        </Button>
      </div>
      {loading ? (
        <div className="text-xs text-slate-400 py-2">{t("Loading holds…")}</div>
      ) : holds.length === 0 ? (
        <div className="text-xs text-slate-400 py-2" data-testid="holds-empty">{t("No active holds.")}</div>
      ) : (
        <ul className="divide-y divide-slate-100">
          {holds.map((h) => (
            <li key={h.id} className="py-2 flex items-start justify-between gap-3" data-testid={`hold-row-${h.kind.replace(/\s/g, "-")}`}>
              <div className="flex-1">
                <div className="font-bold text-amber-900 text-sm">{t(h.kind)}</div>
                <div className="text-xs text-slate-700">{h.reason}</div>
                <div className="text-[10px] uppercase tracking-[0.14em] text-slate-500 font-mono mt-0.5">
                  {h.opened_at?.slice(0, 16)} · {h.source}
                </div>
              </div>
              <Button size="sm" variant="outline" onClick={() => setClearOpen(h)} data-testid={`clear-hold-${h.kind.replace(/\s/g, "-")}`}>
                <CheckCircle2 className="w-3 h-3 mr-1" /> {t("Release")}
              </Button>
            </li>
          ))}
        </ul>
      )}
      <OpenHoldDialog open={openOpen} onOpenChange={setOpenOpen} asset={asset} onOpened={refresh} />
      <ClearHoldDialog open={Boolean(clearOpen)} onOpenChange={(v) => !v && setClearOpen(null)} hold={clearOpen} assetId={asset.asset_id} onCleared={refresh} />
    </section>
  );
}

// ═════════════════════════════════════════════════════════════════════
// Inspections
// ═════════════════════════════════════════════════════════════════════
export function CreateInspectionDialog({ open, onOpenChange, asset, onCreated }) {
  if (!open || !asset) return null;
  return (
    <CreateInspectionDialogInner
      key={`insp-${asset.asset_id}`}
      asset={asset}
      onOpenChange={onOpenChange}
      onCreated={onCreated}
    />
  );
}

function CreateInspectionDialogInner({ asset, onOpenChange, onCreated }) {
  const { t } = useT();
  const isRoadPlate = (asset?.asset_type || "") === "Road Plate";
  const [form, setForm] = useState(() => ({
    inspection_type: "Daily Visual",
    result: "Pass",
    severity: "Minor",
    inspector_name: "",
    findings: "",
    corrective_actions: "",
    competent_person_confirmed: false,
    checklist: isRoadPlate
      ? ROAD_PLATE_CHECKLIST.map((c) => ({ key: c.key, label: c.label, result: "Pass", note: "" }))
      : [],
  }));
  const setChecklistItem = (idx, patch) => {
    setForm((f) => {
      const next = [...(f.checklist || [])];
      next[idx] = { ...next[idx], ...patch };
      return { ...f, checklist: next };
    });
  };
  const [saving, setSaving] = useState(false);
  async function go() {
    if (!form.inspector_name.trim()) {
      toast.error(t("Inspector name is required."));
      return;
    }
    if (
      (form.inspection_type === "Monthly Competent Person" || form.inspection_type === "Annual Review")
      && !form.competent_person_confirmed
    ) {
      toast.error(t("Competent person confirmation is required for this inspection type."));
      return;
    }
    setSaving(true);
    try {
      const payload = {
        inspection_type: form.inspection_type,
        inspector_name: form.inspector_name,
        result: form.result,
        severity: form.result === "Fail" ? form.severity : "None",
        competent_person_confirmed: Boolean(form.competent_person_confirmed),
        checklist: form.checklist,
        findings: form.findings,
        corrective_actions: form.corrective_actions,
      };
      await api.post(`/trench-safety/assets/${asset.asset_id}/inspections`, payload);
      toast.success(t("Inspection recorded."));
      onOpenChange(false);
      onCreated?.();
    } catch (e) {
      toast.error(extractErr(e, t("Inspection failed.")));
    } finally { setSaving(false); }
  }
  return (
    <Dialog open={true} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto" data-testid="create-inspection-dialog">
        <DialogHeader><DialogTitle>{t("Record Inspection")} · {asset.asset_id}</DialogTitle></DialogHeader>
        <div className="grid grid-cols-2 gap-3">
          <div>
            <Label className="text-xs font-bold">{t("Type")}</Label>
            <Select value={form.inspection_type} onValueChange={(v) => setForm({ ...form, inspection_type: v })}>
              <SelectTrigger data-testid="insp-type"><SelectValue /></SelectTrigger>
              <SelectContent>{INSPECTION_TYPES.map((x) => <SelectItem key={x} value={x}>{t(x)}</SelectItem>)}</SelectContent>
            </Select>
          </div>
          <div>
            <Label className="text-xs font-bold">{t("Result")}</Label>
            <Select value={form.result} onValueChange={(v) => setForm({ ...form, result: v })}>
              <SelectTrigger data-testid="insp-result"><SelectValue /></SelectTrigger>
              <SelectContent>{INSPECTION_RESULTS.map((x) => <SelectItem key={x} value={x}>{t(x)}</SelectItem>)}</SelectContent>
            </Select>
          </div>
          {form.result === "Fail" && (
            <div>
              <Label className="text-xs font-bold">{t("Severity")}</Label>
              <Select value={form.severity} onValueChange={(v) => setForm({ ...form, severity: v })}>
                <SelectTrigger data-testid="insp-severity"><SelectValue /></SelectTrigger>
                <SelectContent>{SEVERITIES.map((x) => <SelectItem key={x} value={x}>{t(x)}</SelectItem>)}</SelectContent>
              </Select>
            </div>
          )}
          <div className={form.result === "Fail" ? "" : "col-span-2"}>
            <Label className="text-xs font-bold">{t("Inspector Name")} *</Label>
            <Input value={form.inspector_name} onChange={(e) => setForm({ ...form, inspector_name: e.target.value })} data-testid="insp-inspector" />
          </div>
          {(form.inspection_type === "Monthly Competent Person" || form.inspection_type === "Annual Review") && (
            <div className="col-span-2 flex items-center gap-2">
              <input
                type="checkbox"
                id="cp-confirm"
                checked={Boolean(form.competent_person_confirmed)}
                onChange={(e) => setForm({ ...form, competent_person_confirmed: e.target.checked })}
                data-testid="insp-competent"
              />
              <Label htmlFor="cp-confirm" className="text-xs">{t("I am the designated competent person for this inspection.")}</Label>
            </div>
          )}
        </div>

        {isRoadPlate && (
          <div className="mt-2 border-t pt-3" data-testid="rp-checklist">
            <div className="font-mono text-[10px] uppercase tracking-[0.18em] text-cyan-700 font-bold mb-2">
              {t("Road Plate · Inspection Checklist")}
            </div>
            <ul className="space-y-1.5 max-h-60 overflow-y-auto pr-1">
              {form.checklist.map((item, idx) => (
                <li key={item.key} className="grid grid-cols-12 items-center gap-2 text-sm" data-testid={`rp-checklist-row-${item.key}`}>
                  <div className="col-span-7 text-slate-800">{t(item.label)}</div>
                  <div className="col-span-5">
                    <Select value={item.result} onValueChange={(v) => setChecklistItem(idx, { result: v })}>
                      <SelectTrigger className="h-8" data-testid={`rp-checklist-${item.key}`}><SelectValue /></SelectTrigger>
                      <SelectContent>
                        <SelectItem value="Pass">{t("Pass")}</SelectItem>
                        <SelectItem value="Fail">{t("Fail")}</SelectItem>
                        <SelectItem value="N/A">{t("N/A")}</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                </li>
              ))}
            </ul>
          </div>
        )}

        <div className="grid grid-cols-1 gap-3 mt-2">
          <div>
            <Label className="text-xs font-bold">{t("Findings")}</Label>
            <Textarea value={form.findings} onChange={(e) => setForm({ ...form, findings: e.target.value })} rows={2} data-testid="insp-notes" />
          </div>
          {form.result === "Fail" && (
            <div>
              <Label className="text-xs font-bold">{t("Corrective Actions")}</Label>
              <Textarea value={form.corrective_actions} onChange={(e) => setForm({ ...form, corrective_actions: e.target.value })} rows={2} data-testid="insp-corrective" />
            </div>
          )}
        </div>

        <div className="bg-amber-50 border border-amber-300 rounded p-2 text-xs text-amber-900">
          <AlertTriangle className="w-3 h-3 inline -mt-0.5 mr-1" />
          {t("A Fail with Major or Critical severity automatically opens an Inspection Hold and stubs a repair recommendation.")}
        </div>
        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)}>{t("Cancel")}</Button>
          <Button onClick={go} disabled={saving} className="bg-cyan-700 hover:bg-cyan-800" data-testid="insp-save">
            {saving ? <Loader2 className="w-4 h-4 animate-spin" /> : t("Record Inspection")}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

export function InspectionsPanel({ asset, onChange }) {
  const { t } = useT();
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [createOpen, setCreateOpen] = useState(false);
  const [reloadKey, setReloadKey] = useState(0);
  useEffect(() => {
    let cancelled = false;
    (async () => {
      setLoading(true);
      try {
        const r = await api.get(`/trench-safety/assets/${asset.asset_id}/inspections`, { params: { limit: 25 } });
        if (!cancelled) setItems(r.data?.items || []);
      } catch { /* swallow */ }
      finally { if (!cancelled) setLoading(false); }
    })();
    return () => { cancelled = true; };
  }, [asset.asset_id, reloadKey]);
  const refresh = () => { setReloadKey((k) => k + 1); onChange?.(); };
  return (
    <section className="bg-white border border-slate-200 rounded-md p-4" data-testid="inspections-panel">
      <div className="flex items-center justify-between mb-2">
        <div className="font-mono text-[10px] uppercase tracking-[0.18em] text-cyan-700 font-bold inline-flex items-center gap-1">
          <FileText className="w-3.5 h-3.5" /> {t("Inspections")}
        </div>
        <Button size="sm" variant="outline" onClick={() => setCreateOpen(true)} data-testid="create-inspection-btn">
          <Plus className="w-3 h-3 mr-1" /> {t("Record Inspection")}
        </Button>
      </div>
      {loading ? (
        <div className="text-xs text-slate-400 py-2">{t("Loading…")}</div>
      ) : items.length === 0 ? (
        <div className="text-xs text-slate-400 py-2" data-testid="inspections-empty">{t("No inspections yet.")}</div>
      ) : (
        <ul className="divide-y divide-slate-100 text-sm">
          {items.map((i) => (
            <li key={i.id} className="py-2" data-testid={`insp-row-${i.id}`}>
              <div className="flex items-center gap-2">
                <span className="font-bold text-slate-900">{t(i.inspection_type)}</span>
                <span className={i.result === "Fail" ? "text-red-700 font-bold" : "text-emerald-700 font-bold"}>{t(i.result)}</span>
                <span className="text-xs text-slate-500">· {t(i.severity)}</span>
              </div>
              <div className="text-xs text-slate-600">{i.notes || "—"}</div>
              <div className="text-[10px] uppercase tracking-[0.14em] text-slate-500 font-mono mt-0.5">
                {i.submitted_at?.slice(0, 16)} · {i.inspector_name}
              </div>
            </li>
          ))}
        </ul>
      )}
      <CreateInspectionDialog open={createOpen} onOpenChange={setCreateOpen} asset={asset} onCreated={refresh} />
    </section>
  );
}

// ═════════════════════════════════════════════════════════════════════
// Certifications
// ═════════════════════════════════════════════════════════════════════
export function UploadCertificationDialog({ open, onOpenChange, asset, onUploaded }) {
  const { t } = useT();
  const today = new Date().toISOString().slice(0, 10);
  const [form, setForm] = useState({ kind: "Annual Inspection", issuer: "", issued_at: today, expires_at: "", notes: "" });
  const [saving, setSaving] = useState(false);
  async function go() {
    if (!form.expires_at) { toast.error(t("Expires date is required.")); return; }
    if (!form.issuer.trim()) { toast.error(t("Issuer is required.")); return; }
    setSaving(true);
    try {
      await api.post(`/trench-safety/assets/${asset.asset_id}/certifications`, form);
      toast.success(t("Certification uploaded."));
      onOpenChange(false);
      onUploaded?.();
    } catch (e) {
      toast.error(extractErr(e, t("Upload failed.")));
    } finally { setSaving(false); }
  }
  if (!asset) return null;
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent data-testid="upload-cert-dialog">
        <DialogHeader><DialogTitle>{t("Upload Certification")} · {asset.asset_id}</DialogTitle></DialogHeader>
        <div className="grid grid-cols-2 gap-3">
          <div className="col-span-2">
            <Label className="text-xs font-bold">{t("Certification Type")}</Label>
            <Select value={form.kind} onValueChange={(v) => setForm({ ...form, kind: v })}>
              <SelectTrigger data-testid="cert-type"><SelectValue /></SelectTrigger>
              <SelectContent>{CERTIFICATION_KINDS.map((k) => <SelectItem key={k} value={k}>{t(k)}</SelectItem>)}</SelectContent>
            </Select>
          </div>
          <div>
            <Label className="text-xs font-bold">{t("Issued At")}</Label>
            <Input type="date" value={form.issued_at} onChange={(e) => setForm({ ...form, issued_at: e.target.value })} data-testid="cert-issued" />
          </div>
          <div>
            <Label className="text-xs font-bold">{t("Expires At")} *</Label>
            <Input type="date" value={form.expires_at} onChange={(e) => setForm({ ...form, expires_at: e.target.value })} data-testid="cert-expires" />
          </div>
          <div className="col-span-2">
            <Label className="text-xs font-bold">{t("Issuer")} *</Label>
            <Input value={form.issuer} onChange={(e) => setForm({ ...form, issuer: e.target.value })} data-testid="cert-issuer" />
          </div>
          <div className="col-span-2">
            <Label className="text-xs font-bold">{t("Notes")}</Label>
            <Textarea value={form.notes} onChange={(e) => setForm({ ...form, notes: e.target.value })} rows={2} data-testid="cert-notes" />
          </div>
        </div>
        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)}>{t("Cancel")}</Button>
          <Button onClick={go} disabled={saving} className="bg-cyan-700 hover:bg-cyan-800" data-testid="cert-save">
            {saving ? <Loader2 className="w-4 h-4 animate-spin" /> : t("Upload Certification")}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

function certBadge(c, t) {
  if (!c.expires_at) return { label: t("OK"), cls: "bg-emerald-50 text-emerald-800 border-emerald-300" };
  const days = Math.floor((new Date(c.expires_at).getTime() - Date.now()) / 86400000);
  if (c.status === "Revoked") return { label: t("Revoked"), cls: "bg-slate-100 text-slate-600 border-slate-300" };
  if (days < 0)   return { label: t("Expired"),  cls: "bg-red-50 text-red-800 border-red-400" };
  if (days <= 90) return { label: t("Due Soon"), cls: "bg-amber-50 text-amber-800 border-amber-400" };
  return { label: t("OK"), cls: "bg-emerald-50 text-emerald-800 border-emerald-300" };
}

export function CertificationsPanel({ asset, onChange }) {
  const { t } = useT();
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [openUpload, setOpenUpload] = useState(false);
  const [reloadKey, setReloadKey] = useState(0);
  useEffect(() => {
    let cancelled = false;
    (async () => {
      setLoading(true);
      try {
        const r = await api.get(`/trench-safety/assets/${asset.asset_id}/certifications`, { params: { limit: 25 } });
        if (!cancelled) setItems(r.data?.items || []);
      } catch { /* swallow */ }
      finally { if (!cancelled) setLoading(false); }
    })();
    return () => { cancelled = true; };
  }, [asset.asset_id, reloadKey]);
  const refresh = () => { setReloadKey((k) => k + 1); onChange?.(); };
  async function revoke(c) {
    const reason = window.prompt(t("Reason for revoking this certification?"));
    if (!reason) return;
    try {
      await api.post(`/trench-safety/assets/${asset.asset_id}/certifications/${c.id}/revoke`, { reason });
      toast.success(t("Certification revoked."));
      refresh();
    } catch (e) { toast.error(extractErr(e, t("Revoke failed."))); }
  }
  return (
    <section className="bg-white border border-slate-200 rounded-md p-4" data-testid="certifications-panel">
      <div className="flex items-center justify-between mb-2">
        <div className="font-mono text-[10px] uppercase tracking-[0.18em] text-cyan-700 font-bold inline-flex items-center gap-1">
          <Calendar className="w-3.5 h-3.5" /> {t("Certifications")}
        </div>
        <Button size="sm" variant="outline" onClick={() => setOpenUpload(true)} data-testid="upload-cert-btn">
          <Plus className="w-3 h-3 mr-1" /> {t("Upload")}
        </Button>
      </div>
      {loading ? (
        <div className="text-xs text-slate-400 py-2">{t("Loading…")}</div>
      ) : items.length === 0 ? (
        <div className="text-xs text-slate-400 py-2" data-testid="certs-empty">{t("No certifications on file.")}</div>
      ) : (
        <ul className="divide-y divide-slate-100 text-sm">
          {items.map((c) => {
            const b = certBadge(c, t);
            return (
              <li key={c.id} className="py-2 flex items-start justify-between gap-2" data-testid={`cert-row-${c.id}`}>
                <div className="flex-1">
                  <div className="flex items-center gap-2">
                    <span className="font-bold text-slate-900">{c.kind || c.certification_type}</span>
                    <span className={`px-2 py-0.5 rounded border text-[10px] font-bold uppercase tracking-[0.08em] ${b.cls}`}>
                      {b.label}
                    </span>
                  </div>
                  <div className="text-xs text-slate-600">
                    {t("Expires")}: <span className="font-mono">{c.expires_at?.slice(0, 10) || "—"}</span>
                    {c.issuer ? ` · ${c.issuer}` : ""}
                  </div>
                </div>
                {c.status === "Active" && (
                  <Button size="sm" variant="outline" onClick={() => revoke(c)} data-testid={`cert-revoke-${c.id}`}>
                    <Trash2 className="w-3 h-3 mr-1" /> {t("Revoke")}
                  </Button>
                )}
              </li>
            );
          })}
        </ul>
      )}
      <UploadCertificationDialog open={openUpload} onOpenChange={setOpenUpload} asset={asset} onUploaded={refresh} />
    </section>
  );
}

// ═════════════════════════════════════════════════════════════════════
// Audit Timeline
// ═════════════════════════════════════════════════════════════════════
export function AuditTimelinePanel({ asset }) {
  const { t } = useT();
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  useEffect(() => {
    let cancelled = false;
    (async () => {
      setLoading(true);
      try {
        const r = await api.get(`/trench-safety/assets/${asset.asset_id}/audit`, { params: { limit: 100 } });
        if (!cancelled) setItems(r.data?.items || []);
      } catch { /* swallow */ }
      finally { if (!cancelled) setLoading(false); }
    })();
    return () => { cancelled = true; };
  }, [asset.asset_id]);
  return (
    <section className="bg-white border border-slate-200 rounded-md p-4" data-testid="audit-panel">
      <div className="font-mono text-[10px] uppercase tracking-[0.18em] text-cyan-700 font-bold inline-flex items-center gap-1 mb-2">
        <History className="w-3.5 h-3.5" /> {t("Activity Timeline")}
      </div>
      {loading ? (
        <div className="text-xs text-slate-400 py-2">{t("Loading timeline…")}</div>
      ) : items.length === 0 ? (
        <div className="text-xs text-slate-400 py-2" data-testid="audit-empty">{t("No audit events on file.")}</div>
      ) : (
        <ol className="relative border-l-2 border-slate-200 pl-4 ml-1">
          {items.map((ev) => (
            <li key={ev.id} className="mb-3" data-testid={`audit-row-${ev.id}`}>
              <span className="absolute -left-[7px] w-3 h-3 rounded-full bg-cyan-600 border-2 border-white" />
              <div className="font-bold text-sm text-slate-900">{ev.kind?.replace(/_/g, " ")}</div>
              <div className="text-[10px] uppercase tracking-[0.14em] font-mono text-slate-500">
                {ev.ts?.slice(0, 16)} · {ev.actor}
              </div>
              {ev.detail && Object.keys(ev.detail).length > 0 && (
                <details className="text-xs text-slate-600 mt-0.5">
                  <summary className="cursor-pointer">{t("details")}</summary>
                  <pre className="bg-slate-50 p-2 rounded mt-1 overflow-x-auto text-[10px]">{JSON.stringify(ev.detail, null, 2)}</pre>
                </details>
              )}
            </li>
          ))}
        </ol>
      )}
    </section>
  );
}
