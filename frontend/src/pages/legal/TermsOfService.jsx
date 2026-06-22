import React from "react";
import { Link } from "react-router-dom";
import { ArrowLeft, Scale } from "lucide-react";
import { useBranding } from "@/lib/BrandingProvider";

/**
 * /legal/terms — Terms of Service.
 *
 * Track 15.68A — tenant-aware. For the MASCI tenant the existing
 * iter239 legal text renders unchanged. For any other tenant
 * (Customer #2 etc.) we render a placeholder asking the tenant
 * operator to supply their own terms — the only legitimate path,
 * since legal text is a contract between the licensing customer and
 * ForgedOps LLC, not boilerplate we can autogenerate.
 */
export default function TermsOfService() {
  const branding = useBranding();
  const isMasci = !branding?.tenant_key || branding.tenant_key === "masci";
  if (!isMasci) {
    return <NonMasciLegalPlaceholder branding={branding} kind="Terms of Service" />;
  }
  return <MasciTerms />;
}

function NonMasciLegalPlaceholder({ branding, kind }) {
  const company = branding.company_name || "your company";
  const support = branding.support_email;
  return (
    <main className="min-h-screen bg-slate-50" data-testid="legal-tenant-placeholder">
      <header className="border-b-2 border-slate-200 bg-white">
        <div className="max-w-3xl mx-auto px-4 sm:px-6 py-4 flex items-center gap-3">
          <Link to="/" className="text-slate-600 hover:text-slate-900">
            <ArrowLeft className="w-5 h-5" />
          </Link>
          <Scale className="w-5 h-5 text-slate-500" />
          <h1 className="text-lg font-semibold text-slate-900">{kind}</h1>
        </div>
      </header>
      <div className="max-w-3xl mx-auto px-4 sm:px-6 py-12">
        <div className="rounded-lg border-2 border-dashed border-slate-300 bg-white p-8">
          <h2 className="text-xl font-bold text-slate-900 mb-3">
            {kind} pending tenant configuration
          </h2>
          <p className="text-slate-700 leading-relaxed mb-4">
            {company} has not yet published a tenant-specific {kind.toLowerCase()}.
            {support && (
              <> Contact <span className="font-mono">{support}</span> to request a copy.</>
            )}
          </p>
          <p className="text-slate-500 text-sm leading-relaxed">
            The underlying platform is provided by ForgedOps LLC. Use of the
            platform is governed by the contract between {company} and ForgedOps
            LLC, supplemented by any {kind.toLowerCase()} {company} chooses to
            publish here.
          </p>
        </div>
      </div>
    </main>
  );
}

