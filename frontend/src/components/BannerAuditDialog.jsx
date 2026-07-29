import React, { useEffect, useState } from "react";
import {
  Clock,
  ShieldCheck,
  EyeOff,
  Edit3,
  Trash2,
  Plus,
  Loader2,
  X,
  Globe,
  Monitor,
  FileText,
  Sheet,
} from "lucide-react";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from "@/components/ui/dialog";
import { api } from "@/lib/api";
import { API } from "@/lib/api";
import { buildScopedPortalAuthHeaders } from "@/lib/authHeaders";
import { toast } from "sonner";
// TRACK 27.03 · Phase 3 · Canonical local-time formatter.
import { formatPlatformTime } from "@/lib/platformTime";

/**
 * BannerAuditDialog — admin-only "Audit Trail" peek for a single
 * banner. Pulls /api/admin/banners/{id}/audit which returns a unified
 * timeline of admin actions (create/update/delete) + every per-device
 * ack and dismiss with timestamp, IP, browser, and page.
 *
 * Used as legal-cover evidence: "we can prove the foreman acked the
 * stand-down at 4:42 PM from the job-site IP before he left." That
 * level of proof would have meant pulling raw Mongo dumps before
 * iter66 — now it's a click.
 *
 * Layout
 * ------
 *  Header strip with banner title + ack/dismiss totals.
 *  Scrollable timeline below, newest first. Each row shows:
 *    icon · kind label · timestamp · "device …abc12" · IP · page · UA
 *  Admin rows (create/update/delete) get a slate icon; ack rows get
 *  green; dismiss rows get amber.
 */
const KIND_META = {
  ack: {
    icon: ShieldCheck,
    label: "Acknowledged",
    cls: "bg-emerald-50 border-emerald-300 text-emerald-900",
    iconCls: "text-emerald-700",
  },
  dismiss: {
    icon: EyeOff,
    label: "Dismissed",
    cls: "bg-amber-50 border-amber-300 text-amber-900",
    iconCls: "text-amber-700",
  },
  admin: {
    icon: Edit3,
    label: "Admin",
    cls: "bg-slate-50 border-slate-300 text-slate-900",
    iconCls: "text-slate-700",
  },
};

const ADMIN_ACTION_ICON = {
  create: Plus,
  update: Edit3,
  delete: Trash2,
};

const fmtAbs = (iso) => {
  if (!iso) return "—";
  return formatPlatformTime(iso);
};

