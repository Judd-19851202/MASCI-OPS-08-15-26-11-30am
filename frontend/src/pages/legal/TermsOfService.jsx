import React from "react";
import { Link } from "react-router-dom";
import { ArrowLeft, Scale } from "lucide-react";
import { JuddGroupAttribution } from "@/components/JuddGroupAttribution";

/**
 * /legal/terms — Terms of Service.
 *
 * RELATIONSHIP CLARIFIED (2026-05-02):
 *   • The Judd Group LLC owns and operates the underlying Platform —
 *     the source code, software, infrastructure, and the
 *     mascidocs.com domain. Same way Microsoft owns Word and Excel.
 *   • MASCI is a customer of the Platform. "MASCI HUB" is MASCI's
 *     branded customer deployment. MASCI owns all data they submit
 *     through it. Same way a company that uses Word owns its documents.
 *   • The two companies are independent. Neither owns, controls, or
 *     is a subsidiary of the other.
 */
export default function TermsOfService() {
  return (
    <main className="min-h-screen bg-slate-50">
      <header className="border-b-2 border-slate-200 bg-white">
        <div className="max-w-3xl mx-auto px-4 sm:px-6 py-4 flex items-center gap-3">
          <Link to="/" className="text-slate-600 hover:text-slate-900">
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
        <p className="text-xs font-mono uppercase tracking-wide text-slate-500 mb-4">
          Effective Date: January 01, 2026 · Last Updated: May 02, 2026
        </p>

        <section className="mb-6">
          <p>
            These Terms of Service (&ldquo;<strong>Terms</strong>&rdquo;)
            govern your access to and use of the field-operations and
            safety-documentation software platform (the &ldquo;
            <strong>Platform</strong>&rdquo;) provided by{" "}
            <strong>The Judd Group LLC</strong> (&ldquo;
            <strong>Provider</strong>&rdquo;, &ldquo;we&rdquo;,
            &ldquo;us&rdquo;). The Platform is licensed to{" "}
            <strong>MASCI General Contractors Inc.</strong> and{" "}
            <strong>MASCI Corporation</strong> (collectively, &ldquo;
            <strong>MASCI</strong>&rdquo;) and is delivered to MASCI&rsquo;s
            users at the customer-branded URL <em>mascidocs.com</em> as
            &ldquo;<strong>MASCI HUB</strong>&rdquo;. By accessing or using
            the Platform, you (&ldquo;<strong>User</strong>&rdquo;) agree to
            these Terms.
          </p>
        </section>

        <h2>1. Relationship of the Parties</h2>
        <p>
          The Judd Group LLC and MASCI are independent companies. Neither is
          a parent, subsidiary, affiliate, partner, agent, or co-owner of
          the other. The Judd Group LLC is the software vendor; MASCI is the
          customer.
        </p>

        <h2>2. Ownership of the Platform</h2>
        <p>
          The Judd Group LLC owns and retains all right, title, and interest
          in the Platform, including all source code, designs, databases,
          software, documentation, configurations, infrastructure, and the
          <em> mascidocs.com</em> domain (collectively, the &ldquo;
          <strong>Platform IP</strong>&rdquo;). Nothing in these Terms
          transfers any ownership of the Platform IP to MASCI or to any
          User. MASCI&rsquo;s use of the Platform is limited to the rights
          expressly granted in MASCI&rsquo;s separate written services
          agreement with The Judd Group LLC.
        </p>

        <h2>3. Ownership of Customer Data</h2>
        <p>
          All records, files, photos, signatures, documents, and other
          information that MASCI or its users submit through the Platform
          (&ldquo;<strong>Customer Data</strong>&rdquo;) belong to MASCI.
          The Judd Group LLC stores and processes Customer Data solely to
          provide the Platform to MASCI. The Judd Group LLC does not claim
          ownership of Customer Data, will not use it for advertising, and
          will not sell or share it with third parties except as required
          to deliver the Platform (see Privacy Policy).
        </p>

        <h2>4. License to Use</h2>
        <p>
          Subject to these Terms, The Judd Group LLC grants MASCI&rsquo;s
          authorized employees, contractors, project managers, foremen,
          shop personnel, and approved clients a limited, revocable,
          non-exclusive, non-transferable, non-sublicensable right to access
          the Platform solely for legitimate MASCI business purposes —
          including field operations, safety reporting, training, and
          recordkeeping.
        </p>
        <p>
          This license does <strong>not</strong> grant any right to: (i)
          copy, modify, decompile, reverse-engineer, or create derivative
          works of the Platform; (ii) resell, sublicense, or otherwise
          commercially exploit the Platform; (iii) remove, alter, or obscure
          any attribution, copyright, or vendor notice; or (iv) use the
          Platform unlawfully or outside the scope of your MASCI duties.
        </p>

        <h2>5. Acceptable Use</h2>
        <p>
          You agree not to use the Platform to (i) violate any law or
          regulation; (ii) infringe any third party&rsquo;s rights; (iii)
          upload malicious code; (iv) interfere with the Platform&rsquo;s
          operation or security; (v) attempt unauthorized access to any
          account, system, or data; or (vi) share login credentials with
          anyone outside their authorized scope.
        </p>

        <h2>6. Confidentiality</h2>
        <p>
          The Platform contains MASCI&rsquo;s internal business information,
          safety procedures, financial records, employee data, and
          proprietary workflows. Users agree to keep all non-public
          information accessed through the Platform confidential and to use
          it only for legitimate MASCI business purposes.
        </p>

        <h2>7. No Warranty</h2>
        <p>
          THE PLATFORM IS PROVIDED &ldquo;AS IS&rdquo; AND &ldquo;AS
          AVAILABLE&rdquo; WITHOUT WARRANTIES OF ANY KIND, EXPRESS OR
          IMPLIED, INCLUDING WARRANTIES OF MERCHANTABILITY, FITNESS FOR A
          PARTICULAR PURPOSE, NON-INFRINGEMENT, OR UNINTERRUPTED OPERATION.
          The Platform is a tool to support — not replace — MASCI&rsquo;s
          safety program, supervisors, and competent personnel. Users
          remain responsible for following all applicable safety
          regulations, OSHA standards, and MASCI policies in the field.
        </p>

        <h2>8. Limitation of Liability</h2>
        <p>
          TO THE FULLEST EXTENT PERMITTED BY LAW, IN NO EVENT WILL THE JUDD
          GROUP LLC OR MASCI BE LIABLE TO ANY INDIVIDUAL USER FOR ANY
          INDIRECT, INCIDENTAL, SPECIAL, CONSEQUENTIAL, OR PUNITIVE DAMAGES
          ARISING OUT OF OR RELATED TO THESE TERMS OR THE PLATFORM, EVEN IF
          ADVISED OF THE POSSIBILITY.
        </p>

        <h2>9. Termination</h2>
        <p>
          MASCI or The Judd Group LLC may suspend or terminate any
          individual user&rsquo;s access to the Platform at any time, with
          or without cause. On termination, the user&rsquo;s license ends
          immediately. Sections 1–3, 6, 8, 10, and 11 survive termination.
        </p>

        <h2>10. Changes to These Terms</h2>
        <p>
          The Judd Group LLC may update these Terms from time to time.
          Material changes will be communicated to MASCI and to authorized
          users. Continued use of the Platform after the effective date of a
          change constitutes acceptance.
        </p>

        <h2>11. Governing Law</h2>
        <p>
          These Terms are governed by the laws of the State of Florida
          without regard to its conflicts-of-laws rules. Any dispute will be
          resolved exclusively in the state or federal courts sitting in
          Flagler County, Florida.
        </p>

        <h2>12. Contact</h2>
        <p>
          Questions about these Terms? Contact your MASCI administrator, or
          The Judd Group LLC for questions about the Platform itself.
        </p>

        <hr className="my-8 border-slate-200" />
        <p className="text-xs text-slate-500">
          See also our{" "}
          <Link to="/legal/privacy" className="underline">
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
