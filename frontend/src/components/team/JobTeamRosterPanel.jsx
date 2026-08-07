// src/components/team/JobTeamRosterPanel.jsx
// Track 14.0-JOB-OWNERSHIP-FOUNDATION Phase 1
//
// Self-contained roster manager for a single project. Works in either
// Admin scope (full role-set, audit visible) or PM scope (limited role-
// set, no audit drawer). All writes flow through the team-roster API
// which enforces permissions server-side.

import React, { useCallback, useEffect, useMemo, useState } from "react";
import {
  fetchRoleRegistry, fetchTeam, fetchTeamAudit, addTeamMember,
  patchTeamMember, removeTeamMember, fetchDirectoryUsers,
  fetchPmDirectoryUsers, transferTeamMember,
} from "@/lib/teamRosterApi";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import {
  Select, SelectTrigger, SelectValue, SelectContent, SelectItem,
} from "@/components/ui/select";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter, DialogDescription } from "@/components/ui/dialog";
import { Popover, PopoverTrigger, PopoverContent } from "@/components/ui/popover";
import { Command, CommandEmpty, CommandGroup, CommandInput, CommandItem, CommandList } from "@/components/ui/command";
import { useCmdkTouchGuard } from "@/lib/useCmdkTouchGuard";
import { sanitizeOperatorReference } from "@/lib/operatorLanguage";
import { UserPlus, Users, History, AlertTriangle, X, Star, ArrowRightLeft, ShieldCheck, ShieldAlert, Clock, ShieldOff, HelpCircle, Search, ChevronsUpDown, Check } from "lucide-react";
import { toast } from "sonner";
import { RemoveReasonDialog } from "@/components/team/RemoveReasonDialog";
import { AssignmentHistoryDrawer } from "@/components/team/AssignmentHistoryDrawer";

// TRACK 15.27A · P1-2 — Common field roles bubble to the top so a
// Superintendent / Foreman / Field Engineer assignment is a 1-click
// pick instead of a 17-item scroll. Admin-only governance roles fall
// to the bottom. No new roles. No new logic — purely a sort order
// applied to the same registry the backend already returns.
const ROLE_ORDER_PRIORITY = {
  superintendent: 1,
  assistant_superintendent: 2,
  foreman: 3,
  project_engineer: 4,        // field-engineer label per directive
  project_administrator: 5,
  project_coordinator: 6,
  safety_rep: 7,
  qaqc_rep: 8,
  equipment_manager: 9,
  shop_rep: 10,
  hr_rep: 11,
  dispatch_rep: 12,
  survey_rep: 13,
  accounting_rep: 14,
  pm: 90,                     // admin-only roles last
  co_pm: 91,
  executive_oversight: 92,
};
function sortRoles(roles) {
  return [...roles].sort((a, b) => {
    const pa = ROLE_ORDER_PRIORITY[a.key] ?? 50;
    const pb = ROLE_ORDER_PRIORITY[b.key] ?? 50;
    if (pa !== pb) return pa - pb;
    return (a.label || "").localeCompare(b.label || "");
  });
}

const ROW_TEST = (slot) => `job-team-row-${slot}`;

// TRACK 15.10 · canonical display-name fallback hierarchy.
// 1) full_name → 2) display_name → 3) name → 4) first+last →
// 5) email → 6) Employee #<id> → 7) "Unknown person — Admin review required"
// Never returns the unnamed-placeholder string.
function displayNameOf(it) {
  if (!it || typeof it !== "object") return "Unknown person — Admin review required";
  const tryStr = (s) => (typeof s === "string" ? s.trim() : "");
  const full = tryStr(it.full_name);
  if (full) return sanitizeOperatorReference(full, full);
  const disp = tryStr(it.display_name);
  if (disp) return sanitizeOperatorReference(disp, disp);
  const nm = tryStr(it.name);
  if (nm) return sanitizeOperatorReference(nm, nm);
  const first = tryStr(it.first_name);
  const last = tryStr(it.last_name);
  if (first || last) return sanitizeOperatorReference([first, last].filter(Boolean).join(" "), "Team member");
  const em = tryStr(it.email);
  if (em) return em;
  const emp = tryStr(it.employee_id);
  if (emp) return `Employee #${emp}`;
  return "Unknown person — Admin review required";
}