const browserOf = (ua) => {
  if (!ua) return "—";
  if (/iPhone|iPad|iPod/i.test(ua)) return "iOS";
  if (/Android/i.test(ua)) return "Android";
  if (/Edg\//i.test(ua)) return "Edge";
  if (/Chrome\//i.test(ua) && !/Chromium/i.test(ua)) return "Chrome";
  if (/Firefox\//i.test(ua)) return "Firefox";
  if (/Safari\//i.test(ua)) return "Safari";
  return ua.slice(0, 30);
};

/**
 * downloadFile — fetch the URL with the admin token attached, save as a
 * blob, and pop a synthetic <a download> click. We can't use a plain
 * <a href=...> because the browser will strip the Authorization /
 * X-Admin-Token header on navigation; pinning auth via a `?token=`
 * query param works but exposes the token in the referer chain. The
 * blob approach keeps the token in the request headers only.
 */
async function downloadFile(url, filename) {
  try {
    const r = await fetch(url, {
      headers: buildScopedPortalAuthHeaders(["admin"]),
    });
    if (!r.ok) throw new Error(`HTTP ${r.status}`);
    const blob = await r.blob();
    const objUrl = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = objUrl;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    a.remove();
    setTimeout(() => URL.revokeObjectURL(objUrl), 1500);
    toast.success("Saved to your device");
  } catch (e) {
    toast.error(`Download failed: ${e.message}`);
  }
}

export default function BannerAuditDialog({ banner, onClose }) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!banner?.id) return;
    let alive = true;
    (async () => {
      setLoading(true);
      try {
        const r = await api.get(`/admin/banners/${banner.id}/audit`);
        if (!alive) return;
        setData(r.data);
      } catch (e) {
        toast.error(`Audit load failed: ${e?.response?.data?.detail || e.message}`);
      } finally {
        if (alive) setLoading(false);
      }
    })();
    return () => {
      alive = false;
    };
  }, [banner?.id]);

  const rows = data?.audit || [];

  return (
    <Dialog open={!!banner} onOpenChange={(v) => !v && onClose?.()}>
      <DialogContent
        className="max-w-3xl max-h-[88vh] overflow-y-auto"
        data-testid="banner-audit-dialog"
      >
        <DialogHeader>
          <DialogTitle className="font-display text-lg flex items-center gap-2">
            <Clock className="w-5 h-5" />
            Audit Trail
          </DialogTitle>
          <DialogDescription className="text-xs text-slate-600">
            Combined timeline of admin actions plus every per-device
            acknowledgment and dismissal with timestamp, IP, browser,
            and page. Useful as legal-cover proof that field crews saw
            critical notices.
          </DialogDescription>
        </DialogHeader>

        {banner && (
          <div className="flex flex-wrap gap-2 mb-2">
            <button
              type="button"
              onClick={() =>
                downloadFile(
                  `${API}/admin/banners/${banner.id}/audit.pdf`,
                  `MASCI_banner_audit_${(banner.title_en || "banner")
                    .replace(/[^A-Za-z0-9]+/g, "_")
                    .slice(0, 40)}.pdf`
                )
              }
              className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded border-2 border-red-700 bg-red-50 text-red-900 hover:bg-red-100 text-xs font-bold uppercase tracking-wider"
              data-testid="banner-audit-pdf-btn"
            >
              <FileText className="w-3.5 h-3.5" />
              Export PDF
            </button>
            <button
              type="button"
              onClick={() =>
                downloadFile(
                  `${API}/admin/banners/${banner.id}/audit.csv`,
                  `MASCI_banner_audit_${(banner.title_en || "banner")
                    .replace(/[^A-Za-z0-9]+/g, "_")
                    .slice(0, 40)}.csv`
                )
              }
              className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded border-2 border-slate-400 bg-white text-slate-900 hover:bg-slate-50 text-xs font-bold uppercase tracking-wider"
              data-testid="banner-audit-csv-btn"
            >
              <Sheet className="w-3.5 h-3.5" />
              Export CSV
            </button>
          </div>
        )}

        {banner && (
          <div className="rounded border-2 border-slate-200 p-3 bg-slate-50">
            <div className="font-bold text-sm break-words">
              {banner.title_en}
              {data?.banner?.deleted && (
                <span className="ml-2 text-[10px] font-mono uppercase tracking-wider text-red-700 bg-red-100 px-1.5 py-0.5 rounded border border-red-300">
                  Deleted — admin history retained
                </span>
              )}
            </div>
            <div className="flex flex-wrap gap-x-4 gap-y-1 mt-1 text-[11px] font-mono text-slate-600">
              <span>SEVERITY · {banner.severity}</span>
              {banner.require_ack && <span className="text-red-700 font-bold">ACK REQUIRED</span>}
              <span>ACKS · {data?.banner?.ack_count ?? banner.ack_count ?? 0}</span>
              <span>DISMISSALS · {data?.banner?.dismiss_count ?? banner.dismiss_count ?? 0}</span>
            </div>
          </div>
        )}

        {loading ? (
          <div className="flex items-center gap-2 text-slate-600 text-sm py-6 justify-center">
            <Loader2 className="w-4 h-4 animate-spin" /> Loading audit trail…
          </div>
        ) : rows.length === 0 ? (
          <div className="border-2 border-dashed border-slate-300 rounded p-6 text-center text-sm text-slate-500">
            No activity yet. Acknowledgments and admin edits show up here.
          </div>
        ) : (
          <ol className="space-y-1.5" data-testid="banner-audit-list">
            {rows.map((r, i) => {
              const meta = KIND_META[r.kind] || KIND_META.admin;
              let Icon = meta.icon;
              if (r.kind === "admin" && ADMIN_ACTION_ICON[r.action]) {
                Icon = ADMIN_ACTION_ICON[r.action];
              }
              return (
                <li
                  key={i}
                  className={`border-l-4 ${meta.cls} pl-2.5 pr-3 py-1.5 rounded-r flex items-start gap-2`}
                  data-testid={`audit-row-${r.kind}`}
                >
                  <Icon className={`w-4 h-4 mt-0.5 shrink-0 ${meta.iconCls}`} />
                  <div className="flex-1 min-w-0">
                    <div className="flex items-baseline gap-2 flex-wrap">
                      <span className="font-bold text-xs uppercase tracking-wider">
                        {r.kind === "admin" ? `Admin · ${r.action || "edit"}` : meta.label}
                      </span>
                      <span className="font-mono text-[11px] text-slate-600">
                        {fmtAbs(r.ts)}
                      </span>
                    </div>
                    <div className="flex flex-wrap gap-x-3 gap-y-0.5 mt-0.5 text-[11px] font-mono text-slate-700">
                      {r.actor_name && (
                        <span className="font-bold">{r.actor_name}</span>
                      )}
                      {r.device_id && (
                        <span title={r.device_id}>device …{(r.device_id || "").slice(-6)}</span>
                      )}
                      {r.ip && (
                        <span className="inline-flex items-center gap-1">
                          <Globe className="w-3 h-3" /> {r.ip}
                        </span>
                      )}
                      {r.path && <span>page · {r.path}</span>}
                      {r.lang && r.lang !== "en" && <span>lang · {r.lang}</span>}
                      {r.ua && (
                        <span className="inline-flex items-center gap-1" title={r.ua}>
                          <Monitor className="w-3 h-3" /> {browserOf(r.ua)}
                        </span>
                      )}
                      {r.extra?.fields && (
                        <span title={(r.extra.fields || []).join(", ")}>
                          fields · {(r.extra.fields || []).length}
                        </span>
                      )}
                    </div>
                  </div>
                </li>
              );
            })}
          </ol>
        )}

        <div className="flex justify-end mt-2">
          <button
            onClick={onClose}
            className="text-xs font-mono uppercase tracking-wider text-slate-500 hover:text-slate-900 inline-flex items-center gap-1"
            data-testid="banner-audit-close"
          >
            <X className="w-3 h-3" /> close
          </button>
        </div>
      </DialogContent>
    </Dialog>
  );
}
