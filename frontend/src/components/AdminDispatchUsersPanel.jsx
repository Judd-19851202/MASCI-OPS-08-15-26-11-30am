// AdminDispatchUsersPanel — manage MASCI Dispatch Portal accounts (Safety
// Manager, Dispatcher, Dispatcher). Mirrors
// AdminHRUsersPanel pattern but with the orange-700 accent.
//
// Phase 1 scope: list / add / edit / disable / delete + issue
// per-user passwords. Welcome email delivery is Phase 5 — for now the
// password is always revealed on screen for the admin to hand off
// securely (matches HR "Show on Screen" path).
//
// Backend:
//   GET    /api/admin/dispatch-users
//   POST   /api/admin/dispatch-users        {name, email, phone?, role?}
//   PATCH  /api/admin/dispatch-users/:id    (partial)
//   DELETE /api/admin/dispatch-users/:id
//   POST   /api/admin/dispatch-users/:id/reset-password
import React, { useEffect, useState } from "react";
import {
  Truck, Plus, Trash2, RefreshCcw, Pencil, Save, X, KeyRound, Copy,
  ShieldOff, ShieldCheck, Loader2, Mail,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle,
} from "@/components/ui/dialog";
import {
  Select, SelectContent, SelectItem, SelectTrigger, SelectValue,
} from "@/components/ui/select";
import { api } from "@/lib/api";
import { toast } from "sonner";

const ROLE_OPTIONS = ["Dispatcher", "Dispatcher", "Dispatcher", "Other"];
const inputCls = "h-10 text-sm border-2 border-slate-300 focus-visible:ring-2 focus-visible:ring-orange-700";

