// AdminAssetAdmin.jsx — Track 13.31B Day-2 · Asset Administration spine.
//
// Operator-facing surface for the Asset Administrator role.
// Backed by /api/asset-spine/taxonomy* (Track 13.31B Day-0 backend).
//
//   • Header KPIs — total active, verified, needs review, taxonomy version.
//   • Review queue — every active asset lacking canonical taxonomy.
//     Each row exposes the legacy fields, the suggested mapping, and an
//     operator-selectable class/type pair. "Verify" PATCHes the asset.
//   • Apply legacy crosswalk — dry-run by default; explicit confirm to persist.
//
// Doctrine:
//   • Single source of truth = equipment_master.
//   • No fabricated taxonomy — operators choose, the spine records.
//   • Conservative defaults; honest "needs review" states.

import { useEffect, useState, useCallback, useMemo } from "react";
import { Link } from "react-router-dom";
import {
  Layers, Loader2, RefreshCw, CheckCircle2, AlertTriangle,
  ShieldCheck, Wand2, ListChecks, Tag, ExternalLink, ClipboardList,
  FileText, Download, Camera, Calendar, FileSearch, Plus, ListFilter,
} from "lucide-react";
import AdminShell from "@/components/AdminShell";
import { Button } from "@/components/ui/button";
import { api } from "@/lib/api";
import { toast } from "sonner";
import AddAssetDialog from "@/components/asset/AddAssetDialog";
import RequiredDocsEditor from "@/components/asset/RequiredDocsEditor";

const SOURCE_PILL = {
  legacy_mapped: "bg-emerald-100 text-emerald-900 border-emerald-300",
  manual:        "bg-sky-100 text-sky-900 border-sky-300",
  needs_review:  "bg-amber-100 text-amber-900 border-amber-300",
  motive:        "bg-indigo-100 text-indigo-900 border-indigo-300",
  import:        "bg-slate-100 text-slate-800 border-slate-300",
  system:        "bg-slate-100 text-slate-800 border-slate-300",
};

function StatusPill({ verified, source }) {
  const cls = verified
    ? "bg-emerald-100 text-emerald-900 border-emerald-300"
    : SOURCE_PILL[source] || "bg-amber-100 text-amber-900 border-amber-300";
  const label = verified
    ? `VERIFIED · ${(source || "manual").toUpperCase()}`
    : `NEEDS REVIEW${source && source !== "needs_review" ? ` · ${source.toUpperCase()}` : ""}`;
  return (
    <span
      className={`px-1.5 py-0.5 rounded border font-mono text-[10px] uppercase tracking-[0.15em] font-bold ${cls}`}
      data-testid="asset-admin-status-pill"
    >
      {label}
    </span>
  );
}

function Stat({ label, value, hint, accent = "slate", testid }) {
  const colors = {
    slate:   "text-slate-900 bg-white border-slate-200",
    emerald: "text-emerald-900 bg-emerald-50 border-emerald-200",
    amber:   "text-amber-900 bg-amber-50 border-amber-200",
    red:     "text-red-900 bg-red-50 border-red-200",
    sky:     "text-sky-900 bg-sky-50 border-sky-200",
  }[accent];
  return (
    <div className={`rounded border ${colors} px-4 py-3`} data-testid={testid}>
      <div className="font-mono text-[10px] uppercase tracking-widest opacity-70">{label}</div>
      <div className="text-2xl font-black tabular-nums mt-0.5">{value}</div>
      {hint && <div className="text-xs opacity-70 mt-1">{hint}</div>}
    </div>
  );
}

