import React from "react";
import { Link } from "react-router-dom";
import { ArrowLeft, ShieldCheck } from "lucide-react";
import { JuddGroupAttribution } from "@/components/JuddGroupAttribution";

/**
 * /legal/privacy — Privacy Policy.
 *
 * Plain-English coverage of what data the Platform collects and how it is
 * handled. Reinforces ownership: the Platform is operated by The Judd
 * Group LLC; the licensed organization owns its uploaded records.
 */
export default function PrivacyPolicy() {
  return (
    <main className="min-h-screen bg-slate-50">
      <header className="border-b-2 border-slate-200 bg-white">
        <div className="max-w-3xl mx-auto px-4 sm:px-6 py-4 flex items-center gap-3">
          <Link to="/" className="text-slate-600 hover:text-slate-900">
            <ArrowLeft className="w-5 h-5" />
          </Link>
          <ShieldCheck className="w-6 h-6 text-slate-700" />
          <div>
            <div className="font-mono text-[10px] uppercase tracking-[0.25em] text-slate-600 font-bold">
              Legal
            </div>
            <h1 className="font-display text-xl font-black text-slate-900">
              Privacy Policy
            </h1>
          </div>
        </div>
      </header>

      <article
        className="max-w-3xl mx-auto px-4 sm:px-6 py-8 prose prose-slate prose-sm sm:prose-base"
        data-testid="privacy-policy-page"
      >
        <p className="text-xs font-mono uppercase tracking-wide text-slate-500 mb-4">
          Effective Date: January 01, 2026 · Last Updated: January 01, 2026
        </p>

        <section className="mb-6">
          <p>
            This Privacy Policy describes how{" "}
            <strong>The Judd Group LLC</strong> (&ldquo;<strong>we</strong>
            &rdquo;, &ldquo;us&rdquo;) collects, uses, and protects
            information when you use the field operations and safety
            documentation Platform we operate on behalf of your employer or
            licensed organization (e.g., MASCI General Contractors Inc.
            &amp; MASCI Corporation).
          </p>
        </section>

        <h2>1. Who Owns the Platform vs. Your Data</h2>
        <p>
          The Platform itself — code, design, configuration — is owned by{" "}
          <strong>The Judd Group LLC</strong>. The records you upload (daily
          reports, safety inspections, JHAs, photos, etc.) belong to the
          licensed organization (your employer). We host and process those
          records solely on the organization&rsquo;s behalf as a data
          processor.
        </p>

        <h2>2. Information We Collect</h2>
        <ul>
          <li>
            <strong>Account information:</strong> name, email, phone (where
            provided by the licensed organization).
          </li>
          <li>
            <strong>Authentication:</strong> hashed passwords / session
            tokens. We never store passwords in plain text.
          </li>
          <li>
            <strong>Records you submit:</strong> the contents of forms you
            fill out, including project numbers, photos, signatures, and
            free-text notes.
          </li>
          <li>
            <strong>Operational logs:</strong> request times, error traces,
            IP addresses (for fraud and abuse prevention only). Retained no
            longer than 90 days.
          </li>
        </ul>

        <h2>3. How We Use Information</h2>
        <ul>
          <li>To operate the Platform and route records to the correct PMs.</li>
          <li>To send transactional emails (e.g. the assigned PM and
            office&rsquo;s safety mailbox).</li>
          <li>To create the daily / mid-day backups required by the
            organization&rsquo;s recordkeeping practices.</li>
          <li>To diagnose errors and improve reliability.</li>
        </ul>
        <p>
          We <strong>do not</strong> sell your information. We <strong>do
          not</strong> use your records for advertising. We <strong>do not
          </strong> share records with third parties except the
          subprocessors listed below.
        </p>

        <h2>4. Subprocessors</h2>
        <p>
          We use a small number of vetted subprocessors to deliver the
          Platform:
        </p>
        <ul>
          <li>
            <strong>MongoDB Atlas</strong> — primary record storage.
          </li>
          <li>
            <strong>Resend</strong> — outbound email delivery.
          </li>
          <li>
            <strong>Cloud hosting providers</strong> — server infrastructure.
          </li>
        </ul>

        <h2>5. Security</h2>
        <p>
          The Platform uses industry-standard measures: TLS in transit,
          encrypted storage at rest, hashed credentials, role-based access
          control, and twin-window automated backups. No system is
          impenetrable; if you believe an account is compromised, contact
          your administrator immediately.
        </p>

        <h2>6. Retention</h2>
        <p>
          Safety records are retained as long as the licensed organization
          requires for compliance and recordkeeping. On termination of
          service, the organization may export all of its records within
          thirty (30) days; thereafter we may delete them.
        </p>

        <h2>7. Your Rights</h2>
        <p>
          If you are an end user, all data-access, correction, or deletion
          requests should be directed to your administrator at the licensed
          organization. We will work with the organization to fulfill valid
          requests.
        </p>

        <h2>8. Changes to This Policy</h2>
        <p>
          We may update this Privacy Policy from time to time. Material
          changes will be communicated to the licensed organization in
          writing.
        </p>

        <h2>9. Contact</h2>
        <p>
          Questions about this Privacy Policy? Contact{" "}
          <strong>The Judd Group LLC</strong> through your Platform account
          administrator.
        </p>

        <hr className="my-8 border-slate-200" />
        <p className="text-xs text-slate-500">
          See also our{" "}
          <Link to="/legal/terms" className="underline">
            Terms of Service
          </Link>
          .
        </p>
      </article>

      <footer className="border-t border-slate-200 py-6">
        <JuddGroupAttribution variant="global" />
      </footer>
    </main>
  );
}
