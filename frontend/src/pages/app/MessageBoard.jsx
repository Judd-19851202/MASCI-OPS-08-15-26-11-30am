import React, { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import {
  ArrowLeft, Plus, MessageSquare, Trash2, Loader2, Send,
} from "lucide-react";
import { toast } from "sonner";
import { api } from "@/lib/api";
import { useAuth } from "@/lib/authContext";
import { UserAvatar, relativeTime, apiErr } from "@/lib/crewHubUi";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from "@/components/ui/dialog";

export default function MessageBoard() {
  const { projectId } = useParams();
  const { user } = useAuth();
  const [msgs, setMsgs] = useState(null);
  const [open, setOpen] = useState(false);
  const [selected, setSelected] = useState(null);

  const load = async () => {
    try {
      const r = await api.get(`/projects/${projectId}/messages`);
      setMsgs(r.data);
    } catch (e) {
      toast.error(apiErr(e?.response?.data?.detail, "Failed to load messages"));
    }
  };
  useEffect(() => { load(); }, [projectId]);

  return (
    <div className="p-8 sm:p-10 max-w-4xl" data-testid="message-board">
      <Link to={`/app/projects/${projectId}`} className="inline-flex items-center gap-1 text-xs font-mono uppercase tracking-[0.2em] text-slate-500 hover:text-red-700 font-bold mb-6">
        <ArrowLeft className="w-3 h-3" /> Back to project
      </Link>

      <div className="flex items-start justify-between gap-4 flex-wrap mb-6">
        <div>
          <div className="font-mono text-[10px] uppercase tracking-[0.3em] text-red-700 font-bold">Message Board</div>
          <h1 className="font-display text-2xl sm:text-3xl font-black tracking-tight text-slate-900 mt-1">Post an update</h1>
          <p className="text-slate-600 text-sm mt-1">Announcements, discussion, photos. One thread per topic.</p>
        </div>
        <Button onClick={() => setOpen(true)} className="h-10 bg-red-700 hover:bg-red-800 text-white font-bold uppercase tracking-wide text-xs" data-testid="new-message-btn">
          <Plus className="w-4 h-4 mr-1" /> New Post
        </Button>
      </div>

      {msgs === null && <div className="flex justify-center py-10"><Loader2 className="w-5 h-5 animate-spin text-red-700" /></div>}
      {msgs && msgs.length === 0 && (
        <div className="bg-white border-2 border-dashed border-slate-300 rounded-md p-10 text-center">
          <MessageSquare className="w-8 h-8 mx-auto text-slate-400" />
          <div className="font-mono text-[10px] uppercase tracking-[0.3em] text-slate-500 font-bold mt-3">No posts yet</div>
          <p className="text-slate-600 text-sm mt-1">Kick things off with the first announcement.</p>
        </div>
      )}

      <div className="space-y-3">
        {msgs?.map((m) => (
          <button
            key={m.id}
            onClick={() => setSelected(m.id)}
            className="w-full text-left bg-white border-2 border-slate-200 hover:border-red-700 rounded-md p-4 transition-colors"
            data-testid={`message-row-${m.id}`}
          >
            <div className="flex items-start gap-3">
              <UserAvatar name={m.author.name} userId={m.author.user_id} size="md" />
              <div className="flex-1 min-w-0">
                <div className="font-display font-black text-slate-900 truncate">{m.title}</div>
                <div className="text-sm text-slate-600 mt-1 line-clamp-2">{m.body}</div>
                <div className="flex items-center gap-3 text-xs font-mono uppercase tracking-[0.1em] text-slate-500 mt-2">
                  <span className="font-bold">{m.author.name}</span>
                  <span>{relativeTime(m.created_at)}</span>
                  <span className="inline-flex items-center gap-1"><MessageSquare className="w-3 h-3" /> {m.comment_count}</span>
                </div>
              </div>
            </div>
          </button>
        ))}
      </div>

      <NewPost open={open} onOpenChange={setOpen} projectId={projectId} onCreated={load} />
      <MessageThread
        messageId={selected}
        onClose={() => { setSelected(null); load(); }}
        currentUser={user}
      />
    </div>
  );
}

function NewPost({ open, onOpenChange, projectId, onCreated }) {
  const [title, setTitle] = useState("");
  const [body, setBody] = useState("");
  const [saving, setSaving] = useState(false);
  useEffect(() => { if (!open) { setTitle(""); setBody(""); } }, [open]);

  const onSave = async (e) => {
    e.preventDefault();
    setSaving(true);
    try {
      await api.post(`/projects/${projectId}/messages`, { title, body });
      toast.success("Posted");
      onCreated();
      onOpenChange(false);
    } catch (e) {
      toast.error(apiErr(e?.response?.data?.detail, "Post failed"));
    } finally {
      setSaving(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-xl" data-testid="new-message-dialog">
        <DialogHeader><DialogTitle className="font-display">New post</DialogTitle></DialogHeader>
        <form onSubmit={onSave} className="space-y-4">
          <div>
            <Label>Title</Label>
            <Input required value={title} onChange={(e) => setTitle(e.target.value)} className="mt-1.5" data-testid="new-message-title" />
          </div>
          <div>
            <Label>Message</Label>
            <Textarea required rows={6} value={body} onChange={(e) => setBody(e.target.value)} className="mt-1.5" data-testid="new-message-body" />
          </div>
          <DialogFooter>
            <Button type="button" variant="outline" onClick={() => onOpenChange(false)}>Cancel</Button>
            <Button type="submit" disabled={saving} className="bg-red-700 hover:bg-red-800 text-white font-bold uppercase tracking-wide" data-testid="new-message-save">
              {saving ? <Loader2 className="w-4 h-4 animate-spin" /> : "Post"}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}

function MessageThread({ messageId, onClose, currentUser }) {
  const [msg, setMsg] = useState(null);
  const [comments, setComments] = useState([]);
  const [newComment, setNewComment] = useState("");
  const [posting, setPosting] = useState(false);

  useEffect(() => {
    let alive = true;
    if (!messageId) { setMsg(null); setComments([]); return; }
    (async () => {
      try {
        const [m, c] = await Promise.all([
          api.get(`/messages/${messageId}`),
          api.get(`/messages/${messageId}/comments`),
        ]);
        if (!alive) return;
        setMsg(m.data);
        setComments(c.data);
      } catch (e) {
        toast.error(apiErr(e?.response?.data?.detail, "Failed to load thread"));
      }
    })();
    return () => { alive = false; };
  }, [messageId]);

  const onComment = async (e) => {
    e.preventDefault();
    if (!newComment.trim()) return;
    setPosting(true);
    try {
      const r = await api.post(`/messages/${messageId}/comments`, { body: newComment });
      setComments([...comments, r.data]);
      setNewComment("");
    } catch (err) {
      toast.error(apiErr(err?.response?.data?.detail, "Comment failed"));
    } finally { setPosting(false); }
  };

  const onDelete = async () => {
    if (!window.confirm("Delete this post and all its comments?")) return;
    try {
      await api.delete(`/messages/${messageId}`);
      toast.success("Deleted");
      onClose();
    } catch (e) {
      toast.error(apiErr(e?.response?.data?.detail, "Delete failed"));
    }
  };

  const canDelete = msg && currentUser && (msg.author.user_id === currentUser.id || ["owner","admin"].includes(currentUser.role));

  return (
    <Dialog open={!!messageId} onOpenChange={(o) => !o && onClose()}>
      <DialogContent className="max-w-2xl max-h-[85vh] overflow-y-auto" data-testid="message-thread">
        {!msg ? (
          <div className="flex justify-center py-10"><Loader2 className="w-5 h-5 animate-spin text-red-700" /></div>
        ) : (
          <>
            <DialogHeader>
              <div className="flex items-start gap-3">
                <UserAvatar name={msg.author.name} userId={msg.author.user_id} />
                <div className="flex-1 min-w-0">
                  <DialogTitle className="font-display text-xl leading-tight">{msg.title}</DialogTitle>
                  <div className="text-xs font-mono uppercase tracking-[0.15em] text-slate-500 mt-1">
                    {msg.author.name} · {relativeTime(msg.created_at)}
                  </div>
                </div>
                {canDelete && (
                  <button onClick={onDelete} className="p-2 text-slate-400 hover:text-red-700" title="Delete post">
                    <Trash2 className="w-4 h-4" />
                  </button>
                )}
              </div>
            </DialogHeader>
            <div className="whitespace-pre-wrap text-slate-800 text-sm leading-relaxed mt-2">{msg.body}</div>

            <div className="mt-6 pt-5 border-t-2 border-slate-100">
              <div className="font-mono text-[10px] uppercase tracking-[0.3em] text-red-700 font-bold mb-3">
                Comments · {comments.length}
              </div>
              <div className="space-y-3">
                {comments.map((c) => (
                  <div key={c.id} className="flex items-start gap-3" data-testid={`comment-${c.id}`}>
                    <UserAvatar name={c.author.name} userId={c.author.user_id} size="sm" />
                    <div className="flex-1 min-w-0">
                      <div className="text-xs font-mono uppercase tracking-[0.1em] text-slate-500">
                        <span className="font-bold text-slate-800">{c.author.name}</span> · {relativeTime(c.created_at)}
                      </div>
                      <div className="text-sm text-slate-800 whitespace-pre-wrap mt-0.5">{c.body}</div>
                    </div>
                  </div>
                ))}
              </div>
              <form onSubmit={onComment} className="mt-4 flex gap-2">
                <Input
                  value={newComment}
                  onChange={(e) => setNewComment(e.target.value)}
                  placeholder="Write a comment…"
                  data-testid="comment-input"
                />
                <Button type="submit" disabled={posting || !newComment.trim()} className="bg-red-700 hover:bg-red-800 text-white">
                  {posting ? <Loader2 className="w-4 h-4 animate-spin" /> : <Send className="w-4 h-4" />}
                </Button>
              </form>
            </div>
          </>
        )}
      </DialogContent>
    </Dialog>
  );
}
