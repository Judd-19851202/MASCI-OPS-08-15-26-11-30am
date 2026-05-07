import React from "react";
import { Link } from "react-router-dom";
import { ArrowLeft, ShieldCheck } from "lucide-react";

/**
 * /legal/privacy — Privacy Policy.
 *
 * Authoritative text supplied by the customer (MASCI / ForgedOps)
 * on 2026-05-02. Treat the wording inside <article> as legal text — do
 * not edit phrasing without explicit owner approval.
 *
 * Roles:
 *   • ForgedOps LLC = data PROCESSOR (owns and operates the
 *     Platform — code, software, infrastructure, mascidocs.com).
 *   • MASCI = data CONTROLLER (owns all Customer Data submitted
 *     through MASCI HUB).
 *   • The two companies are independent.
 */
export default function PrivacyPolicy() {
  return (
    <main className="min-h-screen bg-slate-50">
      <header className="border-b-2 border-slate-200 bg-white">
        <div className="max-w-3xl mx-auto px-4 sm:px-6 py-4 flex items-center gap-3">
          <Link to="/" className="text-slate-600 hover:text-slate-900" data-testid="privacy-back-link">
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
        <p className="text-xs font-mono uppercase tracking-wide text-slate-500 mb-6">
          Effective Date: January 01, 2026 · Last Updated: January 01, 2026
        </p>

        <p>
          This Privacy Policy describes how information is collected, used,
          and protected when you access the enterprise operational platform
          technology (the &ldquo;<strong>Platform</strong>&rdquo;) owned and
          operated by <strong>ForgedOps LLC</strong> and deployed for the use
          of <strong>MASCI General Contractors Inc.</strong> and{" "}
          <strong>MASCI Corporation</strong> (collectively, &ldquo;
          <strong>MASCI</strong>&rdquo;) as &ldquo;
          <strong>MASCI HUB</strong>&rdquo;.
        </p>

        <hr className="my-6 border-slate-200" />

        <h2>1. Roles &amp; Relationship</h2>
        <p>
          ForgedOps LLC owns and operates the Platform, including its
          source code, software, infrastructure, and platform technology.
        </p>
        <p>For data protection purposes:</p>
        <ul>
          <li>
            <strong>ForgedOps LLC</strong> acts as a{" "}
            <strong>data processor</strong>, storing and processing
            information solely on behalf of MASCI.
          </li>
          <li>
            <strong>MASCI</strong> acts as the <strong>data controller</strong>{" "}
            and determines what data is collected, how it is used, and who
            has access.
          </li>
        </ul>
        <p>MASCI is solely responsible for:</p>
        <ul>
          <li>Authorizing users</li>
          <li>Determining data inputs</li>
          <li>Managing data use within its operations</li>
        </ul>
        <p>
          ForgedOps LLC and MASCI are independent companies. Neither is a
          parent, subsidiary, affiliate, partner, or co-owner of the other.
        </p>
        <p>
          ForgedOps LLC does not own Customer Data and does not use it
          for any purpose other than providing and maintaining the Platform.
        </p>

        <hr className="my-6 border-slate-200" />

        <h2>2. Information We Collect</h2>
        <p>The Platform may process the following categories of information:</p>

        <h3>Account Information</h3>
        <ul>
          <li>Name, email, and phone number (as provided by MASCI for account access)</li>
        </ul>

        <h3>Authentication Data</h3>
        <ul>
          <li>Hashed passwords and session tokens</li>
          <li>Passwords are never stored in plain text</li>
        </ul>

        <h3>Customer Data</h3>
        <ul>
          <li>
            Forms, reports, photos, signatures, notes, and other job-related
            data submitted by users
          </li>
          <li>All Customer Data is owned and controlled by MASCI</li>
        </ul>

        <h3>Operational Logs</h3>
        <ul>
          <li>IP addresses, access timestamps, request logs, and error traces</li>
          <li>Used strictly for system security, fraud prevention, and diagnostics</li>
          <li>
            Retained for no longer than 90 days unless required for security
            or legal purposes
          </li>
        </ul>

        <hr className="my-6 border-slate-200" />

        <h2>3. How Information Is Used</h2>
        <p>Information is used solely to:</p>
        <ul>
          <li>Operate and deliver the Platform</li>
          <li>Route reports and notifications to appropriate MASCI personnel</li>
          <li>
            Send transactional emails (e.g., PM notifications, safety alerts)
          </li>
          <li>Maintain system backups for operational and compliance purposes</li>
          <li>Monitor system performance and resolve technical issues</li>
        </ul>
        <p>
          <strong>ForgedOps LLC does NOT:</strong>
        </p>
        <ul>
          <li>Sell or monetize Customer Data</li>
          <li>Use Customer Data for advertising</li>
          <li>
            Share Customer Data with third parties except as necessary to
            operate the Platform or comply with legal obligations
          </li>
        </ul>

        <hr className="my-6 border-slate-200" />

        <h2>4. Subprocessors</h2>
        <p>
          ForgedOps LLC uses a limited number of vetted third-party
          providers (&ldquo;<strong>Subprocessors</strong>&rdquo;) to operate
          the Platform, including:
        </p>
        <ul>
          <li>
            <strong>MongoDB Atlas</strong> — data storage
          </li>
          <li>
            <strong>Resend</strong> — email delivery
          </li>
          <li>
            <strong>Cloud infrastructure providers</strong> — hosting and
            system operations
          </li>
        </ul>
        <p>
          These subprocessors process data solely to support Platform
          functionality and are contractually obligated to protect data.
        </p>

        <hr className="my-6 border-slate-200" />

        <h2>5. Security</h2>
        <p>The Platform uses industry-standard security measures, including:</p>
        <ul>
          <li>TLS encryption for data in transit</li>
          <li>Encrypted storage for data at rest</li>
          <li>Hashed authentication credentials</li>
          <li>Role-based access controls</li>
          <li>Automated system backups</li>
        </ul>
        <p>
          While reasonable safeguards are in place, no system is completely
          secure. ForgedOps LLC does not guarantee absolute security.
        </p>
        <p>Users must:</p>
        <ul>
          <li>Protect their login credentials</li>
          <li>Report suspected unauthorized access immediately to MASCI</li>
        </ul>

        <hr className="my-6 border-slate-200" />

        <h2>6. Data Retention</h2>
        <p>
          Customer Data is retained according to MASCI&rsquo;s requirements
          for compliance and operational recordkeeping.
        </p>
        <p>
          <strong>ForgedOps LLC:</strong>
        </p>
        <ul>
          <li>Stores data only as long as necessary to provide the Platform</li>
          <li>
            Does not retain data beyond normal operational needs unless
            required by law
          </li>
        </ul>
        <p>MASCI may request:</p>
        <ul>
          <li>Data export</li>
          <li>Data deletion</li>
        </ul>
        <p>
          Requests are handled in accordance with MASCI&rsquo;s agreement with
          ForgedOps LLC.
        </p>

        <hr className="my-6 border-slate-200" />

        <h2>7. Data Responsibility &amp; Use</h2>
        <p>
          <strong>MASCI is solely responsible for:</strong>
        </p>
        <ul>
          <li>The accuracy of Customer Data</li>
          <li>
            Compliance with applicable laws and regulations (including OSHA
            and privacy laws)
          </li>
          <li>Determining how Customer Data is used within its operations</li>
        </ul>
        <p>
          <strong>ForgedOps LLC is not responsible for:</strong>
        </p>
        <ul>
          <li>How MASCI uses Customer Data</li>
          <li>Any decisions made based on data entered into the Platform</li>
          <li>
            Compliance failures resulting from misuse or incorrect data entry
          </li>
        </ul>

        <hr className="my-6 border-slate-200" />

        <h2>8. User Rights</h2>
        <p>If you are an end user of the Platform:</p>
        <ul>
          <li>
            Requests for access, correction, or deletion of data must be
            directed to your MASCI administrator
          </li>
          <li>
            MASCI (as data controller) is responsible for responding to such
            requests in accordance with applicable laws
          </li>
        </ul>
        <p>
          ForgedOps LLC will assist MASCI in fulfilling these requests as
          required.
        </p>

        <hr className="my-6 border-slate-200" />

        <h2>9. Data Transfers</h2>
        <p>
          Data may be processed and stored in the United States or other
          jurisdictions where the Platform&rsquo;s infrastructure or
          subprocessors operate.
        </p>
        <p>
          By using the Platform, you acknowledge that data may be transferred
          and processed outside your local jurisdiction.
        </p>

        <hr className="my-6 border-slate-200" />

        <h2>10. Changes to This Policy</h2>
        <p>ForgedOps LLC may update this Privacy Policy at any time.</p>
        <p>
          Material changes will be communicated to MASCI and, where
          appropriate, to users.
        </p>
        <p>
          Continued use of the Platform after changes take effect constitutes
          acceptance of the updated policy.
        </p>

        <hr className="my-6 border-slate-200" />

        <h2>11. Contact</h2>
        <p>
          For questions regarding Customer Data:
          <br />→ Contact your MASCI administrator
        </p>
        <p>
          For questions regarding the Platform:
          <br />→ Contact ForgedOps LLC
        </p>

        <hr className="my-8 border-slate-200" />
        <p className="text-xs text-slate-500">
          See also our{" "}
          <Link to="/legal/terms" className="underline" data-testid="privacy-terms-link">
            Terms of Service
          </Link>
          .
        </p>
      </article>
    </main>
  );
}
