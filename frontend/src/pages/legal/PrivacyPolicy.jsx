import React from "react";
import { Link } from "react-router-dom";
import { ArrowLeft, ShieldCheck } from "lucide-react";
import { JuddGroupAttribution } from "@/components/JuddGroupAttribution";

/**
 * /legal/privacy — Privacy Policy.
 *
 * IMPORTANT: MASCI is the data controller / operator of MASCI HUB.
 * The Judd Group LLC is the development contractor only — they built
 * the platform on a work-for-hire basis. They are NOT a parent,
 * subsidiary, partner, or co-owner of MASCI in any form.
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
          Effective Date: January 01, 2026 · Last Updated: May 02, 2026
        </p>

        <section className="mb-6">
          <p>
            This Privacy Policy describes how{" "}
            <strong>MASCI General Contractors Inc.</strong> and{" "}
            <strong>MASCI Corporation</strong> (collectively,{" "}
            <strong>&ldquo;MASCI&rdquo;</strong>, &ldquo;we&rdquo;,
            &ldquo;us&rdquo;) collect, use, and protect information when you
            use the MASCI HUB field operations and safety documentation
            platform (the &ldquo;<strong>Platform</strong>&rdquo;).
          </p>
        </section>

        <h2>1. Who Operates MASCI HUB</h2>
        <p>
          MASCI HUB is owned and operated by MASCI. The Platform was built
          for MASCI on a work-for-hire basis by{" "}
          <strong>The Judd Group LLC</strong>, who acts as MASCI&rsquo;s
          technology development partner only. The Judd Group LLC is not a
          parent, subsidiary, affiliate, or co-owner of MASCI. MASCI is the
          data controller for all information collected through the Platform.
        </p>

        <h2>2. Information We Collect</h2>
        <ul>
          <li>
            <strong>Account information:</strong> name, email, phone (where
            provided to MASCI).
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
          <li>To send transactional emails (e.g. assigned PM and office
            safety mailbox).</li>
          <li>To create the daily / mid-day backups required by MASCI&rsquo;s
            recordkeeping practices.</li>
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
          MASCI uses a small number of vetted subprocessors to deliver the
          Platform:
        </p>
        <ul>
          <li>
            <strong>The Judd Group LLC</strong> — development and technical
            maintenance of the Platform.
          </li>
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
          your MASCI administrator immediately.
        </p>

        <h2>6. Retention</h2>
        <p>
          Safety records are retained as long as MASCI requires for
          compliance and recordkeeping purposes.
        </p>

        <h2>7. Your Rights</h2>
        <p>
          If you are an end user, all data-access, correction, or deletion
          requests should be directed to your MASCI administrator. MASCI
          will respond to valid requests in accordance with applicable law.
        </p>

        <h2>8. Changes to This Policy</h2>
        <p>
          MASCI may update this Privacy Policy from time to time. Material
          changes will be communicated to authorized users.
        </p>

        <h2>9. Contact</h2>
        <p>
          Questions about this Privacy Policy? Contact MASCI through your
          supervisor or the MASCI HUB administrator.
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
