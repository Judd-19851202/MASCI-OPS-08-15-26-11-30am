// Trench Safety — Assign / Return modal components.
//
// Phase 4A · Equipment Inventory + Operations Integration.
// These are admin-gated dialogs that drive the canonical
// `/api/trench-safety/assets/{id}/assign` and `/return` endpoints.
//
// No mock data, no dummy projects — the user enters the project
// the asset is going to (Project # / Project Name / Superintendent /
// Foreman) and the backend records a real deployment row, updates
// the asset's current_project_*, and mirrors to equipment_master.
import React, { useState } from "react";
import {
  Dialog,
  DialogContent,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Loader2 } from "lucide-react";
import { api } from "@/lib/api";
import { toast } from "sonner";
import { useT } from "@/lib/i18n";

const CONDITION_OPTIONS = ["Excellent", "Good", "Fair", "Poor", "Out Of Service"];
const SOURCE_OPTIONS = [
  "Manual Assignment",
  "Daily Report",
  "Project Equipment List",
  "Dispatch / Transport Log",
  "Admin Adjustment",
];

export function AssignToProjectDialog({ open, onOpenChange, asset, onAssigned }) {
  const { t } = useT();
  const [form, setForm] = useState({
    project_number: "",
    project_name: "",
    superintendent: "",
    foreman: "",
    assigned_by: "",
    condition_at_assign: asset?.condition || "Good",
    source: "Manual Assignment",
    notes: "",
  });
  const [busy, setBusy] = useState(false);

  const set = (k, v) => setForm((f) => ({ ...f, [k]: v }));

  const submit = async (e) => {
    e?.preventDefault?.();
    if (!form.project_name.trim()) {
      toast.error(t("Project Name is required"));
      return;
    }
    setBusy(true);
    try {
      const payload = {
        // Backend requires project_id + project_name. Mirror project_number
        // → project_id so it round-trips cleanly when no separate UUID is
        // supplied (operators identify projects by job # in the field).
        project_id: form.project_number.trim() || form.project_name.trim(),
        project_number: form.project_number.trim() || null,
        project_name: form.project_name.trim(),
        superintendent: form.superintendent.trim() || null,
        foreman: form.foreman.trim() || null,
        assigned_by: form.assigned_by.trim() || null,
        condition_at_assign: form.condition_at_assign || null,
        source: form.source,
        notes: form.notes.trim() || null,
      };
      const res = await api.post(
        `/trench-safety/assets/${encodeURIComponent(asset.asset_id)}/assign`,
        payload
      );
      toast.success(t("Assigned to ") + payload.project_name);
      onAssigned?.(res.data);
      onOpenChange(false);
    } catch (err) {
      toast.error(err?.response?.data?.detail || t("Assign failed"));
    } finally {
      setBusy(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-2xl" data-testid="assign-dialog">
        <DialogHeader>
          <DialogTitle className="font-display font-black text-xl">
            {t("Assign to Project")} · <span className="font-mono">{asset?.asset_id}</span>
          </DialogTitle>
          <DialogDescription>
            {t("Records a real deployment. The asset becomes Assigned and appears on the project dashboard.")}
          </DialogDescription>
        </DialogHeader>

        <form onSubmit={submit} className="grid grid-cols-1 md:grid-cols-2 gap-x-6 gap-y-4">
          <div>
            <Label className="font-mono text-[10px] uppercase tracking-[0.18em] text-slate-600">
              {t("Project Number")}
            </Label>
            <Input
              value={form.project_number}
              onChange={(e) => set("project_number", e.target.value)}
              placeholder="e.g. 24-118"
              data-testid="assign-project-number"
            />
          </div>
          <div>
            <Label className="font-mono text-[10px] uppercase tracking-[0.18em] text-slate-600">
              {t("Project Name")} <span className="text-red-600">*</span>
            </Label>
            <Input
              value={form.project_name}
              onChange={(e) => set("project_name", e.target.value)}
              placeholder="NSB Airport"
              required
              data-testid="assign-project-name"
            />
          </div>
          <div>
            <Label className="font-mono text-[10px] uppercase tracking-[0.18em] text-slate-600">
              {t("Superintendent")}
            </Label>
            <Input
              value={form.superintendent}
              onChange={(e) => set("superintendent", e.target.value)}
              placeholder="Jaymn Judd"
              data-testid="assign-superintendent"
            />
          </div>
          <div>
            <Label className="font-mono text-[10px] uppercase tracking-[0.18em] text-slate-600">
              {t("Foreman")}
            </Label>
            <Input
              value={form.foreman}
              onChange={(e) => set("foreman", e.target.value)}
              data-testid="assign-foreman"
            />
          </div>
          <div>
            <Label className="font-mono text-[10px] uppercase tracking-[0.18em] text-slate-600">
              {t("Assigned By")}
            </Label>
            <Input
              value={form.assigned_by}
              onChange={(e) => set("assigned_by", e.target.value)}
              placeholder={t("Your name")}
              data-testid="assign-assigned-by"
            />
          </div>
          <div>
            <Label className="font-mono text-[10px] uppercase tracking-[0.18em] text-slate-600">
              {t("Condition at Assignment")}
            </Label>
            <Select
              value={form.condition_at_assign}
              onValueChange={(v) => set("condition_at_assign", v)}
            >
              <SelectTrigger data-testid="assign-condition"><SelectValue /></SelectTrigger>
              <SelectContent>
                {CONDITION_OPTIONS.map((c) => (
                  <SelectItem key={c} value={c}>{t(c)}</SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          <div>
            <Label className="font-mono text-[10px] uppercase tracking-[0.18em] text-slate-600">
              {t("Source")}
            </Label>
            <Select value={form.source} onValueChange={(v) => set("source", v)}>
              <SelectTrigger data-testid="assign-source"><SelectValue /></SelectTrigger>
              <SelectContent>
                {SOURCE_OPTIONS.map((s) => (
                  <SelectItem key={s} value={s}>{t(s)}</SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          <div className="md:col-span-2">
            <Label className="font-mono text-[10px] uppercase tracking-[0.18em] text-slate-600">
              {t("Notes")}
            </Label>
            <Textarea
              value={form.notes}
              onChange={(e) => set("notes", e.target.value)}
              rows={2}
              data-testid="assign-notes"
            />
          </div>

          <DialogFooter className="md:col-span-2 mt-2">
            <Button
              type="button"
              variant="outline"
              onClick={() => onOpenChange(false)}
              disabled={busy}
              data-testid="assign-cancel"
            >
              {t("Cancel")}
            </Button>
            <Button
              type="submit"
              disabled={busy}
              className="bg-cyan-700 hover:bg-cyan-800"
              data-testid="assign-submit"
            >
              {busy ? <Loader2 className="w-4 h-4 mr-2 animate-spin" /> : null}
              {t("Assign")}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}

export function ReturnFromProjectDialog({ open, onOpenChange, asset, onReturned }) {
  const { t } = useT();
  const [form, setForm] = useState({
    returned_by: "",
    condition_at_return: asset?.condition || "Good",
    notes: "",
  });
  const [busy, setBusy] = useState(false);

  const set = (k, v) => setForm((f) => ({ ...f, [k]: v }));

  const submit = async (e) => {
    e?.preventDefault?.();
    setBusy(true);
    try {
      const payload = {
        returned_by: form.returned_by.trim() || null,
        condition_at_return: form.condition_at_return || null,
        notes: form.notes.trim() || null,
      };
      const res = await api.post(
        `/trench-safety/assets/${encodeURIComponent(asset.asset_id)}/return`,
        payload
      );
      toast.success(t("Returned to yard"));
      onReturned?.(res.data);
      onOpenChange(false);
    } catch (err) {
      toast.error(err?.response?.data?.detail || t("Return failed"));
    } finally {
      setBusy(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-lg" data-testid="return-dialog">
        <DialogHeader>
          <DialogTitle className="font-display font-black text-xl">
            {t("Return from Project")} · <span className="font-mono">{asset?.asset_id}</span>
          </DialogTitle>
          <DialogDescription>
            {t("Closes the active deployment and moves the asset back to Available.")}
          </DialogDescription>
        </DialogHeader>

        <form onSubmit={submit} className="space-y-4">
          <div>
            <Label className="font-mono text-[10px] uppercase tracking-[0.18em] text-slate-600">
              {t("Returned By")}
            </Label>
            <Input
              value={form.returned_by}
              onChange={(e) => set("returned_by", e.target.value)}
              placeholder={t("Your name")}
              data-testid="return-returned-by"
            />
          </div>
          <div>
            <Label className="font-mono text-[10px] uppercase tracking-[0.18em] text-slate-600">
              {t("Condition at Return")}
            </Label>
            <Select
              value={form.condition_at_return}
              onValueChange={(v) => set("condition_at_return", v)}
            >
              <SelectTrigger data-testid="return-condition"><SelectValue /></SelectTrigger>
              <SelectContent>
                {CONDITION_OPTIONS.map((c) => (
                  <SelectItem key={c} value={c}>{t(c)}</SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          <div>
            <Label className="font-mono text-[10px] uppercase tracking-[0.18em] text-slate-600">
              {t("Notes")}
            </Label>
            <Textarea
              value={form.notes}
              onChange={(e) => set("notes", e.target.value)}
              rows={2}
              data-testid="return-notes"
            />
          </div>

          <DialogFooter>
            <Button
              type="button"
              variant="outline"
              onClick={() => onOpenChange(false)}
              disabled={busy}
              data-testid="return-cancel"
            >
              {t("Cancel")}
            </Button>
            <Button
              type="submit"
              disabled={busy}
              className="bg-cyan-700 hover:bg-cyan-800"
              data-testid="return-submit"
            >
              {busy ? <Loader2 className="w-4 h-4 mr-2 animate-spin" /> : null}
              {t("Return to Yard")}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
