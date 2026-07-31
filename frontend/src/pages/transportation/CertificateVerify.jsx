/**
 * TRACK 16.08 · MASCI Public Certificate Verification Page.
 *
 * Used by QR codes on issued orientation certificates. Public · no auth.
 * Shows valid / not-valid attestation with audit hash for trust.
 */
import React, { useEffect, useState } from "react";
import { useParams, Link } from "react-router-dom";
import { api } from "@/lib/api";
import { BadgeCheck, ShieldCheck, AlertCircle, Hash } from "lucide-react";
import { MasciLogo } from "@/components/MasciLogo";
import { ForgedOpsAttribution } from "@/components/ForgedOpsAttribution";

export default function CertificateVerify() {
  const { cnum } = useParams();
  const [cert, setCert] = useState(null);
  const [err, setErr] = useState(null);
  useEffect(() => {
    api.get(`/transportation/orientation/certificates/verify/${cnum}`)
      .then(r => setCert(r.data))
      .catch(e => setErr(e.response?.data?.detail || e.message || "Not found"));
  }, [cnum]);

  return (
    <div className="wp17-public-shell min-h-screen">
      <header className="wp17-public-header">
        <div className="max-w-5xl mx-auto px-4 py-4 flex flex-wrap items-center justify-between gap-3 text-white">
          <div className="flex items-center gap-3">
            <MasciLogo variant="mark" size="md" homeLink="/" />
            <div>
              <div className="wp17-kicker text-white/70">Public verification</div>
              <div className="text-sm font-semibold">Transportation orientation certificate lookup</div>
            </div>
          </div>
          <div className="text-xs text-white/70">Operational trust check · white-label ready surface</div>
        </div>
      </header>
      <div className="wp17-public-main flex items-center justify-center py-12">
      <div className="max-w-md w-full wp17-public-card p-6 text-center" data-testid="cert-verify-page">
        {err ? (
          <div data-testid="cert-verify-error">
            <AlertCircle className="h-12 w-12 mx-auto text-red-500" />
            <h2 className="text-xl font-semibold mt-3">Certificate not found</h2>
            <p className="text-sm text-slate-600 mt-1">{err}</p>
            <p className="text-xs text-slate-400 mt-3 font-mono">{cnum}</p>
          </div>
        ) : !cert ? (
          <div data-testid="cert-verify-loading" className="text-slate-500">Verifying…</div>
        ) : (
          <div data-testid="cert-verify-valid">
            <BadgeCheck className="h-14 w-14 mx-auto text-emerald-600" />
            <h2 className="text-2xl font-semibold mt-3 text-slate-900">Certificate verified</h2>
            <p className="text-sm text-slate-600 mt-1">{cert.module_key} · v{cert.module_version} · {cert.language}</p>
            <dl className="text-left text-sm mt-4 space-y-2">
              <Row label="Certificate #" value={cert.certificate_number} mono />
              <Row label="Completed" value={(cert.completed_at || "").slice(0, 19).replace("T", " ")} />
              <Row label="Audit Hash" value={cert.audit_hash} mono small />
            </dl>
            <div className="mt-5 text-xs text-slate-500 flex items-center justify-center gap-1.5">
              <ShieldCheck className="h-3.5 w-3.5" /> Issued by MASCI Operations Platform
            </div>
            <Link to="/" className="text-amber-700 hover:underline text-xs mt-4 inline-block">← MASCI home</Link>
          </div>
        )}
        <div className="mt-6 flex justify-center"><ForgedOpsAttribution variant="login" /></div>
      </div>
      </div>
    </div>
  );
}

function Row({ label, value, mono, small }) {
  return (
    <div className="flex items-start justify-between gap-3 border-b border-slate-100 pb-1.5">
      <dt className="text-xs text-slate-500">{label}</dt>
      <dd className={`text-right text-slate-900 ${mono ? "font-mono" : ""} ${small ? "text-[10px] break-all max-w-[60%]" : ""}`}>{value}</dd>
    </div>
  );
}
