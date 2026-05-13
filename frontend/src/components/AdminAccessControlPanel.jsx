// AdminAccessControlPanel.jsx — Multi-portal user management (iter82)
//
// Mounts in /admin → Access Control Center. Lets admins:
//   - See every directory user (multi-portal accounts)
//   - Toggle each portal per user (admin / pm / shop / hr) via checkboxes
//   - Disable / enable an account (kills tokens instantly)
//   - Reset a user's master password (generates secure random; copy-on-screen)
//   - Add a new multi-portal user
//
// Super-admin rows are protected: the disable + delete buttons are hidden,
// the admin checkbox is locked on.

import React, { useEffect, useState } from "react";
import {
  Users, Plus, Loader2, ShieldCheck, KeyRound, Trash2,
  Power, AlertOctagon, Copy, CheckCircle2,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Dialog, DialogContent, DialogDescription, DialogFooter,
  DialogHeader, DialogTitle,
} from "@/components/ui/dialog";
import { api } from "@/lib/api";
import { toast } from "sonner";

const PORTAL_OPTIONS = [
  { key: "admin", label: "Admin", color: "bg-red-700" },
  { key: "pm",    label: "PM",    color: "bg-red-600" },
  { key: "shop",  label: "Shop",  color: "bg-orange-600" },
  { key: "hr",    label: "HR",    color: "bg-purple-700" },
];

function genTempPassword(n = 12) {
  const chars = "ABCDEFGHJKMNPQRSTUVWXYZabcdefghijkmnpqrstuvwxyz23456789";
  let out = "";
  for (let i = 0; i < n; i++) out += chars[Math.floor(Math.random() * chars.length)];
  return out + "!";
}

