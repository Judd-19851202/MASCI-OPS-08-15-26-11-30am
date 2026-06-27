/**
 * TRACK 16.08 · MASCI External Carrier Invite Portal (public).
 *
 * Carrier opens this from the email invite link. No auth.
 * Three-step flow:
 *   1. Welcome + carrier confirmation
 *   2. Orientation modules (video + quiz, per driver)
 *   3. Acknowledgement + submission
 */
import React, { useEffect, useState, useCallback } from "react";
import { useParams, Link, useSearchParams } from "react-router-dom";
import { api } from "@/lib/api";
import {
  ShieldCheck, GraduationCap, BadgeCheck, AlertCircle,
  Truck, FileText, ChevronRight, CheckCircle2,
} from "lucide-react";
import MasciVideoPlayer from "@/components/transportation/MasciVideoPlayer";

export default function ExternalCarrierInvite() {
  const { token } = useParams();
  const [invite, setInvite] = useState(null);
  const [err, setErr] = useState(null);
  const [step, setStep] = useState(1);

  useEffect(() => {
    api.get(`/transportation/invite/${token}`)
      .then(r => setInvite(r.data))
      .catch(e => setErr(e.response?.data?.detail || e.message || "Invite invalid"));
  }, [token]);

  if (err) return <PortalShell><FullPageError message={err} /></PortalShell>;
  if (!invite) return <PortalShell><div className="text-slate-500">Loading…</div></PortalShell>;

  return (
    <PortalShell>
      <div data-testid="carrier-invite-portal" className="max-w-4xl mx-auto px-4 py-6 space-y-5">
        <header className="text-center" data-testid="carrier-invite-header">
          <ShieldCheck className="h-12 w-12 mx-auto text-amber-700" />
          <h1 className="text-3xl font-semibold text-slate-900 mt-2">Welcome to MASCI</h1>
          <div className="text-sm text-slate-500 mt-1">
            {invite.carrier_legal_name ? `${invite.carrier_legal_name} · ` : ""}
            Carrier Self-Onboarding Portal
          </div>
        </header>

        <Stepper step={step} />

        {step === 1 && <Step1Confirm invite={invite} onNext={() => setStep(2)} />}
        {step === 2 && <Step2Orientation invite={invite} token={token} onNext={() => setStep(3)} />}
        {step === 3 && <Step3Submit invite={invite} token={token} />}

        <footer className="text-center text-xs text-slate-400 mt-6">
          Secure invite expires {invite.expires_at?.slice(0, 10)}. MASCI Operations Platform.
        </footer>
      </div>
    </PortalShell>
  );
}

function PortalShell({ children }) {
  return (
    <div className="min-h-screen bg-gradient-to-b from-slate-50 to-amber-50">
      <div className="bg-slate-900 text-white px-4 py-2 text-xs text-center">
        MASCI Hauler Orientation · Operational compliance only · Not a DOT / FMCSA replacement
      </div>
      {children}
    </div>
  );
}

function FullPageError({ message }) {
  return (
    <div className="max-w-md mx-auto text-center py-20" data-testid="carrier-invite-error">
      <AlertCircle className="h-12 w-12 mx-auto text-red-500" />
      <h2 className="text-xl font-semibold mt-3">Invite unavailable</h2>
      <p className="text-slate-600 mt-2 text-sm">{message}</p>
      <Link to="/" className="text-amber-700 hover:underline text-sm mt-4 inline-block">Return to MASCI</Link>
    </div>
  );
}

