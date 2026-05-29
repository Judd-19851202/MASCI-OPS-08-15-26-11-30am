// OdrDone.jsx — Phase V.1 · M0.3 · post-submit confirmation.
//
// Calm. One screen. Two actions: view summary · log next day.

import React from "react";
import { Link, useParams } from "react-router-dom";
import { getOdr } from "@/lib/odrApi";

export default function OdrDone() {
  const { id } = useParams();
  const [odr, setOdr] = React.useState(null);
  const [err, setErr] = React.useState("");
  React.useEffect(() => {
    let live = true;
    getOdr(id).then(d => { if (live) setOdr(d); }).catch(e => { if (live) setErr(e.message); });
    return () => { live = false; };
  }, [id]);

  return (
    <div className="min-h-screen bg-slate-50">
      <div className="max-w-md mx-auto px-4 py-12 text-center" data-testid="odr-done-page">
        <div className="text-5xl">✓</div>
        <h1 className="text-xl font-semibold text-slate-800 mt-3">Submitted</h1>
        {odr ? (
          <>
            <p className="text-sm text-slate-500 mt-2">{odr.doc_id}</p>
            <p className="text-xs text-slate-500 mt-1">
              Submitted at {odr.submitted_at} · 24-hour edit window open
            </p>
          </>
        ) : err ? (
          <p className="text-xs text-rose-700 mt-2">{err}</p>
        ) : (
          <p className="text-xs text-slate-500 mt-2">Loading…</p>
        )}
        <div className="mt-8 space-y-2">
          <Link
            to={`/odr/${encodeURIComponent(id)}`}
            data-testid="odr-done-view"
            className="block w-full py-3 rounded-lg bg-slate-800 text-white"
          >
            View record
          </Link>
          <Link
            to="/odr/new"
            data-testid="odr-done-next"
            className="block w-full py-3 rounded-lg border border-slate-300 text-slate-700"
          >
            Log another
          </Link>
        </div>
      </div>
    </div>
  );
}
