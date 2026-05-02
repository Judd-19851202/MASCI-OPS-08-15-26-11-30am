import React from "react";
import { Link } from "react-router-dom";
import { ArrowLeft, ShieldCheck } from "lucide-react";
import { JuddGroupAttribution } from "@/components/JuddGroupAttribution";

/**
 * /legal/privacy — Privacy Policy.
 *
 * RELATIONSHIP CLARIFIED (2026-05-02):
 *   • The Judd Group LLC owns and operates the underlying Platform
 *     (code, software, infrastructure, mascidocs.com domain). They are
 *     the data PROCESSOR.
 *   • MASCI is the customer that uses the Platform. They own all
 *     Customer Data submitted through MASCI HUB and are the data
 *     CONTROLLER.
 *   • The two companies are independent — neither owns the other.
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
            This Privacy Policy describes how information is collected,
            used, and protected when you access the field-operations and
            safety-documentation software platform (the &ldquo;
            <strong>Platform</strong>&rdquo;) operated by{" "}
            <strong>The Judd Group LLC</strong> and delivered to{" "}
            <strong>MASCI General Contractors Inc.</strong> and{" "}
            <strong>MASCI Corporation</strong> (collectively, &ldquo;
            <strong>MASCI</strong>&rdquo;) at <em>mascidocs.com</em> as
            &ldquo;<strong>MASCI HUB</strong>&rdquo;.
          </p>
        </section>

        <h2>1. Roles &amp; Relationship</h2>
        <p>
          The Judd Group LLC owns and operates the Platform — the source
          code, software, infrastructure, and the <em>mascidocs.com</em>{" "}
          domain. In data-protection terms, The Judd Group LLC acts as the{" "}
          <strong>data processor</strong>: storing and processing
          information on MASCI&rsquo;s behalf to deliver the Platform.
        </p>
        <p>
          MASCI is The Judd Group LLC&rsquo;s customer. MASCI is the{" "}
          <strong>data controller</strong> for all records, files, photos,
          and documents submitted through MASCI HUB (&ldquo;
          <strong>Customer Data</strong>&rdquo;). MASCI decides who is
          authorized to use the Platform, what records are submitted, and
          how Customer Data is used in MASCI&rsquo;s business.
        </p>
        <p>
          The Judd Group LLC and MASCI are independent companies — neither
          is a parent, subsidiary, affiliate, partner, or co-owner of the
          other. The Judd Group LLC does <strong>not</strong> own any
          Customer Data and does <strong>not</strong> use it for any
          purpose other than operating the Platform for MASCI.
        </p>

        <h2>2. Information We Collect</h2>
        <ul>
          <li>
            <strong>Account information:</strong> name, email, phone (when
            provided to MASCI for Platform access).
          </li>
          <li>
            <strong>Authentication:</strong> hashed passwords / session
            tokens. Passwords are never stored in plain text.
          </li>
          <li>
            <strong>Customer Data you submit:</strong> the contents of
            forms, photos, signatures, and free-text notes — owned by MASCI.
          </li>
          <li>
            <strong>Operational logs:</strong> request times, error traces,
            IP addresses (for fraud and abuse prevention only). Retained
            no longer than 90 days.
          </li>
        </ul>

        <h2>3. How Information Is Used</h2>
        <ul>
          <li>To operate the Platform and route records to the correct PMs.</li>
          <li>
            To send transactional emails (assigned PM, office safety mailbox).
          </li>
          <li>To create the daily / mid-day backups required for recordkeeping.</li>
          <li>To diagnose errors and improve reliability.</li>
        </ul>
        <p>
          The Judd Group LLC <strong>does not</strong> sell information,{" "}
          <strong>does not</strong> use Customer Data for advertising, and{" "}
          <strong>does not</strong> share Customer Data with third parties
          except the subprocessors listed below or as required by law.
        </p>

        <h2>4. Subprocessors</h2>
        <p>
          To deliver the Platform, The Judd Group LLC uses a small number of
          vetted subprocessors:
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
          your MASCI administrator immediately.
        </p>

        <h2>6. Retention</h2>
        <p>
          Customer Data is retained as long as MASCI requires for compliance
          and recordkeeping. MASCI may request export or deletion at any
          time per its services agreement with The Judd Group LLC.
        </p>

        <h2>7. Your Rights</h2>
        <p>
          If you are an end user, all data-access, correction, or deletion
          requests should be directed to your MASCI administrator. MASCI
          (as data controller) will respond to valid requests in accordance
          with applicable law.
        </p>

        <h2>8. Changes to This Policy</h2>
        <p>
          The Judd Group LLC may update this Privacy Policy from time to
          time. Material changes will be communicated to MASCI and to
          authorized users.
        </p>

        <h2>9. Contact</h2>
        <p>
          Questions about Customer Data → contact your MASCI administrator.
          Questions about the Platform itself → contact The Judd Group LLC.
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
