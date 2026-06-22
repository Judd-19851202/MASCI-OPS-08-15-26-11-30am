import React from "react";
import { Link } from "react-router-dom";
import { ArrowLeft, ShieldCheck } from "lucide-react";
import { useBranding } from "@/lib/BrandingProvider";

/**
 * /legal/privacy — Privacy Policy. Track 15.68A tenant-aware: MASCI
 * tenant renders the original iter76/239 text; other tenants render a
 * placeholder asking the operator to publish their own privacy notice.
 */
export default function PrivacyPolicy() {
  const branding = useBranding();
  const isMasci = !branding?.tenant_key || branding.tenant_key === "masci";
  if (!isMasci) {
    return <NonMasciPrivacyPlaceholder branding={branding} />;
  }
  return <MasciPrivacy />;
}

function NonMasciPrivacyPlaceholder({ branding }) {
  const company = branding.company_name || "your company";
  const support = branding.support_email;
  return (
    <main className="min-h-screen bg-slate-50" data-testid="privacy-tenant-placeholder">
      <header className="border-b-2 border-slate-200 bg-white">
        <div className="max-w-3xl mx-auto px-4 sm:px-6 py-4 flex items-center gap-3">
          <Link to="/" className="text-slate-600 hover:text-slate-900">
            <ArrowLeft className="w-5 h-5" />
          </Link>
          <ShieldCheck className="w-5 h-5 text-slate-500" />
          <h1 className="text-lg font-semibold text-slate-900">Privacy Policy</h1>
        </div>
      </header>
      <div className="max-w-3xl mx-auto px-4 sm:px-6 py-12">
        <div className="rounded-lg border-2 border-dashed border-slate-300 bg-white p-8">
          <h2 className="text-xl font-bold text-slate-900 mb-3">
            Privacy Policy pending tenant configuration
          </h2>
          <p className="text-slate-700 leading-relaxed mb-4">
            {company} has not yet published a tenant-specific Privacy Policy.
            {support && (
              <> Contact <span className="font-mono">{support}</span> to request a copy.</>
            )}
          </p>
          <p className="text-slate-500 text-sm leading-relaxed">
            The underlying platform is operated by ForgedOps LLC and any
            personal data processed is subject to the contract between {company}
            (controller) and ForgedOps LLC (processor). Tenant-specific privacy
            terms are published by {company}.
          </p>
        </div>
      </div>
    </main>
  );
}

