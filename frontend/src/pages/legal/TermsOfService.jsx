import React from "react";
import { Link } from "react-router-dom";
import { ArrowLeft, Scale } from "lucide-react";
import { JuddGroupAttribution } from "@/components/JuddGroupAttribution";

/**
 * /legal/terms — Terms of Service.
 *
 * Authoritative text supplied by the customer (MASCI / Judd Group)
 * on 2026-05-02. Treat the wording inside <article> as legal text — do
 * not edit phrasing without explicit owner approval.
 *
 * Relationship model:
 *   • The Judd Group LLC owns the Platform (code, software,
 *     infrastructure, mascidocs.com domain).
 *   • MASCI is the customer that licenses the Platform and owns all
 *     Customer Data submitted through it.
 *   • The two companies are independent. No subsidiary, affiliate,
 *     partner, or co-owner relationship.
 */
export default function TermsOfService() {
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
          Effective Date: January 01, 2026 · Last Updated: January 01, 2026
        </p>

        <p>
          These Terms of Service (&ldquo;<strong>Terms</strong>&rdquo;) govern
          your access to and use of the field-operations and
          safety-documentation software platform (the &ldquo;
          <strong>Platform</strong>&rdquo;) provided by{" "}
          <strong>The Judd Group LLC</strong> (&ldquo;<strong>Provider</strong>
          &rdquo;, &ldquo;we&rdquo;, &ldquo;us&rdquo;). The Platform is
          licensed to <strong>MASCI General Contractors Inc.</strong> and{" "}
          <strong>MASCI Corporation</strong> (collectively, &ldquo;
          <strong>MASCI</strong>&rdquo;) and is delivered to MASCI&rsquo;s
          users at the customer-branded URL <em>mascidocs.com</em> as &ldquo;
          <strong>MASCI HUB</strong>&rdquo;.
        </p>
        <p>
          By accessing or using the Platform, you (&ldquo;
          <strong>User</strong>&rdquo;) agree to these Terms.
        </p>

        <hr className="my-6 border-slate-200" />

        <h2>1. Relationship of the Parties</h2>
        <p>
          The Judd Group LLC and MASCI are independent companies. Neither is a
          parent, subsidiary, affiliate, partner, agent, or co-owner of the
          other. The Judd Group LLC is the software vendor; MASCI is the
          customer.
        </p>

        <hr className="my-6 border-slate-200" />

        <h2>2. Ownership of the Platform</h2>
        <p>
          The Judd Group LLC owns and retains all right, title, and interest
          in the Platform, including all source code, designs, databases,
          software, documentation, configurations, infrastructure, proprietary
          methods, workflows, system designs, and the <em>mascidocs.com</em>{" "}
          domain (collectively, the &ldquo;<strong>Platform IP</strong>
          &rdquo;).
        </p>
        <p>
          Nothing in these Terms transfers any ownership of the Platform IP to
          MASCI or to any User.
        </p>
        <p>
          MASCI acknowledges that the Platform includes proprietary systems
          and operational methodologies developed by The Judd Group LLC, and
          no rights are granted to replicate, reproduce, or develop competing
          systems based on the Platform.
        </p>
        <p>
          MASCI&rsquo;s use of the Platform is limited to the rights expressly
          granted in MASCI&rsquo;s separate written services agreement with
          The Judd Group LLC.
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
          The Judd Group LLC stores and processes Customer Data solely to
          provide the Platform and related services.
        </p>
        <p>
          The Judd Group LLC does not claim ownership of Customer Data and
          will not sell, share, or use it for advertising purposes.
        </p>
        <p>
          MASCI may request export of its Customer Data in a standard format.
          The Judd Group LLC will provide reasonable assistance but is not
          responsible for long-term storage, backup, or retention beyond
          normal system operations.
        </p>

        <hr className="my-6 border-slate-200" />

        <h2>4. License to Use</h2>
        <p>
          Subject to these Terms, The Judd Group LLC grants MASCI&rsquo;s
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
          third party requires a separate written agreement with The Judd
          Group LLC.
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

        <h2>7. Platform Availability &amp; Services</h2>
        <p>
          Access to the Platform is dependent on systems, infrastructure, and
          services controlled by The Judd Group LLC.
        </p>
        <p>
          The Judd Group LLC reserves the right to modify, suspend, or
          discontinue any portion of the Platform at its sole discretion.
        </p>
        <p>
          The Judd Group LLC does not guarantee uninterrupted access, uptime,
          or availability.
        </p>
        <p>
          Support, maintenance, and updates may be provided at the discretion
          of The Judd Group LLC or under separate agreement.
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
          Users remain fully responsible for compliance with all applicable
          laws, OSHA regulations, and company policies.
        </p>

        <hr className="my-6 border-slate-200" />

        <h2>9. Limitation of Liability</h2>
        <p className="uppercase">
          To the fullest extent permitted by law, in no event shall The Judd
          Group LLC or MASCI be liable to any user for any indirect,
          incidental, special, consequential, or punitive damages arising out
          of or related to the Platform or these Terms.
        </p>

        <hr className="my-6 border-slate-200" />

        <h2>10. Indemnification</h2>
        <p>
          MASCI agrees to defend, indemnify, and hold harmless The Judd Group
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
          The Judd Group LLC or MASCI may suspend or terminate any
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
        <p>The Judd Group LLC may update these Terms at any time.</p>
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
          The Judd Group LLC regarding the Platform.
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

      <footer className="border-t border-slate-200 py-6">
        <JuddGroupAttribution variant="global" />
      </footer>
    </main>
  );
}
