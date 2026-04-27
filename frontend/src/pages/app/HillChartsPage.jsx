import React, { useEffect, useState, useRef } from "react";
import { Link, useParams } from "react-router-dom";
import { ArrowLeft, Plus, Loader2, Trash2, TrendingUp } from "lucide-react";
import { toast } from "sonner";
import { api } from "@/lib/api";
import { useAuth } from "@/lib/authContext";
import { relativeTime, apiErr } from "@/lib/crewHubUi";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from "@/components/ui/dialog";

/**
 * Hill Charts — each "scope" is a dot on a hill curve:
 *   Position 0–50   = "figuring it out" (uphill)
 *   Position 50–100 = "making it happen" (downhill)
 *
 * SVG hill is a single path; every scope renders as a draggable dot at
 * hillY(position). Drag horizontally to update, release to PUT.
 */
export default function HillChartsPage() {
  const { projectId } = useParams();
  const { user } = useAuth();
  const [scopes, setScopes] = useState(null);
  const [open, setOpen] = useState(false);
  const [editScope, setEditScope] = useState(null);

  const load = async () => {
    try {
      const r = await api.get(`/projects/${projectId}/hill-scopes`);
      setScopes(r.data);
    } catch (e) {
      toast.error(apiErr(e?.response?.data?.detail, "Failed to load"));
    }
  };
  useEffect(() => { load(); }, [projectId]);

  return (
    <div className="p-8 sm:p-10 max-w-5xl" data-testid="hill-charts-page">
      <Link to={`/app/projects/${projectId}`} className="inline-flex items-center gap-1 text-xs font-mono uppercase tracking-[0.2em] text-slate-500 hover:text-red-700 font-bold mb-6">
        <ArrowLeft className="w-3 h-3" /> Back to project
      </Link>

      <div className="flex items-start justify-between gap-4 flex-wrap mb-6">
        <div>
          <div className="font-mono text-[10px] uppercase tracking-[0.3em] text-red-700 font-bold">Hill Charts</div>
          <h1 className="font-display text-2xl sm:text-3xl font-black tracking-tight text-slate-900 mt-1">Progress at a glance</h1>
          <p className="text-slate-600 text-sm mt-1">Uphill means "still figuring it out." Downhill means "just executing now." Drag the dots.</p>
        </div>
        <Button onClick={() => setOpen(true)} className="h-10 bg-red-700 hover:bg-red-800 text-white font-bold uppercase tracking-wide text-xs" data-testid="new-scope-btn">
          <Plus className="w-4 h-4 mr-1" /> Add scope
        </Button>
      </div>

      {scopes === null && <div className="flex justify-center py-10"><Loader2 className="w-5 h-5 animate-spin text-red-700" /></div>}
      {scopes && scopes.length === 0 && (
        <div className="bg-white border-2 border-dashed border-slate-300 rounded-md p-10 text-center">
          <TrendingUp className="w-8 h-8 mx-auto text-slate-400" />
          <div className="font-mono text-[10px] uppercase tracking-[0.3em] text-slate-500 font-bold mt-3">No scopes yet</div>
          <p className="text-slate-600 text-sm mt-1">Add a scope per distinct stream of work (e.g. "Stormwater drainage", "Curb & gutter").</p>
        </div>
      )}

      {scopes && scopes.length > 0 && (
        <div className="bg-white border-2 border-slate-200 rounded-md p-5" data-testid="hill-chart-svg">
          <HillSvg scopes={scopes} onUpdate={load} onClickDot={(s) => setEditScope(s)} />
          <div className="mt-6 grid grid-cols-2 gap-3 text-xs">
            <div className="text-slate-600">← <strong>Uphill:</strong> still figuring it out</div>
            <div className="text-slate-600 text-right"><strong>Downhill:</strong> making it happen →</div>
          </div>
        </div>
      )}

      {scopes && scopes.length > 0 && (
        <div className="mt-6 space-y-2" data-testid="hill-scope-list">
          {scopes.map((s) => (
            <ScopeRow key={s.id} scope={s} user={user} onChange={load} onEdit={() => setEditScope(s)} />
          ))}
        </div>
      )}

      <NewScopeDialog open={open} onOpenChange={setOpen} projectId={projectId} onCreated={load} />
      <EditScopeDialog scope={editScope} onOpenChange={(o) => !o && setEditScope(null)} onDone={load} />
    </div>
  );
}

function hillY(pos) {
  // Half sine wave — 0 at x=0, peak (-80) at x=50, 0 at x=100
  return Math.round(-Math.sin((pos / 100) * Math.PI) * 80);
}

// Stable color per scope from id
function scopeColor(id) {
  const palette = ["#b91c1c", "#d97706", "#059669", "#2563eb", "#7c3aed", "#db2777", "#334155", "#ea580c"];
  const h = (id || "").split("").reduce((a, c) => a + c.charCodeAt(0), 0);
  return palette[h % palette.length];
}

