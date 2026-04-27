import React, { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import {
  ArrowLeft, Plus, ListChecks, Trash2, Loader2, Check, Calendar, User as UserIcon,
} from "lucide-react";
import { toast } from "sonner";
import { api } from "@/lib/api";
import { UserAvatar, apiErr } from "@/lib/crewHubUi";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from "@/components/ui/dialog";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";

export default function TodosPage() {
  const { projectId } = useParams();
  const [lists, setLists] = useState(null);
  const [members, setMembers] = useState([]);
  const [showNewList, setShowNewList] = useState(false);

  const load = async () => {
    try {
      const [l, m] = await Promise.all([
        api.get(`/projects/${projectId}/todo-lists`),
        api.get(`/projects/${projectId}/members`),
      ]);
      setLists(l.data);
      setMembers(m.data);
    } catch (e) {
      toast.error(apiErr(e?.response?.data?.detail, "Failed to load"));
    }
  };
  useEffect(() => { load(); }, [projectId]);

  return (
    <div className="p-8 sm:p-10 max-w-5xl" data-testid="todos-page">
      <Link to={`/app/projects/${projectId}`} className="inline-flex items-center gap-1 text-xs font-mono uppercase tracking-[0.2em] text-slate-500 hover:text-red-700 font-bold mb-6">
        <ArrowLeft className="w-3 h-3" /> Back to project
      </Link>

      <div className="flex items-start justify-between gap-4 flex-wrap mb-6">
        <div>
          <div className="font-mono text-[10px] uppercase tracking-[0.3em] text-red-700 font-bold">To-dos</div>
          <h1 className="font-display text-2xl sm:text-3xl font-black tracking-tight text-slate-900 mt-1">Get it done</h1>
          <p className="text-slate-600 text-sm mt-1">Lists, assignees, due dates. Check it off when it's done.</p>
        </div>
        <Button onClick={() => setShowNewList(true)} className="h-10 bg-red-700 hover:bg-red-800 text-white font-bold uppercase tracking-wide text-xs" data-testid="new-list-btn">
          <Plus className="w-4 h-4 mr-1" /> New List
        </Button>
      </div>

      {lists === null && <div className="flex justify-center py-10"><Loader2 className="w-5 h-5 animate-spin text-red-700" /></div>}
      {lists && lists.length === 0 && (
        <div className="bg-white border-2 border-dashed border-slate-300 rounded-md p-10 text-center">
          <ListChecks className="w-8 h-8 mx-auto text-slate-400" />
          <div className="font-mono text-[10px] uppercase tracking-[0.3em] text-slate-500 font-bold mt-3">No lists yet</div>
          <p className="text-slate-600 text-sm mt-1">Make your first list — e.g. "Site prep" or "Punch list".</p>
        </div>
      )}

      <div className="space-y-6">
        {lists?.map((lst) => <TodoList key={lst.id} list={lst} members={members} onChange={load} />)}
      </div>

      <NewListDialog open={showNewList} onOpenChange={setShowNewList} projectId={projectId} onCreated={load} />
    </div>
  );
}

function NewListDialog({ open, onOpenChange, projectId, onCreated }) {
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [saving, setSaving] = useState(false);
  useEffect(() => { if (!open) { setName(""); setDescription(""); } }, [open]);

  const onSave = async (e) => {
    e.preventDefault();
    setSaving(true);
    try {
      await api.post(`/projects/${projectId}/todo-lists`, { name, description: description || null });
      toast.success("List created");
      onCreated(); onOpenChange(false);
    } catch (err) {
      toast.error(apiErr(err?.response?.data?.detail, "Create failed"));
    } finally { setSaving(false); }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent data-testid="new-list-dialog">
        <DialogHeader><DialogTitle>New list</DialogTitle></DialogHeader>
        <form onSubmit={onSave} className="space-y-4">
          <div>
            <Label>Name</Label>
            <Input required value={name} onChange={(e) => setName(e.target.value)} className="mt-1.5" data-testid="new-list-name" />
          </div>
          <div>
            <Label>Description <span className="text-slate-400 font-normal">(optional)</span></Label>
            <Textarea rows={3} value={description} onChange={(e) => setDescription(e.target.value)} className="mt-1.5" />
          </div>
          <DialogFooter>
            <Button type="button" variant="outline" onClick={() => onOpenChange(false)}>Cancel</Button>
            <Button type="submit" disabled={saving} className="bg-red-700 hover:bg-red-800 text-white font-bold uppercase tracking-wide">
              {saving ? <Loader2 className="w-4 h-4 animate-spin" /> : "Create list"}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}

function TodoList({ list, members, onChange }) {
  const [items, setItems] = useState(null);
  const [adding, setAdding] = useState(false);
  const [newItem, setNewItem] = useState("");
  const [newAssignee, setNewAssignee] = useState("");
  const [newDue, setNewDue] = useState("");

  const load = async () => {
    try {
      const r = await api.get(`/todo-lists/${list.id}/items`);
      setItems(r.data);
    } catch (e) {
      toast.error(apiErr(e?.response?.data?.detail, "Failed to load items"));
    }
  };
  useEffect(() => { load(); }, [list.id]);

  const onAdd = async (e) => {
    e.preventDefault();
    if (!newItem.trim()) return;
    setAdding(true);
    try {
      await api.post(`/todos`, {
        list_id: list.id, title: newItem,
        assignee_id: newAssignee || null,
        due_date: newDue || null,
      });
      setNewItem(""); setNewAssignee(""); setNewDue("");
      await load();
      onChange();
    } catch (err) {
      toast.error(apiErr(err?.response?.data?.detail, "Add failed"));
    } finally { setAdding(false); }
  };

  const onToggle = async (item) => {
    try {
      await api.put(`/todos/${item.id}`, { completed: !item.completed_at });
      await load(); onChange();
    } catch (err) {
      toast.error(apiErr(err?.response?.data?.detail, "Update failed"));
    }
  };

  const onDelete = async (id) => {
    try {
      await api.delete(`/todos/${id}`);
      await load(); onChange();
    } catch (err) {
      toast.error(apiErr(err?.response?.data?.detail, "Delete failed"));
    }
  };

  const onDeleteList = async () => {
    if (!window.confirm(`Delete list "${list.name}" and all its items?`)) return;
    try {
      await api.delete(`/todo-lists/${list.id}`);
      toast.success("List deleted");
      onChange();
    } catch (err) {
      toast.error(apiErr(err?.response?.data?.detail, "Delete failed"));
    }
  };

  const open = items?.filter((i) => !i.completed_at) || [];
  const done = items?.filter((i) => i.completed_at) || [];

  return (
    <div className="bg-white border-2 border-slate-200 rounded-md p-5" data-testid={`todo-list-${list.id}`}>
      <div className="flex items-start justify-between gap-3 mb-4">
        <div>
          <div className="font-display font-black text-lg text-slate-900">{list.name}</div>
          {list.description && <div className="text-sm text-slate-600 mt-0.5">{list.description}</div>}
          <div className="font-mono text-[10px] uppercase tracking-[0.2em] text-slate-500 mt-1 font-bold">
            {list.open_count} open · {list.done_count} done
          </div>
        </div>
        <button onClick={onDeleteList} className="p-2 text-slate-400 hover:text-red-700" title="Delete list">
          <Trash2 className="w-4 h-4" />
        </button>
      </div>

      <div className="space-y-1.5">
        {open.map((i) => <TodoRow key={i.id} item={i} onToggle={onToggle} onDelete={onDelete} />)}
      </div>

      {done.length > 0 && (
        <div className="mt-4 pt-3 border-t border-slate-100">
          <div className="font-mono text-[9px] uppercase tracking-[0.2em] text-slate-400 font-bold mb-2">Done · {done.length}</div>
          <div className="space-y-1.5">
            {done.map((i) => <TodoRow key={i.id} item={i} onToggle={onToggle} onDelete={onDelete} />)}
          </div>
        </div>
      )}

      <form onSubmit={onAdd} className="mt-4 pt-3 border-t border-slate-100 grid grid-cols-1 sm:grid-cols-[1fr,auto,auto,auto] gap-2">
        <Input
          value={newItem} onChange={(e) => setNewItem(e.target.value)}
          placeholder="Add a to-do…" className="h-9"
          data-testid={`new-item-input-${list.id}`}
        />
        <Select value={newAssignee || "unassigned"} onValueChange={(v) => setNewAssignee(v === "unassigned" ? "" : v)}>
          <SelectTrigger className="h-9 w-40 text-xs"><SelectValue placeholder="Assign…" /></SelectTrigger>
          <SelectContent>
            <SelectItem value="unassigned">Unassigned</SelectItem>
            {members.map((m) => <SelectItem key={m.user_id} value={m.user_id}>{m.name}</SelectItem>)}
          </SelectContent>
        </Select>
        <Input type="date" value={newDue} onChange={(e) => setNewDue(e.target.value)} className="h-9 w-36 text-xs" />
        <Button type="submit" disabled={adding || !newItem.trim()} className="h-9 bg-red-700 hover:bg-red-800 text-white" data-testid={`add-item-${list.id}`}>
          {adding ? <Loader2 className="w-4 h-4 animate-spin" /> : <Plus className="w-4 h-4" />}
        </Button>
      </form>
    </div>
  );
}

function TodoRow({ item, onToggle, onDelete }) {
  const done = !!item.completed_at;
  const overdue = !done && item.due_date && new Date(item.due_date) < new Date(new Date().toDateString());
  return (
    <div className={`flex items-center gap-2 py-1.5 rounded hover:bg-slate-50 -mx-1 px-1 ${done ? "opacity-60" : ""}`} data-testid={`todo-${item.id}`}>
      <button
        onClick={() => onToggle(item)}
        className={`w-5 h-5 rounded border-2 flex items-center justify-center shrink-0 transition-colors ${done ? "bg-emerald-600 border-emerald-600 text-white" : "border-slate-300 hover:border-red-700"}`}
        aria-label={done ? "Mark incomplete" : "Mark complete"}
        data-testid={`todo-toggle-${item.id}`}
      >
        {done && <Check className="w-3 h-3" />}
      </button>
      <div className="flex-1 min-w-0 text-sm">
        <span className={done ? "line-through text-slate-500" : "text-slate-900"}>{item.title}</span>
      </div>
      {item.due_date && (
        <span className={`inline-flex items-center gap-1 text-xs font-mono ${overdue ? "text-red-700 font-bold" : "text-slate-500"}`}>
          <Calendar className="w-3 h-3" /> {new Date(item.due_date + "T12:00:00").toLocaleDateString(undefined, { month: "short", day: "numeric" })}
        </span>
      )}
      {item.assignee && <UserAvatar name={item.assignee.name} userId={item.assignee.user_id} size="xs" />}
      <button onClick={() => onDelete(item.id)} className="p-1 text-slate-300 hover:text-red-700" title="Delete">
        <Trash2 className="w-3.5 h-3.5" />
      </button>
    </div>
  );
}