export default function AdminAssetAdmin() {
  const [taxonomy, setTaxonomy] = useState(null);   // { asset_classes, asset_types_by_class, behaviors, ... }
  const [queue, setQueue] = useState([]);           // review-needed items
  const [counts, setCounts] = useState({ total: null, verified: null, needs_review: null });
  const [loading, setLoading] = useState(true);
  const [err, setErr] = useState(null);
  const [tab, setTab] = useState("queue");          // queue | crosswalk | docs | required-docs | templates
  const [savingId, setSavingId] = useState(null);
  const [showAddAsset, setShowAddAsset] = useState(false);

  const reload = useCallback(async () => {
    setLoading(true);
    setErr(null);
    try {
      const [tax, q, health] = await Promise.all([
        api.get("/asset-spine/taxonomy"),
        api.get("/asset-spine/taxonomy/review-needed?limit=200"),
        api.get("/asset-spine/health"),
      ]);
      setTaxonomy(tax.data);
      setQueue(q.data?.items || []);
      setCounts({
        total: health.data?.active_assets ?? null,
        needs_review: (q.data?.count ?? (q.data?.items || []).length),
      });
    } catch (e) {
      setErr(e?.response?.data?.detail || e?.message || "Failed to load");
    } finally {
      setLoading(false);
    }
  }, []);

  // Initial fetch — inline to satisfy the react-hooks/set-state-in-effect rule.
  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const [tax, q, health] = await Promise.all([
          api.get("/asset-spine/taxonomy"),
          api.get("/asset-spine/taxonomy/review-needed?limit=200"),
          api.get("/asset-spine/health"),
        ]);
        if (cancelled) return;
        setTaxonomy(tax.data);
        setQueue(q.data?.items || []);
        setCounts({
          total: health.data?.active_assets ?? null,
          needs_review: (q.data?.count ?? (q.data?.items || []).length),
        });
      } catch (e) {
        if (cancelled) return;
        setErr(e?.response?.data?.detail || e?.message || "Failed to load");
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => { cancelled = true; };
  }, []);

  return (
    <AdminShell title="Asset Administration" section="equipment">
      <div className="max-w-6xl" data-testid="asset-admin-page">
        {/* Header */}
        <div className="flex items-start justify-between gap-3 mb-5 flex-wrap">
          <div>
            <div className="font-mono text-[11px] uppercase tracking-[0.22em] text-red-700 font-bold mb-1">
              Canonical Taxonomy · Spine v{taxonomy?.version || "1.0.0"}
            </div>
            <h1 className="text-3xl font-black text-slate-900 tracking-tight">
              Asset Administration
            </h1>
            <p className="text-sm text-slate-600 mt-1 max-w-2xl">
              Verify every active asset against the single canonical taxonomy.
              Each correction stamps the master record permanently — no parallel
              maps, no duplicate spines.
            </p>
          </div>
          <div className="flex items-center gap-2">
            <Button
              size="sm"
              onClick={() => setShowAddAsset(true)}
              className="bg-red-700 hover:bg-red-800 text-white"
              data-testid="asset-admin-add-asset"
            >
              <Plus className="w-3.5 h-3.5 mr-1" /> Add Asset
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={reload}
              disabled={loading}
              data-testid="asset-admin-refresh"
            >
              {loading ? <Loader2 className="w-3.5 h-3.5 mr-1 animate-spin" /> : <RefreshCw className="w-3.5 h-3.5 mr-1" />}
              Refresh
            </Button>
          </div>
        </div>

        <AddAssetDialog
          open={showAddAsset}
          onClose={() => setShowAddAsset(false)}
          onCreated={() => { reload(); }}
        />

        {err && (
          <div className="mb-4 px-4 py-3 rounded border-2 border-red-300 bg-red-50 text-sm text-red-900 font-semibold" data-testid="asset-admin-err">
            {err}
          </div>
        )}

        {/* KPIs */}
        <section className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-6">
          <Stat
            label="Active Assets"
            value={counts.total ?? "—"}
            hint="equipment_master · is_active"
            accent="slate"
            testid="aa-stat-total"
          />
          <Stat
            label="Needs Review"
            value={counts.needs_review ?? "—"}
            hint="missing canonical class/type"
            accent={(counts.needs_review ?? 0) > 0 ? "amber" : "emerald"}
            testid="aa-stat-review"
          />
          <Stat
            label="Asset Classes"
            value={taxonomy?.asset_classes?.length ?? "—"}
            hint={`closed set · v${taxonomy?.version || "—"}`}
            accent="sky"
            testid="aa-stat-classes"
          />
          <Stat
            label="Asset Types"
            value={
              taxonomy
                ? Object.values(taxonomy.asset_types_by_class || {})
                    .reduce((acc, t) => acc + t.length, 0)
                : "—"
            }
            hint="behavior matrix derived"
            accent="sky"
            testid="aa-stat-types"
          />
        </section>

        {/* Tabs */}
        <div className="flex items-center gap-1 mb-3 border-b border-slate-200" data-testid="asset-admin-tabs">
          {[
            { key: "queue", label: "Review Queue", icon: ListChecks },
            { key: "crosswalk", label: "Legacy Crosswalk", icon: Wand2 },
            { key: "documents", label: "Documents & Renewals", icon: FileText },
            { key: "required-docs", label: "Documentation Requirements", icon: ListFilter },
            { key: "templates", label: "Missing Templates", icon: ClipboardList },
          ].map(({ key, label, icon: Icon }) => {
            const active = tab === key;
            return (
              <button
                key={key}
                type="button"
                onClick={() => setTab(key)}
                className={`px-3 py-2 text-xs font-mono uppercase tracking-[0.16em] font-bold inline-flex items-center gap-1.5 border-b-2 -mb-px transition ${
                  active
                    ? "border-red-700 text-red-700"
                    : "border-transparent text-slate-500 hover:text-slate-900"
                }`}
                data-testid={`asset-admin-tab-${key}`}
              >
                <Icon className="w-3.5 h-3.5" />
                {label}
              </button>
            );
          })}
        </div>

        {tab === "queue" && (
          <ReviewQueue
            taxonomy={taxonomy}
            items={queue}
            loading={loading}
            savingId={savingId}
            onVerify={async (item, choice) => {
              setSavingId(item.id);
              try {
                await api.patch(`/asset-spine/assets/${item.id}`, {
                  asset_class: choice.asset_class,
                  asset_type:  choice.asset_type,
                  taxonomy_verified: true,
                  taxonomy_source: "manual",
                });
                toast.success(`Verified · ${item.unit_number || item.id.slice(0, 8)}`);
                // Optimistic remove from queue
                setQueue((q) => q.filter((x) => x.id !== item.id));
                setCounts((c) => ({
                  ...c,
                  needs_review: Math.max(0, (c.needs_review ?? 1) - 1),
                }));
              } catch (e) {
                toast.error(e?.response?.data?.detail || "Failed to verify");
              } finally {
                setSavingId(null);
              }
            }}
          />
        )}

        {tab === "crosswalk" && (
          <LegacyCrosswalkPanel onApplied={reload} />
        )}

        {tab === "documents" && (
          <DocumentsDashboard />
        )}

        {tab === "required-docs" && (
          <RequiredDocsEditor />
        )}

        {tab === "templates" && (
          <MissingTemplateBacklogPanel />
        )}
      </div>
    </AdminShell>
  );
}