function HillSvg({ scopes, onUpdate, onClickDot }) {
  const ref = useRef(null);
  const [dragging, setDragging] = useState(null); // {scopeId, lastPos}

  const W = 800;
  const H = 220;
  const margin = 40;
  const curveW = W - margin * 2;

  // Build curve path
  const pathPts = [];
  for (let i = 0; i <= 50; i++) {
    const pos = i * 2;
    const x = margin + (pos / 100) * curveW;
    const y = H - 30 + hillY(pos);
    pathPts.push(`${i === 0 ? "M" : "L"}${x},${y}`);
  }
  const path = pathPts.join(" ");

  const onPointerDown = (scope, e) => {
    e.preventDefault();
    setDragging({ scopeId: scope.id, pos: scope.position });
  };

  const onPointerMove = async (e) => {
    if (!dragging || !ref.current) return;
    const rect = ref.current.getBoundingClientRect();
    const clientX = e.clientX ?? e.touches?.[0]?.clientX;
    if (clientX == null) return;
    const x = clientX - rect.left;
    const svgX = (x / rect.width) * W;
    const newPos = Math.max(0, Math.min(100, Math.round(((svgX - margin) / curveW) * 100)));
    setDragging({ ...dragging, pos: newPos });
  };

  const onPointerUp = async () => {
    if (!dragging) return;
    const orig = scopes.find((s) => s.id === dragging.scopeId);
    const newPos = dragging.pos;
    setDragging(null);
    if (orig && newPos !== orig.position) {
      try {
        await api.put(`/hill-scopes/${orig.id}`, { position: newPos });
        onUpdate();
      } catch (e) {
        toast.error(apiErr(e?.response?.data?.detail, "Update failed"));
      }
    }
  };

  return (
    <svg
      ref={ref}
      viewBox={`0 0 ${W} ${H}`}
      className="w-full select-none touch-none"
      style={{ maxHeight: 280 }}
      onPointerMove={onPointerMove}
      onPointerUp={onPointerUp}
      onPointerLeave={onPointerUp}
    >
      {/* Dashed center line */}
      <line x1={W / 2} y1={20} x2={W / 2} y2={H - 20} stroke="#cbd5e1" strokeWidth="1.5" strokeDasharray="4 4" />
      {/* The hill */}
      <path d={path} fill="none" stroke="#334155" strokeWidth="2.5" strokeLinecap="round" />
      {/* Baseline */}
      <line x1={margin} y1={H - 30} x2={W - margin} y2={H - 30} stroke="#e2e8f0" strokeWidth="1" />
      {/* Labels */}
      <text x={margin} y={H - 6} fontSize="11" fill="#64748b" fontFamily="monospace">FIGURING IT OUT</text>
      <text x={W - margin} y={H - 6} fontSize="11" fill="#64748b" fontFamily="monospace" textAnchor="end">MAKING IT HAPPEN</text>

      {scopes.map((s) => {
        const liveOverride = dragging && dragging.scopeId === s.id ? dragging.pos : s.position;
        const cx = margin + (liveOverride / 100) * curveW;
        const cy = H - 30 + hillY(liveOverride);
        const color = scopeColor(s.id);
        return (
          <g key={s.id} data-testid={`hill-dot-${s.id}`}>
            <circle
              cx={cx} cy={cy} r="12" fill={color} stroke="white" strokeWidth="3"
              style={{ cursor: "grab", filter: "drop-shadow(0 1px 2px rgba(0,0,0,0.25))" }}
              onPointerDown={(e) => onPointerDown(s, e)}
              onClick={() => !dragging && onClickDot(s)}
            />
            <text x={cx} y={cy - 20} fontSize="11" fill="#0f172a" fontWeight="700" textAnchor="middle" style={{ pointerEvents: "none" }}>
              {s.title.length > 18 ? s.title.slice(0, 16) + "…" : s.title}
            </text>
          </g>
        );
      })}
    </svg>
  );
}

