import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { Plus, Loader2, Trash2, Pencil, Box, Printer, FolderOpen, TriangleAlert, ShieldCheck } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { AdminRouteShell } from "@/components/admin/AdminRouteShell";
import EmptyState from "@/components/EmptyState";
import { DetailPageHero } from "@/components/detail/DetailPageHero";
import { api } from "@/lib/api";
import { operationalError } from "@/lib/errors";
import { toast } from "sonner";
import TrenchBoxTabulatedLibrary from "@/components/TrenchBoxTabulatedLibrary";

const EMPTY = {
  manufacturer: "", model: "", serial_number: "", box_type: "Steel",
  length_ft: "", width_min_ft: "", width_max_ft: "",
  sidewall_height_ft: "", sidewall_thickness_in: "", weight_lbs: "",
  max_depth_type_a_ft: "", max_depth_type_b_ft: "",
  max_depth_type_c_60_ft: "", max_depth_type_c_80_ft: "",
  spreader_count: "", stacking_allowed: "No", stacking_max: "",
  notes: "",
  tabulated_data_file: "",
  tabulated_data_filename: "",
};

function readFileAsDataUrl(file) {
  return new Promise((res, rej) => {
    const r = new FileReader();
    r.onerror = rej;
    r.onload = () => res(r.result);
    r.readAsDataURL(file);
  });
}

const DIALOG_INPUT_CLASS = "mt-2 h-10 border-white/15 bg-white/10 text-white placeholder:text-slate-400";
const DIALOG_TEXTAREA_CLASS = "mt-2 min-h-[7rem] border-white/15 bg-white/10 text-white placeholder:text-slate-400";

function StepPanel({ eyebrow, title, description, children, testId }) {
  return (
    <section className="wp17-panel p-5 sm:p-6" data-testid={testId}>
      <div className="font-mono text-[10px] uppercase tracking-[0.22em] text-red-700 font-bold">{eyebrow}</div>
      <h2 className="mt-2 font-display text-2xl sm:text-3xl font-black tracking-tight text-slate-900">{title}</h2>
      <p className="mt-2 max-w-3xl text-sm sm:text-base leading-6 text-slate-600">{description}</p>
      <div className="mt-5">{children}</div>
    </section>
  );
}