export default function AdminAccessControlPanel() {
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [createOpen, setCreateOpen] = useState(false);

  const refresh = async () => {
    setLoading(true);
    try {
      const r = await api.get("/admin/directory");
      setUsers(r.data?.users || []);
    } catch (err) {
      toast.error(err?.response?.data?.detail || "Failed to load directory");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { refresh(); }, []);

  const togglePortal = async (user, portalKey) => {
    if (user.is_super_admin && portalKey === "admin") {
      toast.info("Super-admin always has admin access.");
      return;
    }
    const next = user.portals.includes(portalKey)
      ? user.portals.filter((p) => p !== portalKey)
      : [...user.portals, portalKey];
    if (next.length === 0) {
      toast.error("User must have at least one portal.");
      return;
    }
    try {
      await api.patch(`/admin/directory/${user.id}`, { portals: next });
      toast.success(
        user.portals.includes(portalKey)
          ? `Removed ${portalKey.toUpperCase()} from ${user.email}`
          : `Granted ${portalKey.toUpperCase()} to ${user.email}`
      );
      refresh();
    } catch (err) {
      toast.error(err?.response?.data?.detail || "Update failed");
    }
  };

  const toggleDisabled = async (user) => {
    if (user.is_super_admin) {
      toast.error("Cannot disable a super-admin.");
      return;
    }
    if (!window.confirm(
      user.disabled
        ? `Re-enable ${user.email}? Their tokens will work again.`
        : `Disable ${user.email}? All their sign-ins will be blocked immediately.`
    )) return;
    try {
      await api.patch(`/admin/directory/${user.id}`, { disabled: !user.disabled });
      toast.success(user.disabled ? "Re-enabled" : "Disabled");
      refresh();
    } catch (err) {
      toast.error(err?.response?.data?.detail || "Update failed");
    }
  };

  const deleteUser = async (user) => {
    if (user.is_super_admin) {
      toast.error("Cannot delete a super-admin.");
      return;
    }
    if (!window.confirm(`Permanently delete ${user.email}? This cannot be undone.`)) return;
    try {
      await api.delete(`/admin/directory/${user.id}`);
      toast.success("Deleted");
      refresh();
    } catch (err) {
      toast.error(err?.response?.data?.detail || "Delete failed");
    }
  };

  const resetPassword = async (user) => {
    const temp = genTempPassword();
    if (!window.confirm(
      `Reset ${user.email}'s master password to a new one and force them to change it on next sign-in?\n\nThe new password will be shown ONCE. You'll need to deliver it to them outside the app.`
    )) return;
    try {
      await api.post(`/admin/directory/${user.id}/reset-password`, {
        new_password: temp,
        must_change: true,
      });
      // Show the temp password in a copyable toast that lasts long enough to write down
      toast.success(
        <div className="space-y-1">
          <div className="font-bold">Password reset — give to user:</div>
          <code className="text-base bg-slate-100 px-2 py-0.5 rounded">{temp}</code>
        </div>,
        { duration: 30000 }
      );
      try { await navigator.clipboard.writeText(temp); } catch { /* ignore */ }
      refresh();
    } catch (err) {
      toast.error(err?.response?.data?.detail || "Reset failed");
    }
  };

  return (
    <Card className="p-5 sm:p-6 mt-4 border-2 border-slate-300 bg-white" data-testid="access-control-panel">
      <div className="flex items-start justify-between gap-3 mb-4 flex-wrap">
        <div className="flex items-start gap-3">
          <div className="p-2 rounded-md bg-slate-900">
            <Users className="w-5 h-5 text-white" />
          </div>
          <div>
            <h3 className="font-display text-lg font-black tracking-tight text-slate-900">
              Access Control Center
            </h3>
            <p className="text-xs text-slate-600 mt-1 max-w-2xl">
              Multi-portal accounts — give a single email + master password access to
              any combination of Admin / PM / Shop / HR. Single-portal employees
              don't need a directory entry; they use the existing portal-specific
              sign-in pages.
            </p>
          </div>
        </div>
        <Button
          onClick={() => setCreateOpen(true)}
          className="bg-red-700 hover:bg-red-800 text-white font-bold uppercase tracking-wide"
          data-testid="acc-add-user-btn"
        >
          <Plus className="w-4 h-4 mr-1" /> Add user
        </Button>
      </div>

      {loading ? (
        <div className="flex items-center gap-2 text-slate-600 py-4">
          <Loader2 className="w-4 h-4 animate-spin" /> Loading directory…
        </div>
      ) : users.length === 0 ? (
        <div className="text-sm text-slate-500 italic py-3">
          No multi-portal users yet. Click "Add user" to grant someone access.
        </div>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-slate-200 text-left">
                <th className="py-2 pr-3 font-mono text-[10px] uppercase tracking-[0.2em] text-slate-500">User</th>
                {PORTAL_OPTIONS.map((p) => (
                  <th key={p.key} className="py-2 px-2 font-mono text-[10px] uppercase tracking-[0.2em] text-slate-500 text-center">
                    {p.label}
                  </th>
                ))}
                <th className="py-2 px-2 font-mono text-[10px] uppercase tracking-[0.2em] text-slate-500 text-center">Last sign-in</th>
                <th className="py-2 pl-3 font-mono text-[10px] uppercase tracking-[0.2em] text-slate-500 text-right">Actions</th>
              </tr>
            </thead>
            <tbody>
              {users.map((u) => (
                <tr
                  key={u.id}
                  className={`border-b border-slate-100 ${u.disabled ? "opacity-50" : ""}`}
                  data-testid={`acc-row-${u.email}`}
                >
                  <td className="py-2 pr-3">
                    <div className="flex items-center gap-2">
                      {u.is_super_admin && (
                        <ShieldCheck className="w-4 h-4 text-red-700" title="Super admin" />
                      )}
                      <div>
                        <div className="font-bold text-slate-900">{u.name || u.email.split("@")[0]}</div>
                        <div className="text-xs text-slate-500">{u.email}</div>
                      </div>
                    </div>
                  </td>
                  {PORTAL_OPTIONS.map((p) => {
                    const hasIt = u.portals.includes(p.key);
                    const locked = u.is_super_admin && p.key === "admin";
                    return (
                      <td key={p.key} className="py-2 px-2 text-center">
                        <input
                          type="checkbox"
                          checked={hasIt}
                          disabled={locked}
                          onChange={() => togglePortal(u, p.key)}
                          className={`w-4 h-4 accent-red-700 ${locked ? "cursor-not-allowed" : "cursor-pointer"}`}
                          data-testid={`acc-portal-${u.email}-${p.key}`}
                          title={locked ? "Locked for super-admin" : `Toggle ${p.label}`}
                        />
                      </td>
                    );
                  })}
                  <td className="py-2 px-2 text-center text-xs text-slate-600 font-mono">
                    {u.last_login_at ? new Date(u.last_login_at).toLocaleDateString() : "—"}
                  </td>
                  <td className="py-2 pl-3 text-right">
                    <div className="inline-flex gap-1">
                      <Button
                        size="sm"
                        variant="ghost"
                        onClick={() => resetPassword(u)}
                        title="Reset master password"
                        className="h-7 px-2 text-xs"
                        data-testid={`acc-reset-${u.email}`}
                      >
                        <KeyRound className="w-3 h-3" />
                      </Button>
                      {!u.is_super_admin && (
                        <>
                          <Button
                            size="sm"
                            variant="ghost"
                            onClick={() => toggleDisabled(u)}
                            title={u.disabled ? "Re-enable" : "Disable"}
                            className="h-7 px-2 text-xs"
                            data-testid={`acc-disable-${u.email}`}
                          >
                            <Power className="w-3 h-3" />
                          </Button>
                          <Button
                            size="sm"
                            variant="ghost"
                            onClick={() => deleteUser(u)}
                            title="Delete"
                            className="h-7 px-2 text-xs text-red-700"
                            data-testid={`acc-delete-${u.email}`}
                          >
                            <Trash2 className="w-3 h-3" />
                          </Button>
                        </>
                      )}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      <CreateUserDialog
        open={createOpen}
        onOpenChange={setCreateOpen}
        onCreated={refresh}
      />
    </Card>
  );
}

// ─────────────────────────────────────────────────────────────────────
function CreateUserDialog({ open, onOpenChange, onCreated }) {
  const [email, setEmail] = useState("");
  const [name, setName] = useState("");
  const [portals, setPortals] = useState({ admin: false, pm: false, shop: false, hr: false });
  const [password, setPassword] = useState("");
  const [busy, setBusy] = useState(false);

  const reset = () => {
    setEmail(""); setName("");
    setPortals({ admin: false, pm: false, shop: false, hr: false });
    setPassword("");
  };

  const generatePassword = () => setPassword(genTempPassword());

  const submit = async () => {
    const grantedPortals = Object.entries(portals).filter(([, v]) => v).map(([k]) => k);
    if (!email.trim() || !email.includes("@")) {
      toast.error("Valid email required"); return;
    }
    if (grantedPortals.length === 0) {
      toast.error("Grant at least one portal"); return;
    }
    if (!password || password.length < 8) {
      toast.error("Password must be at least 8 characters"); return;
    }
    setBusy(true);
    try {
      const r = await api.post("/admin/directory", {
        email: email.trim().toLowerCase(),
        name: name.trim(),
        portals: grantedPortals,
        password,
        must_change_password: true,
      });
      try { await navigator.clipboard.writeText(password); } catch { /* ignore */ }
      toast.success(
        <div className="space-y-1">
          <div className="font-bold">Created {r.data.user.email}</div>
          <div className="text-xs">Initial password copied to clipboard. Deliver it outside the app — they'll be forced to change it on first sign-in.</div>
        </div>,
        { duration: 20000 }
      );
      reset();
      onOpenChange(false);
      onCreated?.();
    } catch (err) {
      toast.error(err?.response?.data?.detail || "Create failed");
    } finally {
      setBusy(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent data-testid="acc-create-dialog">
        <DialogHeader>
          <DialogTitle className="font-display font-black flex items-center gap-2">
            <Users className="w-5 h-5 text-red-700" /> Add multi-portal user
          </DialogTitle>
          <DialogDescription>
            Grant a single email access to one or more portals. They'll sign in at
            <code className="mx-1 px-1 bg-slate-100 rounded text-xs">/sign-in</code>
            with this email + master password.
          </DialogDescription>
        </DialogHeader>
        <div className="space-y-3 py-2">
          <div>
            <Label className="font-mono text-[10px] uppercase tracking-[0.2em] text-slate-700 font-bold">
              Work Email
            </Label>
            <Input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="name@mascigc.com"
              className="mt-1.5 h-11"
              data-testid="acc-create-email"
            />
          </div>
          <div>
            <Label className="font-mono text-[10px] uppercase tracking-[0.2em] text-slate-700 font-bold">
              Display Name
            </Label>
            <Input
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="Optional"
              className="mt-1.5 h-11"
              data-testid="acc-create-name"
            />
          </div>
          <div>
            <Label className="font-mono text-[10px] uppercase tracking-[0.2em] text-slate-700 font-bold">
              Grant access to
            </Label>
            <div className="grid grid-cols-2 gap-2 mt-1.5">
              {PORTAL_OPTIONS.map((p) => (
                <label
                  key={p.key}
                  className="flex items-center gap-2 cursor-pointer p-2 rounded border-2 border-slate-200 hover:border-slate-400"
                >
                  <input
                    type="checkbox"
                    checked={portals[p.key]}
                    onChange={(e) => setPortals({ ...portals, [p.key]: e.target.checked })}
                    className="w-4 h-4 accent-red-700"
                    data-testid={`acc-create-portal-${p.key}`}
                  />
                  <span className={`inline-block w-2.5 h-2.5 rounded-full ${p.color}`} />
                  <span className="text-sm font-bold">{p.label}</span>
                </label>
              ))}
            </div>
          </div>
          <div>
            <Label className="font-mono text-[10px] uppercase tracking-[0.2em] text-slate-700 font-bold">
              Initial Master Password
            </Label>
            <div className="flex gap-2 mt-1.5">
              <Input
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="At least 8 chars"
                className="h-11 font-mono"
                data-testid="acc-create-password"
              />
              <Button
                type="button"
                variant="outline"
                onClick={generatePassword}
                className="h-11 whitespace-nowrap"
                data-testid="acc-create-gen-password"
              >
                Generate
              </Button>
            </div>
            <p className="text-xs text-slate-500 mt-1">
              They will be forced to change this on first sign-in.
            </p>
          </div>
        </div>
        <DialogFooter className="gap-2">
          <Button
            variant="outline"
            onClick={() => onOpenChange(false)}
            disabled={busy}
            data-testid="acc-create-cancel"
          >
            Cancel
          </Button>
          <Button
            onClick={submit}
            disabled={busy}
            className="bg-red-700 hover:bg-red-800 text-white font-bold uppercase tracking-wide"
            data-testid="acc-create-submit"
          >
            {busy ? (
              <><Loader2 className="w-4 h-4 mr-2 animate-spin" /> Creating…</>
            ) : (
              "Create user"
            )}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
