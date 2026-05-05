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
  Download,
  KeyRound,
  Copy,
  Lock,
  ShieldOff,
  ShieldCheck,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
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
 * Auto-email (Site Inspections / Safety Meetings / JHPs / Incidents /
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
  const [exporting, setExporting] = useState(false);
  const [form, setForm] = useState({ name: "", email: "", phone: "" });

  // ----- Activity rollup (last login + 7-day report count) -----
  const [activity, setActivity] = useState({}); // { pm_id: {last_login_at, last_login_ip, reports_7d, job_count} }

  // Relative-time formatter ("3h ago", "yesterday", "5d ago")
  const fmtRel = (iso) => {
    if (!iso) return "Never";
    try {
      const t = new Date(iso).getTime();
      if (!t || Number.isNaN(t)) return "Never";
      const diffMs = Date.now() - t;
      const m = Math.floor(diffMs / 60000);
      if (m < 1) return "Just now";
      if (m < 60) return `${m}m ago`;
      const h = Math.floor(m / 60);
      if (h < 24) return `${h}h ago`;
      const d = Math.floor(h / 24);
      if (d === 1) return "Yesterday";
      if (d < 30) return `${d}d ago`;
      const mo = Math.floor(d / 30);
      return mo === 1 ? "1mo ago" : `${mo}mo ago`;
    } catch {
      return "Never";
    }
  };

  // ----- Password management -----
  const [pwTargetPm, setPwTargetPm] = useState(null);   // PM doc the dialog is acting on
  const [customPw, setCustomPw] = useState("");
  const [pwBusy, setPwBusy] = useState(false);
  const [issuedPw, setIssuedPw] = useState(null);       // {pm_name, plain, generated}
  const [disablingId, setDisablingId] = useState(null);

  const refresh = async () => {
    setLoading(true);
    try {
      const r = await api.get("/admin/project-managers");
      setPms(r.data?.items || []);
      // Pull activity rollup in parallel — non-blocking, swallow failures
      // so a transient activity error doesn't break the roster.
      api
        .get("/admin/project-managers/activity")
        .then((act) => {
          const byId = {};
          for (const p of act.data?.items || []) byId[p.id] = p;
          setActivity(byId);
        })
        .catch(() => {});
    } catch (e) {
      toast.error(e?.response?.data?.detail || "Failed to load PMs");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    refresh();
  }, []);

  const onExport = async () => {
    setExporting(true);
    try {
      const r = await api.get("/admin/project-managers/export", { responseType: "blob" });
      const cd = r.headers["content-disposition"] || r.headers["Content-Disposition"] || "";
      const m = /filename="?([^";]+)"?/i.exec(cd);
      const fname = m ? m[1] : "MASCI_pms.xlsx";
      const url = window.URL.createObjectURL(new Blob([r.data]));
      const a = document.createElement("a");
      a.href = url;
      a.download = fname;
      document.body.appendChild(a);
      a.click();
      a.remove();
      window.URL.revokeObjectURL(url);
      toast.success(`Downloaded ${fname}`);
    } catch (err) {
      toast.error(err?.response?.data?.detail || "Export failed");
    } finally {
      setExporting(false);
    }
  };

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

  // ---------- Password issue / reset ----------
  const openPwDialog = (pm) => {
    setPwTargetPm(pm);
    setCustomPw("");
  };

  const submitSetPassword = async (mode /* "generate" | "custom" */) => {
    if (!pwTargetPm) return;
    if (mode === "custom" && customPw.length < 6) {
      toast.error("Password must be at least 6 characters");
      return;
    }
    setPwBusy(true);
    try {
      const body = mode === "custom" ? { password: customPw } : {};
      const r = await api.post(
        `/admin/project-managers/${pwTargetPm.id}/set-password`,
        body
      );
      setPwTargetPm(null);
      setCustomPw("");
      // Stash the issued password so we can show it ONCE in a copy dialog.
      setIssuedPw({
        pm_name: r.data?.pm?.name || pwTargetPm.name,
        pm_email: r.data?.pm?.email || pwTargetPm.email,
        plain: r.data?.issued_password,
        generated: !!r.data?.generated,
      });
      await refresh();
    } catch (err) {
      toast.error(err?.response?.data?.detail || "Password set failed");
    } finally {
      setPwBusy(false);
    }
  };

  const copyIssued = async () => {
    if (!issuedPw?.plain) return;
    try {
      await navigator.clipboard.writeText(issuedPw.plain);
      toast.success("Copied — paste it into your secure channel");
    } catch {
      toast.error("Copy failed — select and copy manually");
    }
  };

  const toggleDisabled = async (pm) => {
    setDisablingId(pm.id);
    try {
      const r = await api.post(`/admin/project-managers/${pm.id}/disable`, {
        disabled: !pm.disabled,
      });
      toast.success(
        r.data?.pm?.disabled ? `Locked ${pm.name}` : `Unlocked ${pm.name}`
      );
      await refresh();
    } catch (err) {
      toast.error(err?.response?.data?.detail || "Toggle failed");
    } finally {
      setDisablingId(null);
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
              <th className="px-3 py-2 text-center">Login</th>
              <th className="px-3 py-2">Activity</th>
              <th className="px-3 py-2 text-center">Active</th>
              <th className="px-3 py-2 w-44 text-right">Actions</th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr>
                <td colSpan={7} className="px-3 py-6 text-center text-slate-500">
                  <Loader2 className="w-5 h-5 animate-spin inline-block" /> Loading…
                </td>
              </tr>
            ) : pms.length === 0 ? (
              <tr>
                <td colSpan={7} className="px-3 py-6 text-center text-slate-500">
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
                    <td className="px-3 py-2 text-center text-xs">
                      {p.has_password ? (
                        p.must_change_password ? (
                          <span
                            className="inline-flex items-center gap-1 px-1.5 py-0.5 rounded bg-amber-100 text-amber-800 font-mono text-[10px] uppercase tracking-wide"
                            title="Temp password issued — PM must rotate on next login"
                          >
                            <KeyRound className="w-3 h-3" /> Temp
                          </span>
                        ) : (
                          <span
                            className="inline-flex items-center gap-1 px-1.5 py-0.5 rounded bg-emerald-100 text-emerald-800 font-mono text-[10px] uppercase tracking-wide"
                            title="PM has set their own password"
                          >
                            <ShieldCheck className="w-3 h-3" /> Set
                          </span>
                        )
                      ) : (
                        <span
                          className="inline-flex items-center gap-1 px-1.5 py-0.5 rounded bg-slate-200 text-slate-600 font-mono text-[10px] uppercase tracking-wide"
                          title="No password issued yet"
                        >
                          <XCircle className="w-3 h-3" /> None
                        </span>
                      )}
                      {p.disabled && (
                        <div
                          className="inline-flex items-center gap-1 px-1.5 py-0.5 rounded bg-red-100 text-red-700 font-mono text-[10px] uppercase tracking-wide ml-1"
                          title="Account locked"
                        >
                          <Lock className="w-3 h-3" /> Locked
                        </div>
                      )}
                    </td>
                    <td className="px-3 py-2 text-xs text-slate-600 leading-tight">
                      {(() => {
                        const a = activity[p.id] || {};
                        const last = a.last_login_at;
                        const ip = a.last_login_ip;
                        const rep = a.reports_7d ?? 0;
                        const jobs = a.job_count ?? 0;
                        return (
                          <div data-testid={`pm-activity-${p.id}`}>
                            <div
                              className="font-mono text-[10px] uppercase tracking-wide text-slate-700 font-bold"
                              title={last ? `Last login: ${last}${ip ? ` from ${ip}` : ""}` : "Never logged in via per-PM auth"}
                            >
                              {fmtRel(last)}
                              {ip && (
                                <span className="ml-1 text-slate-400 normal-case font-normal">
                                  · {ip}
                                </span>
                              )}
                            </div>
                            <div className="text-[10px] text-slate-500 mt-0.5">
                              <span className={rep > 0 ? "text-emerald-700 font-bold" : ""}>
                                {rep} reports / 7d
                              </span>
                              <span className="text-slate-400"> · {jobs} jobs</span>
                            </div>
                          </div>
                        );
                      })()}
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
                              onClick={() => openPwDialog(p)}
                              className="inline-flex items-center justify-center w-7 h-7 rounded text-amber-700 hover:bg-amber-50"
                              title={p.has_password ? "Reset password" : "Issue password"}
                              data-testid={`pm-set-password-${p.id}`}
                            >
                              <KeyRound className="w-4 h-4" />
                            </button>
                            <button
                              type="button"
                              onClick={() => toggleDisabled(p)}
                              disabled={disablingId === p.id}
                              className={`inline-flex items-center justify-center w-7 h-7 rounded ${p.disabled ? "text-red-700 hover:bg-red-50" : "text-slate-500 hover:bg-slate-100"}`}
                              title={p.disabled ? "Unlock login" : "Lock login"}
                              data-testid={`pm-toggle-disabled-${p.id}`}
                            >
                              {disablingId === p.id ? (
                                <Loader2 className="w-3.5 h-3.5 animate-spin" />
                              ) : p.disabled ? (
                                <Lock className="w-4 h-4" />
                              ) : (
                                <ShieldOff className="w-4 h-4" />
                              )}
                            </button>
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
      {/* Set / Reset password dialog */}
      <Dialog
        open={!!pwTargetPm}
        onOpenChange={(o) => !o && setPwTargetPm(null)}
      >
        <DialogContent data-testid="pm-set-password-dialog">
          <DialogHeader>
            <DialogTitle className="font-display font-black flex items-center gap-2 text-amber-700">
              <KeyRound className="w-5 h-5" />
              {pwTargetPm?.has_password
                ? `Reset password for ${pwTargetPm?.name}`
                : `Issue password for ${pwTargetPm?.name}`}
            </DialogTitle>
            <DialogDescription className="leading-relaxed">
              You can either let the system generate a secure 10-character
              temporary password (recommended) or set a custom one. Either
              way, the PM will be forced to choose their own password on
              their next login. The new password is shown ONCE — copy it
              before closing the dialog.
            </DialogDescription>
          </DialogHeader>

          <div className="space-y-3 pt-1">
            <div className="text-xs text-slate-600 bg-slate-50 border border-slate-200 rounded p-3">
              <div className="font-mono text-[10px] uppercase tracking-[0.2em] text-slate-700 font-bold mb-1">
                Account
              </div>
              <div>
                <span className="font-bold">{pwTargetPm?.name}</span>{" "}
                <span className="font-mono text-slate-500">
                  &lt;{pwTargetPm?.email}&gt;
                </span>
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
                data-testid="pm-set-password-custom-input"
              />
            </div>
          </div>

          <DialogFooter className="gap-2 pt-2">
            <Button
              variant="outline"
              onClick={() => setPwTargetPm(null)}
              disabled={pwBusy}
              data-testid="pm-set-password-cancel"
            >
              Cancel
            </Button>
            {customPw.length === 0 ? (
              <Button
                onClick={() => submitSetPassword("generate")}
                disabled={pwBusy}
                className="bg-amber-600 hover:bg-amber-700 text-white font-bold uppercase tracking-wide"
                data-testid="pm-set-password-generate"
              >
                {pwBusy ? (
                  <>
                    <Loader2 className="w-4 h-4 mr-2 animate-spin" /> Generating…
                  </>
                ) : (
                  <>Generate &amp; Issue</>
                )}
              </Button>
            ) : (
              <Button
                onClick={() => submitSetPassword("custom")}
                disabled={pwBusy || customPw.length < 6}
                className="bg-amber-600 hover:bg-amber-700 text-white font-bold uppercase tracking-wide"
                data-testid="pm-set-password-custom"
              >
                {pwBusy ? (
                  <>
                    <Loader2 className="w-4 h-4 mr-2 animate-spin" /> Setting…
                  </>
                ) : (
                  <>Set custom password</>
                )}
              </Button>
            )}
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Issued password — shown ONCE */}
      <Dialog
        open={!!issuedPw}
        onOpenChange={(o) => !o && setIssuedPw(null)}
      >
        <DialogContent data-testid="pm-issued-password-dialog">
          <DialogHeader>
            <DialogTitle className="font-display font-black flex items-center gap-2 text-emerald-700">
              <CheckCircle2 className="w-5 h-5" />
              {issuedPw?.generated ? "Temporary password issued" : "Password set"}
            </DialogTitle>
            <DialogDescription className="leading-relaxed">
              Send this password to{" "}
              <strong>
                {issuedPw?.pm_name} ({issuedPw?.pm_email})
              </strong>{" "}
              through a secure channel (in person, work phone, encrypted
              chat). They'll be forced to choose their own password on
              first login. <strong>You will NOT see this password again
              after closing this dialog.</strong>
            </DialogDescription>
          </DialogHeader>

          <div className="bg-slate-900 text-emerald-300 border-2 border-emerald-500 rounded p-4 font-mono text-2xl text-center tracking-widest break-all select-all"
            data-testid="pm-issued-password-value"
          >
            {issuedPw?.plain}
          </div>

          <DialogFooter className="gap-2">
            <Button
              variant="outline"
              onClick={copyIssued}
              data-testid="pm-issued-password-copy"
            >
              <Copy className="w-4 h-4 mr-1" /> Copy
            </Button>
            <Button
              onClick={() => setIssuedPw(null)}
              className="bg-slate-900 hover:bg-slate-800 text-white font-bold uppercase tracking-wide"
              data-testid="pm-issued-password-close"
            >
              I've copied it — close
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </section>
  );
}
