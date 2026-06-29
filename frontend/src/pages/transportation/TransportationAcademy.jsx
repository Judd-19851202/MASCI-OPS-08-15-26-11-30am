/**
 * TRACK 19.01A · Transportation Academy.
 *
 *   • `/transportation-operations/academy`              → 11-module catalog.
 *   • `/transportation-operations/academy/:moduleKey`   → module detail
 *                                                          (video for
 *                                                          published,
 *                                                          professional
 *                                                          "in development"
 *                                                          copy otherwise).
 *
 * Uses the Track 19.01A endpoint
 *   GET /api/admin/transportation/academy/modules
 * which returns ONLY modules tagged curriculum_track="transportation_academy_v1"
 * in curriculum_order ascending. Dispatchers + admins both can read.
 */
import React, { useCallback, useEffect, useMemo, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import {
  Play, Clock, ShieldCheck, ChevronRight, ChevronLeft,
  CheckCircle2, Wrench, GraduationCap, Languages, FileText, Lock,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { PageHeader, txGet, isTxRestricted } from "./_shared";
import { TxOpsRestrictedData } from "@/components/transportation/TxOpsRestricted";

const STATUS_BADGE = {
  published: { label: "Published", className: "bg-emerald-100 text-emerald-800" },
  in_development: { label: "In Development", className: "bg-amber-100 text-amber-800" },
};

function StatusChip({ status, testid }) {
  const cfg = STATUS_BADGE[status] || { label: status, className: "bg-slate-100 text-slate-700" };
  return (
    <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${cfg.className}`} data-testid={testid}>
      {cfg.label}
    </span>
  );
}

function ProgressStrip({ total, published, inDev }) {
  const pct = total > 0 ? Math.round((published / total) * 100) : 0;
  return (
    <div className="bg-slate-900 text-white rounded-lg p-5" data-testid="academy-progress-strip">
      <div className="flex items-center justify-between flex-wrap gap-3">
        <div>
          <div className="text-xs uppercase tracking-[0.2em] text-amber-400 font-mono">
            Transportation Academy
          </div>
          <h2 className="text-xl font-semibold mt-1">{published} of {total} modules available</h2>
          <p className="text-sm text-slate-300 mt-1">{inDev} additional modules in production for future release.</p>
        </div>
        <div className="text-right">
          <div className="text-3xl font-bold tabular-nums" data-testid="academy-progress-pct">{pct}%</div>
          <div className="text-xs text-slate-400 mt-0.5">curriculum available</div>
        </div>
      </div>
      <div className="mt-4 h-2 bg-slate-700 rounded-full overflow-hidden">
        <div
          className="h-full bg-amber-500 transition-all"
          style={{ width: `${pct}%` }}
          data-testid="academy-progress-bar"
        />
      </div>
    </div>
  );
}

function ModuleCard({ module }) {
  const isPublished = module.status === "published";
  return (
    <div
      className="bg-white border border-slate-200 rounded-lg shadow-sm hover:shadow-md transition-shadow overflow-hidden"
      data-testid={`academy-card-${module.key}`}
    >
      <div className="p-5 flex flex-col h-full">
        <div className="flex items-start justify-between gap-2 mb-2">
          <div className="text-xs uppercase tracking-[0.18em] font-mono text-slate-500">
            Module {module.curriculum_order}
          </div>
          <StatusChip status={module.status} testid={`academy-card-${module.key}-status`} />
        </div>
        <h3 className="text-lg font-semibold text-slate-900 leading-snug">
          {module.title}
        </h3>
        <p className="text-sm text-slate-600 mt-2 line-clamp-3">
          {module.description}
        </p>
        <div className="mt-3 flex items-center gap-3 text-xs text-slate-500">
          <span className="inline-flex items-center gap-1"><Clock className="h-3 w-3" />{module.estimated_runtime_minutes} min</span>
          <span className="inline-flex items-center gap-1"><Languages className="h-3 w-3" />English</span>
          <span className="inline-flex items-center gap-1"><FileText className="h-3 w-3" />{(module.topics || []).length} topics</span>
          {module.required ? <Badge variant="outline" className="text-[10px]">Required</Badge> : null}
        </div>
        <div className="mt-4 flex-1" />
        <div className="pt-3 border-t border-slate-100 flex items-center justify-between">
          <Link
            to={`/transportation-operations/academy/${module.key}`}
            data-testid={`academy-card-${module.key}-open`}
          >
            <Button size="sm" variant={isPublished ? "default" : "outline"}>
              {isPublished ? (<><Play className="h-3 w-3 mr-1" /> Watch</>) : (<><Wrench className="h-3 w-3 mr-1" /> View details</>)}
            </Button>
          </Link>
          <ChevronRight className="h-4 w-4 text-slate-400" />
        </div>
      </div>
    </div>
  );
}

export function TransportationAcademy() {
  const [data, setData] = useState({ items: [], total: 0, published: 0, in_development: 0 });
  const [loading, setLoading] = useState(true);
  const [restricted, setRestricted] = useState(false);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const r = await txGet("/admin/transportation/academy/modules");
      if (isTxRestricted(r)) { setRestricted(true); return; }
      setRestricted(false);
      setData(r.data);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { load(); }, [load]);

  return (
    <div data-testid="transportation-academy-page" className="space-y-5">
      <PageHeader
        title="Transportation Academy"
        subtitle="MASCI's permanent learning system for Transportation Operations. Eleven modules covering orientation, safety, qualification, operations, and certification."
      />
      {restricted ? <TxOpsRestrictedData testid="transportation-academy-restricted" /> : (
        <>
          <ProgressStrip total={data.total} published={data.published} inDev={data.in_development} />
          {loading ? (
            <div className="text-sm text-slate-500" data-testid="academy-loading">Loading curriculum…</div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4" data-testid="academy-modules-grid">
              {(data.items || []).map((m) => <ModuleCard key={m.key} module={m} />)}
            </div>
          )}
        </>
      )}
    </div>
  );
}

// ───────────────────── Detail page ─────────────────────

function PublishedVideo({ module }) {
  return (
    <div className="bg-black rounded-lg overflow-hidden shadow-xl" data-testid="academy-published-video">
      <video
        src={module.video_url}
        controls
        playsInline
        className="w-full aspect-video"
        data-testid="academy-video-element"
      />
      <div className="bg-slate-900 text-white px-4 py-3 text-xs flex items-center gap-3">
        <ShieldCheck className="h-4 w-4 text-emerald-400" />
        <span>Module {module.curriculum_order} · {module.title}</span>
        <span className="ml-auto opacity-70">English · {module.estimated_runtime_minutes} min</span>
      </div>
    </div>
  );
}

function InDevelopmentPanel() {
  return (
    <div className="bg-gradient-to-br from-slate-900 via-amber-950 to-slate-900 rounded-lg p-8 text-amber-50 shadow-xl" data-testid="academy-in-development-panel">
      <div className="flex items-start gap-4">
        <Wrench className="h-10 w-10 text-amber-400 flex-shrink-0" />
        <div>
          <h2 className="text-xl font-semibold">Module in production</h2>
          <p className="mt-2 text-sm text-amber-100/90 max-w-2xl leading-relaxed">
            This Transportation Academy module is currently in production and will be published in a future platform release. Continue completing the currently available modules while additional training becomes available.
          </p>
        </div>
      </div>
    </div>
  );
}

function MetaList({ label, items, testid }) {
  if (!items || items.length === 0) return null;
  return (
    <div data-testid={testid}>
      <h3 className="text-xs font-mono uppercase tracking-[0.18em] text-slate-500">{label}</h3>
      <ul className="mt-2 space-y-1 text-sm text-slate-700">
        {items.map((t, i) => (
          <li key={i} className="flex items-start gap-2">
            <CheckCircle2 className="h-3.5 w-3.5 mt-0.5 text-emerald-600 flex-shrink-0" />
            <span>{t}</span>
          </li>
        ))}
      </ul>
    </div>
  );
}

export function TransportationAcademyModule() {
  const { moduleKey } = useParams();
  const navigate = useNavigate();
  const [data, setData] = useState({ items: [] });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    txGet("/admin/transportation/academy/modules").then((r) => {
      setData(r.data || { items: [] });
    }).finally(() => setLoading(false));
  }, []);

  const idx = useMemo(
    () => (data.items || []).findIndex((m) => m.key === moduleKey),
    [data, moduleKey],
  );
  const module = idx >= 0 ? data.items[idx] : null;
  const prev = idx > 0 ? data.items[idx - 1] : null;
  const next = idx >= 0 && idx < (data.items || []).length - 1 ? data.items[idx + 1] : null;

  if (loading) return <div className="text-sm text-slate-500" data-testid="academy-detail-loading">Loading…</div>;
  if (!module) return (
    <div className="text-sm text-slate-600 p-6 bg-slate-50 rounded" data-testid="academy-detail-notfound">
      Module not found.{" "}
      <Link to="/transportation-operations/academy" className="text-blue-700 hover:underline">Return to the Academy.</Link>
    </div>
  );

  const isPublished = module.status === "published";

  return (
    <div className="space-y-5" data-testid={`academy-detail-${module.key}`}>
      <div>
        <Link to="/transportation-operations/academy" className="text-xs text-slate-500 hover:text-slate-900 inline-flex items-center gap-1" data-testid="academy-detail-back">
          <ChevronLeft className="h-3 w-3" /> Transportation Academy
        </Link>
        <div className="flex items-center gap-3 mt-2 flex-wrap">
          <GraduationCap className="h-5 w-5 text-amber-700" />
          <div className="text-xs uppercase tracking-[0.18em] font-mono text-slate-500">Module {module.curriculum_order}</div>
          <StatusChip status={module.status} testid="academy-detail-status" />
          {module.required ? <Badge variant="outline" className="text-[10px]">Required</Badge> : null}
        </div>
        <h1 className="text-2xl md:text-3xl font-semibold text-slate-900 mt-1">{module.title}</h1>
        <p className="text-sm text-slate-600 mt-2 max-w-3xl">{module.description}</p>
      </div>

      {isPublished ? <PublishedVideo module={module} /> : <InDevelopmentPanel />}

      <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
        <MetaList label="Learning Objectives" items={module.learning_objectives} testid="academy-detail-objectives" />
        <MetaList label="Topics Covered" items={module.topics} testid="academy-detail-topics" />
      </div>

      <div className="grid grid-cols-2 gap-3 pt-3 border-t border-slate-200">
        <div>
          {prev ? (
            <button
              type="button"
              onClick={() => navigate(`/transportation-operations/academy/${prev.key}`)}
              className="w-full text-left p-3 border border-slate-200 rounded hover:bg-slate-50"
              data-testid="academy-detail-prev"
            >
              <div className="text-xs text-slate-500">← Previous</div>
              <div className="text-sm font-medium text-slate-900 mt-0.5">Module {prev.curriculum_order}: {prev.title}</div>
            </button>
          ) : <div />}
        </div>
        <div>
          {next ? (
            <button
              type="button"
              onClick={() => navigate(`/transportation-operations/academy/${next.key}`)}
              className="w-full text-right p-3 border border-slate-200 rounded hover:bg-slate-50"
              data-testid="academy-detail-next"
            >
              <div className="text-xs text-slate-500">Next →</div>
              <div className="text-sm font-medium text-slate-900 mt-0.5">Module {next.curriculum_order}: {next.title}</div>
            </button>
          ) : <div />}
        </div>
      </div>

      <div className="text-xs text-slate-400 inline-flex items-center gap-2">
        <Lock className="h-3 w-3" />
        Knowledge check reserved for a future release (passing score {module.passing_score || 80}% · {module.question_count || 5} questions).
      </div>
    </div>
  );
}

export default TransportationAcademy;
