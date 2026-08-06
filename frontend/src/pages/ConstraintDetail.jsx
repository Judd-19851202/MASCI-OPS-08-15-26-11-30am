// ConstraintDetail.jsx — Phase V-Prelude · Wave 1 · Substrate.
//
// Detail view for an operational constraint. Includes the read-only
// Chronology panel substrate. Calm, text-first.
// Read OPERATIONAL_CONSTRAINT_FOUNDATION.md and
// OPERATIONAL_TIMELINE_FOUNDATION.md before changes.

import React from "react";
import { useParams, useNavigate, Link } from "react-router-dom";
import {
  getConstraint, resolveConstraint, appendChronology, getTimeline,
} from "@/lib/operationalApi";
import { ensureConstraintPortalContext, getConstraintCapabilities } from "@/lib/constraintCapabilities";
import { formatLocalShort } from "@/lib/dateUtils";
import SeverityPill from "@/components/operational/SeverityPill";
import ChronologyPanel from "@/components/operational/ChronologyPanel";

export default function ConstraintDetail() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [portalReady] = React.useState(() => {
    ensureConstraintPortalContext();
    return true;
  });
  const caps = React.useMemo(() => getConstraintCapabilities(), [portalReady]);
  const [doc, setDoc] = React.useState(null);
  const [timeline, setTimeline] = React.useState([]);
  const [err, setErr] = React.useState("");
  const [busy, setBusy] = React.useState(false);
  const [resolveNote, setResolveNote] = React.useState("");
  const [showResolve, setShowResolve] = React.useState(false);
  const [chronologyNote, setChronologyNote] = React.useState("");
  const [chronologyAction, setChronologyAction] = React.useState("note");

  const load = React.useCallback(async () => {
    setErr("");
    try {
      const c = await getConstraint(id);
      setDoc(c);
      try {
        const tl = await getTimeline(c.project_id);
        // Filter timeline to events touching this constraint OR
        // chronology rows for this constraint id.
        const filtered = (tl.items || []).filter((it) => {
          if (it.kind === "operational_constraint" && it.id === id) return true;
          if (
            it.linked_to &&
            it.linked_to.some(
              (l) => l.kind === "operational_constraint" && l.id === id,
            )
          ) return true;
          return false;
        });
        setTimeline(filtered);
      } catch {
        setTimeline([]);
      }
    } catch (e) {
      setErr(e.message || "Could not load constraint");
    }
  }, [id]);

  React.useEffect(() => { load(); }, [load]);

  const onResolve = async () => {
    if (!resolveNote.trim()) {
      setErr("Resolution note required.");
      return;
    }
    setBusy(true);
    try {
      const next = await resolveConstraint(id, resolveNote.trim());
      setDoc(next);
      setShowResolve(false);
      setResolveNote("");
      await load();
    } catch (e) {
      setErr(e.message || "Could not resolve");
    } finally {
      setBusy(false);
    }
  };

  const onChronology = async () => {
    if (!chronologyNote.trim()) {
      setErr("Note required.");
      return;
    }
    setBusy(true);
    try {
      const next = await appendChronology(
        id, chronologyAction.trim() || "note", chronologyNote.trim(),
      );
      setDoc(next);
      setChronologyNote("");
      await load();
    } catch (e) {
      setErr(e.message || "Could not append");
    } finally {
      setBusy(false);
    }
  };

  if (!caps["constraint.view"]) {
    return (
      <div className="max-w-3xl mx-auto p-6 text-slate-700">
        <p className="text-sm">Your role does not include this view.</p>
      </div>
    );
  }
  if (err && !doc) {
    return (
      <div className="max-w-3xl mx-auto p-6">
        <Link to="/constraints" className="text-sm text-slate-600 hover:underline">
          ← All constraints
        </Link>
        <p data-testid="constraint-detail-error" className="text-rose-700 mt-3 text-sm">{err}</p>
      </div>
    );
  }
  if (!doc) {
    return (
      <div data-testid="constraint-detail-loading" className="max-w-3xl mx-auto p-6 text-sm text-slate-500">
        Loading…
      </div>
    );
  }

  const isOpen = doc.status === "open" || doc.status === "monitoring";

  return (
    <div data-testid="constraint-detail-page" className="max-w-3xl mx-auto p-4 sm:p-6 text-slate-800">
      <Link
        to="/constraints"
        data-testid="constraint-back-link"
        className="text-sm text-slate-600 hover:underline inline-block mb-3"
      >
        ← All constraints
      </Link>

      <header className="mb-4">
        <div className="flex items-start justify-between gap-3 flex-wrap">
          <h1
            data-testid="constraint-title"
            className="text-xl sm:text-2xl font-semibold tracking-tight break-words"
          >
            {doc.title}
          </h1>
          <SeverityPill severity={doc.severity} dataTestId="constraint-severity" />
        </div>
        <div className="text-xs text-slate-500 mt-1 flex flex-wrap items-center gap-x-2 gap-y-1">
          {doc.doc_id ? <span data-testid="constraint-doc-id" className="font-mono text-slate-700">{doc.doc_id}</span> : null}
          {doc.doc_id ? <span>·</span> : null}
          <span data-testid="constraint-project_id">{doc.project_id}</span>
          <span>·</span>
          <span>{doc.discipline}</span>
          <span>·</span>
          <span>{doc.kind}</span>
          <span>·</span>
          <span data-testid="constraint-status" className="font-medium">
            {doc.status}
          </span>
          <span>·</span>
          <span>filed {formatLocalShort(doc.created_at)}</span>
          {doc.age_days > 2 && (
            <>
              <span>·</span>
              <span data-testid="constraint-age" className="text-slate-600 font-medium">
                {doc.age_days}d
              </span>
            </>
          )}
        </div>
      </header>

      {doc.owner && (
        <section className="mb-3">
          <div className="text-xs text-slate-500">Responsible party</div>
          <div data-testid="constraint-owner" className="text-sm">{doc.owner}</div>
        </section>
      )}

      {doc.operational_impact && (
        <section className="mb-3">
          <div className="text-xs text-slate-500">Operational impact</div>
          <p data-testid="constraint-operational_impact" className="text-sm whitespace-pre-wrap break-words">
            {doc.operational_impact}
          </p>
        </section>
      )}

      {doc.notes && (
        <section className="mb-4">
          <div className="text-xs text-slate-500">Notes</div>
          <p data-testid="constraint-notes" className="text-sm whitespace-pre-wrap break-words">
            {doc.notes}
          </p>
        </section>
      )}

      {/* Chronology */}
      <section className="mt-6 border-t border-slate-200 pt-4">
        <h2 className="text-sm font-semibold text-slate-700 mb-2">
          Chronology · this constraint
        </h2>
        <ChronologyPanel
          items={[
            ...doc.chronology.map((e) => ({
              kind: "operational_constraint",
              id: doc.id,
              at: e.at,
              title: e.action,
              subtitle: e.note || "",
              relationship: e.action,
              linked_to: [],
            })),
            // Cross-artifact links (photos, reports, etc.) come from
            // the timeline aggregator and reference operational_links.
            ...timeline.filter(
              (it) =>
                !(it.kind === "operational_constraint" && it.id === doc.id),
            ),
          ].sort((a, b) => (a.at < b.at ? 1 : -1))}
          emptyText="No chronology yet."
        />
      </section>

      {caps["constraint.chronology_note"] && isOpen && (
        <section
          data-testid="constraint-chronology-add"
          className="mt-4 border border-slate-200 rounded-md p-3"
        >
          <div className="text-xs font-medium text-slate-600 mb-2">
            Append chronology note
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-[160px_1fr_auto] gap-2 items-start">
            <input
              data-testid="chronology-action"
              value={chronologyAction}
              onChange={(e) => setChronologyAction(e.target.value)}
              placeholder="action (e.g., owner contacted)"
              maxLength={80}
              className="text-sm border border-slate-300 rounded-md px-2 py-1.5"
            />
            <input
              data-testid="chronology-note"
              value={chronologyNote}
              onChange={(e) => setChronologyNote(e.target.value)}
              placeholder="optional note"
              maxLength={500}
              className="text-sm border border-slate-300 rounded-md px-2 py-1.5"
            />
            <button
              type="button"
              onClick={onChronology}
              disabled={busy}
              data-testid="chronology-add-btn"
              className="text-sm font-medium px-3 py-1.5 rounded-md bg-slate-900 text-white hover:bg-slate-800 disabled:opacity-50"
            >
              Add
            </button>
          </div>
        </section>
      )}

      {caps["constraint.resolve"] && isOpen && (
        <section data-testid="constraint-resolve-section" className="mt-4">
          {!showResolve ? (
            <button
              type="button"
              onClick={() => setShowResolve(true)}
              data-testid="constraint-resolve-open"
              className="text-sm font-medium px-3 py-1.5 rounded-md border border-emerald-300 text-emerald-800 hover:bg-emerald-50"
            >
              Mark resolved
            </button>
          ) : (
            <div className="border border-emerald-200 rounded-md p-3 bg-emerald-50/30">
              <div className="text-xs font-medium text-slate-700 mb-1">
                Resolution note (required, ≤500 chars)
              </div>
              <textarea
                data-testid="constraint-resolve-note"
                value={resolveNote}
                onChange={(e) => setResolveNote(e.target.value)}
                rows={2}
                maxLength={500}
                className="block w-full text-sm border border-slate-300 rounded-md px-2 py-1.5"
              />
              <div className="flex gap-2 mt-2">
                <button
                  type="button"
                  onClick={onResolve}
                  disabled={busy}
                  data-testid="constraint-resolve-submit"
                  className="text-sm font-medium px-3 py-1.5 rounded-md bg-emerald-700 text-white hover:bg-emerald-800 disabled:opacity-50"
                >
                  Resolve
                </button>
                <button
                  type="button"
                  onClick={() => setShowResolve(false)}
                  className="text-sm font-medium px-3 py-1.5 rounded-md border border-slate-300 text-slate-700 hover:bg-slate-50"
                >
                  Cancel
                </button>
              </div>
            </div>
          )}
        </section>
      )}

      {err && (
        <div data-testid="constraint-detail-action-error" className="text-sm text-rose-700 mt-3">
          {err}
        </div>
      )}

      <footer className="mt-8 text-xs text-slate-400">
        Filed by {doc.created_by} · {formatLocalShort(doc.created_at)}
        {doc.resolved_at && (
          <> · resolved {formatLocalShort(doc.resolved_at)}</>
        )}
      </footer>
    </div>
  );
}
