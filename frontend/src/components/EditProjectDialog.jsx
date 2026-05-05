import React, { useState } from "react";
import { Pencil, Save, X } from "lucide-react";
import { toast } from "sonner";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { JobPicker } from "@/components/JobPicker";
import { api } from "@/lib/api";

/**
 * Re-tag the project on an already-submitted record. Used when a foreman
 * picked the wrong job at submit time and a PM/admin needs to move the
 * report under the right project after the fact.
 *
 * Accepted record kinds (matches backend `_EDIT_KIND_TO_COLL`):
 *   daily-reports · incidents · meetings · inspections · equipment-inspections
 *
 * Only project_name / project_number / project_id / location are touched
 * on the server. Signatures, photos, narrative, checklist results stay
 * exactly as the foreman submitted them.
 */
export function EditProjectDialog({ kind, recordId, current, onSaved }) {
  const [open, setOpen] = useState(false);
  const [job, setJob] = useState({
    project_name: current?.project_name || "",
    project_number: current?.project_number || "",
    project_id: current?.project_id || "",
    location: current?.location || "",
  });
  const [saving, setSaving] = useState(false);

  const handleJobPick = (picked) => {
    // JobPicker `onSelect` receives the full job object.
    setJob((prev) => ({
      ...prev,
      project_name: picked?.project_name || "",
      project_number: picked?.project_number || "",
      project_id: picked?.project_id || picked?.id || "",
      location: picked?.location || picked?.address || prev.location || "",
    }));
  };

  const handleSave = async () => {
    if (!job.project_name?.trim()) {
      toast.error("Project name is required");
      return;
    }
    setSaving(true);
    try {
      const res = await api.patch(
        `/admin/records/${kind}/${recordId}/project`,
        job,
      );
      toast.success("Project updated");
      setOpen(false);
      onSaved?.(res.data?.record);
    } catch (e) {
      toast.error(
        e?.response?.data?.detail || "Failed to update project — try again",
      );
    } finally {
      setSaving(false);
    }
  };

  return (
    <>
      <Button
        type="button"
        variant="outline"
        onClick={() => setOpen(true)}
        className="border-2 border-amber-500 text-amber-700 hover:bg-amber-50 font-bold uppercase tracking-wide text-xs h-9"
        data-testid="edit-project-btn"
      >
        <Pencil className="w-3.5 h-3.5 mr-1.5" /> Edit Project
      </Button>
      <Dialog open={open} onOpenChange={setOpen}>
        <DialogContent className="max-w-lg" data-testid="edit-project-dialog">
          <DialogHeader>
            <DialogTitle className="font-display text-xl font-black uppercase tracking-tight">
              Re-tag this report
            </DialogTitle>
          </DialogHeader>
          <div className="space-y-3 py-2 text-sm">
            <p className="text-slate-600 leading-relaxed">
              Change the project this record is filed under. Signatures,
              photos, narrative, and checklist data stay untouched.
            </p>
            <div>
              <div className="font-mono text-[10px] uppercase tracking-[0.2em] text-slate-500 font-bold mb-1">
                Currently filed under
              </div>
              <div className="px-3 py-2 rounded bg-slate-100 border-l-2 border-slate-400 font-mono text-[12px] text-slate-700">
                {current?.project_name || "—"}
                {current?.project_number ? ` · #${current.project_number}` : ""}
              </div>
            </div>
            <div>
              <div className="font-mono text-[10px] uppercase tracking-[0.2em] text-slate-500 font-bold mb-1">
                Move to
              </div>
              <JobPicker
                projectName={job.project_name}
                projectNumber={job.project_number}
                onSelect={handleJobPick}
              />
            </div>
          </div>
          <DialogFooter className="gap-2">
            <Button
              type="button"
              variant="outline"
              onClick={() => setOpen(false)}
              disabled={saving}
              data-testid="edit-project-cancel"
            >
              <X className="w-4 h-4 mr-1" /> Cancel
            </Button>
            <Button
              type="button"
              onClick={handleSave}
              disabled={saving}
              className="bg-red-700 hover:bg-red-800 text-white font-bold uppercase tracking-wide"
              data-testid="edit-project-save"
            >
              <Save className="w-4 h-4 mr-1" /> {saving ? "Saving…" : "Save"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </>
  );
}

export default EditProjectDialog;