function ReviewQueue({ taxonomy, items, loading, savingId, onVerify }) {
  if (loading && items.length === 0) {
    return (
      <div className="bg-white border border-slate-200 rounded p-8 text-center text-slate-500" data-testid="aa-queue-loading">
        <Loader2 className="w-5 h-5 animate-spin mx-auto mb-2" />
        Loading review queue…
      </div>
    );
  }
  if (items.length === 0) {
    return (
      <div className="bg-emerald-50 border border-emerald-200 rounded p-8 text-center" data-testid="aa-queue-empty">
        <CheckCircle2 className="w-8 h-8 text-emerald-700 mx-auto mb-2" />
        <div className="font-display text-lg font-black text-emerald-900">All assets verified</div>
        <p className="text-sm text-emerald-800 mt-1">
          Every active record carries a canonical class / type. The spine is clean.
        </p>
      </div>
    );
  }
  return (
    <div className="space-y-3" data-testid="aa-queue">
      {items.map((it) => (
        <ReviewRow
          key={it.id}
          item={it}
          taxonomy={taxonomy}
          busy={savingId === it.id}
          onVerify={(choice) => onVerify(it, choice)}
        />
      ))}
    </div>
  );
}

function ReviewRow({ item, taxonomy, busy, onVerify }) {
  const suggested = item.suggested || {};
  const initialClass = item.current_asset_class || suggested.asset_class || "";
  const initialType  = item.current_asset_type  || suggested.asset_type  || "";
  const [klass, setKlass] = useState(initialClass);
  const [typ, setTyp] = useState(initialType);

  const types = useMemo(() => {
    if (!taxonomy || !klass) return [];
    return taxonomy.asset_types_by_class?.[klass] || [];
  }, [taxonomy, klass]);

  const canVerify = !!klass && !!typ && types.includes(typ);

  return (
    <div
      className="bg-white border border-slate-200 rounded p-4"
      data-testid={`aa-row-${item.id}`}
    >
      <div className="flex items-start justify-between gap-3 flex-wrap">
        <div className="min-w-0 flex-1">
          <div className="flex items-center gap-2 flex-wrap">
            <Tag className="w-3.5 h-3.5 text-slate-500" />
            <span className="font-mono text-[11px] uppercase tracking-[0.18em] text-slate-600 font-bold">
              {item.unit_number || "—"}
            </span>
            <StatusPill
              verified={item.current_taxonomy_verified}
              source={suggested.taxonomy_source}
            />
            <Link
              to={`/admin/assets/${item.id}`}
              className="ml-auto inline-flex items-center gap-1 text-[11px] font-mono uppercase tracking-[0.15em] text-slate-600 hover:text-slate-900"
              data-testid={`aa-row-open-${item.id}`}
            >
              Open profile <ExternalLink className="w-3 h-3" />
            </Link>
          </div>
          <div className="font-display text-base font-black text-slate-900 mt-0.5 truncate">
            {item.display_label || "(unlabeled)"}
          </div>
          <div className="text-xs text-slate-500 mt-0.5 font-mono">
            legacy · category=&quot;{item.legacy_category || "—"}&quot; · preop=&quot;{item.legacy_preop_equipment_type || "—"}&quot; · type=&quot;{item.legacy_type || "—"}&quot;
          </div>
          {suggested.taxonomy_review_reason && (
            <div className="text-xs text-amber-800 mt-1 flex items-start gap-1.5">
              <AlertTriangle className="w-3.5 h-3.5 shrink-0 mt-0.5" />
              <span className="font-mono">{suggested.taxonomy_review_reason}</span>
            </div>
          )}
        </div>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 mt-3">
        <div>
          <label className="font-mono text-[9px] uppercase tracking-[0.18em] text-slate-500 font-bold block mb-1">
            Asset Class
          </label>
          <select
            value={klass}
            onChange={(e) => { setKlass(e.target.value); setTyp(""); }}
            className="w-full text-sm border border-slate-300 rounded px-2 py-1.5 bg-white"
            disabled={busy}
            data-testid={`aa-row-class-${item.id}`}
          >
            <option value="">— select class —</option>
            {(taxonomy?.asset_classes || []).map((c) => (
              <option key={c} value={c}>{c}</option>
            ))}
          </select>
        </div>
        <div>
          <label className="font-mono text-[9px] uppercase tracking-[0.18em] text-slate-500 font-bold block mb-1">
            Asset Type
          </label>
          <select
            value={typ}
            onChange={(e) => setTyp(e.target.value)}
            className="w-full text-sm border border-slate-300 rounded px-2 py-1.5 bg-white"
            disabled={busy || !klass}
            data-testid={`aa-row-type-${item.id}`}
          >
            <option value="">— select type —</option>
            {types.map((t) => (
              <option key={t} value={t}>{t}</option>
            ))}
          </select>
        </div>
        <div className="flex items-end">
          <button
            type="button"
            disabled={!canVerify || busy}
            onClick={() => onVerify({ asset_class: klass, asset_type: typ })}
            className="w-full inline-flex items-center justify-center gap-1.5 px-3 py-1.5 rounded bg-slate-900 text-white text-xs font-mono font-bold uppercase tracking-[0.18em] disabled:opacity-50 hover:bg-black transition"
            data-testid={`aa-row-verify-${item.id}`}
          >
            {busy ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <ShieldCheck className="w-3.5 h-3.5" />}
            Verify & Save
          </button>
        </div>
      </div>

      {(suggested.asset_class || suggested.asset_type) && (
        <div className="text-[11px] text-slate-500 mt-2 font-mono">
          Suggested · <strong className="text-slate-700">{suggested.asset_class || "—"}</strong> / <strong className="text-slate-700">{suggested.asset_type || "—"}</strong>
        </div>
      )}
    </div>
  );
}

