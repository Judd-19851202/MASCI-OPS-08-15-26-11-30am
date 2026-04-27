import React, { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { ArrowLeft, Plus, Calendar, MapPin, Trash2, Loader2 } from "lucide-react";
import { toast } from "sonner";
import { api } from "@/lib/api";
import { useAuth } from "@/lib/authContext";
import { apiErr } from "@/lib/crewHubUi";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from "@/components/ui/dialog";

export default function SchedulePage() {
  const { projectId } = useParams();
  const { user } = useAuth();
  const [events, setEvents] = useState(null);
  const [open, setOpen] = useState(false);

  const load = async () => {
    try {
      const r = await api.get(`/projects/${projectId}/events`);
      setEvents(r.data);
    } catch (e) {
      toast.error(apiErr(e?.response?.data?.detail, "Failed to load events"));
    }
  };
  useEffect(() => { load(); }, [projectId]);

  const onDelete = async (id) => {
    if (!window.confirm("Delete this event?")) return;
    try {
      await api.delete(`/events/${id}`);
      toast.success("Deleted");
      load();
    } catch (e) {
      toast.error(apiErr(e?.response?.data?.detail, "Delete failed"));
    }
  };

  // Group by date
  const grouped = {};
  (events || []).forEach((e) => {
    const k = e.starts_at.slice(0, 10);
    (grouped[k] = grouped[k] || []).push(e);
  });
  const keys = Object.keys(grouped).sort();

  const fmtDate = (iso) => new Date(iso + "T12:00:00").toLocaleDateString(undefined, { weekday: "long", month: "short", day: "numeric" });
  const fmtTime = (iso) => new Date(iso).toLocaleTimeString(undefined, { hour: "numeric", minute: "2-digit" });

  return (
    <div className="p-8 sm:p-10 max-w-4xl" data-testid="schedule-page">
      <Link to={`/app/projects/${projectId}`} className="inline-flex items-center gap-1 text-xs font-mono uppercase tracking-[0.2em] text-slate-500 hover:text-red-700 font-bold mb-6">
        <ArrowLeft className="w-3 h-3" /> Back to project
      </Link>

      <div className="flex items-start justify-between gap-4 flex-wrap mb-6">
        <div>
          <div className="font-mono text-[10px] uppercase tracking-[0.3em] text-red-700 font-bold">Schedule</div>
          <h1 className="font-display text-2xl sm:text-3xl font-black tracking-tight text-slate-900 mt-1">What's coming up</h1>
          <p className="text-slate-600 text-sm mt-1">Inspections, pre-cons, deliveries — all in one place.</p>
        </div>
        <Button onClick={() => setOpen(true)} className="h-10 bg-red-700 hover:bg-red-800 text-white font-bold uppercase tracking-wide text-xs" data-testid="new-event-btn">
          <Plus className="w-4 h-4 mr-1" /> Add event
        </Button>
      </div>

      {events === null && <div className="flex justify-center py-10"><Loader2 className="w-5 h-5 animate-spin text-red-700" /></div>}
      {events && events.length === 0 && (
        <div className="bg-white border-2 border-dashed border-slate-300 rounded-md p-10 text-center">
          <Calendar className="w-8 h-8 mx-auto text-slate-400" />
          <div className="font-mono text-[10px] uppercase tracking-[0.3em] text-slate-500 font-bold mt-3">Nothing scheduled</div>
        </div>
      )}

      <div className="space-y-5">
        {keys.map((k) => (
          <div key={k} data-testid={`schedule-day-${k}`}>
            <div className="font-mono text-[10px] uppercase tracking-[0.3em] text-red-700 font-black mb-2">{fmtDate(k)}</div>
            <div className="space-y-2">
              {grouped[k].map((e) => {
                const canDelete = e.created_by === user?.id || ["owner", "admin"].includes(user?.role);
                return (
                  <div key={e.id} className="bg-white border-2 border-slate-200 rounded-md p-4 flex items-start gap-3" data-testid={`event-row-${e.id}`}>
                    <div className="w-10 h-10 rounded-md bg-emerald-600 text-white flex items-center justify-center shrink-0">
                      <Calendar className="w-5 h-5" />
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="font-display font-black text-slate-900">{e.title}</div>
                      <div className="text-xs font-mono uppercase tracking-[0.1em] text-slate-500 mt-1">
                        {e.all_day ? "All day" : (<>
                          {fmtTime(e.starts_at)}{e.ends_at ? ` – ${fmtTime(e.ends_at)}` : ""}
                        </>)}
                      </div>
                      {e.location && <div className="flex items-center gap-1 text-xs text-slate-600 mt-1"><MapPin className="w-3 h-3" /> {e.location}</div>}
                      {e.description && <div className="text-sm text-slate-700 mt-2 whitespace-pre-wrap">{e.description}</div>}
                    </div>
                    {canDelete && (
                      <button onClick={() => onDelete(e.id)} className="p-2 text-slate-300 hover:text-red-700" title="Delete">
                        <Trash2 className="w-4 h-4" />
                      </button>
                    )}
                  </div>
                );
              })}
            </div>
          </div>
        ))}
      </div>

      <NewEventDialog open={open} onOpenChange={setOpen} projectId={projectId} onCreated={load} />
    </div>
  );
}

function NewEventDialog({ open, onOpenChange, projectId, onCreated }) {
  const [title, setTitle] = useState("");
  const [date, setDate] = useState("");
  const [startTime, setStartTime] = useState("09:00");
  const [endTime, setEndTime] = useState("10:00");
  const [allDay, setAllDay] = useState(false);
  const [location, setLocation] = useState("");
  const [description, setDescription] = useState("");
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    if (!open) { setTitle(""); setDate(""); setStartTime("09:00"); setEndTime("10:00"); setAllDay(false); setLocation(""); setDescription(""); }
  }, [open]);

  const onSave = async (e) => {
    e.preventDefault();
    if (!date) { toast.error("Pick a date"); return; }
    setSaving(true);
    try {
      const starts_at = allDay ? `${date}T00:00:00` : `${date}T${startTime}:00`;
      const ends_at = allDay ? null : `${date}T${endTime}:00`;
      await api.post(`/projects/${projectId}/events`, {
        title, starts_at, ends_at, all_day: allDay,
        location: location || null, description: description || null,
      });
      toast.success("Event added");
      onCreated(); onOpenChange(false);
    } catch (err) {
      toast.error(apiErr(err?.response?.data?.detail, "Create failed"));
    } finally { setSaving(false); }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent data-testid="new-event-dialog">
        <DialogHeader><DialogTitle>Add event</DialogTitle></DialogHeader>
        <form onSubmit={onSave} className="space-y-4">
          <div>
            <Label>Title</Label>
            <Input required value={title} onChange={(e) => setTitle(e.target.value)} className="mt-1.5" data-testid="new-event-title" />
          </div>
          <div>
            <Label>Date</Label>
            <Input type="date" required value={date} onChange={(e) => setDate(e.target.value)} className="mt-1.5" data-testid="new-event-date" />
          </div>
          <label className="flex items-center gap-2 text-sm">
            <input type="checkbox" checked={allDay} onChange={(e) => setAllDay(e.target.checked)} />
            All day
          </label>
          {!allDay && (
            <div className="grid grid-cols-2 gap-3">
              <div>
                <Label>Start</Label>
                <Input type="time" value={startTime} onChange={(e) => setStartTime(e.target.value)} className="mt-1.5" />
              </div>
              <div>
                <Label>End</Label>
                <Input type="time" value={endTime} onChange={(e) => setEndTime(e.target.value)} className="mt-1.5" />
              </div>
            </div>
          )}
          <div>
            <Label>Location <span className="text-slate-400 font-normal">(optional)</span></Label>
            <Input value={location} onChange={(e) => setLocation(e.target.value)} className="mt-1.5" />
          </div>
          <div>
            <Label>Description <span className="text-slate-400 font-normal">(optional)</span></Label>
            <Textarea rows={3} value={description} onChange={(e) => setDescription(e.target.value)} className="mt-1.5" />
          </div>
          <DialogFooter>
            <Button type="button" variant="outline" onClick={() => onOpenChange(false)}>Cancel</Button>
            <Button type="submit" disabled={saving} className="bg-red-700 hover:bg-red-800 text-white font-bold uppercase tracking-wide" data-testid="new-event-save">
              {saving ? <Loader2 className="w-4 h-4 animate-spin" /> : "Add event"}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
