// src/components/team/JobTeamRosterPanel.jsx
// Track 14.0-JOB-OWNERSHIP-FOUNDATION Phase 1
//
// Self-contained roster manager for a single project. Works in either
// Admin scope (full role-set, audit visible) or PM scope (limited role-
// set, no audit drawer). All writes flow through the team-roster API
// which enforces permissions server-side.

import React, { useEffect, useMemo, useState } from "react";
import {
  fetchRoleRegistry, fetchTeam, fetchTeamAudit, addTeamMember,
  patchTeamMember, removeTeamMember, fetchDirectoryUsers,
  transferTeamMember,
} from "@/lib/teamRosterApi";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import {
  Select, SelectTrigger, SelectValue, SelectContent, SelectItem,
} from "@/components/ui/select";
import { UserPlus, Users, History, AlertTriangle, X, Star, ArrowRightLeft } from "lucide-react";
import { toast } from "sonner";

const ROW_TEST = (slot) => `job-team-row-${slot}`;

export default function JobTeamRosterPanel({ projectNumber, scope = "admin" }) {
  const adminScope = scope === "admin";
  const [items, setItems] = useState([]);
  const [registry, setRegistry] = useState([]);
  const [directory, setDirectory] = useState([]);
  const [audit, setAudit] = useState([]);
  const [showAudit, setShowAudit] = useState(false);
  const [showAdd, setShowAdd] = useState(false);
  const [loading, setLoading] = useState(true);
  const [err, setErr] = useState(null);

  const [newRole, setNewRole] = useState("");
  const [newUserId, setNewUserId] = useState("");
  const [newNotes, setNewNotes] = useState("");
  const [isPrimary, setIsPrimary] = useState(false);
  const [submitting, setSubmitting] = useState(false);

  const reload = async () => {
    if (!projectNumber) return;
    setLoading(true);
    setErr(null);
    try {
      const [t, reg] = await Promise.all([
        fetchTeam(projectNumber, { adminScope, pmScope: !adminScope }),
        fetchRoleRegistry(),
      ]);
      setItems(t.items || []);
      setRegistry(reg.roles || []);
      if (adminScope) {
        const dir = await fetchDirectoryUsers().catch(() => []);
        setDirectory(dir);
        const a = await fetchTeamAudit(projectNumber).catch(() => ({ items: [] }));
        setAudit(a.items || []);
      }
    } catch (e) {
      setErr(e.message || String(e));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { reload(); /* eslint-disable-next-line */ }, [projectNumber, scope]);

  const grouped = useMemo(() => {
    const out = {};
    for (const r of registry) out[r.key] = { ...r, active: [], inactive: [] };
    for (const it of items) {
      const slot = out[it.assignment_role];
      if (!slot) continue;
      (it.active ? slot.active : slot.inactive).push(it);
    }
    return Object.values(out);
  }, [items, registry]);

  const assignableRoles = useMemo(() => {
    // Track 14.0-PM-STAFFING-UI-DISCOVERABILITY: PMs see every role in
    // the picker — admin-only roles are visible but disabled with a
    // tooltip so PMs always know the full role set + who manages it.
    return registry;
  }, [registry]);

  const handleAdd = async () => {
    if (!newRole) { toast.error("Pick a role"); return; }
    if (!newUserId) { toast.error("Pick a user"); return; }
    setSubmitting(true);
    try {
      const r = await addTeamMember(
        projectNumber,
        { user_id: newUserId, assignment_role: newRole,
          is_primary: isPrimary, notes: newNotes || undefined },
        { adminScope },
      );
      toast.success(`Added ${r.assignment.display_name || r.assignment.email || "member"} as ${r.assignment.role_label}`);
      if (r.user_link_warning) toast.warning("User/employee link missing — notifications may route by role until linked.");
      setShowAdd(false);
      setNewRole(""); setNewUserId(""); setNewNotes(""); setIsPrimary(false);
      reload();
    } catch (e) {
      toast.error(e.message || "Add failed");
    } finally {
      setSubmitting(false);
    }
  };

  const handleRemove = async (it) => {
    const reason = prompt(`Remove ${it.display_name || it.email} as ${it.role_label}? (optional reason)`);
    if (reason === null) return;
    try {
      await removeTeamMember(projectNumber, it.id, reason || undefined, { adminScope });
      toast.success("Assignment removed.");
      reload();
    } catch (e) { toast.error(e.message); }
  };

  const handleTogglePrimary = async (it) => {
    try {
      await patchTeamMember(projectNumber, it.id, { is_primary: !it.is_primary });
      toast.success(it.is_primary ? "Marked secondary." : "Marked primary.");
      reload();
    } catch (e) { toast.error(e.message); }
  };

  const handleTransfer = async (it) => {
    if (!adminScope) return; // admin-only action
    const repEmail = prompt(`Transfer ${it.display_name || it.email}'s ${it.role_label} role to another user — enter replacement EMAIL (must exist in directory):`);
    if (!repEmail) return;
    const reason = prompt("Reason for transfer (required):") || "(no reason supplied)";
    try {
      const r = await transferTeamMember(it.id, {
        replacement_email: repEmail,
        reason,
        end_status: "REPLACED",
      });
      const mig = r.migration || {};
      toast.success(
        `Transferred. ${mig.notifications_repointed || 0} notifications repointed · ${mig.tasks_repointed || 0} tasks repointed.`
      );
      reload();
    } catch (e) {
      toast.error(e.message || "Transfer failed");
    }
  };

  return (
    <Card data-testid="job-team-roster-panel">
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <CardTitle className="text-lg flex items-center gap-2">
          <Users className="h-5 w-5" />
          Project Team — {projectNumber}
          <Badge variant="outline" className="ml-2">
            {items.filter((i) => i.active).length} active
          </Badge>
        </CardTitle>
        <div className="flex gap-2">
          {adminScope && (
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setShowAudit((v) => !v)}
              data-testid="job-team-audit-toggle"
            >
              <History className="h-4 w-4 mr-1" />
              {showAudit ? "Hide history" : `History (${audit.length})`}
            </Button>
          )}
          <Button
            size="sm"
            onClick={() => setShowAdd(true)}
            data-testid="job-team-add-btn"
          >
            <UserPlus className="h-4 w-4 mr-1" /> Add member
          </Button>
        </div>
      </CardHeader>
      <CardContent>
        {loading && <p className="text-sm text-slate-500">Loading roster…</p>}
        {err && (
          <p className="text-sm text-red-700 bg-red-50 p-2 rounded mb-3">
            {err}
          </p>
        )}
        {!adminScope && !loading && (
          <p
            className="text-xs text-slate-600 bg-amber-50 border border-amber-200 rounded p-2 mb-3"
            data-testid="job-team-pm-scope-note"
          >
            <strong>PM scope:</strong> You can assign all operational roles
            (Superintendent, Foreman, Safety, QA/QC, Project Engineer, and 11
            more). <span className="text-amber-800">Project Manager</span>,{" "}
            <span className="text-amber-800">Co-PM</span>, and{" "}
            <span className="text-amber-800">Executive Oversight</span> are
            admin-only — request changes from your administrator.
          </p>
        )}
        {!loading && !err && (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-x-6 gap-y-3">
            {grouped.map((slot) => (
              <div key={slot.key} data-testid={ROW_TEST(slot.key)} className="border-b border-slate-100 pb-2">
                <div className="flex items-center justify-between mb-1">
                  <p className="text-xs uppercase tracking-wide text-slate-500 font-medium">
                    {slot.label}
                    {slot.admin_only && (
                      <Badge variant="secondary" className="ml-2 text-[10px]">admin-only</Badge>
                    )}
                  </p>
                </div>
                {slot.active.length === 0 && (
                  <p className="text-sm text-slate-400 italic">Unassigned</p>
                )}
                {slot.active.map((it) => (
                  <div
                    key={it.id}
                    className="flex items-center justify-between bg-slate-50 px-2 py-1.5 rounded mt-1"
                    data-testid={`job-team-member-${it.id}`}
                  >
                    <div>
                      <p className="text-sm font-medium">
                        {it.display_name || it.email || "(unnamed)"}
                        {it.is_primary && (
                          <Star className="inline h-3 w-3 ml-1 text-amber-500" data-testid="primary-badge" />
                        )}
                      </p>
                      <p className="text-xs text-slate-500">{it.email || "—"}</p>
                      {!it.user_id && (
                        <p className="text-xs text-amber-700 flex items-center gap-1">
                          <AlertTriangle className="h-3 w-3" />
                          User/employee link missing — notifications may route by role until linked.
                        </p>
                      )}
                    </div>
                    <div className="flex items-center gap-1">
                      {adminScope && (
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => handleTogglePrimary(it)}
                          data-testid={`job-team-toggle-primary-${it.id}`}
                          title={it.is_primary ? "Mark secondary" : "Mark primary"}
                        >
                          <Star className={`h-3 w-3 ${it.is_primary ? "text-amber-500" : "text-slate-300"}`} />
                        </Button>
                      )}
                      {adminScope && (
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => handleTransfer(it)}
                          data-testid={`job-team-transfer-${it.id}`}
                          title="Transfer / replace"
                        >
                          <ArrowRightLeft className="h-3 w-3" />
                        </Button>
                      )}
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => handleRemove(it)}
                        data-testid={`job-team-remove-${it.id}`}
                        title="Remove"
                      >
                        <X className="h-3 w-3" />
                      </Button>
                    </div>
                  </div>
                ))}
              </div>
            ))}
          </div>
        )}

        {showAdd && (
          <div className="mt-4 p-3 border rounded bg-slate-50" data-testid="job-team-add-form">
            <p className="text-sm font-medium mb-2">Add team member</p>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
              <Select value={newRole} onValueChange={setNewRole}>
                <SelectTrigger data-testid="job-team-role-select">
                  <SelectValue placeholder="Pick role" />
                </SelectTrigger>
                <SelectContent>
                  {assignableRoles.map((r) => {
                    const disabledForPm = !adminScope && r.admin_only;
                    return (
                      <SelectItem
                        key={r.key}
                        value={r.key}
                        disabled={disabledForPm}
                        data-testid={`job-team-role-option-${r.key}`}
                        title={
                          disabledForPm
                            ? "Admin only — request from your administrator"
                            : undefined
                        }
                      >
                        {r.label}
                        {r.admin_only ? " (admin-only)" : ""}
                        {disabledForPm ? " — admin only" : ""}
                      </SelectItem>
                    );
                  })}
                </SelectContent>
              </Select>
              {adminScope ? (
                <Select value={newUserId} onValueChange={setNewUserId}>
                  <SelectTrigger data-testid="job-team-user-select">
                    <SelectValue placeholder="Pick user from directory" />
                  </SelectTrigger>
                  <SelectContent>
                    {directory.map((u) => (
                      <SelectItem key={u.id} value={u.id}>
                        {u.name || u.email} · {u.email}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              ) : (
                <Input
                  placeholder="User email (must exist in directory)"
                  onChange={(e) => setNewUserId(e.target.value)}
                  value={newUserId}
                  data-testid="job-team-user-email"
                />
              )}
              <Input
                placeholder="Notes (optional)"
                value={newNotes}
                onChange={(e) => setNewNotes(e.target.value)}
                data-testid="job-team-notes"
              />
              <label className="flex items-center gap-2 text-sm">
                <input
                  type="checkbox"
                  checked={isPrimary}
                  onChange={(e) => setIsPrimary(e.target.checked)}
                  data-testid="job-team-primary-checkbox"
                />
                Mark primary
              </label>
            </div>
            <div className="flex gap-2 mt-3">
              <Button
                size="sm"
                onClick={handleAdd}
                disabled={submitting}
                data-testid="job-team-submit"
              >
                {submitting ? "Adding…" : "Add"}
              </Button>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setShowAdd(false)}
                data-testid="job-team-cancel"
              >
                Cancel
              </Button>
            </div>
          </div>
        )}

        {adminScope && showAudit && (
          <div className="mt-4 p-3 border rounded bg-slate-50" data-testid="job-team-audit-drawer">
            <p className="text-sm font-medium mb-2">Roster history</p>
            {audit.length === 0 && <p className="text-xs text-slate-500">No history yet.</p>}
            <ul className="text-xs space-y-1 max-h-72 overflow-auto">
              {audit.map((a) => (
                <li key={a.id} className="font-mono">
                  <span className="text-slate-500">{a.at?.slice(0, 19)}</span> · {a.action} ·{" "}
                  {a.assignment_role} · {a.target_email || a.target_user_id || "—"} ·{" "}
                  by {a.actor_email || a.actor_name || a.actor_role}
                  {a.notes ? ` — ${a.notes}` : ""}
                </li>
              ))}
            </ul>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
