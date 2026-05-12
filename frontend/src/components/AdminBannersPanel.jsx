import React, { useEffect, useState } from "react";
import {
  Megaphone,
  Plus,
  Edit3,
  Trash2,
  Loader2,
  Eye,
  EyeOff,
  CheckCircle2,
  Languages,
  AlertTriangle,
  AlertOctagon,
  OctagonAlert,
  Info,
  Clock,
  X,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from "@/components/ui/dialog";
import { api } from "@/lib/api";
import { toast } from "sonner";
import { HUB_BANNER_TEMPLATES, SEVERITY_META } from "@/lib/hubBannerTemplates";

/**
 * AdminBannersPanel — admin tool for managing the site-wide Hub
 * banner. Lives inside AdminHub.jsx between the email-routing block
 * and the Site Posters block (high-visibility position so admins
 * notice it during incident response).
 *
 * UX flow
 * -------
 *  1. Click "Post New Banner" → modal opens with a template picker
 *     across the top + freeform compose area below.
 *  2. Pick a template → title/body/severity/expires_at are prefilled.
 *     Admin can edit anything before saving (templates are scaffolds,
 *     not rigid).
 *  3. Click "Preview Spanish" to see the Claude translation before
 *     posting (optional — auto-translates on save anyway).
 *  4. Click "Post Banner" → banner appears on every page within 60s
 *     (poll interval on BannerStrip).
 *
 * Active list shows live ack/dismiss counts, expiration countdown,
 * and per-row Edit / Delete buttons.
 */
const SEVERITY_ICON = {
  info: Info,
  advisory: AlertTriangle,
  warning: AlertOctagon,
  critical: OctagonAlert,
};

const fmtRelative = (iso) => {
  if (!iso) return "never";
  try {
    const dt = new Date(iso);
    const diffMs = dt - new Date();
    const mins = Math.round(diffMs / 60000);
    if (Math.abs(mins) < 60) return mins > 0 ? `in ${mins}m` : `${-mins}m ago`;
    const hrs = Math.round(mins / 60);
    if (Math.abs(hrs) < 48) return hrs > 0 ? `in ${hrs}h` : `${-hrs}h ago`;
    const days = Math.round(hrs / 24);
    return days > 0 ? `in ${days}d` : `${-days}d ago`;
  } catch {
    return iso;
  }
};

function ComposeDialog({ open, onClose, initial, onSaved }) {
  const isEdit = !!initial?.id;
  const [title_en, setTitleEn] = useState(initial?.title_en || "");
  const [body_en, setBodyEn] = useState(initial?.body_en || "");
  const [title_es, setTitleEs] = useState(initial?.title_es || "");
  const [body_es, setBodyEs] = useState(initial?.body_es || "");
  const [severity, setSeverity] = useState(initial?.severity || "advisory");
  const [requireAck, setRequireAck] = useState(!!initial?.require_ack);
  const [expiresAt, setExpiresAt] = useState(initial?.expires_at || "");
  const [translating, setTranslating] = useState(false);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    setTitleEn(initial?.title_en || "");
    setBodyEn(initial?.body_en || "");
    setTitleEs(initial?.title_es || "");
    setBodyEs(initial?.body_es || "");
    setSeverity(initial?.severity || "advisory");
    setRequireAck(!!initial?.require_ack);
    setExpiresAt(initial?.expires_at || "");
  }, [initial, open]);

  const applyTemplate = (tpl) => {
    setTitleEn(tpl.title_en);
    setBodyEn(tpl.body_en);
    setSeverity(tpl.severity);
    setRequireAck(tpl.require_ack);
    setTitleEs("");
    setBodyEs("");
    if (tpl.default_expires_hours) {
      const dt = new Date(Date.now() + tpl.default_expires_hours * 3600 * 1000);
      // datetime-local needs "YYYY-MM-DDTHH:mm" in LOCAL time
      const pad = (n) => String(n).padStart(2, "0");
      setExpiresAt(
        `${dt.getFullYear()}-${pad(dt.getMonth() + 1)}-${pad(dt.getDate())}T${pad(dt.getHours())}:${pad(dt.getMinutes())}`
      );
    } else {
      setExpiresAt("");
    }
    toast.success(`Template loaded: ${tpl.label}`);
  };

  const previewSpanish = async () => {
    if (!title_en.trim()) return toast.error("Add an English title first");
    setTranslating(true);
    try {
      const r = await api.post("/admin/banners/translate", { title_en, body_en });
      setTitleEs(r.data?.title_es || "");
      setBodyEs(r.data?.body_es || "");
      toast.success("Spanish preview loaded");
    } catch (e) {
      toast.error(`Translate failed: ${e?.response?.data?.detail || e.message}`);
    } finally {
      setTranslating(false);
    }
  };

  const save = async () => {
    if (!title_en.trim()) return toast.error("Title is required");
    setSaving(true);
    try {
      // Convert local datetime back to ISO 8601 UTC
      let exp = null;
      if (expiresAt) {
        try {
          exp = new Date(expiresAt).toISOString();
        } catch {
          /* fall through with null */
        }
      }
      const payload = {
        title_en: title_en.trim(),
        body_en: body_en.trim(),
        title_es: title_es.trim() || null,
        body_es: body_es.trim() || null,
        severity,
        require_ack: requireAck,
        expires_at: exp,
        auto_translate: true,
      };
      if (isEdit) {
        await api.patch(`/admin/banners/${initial.id}`, payload);
        toast.success("Banner updated");
      } else {
        await api.post("/admin/banners", payload);
        toast.success("Banner posted — visible site-wide within 60 seconds");
      }
      onSaved?.();
      onClose?.();
    } catch (e) {
      toast.error(`Save failed: ${e?.response?.data?.detail || e.message}`);
    } finally {
      setSaving(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={(v) => !v && onClose?.()}>
      <DialogContent
        className="max-w-3xl max-h-[92vh] overflow-y-auto"
        data-testid="banner-compose-dialog"
      >
        <DialogHeader>
          <DialogTitle className="font-display text-xl">
            {isEdit ? "Edit Hub Banner" : "Post New Hub Banner"}
          </DialogTitle>
        </DialogHeader>

        {!isEdit && (
          <div className="mb-3">
            <Label className="font-mono text-[10px] uppercase tracking-[0.2em] text-slate-600">
              Quick Templates
            </Label>
            <div className="mt-2 grid grid-cols-2 sm:grid-cols-3 gap-1.5">
              {HUB_BANNER_TEMPLATES.map((tpl) => {
                const Icon = SEVERITY_ICON[tpl.severity] || AlertTriangle;
                const m = SEVERITY_META[tpl.severity];
                return (
                  <button
                    key={tpl.id}
                    type="button"
                    onClick={() => applyTemplate(tpl)}
                    className={`text-left px-2.5 py-2 rounded border-2 text-xs font-bold hover:border-slate-900 transition-colors ${m.cls_chip}`}
                    data-testid={`banner-template-${tpl.id}`}
                  >
                    <div className="flex items-center gap-1.5">
                      <Icon className="w-3.5 h-3.5 shrink-0" />
                      <span className="truncate">{tpl.label}</span>
                    </div>
                  </button>
                );
              })}
            </div>
          </div>
        )}

        <div className="space-y-3">
          <div>
            <Label htmlFor="b-title-en">Title (English) *</Label>
            <Input
              id="b-title-en"
              value={title_en}
              onChange={(e) => setTitleEn(e.target.value)}
              maxLength={200}
              data-testid="banner-title-en"
            />
          </div>
          <div>
            <Label htmlFor="b-body-en">Body (English)</Label>
            <Textarea
              id="b-body-en"
              value={body_en}
              onChange={(e) => setBodyEn(e.target.value)}
              rows={3}
              maxLength={2000}
              data-testid="banner-body-en"
            />
          </div>

          <div className="flex items-center gap-2">
            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={previewSpanish}
              disabled={translating}
              data-testid="banner-translate-btn"
            >
              {translating ? <Loader2 className="w-3.5 h-3.5 animate-spin mr-1.5" /> : <Languages className="w-3.5 h-3.5 mr-1.5" />}
              Preview Spanish
            </Button>
            <span className="text-xs text-slate-500">
              (auto-translates on save if left blank)
            </span>
          </div>

          <div>
            <Label htmlFor="b-title-es">Título (Español)</Label>
            <Input
              id="b-title-es"
              value={title_es}
              onChange={(e) => setTitleEs(e.target.value)}
              maxLength={200}
              data-testid="banner-title-es"
            />
          </div>
          <div>
            <Label htmlFor="b-body-es">Cuerpo (Español)</Label>
            <Textarea
              id="b-body-es"
              value={body_es}
              onChange={(e) => setBodyEs(e.target.value)}
              rows={3}
              maxLength={2000}
              data-testid="banner-body-es"
            />
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <div>
              <Label>Severity</Label>
              <div className="mt-1 grid grid-cols-2 gap-1.5">
                {["info", "advisory", "warning", "critical"].map((s) => {
                  const m = SEVERITY_META[s];
                  return (
                    <button
                      key={s}
                      type="button"
                      onClick={() => setSeverity(s)}
                      className={`px-2 py-1.5 rounded border-2 text-xs font-bold uppercase tracking-wide transition-colors ${
                        severity === s
                          ? m.cls_bar
                          : "bg-white text-slate-700 border-slate-300 hover:border-slate-500"
                      }`}
                      data-testid={`banner-severity-${s}`}
                    >
                      {m.label}
                    </button>
                  );
                })}
              </div>
            </div>
            <div>
              <Label htmlFor="b-expires">Auto-expires (optional)</Label>
              <Input
                id="b-expires"
                type="datetime-local"
                value={expiresAt}
                onChange={(e) => setExpiresAt(e.target.value)}
                data-testid="banner-expires-at"
              />
              {expiresAt && (
                <button
                  type="button"
                  onClick={() => setExpiresAt("")}
                  className="text-[10px] text-slate-500 hover:text-slate-900 mt-1 inline-flex items-center gap-1"
                >
                  <X className="w-3 h-3" /> clear
                </button>
              )}
            </div>
          </div>

          <label className="flex items-start gap-2 p-3 rounded border-2 border-slate-200 bg-slate-50 cursor-pointer hover:bg-slate-100">
            <input
              type="checkbox"
              checked={requireAck}
              onChange={(e) => setRequireAck(e.target.checked)}
              className="mt-0.5"
              data-testid="banner-require-ack"
            />
            <div className="flex-1">
              <div className="font-bold text-sm">Require Acknowledgment</div>
              <div className="text-xs text-slate-600">
                Hard-gates every page until each device clicks "I Acknowledge".
                Use for stand-downs, hurricane warnings, and OSHA visits where
                you need proof the crew saw the message.
              </div>
            </div>
          </label>
        </div>

        <DialogFooter className="mt-4">
          <Button variant="outline" onClick={onClose} disabled={saving}>
            Cancel
          </Button>
          <Button
            onClick={save}
            disabled={saving || !title_en.trim()}
            className="bg-red-700 hover:bg-red-800 text-white"
            data-testid="banner-save-btn"
          >
            {saving && <Loader2 className="w-4 h-4 animate-spin mr-1.5" />}
            {isEdit ? "Save Changes" : "Post Banner"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

export default function AdminBannersPanel() {
  const [banners, setBanners] = useState([]);
  const [loading, setLoading] = useState(true);
  const [composeOpen, setComposeOpen] = useState(false);
  const [editing, setEditing] = useState(null);

  const load = async () => {
    setLoading(true);
    try {
      const r = await api.get("/admin/banners");
      setBanners(r.data?.banners || []);
    } catch (e) {
      toast.error(`Load failed: ${e?.response?.data?.detail || e.message}`);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, []);

  const remove = async (b) => {
    if (!window.confirm(`Delete this banner?\n\n"${b.title_en}"\n\nThis cannot be undone.`)) return;
    try {
      await api.delete(`/admin/banners/${b.id}`);
      toast.success("Banner deleted");
      load();
    } catch (e) {
      toast.error(`Delete failed: ${e?.response?.data?.detail || e.message}`);
    }
  };

  const openCompose = (b = null) => {
    setEditing(b);
    setComposeOpen(true);
  };

  return (
    <div className="border-2 border-amber-300 rounded-md p-5 bg-amber-50" data-testid="admin-banners-panel">
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <Megaphone className="w-5 h-5 text-amber-900" />
          <h2 className="font-display text-lg font-black text-amber-950 uppercase tracking-wide">
            Hub Banner Messages
          </h2>
        </div>
        <Button
          onClick={() => openCompose()}
          className="bg-amber-700 hover:bg-amber-800 text-white"
          size="sm"
          data-testid="banner-new-btn"
        >
          <Plus className="w-4 h-4 mr-1" /> Post New Banner
        </Button>
      </div>

      <p className="text-xs text-amber-900 mb-3">
        Post Heat Advisories, Hurricane Warnings, Stand-Downs, or any custom
        message. Active banners appear site-wide on every page within 60 seconds.
        English is auto-translated to Spanish via Claude.
      </p>

      {loading ? (
        <div className="flex items-center gap-2 text-amber-900 text-sm py-4">
          <Loader2 className="w-4 h-4 animate-spin" /> Loading banners…
        </div>
      ) : banners.length === 0 ? (
        <div className="border-2 border-dashed border-amber-300 rounded p-6 text-center text-sm text-amber-900">
          No banners posted yet. Click "Post New Banner" to broadcast a notice
          to all crews.
        </div>
      ) : (
        <div className="space-y-2">
          {banners.map((b) => {
            const m = SEVERITY_META[b.severity] || SEVERITY_META.advisory;
            const Icon = SEVERITY_ICON[b.severity] || AlertTriangle;
            const expired = b.expires_at && new Date(b.expires_at) < new Date();
            return (
              <div
                key={b.id}
                className={`border-2 rounded p-3 bg-white ${
                  expired ? "border-slate-300 opacity-60" : "border-amber-400"
                }`}
                data-testid={`banner-row-${b.id}`}
              >
                <div className="flex items-start gap-3">
                  <div className={`px-2 py-1 rounded font-mono text-[10px] font-bold uppercase tracking-[0.15em] border-2 ${m.cls_chip} shrink-0 inline-flex items-center gap-1`}>
                    <Icon className="w-3 h-3" />
                    {m.label}
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="font-bold text-sm break-words">{b.title_en}</div>
                    {b.body_en && (
                      <div className="text-xs text-slate-600 mt-0.5 line-clamp-2 break-words">
                        {b.body_en}
                      </div>
                    )}
                    <div className="flex flex-wrap gap-x-3 gap-y-1 mt-1 text-[11px] text-slate-500 font-mono">
                      <span className="inline-flex items-center gap-1">
                        <Eye className="w-3 h-3" /> {b.ack_count || 0} ack
                      </span>
                      <span className="inline-flex items-center gap-1">
                        <EyeOff className="w-3 h-3" /> {b.dismiss_count || 0} dismissed
                      </span>
                      {b.require_ack && (
                        <span className="inline-flex items-center gap-1 text-red-700 font-bold">
                          <CheckCircle2 className="w-3 h-3" /> ACK REQUIRED
                        </span>
                      )}
                      {b.expires_at && (
                        <span className="inline-flex items-center gap-1">
                          <Clock className="w-3 h-3" /> {expired ? "expired" : "expires"} {fmtRelative(b.expires_at)}
                        </span>
                      )}
                    </div>
                  </div>
                  <div className="flex flex-col gap-1 shrink-0">
                    <Button
                      onClick={() => openCompose(b)}
                      variant="outline"
                      size="sm"
                      className="h-7 px-2 text-xs"
                      data-testid={`banner-edit-${b.id}`}
                    >
                      <Edit3 className="w-3.5 h-3.5" />
                    </Button>
                    <Button
                      onClick={() => remove(b)}
                      variant="outline"
                      size="sm"
                      className="h-7 px-2 text-xs text-red-700 hover:bg-red-50 border-red-300"
                      data-testid={`banner-delete-${b.id}`}
                    >
                      <Trash2 className="w-3.5 h-3.5" />
                    </Button>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}

      <ComposeDialog
        open={composeOpen}
        onClose={() => {
          setComposeOpen(false);
          setEditing(null);
        }}
        initial={editing}
        onSaved={load}
      />
    </div>
  );
}
