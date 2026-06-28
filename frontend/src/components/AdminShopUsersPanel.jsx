// AdminShopUsersPanel — manage MASCI Shop accounts (Shop Manager,
// Mechanics, Parts Coordinator). Mirrors the AdminPMPanel pattern:
// list / add / edit / disable / delete + issue per-user passwords.
//
// Backend:
//   GET    /api/admin/shop-users
//   POST   /api/admin/shop-users        {name, email, phone?, role?, is_active?}
//   PATCH  /api/admin/shop-users/:id    (partial)
//   DELETE /api/admin/shop-users/:id
//   POST   /api/admin/shop-users/:id/set-password  {password?, must_change?}
//   POST   /api/admin/shop-users/:id/disable       {disabled: true|false}
//
// Once a shop user has a password they can sign in at /shop/login with
// their email + password. Email submissions for failed Pre-Ops route
// to SHOP_MANAGER_EMAIL (default shopmanager@mascigc.com).

import React, { useEffect, useState } from "react";
import {
  Wrench, Plus, Trash2, RefreshCcw, Pencil, Save, X, KeyRound, Copy,
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
import { useBranding } from "@/lib/BrandingProvider";

// Track 15.1 (2026-06-16) — Defect 5 fix: extended shop role catalog
// to include Equipment / Asset Management labels that the operational
// vocabulary uses. `role` is a free-text label on the shop_users
// record (backend does not permission-gate on it). Asset-admin
// authority is granted separately via the `is_asset_admin` boolean
// on the directory record, not by role name. Adding labels here is
// safe and additive — no backend or permission migration required.
const ROLE_OPTIONS = [
  "Shop Manager",
  "Equipment Manager",
  "Asset Manager",
  "Asset Administrator",
  "Fleet Coordinator",
  "Mechanic",
  "Parts Coordinator",
  "Service Writer",
  "Shop Representative",
  "Other",
];

const inputCls =
  "h-10 text-sm border-2 border-slate-300 focus-visible:ring-2 focus-visible:ring-orange-600";

export default function AdminShopUsersPanel() {
  const branding = useBranding();
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [adding, setAdding] = useState(false);
  const [savingId, setSavingId] = useState(null);
  const [editingId, setEditingId] = useState(null);
  const [editDraft, setEditDraft] = useState({});
  const [form, setForm] = useState({ name: "", email: "", phone: "", role: "Mechanic" });

  // Password reveal modal
  const [showPwReveal, setShowPwReveal] = useState(false);
  const [pwReveal, setPwReveal] = useState({ name: "", email: "", password: "", must_change: true });

  // Issue-password choice dialog (Show / Email / Custom)
  const [pwChoice, setPwChoice] = useState({ open: false, user: null, sending: false });
  const [customPw, setCustomPw] = useState("");

  const refresh = async () => {
    setLoading(true);
    try {
      const r = await api.get("/admin/shop-users");
      setUsers(r.data?.items || []);
    } catch (err) {
      toast.error(err?.response?.data?.detail || "Could not load shop users");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { refresh(); /* eslint-disable-next-line */ }, []);

  const addUser = async () => {
    if (!form.name.trim()) return toast.error("Name required");
    if (!form.email.trim() || !form.email.includes("@")) return toast.error("Valid email required");
    setAdding(true);
    try {
      await api.post("/admin/shop-users", form);
      toast.success("Shop user added");
      setForm({ name: "", email: "", phone: "", role: "Mechanic" });
      refresh();
    } catch (err) {
      toast.error(err?.response?.data?.detail || "Could not add user");
    } finally {
      setAdding(false);
    }
  };

  const startEdit = (u) => {
    setEditingId(u.id);
    setEditDraft({ name: u.name || "", email: u.email || "", phone: u.phone || "", role: u.role || "Mechanic" });
  };

  const saveEdit = async (u) => {
    setSavingId(u.id);
    try {
      await api.patch(`/admin/shop-users/${u.id}`, editDraft);
      toast.success("Saved");
      setEditingId(null);
      refresh();
    } catch (err) {
      toast.error(err?.response?.data?.detail || "Save failed");
    } finally {
      setSavingId(null);
    }
  };

  const toggleActive = async (u) => {
    setSavingId(u.id);
    try {
      await api.patch(`/admin/shop-users/${u.id}`, { is_active: !u.is_active });
      refresh();
    } catch {
      toast.error("Could not update");
    } finally {
      setSavingId(null);
    }
  };

  const toggleDisabled = async (u) => {
    setSavingId(u.id);
    try {
      await api.post(`/admin/shop-users/${u.id}/disable`, { disabled: !u.disabled });
      refresh();
    } catch {
      toast.error("Could not update");
    } finally {
      setSavingId(null);
    }
  };

  const removeUser = async (u) => {
    if (!window.confirm(`Permanently delete shop user ${u.name}?`)) return;
    try {
      await api.delete(`/admin/shop-users/${u.id}`);
      toast.success("Removed");
      refresh();
    } catch (err) {
      toast.error(err?.response?.data?.detail || "Could not delete");
    }
  };

  const issuePassword = async (u, customPassword = null) => {
    if (customPassword !== null && customPassword.length < 6) {
      toast.error("Custom password must be at least 6 characters");
      return;
    }
    try {
      const r = await api.post(`/admin/shop-users/${u.id}/set-password`, {
        password: customPassword || undefined,
        must_change: true,
      });
      setPwReveal({
        name: u.name, email: u.email,
        password: r.data?.temp_password || customPassword,
        must_change: r.data?.must_change_password,
      });
      setShowPwReveal(true);
      refresh();
    } catch (err) {
      toast.error(err?.response?.data?.detail || "Could not set password");
    }
  };

  const emailWelcome = async (u) => {
    setPwChoice((p) => ({ ...p, sending: true }));
    try {
      const payload = { must_change: true };
      if (customPw.trim()) payload.password = customPw.trim();
      const r = await api.post(`/admin/shop-users/${u.id}/email-welcome`, payload);
      if (r.data?.ok) {
        toast.success(`Welcome email sent to ${r.data.sent_to}`);
        setPwChoice({ open: false, user: null, sending: false });
        setCustomPw("");
        refresh();
      } else {
        toast.error("Email send failed");
        setPwChoice((p) => ({ ...p, sending: false }));
      }
    } catch (err) {
      toast.error(err?.response?.data?.detail || "Email send failed");
      setPwChoice((p) => ({ ...p, sending: false }));
    }
  };

  const showOnScreen = async (u) => {
    setPwChoice({ open: false, user: null, sending: false });
    const custom = customPw.trim();
    setCustomPw("");
    await issuePassword(u, custom || null);
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
    <div className="border border-slate-200 rounded-md p-5 bg-white" data-testid="admin-shop-users-panel">
      <div className="flex items-start justify-between gap-3 mb-4">
        <div className="flex items-start gap-3">
          <div className="inline-flex items-center justify-center w-12 h-12 rounded-md bg-orange-600 text-white shrink-0">
            <Wrench className="w-6 h-6" />
          </div>
          <div>
            <span className="font-mono text-xs uppercase tracking-[0.2em] text-orange-700 font-bold">
              Shop Console
            </span>
            <h3 className="font-display text-xl sm:text-2xl font-black mt-1 leading-none">
              Shop Users & Logins
            </h3>
            <p className="text-sm text-slate-600 mt-1 max-w-xl">
              Add or remove shop personnel and issue per-user passwords. Failed
              Pre-Op submissions auto-email <strong>{branding.operations_email || "your shop manager"}</strong>.
            </p>
          </div>
        </div>
        <Button
          variant="outline"
          onClick={refresh}
          disabled={loading}
          className="h-9"
          data-testid="admin-shop-users-refresh"
        >
          {loading ? <Loader2 className="w-4 h-4 mr-1 animate-spin" /> : <RefreshCcw className="w-4 h-4 mr-1" />}
          Refresh
        </Button>
      </div>

      {/* Add user row */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-x-6 gap-y-3 mb-4 p-3 bg-slate-50 rounded-md border border-slate-200">
        <Input value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} placeholder="Name" className={inputCls} data-testid="admin-shop-add-name" />
        <Input value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} placeholder="Email" className={inputCls} data-testid="admin-shop-add-email" />
        <Input value={form.phone} onChange={(e) => setForm({ ...form, phone: e.target.value })} placeholder="Phone (optional)" className={inputCls} data-testid="admin-shop-add-phone" />
        <Select value={form.role} onValueChange={(v) => setForm({ ...form, role: v })}>
          <SelectTrigger className={inputCls} data-testid="admin-shop-add-role"><SelectValue /></SelectTrigger>
          <SelectContent>
            {ROLE_OPTIONS.map((r) => <SelectItem key={r} value={r}>{r}</SelectItem>)}
          </SelectContent>
        </Select>
        <Button onClick={addUser} disabled={adding} className="bg-orange-600 hover:bg-orange-700 text-white h-10" data-testid="admin-shop-add-submit">
          {adding ? <Loader2 className="w-4 h-4 mr-1 animate-spin" /> : <Plus className="w-4 h-4 mr-1" />}
          Add User
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
              <tr><td colSpan={7} className="px-3 py-6 text-center text-slate-500">No shop users yet. Add one above.</td></tr>
            ) : users.map((u) => {
              const isEditing = editingId === u.id;
              return (
                <tr key={u.id} className="border-t border-slate-100" data-testid={`admin-shop-row-${u.id}`}>
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
                      <span className="inline-block px-2 py-0.5 rounded bg-slate-100 text-slate-700 text-xs font-mono">{u.role || "Mechanic"}</span>
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
                      data-testid={`admin-shop-toggle-disabled-${u.id}`}
                    >
                      {u.disabled ? <><ShieldOff className="w-3 h-3" />Disabled</> : <><ShieldCheck className="w-3 h-3" />Active</>}
                    </button>
                    <IamStandardCells user={u} portal="shop" compact />
                  </td>
                  <td className="px-3 py-2 text-center">
                    <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-mono ${u.has_password ? "bg-blue-100 text-blue-800" : "bg-amber-100 text-amber-800"}`}>
                      {u.has_password ? "Set" : "Not Set"}
                    </span>
                  </td>
                  <td className="px-3 py-2 text-right">
                    {isEditing ? (
                      <div className="inline-flex gap-1">
                        <Button size="sm" variant="outline" onClick={() => setEditingId(null)} className="h-8" aria-label="Cancel edit" title="Cancel" data-testid={`admin-shop-cancel-${u.id}`}><X className="w-3.5 h-3.5" /></Button>
                        <Button size="sm" onClick={() => saveEdit(u)} className="bg-emerald-600 hover:bg-emerald-700 text-white h-8" data-testid={`admin-shop-save-${u.id}`}>
                          {savingId === u.id ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Save className="w-3.5 h-3.5" />}
                        </Button>
                      </div>
                    ) : (
                      <div className="inline-flex gap-1">
                        <Button size="sm" variant="outline" onClick={() => startEdit(u)} className="h-8" title="Edit" data-testid={`admin-shop-edit-${u.id}`}><Pencil className="w-3.5 h-3.5" /></Button>
                        <Button size="sm" variant="outline" onClick={() => setPwChoice({ open: true, user: u, sending: false })} className="h-8" title="Issue password" data-testid={`admin-shop-pw-${u.id}`}><KeyRound className="w-3.5 h-3.5" /></Button>
                        <Button size="sm" variant="outline" onClick={() => removeUser(u)} className="border-red-300 text-red-700 hover:bg-red-50 h-8" title="Delete" data-testid={`admin-shop-delete-${u.id}`}><Trash2 className="w-3.5 h-3.5" /></Button>
                      </div>
                    )}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      {/* Password reveal dialog */}
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
                <div className="font-mono text-base flex-1 bg-amber-50 border-2 border-amber-300 rounded px-3 py-2 select-all" data-testid="admin-shop-pw-reveal">
                  {pwReveal.password}
                </div>
                <Button onClick={copyPw} className="h-10" variant="outline" aria-label="Copy password" title="Copy password"><Copy className="w-4 h-4" /></Button>
              </div>
            </div>
            {pwReveal.must_change && (
              <p className="text-xs text-amber-800 bg-amber-50 border border-amber-200 rounded px-3 py-2">
                User will be prompted to change this on first login.
              </p>
            )}
          </div>
          <DialogFooter>
            <Button onClick={() => setShowPwReveal(false)} className="bg-slate-700 hover:bg-slate-800 text-white">Done</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Issue password — choose Email vs Show on Screen vs Custom */}
      <Dialog open={pwChoice.open} onOpenChange={(open) => {
        if (pwChoice.sending) return;
        if (!open) setCustomPw("");
        setPwChoice({ open, user: pwChoice.user, sending: false });
      }}>
        <DialogContent className="sm:max-w-lg">
          <DialogHeader>
            <DialogTitle>
              {pwChoice.user?.has_password
                ? `Reset password for ${pwChoice.user?.name}`
                : `Issue password for ${pwChoice.user?.name}`}
            </DialogTitle>
            <DialogDescription className="leading-relaxed text-sm">
              Three ways to issue (or reset) this shop user's password — pick whichever fits the situation.
              <br /><strong>Email to User</strong> (recommended for remote) — auto-generates a temp pw and emails it directly to the user.
              <br /><strong>Show on Screen</strong> — temp pw rendered in a copy dialog, in case you'd rather text/call them.
              <br />Or type a <strong>custom</strong> password below. The user must rotate to their own on first login regardless.
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
                placeholder="At least 6 characters"
                className="h-10 text-sm mt-1 font-mono"
                data-testid="admin-shop-set-password-custom-input"
              />
            </div>
          </div>
          <DialogFooter className="flex-wrap gap-2 pt-2">
            <Button
              variant="outline"
              onClick={() => { setCustomPw(""); setPwChoice({ open: false, user: null, sending: false }); }}
              disabled={pwChoice.sending}
              data-testid="admin-shop-pw-choice-cancel"
            >
              Cancel
            </Button>
            <Button
              variant="outline"
              onClick={() => showOnScreen(pwChoice.user)}
              disabled={pwChoice.sending}
              data-testid="admin-shop-pw-choice-show"
            >
              <KeyRound className="w-4 h-4 mr-1" />
              {customPw.trim() ? "Set custom · Show" : "Show on Screen"}
            </Button>
            <Button
              onClick={() => emailWelcome(pwChoice.user)}
              disabled={pwChoice.sending || !pwChoice.user?.email}
              className="bg-orange-600 hover:bg-orange-700 text-white"
              data-testid="admin-shop-pw-choice-email"
            >
              {pwChoice.sending ? <Loader2 className="w-4 h-4 mr-1 animate-spin" /> : <Mail className="w-4 h-4 mr-1" />}
              {customPw.trim() ? "Set custom · Email" : "Email to User"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
