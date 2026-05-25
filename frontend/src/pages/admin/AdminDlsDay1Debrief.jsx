/**
 * AdminDlsDay1Debrief.jsx · iter416 · Phase 19.1 · Day-1 Live Ops Debrief.
 *
 * Route: /admin/dls/day-1-debrief  (admin token gated)
 *
 * Doctrine
 * --------
 * One tiny, calm, admin-only capture page. Closes the Phase 17/19
 * doctrinal loop: operations runs → debrief filed same-day → surgical
 * pickup follows.
 *
 *   - 12 questions (10 doctrine-approved + 2 anti-creep · #11 #12)
 *   - 2 freeform notes (operational + doctrine observations)
 *   - One submit button → markdown file written to /app/memory/
 *   - NO database storage · NO analytics · NO scoring · NO charts
 *   - NO multi-step wizard · NO progress tracker · NO emoji reactions
 *
 * The page is bilingual (EN ↔ ES) via the standard useT() hook.
 */
import React, { useEffect, useMemo, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { ArrowLeft, ClipboardCheck, Send, FileText } from "lucide-react";
import AdminShell from "@/components/AdminShell";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import { usePageTitle } from "@/lib/usePageTitle";
import { useT } from "@/lib/i18n";
import { getAdminToken } from "@/lib/adminAuth";

const API = process.env.REACT_APP_BACKEND_URL;

// Canonical 12 questions — mirror of backend list.
// Backend is the source of truth via GET /api/admin/dls/day-1-debrief/questions
// but we keep a synced fallback so the page renders even if that GET fails.
const FALLBACK_QUESTIONS = [
  { id: "q1",  label: "Where did dispatch hesitate?" },
  { id: "q2",  label: "What was difficult to find?" },
  { id: "q3",  label: "Did drivers understand shift start?" },
  { id: "q4",  label: "Did drivers understand assignment flow?" },
  { id: "q5",  label: "Was assignment issuance fast enough?" },
  { id: "q6",  label: "Did PM haul visibility help production awareness?" },
  { id: "q7",  label: "Did Shop breakdown continuity make sense?" },
  { id: "q8",  label: "Were any dropdowns confusing?" },
  { id: "q9",  label: "Were any wait states missing or unclear?" },
  { id: "q10", label: "Where did users pause too long or become uncertain?" },
  { id: "q11", label: "What felt unnecessary or overly complicated?" },
  { id: "q12", label: "What should remain simple and untouched?" },
];

export default function AdminDlsDay1Debrief() {
  usePageTitle("Day-1 Live Ops Debrief · Dispatch · MASCI");
  const { t } = useT();
  const navigate = useNavigate();

  const [questions, setQuestions] = useState(FALLBACK_QUESTIONS);
  const [answers, setAnswers] = useState({});
  const [operationalNotes, setOperationalNotes] = useState("");
  const [doctrineObservations, setDoctrineObservations] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState("");

  // Fetch canonical question list on mount (admin source of truth).
  useEffect(() => {
    let cancelled = false;
    const token = getAdminToken();
    if (!token) return;
    fetch(`${API}/api/admin/dls/day-1-debrief/questions`, {
      headers: { "X-Admin-Token": token },
    })
      .then((r) => (r.ok ? r.json() : null))
      .then((data) => {
        if (cancelled || !data?.questions?.length) return;
        setQuestions(data.questions);
      })
      .catch(() => { /* keep fallback */ });
    return () => { cancelled = true; };
  }, []);

  const today = useMemo(() => new Date().toISOString().slice(0, 10), []);

  const updateAnswer = (qid, val) => {
    setAnswers((prev) => ({ ...prev, [qid]: val }));
  };

  const onSubmit = async () => {
    setError("");
    setResult(null);
    setSubmitting(true);
    const token = getAdminToken();
    if (!token) {
      setError(t("Admin sign-in required."));
      setSubmitting(false);
      return;
    }
    try {
      const r = await fetch(`${API}/api/admin/dls/day-1-debrief`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-Admin-Token": token,
        },
        body: JSON.stringify({
          answers,
          operational_notes: operationalNotes,
          doctrine_observations: doctrineObservations,
        }),
      });
      const data = await r.json().catch(() => ({}));
      if (!r.ok || !data?.ok) {
        setError(data?.detail || t("Submission failed."));
      } else {
        setResult(data);
      }
    } catch (e) {
      setError(String(e?.message || e));
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <AdminShell>
      <div className="max-w-3xl mx-auto px-4 sm:px-6 py-6">
        {/* Back link · calm slate */}
        <div className="mb-4">
          <Link
            to="/admin"
            data-testid="day1-back-to-admin"
            className="inline-flex items-center text-xs text-slate-500 hover:text-slate-800"
          >
            <ArrowLeft className="w-3.5 h-3.5 mr-1" /> {t("Back to Admin")}
          </Link>
        </div>

        {/* Section header · calm operational chrome */}
        <div
          data-testid="day1-debrief-header"
          className="bg-white rounded-2xl border border-slate-200 p-5 sm:p-6"
        >
          <div className="flex items-start gap-3">
            <div className="w-9 h-9 rounded-lg bg-slate-100 flex items-center justify-center shrink-0">
              <ClipboardCheck className="w-5 h-5 text-slate-700" />
            </div>
            <div>
              <div className="text-[11px] uppercase tracking-wide text-slate-500 font-bold">
                {t("Day-1 review")}
              </div>
              <h1 className="font-display text-xl sm:text-2xl font-black text-slate-900 leading-tight">
                {t("Day-1 Live Ops Debrief")}
              </h1>
              <p className="text-sm text-slate-600 mt-1 leading-relaxed">
                {t("Capture real operational friction while it is still fresh. Only document repeated hesitation, confusion, downstream continuity problems, or operational slowdowns.")}
              </p>
              <p className="text-xs text-slate-500 mt-2">
                {t("Today")}: <span className="font-bold text-slate-700">{today}</span>
              </p>
            </div>
          </div>
        </div>

        {/* Questions · single-column · calm spacing */}
        <div className="mt-5 space-y-4">
          {questions.map((q, idx) => (
            <div
              key={q.id}
              data-testid={`day1-q-${q.id}`}
              className="bg-white rounded-xl border border-slate-200 p-4"
            >
              <Label
                htmlFor={`day1-q-${q.id}-input`}
                className="block text-sm font-bold text-slate-900"
              >
                <span className="text-slate-400 mr-2">{idx + 1}.</span>
                {t(q.label)}
              </Label>
              <Textarea
                id={`day1-q-${q.id}-input`}
                data-testid={`day1-q-${q.id}-input`}
                rows={2}
                value={answers[q.id] || ""}
                onChange={(e) => updateAnswer(q.id, e.target.value)}
                placeholder={t("Brief operational observation…")}
                className="mt-2 text-sm"
              />
            </div>
          ))}
        </div>

        {/* Notes & doctrine observations · optional */}
        <div className="mt-5 bg-white rounded-xl border border-slate-200 p-4">
          <Label htmlFor="day1-ops-notes" className="block text-sm font-bold text-slate-900">
            {t("Operational notes")}
          </Label>
          <Textarea
            id="day1-ops-notes"
            data-testid="day1-ops-notes"
            rows={2}
            value={operationalNotes}
            onChange={(e) => setOperationalNotes(e.target.value)}
            placeholder={t("Anything else from the field…")}
            className="mt-2 text-sm"
          />
        </div>

        <div className="mt-4 bg-white rounded-xl border border-slate-200 p-4">
          <Label htmlFor="day1-doctrine" className="block text-sm font-bold text-slate-900">
            {t("Doctrine observations")}
          </Label>
          <Textarea
            id="day1-doctrine"
            data-testid="day1-doctrine"
            rows={2}
            value={doctrineObservations}
            onChange={(e) => setDoctrineObservations(e.target.value)}
            placeholder={t("Did doctrine hold? Any restraint pressure points?")}
            className="mt-2 text-sm"
          />
        </div>

        {/* Submit · single calm button */}
        <div className="mt-5 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
          <Button
            onClick={onSubmit}
            disabled={submitting}
            data-testid="day1-submit"
            className="bg-slate-900 hover:bg-slate-800 text-white"
          >
            <Send className="w-4 h-4 mr-2" />
            {submitting ? t("Saving…") : t("Save Day-1 debrief")}
          </Button>
          {error && (
            <span
              data-testid="day1-error"
              className="text-xs text-rose-700"
            >
              {error}
            </span>
          )}
        </div>

        {/* Success card · shows filename written */}
        {result?.ok && (
          <div
            data-testid="day1-success"
            className="mt-4 bg-emerald-50 border border-emerald-200 rounded-xl p-4"
          >
            <div className="flex items-start gap-2">
              <FileText className="w-5 h-5 text-emerald-700 mt-0.5" />
              <div className="text-sm">
                <div className="font-bold text-emerald-900">
                  {t("Debrief saved.")}
                </div>
                <div className="text-emerald-800 mt-1">
                  {t("Written to")}: <code className="text-xs bg-white px-1 py-0.5 rounded border border-emerald-200">{result.path}</code>
                </div>
                <div className="text-xs text-emerald-700 mt-1">
                  {t("Re-submitting same day will overwrite this file with your latest version.")}
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Doctrine reminder · calm slate · bottom */}
        <div
          data-testid="day1-doctrine-reminder"
          className="mt-6 mb-10 px-1 text-xs text-slate-500 leading-relaxed"
        >
          {t("Capture operational hesitation and continuity gaps — not feature wishlists. Build from repeated operational patterns, not isolated requests.")}
        </div>
      </div>
    </AdminShell>
  );
}