function MasciPrivacy() {
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
          Effective Date: January 01, 2026 · Last Updated: May 18, 2026
        </p>

        <p>
          This Privacy Policy describes how information is collected, used,
          and protected when you access the enterprise operational platform
          technology (the &ldquo;<strong>Platform</strong>&rdquo;) owned and
          operated by <strong>ForgedOps LLC</strong> and deployed for the use
          of <strong>MASCI General Contractors Inc.</strong> and{" "}
          <strong>MASCI Corporation</strong> (collectively, &ldquo;
          <strong>MASCI</strong>&rdquo;) as the{" "}
          <strong>MASCI Operations Platform</strong>, a customer-branded
          deployment of the underlying ForgedOps&trade; platform technology.
        </p>

        <hr className="my-6 border-slate-200" />

        <h2>1. Roles &amp; Relationship</h2>
        <p>
          ForgedOps LLC owns and operates the Platform, including its
          source code, software, infrastructure, and platform technology.
        </p>
        <p>
          Customer deployments may be customized and branded for operational
          use while remaining part of the ForgedOps platform ecosystem.
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
          <li>Route reports, alerts, and notifications to appropriate MASCI personnel</li>
          <li>
            Send operational notifications, workflow alerts, safety
            notices, maintenance alerts, account notifications, and
            related system communications via PWA / mobile push,
            email, or SMS where applicable
          </li>
          <li>
            Maintain commercially reasonable backup, redundancy, and
            disaster-recovery processes (see Section 5) necessary to
            support Platform functionality and continuity
          </li>
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
          the Platform. The current Subprocessor list is:
        </p>
        <ul>
          <li>
            <strong>MongoDB Atlas</strong> — primary database storage and
            replication.
          </li>
          <li>
            <strong>Cloudflare R2</strong> — redundant object storage,
            photo and signature archival, system backup infrastructure,
            content delivery, and operational resiliency services.
          </li>
          <li>
            <strong>Cloudflare</strong> — DNS, edge caching, TLS
            termination, and DDoS protection for mascidocs.com.
          </li>
          <li>
            <strong>Resend</strong> — transactional email delivery
            (operational notifications, password resets, distribution
            emails, daily report routing).
          </li>
          <li>
            <strong>Anthropic Claude</strong> — supervised AI text
            generation for translation, banner localization, and
            optional AI-assisted drafting features.
          </li>
          <li>
            <strong>OpenAI</strong> — supervised AI text and image
            generation where applicable to the Automated Features.
          </li>
          <li>
            <strong>Google Gemini</strong> — supervised AI text and image
            generation where applicable to the Automated Features.
          </li>
          <li>
            <strong>Twilio</strong> (conditional) — SMS / text-message
            delivery for dispatch, safety, and operational notifications.
            Twilio is engaged only when SMS is provisioned for a
            deployment; where SMS is not provisioned, Twilio receives no
            Platform data.
          </li>
          <li>
            <strong>Cloud infrastructure providers</strong> — compute
            hosting, container orchestration, supervisor services, and
            related system operations.
          </li>
        </ul>
        <p>
          Subprocessors process data solely to support Platform
          functionality and are contractually obligated to protect data.
          The current Subprocessor list may evolve as the Platform
          scales; material changes are communicated to MASCI in
          accordance with the separate services agreement.
        </p>

        <hr className="my-6 border-slate-200" />

        <h2>5. Security, Backup &amp; Operational Resiliency</h2>
        <p>The Platform uses industry-standard security measures, including:</p>
        <ul>
          <li>TLS encryption for data in transit</li>
          <li>Encrypted storage for data at rest</li>
          <li>Hashed authentication credentials (bcrypt or stronger)</li>
          <li>Role-based access controls, scoped per portal (Admin, PM, Shop, HR, Field Leadership)</li>
          <li>Session-token isolation per portal scope</li>
        </ul>
        <p>
          ForgedOps&trade; maintains commercially reasonable backup,
          redundancy, disaster-recovery, and operational-resiliency
          measures designed to support continuity and system recovery,
          including:
        </p>
        <ul>
          <li>Automated nightly archives of every form, photo, and signature.</li>
          <li>Redundant cloud object storage on Cloudflare R2 for photos, signatures, and complete-system archives.</li>
          <li>Periodic recovery testing and integrity checks on archive contents.</li>
          <li>Diagnostic and alert tooling for backup health (heartbeat email + admin dashboard).</li>
        </ul>
        <p>
          While reasonable safeguards are in place, no system is
          completely secure and no backup architecture guarantees
          zero data loss. ForgedOps LLC does not guarantee absolute
          security, perfect uptime, or any specific recovery time
          objective (RTO) or recovery point objective (RPO).
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

        <h2>7. Data Responsibility &amp; Regulatory Compliance</h2>
        <p>
          <strong>MASCI is solely responsible for:</strong>
        </p>
        <ul>
          <li>The accuracy of Customer Data</li>
          <li>
            Compliance with applicable laws and regulations — including
            OSHA, the U.S. Department of Transportation (DOT), the
            Federal Aviation Administration (FAA), the Federal Motor
            Carrier Safety Administration (FMCSA), employment law,
            wage-and-hour law, payroll regulations, and applicable
            privacy regulations (including GDPR, CCPA, and any state
            privacy laws)
          </li>
          <li>Determining how Customer Data is used within its operations</li>
          <li>
            Validating the output of Automated Features (see Section
            7B) before relying on it for any operational, regulatory,
            payroll, safety, or personnel decision
          </li>
        </ul>
        <p>
          <strong>ForgedOps LLC is not responsible for:</strong>
        </p>
        <ul>
          <li>How MASCI uses Customer Data</li>
          <li>Any decisions made based on data entered into the Platform</li>
          <li>
            Compliance failures resulting from misuse, incorrect data
            entry, or reliance on Automated Features without human
            review
          </li>
          <li>
            Demonstrating regulatory compliance on behalf of MASCI —
            use of the Platform does not by itself ensure compliance
            with any law or regulation
          </li>
        </ul>

        <hr className="my-6 border-slate-200" />

        <h2>7A. Notifications &amp; Communications Consent</h2>
        <p>
          By using the Platform, users consent to receive operational
          notifications, workflow alerts, safety notices, maintenance
          alerts, account-related communications, and security
          notifications via PWA / mobile push, email, SMS, or in-app
          messaging.
        </p>
        <p>
          Notifications may be triggered by workflow events, automated
          routing rules, scheduled processes, role-based recipient
          lists, or on-demand actions taken by authorized MASCI
          personnel.
        </p>
        <p>
          Users may opt out of non-essential communications but may
          not opt out of safety, security, or operationally critical
          notifications without losing access to the affected Platform
          features.
        </p>

        <hr className="my-6 border-slate-200" />

        <h2>7B. Automated Processing &amp; AI-Assisted Features</h2>
        <p>
          Certain Platform features may utilize automated processing,
          workflow automation, machine-generated summaries, scheduled
          background jobs, system-generated recommendations,
          predictive operational tooling, or AI-assisted drafting
          (collectively, the &ldquo;<strong>Automated Features</strong>
          &rdquo;).
        </p>
        <p>
          Where AI-assisted features are used, the relevant AI
          subprocessor (Anthropic, OpenAI, or Google) processes only
          the specific input necessary to generate the requested
          output (e.g., banner translation, draft text suggestion).
          AI subprocessors are not granted ongoing access to Customer
          Data, are not used for model training on MASCI data, and
          process inputs solely to return the requested output.
        </p>
        <p>
          Users remain solely responsible for reviewing, validating,
          approving, and acting on any output produced by an Automated
          Feature. Automated outputs do not constitute regulatory
          determinations, legal opinions, engineering certifications,
          medical advice, or safety clearances.
        </p>

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
