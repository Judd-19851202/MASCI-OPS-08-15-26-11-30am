// AdminSafetyUsersPanel — manage MASCI Safety Portal accounts (Safety
// Manager, Safety Coordinator, Safety Officer). Mirrors
// AdminHRUsersPanel pattern with the cyan-700 accent.
//
// iter243 — Welcome-email delivery parity with HR/PM/Shop/Dispatch.
// "Add User" now defaults to emailing a branded Safety Portal welcome
// with the temp password + sign-in link. "Reset Password" opens a
// choice dialog where the admin picks Email-to-User vs Show-on-Screen,
// optionally with an admin-typed custom password.
//
// Backend:
//   GET    /api/admin/safety-users
//   POST   /api/admin/safety-users        {name, email, phone?, role?, delivery, custom_password?}
//   PATCH  /api/admin/safety-users/:id    (partial)
//   DELETE /api/admin/safety-users/:id
//   POST   /api/admin/safety-users/:id/reset-password  {delivery, custom_password?}
import React, { useEffect, useState } from "react";
import {
  ShieldAlert, Plus, Trash2, RefreshCcw, Pencil, Save, X, KeyRound, Copy,
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
import { IamStandardCells } from "@/components/iam/IamStandardCells";
import { toast } from "sonner";

const ROLE_OPTIONS = ["Safety Manager", "Safety Coordinator", "Safety Officer", "Other"];
const inputCls = "h-10 text-sm border-2 border-slate-300 focus-visible:ring-2 focus-visible:ring-cyan-700";

export default function AdminSafetyUsersPanel() {
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [adding, setAdding] = useState(false);
  const [savingId, setSavingId] = useState(null);
  const [editingId, setEditingId] = useState(null);
  const [editDraft, setEditDraft] = useState({});
  const [form, setForm] = useState({ name: "", email: "", phone: "", role: "Safety Coordinator" });

  // Password reveal modal (used when admin chose Show-on-Screen or set a custom pw)
  const [showPwReveal, setShowPwReveal] = useState(false);
  const [pwReveal, setPwReveal] = useState({ name: "", email: "", password: "" });

  // Issue/reset-password choice modal (iter243)
  const [pwChoice, setPwChoice] = useState({ open: false, user: null, sending: false });
  const [customPw, setCustomPw] = useState("");

  const refresh = async () => {
    setLoading(true);
    try {
      const r = await api.get("/admin/safety-users");
      // Backend returns a plain array for safety users
      setUsers(Array.isArray(r.data) ? r.data : (r.data?.users || []));
    } catch (err) {
      toast.error(err?.response?.data?.detail || "Could not load Safety users");
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
      // iter243 — Default: email a branded welcome with auto-generated
      // temp password. Mirrors the HR/PM/Shop/Dispatch pattern.
      const r = await api.post("/admin/safety-users", { ...form, delivery: "email" });
      const u = r.data?.user || {};
      toast.success(`Safety user added — welcome email sent to ${u.email}`);
      setForm({ name: "", email: "", phone: "", role: "Safety Coordinator" });
      refresh();
    } catch (err) {
      toast.error(err?.response?.data?.detail || "Could not add user");
    } finally {
      setAdding(false);
    }
  };

  const startEdit = (u) => {
    setEditingId(u.id);
    setEditDraft({ name: u.name || "", email: u.email || "", phone: u.phone || "", role: u.role || "Safety Coordinator" });
  };

  const saveEdit = async (u) => {
    setSavingId(u.id);
    try {
      await api.patch(`/admin/safety-users/${u.id}`, editDraft);
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
      await api.patch(`/admin/safety-users/${u.id}`, { disabled: !u.disabled });
      refresh();
    } catch {
      toast.error("Could not update");
    } finally {
      setSavingId(null);
    }
  };

  const removeUser = async (u) => {
    if (!window.confirm(`Permanently delete Safety user ${u.name}?`)) return;
    try {
      await api.delete(`/admin/safety-users/${u.id}`);
      toast.success("Removed");
      refresh();
    } catch (err) {
      toast.error(err?.response?.data?.detail || "Could not delete");
    }
  };

  const issueShowOnScreen = async (u) => {
    const custom = customPw.trim();
    setCustomPw("");
    setPwChoice({ open: false, user: null, sending: false });
    try {
      const payload = custom ? { delivery: "custom", custom_password: custom } : { delivery: "screen" };
      const r = await api.post(`/admin/safety-users/${u.id}/reset-password`, payload);
      setPwReveal({ name: u.name, email: u.email, password: r.data?.temp_password || custom || "" });
      setShowPwReveal(true);
      refresh();
    } catch (err) {
      toast.error(err?.response?.data?.detail || "Could not set password");
    }
  };

  const issueEmail = async (u) => {
    setPwChoice((p) => ({ ...p, sending: true }));
    try {
      const custom = customPw.trim();
      if (custom) {
        // Custom passwords are revealed on screen — backend currently
        // only emails auto-generated temp passwords. Matches HR.
        await api.post(`/admin/safety-users/${u.id}/reset-password`, { delivery: "custom", custom_password: custom });
        setPwReveal({ name: u.name, email: u.email, password: custom });
        setShowPwReveal(true);
      } else {
        await api.post(`/admin/safety-users/${u.id}/reset-password`, { delivery: "email" });
        toast.success(`Welcome email sent to ${u.email}`);
      }
      setCustomPw("");
      setPwChoice({ open: false, user: null, sending: false });
      refresh();
    } catch (err) {
      toast.error(err?.response?.data?.detail || "Email send failed");
      setPwChoice((p) => ({ ...p, sending: false }));
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
    <div className="border border-slate-200 rounded-md p-5 bg-white" data-testid="admin-safety-users-panel">
      <div className="flex items-start justify-between gap-3 mb-4">
        <div className="flex items-start gap-3">
          <div className="inline-flex items-center justify-center w-12 h-12 rounded-md bg-cyan-700 text-white shrink-0">
            <ShieldAlert className="w-6 h-6" />
          </div>
          <div>
            <span className="font-mono text-xs uppercase tracking-[0.2em] text-cyan-700 font-bold">
              Safety Portal
            </span>
            <h3 className="font-display text-xl sm:text-2xl font-black mt-1 leading-none">
              Safety Users & Logins
            </h3>
            <p className="text-sm text-slate-600 mt-1 max-w-xl">
              Add or remove Safety personnel and issue per-user passwords. Safety
              users sign in at <strong>/safety-portal/login</strong>. New users
              receive a branded Safety Portal welcome email containing their
              temp password and sign-in link — they're prompted to choose their
              own password on first login.
            </p>
          </div>
        </div>
        <Button variant="outline" onClick={refresh} disabled={loading} className="h-9" data-testid="admin-safety-users-refresh">
          {loading ? <Loader2 className="w-4 h-4 mr-1 animate-spin" /> : <RefreshCcw className="w-4 h-4 mr-1" />}
          Refresh
        </Button>
      </div>

      {/* Add user row */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-x-6 gap-y-3 mb-4 p-3 bg-slate-50 rounded-md border border-slate-200">
        <Input value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} placeholder="Name" className={inputCls} data-testid="admin-safety-add-name" />
        <Input value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} placeholder="Email" className={inputCls} data-testid="admin-safety-add-email" />
        <Input value={form.phone} onChange={(e) => setForm({ ...form, phone: e.target.value })} placeholder="Phone (optional)" className={inputCls} data-testid="admin-safety-add-phone" />
        <Select value={form.role} onValueChange={(v) => setForm({ ...form, role: v })}>
          <SelectTrigger className={inputCls} data-testid="admin-safety-add-role"><SelectValue /></SelectTrigger>
          <SelectContent>
            {ROLE_OPTIONS.map((r) => <SelectItem key={r} value={r}>{r}</SelectItem>)}
          </SelectContent>
        </Select>
        <Button onClick={addUser} disabled={adding} className="bg-cyan-700 hover:bg-cyan-800 text-white h-10" data-testid="admin-safety-add-submit">
          {adding ? <Loader2 className="w-4 h-4 mr-1 animate-spin" /> : <Mail className="w-4 h-4 mr-1" />}
          Add &amp; Email Welcome
        </Button>
      </div>

      {/* User list */}
      <div className="overflow-x-auto">
        <table className="w-full min-w-[900px] text-sm">
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
              <tr><td colSpan={7} className="px-3 py-6 text-center text-slate-500">No Safety users yet. Add one above.</td></tr>
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
                      <span className="inline-block px-2 py-0.5 rounded bg-slate-100 text-slate-700 text-xs font-mono">{u.role || "Safety Coordinator"}</span>
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
                    <IamStandardCells user={u} portal="safety" compact />
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
                        <Button size="sm" variant="outline" onClick={() => setPwChoice({ open: true, user: u, sending: false })} className="h-8" title="Issue / reset password" data-testid={`admin-safety-pw-${u.id}`}><KeyRound className="w-3.5 h-3.5" /></Button>
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

      {/* Password reveal (show-on-screen or custom pw paths) */}
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

      {/* iter243 — Issue / reset password choice modal */}
      <Dialog open={pwChoice.open} onOpenChange={(open) => {
        if (pwChoice.sending) return;
        if (!open) setCustomPw("");
        setPwChoice({ open, user: pwChoice.user, sending: false });
      }}>
        <DialogContent className="sm:max-w-lg">
          <DialogHeader>
            <DialogTitle>
              {pwChoice.user?.has_password ? `Reset password for ${pwChoice.user?.name}` : `Issue password for ${pwChoice.user?.name}`}
            </DialogTitle>
            <DialogDescription className="leading-relaxed text-sm">
              Two ways to issue (or reset) this Safety user's password. <strong>Email to User</strong> auto-generates a temp pw and sends a branded Safety Portal welcome email. <strong>Show on Screen</strong> reveals a temp pw in a copy dialog. Or type a <strong>custom</strong> password below. The user must rotate to their own on first login regardless.
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-3 pt-1">
            <div className="bg-slate-50 border border-slate-200 rounded p-3">
              <div className="font-mono text-[10px] uppercase tracking-[0.2em] text-slate-700 font-bold mb-1">Account</div>
              <div className="text-sm">
                <span className="font-bold">{pwChoice.user?.name}</span>{" "}
                <span className="font-mono text-slate-500">&lt;{pwChoice.user?.email}&gt;</span>
              </div>
            </div>
            <div>
              <Label className="font-mono text-[10px] uppercase tracking-[0.2em] text-slate-700 font-bold">
                Custom password (optional — leave blank to auto-generate)
              </Label>
              <Input
                type="text"
                value={customPw}
                onChange={(e) => setCustomPw(e.target.value)}
                placeholder="At least 8 characters"
                className="h-10 text-sm mt-1 font-mono"
                data-testid="admin-safety-pw-custom"
              />
            </div>
          </div>
          <DialogFooter className="flex-wrap gap-2 pt-2">
            <Button variant="outline" onClick={() => { setCustomPw(""); setPwChoice({ open: false, user: null, sending: false }); }} disabled={pwChoice.sending} data-testid="admin-safety-pw-cancel">
              Cancel
            </Button>
            <Button variant="outline" onClick={() => issueShowOnScreen(pwChoice.user)} disabled={pwChoice.sending} data-testid="admin-safety-pw-show">
              <KeyRound className="w-4 h-4 mr-1" />
              {customPw.trim() ? "Set custom · Show" : "Show on Screen"}
            </Button>
            <Button onClick={() => issueEmail(pwChoice.user)} disabled={pwChoice.sending || !pwChoice.user?.email} className="bg-cyan-700 hover:bg-cyan-800 text-white" data-testid="admin-safety-pw-email">
              {pwChoice.sending ? <Loader2 className="w-4 h-4 mr-1 animate-spin" /> : <Mail className="w-4 h-4 mr-1" />}
              {customPw.trim() ? "Set custom · Email" : "Email to User"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
