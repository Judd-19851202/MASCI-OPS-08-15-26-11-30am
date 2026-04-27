import React, { useEffect, useState } from "react";
import {
  Plus,
  Loader2,
  UserCheck,
  UserX,
  KeyRound,
  ShieldCheck,
  Shield,
  User,
  Users as UsersIcon,
} from "lucide-react";
import { toast } from "sonner";
import { api } from "@/lib/api";
import { useAuth } from "@/lib/authContext";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from "@/components/ui/dialog";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";

function apiErr(detail, fallback) {
  if (!detail) return fallback;
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail)) return detail.map((e) => e?.msg || JSON.stringify(e)).join(" ");
  return detail?.msg || String(detail);
}

const ROLE_LABELS = {
  owner: { label: "Owner", Icon: ShieldCheck, cls: "text-red-700" },
  admin: { label: "Admin", Icon: Shield, cls: "text-amber-700" },
  member: { label: "Member", Icon: User, cls: "text-slate-600" },
};

export default function UsersAdmin() {
  const { user: me } = useAuth();
  const [users, setUsers] = useState(null);
  const [showNew, setShowNew] = useState(false);
  const [reset, setReset] = useState(null);
  const [saving, setSaving] = useState(false);

  const load = async () => {
    try {
      const r = await api.get("/users");
      setUsers(r.data || []);
    } catch (err) {
      toast.error(apiErr(err?.response?.data?.detail, "Failed to load users"));
    }
  };
  useEffect(() => { load(); }, []);

  const onUpdate = async (id, patch) => {
    setSaving(true);
    try {
      await api.put(`/users/${id}`, patch);
      toast.success("Saved");
      await load();
    } catch (err) {
      toast.error(apiErr(err?.response?.data?.detail, "Update failed"));
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="p-8 sm:p-10 max-w-5xl" data-testid="users-admin">
      <div className="flex items-start justify-between gap-4 flex-wrap mb-6">
        <div>
          <div className="font-mono text-[10px] uppercase tracking-[0.3em] text-red-700 font-bold">Admin · Users</div>
          <h1 className="font-display text-2xl sm:text-3xl font-black tracking-tight text-slate-900 mt-1">Crew Hub users</h1>
          <p className="text-slate-600 text-sm mt-1 max-w-xl">
            Owners and admins can add people, change roles, reset passwords, and deactivate accounts.
          </p>
        </div>
        <Button
          onClick={() => setShowNew(true)}
          className="h-11 bg-red-700 hover:bg-red-800 text-white font-bold uppercase tracking-wide text-sm border-b-2 border-red-900"
          data-testid="new-user-btn"
        >
          <Plus className="w-4 h-4 mr-2" /> Invite user
        </Button>
      </div>

      {users === null && (
        <div className="flex items-center gap-2 text-slate-500 py-10 justify-center">
          <Loader2 className="w-5 h-5 animate-spin" /> Loading users…
        </div>
      )}

      {users !== null && (
        <div className="bg-white border-2 border-slate-200 rounded-md overflow-hidden">
          <table className="w-full text-sm" data-testid="users-table">
            <thead className="bg-slate-900 text-white font-mono text-[10px] uppercase tracking-[0.2em]">
              <tr>
                <th className="text-left px-4 py-3">Name</th>
                <th className="text-left px-4 py-3">Email</th>
                <th className="text-left px-4 py-3">Role</th>
                <th className="text-left px-4 py-3">Status</th>
                <th className="text-right px-4 py-3">Actions</th>
              </tr>
            </thead>
            <tbody>
              {users.length === 0 && (
                <tr>
                  <td colSpan={5} className="px-4 py-8 text-center text-slate-500 italic">
                    No users yet.
                  </td>
                </tr>
              )}
              {users.map((u) => {
                const meta = ROLE_LABELS[u.role] || ROLE_LABELS.member;
                const Icon = meta.Icon;
                const isSelf = u.id === me?.id;
                return (
                  <tr key={u.id} className="border-t border-slate-100" data-testid={`user-row-${u.id}`}>
                    <td className="px-4 py-3 font-display font-bold text-slate-900">{u.name}</td>
                    <td className="px-4 py-3 font-mono text-xs text-slate-700 truncate">{u.email}</td>
                    <td className="px-4 py-3">
                      <Select
                        value={u.role}
                        onValueChange={(v) => onUpdate(u.id, { role: v })}
                        disabled={saving || isSelf}
                      >
                        <SelectTrigger className="h-8 w-32 text-xs">
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="owner">Owner</SelectItem>
                          <SelectItem value="admin">Admin</SelectItem>
                          <SelectItem value="member">Member</SelectItem>
                        </SelectContent>
                      </Select>
                    </td>
                    <td className="px-4 py-3">
                      {u.is_active ? (
                        <span className="inline-flex items-center gap-1 text-emerald-700 font-mono text-[10px] uppercase tracking-[0.15em] font-bold">
                          <UserCheck className="w-3 h-3" /> Active
                        </span>
                      ) : (
                        <span className="inline-flex items-center gap-1 text-slate-500 font-mono text-[10px] uppercase tracking-[0.15em] font-bold">
                          <UserX className="w-3 h-3" /> Disabled
                        </span>
                      )}
                      {u.must_change_password && (
                        <div className="text-[10px] font-mono uppercase tracking-[0.15em] text-amber-700 mt-1">· must reset pwd</div>
                      )}
                    </td>
                    <td className="px-4 py-3 text-right">
                      <button
                        onClick={() => setReset(u)}
                        className="text-xs font-mono uppercase tracking-[0.15em] text-slate-600 hover:text-red-700 font-bold inline-flex items-center gap-1 mr-3"
                        data-testid={`reset-pw-${u.id}`}
                      >
                        <KeyRound className="w-3 h-3" /> Reset PW
                      </button>
                      <button
                        onClick={() => onUpdate(u.id, { is_active: !u.is_active })}
                        disabled={saving || isSelf}
                        className="text-xs font-mono uppercase tracking-[0.15em] text-slate-600 hover:text-red-700 font-bold inline-flex items-center gap-1 disabled:opacity-40 disabled:hover:text-slate-600"
                        data-testid={`toggle-active-${u.id}`}
                      >
                        {u.is_active ? <><UserX className="w-3 h-3" /> Disable</> : <><UserCheck className="w-3 h-3" /> Enable</>}
                      </button>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}

      <NewUserDialog open={showNew} onOpenChange={setShowNew} onCreated={load} />
      <ResetPasswordDialog user={reset} onOpenChange={(o) => !o && setReset(null)} onDone={load} />
    </div>
  );
}

function NewUserDialog({ open, onOpenChange, onCreated }) {
  const [email, setEmail] = useState("");
  const [name, setName] = useState("");
  const [role, setRole] = useState("member");
  const [password, setPassword] = useState("");
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    if (!open) { setEmail(""); setName(""); setRole("member"); setPassword(""); }
  }, [open]);

  const onSave = async (e) => {
    e.preventDefault();
    if (password.length < 10) {
      toast.error("Temp password must be at least 10 characters.");
      return;
    }
    setSaving(true);
    try {
      await api.post("/users", { email: email.trim().toLowerCase(), name: name.trim(), role, password });
      toast.success(`Invited ${email}. Share the temp password — they'll be asked to change it on first login.`);
      onCreated();
      onOpenChange(false);
    } catch (err) {
      toast.error(apiErr(err?.response?.data?.detail, "Invite failed"));
    } finally {
      setSaving(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent data-testid="new-user-dialog">
        <DialogHeader>
          <DialogTitle className="font-display">Invite user</DialogTitle>
        </DialogHeader>
        <form onSubmit={onSave} className="space-y-4">
          <div>
            <Label>Email</Label>
            <Input type="email" required value={email} onChange={(e) => setEmail(e.target.value)} className="mt-1.5" data-testid="new-user-email" />
          </div>
          <div>
            <Label>Name</Label>
            <Input required value={name} onChange={(e) => setName(e.target.value)} className="mt-1.5" data-testid="new-user-name" />
          </div>
          <div>
            <Label>Role</Label>
            <Select value={role} onValueChange={setRole}>
              <SelectTrigger className="mt-1.5" data-testid="new-user-role"><SelectValue /></SelectTrigger>
              <SelectContent>
                <SelectItem value="owner">Owner — full access + user management</SelectItem>
                <SelectItem value="admin">Admin — user management, all projects</SelectItem>
                <SelectItem value="member">Member — projects they're added to</SelectItem>
              </SelectContent>
            </Select>
          </div>
          <div>
            <Label>Temporary password (≥ 10 chars)</Label>
            <Input required minLength={10} value={password} onChange={(e) => setPassword(e.target.value)} className="mt-1.5" placeholder="e.g. Welcome2MASCI!" data-testid="new-user-password" />
            <p className="text-xs text-slate-500 mt-1">Share this securely. The user must change it on first login.</p>
          </div>
          <DialogFooter>
            <Button type="button" variant="outline" onClick={() => onOpenChange(false)}>Cancel</Button>
            <Button type="submit" disabled={saving} className="bg-red-700 hover:bg-red-800 text-white font-bold uppercase tracking-wide" data-testid="new-user-save">
              {saving ? <Loader2 className="w-4 h-4 animate-spin" /> : "Invite"}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}

function ResetPasswordDialog({ user, onOpenChange, onDone }) {
  const [newPw, setNewPw] = useState("");
  const [saving, setSaving] = useState(false);

  useEffect(() => { if (!user) setNewPw(""); }, [user]);

  const onSave = async (e) => {
    e.preventDefault();
    if (newPw.length < 10) {
      toast.error("Password must be at least 10 characters.");
      return;
    }
    setSaving(true);
    try {
      await api.post(`/users/${user.id}/reset-password`, { new_password: newPw });
      toast.success(`Reset. Share the new password with ${user.name}.`);
      onDone();
      onOpenChange(false);
    } catch (err) {
      toast.error(apiErr(err?.response?.data?.detail, "Reset failed"));
    } finally {
      setSaving(false);
    }
  };

  return (
    <Dialog open={!!user} onOpenChange={onOpenChange}>
      <DialogContent data-testid="reset-password-dialog">
        <DialogHeader>
          <DialogTitle className="font-display">Reset password for {user?.name}</DialogTitle>
        </DialogHeader>
        <form onSubmit={onSave} className="space-y-4">
          <div>
            <Label>New temporary password (≥ 10 chars)</Label>
            <Input required minLength={10} value={newPw} onChange={(e) => setNewPw(e.target.value)} className="mt-1.5" data-testid="reset-new-password" />
            <p className="text-xs text-slate-500 mt-1">The user will be forced to change it on next login.</p>
          </div>
          <DialogFooter>
            <Button type="button" variant="outline" onClick={() => onOpenChange(false)}>Cancel</Button>
            <Button type="submit" disabled={saving} className="bg-red-700 hover:bg-red-800 text-white font-bold uppercase tracking-wide" data-testid="reset-save">
              {saving ? <Loader2 className="w-4 h-4 animate-spin" /> : "Reset password"}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
