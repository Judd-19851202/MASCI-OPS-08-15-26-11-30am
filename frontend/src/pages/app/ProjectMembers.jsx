import React, { useEffect, useState, useCallback } from "react";
import { Link, useParams } from "react-router-dom";
import { ArrowLeft, Loader2, UserMinus, UserPlus, ShieldCheck, Shield, User as UserIcon } from "lucide-react";
import { toast } from "sonner";
import { api } from "@/lib/api";
import { useAuth } from "@/lib/authContext";
import { Button } from "@/components/ui/button";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";

function apiErr(detail, fallback) {
  if (!detail) return fallback;
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail)) return detail.map((e) => e?.msg || JSON.stringify(e)).join(" ");
  return detail?.msg || String(detail);
}

const roleBadge = (role) => {
  const map = {
    owner: { Icon: ShieldCheck, cls: "text-red-700 bg-red-50", label: "Owner" },
    admin: { Icon: Shield, cls: "text-amber-700 bg-amber-50", label: "Admin" },
    member: { Icon: UserIcon, cls: "text-slate-700 bg-slate-100", label: "Member" },
  };
  return map[role] || map.member;
};

/**
 * ProjectMembers — list + add/remove members for a single project.
 * HQ is a special case: auto-includes every active user, no add/remove.
 */
export default function ProjectMembers() {
  const { projectId } = useParams();
  const { user: me } = useAuth();
  const [project, setProject] = useState(null);
  const [members, setMembers] = useState([]);
  const [allUsers, setAllUsers] = useState([]);
  const [adding, setAdding] = useState("");
  const [saving, setSaving] = useState(false);

  const isAdmin = me?.role === "owner" || me?.role === "admin";

  const load = useCallback(async () => {
    try {
      const [p, m] = await Promise.all([
        api.get(`/projects/${projectId}`),
        api.get(`/projects/${projectId}/members`),
      ]);
      setProject(p.data);
      setMembers(m.data || []);
      if (isAdmin && !p.data.is_hq) {
        const u = await api.get("/users");
        setAllUsers((u.data || []).filter((x) => x.is_active));
      }
    } catch (err) {
      toast.error(apiErr(err?.response?.data?.detail, "Failed to load members"));
    }
  }, [projectId, isAdmin]);

  useEffect(() => { load(); }, [load]);

  const availableToAdd = allUsers.filter(
    (u) => !members.find((m) => m.user_id === u.id)
  );

  const onAdd = async () => {
    if (!adding) return;
    setSaving(true);
    try {
      await api.post(`/projects/${projectId}/members`, { user_id: adding });
      toast.success("Added to project");
      setAdding("");
      await load();
    } catch (err) {
      toast.error(apiErr(err?.response?.data?.detail, "Add failed"));
    } finally {
      setSaving(false);
    }
  };

  const onRemove = async (userId, name) => {
    if (!window.confirm(`Remove ${name} from this project?`)) return;
    setSaving(true);
    try {
      await api.delete(`/projects/${projectId}/members/${userId}`);
      toast.success("Removed");
      await load();
    } catch (err) {
      toast.error(apiErr(err?.response?.data?.detail, "Remove failed"));
    } finally {
      setSaving(false);
    }
  };

  if (!project) {
    return (
      <div className="flex items-center justify-center py-24">
        <Loader2 className="w-6 h-6 animate-spin text-red-700" />
      </div>
    );
  }

  return (
    <div className="p-8 sm:p-10 max-w-4xl" data-testid="project-members">
      <Link
        to={`/app/projects/${projectId}`}
        className="inline-flex items-center gap-1 text-xs font-mono uppercase tracking-[0.2em] text-slate-500 hover:text-red-700 font-bold mb-6"
      >
        <ArrowLeft className="w-3 h-3" /> Back to {project.name}
      </Link>

      <div className="mb-6">
        <div className="font-mono text-[10px] uppercase tracking-[0.3em] text-red-700 font-bold">
          Members · {members.length}
        </div>
        <h1 className="font-display text-2xl sm:text-3xl font-black tracking-tight text-slate-900 mt-1">
          Who's on this project
        </h1>
        {project.is_hq && (
          <p className="text-slate-600 text-sm mt-1.5">
            MASCI HQ auto-includes every active user. To remove someone from HQ, deactivate their account in Users.
          </p>
        )}
      </div>

      {isAdmin && !project.is_hq && availableToAdd.length > 0 && (
        <div className="mb-6 bg-white border-2 border-slate-200 rounded-md p-4 flex items-center gap-2" data-testid="add-member-row">
          <UserPlus className="w-4 h-4 text-red-700 shrink-0" />
          <Select value={adding} onValueChange={setAdding}>
            <SelectTrigger className="flex-1" data-testid="add-member-select">
              <SelectValue placeholder="Add a user to this project…" />
            </SelectTrigger>
            <SelectContent>
              {availableToAdd.map((u) => (
                <SelectItem key={u.id} value={u.id}>
                  {u.name} — {u.email}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          <Button
            onClick={onAdd}
            disabled={!adding || saving}
            className="bg-red-700 hover:bg-red-800 text-white font-bold uppercase tracking-wide text-xs"
            data-testid="add-member-save"
          >
            Add
          </Button>
        </div>
      )}

      <div className="bg-white border-2 border-slate-200 rounded-md overflow-hidden">
        {members.length === 0 && (
          <div className="p-8 text-center text-slate-500 italic text-sm">No members yet.</div>
        )}
        {members.map((m) => {
          const badge = roleBadge(m.role);
          const Icon = badge.Icon;
          return (
            <div key={m.user_id} className="flex items-center gap-3 p-4 border-b border-slate-100 last:border-0" data-testid={`member-row-${m.user_id}`}>
              <div className="w-10 h-10 rounded-full bg-slate-900 text-white flex items-center justify-center font-display font-black text-sm shrink-0">
                {m.name.charAt(0).toUpperCase()}
              </div>
              <div className="flex-1 min-w-0">
                <div className="font-display font-bold text-slate-900 truncate">{m.name}</div>
                <div className="font-mono text-xs text-slate-500 truncate">{m.email}</div>
              </div>
              <span className={`inline-flex items-center gap-1 px-2 py-1 rounded text-[10px] font-mono uppercase tracking-[0.15em] font-bold ${badge.cls}`}>
                <Icon className="w-3 h-3" /> {badge.label}
              </span>
              {isAdmin && !project.is_hq && (
                <button
                  onClick={() => onRemove(m.user_id, m.name)}
                  disabled={saving}
                  className="p-2 text-slate-400 hover:text-red-700 disabled:opacity-40"
                  title="Remove from project"
                  data-testid={`remove-member-${m.user_id}`}
                >
                  <UserMinus className="w-4 h-4" />
                </button>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
