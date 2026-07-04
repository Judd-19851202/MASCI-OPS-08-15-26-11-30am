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
  Power, AlertOctagon, Copy, CheckCircle2, Mail, MailCheck,
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
import { IamStandardCells } from "@/components/iam/IamStandardCells";
import { toast } from "sonner";

// ─── Track 15.88 · Credential / usability badge contract ──────────
//
// Every row of the Access Control Center renders a small calm pair
// of badges that tell the truth about whether the user can actually
// sign in right now. The strings come from the backend canonical
// helper `lib/directory_access_state.py` — keep these maps in sync
// with that file. Drift would silently lie to the admin.

const CREDENTIAL_BADGE = {
  issued: {
    label: "Credentials Issued",
    cls: "bg-emerald-50 border-emerald-200 text-emerald-800",
    title: "Master password is set on this account.",
  },
  never_issued: {
    label: "Never Issued",
    cls: "bg-amber-50 border-amber-300 text-amber-900",
    title: "No master password has been issued — user cannot sign in until you issue credentials.",
  },
  change_required: {
    label: "Password Change Required",
    cls: "bg-amber-50 border-amber-300 text-amber-900",
    title: "User must rotate their password at /sign-in before portal tokens are issued.",
  },
  blocked: {
    label: "Credentials Blocked",
    cls: "bg-slate-100 border-slate-300 text-slate-700",
    title: "Account is disabled; credentials are inaccessible.",
  },
};

const BLOCKED_REASON_COPY = {
  disabled: "Disabled · cannot sign in",
  never_issued: "Credentials not issued",
  change_required: "Password change required",
  no_portal_access: "No portal access granted",
};

function UsabilityBadges({ user }) {
  // Backend (Track 15.88) ships `credential_state`, `usable_now`,
  // `blocked_reason`. We defensively fall back when an older response
  // payload is in transit (e.g. cached frontend ↔ pre-15.88 backend).
  const credKey = user.credential_state || (user.must_change_password
    ? "change_required"
    : (user.disabled ? "blocked" : "issued"));
  const cred = CREDENTIAL_BADGE[credKey] || CREDENTIAL_BADGE.issued;
  const usable = user.usable_now ?? (!user.disabled && !user.must_change_password && (user.portals || []).length > 0);
  const blockedKey = user.blocked_reason || null;
  return (
    <div
      className="mt-1.5 flex flex-wrap items-center gap-1.5"
      data-testid={`acc-row-state-${user.email}`}
    >
      <span
        className={`inline-flex items-center rounded-full border px-2 py-0.5 text-[10px] font-mono uppercase tracking-wider ${cred.cls}`}
        title={cred.title}
        data-testid={`acc-row-credstate-${user.email}`}
        data-credstate={credKey}
      >
        {cred.label}
      </span>
      {usable ? (
        <span
          className="inline-flex items-center rounded-full border px-2 py-0.5 text-[10px] font-mono uppercase tracking-wider bg-emerald-700 border-emerald-700 text-white"
          title="User can sign in to their granted portals right now."
          data-testid={`acc-row-usable-${user.email}`}
          data-usable="1"
        >
          Usable Now
        </span>
      ) : (
        <span
          className="inline-flex items-center rounded-full border px-2 py-0.5 text-[10px] font-mono uppercase tracking-wider bg-slate-900 border-slate-900 text-amber-200"
          title="User cannot sign in — see reason."
          data-testid={`acc-row-blocked-${user.email}`}
          data-usable="0"
          data-blockedreason={blockedKey || "unknown"}
        >
          {BLOCKED_REASON_COPY[blockedKey] || "Blocked"}
        </span>
      )}
    </div>
  );
}