// TRACK 15.10 · login/access status badge derived from existing
// user_directory fields. NO new auth system, NO silent account
// creation — just a visibility surface so PMs can tell whether an
// assigned person can actually log in.
const LOGIN_STATUS_META = {
  active:          { label: "Active login",    cls: "bg-emerald-50 text-emerald-800 border-emerald-200", Icon: ShieldCheck },
  invite_pending:  { label: "Invite pending",  cls: "bg-amber-50 text-amber-800 border-amber-200",       Icon: Clock },
  no_login:        { label: "No login",        cls: "bg-rose-50 text-rose-800 border-rose-200",          Icon: ShieldAlert },
  disabled:        { label: "Disabled",        cls: "bg-slate-200 text-slate-700 border-slate-300",      Icon: ShieldOff },
  unknown:         { label: "Unknown",         cls: "bg-slate-50 text-slate-600 border-slate-200",       Icon: HelpCircle },
};

function LoginStatusBadge({ status }) {
  const meta = LOGIN_STATUS_META[status] || LOGIN_STATUS_META.unknown;
  const Icon = meta.Icon;
  return (
    <span
      className={`inline-flex items-center gap-1 px-1.5 py-0.5 rounded border text-[10px] font-mono uppercase tracking-wide ${meta.cls}`}
      data-testid={`job-team-login-status-${status}`}
      title={
        status === "active" ? "User has set a password and can sign in to the platform." :
        status === "invite_pending" ? "User account exists but they haven't set a password yet — Admin can issue/reset a temporary password." :
        status === "no_login" ? "No platform login on file — Admin must issue access." :
        status === "disabled" ? "Account is disabled. Admin must re-enable before this person can sign in." :
        "Login status could not be determined."
      }
    >
      <Icon className="w-3 h-3" /> {meta.label}
    </span>
  );
}