function LegacyCrosswalkPanel({ onApplied }) {
  const [preview, setPreview] = useState(null); // { scanned, would_verify, would_need_review }
  const [busy, setBusy] = useState(false);
  const [confirmOpen, setConfirmOpen] = useState(false);

  const runDryRun = useCallback(async () => {
    setBusy(true);
    try {
      const r = await api.post("/asset-spine/taxonomy/apply-legacy-crosswalk?dry_run=true&limit=2000", {});
      setPreview(r.data);
    } catch (e) {
      toast.error(e?.response?.data?.detail || "Dry-run failed");
    } finally {
      setBusy(false);
    }
  }, []);

  const apply = useCallback(async () => {
    setBusy(true);
    try {
      const r = await api.post("/asset-spine/taxonomy/apply-legacy-crosswalk?dry_run=false&limit=2000", {});
      toast.success(`Stamped ${r.data?.would_verify ?? 0} canonical · ${r.data?.would_need_review ?? 0} need review`);
      setConfirmOpen(false);
      setPreview(r.data);
      onApplied?.();
    } catch (e) {
      toast.error(e?.response?.data?.detail || "Apply failed");
    } finally {
      setBusy(false);
    }
  }, [onApplied]);

  return (
    <div className="space-y-4" data-testid="aa-crosswalk">
      <div className="bg-white border border-slate-200 rounded p-5">
        <div className="flex items-start gap-3">
          <Layers className="w-5 h-5 text-slate-700 shrink-0 mt-0.5" />
          <div className="flex-1">
            <h3 className="font-display text-lg font-black text-slate-900">Legacy crosswalk</h3>
            <p className="text-sm text-slate-600 mt-1 max-w-2xl">
              Walks every asset in <code className="text-xs px-1 bg-slate-100 rounded">equipment_master</code>,
              maps legacy <span className="font-mono">category</span> / <span className="font-mono">preop_equipment_type</span> / <span className="font-mono">type</span> to canonical
              <span className="font-mono"> asset_class</span> + <span className="font-mono">asset_type</span> using the spine crosswalk, and
              stamps <span className="font-mono">taxonomy_verified=true</span> when sources agree. Conflicts stay in the review queue.
            </p>
          </div>
        </div>
        <div className="flex flex-wrap gap-2 mt-4">
          <button
            type="button"
            onClick={runDryRun}
            disabled={busy}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded border border-slate-300 bg-white hover:bg-slate-50 text-xs font-mono font-bold uppercase tracking-[0.18em] text-slate-900 disabled:opacity-50"
            data-testid="aa-crosswalk-dryrun"
          >
            {busy ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Wand2 className="w-3.5 h-3.5" />}
            Run dry-run
          </button>
          <button
            type="button"
            disabled={busy || !preview}
            onClick={() => setConfirmOpen(true)}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded bg-red-700 hover:bg-red-800 text-white text-xs font-mono font-bold uppercase tracking-[0.18em] disabled:opacity-50"
            data-testid="aa-crosswalk-apply"
          >
            <ShieldCheck className="w-3.5 h-3.5" />
            Stamp canonical
          </button>
        </div>
      </div>

      {preview && (
        <div className="bg-white border border-slate-200 rounded p-5" data-testid="aa-crosswalk-preview">
          <div className="font-mono text-[10px] uppercase tracking-[0.2em] text-slate-600 font-bold">
            {preview.dry_run ? "Dry-run preview" : "Last apply result"}
          </div>
          <div className="grid grid-cols-3 gap-4 mt-2">
            <div>
              <div className="font-mono text-[9px] uppercase tracking-[0.18em] text-slate-500 font-bold">Scanned</div>
              <div className="text-2xl font-black text-slate-900 tabular-nums">{preview.scanned}</div>
            </div>
            <div>
              <div className="font-mono text-[9px] uppercase tracking-[0.18em] text-emerald-700 font-bold">Would verify</div>
              <div className="text-2xl font-black text-emerald-700 tabular-nums">{preview.would_verify}</div>
            </div>
            <div>
              <div className="font-mono text-[9px] uppercase tracking-[0.18em] text-amber-700 font-bold">Needs review</div>
              <div className="text-2xl font-black text-amber-700 tabular-nums">{preview.would_need_review}</div>
            </div>
          </div>
        </div>
      )}

      {confirmOpen && (
        <div className="fixed inset-0 bg-black/40 z-50 flex items-center justify-center p-4" data-testid="aa-crosswalk-confirm">
          <div className="bg-white rounded shadow-xl max-w-md w-full p-5">
            <h3 className="font-display text-lg font-black text-slate-900">Stamp canonical taxonomy?</h3>
            <p className="text-sm text-slate-600 mt-2">
              This persists canonical <span className="font-mono">asset_class</span> / <span className="font-mono">asset_type</span> on
              every cleanly-mapped record. Conflicts remain in the review queue.
            </p>
            <div className="flex justify-end gap-2 mt-4">
              <button
                type="button"
                onClick={() => setConfirmOpen(false)}
                className="px-3 py-1.5 rounded border border-slate-300 text-xs font-mono font-bold uppercase tracking-[0.18em] text-slate-700"
                data-testid="aa-crosswalk-cancel"
              >
                Cancel
              </button>
              <button
                type="button"
                disabled={busy}
                onClick={apply}
                className="px-3 py-1.5 rounded bg-red-700 hover:bg-red-800 text-white text-xs font-mono font-bold uppercase tracking-[0.18em] disabled:opacity-50"
                data-testid="aa-crosswalk-confirm-apply"
              >
                {busy ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : "Stamp"}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

// ────────────────────────────────────────────────────────────
// Track 13.31B-D5.3 · Missing-Template Backlog panel
// Reads `/api/asset-spine/inspection-templates/missing-backlog`
// and shows the Asset Administrator which canonical asset_types
// have active rows but no template in the registry yet.
// ────────────────────────────────────────────────────────────
function MissingTemplateBacklogPanel() {
  const [state, setState] = useState({ loading: true, scanned: 0, items: [], err: null });

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const r = await api.get("/asset-spine/inspection-templates/missing-backlog");
        if (cancelled) return;
        setState({ loading: false, scanned: r.data?.scanned || 0, items: r.data?.items || [], err: null });
      } catch (e) {
        if (cancelled) return;
        setState({ loading: false, scanned: 0, items: [], err: e?.response?.data?.detail || "Failed to load" });
      }
    })();
    return () => { cancelled = true; };
  }, []);

  if (state.loading) {
    return (
      <div className="bg-white border border-slate-200 rounded p-8 text-center text-slate-500" data-testid="aa-templates-loading">
        <Loader2 className="w-5 h-5 animate-spin mx-auto mb-2" />
        Loading missing-template backlog…
      </div>
    );
  }
  if (state.err) {
    return (
      <div className="px-4 py-3 rounded border-2 border-red-300 bg-red-50 text-sm text-red-900 font-semibold" data-testid="aa-templates-err">
        {state.err}
      </div>
    );
  }
  if (state.items.length === 0) {
    return (
      <div className="bg-emerald-50 border border-emerald-200 rounded p-8 text-center" data-testid="aa-templates-empty">
        <CheckCircle2 className="w-8 h-8 text-emerald-700 mx-auto mb-2" />
        <div className="font-display text-lg font-black text-emerald-900">Every active asset type has a canonical inspection template</div>
        <p className="text-sm text-emerald-800 mt-1">
          Scanned {state.scanned} active assets · zero missing templates.
        </p>
      </div>
    );
  }
  return (
    <div className="space-y-3" data-testid="aa-templates">
      <div className="text-xs font-mono uppercase tracking-[0.16em] text-slate-600 font-bold">
        Scanned {state.scanned} active assets · {state.items.length} canonical type{state.items.length === 1 ? "" : "s"} missing a template
      </div>
      {state.items.map((it) => (
        <div key={it.asset_type} className="bg-white border border-slate-200 rounded p-4 flex items-center justify-between gap-3" data-testid={`aa-templates-row-${it.asset_type}`}>
          <div>
            <div className="font-mono text-[10px] uppercase tracking-[0.18em] text-slate-600 font-bold">
              {it.asset_class || "—"}
            </div>
            <div className="font-display text-base font-black text-slate-900">{it.asset_type}</div>
            <div className="text-xs text-slate-500 mt-0.5">
              {it.verified_count}/{it.count} verified · template not built yet
            </div>
          </div>
          <div className="text-3xl font-black text-amber-700 tabular-nums">{it.count}</div>
        </div>
      ))}
    </div>
  );
}