// iter332 · Phase A · expanded portal grid to include safety + dispatch.
// These are already in backend ALLOWED_PORTALS, so this is the safe
// bounded UI fix (no model changes, no auth changes). Field Leadership
// is intentionally NOT included yet — that's Phase B, scheduled for a
// follow-up iter once FL multi-login + identity-mirror plumbing lands.
const PORTAL_OPTIONS = [
  { key: "admin",    label: "Admin",    color: "bg-red-700" },
  { key: "pm",       label: "PM",       color: "bg-red-600" },
  { key: "shop",     label: "Shop",     color: "bg-orange-600" },
  { key: "hr",       label: "HR",       color: "bg-purple-700" },
  { key: "safety",   label: "Safety",   color: "bg-cyan-700" },
  { key: "dispatch", label: "Dispatch", color: "bg-amber-700" },
  // iter345 · FL Phase B · Hybrid · 7th column. Granting this lets
  // any directory user sign in at /leadership/login with their
  // master password and enter the Field Leadership Hub without
  // creating a duplicate field_leadership_users row.
  { key: "field_leadership", label: "Field Leadership", color: "bg-red-800" },
];

// Empty portals state matching the expanded option set.
const EMPTY_PORTALS = { admin: false, pm: false, shop: false, hr: false, safety: false, dispatch: false };

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
    // Iter90: Match the PM/Shop/HR admin flow — admin picks
    // "email it to the user" or "show on screen so I can deliver it".
    // The default is email so the experience matches what admins are
    // already used to in /admin/people for the per-portal user lists.
    const choice = window.prompt(
      `Reset master password for ${user.email}?\n\n` +
      `Type "EMAIL" to email a temporary password to ${user.email}.\n` +
      `Type "SHOW" to generate one and have it shown to you here so you can deliver it manually.\n` +
      `Leave blank or cancel to abort.`,
      "EMAIL"
    );
    const decision = (choice || "").trim().toUpperCase();
    if (!decision || (decision !== "EMAIL" && decision !== "SHOW")) {
      if (choice !== null) toast.info("Cancelled — type EMAIL or SHOW exactly.");
      return;
    }
    try {
      const r = await api.post(`/admin/directory/${user.id}/reset-password`, {
        // Backend will generate one for either delivery mode when blank.
        new_password: "",
        must_change: true,
        delivery: decision === "EMAIL" ? "email" : "show",
      });
      if (r.data?.email_sent) {
        toast.success(
          <div className="space-y-1">
            <div className="font-bold flex items-center gap-1.5">
              <MailCheck className="w-4 h-4" /> Email sent to {user.email}
            </div>
            <div className="text-xs">
              They&apos;ll be forced to choose a new password on first sign-in.
            </div>
          </div>,
          { duration: 12000 }
        );
      } else if (r.data?.temp_password) {
        // Email channel unavailable OR admin picked SHOW — surface pw.
        try { await navigator.clipboard.writeText(r.data.temp_password); } catch { /* ignore */ }
        toast.success(
          <div className="space-y-1">
            <div className="font-bold">Password reset — give to user:</div>
            <code className="text-base bg-slate-100 px-2 py-0.5 rounded">{r.data.temp_password}</code>
            <div className="text-[11px] text-slate-500">Copied to clipboard. Deliver it outside the app.</div>
          </div>,
          { duration: 45000 }
        );
      }
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
              any combination of Admin / PM / Shop / HR / Safety / Dispatch. Single-portal
              employees don&apos;t need a directory entry; they use the existing
              portal-specific sign-in pages.
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
          No multi-portal users yet. Click &quot;Add user&quot; to grant someone access.
        </div>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full min-w-[1200px] text-sm">
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
                        <IamStandardCells user={u} portal="access-control" compact />
                        {/* Track 15.88 · credential + usability truth */}
                        <UsabilityBadges user={u} />
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
  const [portals, setPortals] = useState({ ...EMPTY_PORTALS });
  const [delivery, setDelivery] = useState("email"); // 'email' | 'show'
  const [password, setPassword] = useState("");
  const [busy, setBusy] = useState(false);

  const reset = () => {
    setEmail(""); setName("");
    setPortals({ ...EMPTY_PORTALS });
    setDelivery("email");
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
    // Email delivery: backend will generate if password is blank.
    // Show delivery: admin must type one (so they can deliver it).
    if (delivery === "show" && (!password || password.length < 8)) {
      toast.error("Type or generate a password (min 8 chars) for show-on-screen delivery");
      return;
    }
    setBusy(true);
    try {
      const r = await api.post("/admin/directory", {
        email: email.trim().toLowerCase(),
        name: name.trim(),
        portals: grantedPortals,
        password: delivery === "email" ? (password || "") : password,
        must_change_password: true,
        delivery,
      });
      const view = r.data?.user;
      if (r.data?.email_sent) {
        toast.success(
          <div className="space-y-1">
            <div className="font-bold flex items-center gap-1.5">
              <MailCheck className="w-4 h-4" /> Welcome email sent to {view.email}
            </div>
            <div className="text-xs">
              They&apos;ll be asked to choose their own password on first sign-in.
            </div>
          </div>,
          { duration: 12000 }
        );
      } else if (r.data?.temp_password) {
        try { await navigator.clipboard.writeText(r.data.temp_password); } catch { /* ignore */ }
        toast.success(
          <div className="space-y-1">
            <div className="font-bold">Created {view.email}</div>
            <div className="text-xs">Initial password copied to clipboard — deliver it outside the app.</div>
            <code className="text-sm bg-slate-100 px-2 py-0.5 rounded inline-block">{r.data.temp_password}</code>
          </div>,
          { duration: 45000 }
        );
      } else {
        toast.success(`Created ${view.email}`);
      }
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
            Grant a single email access to one or more portals. They&apos;ll sign in at
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
              placeholder="name@yourcompany.com"
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
          {/* Delivery toggle — matches PM/Shop/HR admin UX */}
          <div>
            <Label className="font-mono text-[10px] uppercase tracking-[0.2em] text-slate-700 font-bold">
              How should they receive their password?
            </Label>
            <div className="grid grid-cols-2 gap-2 mt-1.5">
              <label
                className={`flex items-start gap-2 cursor-pointer p-2.5 rounded border-2 ${
                  delivery === "email" ? "border-red-700 bg-red-50" : "border-slate-200 hover:border-slate-400"
                }`}
              >
                <input
                  type="radio"
                  name="delivery"
                  value="email"
                  checked={delivery === "email"}
                  onChange={() => setDelivery("email")}
                  className="w-4 h-4 accent-red-700 mt-0.5"
                  data-testid="acc-delivery-email"
                />
                <div>
                  <div className="text-sm font-bold flex items-center gap-1"><Mail className="w-3.5 h-3.5" /> Email it (recommended)</div>
                  <div className="text-[11px] text-slate-500 leading-tight">
                    Sends a welcome email with a temp password + sign-in link.
                  </div>
                </div>
              </label>
              <label
                className={`flex items-start gap-2 cursor-pointer p-2.5 rounded border-2 ${
                  delivery === "show" ? "border-amber-600 bg-amber-50" : "border-slate-200 hover:border-slate-400"
                }`}
              >
                <input
                  type="radio"
                  name="delivery"
                  value="show"
                  checked={delivery === "show"}
                  onChange={() => setDelivery("show")}
                  className="w-4 h-4 accent-amber-600 mt-0.5"
                  data-testid="acc-delivery-show"
                />
                <div>
                  <div className="text-sm font-bold flex items-center gap-1"><Copy className="w-3.5 h-3.5" /> Show me</div>
                  <div className="text-[11px] text-slate-500 leading-tight">
                    Shown on-screen + copied to clipboard for manual delivery.
                  </div>
                </div>
              </label>
            </div>
          </div>
          {/* Password field — required only for "show", optional for "email" */}
          <div>
            <Label className="font-mono text-[10px] uppercase tracking-[0.2em] text-slate-700 font-bold">
              {delivery === "email" ? "Custom password (optional)" : "Initial password"}
            </Label>
            <div className="flex gap-2 mt-1.5">
              <Input
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder={delivery === "email" ? "Leave blank to auto-generate" : "At least 8 chars"}
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
              {delivery === "email"
                ? "If left blank, the backend generates a secure temp password and emails it. They'll be forced to change it on first sign-in."
                : "You'll see this password once after submit — copy it and deliver it outside the app."}
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
