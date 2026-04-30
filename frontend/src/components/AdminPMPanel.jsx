import React, { useEffect, useState } from "react";
import {
  Users,
  Loader2,
  Plus,
  Trash2,
  RefreshCcw,
  CheckCircle2,
  XCircle,
  Pencil,
  Save,
  X,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { api } from "@/lib/api";
import { toast } from "sonner";

/**
 * AdminPMPanel — manage MASCI Project Managers (the email routing roster).
 *
 * Backend:
 *   GET    /api/admin/project-managers
 *   POST   /api/admin/project-managers     {name, email, phone?, is_active?}
 *   PATCH  /api/admin/project-managers/:id (partial)
 *   DELETE /api/admin/project-managers/:id (blocked if jobs reference)
 *
 * Auto-email (Site Inspections / Safety Meetings / JHAs / Incidents /
 * Daily Reports / Equipment Pre-Op) routes per the PM assigned to each
 * job in /admin → Active Jobs Master. Add a new PM here, then open the
 * Active Jobs Master card to reassign jobs to them.
 */
export default function AdminPMPanel() {
  const [pms, setPms] = useState([]);
  const [loading, setLoading] = useState(true);
  const [adding, setAdding] = useState(false);
  const [editingId, setEditingId] = useState(null);
  const [editDraft, setEditDraft] = useState({});
  const [savingId, setSavingId] = useState(null);
  const [form, setForm] = useState({ name: "", email: "", phone: "" });

  const refresh = async () => {
    setLoading(true);
    try {
      const r = await api.get("/admin/project-managers");
      setPms(r.data?.items || []);
    } catch (e) {
      toast.error(e?.response?.data?.detail || "Failed to load PMs");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    refresh();
  }, []);

  const addPm = async (e) => {
    e?.preventDefault?.();
    if (!form.name.trim() || !form.email.trim()) {
      toast.error("Name and email are required");
      return;
    }
    setAdding(true);
    try {
      await api.post("/admin/project-managers", form);
      toast.success(`Added ${form.name}`);
      setForm({ name: "", email: "", phone: "" });
      await refresh();
    } catch (err) {
      toast.error(err?.response?.data?.detail || "Add failed");
    } finally {
      setAdding(false);
    }
  };

  const startEdit = (pm) => {
    setEditingId(pm.id);
    setEditDraft({ name: pm.name, email: pm.email, phone: pm.phone || "" });
  };

  const saveEdit = async (pm) => {
    setSavingId(pm.id);
    try {
      await api.patch(`/admin/project-managers/${pm.id}`, editDraft);
      toast.success(`Updated ${editDraft.name}`);
      setEditingId(null);
      setEditDraft({});
      await refresh();
    } catch (err) {
      toast.error(err?.response?.data?.detail || "Save failed");
    } finally {
      setSavingId(null);
    }
  };

  const toggleActive = async (pm) => {
    setSavingId(pm.id);
    try {
      await api.patch(`/admin/project-managers/${pm.id}`, {
        is_active: !pm.is_active,
      });
      await refresh();
    } catch (err) {
      toast.error(err?.response?.data?.detail || "Toggle failed");
    } finally {
      setSavingId(null);
    }
  };

  const removePm = async (pm) => {
    if (
      !window.confirm(
        `Permanently delete ${pm.name}?\n\nIf they're still assigned to jobs you'll be told to reassign first. Use Deactivate instead if they just left the company.`
      )
    )
      return;
    setSavingId(pm.id);
    try {
      await api.delete(`/admin/project-managers/${pm.id}`);
      toast.success(`Deleted ${pm.name}`);
      await refresh();
    } catch (err) {
      toast.error(err?.response?.data?.detail || "Delete failed");
    } finally {
      setSavingId(null);
    }
  };

  const total = pms.length;
  const activeCount = pms.filter((p) => p.is_active).length;

  return (
    <section
      className="bg-white border-2 border-slate-300 rounded-md p-5 sm:p-7 mb-8 shadow-sm"
      data-testid="admin-pm-panel"
    >
      <div className="flex items-start gap-3 mb-4">
        <div className="inline-flex items-center justify-center w-11 h-11 rounded-md bg-slate-900 text-white shrink-0">
          <Users className="w-5 h-5" />
        </div>
        <div className="flex-1">
          <div className="font-mono text-[10px] uppercase tracking-[0.25em] text-slate-700 font-bold">
            Email Routing Roster
          </div>
          <h2 className="font-display text-xl sm:text-2xl font-black text-slate-900 leading-none mt-1">
            Project Managers
          </h2>
          <p className="text-sm text-slate-600 mt-2">
            Add, edit, or deactivate the PMs the auto-email engine routes to.
            Open the <strong>Active Jobs Master</strong> card below to reassign
            jobs to a different PM. Total: <strong>{total}</strong> ({activeCount}{" "}
            active).
          </p>
        </div>
        <Button
          variant="outline"
          onClick={refresh}
          disabled={loading}
          className="h-9 text-xs font-mono uppercase tracking-wide"
          data-testid="pm-refresh"
        >
          {loading ? (
            <Loader2 className="w-3.5 h-3.5 mr-1 animate-spin" />
          ) : (
            <RefreshCcw className="w-3.5 h-3.5 mr-1" />
          )}
          Refresh
        </Button>
      </div>

      {/* Add new PM form */}
      <form
        onSubmit={addPm}
        className="grid sm:grid-cols-[1fr_1.4fr_1fr_auto] gap-2 mb-4 p-3 border-2 border-slate-200 rounded bg-slate-50"
      >
        <div>
          <Label className="font-mono text-[9px] uppercase tracking-wide text-slate-700">
            Name
          </Label>
          <Input
            value={form.name}
            onChange={(e) => setForm({ ...form, name: e.target.value })}
            placeholder="John Doe"
            className="h-9 text-sm mt-1"
            data-testid="pm-input-name"
          />
        </div>
        <div>
          <Label className="font-mono text-[9px] uppercase tracking-wide text-slate-700">
            Work Email
          </Label>
          <Input
            type="email"
            value={form.email}
            onChange={(e) => setForm({ ...form, email: e.target.value })}
            placeholder="johndoe@mascigc.com"
            className="h-9 text-sm mt-1"
            data-testid="pm-input-email"
          />
        </div>
        <div>
          <Label className="font-mono text-[9px] uppercase tracking-wide text-slate-700">
            Phone
          </Label>
          <Input
            value={form.phone}
            onChange={(e) => setForm({ ...form, phone: e.target.value })}
            placeholder="555-0123"
            className="h-9 text-sm mt-1"
            data-testid="pm-input-phone"
          />
        </div>
        <div className="flex items-end">
          <Button
            type="submit"
            disabled={adding}
            className="bg-slate-900 hover:bg-slate-800 text-white font-bold uppercase tracking-wide text-xs h-9 px-3 border-b-2 border-slate-950"
            data-testid="pm-add-btn"
          >
            {adding ? (
              <Loader2 className="w-3.5 h-3.5 animate-spin" />
            ) : (
              <>
                <Plus className="w-3.5 h-3.5 mr-1" /> Add PM
              </>
            )}
          </Button>
        </div>
      </form>

      {/* PM list */}
      <div className="overflow-x-auto rounded border border-slate-200">
        <table className="w-full text-sm" data-testid="pm-table">
          <thead className="bg-slate-100">
            <tr className="text-left font-mono text-[10px] uppercase tracking-wide text-slate-700">
              <th className="px-3 py-2">Name</th>
              <th className="px-3 py-2">Email</th>
              <th className="px-3 py-2">Phone</th>
              <th className="px-3 py-2 text-center">Active</th>
              <th className="px-3 py-2 w-32 text-right">Actions</th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr>
                <td colSpan={5} className="px-3 py-6 text-center text-slate-500">
                  <Loader2 className="w-5 h-5 animate-spin inline-block" /> Loading…
                </td>
              </tr>
            ) : pms.length === 0 ? (
              <tr>
                <td colSpan={5} className="px-3 py-6 text-center text-slate-500">
                  No PMs yet. Add one above.
                </td>
              </tr>
            ) : (
              pms.map((p) => {
                const isEditing = editingId === p.id;
                return (
                  <tr
                    key={p.id}
                    className={`border-t border-slate-100 ${p.is_active ? "" : "bg-slate-50 text-slate-500"}`}
                    data-testid={`pm-row-${p.id}`}
                  >
                    <td className="px-3 py-2 font-medium">
                      {isEditing ? (
                        <Input
                          value={editDraft.name}
                          onChange={(e) =>
                            setEditDraft({ ...editDraft, name: e.target.value })
                          }
                          className="h-8 text-xs"
                          data-testid={`pm-edit-name-${p.id}`}
                        />
                      ) : (
                        p.name
                      )}
                    </td>
                    <td className="px-3 py-2 text-xs">
                      {isEditing ? (
                        <Input
                          value={editDraft.email}
                          onChange={(e) =>
                            setEditDraft({ ...editDraft, email: e.target.value })
                          }
                          className="h-8 text-xs"
                          data-testid={`pm-edit-email-${p.id}`}
                        />
                      ) : (
                        <span className="font-mono">{p.email}</span>
                      )}
                    </td>
                    <td className="px-3 py-2 text-xs text-slate-600">
                      {isEditing ? (
                        <Input
                          value={editDraft.phone}
                          onChange={(e) =>
                            setEditDraft({ ...editDraft, phone: e.target.value })
                          }
                          className="h-8 text-xs"
                          data-testid={`pm-edit-phone-${p.id}`}
                        />
                      ) : (
                        p.phone || "—"
                      )}
                    </td>
                    <td className="px-3 py-2 text-center">
                      <button
                        type="button"
                        onClick={() => toggleActive(p)}
                        disabled={savingId === p.id || isEditing}
                        className={`inline-flex items-center justify-center w-7 h-7 rounded ${p.is_active ? "bg-emerald-100 text-emerald-700 hover:bg-emerald-200" : "bg-slate-200 text-slate-500 hover:bg-slate-300"}`}
                        title={p.is_active ? "Click to deactivate" : "Click to reactivate"}
                        data-testid={`pm-toggle-${p.id}`}
                      >
                        {savingId === p.id && !isEditing ? (
                          <Loader2 className="w-3.5 h-3.5 animate-spin" />
                        ) : p.is_active ? (
                          <CheckCircle2 className="w-4 h-4" />
                        ) : (
                          <XCircle className="w-4 h-4" />
                        )}
                      </button>
                    </td>
                    <td className="px-3 py-2 text-right">
                      <div className="inline-flex items-center gap-1">
                        {isEditing ? (
                          <>
                            <button
                              type="button"
                              onClick={() => saveEdit(p)}
                              disabled={savingId === p.id}
                              className="inline-flex items-center justify-center w-7 h-7 rounded text-emerald-600 hover:bg-emerald-50"
                              title="Save"
                              data-testid={`pm-save-${p.id}`}
                            >
                              {savingId === p.id ? (
                                <Loader2 className="w-3.5 h-3.5 animate-spin" />
                              ) : (
                                <Save className="w-4 h-4" />
                              )}
                            </button>
                            <button
                              type="button"
                              onClick={() => {
                                setEditingId(null);
                                setEditDraft({});
                              }}
                              className="inline-flex items-center justify-center w-7 h-7 rounded text-slate-400 hover:bg-slate-100"
                              title="Cancel"
                              data-testid={`pm-cancel-${p.id}`}
                            >
                              <X className="w-4 h-4" />
                            </button>
                          </>
                        ) : (
                          <>
                            <button
                              type="button"
                              onClick={() => startEdit(p)}
                              className="inline-flex items-center justify-center w-7 h-7 rounded text-slate-600 hover:bg-slate-100"
                              title="Edit"
                              data-testid={`pm-edit-${p.id}`}
                            >
                              <Pencil className="w-4 h-4" />
                            </button>
                            <button
                              type="button"
                              onClick={() => removePm(p)}
                              disabled={savingId === p.id}
                              className="inline-flex items-center justify-center w-7 h-7 rounded text-slate-400 hover:text-red-600 hover:bg-red-50"
                              title="Delete (use Deactivate first)"
                              data-testid={`pm-delete-${p.id}`}
                            >
                              <Trash2 className="w-4 h-4" />
                            </button>
                          </>
                        )}
                      </div>
                    </td>
                  </tr>
                );
              })
            )}
          </tbody>
        </table>
      </div>
    </section>
  );
}