// ─── Track 13.31B-D3+D4 · Documents & Renewals dashboard ───────────────────

function DocumentsDashboard() {
  const [loading, setLoading] = useState(true);
  const [err, setErr] = useState(null);
  const [missing, setMissing] = useState(null);
  const [renewals, setRenewals] = useState(null);
  const [recent, setRecent] = useState([]);

  const reload = useCallback(async () => {
    setLoading(true);
    setErr(null);
    try {
      const [m, r, u] = await Promise.all([
        api.get("/asset-spine/dashboard/missing-documents"),
        api.get("/asset-spine/dashboard/renewals?bucket=all"),
        api.get("/asset-spine/dashboard/recent-uploads?limit=12"),
      ]);
      setMissing(m.data);
      setRenewals(r.data);
      setRecent(u.data.items || []);
    } catch (e) {
      setErr(e?.response?.data?.detail || "Unable to load Documents dashboard.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { reload(); }, [reload]);

  const downloadCsv = useCallback(async (path, filename) => {
    try {
      const r = await api.get(path, { responseType: "blob" });
      const url = URL.createObjectURL(r.data);
      const a = document.createElement("a");
      a.href = url;
      a.download = filename;
      a.click();
      URL.revokeObjectURL(url);
    } catch {
      toast.error("Export failed. Try again.");
    }
  }, []);

  if (loading) {
    return (
      <div className="p-8 text-center text-slate-500" data-testid="aa-docs-loading">
        <Loader2 className="w-5 h-5 animate-spin mx-auto" />
      </div>
    );
  }
  if (err) {
    return <div className="bg-red-50 border-2 border-red-200 rounded p-3 text-red-900">{err}</div>;
  }

  return (
    <div className="space-y-4" data-testid="aa-documents-dashboard">
      {/* Renewals cards */}
      <section>
        <div className="flex items-center justify-between mb-2">
          <h3 className="font-mono text-xs uppercase tracking-[0.18em] text-slate-700 font-bold">
            Renewal Status
          </h3>
          <Button size="sm" variant="outline"
            onClick={() => downloadCsv("/asset-spine/exports/renewals.csv", "MASCI_Asset_Renewals.csv")}
            data-testid="aa-docs-export-renewals">
            <Download className="w-3.5 h-3.5 mr-1" /> Export Renewals CSV
          </Button>
        </div>
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
          <RenewalCard label="Expired" count={renewals?.counters?.expired ?? 0}
            accent="red" testid="aa-renewal-expired" />
          <RenewalCard label="Within 30 Days" count={renewals?.counters?.["30"] ?? 0}
            accent="amber" testid="aa-renewal-30" />
          <RenewalCard label="Within 60 Days" count={renewals?.counters?.["60"] ?? 0}
            accent="sky" testid="aa-renewal-60" />
          <RenewalCard label="Within 90 Days" count={renewals?.counters?.["90"] ?? 0}
            accent="emerald" testid="aa-renewal-90" />
        </div>
        {(renewals?.items || []).length > 0 && (
          <div className="mt-3 bg-white border border-slate-200 rounded divide-y divide-slate-100"
            data-testid="aa-renewal-list">
            {(renewals.items || []).slice(0, 8).map((r) => (
              <div key={r.attachment_id} className="px-3 py-2 flex items-center gap-2 text-sm"
                data-testid={`aa-renewal-row-${r.attachment_id}`}>
                <Calendar className="w-3.5 h-3.5 text-slate-500" />
                <div className="flex-1 min-w-0">
                  <div className="font-bold text-slate-900 truncate">
                    {r.unit_number} · {r.document_label}
                  </div>
                  <div className="text-xs text-slate-500">{r.asset_type || "—"}</div>
                </div>
                <div className="font-mono text-[10px] uppercase tracking-[0.14em] text-slate-700">
                  {r.expiration_date}{r.days_remaining !== null ? ` · ${r.days_remaining}d` : ""}
                </div>
                <Link to={`/admin/assets/${r.asset_id}?tab=documents`}
                  className="text-xs text-red-700 hover:underline font-bold ml-2"
                  data-testid={`aa-renewal-open-${r.attachment_id}`}>
                  Open
                </Link>
              </div>
            ))}
          </div>
        )}
      </section>

      {/* Missing documents */}
      <section>
        <div className="flex items-center justify-between mb-2">
          <h3 className="font-mono text-xs uppercase tracking-[0.18em] text-slate-700 font-bold">
            Documentation Required
          </h3>
          <Button size="sm" variant="outline"
            onClick={() => downloadCsv("/asset-spine/exports/missing-documents.csv", "MASCI_Missing_Documents.csv")}
            data-testid="aa-docs-export-missing">
            <Download className="w-3.5 h-3.5 mr-1" /> Export Missing CSV
          </Button>
        </div>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-2">
          {(missing?.per_document_type || []).slice(0, 9).map((m) => (
            <div key={m.document_type}
              className="bg-white border border-slate-200 rounded p-3 flex items-center justify-between"
              data-testid={`aa-missing-card-${m.document_type}`}>
              <div className="font-bold text-slate-900 text-sm">{m.label}</div>
              <div className="text-2xl font-black text-amber-700 tabular-nums">{m.count}</div>
            </div>
          ))}
          {(missing?.per_document_type || []).length === 0 && (
            <div className="bg-emerald-50 border border-emerald-200 rounded p-3 text-emerald-900 col-span-full"
              data-testid="aa-missing-empty">
              All required documents on file for verified assets.
            </div>
          )}
        </div>
        {(missing?.assets || []).length > 0 && (
          <div className="mt-3 bg-white border border-slate-200 rounded divide-y divide-slate-100"
            data-testid="aa-missing-list">
            {(missing.assets || []).slice(0, 8).map((a) => (
              <div key={a.asset_id} className="px-3 py-2 flex items-center gap-2 text-sm"
                data-testid={`aa-missing-row-${a.asset_id}`}>
                <FileSearch className="w-3.5 h-3.5 text-slate-500" />
                <div className="flex-1 min-w-0">
                  <div className="font-bold text-slate-900 truncate">
                    {a.unit_number} · {a.asset_type || "—"}
                  </div>
                  <div className="text-xs text-slate-500 truncate">
                    {a.missing_documents.join(" · ")}
                  </div>
                </div>
                <div className="font-mono text-[10px] uppercase tracking-[0.14em] text-amber-800 font-bold">
                  {a.missing_count} pending
                </div>
                <Link to={`/admin/assets/${a.asset_id}?tab=documents`}
                  className="text-xs text-red-700 hover:underline font-bold ml-2"
                  data-testid={`aa-missing-open-${a.asset_id}`}>
                  Open
                </Link>
              </div>
            ))}
          </div>
        )}
      </section>

      {/* Recent uploads */}
      <section>
        <div className="flex items-center justify-between mb-2">
          <h3 className="font-mono text-xs uppercase tracking-[0.18em] text-slate-700 font-bold">
            Recently Uploaded
          </h3>
          <Button size="sm" variant="outline"
            onClick={() => downloadCsv("/asset-spine/exports/assets.csv", "MASCI_Asset_Inventory.csv")}
            data-testid="aa-docs-export-inventory">
            <Download className="w-3.5 h-3.5 mr-1" /> Export Inventory CSV
          </Button>
        </div>
        {recent.length === 0 ? (
          <div className="bg-white border border-slate-200 rounded p-6 text-center text-slate-500" data-testid="aa-recent-empty">
            No recent uploads.
          </div>
        ) : (
          <div className="bg-white border border-slate-200 rounded divide-y divide-slate-100" data-testid="aa-recent-list">
            {recent.map((r) => (
              <div key={r.id} className="px-3 py-2 flex items-center gap-2 text-sm"
                data-testid={`aa-recent-row-${r.id}`}>
                <FileText className="w-3.5 h-3.5 text-slate-500" />
                <div className="flex-1 min-w-0">
                  <div className="font-bold text-slate-900 truncate">
                    {r.unit_number} · {r.document_label}
                  </div>
                  <div className="text-xs text-slate-500 truncate">
                    {r.filename || "—"} · {r.uploaded_at?.slice(0, 10)} · {r.uploaded_by}
                  </div>
                </div>
                <Link to={`/admin/assets/${r.asset_id}?tab=documents`}
                  className="text-xs text-red-700 hover:underline font-bold"
                  data-testid={`aa-recent-open-${r.id}`}>
                  Open
                </Link>
              </div>
            ))}
          </div>
        )}
      </section>
    </div>
  );
}

function RenewalCard({ label, count, accent, testid }) {
  const accents = {
    red: "bg-red-50 border-red-200 text-red-900",
    amber: "bg-amber-50 border-amber-200 text-amber-900",
    sky: "bg-sky-50 border-sky-200 text-sky-900",
    emerald: "bg-emerald-50 border-emerald-200 text-emerald-900",
  };
  return (
    <div
      data-testid={testid}
      className={`rounded border-2 p-3 ${accents[accent] || accents.sky}`}
    >
      <div className="font-mono text-[10px] uppercase tracking-[0.16em] font-bold">{label}</div>
      <div className="text-3xl font-black tabular-nums">{count}</div>
    </div>
  );
}