export default function AdminDispatchUsersPanel() {
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [adding, setAdding] = useState(false);
  const [savingId, setSavingId] = useState(null);
  const [editingId, setEditingId] = useState(null);
  const [editDraft, setEditDraft] = useState({});
  const [form, setForm] = useState({ name: "", email: "", phone: "", role: "Dispatcher" });

  const [showPwReveal, setShowPwReveal] = useState(false);
  const [pwReveal, setPwReveal] = useState({ name: "", email: "", password: "" });

  const refresh = async () => {
    setLoading(true);
    try {
      const r = await api.get("/admin/dispatch-users");
      // Backend returns a plain array for dispatch users
      setUsers(Array.isArray(r.data) ? r.data : (r.data?.users || []));
    } catch (err) {
      toast.error(err?.response?.data?.detail || "Could not load Dispatch users");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { refresh(); }, []);

  const addUser = async () => {
    if (!form.name.trim()) return toast.error("Name required");
    if (!form.email.trim() || !form.email.includes("@")) return toast.error("Valid email required");
    setAdding(true);
    try {
      const r = await api.post("/admin/dispatch-users", form);
      const u = r.data?.user || {};
      const tempPw = r.data?.temp_password || "";
      setPwReveal({ name: u.name, email: u.email, password: tempPw });
      setShowPwReveal(true);
      setForm({ name: "", email: "", phone: "", role: "Dispatcher" });
      refresh();
    } catch (err) {
      toast.error(err?.response?.data?.detail || "Could not add user");
    } finally {
      setAdding(false);
    }
  };

  const startEdit = (u) => {
    setEditingId(u.id);
    setEditDraft({ name: u.name || "", email: u.email || "", phone: u.phone || "", role: u.role || "Dispatcher" });
  };

  const saveEdit = async (u) => {
    setSavingId(u.id);
    try {
      await api.patch(`/admin/dispatch-users/${u.id}`, editDraft);
      toast.success("Saved");
      setEditingId(null);
      refresh();
    } catch (err) {
      toast.error(err?.response?.data?.detail || "Save failed");
    } finally {
      setSavingId(null);
    }
  };

  const toggleDisabled = async (u) => {
    setSavingId(u.id);
    try {
      await api.patch(`/admin/dispatch-users/${u.id}`, { disabled: !u.disabled });
      refresh();
    } catch {
      toast.error("Could not update");
    } finally {
      setSavingId(null);
    }
  };

  const removeUser = async (u) => {
    if (!window.confirm(`Permanently delete Dispatch user ${u.name}?`)) return;
    try {
      await api.delete(`/admin/dispatch-users/${u.id}`);
      toast.success("Removed");
      refresh();
    } catch (err) {
      toast.error(err?.response?.data?.detail || "Could not delete");
    }
  };

  const issuePassword = async (u) => {
    try {
      const r = await api.post(`/admin/dispatch-users/${u.id}/reset-password`);
      const tempPw = r.data?.temp_password || "";
      setPwReveal({ name: u.name, email: u.email, password: tempPw });
      setShowPwReveal(true);
      refresh();
    } catch (err) {
      toast.error(err?.response?.data?.detail || "Could not set password");
    }
  };

  const copyPw = async () => {
    try {
      await navigator.clipboard.writeText(pwReveal.password);
      toast.success("Copied to clipboard");
    } catch {
      toast.error("Copy failed — write it down by hand");
    }
  };

  return (
    <div className="border-2 border-slate-300 rounded-md p-5 bg-white" data-testid="admin-dispatch-users-panel">
      <div className="flex items-start justify-between gap-3 mb-4">
        <div className="flex items-start gap-3">
          <div className="inline-flex items-center justify-center w-12 h-12 rounded-md bg-orange-700 text-white shrink-0">
            <Truck className="w-6 h-6" />
          </div>
          <div>
            <span className="font-mono text-xs uppercase tracking-[0.2em] text-orange-700 font-bold">
              Safety Portal
            </span>
            <h3 className="font-display text-xl sm:text-2xl font-black mt-1 leading-none">
              Dispatch Users & Logins
            </h3>
            <p className="text-sm text-slate-600 mt-1 max-w-xl">
              Add or remove Safety personnel and issue per-user passwords. Safety
              users sign in at <strong>/safety-portal/login</strong> and only see
              Safety-scoped data (overview KPIs, corrective actions, and — in later
              phases — fire extinguishers, training records, and document library).
            </p>
          </div>
        </div>
        <Button variant="outline" onClick={refresh} disabled={loading} className="h-9" data-testid="admin-dispatch-users-refresh">
          {loading ? <Loader2 className="w-4 h-4 mr-1 animate-spin" /> : <RefreshCcw className="w-4 h-4 mr-1" />}
          Refresh
        </Button>
      </div>

      {/* Add user row */}
      <div className="grid grid-cols-1 md:grid-cols-5 gap-2 mb-4 p-3 bg-slate-50 rounded-md border border-slate-200">
        <Input value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} placeholder="Name" className={inputCls} data-testid="admin-safety-add-name" />
        <Input value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} placeholder="Email" className={inputCls} data-testid="admin-safety-add-email" />
        <Input value={form.phone} onChange={(e) => setForm({ ...form, phone: e.target.value })} placeholder="Phone (optional)" className={inputCls} data-testid="admin-safety-add-phone" />
        <Select value={form.role} onValueChange={(v) => setForm({ ...form, role: v })}>
          <SelectTrigger className={inputCls} data-testid="admin-safety-add-role"><SelectValue /></SelectTrigger>
          <SelectContent>
            {ROLE_OPTIONS.map((r) => <SelectItem key={r} value={r}>{r}</SelectItem>)}
          </SelectContent>
        </Select>
        <Button onClick={addUser} disabled={adding} className="bg-orange-700 hover:bg-cyan-800 text-white h-10" data-testid="admin-safety-add-submit">
          {adding ? <Loader2 className="w-4 h-4 mr-1 animate-spin" /> : <Plus className="w-4 h-4 mr-1" />}
          Add User
        </Button>
      </div>

      {/* User list */}
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead className="bg-slate-100 text-slate-700 text-xs uppercase tracking-[0.15em] font-mono">
            <tr>
              <th className="text-left px-3 py-2">Name</th>
              <th className="text-left px-3 py-2">Email</th>
              <th className="text-left px-3 py-2">Role</th>
              <th className="text-left px-3 py-2">Phone</th>
              <th className="text-center px-3 py-2">Status</th>
              <th className="text-center px-3 py-2">Password</th>
              <th className="text-right px-3 py-2">Actions</th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr><td colSpan={7} className="px-3 py-6 text-center text-slate-500">Loading…</td></tr>
            ) : users.length === 0 ? (
              <tr><td colSpan={7} className="px-3 py-6 text-center text-slate-500">No Dispatch users yet. Add one above.</td></tr>
            ) : users.map((u) => {
              const isEditing = editingId === u.id;
              return (
                <tr key={u.id} className="border-t border-slate-100" data-testid={`admin-safety-row-${u.id}`}>
                  <td className="px-3 py-2 font-semibold">
                    {isEditing ? (
                      <Input value={editDraft.name} onChange={(e) => setEditDraft({ ...editDraft, name: e.target.value })} className="h-8 text-sm" />
                    ) : u.name}
                  </td>
                  <td className="px-3 py-2 text-slate-700">
                    {isEditing ? (
                      <Input value={editDraft.email} onChange={(e) => setEditDraft({ ...editDraft, email: e.target.value })} className="h-8 text-sm" />
                    ) : (
                      <a href={`mailto:${u.email}`} className="text-blue-700 hover:underline inline-flex items-center gap-1">
                        <Mail className="w-3.5 h-3.5" /> {u.email}
                      </a>
                    )}
                  </td>
                  <td className="px-3 py-2">
                    {isEditing ? (
                      <Select value={editDraft.role} onValueChange={(v) => setEditDraft({ ...editDraft, role: v })}>
                        <SelectTrigger className="h-8"><SelectValue /></SelectTrigger>
                        <SelectContent>{ROLE_OPTIONS.map((r) => <SelectItem key={r} value={r}>{r}</SelectItem>)}</SelectContent>
                      </Select>
                    ) : (
                      <span className="inline-block px-2 py-0.5 rounded bg-slate-100 text-slate-700 text-xs font-mono">{u.role || "Dispatcher"}</span>
                    )}
                  </td>
                  <td className="px-3 py-2 text-slate-700">
                    {isEditing ? (
                      <Input value={editDraft.phone} onChange={(e) => setEditDraft({ ...editDraft, phone: e.target.value })} className="h-8 text-sm" />
                    ) : (u.phone || "—")}
                  </td>
                  <td className="px-3 py-2 text-center">
                    <button
                      onClick={() => toggleDisabled(u)}
                      disabled={savingId === u.id}
                      className={`inline-flex items-center gap-1 px-2 py-1 rounded text-xs font-bold uppercase ${u.disabled ? "bg-red-100 text-red-700" : "bg-emerald-100 text-emerald-800"}`}
                      data-testid={`admin-safety-toggle-disabled-${u.id}`}
                    >
                      {u.disabled ? <><ShieldOff className="w-3 h-3" />Disabled</> : <><ShieldCheck className="w-3 h-3" />Active</>}
                    </button>
                  </td>
                  <td className="px-3 py-2 text-center">
                    <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-mono ${u.has_password ? "bg-blue-100 text-blue-800" : "bg-amber-100 text-amber-800"}`}>
                      {u.has_password ? "Set" : "Not Set"}
                    </span>
                  </td>
                  <td className="px-3 py-2 text-right">
                    {isEditing ? (
                      <div className="inline-flex gap-1">
                        <Button size="sm" variant="outline" onClick={() => setEditingId(null)} className="h-8"><X className="w-3.5 h-3.5" /></Button>
                        <Button size="sm" onClick={() => saveEdit(u)} className="bg-emerald-600 hover:bg-emerald-700 text-white h-8" data-testid={`admin-safety-save-${u.id}`}>
                          {savingId === u.id ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Save className="w-3.5 h-3.5" />}
                        </Button>
                      </div>
                    ) : (
                      <div className="inline-flex gap-1">
                        <Button size="sm" variant="outline" onClick={() => startEdit(u)} className="h-8" title="Edit" data-testid={`admin-safety-edit-${u.id}`}><Pencil className="w-3.5 h-3.5" /></Button>
                        <Button size="sm" variant="outline" onClick={() => issuePassword(u)} className="h-8" title="Issue password" data-testid={`admin-safety-pw-${u.id}`}><KeyRound className="w-3.5 h-3.5" /></Button>
                        <Button size="sm" variant="outline" onClick={() => removeUser(u)} className="border-red-300 text-red-700 hover:bg-red-50 h-8" title="Delete" data-testid={`admin-safety-delete-${u.id}`}><Trash2 className="w-3.5 h-3.5" /></Button>
                      </div>
                    )}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      {/* Password reveal */}
      <Dialog open={showPwReveal} onOpenChange={setShowPwReveal}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle>Password Issued</DialogTitle>
            <DialogDescription>
              Copy this password and share it with {pwReveal.name} via a secure channel. It will not be shown again.
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-3">
            <div>
              <Label className="text-xs uppercase tracking-[0.15em] font-mono text-slate-600">Email</Label>
              <div className="font-mono text-sm bg-slate-50 border border-slate-200 rounded px-3 py-2">{pwReveal.email}</div>
            </div>
            <div>
              <Label className="text-xs uppercase tracking-[0.15em] font-mono text-slate-600">Password</Label>
              <div className="flex items-center gap-2">
                <div className="font-mono text-base flex-1 bg-amber-50 border-2 border-amber-300 rounded px-3 py-2 select-all" data-testid="admin-safety-pw-reveal">
                  {pwReveal.password}
                </div>
                <Button onClick={copyPw} className="h-10" variant="outline"><Copy className="w-4 h-4" /></Button>
              </div>
            </div>
            <p className="text-xs text-amber-800 bg-amber-50 border border-amber-200 rounded px-3 py-2">
              User will be prompted to change this on first login.
            </p>
          </div>
          <DialogFooter>
            <Button onClick={() => setShowPwReveal(false)} className="bg-slate-700 hover:bg-slate-800 text-white">Done</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