export default function JobTeamRosterPanel({ projectNumber, scope = "admin" }) {
  const adminScope = scope === "admin";
  const safeProjectNumber = sanitizeOperatorReference(projectNumber, "Project support");
  const [items, setItems] = useState([]);
  const [registry, setRegistry] = useState([]);
  const [directory, setDirectory] = useState([]);
  const [audit, setAudit] = useState([]);
  const [showAdd, setShowAdd] = useState(false);
  const [loading, setLoading] = useState(true);
  const [err, setErr] = useState(null);

  const [newRole, setNewRole] = useState("");
  const [newUserId, setNewUserId] = useState("");
  const [newNotes, setNewNotes] = useState("");
  const [isPrimary, setIsPrimary] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  // TRACK 15.27A · P1-1 — searchable employee picker state
  const [userPickerOpen, setUserPickerOpen] = useState(false);
  // TRACK 24.9 Phase B · shared cmdk touch-vs-scroll guard.
  const {
    commitHandlersFor: userPickerHandlers,
    guardedOnSelect: guardedUserPickerSelect,
  } = useCmdkTouchGuard(userPickerOpen);
  // TRACK 15.27A · P0-2 — actionable 403 message when a PM opens a
  // project they are not assigned to as PM/Co-PM.
  const [accessErr, setAccessErr] = useState(null);
  // TRACK 15.39A · structured remove + history drawer + inline role
  // change. `removeTarget` holds the assignment row to remove; the
  // dialog reads it for the title + role label. `rowBusy` disables
  // the inline role Select while a PATCH is in flight (per-row).
  // `historyOpen` controls the read-only audit drawer.
  const [removeTarget, setRemoveTarget] = useState(null);
  const [rowBusy, setRowBusy] = useState({});
  const [historyOpen, setHistoryOpen] = useState(false);

  const reload = useCallback(async () => {
    if (!projectNumber) return;
    setLoading(true);
    setErr(null);
    setAccessErr(null);
    try {
      // TRACK 15.27A · P0-2 — fetch team and registry independently so
      // a 403 on the team-fetch (PM-not-PM-of-record) does not also
      // wipe the role registry + directory, which the add form needs.
      const reg = await fetchRoleRegistry();
      setRegistry(reg.roles || []);
      try {
        const t = await fetchTeam(projectNumber, { adminScope, pmScope: !adminScope });
        setItems(t.items || []);
      } catch (fetchErr) {
        const msg = String(fetchErr?.message || fetchErr || "");
        if (msg.includes(": 403") || /authoriz/i.test(msg)) {
          setAccessErr(
            "You are not assigned as PM or Co-PM on this project. Ask an Admin (or the project's PM) to add you to the team before you can manage its roster."
          );
          setItems([]);
        } else {
          throw fetchErr;
        }
      }
      if (adminScope) {
        const dir = await fetchDirectoryUsers().catch(() => []);
        setDirectory(dir);
        const a = await fetchTeamAudit(projectNumber).catch(() => ({ items: [] }));
        setAudit(a.items || []);
      } else {
        // TRACK 15.10 · PM scope now also loads a directory picker
        // (read-only via /api/pm/directory/users — same user_directory
        // collection the existing portal rosters live in).
        const dir = await fetchPmDirectoryUsers().catch(() => []);
        setDirectory(dir);
      }
    } catch (e) {
      setErr(e.message || String(e));
    } finally {
      setLoading(false);
    }
  }, [adminScope, projectNumber]);

  useEffect(() => { reload(); }, [reload]);

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
    // TRACK 15.27A · P1-2 — common field roles bubble to the top.
    return sortRoles(registry);
  }, [registry]);

  // TRACK 15.39A · O(1) label lookup for inline role-change toasts and
  // the dropdown trigger value text.
  const roleByKey = useMemo(() => {
    const m = {};
    for (const r of registry) m[r.key] = r;
    return m;
  }, [registry]);

  // TRACK 15.27A · P0-2 — clean cancel/close helper so all paths reset
  // form state uniformly.
  const closeAdd = () => {
    setShowAdd(false);
    setNewRole(""); setNewUserId(""); setNewNotes(""); setIsPrimary(false);
    setUserPickerOpen(false);
  };

  const pickedUser = useMemo(
    () => directory.find((u) => u.id === newUserId) || null,
    [directory, newUserId],
  );

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
      closeAdd();
      reload();
    } catch (e) {
      toast.error(e.message || "Add failed");
    } finally {
      setSubmitting(false);
    }
  };

  const handleRemove = (it) => {
    // TRACK 15.39A · structured reason dialog replaces the legacy
    // window.prompt(...). The dialog calls handleRemoveConfirm below
    // with (reason_category, reason_text).
    setRemoveTarget(it);
  };

  const handleRemoveConfirm = async (reason_category, reason_text) => {
    if (!removeTarget) return;
    await removeTeamMember(
      projectNumber,
      removeTarget.id,
      { reason_category, reason_text },
      { adminScope },
    );
    toast.success("Assignment removed.");
    setRemoveTarget(null);
    reload();
  };

  // TRACK 15.39A · inline role change (admin scope only). PATCH the
  // assignment to a new role; backend single-source-of-truths the
  // audit row (one `role_change` event, no synthetic add+remove).
  const setBusy = (id, v) => setRowBusy((b) => ({ ...b, [id]: v }));
  const handleRoleChange = async (it, newRoleKey) => {
    if (!newRoleKey || newRoleKey === it.assignment_role) return;
    setBusy(it.id, true);
    try {
      await patchTeamMember(projectNumber, it.id, { assignment_role: newRoleKey });
      const label = roleByKey[newRoleKey]?.label || newRoleKey;
      toast.success(`Role changed to ${label}`);
      reload();
    } catch (e) {
      if (e?.status === 409) {
        toast.error(e.detail || "User already holds that role on this project.");
      } else {
        toast.error(e?.detail || e?.message || "Role change failed");
      }
    } finally {
      setBusy(it.id, false);
    }
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
          Project Team — {safeProjectNumber}
          <Badge variant="outline" className="ml-2">
            {items.filter((i) => i.active).length} active
          </Badge>
        </CardTitle>
        <div className="flex gap-2">
          {adminScope && (
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setHistoryOpen(true)}
              data-testid="open-history-drawer"
            >
              <History className="h-4 w-4 mr-1" />
              {`History (${audit.length})`}
            </Button>
          )}
          <Button
            size="sm"
            onClick={() => setShowAdd(true)}
            disabled={!!accessErr || loading}
            data-testid="job-team-add-btn"
          >
            <UserPlus className="h-4 w-4 mr-1" /> Add member
          </Button>
        </div>
      </CardHeader>
      <CardContent>
        {loading && <p className="text-sm text-slate-500">Loading roster…</p>}
        {accessErr && (
          <div
            data-testid="job-team-access-error"
            className="text-sm text-amber-900 bg-amber-50 border border-amber-200 p-3 rounded mb-3 flex items-start gap-2"
          >
            <ShieldAlert className="h-4 w-4 mt-0.5 flex-shrink-0 text-amber-700" />
            <p>{accessErr}</p>
          </div>
        )}
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
                {slot.active.map((it) => {
                  const isSynthetic = !!it.synthetic;
                  return (
                  <div
                    key={it.id}
                    className="flex items-center justify-between bg-slate-50 px-2 py-1.5 rounded mt-1"
                    data-testid={`job-team-member-${it.id}`}
                  >
                    <div className="min-w-0">
                      <p className="text-sm font-medium flex items-center gap-1.5 flex-wrap">
                        <span data-testid={`job-team-member-name-${it.id}`}>
                          {displayNameOf(it)}
                        </span>
                        {it.is_primary && (
                          <Star className="inline h-3 w-3 text-amber-500" data-testid="primary-badge" />
                        )}
                        {/* TRACK 15.10 · login/access status surfaced from
                            user_directory. No silent account creation. */}
                        <LoginStatusBadge status={it.login_status || "unknown"} />
                        {isSynthetic && (
                          <Badge
                            variant="secondary"
                            className="text-[10px] bg-blue-50 text-blue-800 border-blue-200"
                            data-testid={`job-team-synthetic-${it.id}`}
                            title="Known from jobs_master but not yet materialised into project_team_assignments. Admin can run a backfill to bind."
                          >
                            from project record
                          </Badge>
                        )}
                      </p>
                      <p className="text-xs text-slate-500">{it.email || "—"}</p>
                      {!it.user_id && !isSynthetic && (
                        <p className="text-xs text-amber-700 flex items-center gap-1">
                          <AlertTriangle className="h-3 w-3" />
                          User/employee link missing — notifications may route by role until linked.
                        </p>
                      )}
                    </div>
                    <div className="flex items-center gap-1">
                      {adminScope && !isSynthetic && (
                        <Select
                          value={it.assignment_role}
                          onValueChange={(v) => handleRoleChange(it, v)}
                          disabled={!!rowBusy[it.id]}
                        >
                          <SelectTrigger
                            className="h-7 w-44 text-xs"
                            data-testid={`row-role-${it.id}`}
                            title="Change role"
                          >
                            <SelectValue />
                          </SelectTrigger>
                          <SelectContent>
                            {assignableRoles.map((r) => (
                              <SelectItem
                                key={r.key}
                                value={r.key}
                                data-testid={`row-role-${it.id}-opt-${r.key}`}
                              >
                                {r.label}
                                {r.admin_only ? " (admin-only)" : ""}
                              </SelectItem>
                            ))}
                          </SelectContent>
                        </Select>
                      )}
                      {adminScope && !isSynthetic && (
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
                      {adminScope && !isSynthetic && (
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
                      {!isSynthetic && (
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => handleRemove(it)}
                          data-testid={`row-remove-${it.id}`}
                          title="Remove"
                        >
                          <X className="h-3 w-3" />
                        </Button>
                      )}
                    </div>
                  </div>
                  );
                })}
              </div>
            ))}
          </div>
        )}

        {/* TRACK 15.27A · P0-1 — Add-member is now a Dialog modal. The
            previous inline form rendered below the 17-role grid which
            users perceived as a dead button. Dialog always centers on
            screen, so the click → form-visible loop is unambiguous on
            desktop, iPad portrait, and iPad landscape. */}
        <Dialog
          open={showAdd}
          onOpenChange={(o) => (o ? setShowAdd(true) : closeAdd())}
        >
          <DialogContent
            className="max-w-lg"
            data-testid="job-team-add-form"
          >
            <DialogHeader>
              <DialogTitle>Add team member</DialogTitle>
              <DialogDescription>
                Pick a role and an employee — both are required.
              </DialogDescription>
            </DialogHeader>
            <div className="space-y-3 py-2">
              <div>
                <p className="text-xs font-medium uppercase tracking-wide text-slate-500 mb-1">Role</p>
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
              </div>

              {/* TRACK 15.27A · P1-1 — search-as-you-type employee picker.
                  Replaces the long scrollable Select with a Command (cmdk)
                  inside a Popover so typing "Joe" narrows results live.
                  No new endpoints; reads the same `directory` array
                  already loaded into state. */}
              <div>
                <p className="text-xs font-medium uppercase tracking-wide text-slate-500 mb-1">Employee</p>
                <Popover open={userPickerOpen} onOpenChange={setUserPickerOpen}>
                  <PopoverTrigger asChild>
                    <Button
                      variant="outline"
                      role="combobox"
                      aria-expanded={userPickerOpen}
                      className="w-full justify-between font-normal"
                      data-testid={adminScope ? "job-team-user-select" : "job-team-user-select-pm"}
                    >
                      <span className="truncate text-left">
                        {pickedUser
                          ? `${pickedUser.name || pickedUser.email}${pickedUser.email ? " · " + pickedUser.email : ""}`
                          : (directory.length === 0
                              ? "No active candidates found — ask Admin"
                              : "Pick from existing roster")}
                      </span>
                      <ChevronsUpDown className="ml-2 h-4 w-4 shrink-0 opacity-50" />
                    </Button>
                  </PopoverTrigger>
                  <PopoverContent className="w-[var(--radix-popover-trigger-width)] p-0" align="start">
                    <Command>
                      <CommandInput
                        placeholder="Type a name or email…"
                        data-testid="job-team-user-search"
                      />
                      <CommandList>
                        <CommandEmpty>
                          {directory.length === 0
                            ? "No active candidates found."
                            : "No employee matches."}
                        </CommandEmpty>
                        <CommandGroup>
                          {directory.map((u) => {
                            const label = (u.name || u.email || "").toString();
                            const portals = Array.isArray(u.portals) ? u.portals.join("/") : "";
                            // Build a single string cmdk uses for matching:
                            const value = `${label} ${u.email || ""} ${portals}`.toLowerCase();
                            const commit = () => { setNewUserId(u.id); setUserPickerOpen(false); };
                            const testid = `job-team-user-option-${u.id}`;
                            return (
                              <CommandItem
                                key={u.id}
                                value={value}
                                data-testid={testid}
                                onSelect={guardedUserPickerSelect(commit)}
                                {...userPickerHandlers(commit, testid)}
                              >
                                <Check className={`mr-2 h-4 w-4 ${newUserId === u.id ? "opacity-100" : "opacity-0"}`} />
                                <span className="flex-1 min-w-0">
                                  <span className="block truncate">
                                    {label}
                                    {portals ? <span className="ml-1 text-xs text-slate-500">· {portals}</span> : null}
                                  </span>
                                  {u.email ? (
                                    <span className="block text-xs text-slate-500 truncate">{u.email}</span>
                                  ) : null}
                                </span>
                              </CommandItem>
                            );
                          })}
                        </CommandGroup>
                      </CommandList>
                    </Command>
                  </PopoverContent>
                </Popover>
              </div>

              <div>
                <p className="text-xs font-medium uppercase tracking-wide text-slate-500 mb-1">Notes (optional)</p>
                <Input
                  placeholder="Notes (optional)"
                  value={newNotes}
                  onChange={(e) => setNewNotes(e.target.value)}
                  data-testid="job-team-notes"
                />
              </div>

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
            <DialogFooter>
              <Button
                variant="ghost"
                onClick={closeAdd}
                data-testid="job-team-cancel"
              >
                Cancel
              </Button>
              <Button
                onClick={handleAdd}
                disabled={submitting || !newRole || !newUserId}
                data-testid="job-team-submit"
              >
                {submitting ? "Adding…" : "Add"}
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>

        {adminScope && (
          <AssignmentHistoryDrawer
            open={historyOpen}
            onOpenChange={setHistoryOpen}
            items={audit}
          />
        )}

        <RemoveReasonDialog
          open={!!removeTarget}
          onOpenChange={(v) => { if (!v) setRemoveTarget(null); }}
          member={
            removeTarget
              ? {
                  id: removeTarget.id,
                  display_name: displayNameOf(removeTarget),
                  email: removeTarget.email,
                  role_label:
                    removeTarget.role_label ||
                    (registry.find((r) => r.key === removeTarget.assignment_role)?.label) ||
                    removeTarget.assignment_role,
                }
              : null
          }
          onConfirm={handleRemoveConfirm}
        />
      </CardContent>
    </Card>
  );
}
