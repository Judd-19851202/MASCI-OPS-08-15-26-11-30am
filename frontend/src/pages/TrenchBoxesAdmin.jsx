import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { Plus, Loader2, Trash2, Pencil, Box, Printer, FolderOpen } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { MasciLogo } from "@/components/MasciLogo";
import HubBackLink, { useHubHome } from "@/components/HubBackLink";
import { api } from "@/lib/api";
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

export default function TrenchBoxesAdmin() {
  const [boxes, setBoxes] = useState([]);
  const [loading, setLoading] = useState(true);
  const [open, setOpen] = useState(false);
  const [editingId, setEditingId] = useState(null);
  const [form, setForm] = useState(EMPTY);
  const [saving, setSaving] = useState(false);
  const hubHome = useHubHome();

  const refresh = async () => {
    setLoading(true);
    try {
      const r = await api.get("/trench-boxes");
      setBoxes(r.data || []);
    } catch {
      setBoxes([]);
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
      return toast.error("Manufacturer and model are required");
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
      toast.error(e?.response?.data?.detail || "Save failed");
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
      toast.error("Delete failed");
    }
  };

  const F = ({ k, label, ph, type = "text" }) => (
    <div>
      <Label className="font-mono text-[10px] uppercase tracking-[0.2em] text-slate-500">{label}</Label>
      <Input
        type={type}
        value={form[k] ?? ""}
        onChange={(e) => set(k, e.target.value)}
        placeholder={ph}
        className="h-10 mt-1 border-2"
      />
    </div>
  );

  return (
    <div className="min-h-screen bg-slate-50">
      <div className="caution-stripe" />
      <header className="bg-slate-900 border-b-4 border-red-700">
        <div className="max-w-5xl mx-auto px-4 sm:px-6 py-3 flex items-center justify-between gap-3">
          <HubBackLink testId="back-link" />
          <MasciLogo variant="mark" size="md" homeLink={hubHome} />
          <div className="flex items-center gap-2">
            <Link
              to="/admin/trench-boxes/poster"
              className="hidden sm:inline-flex items-center gap-1.5 h-10 px-3 rounded-md border-2 border-slate-300 text-slate-700 hover:border-red-700 hover:text-red-700 font-mono text-xs uppercase tracking-[0.15em] font-bold"
              data-testid="open-poster-link"
            >
              <Printer className="w-4 h-4" /> QR Poster
            </Link>
            <Button onClick={openNew} className="h-10 px-4 bg-red-700 hover:bg-red-800 text-white font-bold uppercase tracking-wide text-xs" data-testid="new-trench-btn">
              <Plus className="w-4 h-4 mr-1" /> Add Box
            </Button>
          </div>
        </div>
      </header>

      <main className="max-w-5xl mx-auto px-4 sm:px-6 py-6 sm:py-10">
        <div className="mb-6">
          <span className="font-mono text-xs uppercase tracking-[0.25em] text-red-700">Trench Box Tabulated Data</span>
          <h1 className="font-display text-3xl sm:text-4xl font-black tracking-tight text-slate-900 mt-1">
            MASCI Trench Box Fleet
          </h1>
          <p className="text-slate-600 text-sm mt-2">
            Add every trench shield from the MASCI fleet here so foremen can verify OSHA compliance on the fly. Each entry should mirror the manufacturer's data plate.
          </p>
        </div>

        {/* Section banner so this is impossible to miss */}
        <div
          className="bg-amber-50 border-2 border-amber-400 rounded-md p-4 sm:p-5 mb-4 flex items-start gap-3"
          data-testid="admin-tabulated-banner"
        >
          <div className="inline-flex items-center justify-center w-10 h-10 rounded-md bg-amber-500 text-white shrink-0">
            <FolderOpen className="w-5 h-5" />
          </div>
          <div>
            <div className="font-mono text-[10px] uppercase tracking-[0.25em] text-amber-800 font-black">
              Step 1 · Upload &amp; Manage Files
            </div>
            <h2 className="font-display text-xl sm:text-2xl font-black text-slate-900 leading-tight mt-0.5">
              Tabulated Data Files — Upload / Delete
            </h2>
            <p className="text-slate-700 text-sm mt-1.5">
              Drag-and-drop manufacturer PDFs, Excel sheets, ZIPs, or images
              into any folder below. Crews see these on{" "}
              <code className="px-1 bg-white rounded border border-amber-300 text-xs">
                /trench-boxes
              </code>
              . Use the <strong>General / Educational</strong> folder for
              shared explainers (e.g. United Rentals primer).
            </p>
          </div>
        </div>

        <TrenchBoxTabulatedLibrary adminMode={true} />

        <div className="mb-4 mt-8 pt-6 border-t-2 border-slate-200">
          <div className="font-mono text-[10px] uppercase tracking-[0.25em] text-red-800 font-black">
            Step 2 · Master List
          </div>
          <h2 className="font-display text-xl sm:text-2xl font-black text-slate-900 mt-0.5">
            Fleet — Trench Box Master List
          </h2>
          <p className="text-slate-600 text-sm mt-1">
            Add, edit, or remove individual trench shields. Each shield here
            becomes a folder above for its tabulated data.
          </p>
        </div>

        {loading ? (
          <div className="p-12 flex items-center justify-center text-slate-500"><Loader2 className="w-6 h-6 animate-spin mr-2" /> Loading…</div>
        ) : boxes.length === 0 ? (
          <div className="bg-white border-2 border-slate-300 rounded-md p-10 text-center">
            <Box className="w-10 h-10 text-slate-400 mx-auto mb-3" />
            <h3 className="font-display text-xl font-bold text-slate-900">No trench boxes yet</h3>
            <p className="text-slate-600 mt-2">Click "Add Box" to enter the first one.</p>
          </div>
        ) : (
          <ul className="bg-white border-2 border-slate-300 rounded-md divide-y-2 divide-slate-100">
            {boxes.map((b) => (
              <li key={b.id} className="p-4 sm:p-5 flex flex-col sm:flex-row sm:items-center gap-3" data-testid={`admin-trench-row-${b.id}`}>
                <div className="flex-1 min-w-0">
                  <div className="font-display font-bold text-slate-900 truncate">{b.manufacturer} · {b.model}</div>
                  <div className="text-xs text-slate-500 mt-0.5">
                    {b.serial_number && `S/N ${b.serial_number} · `}{b.length_ft && `${b.length_ft} ft · `}{b.weight_lbs && `${b.weight_lbs} lbs`}
                  </div>
                  <div className="text-xs text-slate-500 mt-1 italic">
                    Type C max {b.max_depth_type_c_60_ft || "—"} ft · Type B max {b.max_depth_type_b_ft || "—"} ft · Type A max {b.max_depth_type_a_ft || "—"} ft
                  </div>
                </div>
                <div className="flex gap-2">
                  <Button onClick={() => openEdit(b)} variant="outline" className="h-10 border-2 border-slate-300 hover:border-red-700 hover:text-red-700 text-xs uppercase font-bold" data-testid={`edit-trench-${b.id}`}>
                    <Pencil className="w-4 h-4 mr-1" /> Edit
                  </Button>
                  <Button onClick={() => onDelete(b)} variant="outline" size="icon" className="h-10 w-10 border-2 border-slate-300 hover:border-red-500 hover:text-red-600" data-testid={`delete-trench-${b.id}`}>
                    <Trash2 className="w-4 h-4" />
                  </Button>
                </div>
              </li>
            ))}
          </ul>
        )}

        <Dialog open={open} onOpenChange={setOpen}>
          <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
            <DialogHeader>
              <DialogTitle className="font-display font-black">{editingId ? "Edit Trench Box" : "Add Trench Box"}</DialogTitle>
            </DialogHeader>
            <div className="space-y-4">
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <F k="manufacturer" label="Manufacturer *" ph="e.g. Speed Shore" />
                <F k="model" label="Model *" ph="e.g. SLD-8x16" />
                <F k="serial_number" label="Serial #" />
                <div>
                  <Label className="font-mono text-[10px] uppercase tracking-[0.2em] text-slate-500">Type</Label>
                  <Select value={form.box_type} onValueChange={(v) => set("box_type", v)}>
                    <SelectTrigger className="h-10 mt-1 border-2"><SelectValue /></SelectTrigger>
                    <SelectContent>
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
                  <Label className="font-mono text-[10px] uppercase tracking-[0.2em] text-slate-500">Stacking Allowed</Label>
                  <Select value={form.stacking_allowed} onValueChange={(v) => set("stacking_allowed", v)}>
                    <SelectTrigger className="h-10 mt-1 border-2"><SelectValue /></SelectTrigger>
                    <SelectContent>
                      <SelectItem value="No">No</SelectItem>
                      <SelectItem value="Yes">Yes</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                {form.stacking_allowed === "Yes" && (
                  <F k="stacking_max" label="Stacking Max" ph="2" type="number" />
                )}
              </div>

              <div className="border-t-2 border-slate-100 pt-3">
                <div className="font-mono text-[10px] uppercase tracking-[0.2em] text-red-700 font-bold mb-2">Maximum Allowable Depth (ft) — OSHA 1926.652</div>
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                  <F k="max_depth_type_a_ft" label="Type A" type="number" />
                  <F k="max_depth_type_b_ft" label="Type B" type="number" />
                  <F k="max_depth_type_c_60_ft" label="Type C-60" type="number" />
                  <F k="max_depth_type_c_80_ft" label="Type C-80" type="number" />
                </div>
              </div>

              <div>
                <Label className="font-mono text-[10px] uppercase tracking-[0.2em] text-slate-500">Manufacturer Tabulated-Data PDF (optional)</Label>
                <Input type="file" accept="application/pdf,.pdf" onChange={(e) => onFile(e.target.files?.[0])} className="h-10 mt-1 border-2 file:mr-2 file:py-2 file:px-3 file:rounded file:border-0 file:bg-slate-900 file:text-white file:font-bold" data-testid="trench-file-input" />
                {form.tabulated_data_filename && <p className="text-xs text-slate-500 mt-1">{form.tabulated_data_filename}</p>}
              </div>

              <div>
                <Label className="font-mono text-[10px] uppercase tracking-[0.2em] text-slate-500">Notes</Label>
                <Textarea value={form.notes} onChange={(e) => set("notes", e.target.value)} className="mt-1 border-2" placeholder="Inspection date, repairs, special-use restrictions…" />
              </div>

              <Button onClick={submit} disabled={saving} className="w-full h-12 bg-red-700 hover:bg-red-800 text-white font-bold uppercase tracking-wide" data-testid="save-trench-btn">
                {saving ? <Loader2 className="w-4 h-4 animate-spin mr-1" /> : null}
                {saving ? "Saving…" : editingId ? "Save Changes" : "Add Box"}
              </Button>
            </div>
          </DialogContent>
        </Dialog>
      </main>
    </div>
  );
}