function Stepper({ step }) {
  const steps = [
    { n: 1, label: "Confirm" },
    { n: 2, label: "Orientation" },
    { n: 3, label: "Submit" },
  ];
  return (
    <ol className="flex items-center justify-center gap-2 text-xs" data-testid="carrier-invite-stepper">
      {steps.map((s, i) => (
        <React.Fragment key={s.n}>
          <li
            data-testid={`stepper-${s.n}-${step >= s.n ? "done" : "pending"}`}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-full border ${step >= s.n ? "bg-amber-700 text-white border-amber-700" : "bg-white text-slate-500 border-slate-200"}`}
          >
            <span className="font-mono">{s.n}</span> {s.label}
          </li>
          {i < steps.length - 1 ? <ChevronRight className="h-3 w-3 text-slate-300" /> : null}
        </React.Fragment>
      ))}
    </ol>
  );
}

// ────────────────────────────────────────────────────────────────────
function Step1Confirm({ invite, onNext }) {
  return (
    <section className="bg-white rounded-lg border border-slate-200 p-5 shadow-sm" data-testid="step-1-confirm">
      <h2 className="text-xl font-semibold flex items-center gap-2"><Truck className="h-5 w-5 text-amber-700" /> Carrier Information</h2>
      <p className="text-sm text-slate-600 mt-2">
        Please confirm your company information before continuing. The MASCI safety and dispatch teams will receive a notification when each step completes.
      </p>
      <dl className="grid grid-cols-1 sm:grid-cols-2 gap-3 mt-4 text-sm">
        <div>
          <dt className="text-xs text-slate-500">Carrier Legal Name</dt>
          <dd className="font-medium text-slate-900">{invite.carrier_legal_name || "—"}</dd>
        </div>
        <div>
          <dt className="text-xs text-slate-500">Primary Contact</dt>
          <dd className="font-medium text-slate-900">{invite.contact_name || "—"}</dd>
        </div>
      </dl>
      <div className="text-xs text-slate-500 mt-4 bg-amber-50 border border-amber-200 rounded p-3">
        By continuing, you acknowledge that MASCI Transportation operates under the MASCI Hauler Packet rate schedule and that drivers must complete every required orientation module before being dispatchable.
      </div>
      <button
        data-testid="step-1-continue"
        onClick={onNext}
        className="mt-4 inline-flex items-center gap-2 bg-amber-700 hover:bg-amber-800 text-white font-medium px-4 py-2 rounded"
      >
        Continue to orientation <ChevronRight className="h-4 w-4" />
      </button>
    </section>
  );
}

// ────────────────────────────────────────────────────────────────────
function Step2Orientation({ invite, token, onNext }) {
  const [modules, setModules] = useState([]);
  const [active, setActive] = useState(null);
  const [err, setErr] = useState(null);

  useEffect(() => {
    api.get(`/transportation/invite/${token}/orientation/modules`)
      .then(r => setModules(r.data.items || []))
      .catch(e => setErr(e.message || String(e)));
  }, [token]);

  if (err) return <FullPageError message={err} />;

  return (
    <section className="bg-white rounded-lg border border-slate-200 p-5 shadow-sm" data-testid="step-2-orientation">
      <h2 className="text-xl font-semibold flex items-center gap-2">
        <GraduationCap className="h-5 w-5 text-amber-700" /> MASCI Hauler Orientation
      </h2>
      <p className="text-sm text-slate-600 mt-2">
        {modules.length} modules cover every operational expectation. Each driver completes them on their own device. Videos cannot be skipped or fast-forwarded.
      </p>

      {active ? (
        <ActiveModule invite={invite} token={token} mod={active} onBack={() => setActive(null)} />
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 mt-4">
          {modules.map((m) => (
            <button
              key={m.id}
              data-testid={`carrier-portal-module-${m.key}`}
              onClick={() => setActive(m)}
              className="text-left rounded border border-slate-200 hover:border-amber-300 hover:bg-amber-50 p-3 text-sm"
            >
              <div className="font-medium flex items-center gap-2">
                <FileText className="h-4 w-4 text-amber-700" /> {m.title}
              </div>
              <div className="text-xs text-slate-500 mt-1">
                {m.category} · {m.required ? "Required" : "Optional"} · {(m.languages || []).join(" · ")}
              </div>
            </button>
          ))}
        </div>
      )}

      <button
        data-testid="step-2-continue"
        onClick={onNext}
        className="mt-4 inline-flex items-center gap-2 bg-amber-700 hover:bg-amber-800 text-white font-medium px-4 py-2 rounded"
      >
        I've completed the orientation modules
        <ChevronRight className="h-4 w-4" />
      </button>
    </section>
  );
}

function ActiveModule({ invite, token, mod, onBack }) {
  // For demo + smoke purposes we don't have per-driver IDs yet — the
  // real carrier portal flow creates drivers in step 1's expansion. We
  // present a per-module preview so the operator and the testing
  // subagent can both observe the no-skip player behaviour live.
  return (
    <div className="mt-3 border border-slate-200 rounded p-3" data-testid="carrier-portal-active-module">
      <button data-testid="carrier-portal-back" onClick={onBack} className="text-amber-700 text-xs hover:underline mb-2">← All modules</button>
      <div className="font-medium">{mod.title}</div>
      <div className="text-xs text-slate-500 mb-2">{mod.category}</div>
      <div className="text-xs text-amber-700 bg-amber-50 border border-amber-200 rounded p-2 mb-2">
        Real driver-level orientation runs after the carrier confirms drivers in their packet. This preview renders the no-skip video player exactly as the driver will see it on their device.
      </div>
      <MasciVideoPlayer
        token={token}
        assignment={{ id: "preview", position_seconds: 0, watch_seconds: 0,
                      completion_pct: 0, checkpoints_visited: [],
                      language: "en" }}
        module={mod}
      />
    </div>
  );
}

// ────────────────────────────────────────────────────────────────────
function Step3Submit({ invite, token }) {
  const [submitted, setSubmitted] = useState(false);
  const [err, setErr] = useState(null);
  const [signature, setSignature] = useState("");
  const submit = async () => {
    try {
      await api.post(`/transportation/invite/${token}/submit`, {
        printed_name: signature,
        acknowledged_at: new Date().toISOString(),
        user_agent: navigator.userAgent,
        timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
      });
      setSubmitted(true);
    } catch (e) {
      setErr(e.response?.data?.detail || e.message || "Submit failed");
    }
  };
  if (submitted) {
    return (
      <section className="bg-white rounded-lg border border-emerald-200 p-6 shadow-sm text-center" data-testid="step-3-submitted">
        <CheckCircle2 className="h-12 w-12 mx-auto text-emerald-600" />
        <h2 className="text-2xl font-semibold mt-3">Submission received</h2>
        <p className="text-sm text-slate-600 mt-1">
          The MASCI Transportation Compliance Center has been notified. You'll receive an email confirmation when your packet is approved.
        </p>
      </section>
    );
  }
  return (
    <section className="bg-white rounded-lg border border-slate-200 p-5 shadow-sm" data-testid="step-3-submit">
      <h2 className="text-xl font-semibold flex items-center gap-2"><BadgeCheck className="h-5 w-5 text-amber-700" /> Acknowledgement</h2>
      <p className="text-sm text-slate-600 mt-2">
        By typing your printed name below you confirm that every driver on this carrier has watched, understood, and accepted the orientation expectations and that all uploaded documents are accurate.
      </p>
      <label className="block text-xs text-slate-500 mt-4">Printed name</label>
      <input
        data-testid="step-3-printed-name"
        value={signature}
        onChange={(e) => setSignature(e.target.value)}
        placeholder="Your full legal name"
        className="w-full border border-slate-300 rounded px-3 py-2 text-sm"
      />
      <button
        data-testid="step-3-submit"
        onClick={submit}
        disabled={!signature.trim()}
        className="mt-3 bg-amber-700 hover:bg-amber-800 disabled:opacity-50 text-white font-medium px-4 py-2 rounded inline-flex items-center gap-2"
      >
        Submit to MASCI <ChevronRight className="h-4 w-4" />
      </button>
      {err ? <div className="text-xs text-red-600 mt-2">{err}</div> : null}
    </section>
  );
}