export default function TrenchBoxesAdmin() {
  const [boxes, setBoxes] = useState([]);
  const [loading, setLoading] = useState(true);
  const [open, setOpen] = useState(false);
  const [editingId, setEditingId] = useState(null);
  const [form, setForm] = useState(EMPTY);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");

  const refresh = async () => {
    setLoading(true);
    setError("");
    try {
      const r = await api.get("/trench-boxes");
      setBoxes(r.data || []);
    } catch (e) {
      setBoxes([]);
      const message = operationalError(
        e,
        "Trench box library temporarily unavailable. Try again in a moment.",
        "Your admin session expired. Please sign in again."
      );
      setError(message);
      toast.error(message);
    } finally {
      setLoading(false);
    }
  };
  useEffect(() => { refresh(); }, []);

  const set = (k, v) => setForm((p) => ({ ...p, [k]: v }));

  const openNew = () => { setEditingId(null); setForm(EMPTY); setOpen(true); };
  const openEdit = (b) => {
    setEditingId(b.id);
    setForm({ ...EMPTY, ...b, tabulated_data_file: "" }); // don't pre-populate file
    setOpen(true);
  };

  const onFile = async (file) => {
    if (!file) { set("tabulated_data_file", ""); set("tabulated_data_filename", ""); return; }
    const url = await readFileAsDataUrl(file);
    set("tabulated_data_file", url);
    set("tabulated_data_filename", file.name);
  };

  const submit = async () => {
    if (!form.manufacturer.trim() || !form.model.trim()) {
      return toast.error("Manufacturer and model required.");
    }
    setSaving(true);
    try {
      const payload = { ...form };
      if (editingId) {
        await api.put(`/trench-boxes/${editingId}`, payload);
        toast.success("Trench box updated");
      } else {
        await api.post("/trench-boxes", payload);
        toast.success("Trench box added");
      }
      setOpen(false);
      refresh();
    } catch (e) {
      console.error(e);
      toast.error(operationalError(e,
        "Save temporarily unavailable. Try again in a moment.",
        "Your admin session expired. Please sign in again."));
    } finally {
      setSaving(false);
    }
  };

  const onDelete = async (b) => {
    if (!window.confirm(`Delete ${b.manufacturer} ${b.model}? This cannot be undone.`)) return;
    try {
      await api.delete(`/trench-boxes/${b.id}`);
      toast.success("Deleted");
      refresh();
    } catch {
      toast.error("Could not delete. Try again.");
    }
  };

  // Track 21.1 tech-debt: F closes over `form` + `set`; safe hoist scheduled for Track 21.y.
  // eslint-disable-next-line react/no-unstable-nested-components
  const F = ({ k, label, ph, type = "text" }) => (
    <div>
      <Label className="font-mono text-[10px] uppercase tracking-[0.2em] text-slate-300">{label}</Label>
      <Input
        type={type}
        value={form[k] ?? ""}
        onChange={(e) => set(k, e.target.value)}
        placeholder={ph}
        className={DIALOG_INPUT_CLASS}
        data-testid={`trench-form-${k}`}
      />
    </div>
  );

  const fleetCount = boxes.length;

  return (
    <AdminRouteShell
      pageTitle="MASCI Trench Box Fleet"
      subtitle="Trench shield tabulated data · OSHA compliance ready"
      portalRole="Admin · Trench Box Library"
      crumbs={[{ label: "Admin OS" }, { label: "Trench Safety" }, { label: "Trench Box Library" }]}
      showShellHeader={false}
      showBreadcrumbs={false}
      contentClassName="px-0 py-0"
      testId="admin-trench-box-shell"
    >
      <div className="min-h-screen bg-slate-50">
        <div className="caution-stripe print:hidden" />
        <main className="max-w-6xl mx-auto px-4 sm:px-6 py-6 sm:py-8 space-y-6" data-testid="admin-trench-page">
          <DetailPageHero
            backHref="/admin"
            backLabel="Admin OS"
            kicker="Trench Safety · fleet and reference control"
            title="Trench Box Fleet"
            description="Maintain the governed trench shield registry, tabulated data, and printable field access tools from one MASCI surface."
            actions={(
              <>
                <span className="inline-flex items-center gap-1.5 rounded-full border border-red-200 bg-red-50 px-3 py-1 text-xs font-bold text-red-900" data-testid="trench-box-count-chip">
                  <Box className="w-3.5 h-3.5" /> {fleetCount} box{fleetCount === 1 ? "" : "es"} on file
                </span>
                <span className="inline-flex items-center gap-1.5 rounded-full border border-emerald-200 bg-emerald-50 px-3 py-1 text-xs font-bold text-emerald-900" data-testid="trench-box-osha-chip">
                  <ShieldCheck className="w-3.5 h-3.5" /> OSHA reference ready
                </span>
              </>
            )}
            toolbar={(
              <div className="flex flex-wrap items-center gap-2">
                <Link
                  to="/admin/trench-boxes/poster"
                  className="inline-flex h-11 items-center gap-2 rounded-full border border-slate-300 bg-white px-4 text-xs font-bold uppercase tracking-[0.18em] text-slate-800 transition-colors hover:border-red-500 hover:text-red-700"
                  data-testid="open-poster-link"
                >
                  <Printer className="w-4 h-4" /> QR Poster
                </Link>
                <Button onClick={openNew} className="h-11 rounded-full bg-red-700 px-4 text-xs font-bold uppercase tracking-[0.18em] text-white hover:bg-red-800" data-testid="new-trench-btn">
                  <Plus className="w-4 h-4 mr-1" /> Add Box
                </Button>
              </div>
            )}
            testId="trench-box-hero"
          />

          {error ? (
            <section className="wp17-panel border border-amber-200 bg-amber-50 p-4 sm:p-5" data-testid="admin-trench-error-state">
              <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
                <div className="flex items-start gap-3 text-amber-900">
                  <TriangleAlert className="mt-0.5 h-5 w-5 shrink-0" />
                  <div>
                    <div className="font-display text-lg font-black">Trench box registry unavailable</div>
                    <p className="mt-1 text-sm leading-6">{error}</p>
                  </div>
                </div>
                <Button type="button" variant="outline" onClick={refresh} className="h-11 border-amber-300 bg-white text-amber-900 hover:bg-amber-100" data-testid="admin-trench-error-retry">
                  Retry
                </Button>
              </div>
            </section>
          ) : null}

          <div className="grid gap-6">
            <StepPanel
              eyebrow="Step 1 · upload and manage files"
              title="Tabulated data library"
              description="Drag-and-drop manufacturer PDFs, Excel sheets, ZIPs, or images into any folder below. Use the General / Educational folder for shared explainers crews need in the field."
              testId="admin-tabulated-banner"
            >
              <TrenchBoxTabulatedLibrary adminMode={true} />
            </StepPanel>

            <StepPanel
              eyebrow="Step 2 · maintain the fleet register"
              title="Master trench box list"
              description="Add, edit, or remove individual trench shields. Each registered shield becomes a searchable folder in the tabulated-data library above."
              testId="admin-trench-master-list-section"
            >
              {loading ? (
                <div className="flex min-h-[14rem] items-center justify-center text-slate-500" data-testid="admin-trench-loading-state">
                  <Loader2 className="w-6 h-6 animate-spin mr-2" /> Loading…
                </div>
              ) : boxes.length === 0 ? (
                <EmptyState
                  title="No trench boxes yet"
                  message="Use Add Box to enter the first shield and start the governed field library."
                  icon={FolderOpen}
                  data-testid="admin-trench-empty-state"
                />
              ) : (
                <ul className="space-y-3" data-testid="admin-trench-list">
                  {boxes.map((b) => (
                    <li key={b.id} className="rounded-[1.35rem] border border-slate-200 bg-white px-4 py-4 shadow-[0_10px_24px_rgba(15,23,42,0.05)] sm:px-5" data-testid={`admin-trench-row-${b.id}`}>
                      <div className="flex flex-col gap-4 sm:flex-row sm:items-center">
                        <div className="min-w-0 flex-1">
                          <div className="font-display text-xl font-black text-slate-900 truncate">{b.manufacturer} · {b.model}</div>
                          <div className="mt-1 text-xs text-slate-500">
                            {b.serial_number && `S/N ${b.serial_number} · `}{b.length_ft && `${b.length_ft} ft · `}{b.weight_lbs && `${b.weight_lbs} lbs`}
                          </div>
                          <div className="mt-2 flex flex-wrap gap-2 text-[11px] text-slate-600">
                            <span className="rounded-full border border-slate-200 bg-slate-50 px-2.5 py-1">Type C max {b.max_depth_type_c_60_ft || "—"} ft</span>
                            <span className="rounded-full border border-slate-200 bg-slate-50 px-2.5 py-1">Type B max {b.max_depth_type_b_ft || "—"} ft</span>
                            <span className="rounded-full border border-slate-200 bg-slate-50 px-2.5 py-1">Type A max {b.max_depth_type_a_ft || "—"} ft</span>
                          </div>
                        </div>
                        <div className="flex gap-2 sm:justify-end">
                          <Button onClick={() => openEdit(b)} variant="outline" className="h-10 border-slate-300 bg-white text-xs uppercase font-bold tracking-[0.18em] hover:border-red-700 hover:text-red-700" data-testid={`edit-trench-${b.id}`}>
                            <Pencil className="w-4 h-4 mr-1" /> Edit
                          </Button>
                          <Button onClick={() => onDelete(b)} variant="outline" size="icon" className="h-10 w-10 border-slate-300 bg-white hover:border-red-500 hover:text-red-600" data-testid={`delete-trench-${b.id}`} aria-label="Delete trench box" title="Delete">
                            <Trash2 className="w-4 h-4" />
                          </Button>
                        </div>
                      </div>
                    </li>
                  ))}
                </ul>
              )}
            </StepPanel>
          </div>

          <Dialog open={open} onOpenChange={setOpen}>
            <DialogContent className="max-h-[90vh] max-w-2xl overflow-y-auto border border-white/15 bg-[#0f1c33]/96 text-white shadow-[0_28px_90px_rgba(2,6,23,0.58)] backdrop-blur-2xl sm:rounded-[1.75rem]" data-testid="trench-box-dialog">
              <DialogHeader>
                <div className="font-mono text-[10px] uppercase tracking-[0.22em] text-red-300">Governed trench asset editor</div>
                <DialogTitle className="font-display font-black text-2xl text-white">{editingId ? "Edit Trench Box" : "Add Trench Box"}</DialogTitle>
              </DialogHeader>
              <div className="space-y-5">
                <div className="grid grid-cols-1 gap-x-8 gap-y-4 lg:grid-cols-2">
                  <F k="manufacturer" label="Manufacturer *" ph="e.g. Speed Shore" />
                  <F k="model" label="Model *" ph="e.g. SLD-8x16" />
                  <F k="serial_number" label="Serial #" />
                  <div>
                    <Label className="font-mono text-[10px] uppercase tracking-[0.2em] text-slate-300">Type</Label>
                    <Select value={form.box_type} onValueChange={(v) => set("box_type", v)}>
                      <SelectTrigger className={DIALOG_INPUT_CLASS} data-testid="trench-box-type-select"><SelectValue /></SelectTrigger>
                      <SelectContent className="border-white/15 bg-[#162744] text-white">
                        <SelectItem value="Steel">Steel</SelectItem>
                        <SelectItem value="Aluminum">Aluminum</SelectItem>
                        <SelectItem value="Modular">Modular</SelectItem>
                        <SelectItem value="Slide Rail">Slide Rail</SelectItem>
                        <SelectItem value="Other">Other</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  <F k="length_ft" label="Length (ft)" ph="16" type="number" />
                  <F k="weight_lbs" label="Weight (lbs)" ph="6500" type="number" />
                  <F k="width_min_ft" label="Min Width (ft)" ph="4" type="number" />
                  <F k="width_max_ft" label="Max Width (ft)" ph="8" type="number" />
                  <F k="sidewall_height_ft" label="Sidewall Height (ft)" ph="8" type="number" />
                  <F k="sidewall_thickness_in" label='Sidewall Thickness (")' ph="3" />
                  <F k="spreader_count" label="Spreaders" ph="2" />
                  <div>
                    <Label className="font-mono text-[10px] uppercase tracking-[0.2em] text-slate-300">Stacking Allowed</Label>
                    <Select value={form.stacking_allowed} onValueChange={(v) => set("stacking_allowed", v)}>
                      <SelectTrigger className={DIALOG_INPUT_CLASS} data-testid="trench-box-stacking-select"><SelectValue /></SelectTrigger>
                      <SelectContent className="border-white/15 bg-[#162744] text-white">
                        <SelectItem value="No">No</SelectItem>
                        <SelectItem value="Yes">Yes</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  {form.stacking_allowed === "Yes" ? (
                    <F k="stacking_max" label="Stacking Max" ph="2" type="number" />
                  ) : null}
                </div>

                <div className="rounded-[1.25rem] border border-white/10 bg-white/6 p-4">
                  <div className="font-mono text-[10px] uppercase tracking-[0.2em] text-red-300 font-bold mb-3">Maximum allowable depth (ft) · OSHA 1926.652</div>
                  <div className="grid grid-cols-1 gap-x-6 gap-y-3 sm:grid-cols-2">
                    <F k="max_depth_type_a_ft" label="Type A" type="number" />
                    <F k="max_depth_type_b_ft" label="Type B" type="number" />
                    <F k="max_depth_type_c_60_ft" label="Type C-60" type="number" />
                    <F k="max_depth_type_c_80_ft" label="Type C-80" type="number" />
                  </div>
                </div>

                <div>
                  <Label className="font-mono text-[10px] uppercase tracking-[0.2em] text-slate-300">Manufacturer tabulated-data PDF (optional)</Label>
                  <Input
                    type="file"
                    accept="application/pdf,.pdf"
                    onChange={(e) => onFile(e.target.files?.[0])}
                    className="mt-2 h-10 border-white/15 bg-white/10 text-white file:mr-2 file:rounded-full file:border-0 file:bg-white file:px-3 file:py-2 file:text-xs file:font-bold file:text-slate-900"
                    data-testid="trench-file-input"
                  />
                  {form.tabulated_data_filename ? <p className="mt-2 text-xs text-slate-300">{form.tabulated_data_filename}</p> : null}
                </div>

                <div>
                  <Label className="font-mono text-[10px] uppercase tracking-[0.2em] text-slate-300">Notes</Label>
                  <Textarea
                    value={form.notes}
                    onChange={(e) => set("notes", e.target.value)}
                    className={DIALOG_TEXTAREA_CLASS}
                    placeholder="Inspection date, repairs, special-use restrictions…"
                    data-testid="trench-notes-input"
                  />
                </div>

                <Button onClick={submit} disabled={saving} className="h-12 w-full rounded-full bg-red-700 text-xs font-bold uppercase tracking-[0.18em] text-white hover:bg-red-800" data-testid="save-trench-btn">
                  {saving ? <Loader2 className="w-4 h-4 animate-spin mr-1" /> : null}
                  {saving ? "Saving…" : editingId ? "Save Changes" : "Add Box"}
                </Button>
              </div>
            </DialogContent>
          </Dialog>
        </main>
      </div>
    </AdminRouteShell>
  );
}
