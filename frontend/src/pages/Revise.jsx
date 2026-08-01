/**
 * OMEGA · iter452.5 Tier 1 · /revise/:token page
 *
 * Public · pre-authenticated by the signed JWT in the URL. Renders:
 *   1. The submitter's identity (read-only)
 *   2. A short summary of the original submission
 *   3. A free-form correction box
 *
 * GET  /api/revise/{token} resolves the token + emits the
 *      `revision_link_consumed` audit event.
 * POST /api/revise/{token} persists the correction + emits the
 *      `revision_saved` audit event.
 *
 * No SMS, no push, no PWA install messaging (Tier 2 — frozen).
 */
import { useEffect, useRef, useState } from "react";
import { useParams } from "react-router-dom";
import axios from "axios";
import { CanonicalHeader } from "@/components/CanonicalHeader";

export default function Revise() {
  const { token } = useParams();
  const [loading, setLoading] = useState(true);
  const [resolved, setResolved] = useState(null);
  const [error, setError] = useState("");
  const [note, setNote] = useState("");
  const [changes, setChanges] = useState("");
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);
  const resolvedOnceRef = useRef(false);

  useEffect(() => {
    const base = process.env.REACT_APP_BACKEND_URL;
    if (!base || !token) return;
    if (resolvedOnceRef.current) return;
    resolvedOnceRef.current = true;
    (async () => {
      try {
        const r = await axios.get(
          `${base}/api/revise/${encodeURIComponent(token)}`,
          { validateStatus: () => true }
        );
        if (r.status >= 200 && r.status < 300) {
          setResolved(r.data || {});
        } else {
          setError((r.data && r.data.detail) || "Could not resolve link.");
        }
      } catch (e) {
        setError(String(e?.message || e));
      } finally {
        setLoading(false);
      }
    })();
  }, [token]);

  const submitRevision = async (e) => {
    e.preventDefault();
    if (!token) return;
    setSaving(true);
    setError("");
    try {
      const base = process.env.REACT_APP_BACKEND_URL;
      const body = {
        note,
        changes: changes ? { free_text_revision: changes } : {},
      };
      const r = await axios.post(
        `${base}/api/revise/${encodeURIComponent(token)}`,
        body,
        { validateStatus: () => true }
      );
      if (r.status >= 200 && r.status < 300) setSaved(true);
      else setError((r.data && r.data.detail) || "Could not save the revision.");
    } catch (e) {
      setError(String(e?.message || e));
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="wp17-public-shell min-h-screen" data-testid="revise-page">
      <CanonicalHeader
        portalLabel="MASCI Operations Platform"
        pageLabel="Secure correction workflow"
        accent="red"
        homeTo="/"
        showHomeLink
        showLangToggle
        containerClassName="max-w-4xl"
        testIdPrefix="revise"
      />
      <div className="wp17-public-main py-10">
      <div className="mx-auto max-w-2xl wp17-public-card p-6">
        <div className="mb-4 flex items-center justify-between">
          <h1
            className="text-xl font-semibold text-slate-800"
            data-testid="revise-page-title"
          >
            Submit a Correction
          </h1>
          <span className="text-xs uppercase tracking-wider text-slate-500">
            FSI · v1
          </span>
        </div>

        {loading && (
          <p className="text-sm text-slate-600" data-testid="revise-loading">
            Loading your submission…
          </p>
        )}

        {!loading && error && (
          <div
            className="rounded border border-red-200 bg-red-50 p-3 text-sm text-red-700"
            data-testid="revise-error"
          >
            {error}
          </div>
        )}

        {!loading && resolved && !saved && (
          <>
            <div
              className="mb-4 rounded border border-slate-200 bg-slate-50 p-3 text-sm text-slate-700"
              data-testid="revise-summary"
            >
              <div>
                <strong>Submission:</strong>{" "}
                {resolved.submission?.doc_id || resolved.submission?.id}
              </div>
              <div>
                <strong>Project:</strong>{" "}
                {resolved.submission?.project_name || "—"} (
                {resolved.submission?.project_number || "—"})
              </div>
              <div>
                <strong>Date:</strong> {resolved.submission?.report_date || "—"}
              </div>
              <div>
                <strong>Submitter on file:</strong>{" "}
                {resolved.binding?.submitter_name || "—"}{" "}
                {resolved.binding?.legacy_submitter && (
                  <span className="ml-1 inline-block rounded bg-amber-100 px-1.5 py-0.5 text-xs text-amber-800">
                    legacy
                  </span>
                )}
              </div>
              <div>
                <strong>Email on file:</strong>{" "}
                {resolved.binding?.submitter_email_at_submit || "—"}
              </div>
            </div>

            <form onSubmit={submitRevision} className="space-y-3">
              <div>
                <label
                  htmlFor="revise-changes"
                  className="block text-xs font-medium text-slate-700"
                >
                  What is being corrected?
                </label>
                <textarea
                  id="revise-changes"
                  className="block w-full rounded border border-slate-300 p-2 text-sm"
                  rows={4}
                  value={changes}
                  onChange={(e) => setChanges(e.target.value)}
                  placeholder="Describe the change. Plain text is fine."
                  required
                  data-testid="revise-changes-input"
                />
              </div>
              <div>
                <label
                  htmlFor="revise-note"
                  className="block text-xs font-medium text-slate-700"
                >
                  Optional note to the office
                </label>
                <textarea
                  id="revise-note"
                  className="block w-full rounded border border-slate-300 p-2 text-sm"
                  rows={2}
                  value={note}
                  onChange={(e) => setNote(e.target.value)}
                  data-testid="revise-note-input"
                />
              </div>
              <button
                type="submit"
                disabled={saving || !changes}
                className="rounded bg-blue-600 px-4 py-2 text-sm font-semibold text-white disabled:opacity-60"
                data-testid="revise-submit-btn"
              >
                {saving ? "Saving…" : "Save correction"}
              </button>
            </form>
          </>
        )}

        {saved && (
          <div
            className="rounded border border-green-200 bg-green-50 p-3 text-sm text-green-700"
            data-testid="revise-saved"
          >
            Correction received. The office has been notified.
          </div>
        )}
      </div>
      </div>
    </div>
  );
}