function ScopeRow({ scope, user, onChange, onEdit }) {
  const canDelete = scope.created_by === user?.id || ["owner", "admin"].includes(user?.role);
  const onDelete = async () => {
    if (!window.confirm(`Delete scope "${scope.title}"?`)) return;
    try {
      await api.delete(`/hill-scopes/${scope.id}`);
      toast.success("Deleted"); onChange();
    } catch (e) {
      toast.error(apiErr(e?.response?.data?.detail, "Delete failed"));
    }
  };
  const side = scope.position < 50 ? "Figuring out" : scope.position < 95 ? "Making it happen" : "Almost done";
  return (
    <div className="bg-white border-2 border-slate-200 rounded-md p-4 flex items-center gap-3" data-testid={`scope-row-${scope.id}`}>
      <div className="w-3 h-3 rounded-full shrink-0" style={{ background: scopeColor(scope.id) }} />
      <button onClick={onEdit} className="flex-1 text-left min-w-0">
        <div className="font-display font-bold text-slate-900 truncate">{scope.title}</div>
        <div className="font-mono text-[10px] uppercase tracking-[0.15em] text-slate-500 mt-0.5">
          {side} · {scope.position}% · updated {relativeTime(scope.last_update)}
        </div>
        {scope.last_note && <div className="text-xs text-slate-600 mt-1 line-clamp-1">"{scope.last_note}"</div>}
      </button>
      {canDelete && (
        <button onClick={onDelete} className="p-2 text-slate-300 hover:text-red-700" title="Delete">
          <Trash2 className="w-4 h-4" />
        </button>
      )}
    </div>
  );
}

function NewScopeDialog({ open, onOpenChange, projectId, onCreated }) {
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [saving, setSaving] = useState(false);
  useEffect(() => { if (!open) { setTitle(""); setDescription(""); } }, [open]);

  const onSave = async (e) => {
    e.preventDefault();
    setSaving(true);
    try {
      await api.post(`/projects/${projectId}/hill-scopes`, { title, description: description || null, position: 0 });
      toast.success("Scope added");
      onCreated(); onOpenChange(false);
    } catch (err) {
      toast.error(apiErr(err?.response?.data?.detail, "Create failed"));
    } finally { setSaving(false); }
  };
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent data-testid="new-scope-dialog">
        <DialogHeader><DialogTitle>Add scope</DialogTitle></DialogHeader>
        <form onSubmit={onSave} className="space-y-4">
          <div>
            <Label>Scope title</Label>
            <Input required value={title} onChange={(e) => setTitle(e.target.value)} className="mt-1.5" placeholder="e.g. Stormwater drainage" data-testid="new-scope-title" />
          </div>
          <div>
            <Label>Description <span className="text-slate-400 font-normal">(optional)</span></Label>
            <Textarea rows={3} value={description} onChange={(e) => setDescription(e.target.value)} className="mt-1.5" />
          </div>
          <DialogFooter>
            <Button type="button" variant="outline" onClick={() => onOpenChange(false)}>Cancel</Button>
            <Button type="submit" disabled={saving} className="bg-red-700 hover:bg-red-800 text-white font-bold uppercase tracking-wide" data-testid="new-scope-save">
              {saving ? <Loader2 className="w-4 h-4 animate-spin" /> : "Add scope"}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}

function EditScopeDialog({ scope, onOpenChange, onDone }) {
  const [note, setNote] = useState("");
  const [position, setPosition] = useState(0);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    if (scope) { setNote(""); setPosition(scope.position); }
  }, [scope?.id]); // eslint-disable-line

  const onSave = async (e) => {
    e.preventDefault();
    if (!scope) return;
    setSaving(true);
    try {
      await api.put(`/hill-scopes/${scope.id}`, { position, note: note || null });
      toast.success("Updated");
      onDone(); onOpenChange(false);
    } catch (err) {
      toast.error(apiErr(err?.response?.data?.detail, "Update failed"));
    } finally { setSaving(false); }
  };

  return (
    <Dialog open={!!scope} onOpenChange={onOpenChange}>
      <DialogContent data-testid="edit-scope-dialog">
        <DialogHeader><DialogTitle>{scope?.title}</DialogTitle></DialogHeader>
        {scope?.description && <div className="text-sm text-slate-600">{scope.description}</div>}
        <form onSubmit={onSave} className="space-y-4">
          <div>
            <Label>Position: {position}%</Label>
            <input
              type="range" min={0} max={100} value={position}
              onChange={(e) => setPosition(Number(e.target.value))}
              className="w-full mt-2"
              data-testid="edit-scope-slider"
            />
            <div className="flex justify-between font-mono text-[10px] uppercase tracking-[0.15em] text-slate-500 mt-1">
              <span>Figuring out</span>
              <span>Making it happen</span>
            </div>
          </div>
          <div>
            <Label>Update note <span className="text-slate-400 font-normal">(optional)</span></Label>
            <Textarea rows={2} value={note} onChange={(e) => setNote(e.target.value)} className="mt-1.5" placeholder="What changed since last update?" />
          </div>
          <DialogFooter>
            <Button type="button" variant="outline" onClick={() => onOpenChange(false)}>Cancel</Button>
            <Button type="submit" disabled={saving} className="bg-red-700 hover:bg-red-800 text-white font-bold uppercase tracking-wide" data-testid="edit-scope-save">
              {saving ? <Loader2 className="w-4 h-4 animate-spin" /> : "Save update"}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