function MasciTerms() {
  return (
    <main className="min-h-screen bg-slate-50">
      <header className="border-b-2 border-slate-200 bg-white">
        <div className="max-w-3xl mx-auto px-4 sm:px-6 py-4 flex items-center gap-3">
          <Link to="/" className="text-slate-600 hover:text-slate-900" data-testid="terms-back-link">
            <ArrowLeft className="w-5 h-5" />
          </Link>
          <Scale className="w-6 h-6 text-slate-700" />
          <div>
            <div className="font-mono text-[10px] uppercase tracking-[0.25em] text-slate-600 font-bold">
              Legal
            </div>
            <h1 className="font-display text-xl font-black text-slate-900">
              Terms of Service
            </h1>
          </div>
        </div>
      </header>

      <article
        className="max-w-3xl mx-auto px-4 sm:px-6 py-8 prose prose-slate prose-sm sm:prose-base"
        data-testid="terms-of-service-page"
      >
        <p className="text-xs font-mono uppercase tracking-wide text-slate-500 mb-6">
          Effective Date: January 01, 2026 · Last Updated: May 18, 2026
        </p>

        <p>
          These Terms of Service (&ldquo;<strong>Terms</strong>&rdquo;) govern
          your access to and use of the enterprise operational platform
          technology (the &ldquo;<strong>Platform</strong>&rdquo;) owned and
          operated by <strong>ForgedOps LLC</strong> (&ldquo;
          <strong>Provider</strong>&rdquo;, &ldquo;we&rdquo;, &ldquo;us&rdquo;).
          The Platform is deployed for the use of{" "}
          <strong>MASCI General Contractors Inc.</strong> and{" "}
          <strong>MASCI Corporation</strong> (collectively, &ldquo;
          <strong>MASCI</strong>&rdquo;) as the{" "}
          <strong>MASCI Operations Platform</strong>, a customer-branded
          deployment of the underlying ForgedOps&trade; platform technology.
        </p>
        <p>
          By accessing or using the Platform, you (&ldquo;
          <strong>User</strong>&rdquo;) agree to these Terms.
        </p>

        <hr className="my-6 border-slate-200" />

        <h2>1. Relationship of the Parties</h2>
        <p>
          ForgedOps LLC and MASCI are independent companies. Neither is a
          parent, subsidiary, affiliate, partner, agent, or co-owner of the
          other. ForgedOps LLC is the platform technology owner and operator;
          MASCI is the deployed-for organization.
        </p>

        <hr className="my-6 border-slate-200" />

        <h2>2. Ownership of the Platform</h2>
        <p>
          ForgedOps LLC owns and retains all right, title, and interest
          in the Platform, including all source code, designs, databases,
          software, documentation, configurations, infrastructure, proprietary
          methods, workflows, and system designs (collectively, the &ldquo;
          <strong>Platform IP</strong>&rdquo;).
        </p>
        <p>
          Nothing in these Terms transfers any ownership of the Platform IP to
          MASCI or to any User. The white-label deployment of the Platform as
          the MASCI Operations Platform reflects customer-branded presentation
          only and does not transfer any underlying Platform IP, source code,
          architecture, or operational methodology to MASCI.
        </p>
        <p>
          Customer Data submitted by MASCI through the Platform remains the
          exclusive property of MASCI as set forth in Section 3 below. The
          separation between Platform IP (owned by ForgedOps LLC) and Customer
          Data (owned by MASCI) is intentional and material to these Terms.
        </p>
        <p>
          MASCI&rsquo;s use of the Platform is limited to the rights expressly
          granted in MASCI&rsquo;s separate written services agreement with
          ForgedOps LLC.
        </p>

        <hr className="my-6 border-slate-200" />

        <h2>2A. Trademarks, Branding &amp; Trade Dress</h2>
        <p>
          ForgedOps&trade;, the ForgedOps logo, the MASCI Operations Platform
          name, and related platform names, logos, workflows, interfaces,
          screen layouts, branding elements, color systems, and operational
          system designs (collectively, the &ldquo;
          <strong>Marks &amp; Trade Dress</strong>&rdquo;) are the proprietary
          trademarks, service marks, trade dress, or other intellectual
          property of ForgedOps LLC, whether registered or unregistered.
        </p>
        <p>
          MASCI is granted a non-exclusive, non-transferable, revocable right
          to display the &ldquo;MASCI Operations Platform&rdquo; deployment
          name and accompanying &ldquo;Powered by ForgedOps&trade;&rdquo;
          attribution within MASCI&rsquo;s internal operations during the term
          of MASCI&rsquo;s services agreement. All other uses (including
          marketing, public-facing materials, press, recruiting, or
          third-party communications) require ForgedOps LLC&rsquo;s prior
          written consent.
        </p>
        <p>
          Consistent with standard enterprise software terms, Users agree not
          to reproduce, reverse-engineer, decompile, benchmark for the purpose
          of building a competing product, or use the Platform to develop a
          substantially similar service. This clause is intended to align
          with industry-standard enterprise SaaS protections and is not
          intended to restrict ordinary internal evaluation, troubleshooting,
          or operational use by MASCI.
        </p>
        <p>
          Users agree not to remove, alter, obscure, or replicate any
          ForgedOps&trade; mark, the &ldquo;Powered by ForgedOps&trade;&rdquo;
          attribution, footers, copyright notices, or attribution language
          appearing in the Platform, its exports, generated PDFs, or printed
          materials.
        </p>

        <hr className="my-6 border-slate-200" />

        <h2>3. Ownership of Customer Data</h2>
        <p>
          All records, files, photos, signatures, documents, and other
          information that MASCI or its users submit through the Platform
          (&ldquo;<strong>Customer Data</strong>&rdquo;) belong exclusively to
          MASCI.
        </p>
        <p>
          ForgedOps LLC stores and processes Customer Data solely to
          provide the Platform and related services.
        </p>
        <p>
          ForgedOps LLC does not claim ownership of Customer Data and
          will not sell, share, or use it for advertising purposes.
        </p>
        <p>
          MASCI may request export of its Customer Data in a standard format.
          ForgedOps LLC will provide reasonable assistance but is not
          responsible for long-term storage, backup, or retention beyond
          normal system operations.
        </p>

        <hr className="my-6 border-slate-200" />

        <h2>4. License to Use</h2>
        <p>
          Subject to these Terms, ForgedOps LLC grants MASCI&rsquo;s
          authorized employees, contractors, project managers, foremen, shop
          personnel, and approved clients a limited, revocable, non-exclusive,
          non-transferable, non-sublicensable license to access and use the
          Platform solely for legitimate MASCI business operations.
        </p>
        <p>
          Use of the Platform is strictly limited to MASCI General Contractors
          Inc. and MASCI Corporation as a single legal entity.
        </p>
        <p>
          Use by any affiliate, subsidiary, joint venture, partner company, or
          third party requires a separate written agreement with ForgedOps LLC.
        </p>
        <p>This license does not grant any right to:</p>
        <ol>
          <li>
            copy, modify, decompile, reverse-engineer, or create derivative
            works of the Platform;
          </li>
          <li>
            resell, sublicense, lease, distribute, or otherwise commercially
            exploit the Platform;
          </li>
          <li>provide services to third parties using the Platform;</li>
          <li>represent the Platform as MASCI&rsquo;s own product;</li>
          <li>
            remove, alter, or obscure any attribution, copyright, or vendor
            notice; or
          </li>
          <li>
            use the Platform outside the scope of MASCI&rsquo;s internal
            business operations.
          </li>
        </ol>

        <hr className="my-6 border-slate-200" />

        <h2>5. Acceptable Use</h2>
        <p>Users agree not to:</p>
        <ol>
          <li>violate any applicable law or regulation;</li>
          <li>infringe any third-party rights;</li>
          <li>upload or transmit malicious code;</li>
          <li>
            interfere with or disrupt the Platform&rsquo;s functionality,
            performance, or security;
          </li>
          <li>
            attempt unauthorized access to any system, account, or data;
          </li>
          <li>share login credentials outside of authorized personnel.</li>
        </ol>

        <hr className="my-6 border-slate-200" />

        <h2>6. Confidentiality</h2>
        <p>
          The Platform contains MASCI&rsquo;s internal business information,
          safety procedures, employee data, financial records, and proprietary
          workflows.
        </p>
        <p>
          Users agree to maintain strict confidentiality of all non-public
          information accessed through the Platform and to use such
          information solely for legitimate MASCI business purposes.
        </p>

        <hr className="my-6 border-slate-200" />

        <h2>7. Platform Availability, Backup &amp; Operational Resiliency</h2>
        <p>
          Access to the Platform is dependent on systems, infrastructure, and
          services controlled by ForgedOps LLC.
        </p>
        <p>
          ForgedOps&trade; maintains commercially reasonable backup,
          redundancy, disaster-recovery, and operational-resiliency measures
          designed to support continuity and system recovery. These measures
          include — without limitation — automated nightly archives,
          redundant cloud object storage (including Cloudflare R2 backup and
          redundancy services), encrypted at-rest storage, periodic recovery
          testing, and infrastructure-level fail-over capabilities at the
          discretion of ForgedOps LLC.
        </p>
        <p>
          ForgedOps LLC reserves the right to modify, suspend, or
          discontinue any portion of the Platform at its sole discretion.
        </p>
        <p>
          ForgedOps LLC does not guarantee uninterrupted access, perfect
          uptime, perfect data recovery, zero data loss, or availability
          during force-majeure or third-party outage events. Backup and
          disaster-recovery capabilities are commercially reasonable
          operational measures, not warranties of any specific recovery time
          objective (RTO) or recovery point objective (RPO).
        </p>
        <p>
          Support, maintenance, and updates may be provided at the
          discretion of ForgedOps LLC or under a separate written agreement.
        </p>

        <hr className="my-6 border-slate-200" />

        <h2>7A. Notifications &amp; Operational Communications</h2>
        <p>
          By using the Platform, MASCI authorizes ForgedOps&trade; to
          deliver — and Users consent to receive — operational
          notifications, workflow alerts, safety notices, maintenance
          alerts, account notifications, security-related communications,
          PWA / mobile push notifications, email alerts, SMS alerts, and
          related system communications reasonably necessary to operate the
          Platform.
        </p>
        <p>
          Notifications may be triggered by workflow events, automated
          routing rules, scheduled processes, role-based recipient lists, or
          on-demand actions taken by authorized MASCI personnel.
        </p>
        <p>
          Users may opt out of non-essential marketing communications but
          may not opt out of safety, security, or operationally critical
          notifications without losing access to the affected Platform
          features.
        </p>

        <hr className="my-6 border-slate-200" />

        <h2>7A. SMS &amp; Text-Message Communications</h2>
        <p>
          Where the Platform is configured to deliver SMS / text-message
          notifications, by providing a mobile number — directly or via
          MASCI&rsquo;s administrative provisioning — the recipient
          consents to receive operational text messages from the Platform
          related to dispatch, safety, scheduling, account security,
          and similar workflow events.
        </p>
        <p>
          Message frequency varies based on operational activity.
          <strong> Message and data rates may apply</strong> as charged by
          the recipient&rsquo;s wireless carrier; ForgedOps&trade;, MASCI,
          and their respective subprocessors are not responsible for any
          such carrier charges.
        </p>
        <p>
          Recipients may opt out of non-critical text messages by replying
          <strong> STOP</strong> to any Platform text message, or by
          contacting MASCI&rsquo;s administrator. Recipients may reply
          <strong> HELP</strong> for assistance. Opting out of safety,
          security, or operationally critical SMS may result in loss of
          access to affected Platform features as set forth in Section 7.
          Wireless carriers are not liable for delayed or undelivered
          messages.
        </p>

        <hr className="my-6 border-slate-200" />

        <h2>7B. Automated Processing &amp; AI-Assisted Features</h2>
        <p>
          Certain Platform features may utilize automated processing,
          workflow automation, machine-generated summaries, scheduled
          background jobs, system-generated recommendations, predictive
          operational tooling, or AI-assisted drafting (collectively, the
          &ldquo;<strong>Automated Features</strong>&rdquo;). The Automated
          Features are intended to assist — not replace — human review,
          decision-making, or signature authority.
        </p>
        <p>
          <strong>Output from Automated Features is advisory only and may
          contain errors, omissions, or outdated information.</strong> Users
          remain solely responsible for reviewing, validating, approving,
          and acting on any output produced by an Automated Feature.
          Human review and human approval are required before relying on
          any Automated Feature output for an operational, financial,
          regulatory, safety, payroll, or personnel decision.
        </p>
        <p>
          <strong>No output from any Automated Feature constitutes legal
          advice, engineering approval, regulatory determination, payroll
          decision, medical advice, safety certification, or any other
          professional opinion or licensed determination.</strong> Users
          must obtain qualified human review from the appropriate licensed
          professional before acting on any Automated Feature output in a
          context that requires such determination.
        </p>
        <p>
          ForgedOps&trade; may add, remove, or modify the Automated Features
          at its discretion. Where third-party AI subprocessors are used,
          they are disclosed in the Privacy Policy.
        </p>

        <hr className="my-6 border-slate-200" />

        <h2>8. No Warranty</h2>
        <p className="uppercase">
          The Platform is provided &ldquo;as is&rdquo; and &ldquo;as
          available&rdquo; without warranties of any kind, express or implied,
          including but not limited to warranties of merchantability, fitness
          for a particular purpose, non-infringement, or uninterrupted
          operation.
        </p>
        <p>
          The Platform is a tool to support — not replace — MASCI&rsquo;s
          safety programs, supervisors, and competent personnel.
        </p>
        <p>
          Use of the Platform does not by itself ensure compliance with
          OSHA, the U.S. Department of Transportation (DOT), the Federal
          Aviation Administration (FAA), the Federal Motor Carrier Safety
          Administration (FMCSA), employment laws, wage-and-hour laws,
          payroll regulations, privacy regulations (including the GDPR,
          CCPA, and any applicable state privacy laws), or any other
          regulatory requirement.
        </p>
        <p>
          MASCI remains solely responsible for operational and regulatory
          compliance, the accuracy of inputs into the Platform, the
          assignment of trained and competent personnel, and the operational
          decisions made based on Platform outputs.
        </p>

        <hr className="my-6 border-slate-200" />

        <h2>9. Limitation of Liability</h2>
        <p className="uppercase">
          TO THE FULLEST EXTENT PERMITTED BY LAW, IN NO EVENT SHALL FORGEDOPS LLC
          BE LIABLE TO MASCI OR TO ANY USER FOR ANY INDIRECT, INCIDENTAL, SPECIAL,
          CONSEQUENTIAL, OR PUNITIVE DAMAGES, INCLUDING WITHOUT LIMITATION LOST
          PROFITS, LOST REVENUE, LOSS OF BUSINESS, LOSS OF OPPORTUNITY, LOSS OF
          GOODWILL, LOSS OR INACCURACY OF DATA, OR COST OF PROCUREMENT OF
          SUBSTITUTE GOODS OR SERVICES, ARISING OUT OF OR RELATED TO THE PLATFORM
          OR THESE TERMS, WHETHER BASED ON CONTRACT, TORT (INCLUDING NEGLIGENCE),
          STRICT LIABILITY, OR ANY OTHER LEGAL THEORY, EVEN IF FORGEDOPS LLC HAS
          BEEN ADVISED OF THE POSSIBILITY OF SUCH DAMAGES.
        </p>
        <p className="uppercase">
          THE AGGREGATE LIABILITY OF FORGEDOPS LLC ARISING OUT OF OR RELATED TO
          THE PLATFORM OR THESE TERMS, FROM ALL CLAIMS AND ALL CAUSES OF ACTION
          COMBINED, SHALL NOT EXCEED FIFTY THOUSAND U.S. DOLLARS ($50,000 USD)
          IN THE AGGREGATE.
        </p>
        <p>
          The exclusions and cap set forth in this Section 9 do not apply to:
          (a) liability that cannot be limited or excluded under applicable law;
          (b) a party&rsquo;s indemnification obligations under Section 10; or
          (c) liability arising from fraud, gross negligence, or willful misconduct.
          These exclusions and the cap apply notwithstanding any failure of essential
          purpose of any limited remedy.
        </p>

        <hr className="my-6 border-slate-200" />

        <h2>10. Indemnification</h2>
        <p>
          MASCI agrees to defend, indemnify, and hold harmless ForgedOps
          LLC from and against any claims, damages, losses, liabilities, or
          expenses arising out of or related to:
        </p>
        <ol>
          <li>MASCI&rsquo;s use of the Platform;</li>
          <li>any violation of law or regulation;</li>
          <li>failure to comply with safety or operational requirements;</li>
          <li>misuse of the Platform by MASCI or its users.</li>
        </ol>

        <hr className="my-6 border-slate-200" />

        <h2>11. Termination</h2>
        <p>
          ForgedOps LLC or MASCI may suspend or terminate any
          user&rsquo;s access to the Platform at any time, with or without
          cause.
        </p>
        <p>Upon termination, all rights granted under these Terms immediately cease.</p>
        <p>
          Sections relating to ownership, confidentiality, liability,
          indemnification, and governing law survive termination.
        </p>

        <hr className="my-6 border-slate-200" />

        <h2>12. Changes to These Terms</h2>
        <p>ForgedOps LLC may update these Terms at any time.</p>
        <p>Material changes will be communicated to MASCI.</p>
        <p>
          Continued use of the Platform after changes become effective
          constitutes acceptance of the updated Terms.
        </p>

        <hr className="my-6 border-slate-200" />

        <h2>13. Governing Law</h2>
        <p>These Terms are governed by the laws of the State of Florida.</p>
        <p>
          Any disputes shall be resolved exclusively in the state or federal
          courts located in Flagler County, Florida.
        </p>

        <hr className="my-6 border-slate-200" />

        <h2>14. Contact</h2>
        <p>
          For questions regarding these Terms, contact MASCI administration or
          ForgedOps LLC regarding the Platform.
        </p>

        <hr className="my-8 border-slate-200" />
        <p className="text-xs text-slate-500">
          See also our{" "}
          <Link to="/legal/privacy" className="underline" data-testid="terms-privacy-link">
            Privacy Policy
          </Link>
          .
        </p>
      </article>
    </main>
  );
}
