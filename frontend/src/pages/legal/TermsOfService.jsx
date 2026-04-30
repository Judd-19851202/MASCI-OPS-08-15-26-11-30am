import React from "react";
import { Link } from "react-router-dom";
import { ArrowLeft, Scale } from "lucide-react";
import { JuddGroupAttribution } from "@/components/JuddGroupAttribution";

/**
 * /legal/terms — Terms of Service.
 *
 * Plain-English ownership protection covering:
 *   • Platform owned by The Judd Group LLC (sole owner).
 *   • MASCI's licensed-use rights (limited, non-transferable, revocable).
 *   • No transfer of ownership.
 *   • Confidentiality, no warranty, limitation of liability.
 *
 * Drafted as a template that fits MASCI today and any future client
 * Jaymn onboards under the same platform.
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
          Effective Date: April 30, 2026 · Last Updated: April 30, 2026
        </p>

        <section className="mb-6">
          <p>
            These Terms of Service (&ldquo;<strong>Terms</strong>&rdquo;)
            govern your access to and use of the field operations and safety
            documentation platform (the &ldquo;<strong>Platform</strong>
            &rdquo;) operated and maintained by{" "}
            <strong>The Judd Group LLC</strong> (&ldquo;<strong>Owner</strong>
            &rdquo;, &ldquo;we&rdquo;, &ldquo;us&rdquo;, or &ldquo;our&rdquo;).
            By accessing or using the Platform you (&ldquo;<strong>User</strong>
            &rdquo;) agree to be bound by these Terms.
          </p>
        </section>

        <h2>1. Ownership</h2>
        <p>
          The Platform — including all source code, designs, branding,
          databases, copy, configurations, integrations, and related
          intellectual property (collectively, the &ldquo;
          <strong>Platform IP</strong>&rdquo;) — is and remains the sole and
          exclusive property of The Judd Group LLC. No part of the Platform
          IP transfers to any User, customer, employee, contractor, or third
          party by virtue of access, configuration, or use.
        </p>

        <h2>2. Limited License to Use</h2>
        <p>
          The Owner grants the licensed organization (e.g., MASCI General
          Contractors and other authorized customers) a limited, revocable,
          non-exclusive, non-transferable, non-sublicensable right to access
          and use the Platform solely for its internal field operations,
          safety reporting, and recordkeeping purposes during the term of
          its services agreement with the Owner.
        </p>
        <p>
          This license does <strong>not</strong> grant any right to: (i) copy,
          modify, decompile, reverse-engineer, or create derivative works of
          the Platform; (ii) resell, sublicense, or otherwise commercially
          exploit the Platform; (iii) remove, alter, or obscure any
          attribution, copyright, or ownership notice; or (iv) use the
          Platform for any unlawful purpose.
        </p>

        <h2>3. No Transfer of Ownership</h2>
        <p>
          For the avoidance of doubt, payment of subscription, hosting,
          implementation, or service fees does <strong>not</strong> constitute
          a sale, assignment, or transfer of any portion of the Platform IP.
          The licensed organization receives the right to use the Platform —
          not to own it. This applies regardless of the volume of data the
          User uploads, the customizations requested, or the duration of use.
        </p>

        <h2>4. User Data</h2>
        <p>
          The licensed organization retains ownership of the records, files,
          photos, and documents it uploads to the Platform (&ldquo;
          <strong>User Data</strong>&rdquo;). The Owner is granted a limited
          right to host, process, and back up User Data solely as required to
          operate the Platform on the User&rsquo;s behalf. Upon termination,
          the User may export its User Data within thirty (30) days; after
          that period the Owner may delete it.
        </p>

        <h2>5. Confidentiality</h2>
        <p>
          Each party agrees to keep the other party&rsquo;s non-public
          information confidential and to use it only for the purposes
          contemplated by these Terms. The Owner&rsquo;s source code,
          architecture, and roadmaps are confidential information of the
          Owner.
        </p>

        <h2>6. Acceptable Use</h2>
        <p>
          You agree not to use the Platform to (i) violate any law or
          regulation; (ii) infringe any third party&rsquo;s rights; (iii)
          upload malicious code; (iv) interfere with the Platform&rsquo;s
          operation or security; or (v) attempt to gain unauthorized access
          to any account, system, or data.
        </p>

        <h2>7. No Warranty</h2>
        <p>
          THE PLATFORM IS PROVIDED &ldquo;AS IS&rdquo; AND &ldquo;AS
          AVAILABLE&rdquo; WITHOUT WARRANTIES OF ANY KIND, WHETHER EXPRESS OR
          IMPLIED, INCLUDING WARRANTIES OF MERCHANTABILITY, FITNESS FOR A
          PARTICULAR PURPOSE, NON-INFRINGEMENT, OR UNINTERRUPTED OPERATION.
          The Platform is a tool to support — not replace — the licensed
          organization&rsquo;s safety program and competent personnel.
        </p>

        <h2>8. Limitation of Liability</h2>
        <p>
          TO THE FULLEST EXTENT PERMITTED BY LAW, IN NO EVENT WILL THE OWNER
          BE LIABLE FOR ANY INDIRECT, INCIDENTAL, SPECIAL, CONSEQUENTIAL, OR
          PUNITIVE DAMAGES, INCLUDING LOST PROFITS, LOST DATA, OR BUSINESS
          INTERRUPTION, ARISING OUT OF OR RELATED TO THESE TERMS OR THE
          PLATFORM, EVEN IF ADVISED OF THE POSSIBILITY. The Owner&rsquo;s
          aggregate liability for any claim will not exceed the fees paid by
          the licensed organization to the Owner in the twelve (12) months
          preceding the claim.
        </p>

        <h2>9. Termination</h2>
        <p>
          The Owner may suspend or terminate access to the Platform if the
          User materially breaches these Terms or the underlying services
          agreement. On termination, the User&rsquo;s license to use the
          Platform ends immediately; ownership and confidentiality
          obligations survive.
        </p>

        <h2>10. Changes to These Terms</h2>
        <p>
          The Owner may update these Terms from time to time. Material
          changes will be communicated to the licensed organization in
          writing. Continued use of the Platform after the effective date of
          a change constitutes acceptance.
        </p>

        <h2>11. Governing Law</h2>
        <p>
          These Terms are governed by the laws of the State of Florida
          without regard to its conflicts-of-laws rules. Any dispute will be
          resolved exclusively in the state or federal courts sitting in
          Volusia County, Florida.
        </p>

        <h2>12. Contact</h2>
        <p>
          Questions about these Terms? Contact{" "}
          <strong>The Judd Group LLC</strong> through your Platform account
          administrator.
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
