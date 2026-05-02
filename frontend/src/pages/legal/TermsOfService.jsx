import React from "react";
import { Link } from "react-router-dom";
import { ArrowLeft, Scale } from "lucide-react";
import { JuddGroupAttribution } from "@/components/JuddGroupAttribution";

/**
 * /legal/terms — Terms of Service.
 *
 * IMPORTANT: MASCI is the owner and operator of MASCI HUB. The Judd Group
 * LLC is the development contractor only — they built the platform on a
 * work-for-hire basis for MASCI. They are NOT a parent, subsidiary,
 * partner, or co-owner of MASCI in any form.
 *
 * Plain-English coverage:
 *   • MASCI is the operator and owner of the Platform.
 *   • Authorized users (MASCI employees, contractors, clients) have a
 *     limited license to use the Platform per MASCI's policies.
 *   • Confidentiality, no warranty, limitation of liability protections.
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
            govern your access to and use of the MASCI HUB field operations
            and safety documentation platform (the &ldquo;
            <strong>Platform</strong>&rdquo;) operated by{" "}
            <strong>MASCI General Contractors Inc.</strong> and{" "}
            <strong>MASCI Corporation</strong> (collectively, &ldquo;
            <strong>MASCI</strong>&rdquo;, &ldquo;we&rdquo;, &ldquo;us&rdquo;,
            or &ldquo;our&rdquo;). By accessing or using the Platform you
            (&ldquo;<strong>User</strong>&rdquo;) agree to be bound by these
            Terms.
          </p>
        </section>

        <h2>1. Ownership</h2>
        <p>
          The Platform — including all source code, designs, branding,
          databases, copy, configurations, integrations, and related
          intellectual property (collectively, the &ldquo;
          <strong>Platform IP</strong>&rdquo;) — is owned by MASCI. The
          Platform was developed for MASCI on a work-for-hire basis by{" "}
          <strong>The Judd Group LLC</strong>, who serves solely as MASCI&rsquo;s
          technology development partner. The Judd Group LLC is not a parent,
          subsidiary, affiliate, or co-owner of MASCI.
        </p>

        <h2>2. Limited License to Use</h2>
        <p>
          MASCI grants its authorized employees, contractors, project
          managers, foremen, shop personnel, and approved clients a limited,
          revocable, non-exclusive, non-transferable, non-sublicensable right
          to access and use the Platform solely for legitimate MASCI business
          purposes — including field operations, safety reporting, training,
          and recordkeeping.
        </p>
        <p>
          This license does <strong>not</strong> grant any right to: (i) copy,
          modify, decompile, reverse-engineer, or create derivative works of
          the Platform; (ii) resell, sublicense, or otherwise commercially
          exploit the Platform; (iii) remove, alter, or obscure any
          attribution, copyright, or ownership notice; or (iv) use the
          Platform for any unlawful purpose or outside the scope of your
          MASCI duties.
        </p>

        <h2>3. User Data &amp; Records</h2>
        <p>
          MASCI owns all records, files, photos, signatures, and documents
          submitted through the Platform (&ldquo;<strong>User Data</strong>
          &rdquo;) as part of its normal business records. Authorized users
          who upload User Data do so as part of their work for MASCI. Upon
          separation from MASCI, an individual user&rsquo;s access ends, but
          the User Data they created during their tenure remains MASCI
          property.
        </p>

        <h2>4. Confidentiality</h2>
        <p>
          The Platform contains internal MASCI business information, safety
          procedures, financial records, employee data, and proprietary
          workflows. Users agree to keep all non-public information accessed
          through the Platform confidential and to use it only for legitimate
          MASCI business purposes.
        </p>

        <h2>5. Acceptable Use</h2>
        <p>
          You agree not to use the Platform to (i) violate any law or
          regulation; (ii) infringe any third party&rsquo;s rights; (iii)
          upload malicious code; (iv) interfere with the Platform&rsquo;s
          operation or security; (v) attempt to gain unauthorized access to
          any account, system, or data; or (vi) share login credentials or
          access tokens with anyone outside their authorized scope.
        </p>

        <h2>6. No Warranty</h2>
        <p>
          THE PLATFORM IS PROVIDED &ldquo;AS IS&rdquo; AND &ldquo;AS
          AVAILABLE&rdquo; WITHOUT WARRANTIES OF ANY KIND, WHETHER EXPRESS OR
          IMPLIED, INCLUDING WARRANTIES OF MERCHANTABILITY, FITNESS FOR A
          PARTICULAR PURPOSE, NON-INFRINGEMENT, OR UNINTERRUPTED OPERATION.
          The Platform is a tool to support — not replace — MASCI&rsquo;s
          safety program, supervisors, and competent personnel. Users remain
          responsible for following all applicable safety regulations,
          OSHA standards, and MASCI policies in the field.
        </p>

        <h2>7. Limitation of Liability</h2>
        <p>
          TO THE FULLEST EXTENT PERMITTED BY LAW, IN NO EVENT WILL MASCI BE
          LIABLE TO ANY INDIVIDUAL USER FOR ANY INDIRECT, INCIDENTAL,
          SPECIAL, CONSEQUENTIAL, OR PUNITIVE DAMAGES ARISING OUT OF OR
          RELATED TO THESE TERMS OR THE PLATFORM, EVEN IF ADVISED OF THE
          POSSIBILITY.
        </p>

        <h2>8. Termination</h2>
        <p>
          MASCI may suspend or terminate any individual user&rsquo;s access
          to the Platform at any time, with or without cause. On termination,
          the user&rsquo;s license to use the Platform ends immediately;
          ownership, confidentiality, and acceptable-use obligations survive.
        </p>

        <h2>9. Changes to These Terms</h2>
        <p>
          MASCI may update these Terms from time to time. Material changes
          will be communicated to authorized users. Continued use of the
          Platform after the effective date of a change constitutes
          acceptance.
        </p>

        <h2>10. Governing Law</h2>
        <p>
          These Terms are governed by the laws of the State of Florida
          without regard to its conflicts-of-laws rules. Any dispute will be
          resolved exclusively in the state or federal courts sitting in
          Flagler County, Florida.
        </p>

        <h2>11. Contact</h2>
        <p>
          Questions about these Terms? Contact MASCI through your supervisor
          or the MASCI HUB administrator.
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
