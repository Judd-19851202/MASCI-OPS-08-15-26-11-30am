# MASCI IT Integration Brief

**Subject:** Server-Side Archive Integration for the MASCI Operations Platform
**Prepared for:** MASCI IT Leadership
**Prepared by:** Emergent / MASCI Operations Platform team
**Status:** Planning document · no implementation has begun · awaiting MASCI IT input

---

## Executive Summary

The MASCI Operations Platform (`mascidocs.com`) is the company's production
operational platform supporting daily field, HR, dispatch, safety, and
project-management workflows. It currently runs on Emergent-managed
infrastructure with Cloudflare R2 (S3-compatible object storage) as the
primary disaster-recovery backup target.

We are proposing a **second, MASCI-owned archive target** on MASCI server
infrastructure. The purpose is **operational sovereignty over human-readable
records** — PDFs, CSVs, photos, and export bundles that MASCI may need to
access independently of Emergent or Cloudflare in the future.

### What is being archived
Human-readable operational records only. **Not** the live production database.
**Not** real-time data. **Not** application state.

### Why MASCI wants this
1. **Independent ownership** — records of the business should live on hardware
   the business controls, regardless of vendor relationships.
2. **Audit / compliance readiness** — regulators, insurers, attorneys, or
   acquirers may someday request records in a format and from a location
   that doesn't depend on a SaaS subscription.
3. **Operational continuity** — if the platform vendor relationship changes
   five years from now, MASCI still has the last five years of operational
   records accessible without negotiation.
4. **Backup-of-the-backup** — Cloudflare R2 is the operational restore target;
   MASCI's archive is the long-term company-owned record.

### What this proposal is NOT
- ❌ NOT a request to host the live database on MASCI servers
- ❌ NOT a migration off Emergent or Cloudflare
- ❌ NOT a request to run application logic on MASCI infrastructure
- ❌ NOT a request to expose MASCI infrastructure to public internet
- ❌ NOT a real-time replication target

### Two distinct archive layers (post-integration)

| Layer | Owner | Purpose | Retention |
|---|---|---|---|
| **Cloudflare R2** | Emergent-managed | Operational restore / disaster recovery | Rolling (operational) |
| **MASCI server archive** | MASCI-owned | Long-term human-readable record | Indefinite (per MASCI policy) |

These two layers are **independent and complementary**. Neither replaces
the other.

---

## 1 · What Data Is Expected to Move

### 1.1 · File types

| Type | Typical size | Purpose |
|---|---|---|
| **PDF exports** | 50 KB – 5 MB | Daily reports · safety incidents · write-ups · onboarding packets · operational summaries |
| **CSV exports** | 10 KB – 2 MB | Time records · equipment lists · employee rosters · dispatch logs |
| **Photos / images** | 200 KB – 5 MB | Incident photos · equipment condition photos · jobsite documentation |
| **Bundled archives** | 10 MB – 200 MB | Multi-record export bundles (e.g., a month of daily reports + photos) |
| **Index / manifest files** | < 50 KB | Structured manifests describing what's in each bundle |

### 1.2 · Approximate archive structure

The proposed on-disk layout (illustrative · final structure subject to MASCI IT preferences):

```
masci-archive/
├── 2026/
│   ├── 01/
│   │   ├── daily-reports/
│   │   │   ├── 2026-01-15_DR-1234.pdf
│   │   │   ├── 2026-01-15_DR-1234_photos/
│   │   │   └── manifest.json
│   │   ├── hr-records/
│   │   ├── safety-incidents/
│   │   ├── dispatch-logs/
│   │   └── exports/
│   ├── 02/
│   └── ...
├── 2025/
└── 2024/
```

This structure is one proposal. MASCI IT may have an alternative preference
(e.g., flat organization by record-type root with year subfolders, or
SharePoint document-library structure). **We will adapt to MASCI's
preferred layout.**

### 1.3 · Estimated storage growth

These are honest ranges, not promises. Final numbers depend on MASCI's
operational scale.

| Time horizon | Estimated total size | Notes |
|---|---|---|
| Year 1 (current pace) | **30 – 80 GB** | Dependent on photo volume |
| Year 5 cumulative | **150 – 400 GB** | Assuming linear growth |
| Year 10 cumulative | **300 – 800 GB** | Assuming linear growth |

**Drivers of variance:** number of active foremen, photo upload frequency,
incident rate, daily report attachment behavior, export bundle frequency.

**Recommendation:** provision **1 TB** of MASCI-side storage initially with
a clear path to expand. This buys ~10 years of runway at current pace and
gives MASCI IT room to grow without re-architecting.

### 1.4 · Archive frequency options

| Cadence | Bandwidth | Operational fit |
|---|---|---|
| **Continuous (near-real-time)** | High · constant low-rate | Not recommended for human-readable archive · operational overkill |
| **Hourly** | Medium | Available if MASCI wants near-current view · adds complexity |
| **Daily** | **Low** | **Recommended** · matches operational rhythm · simplest |
| **Weekly** | Very low | Acceptable · trades freshness for simplicity |
| **Monthly bundle** | Very low (bursty) | Acceptable for human-readable archive · larger transfers, less frequent |

**Recommendation:** **Daily archive run** with a configurable retention
window on the Emergent side. This gives MASCI a fresh-enough mirror while
keeping the transfer cadence predictable.

### 1.5 · Expected bandwidth

Daily archive at current operational pace:
- Typical day: **50 – 300 MB** transferred
- Heavy day (multi-photo incidents · large export bundle generated): **500 MB – 1.5 GB**

On a standard 100 Mbps business connection, even a heavy day completes in
under 2 minutes. **No bandwidth concerns at any realistic MASCI scale.**

---

## 2 · Integration Methods · Comparison

We've evaluated the common options from MASCI IT's perspective. Honest
trade-offs:

| Method | Pros | Cons | MASCI IT effort |
|---|---|---|---|
| **MASCI pulls from R2** (recommended) | MASCI controls everything · no inbound exposure · MASCI owns schedule · read-only S3 credentials limited scope · works with `rclone` / `aws cli` / Cyberduck / Synology Cloud Sync · MASCI can use any tool that speaks S3 | MASCI runs the scheduled job · needs S3-compatible client | **Low.** Set up a scheduled task. |
| **SFTP push from Emergent** | Universal · IT-friendly · encrypted by default | MASCI must expose inbound SFTP port · Emergent stores SFTP creds · MASCI must provision account | **Medium.** Open firewall, provision user. |
| **SMB / CIFS share** | Native Windows experience · IT teams comfortable | Requires VPN tunnel or exposed share · firewall complexity · Linux-side mount fragility | **Medium-high.** VPN + share + permissions. |
| **NAS direct (over VPN)** | Native storage appliance | Same as SMB · VPN dependency · single point of failure | **Medium-high.** |
| **Azure Files** | Cloud-managed · Microsoft-stack synergy | Requires Azure subscription · MASCI infra dependency on Azure · cost adds up | **Low-medium** (if already Azure). |
| **SharePoint / OneDrive (Graph API)** | Microsoft-stack synergy · familiar UI for end-users | API rate limits · auth complexity (Azure AD app registration) · file-size limits · throttling | **Medium-high.** App registration + permissions. |
| **Custom API endpoint on MASCI side** | Full control | MASCI builds, hosts, and maintains an HTTPS endpoint · requires app development | **Very high.** Not recommended. |
| **Mapped drive (over VPN)** | Familiar to admins | Same constraints as SMB · least reliable | **Medium-high.** |
| **Local sync agent** (Resilio · Syncthing) | Bidirectional · resilient · resumable | MASCI must install + maintain agent on a MASCI server · vendor dependency | **Medium.** Software install + ongoing maintenance. |

---

## 3 · Recommended Architecture

### 3.1 · Honest recommendation

> **MASCI pulls archives from Cloudflare R2 on a scheduled cron job.**

This is the simplest, safest, lowest-maintenance, and most operationally
mature setup for the stated goal (long-term company-owned human-readable
archive).

### 3.2 · Why this is the right answer

| Concern | How this design addresses it |
|---|---|
| **Inbound firewall risk** | None. MASCI makes outbound HTTPS requests only. No exposed inbound port required. |
| **Credential exposure** | Minimal. Read-only S3 credentials scoped to a single bucket prefix. MASCI rotates on their schedule. |
| **MASCI controls schedule** | Yes. The pull job runs when MASCI's IT schedules it. Emergent doesn't push anything. |
| **MASCI controls retention** | Yes. Once a file is on MASCI's server, MASCI owns it indefinitely. Emergent's R2 retention does not affect MASCI's local copy. |
| **Vendor independence** | Yes. If Emergent goes away, MASCI still has every record pulled to date. |
| **Encryption in transit** | Built-in. HTTPS/TLS to Cloudflare R2. |
| **Encryption at rest on MASCI side** | MASCI's responsibility · standard server-side encryption applies. |
| **Resumability of partial transfers** | Built-in via `rclone` and `aws cli` chunked transfers. |
| **Verification / integrity** | Built-in. S3 ETag / MD5 / SHA-256 checksums on every object. |
| **Disaster recovery on the MASCI side** | Standard. MASCI backs up its own server using existing MASCI backup procedures. |
| **No software install on MASCI infra** | True if MASCI uses native `rclone` or `aws cli` (both free, open-source, widely deployed). |

### 3.3 · Sample operational flow

1. **Emergent side (no MASCI involvement):** the platform's existing export
   pipeline (already operational) writes daily archive bundles to a dedicated
   R2 bucket prefix, e.g. `masci-archive/YYYY/MM/DD/...`.
2. **MASCI side:** a scheduled task (Windows Task Scheduler / cron / etc.)
   runs once daily — say at 02:00 local. The task executes `rclone sync` (or
   equivalent) from the R2 bucket prefix to the MASCI archive volume.
3. **MASCI side:** existing MASCI server backup procedures back up the archive
   volume to MASCI's standard backup target.
4. **Verification:** the pull tool writes a daily log file recording number of
   files transferred, total bytes, and any errors. MASCI IT monitors this log
   per standard MASCI IT operational practice.

### 3.4 · What this design avoids

- No VPN tunnel
- No inbound port opening on MASCI infrastructure
- No exposed shares
- No application software running on MASCI infrastructure
- No real-time replication complexity
- No Azure / Microsoft 365 dependency
- No custom-built endpoints on the MASCI side
- No vendor agents installed on MASCI servers

### 3.5 · Acceptable secondary option

If MASCI IT specifically prefers a "push to us" model rather than a "pull
from R2" model, **SFTP push from Emergent to a MASCI-hosted SFTP server**
is the second-best option. The trade-off: MASCI exposes an inbound SFTP
port (standard practice, firewall-restricted to Emergent's outbound IP
range), Emergent stores the SFTP credentials, and Emergent owns the
schedule.

We'd recommend the pull-from-R2 model first, but we will accommodate
SFTP-push if MASCI IT has a strong preference.

---

## 4 · What Emergent Needs From MASCI IT

To finalize the integration design, we need MASCI IT to confirm or provide
the following. Most of these are simple yes/no or one-line answers — we
just need them in writing before we begin implementation.

### 4.1 · Architectural decision
- [ ] Preferred transfer method (pull-from-R2 recommended · SFTP-push acceptable · other if strongly preferred)

### 4.2 · Storage
- [ ] Server / NAS / network location designated for the archive (path or share name)
- [ ] Initial storage quota commitment (we recommend **1 TB** initial provision)
- [ ] Path to expand quota when needed (we'll alert at 75% used)

### 4.3 · Access path
- [ ] If pull-from-R2: confirmation that the MASCI server can make outbound HTTPS to `*.r2.cloudflarestorage.com`
- [ ] If SFTP-push: MASCI provides hostname, port, dedicated SFTP user, and key-based authentication (we do NOT want password auth)

### 4.4 · Retention
- [ ] MASCI's retention policy for archived records (years · indefinite · per-category)
- [ ] Whether MASCI wants old records deleted at any point, or kept forever

### 4.5 · Firewall / network rules
- [ ] If pull-from-R2: no inbound rules needed; confirmation that outbound HTTPS to Cloudflare R2 is allowed
- [ ] If SFTP-push: inbound rule for Emergent's outbound IP range (we will provide)

### 4.6 · Monitoring expectations
- [ ] How MASCI wants to receive operational alerts (email · ticket · syslog · existing MASCI monitoring stack)
- [ ] What MASCI considers a "successful daily archive run" vs. requiring escalation

### 4.7 · Write permissions
- [ ] If pull-from-R2: the cron user on the MASCI server needs write access to the archive volume
- [ ] If SFTP-push: the SFTP user needs write access scoped to the archive directory (and nothing else)

### 4.8 · Point of contact
- [ ] Designated MASCI IT contact for archive operations (escalation path for failures)
- [ ] Designated MASCI IT contact for credential rotation / access changes

---

## 5 · Security · Operational Considerations

### 5.1 · Encryption

| Layer | Method | Owner |
|---|---|---|
| **In transit (Emergent → R2)** | HTTPS / TLS 1.2+ | Emergent / Cloudflare |
| **At rest (R2 bucket)** | Cloudflare R2 server-side encryption | Cloudflare |
| **In transit (R2 → MASCI)** | HTTPS / TLS 1.2+ | Cloudflare → MASCI |
| **At rest (MASCI server)** | MASCI's standard server-side encryption | **MASCI** |

### 5.2 · Archive ownership boundaries

| Asset | Owner | Responsibility |
|---|---|---|
| Live production database | Emergent-managed | Emergent operates and backs up |
| Cloudflare R2 backup | Emergent-managed | Emergent operates, monitors, restores |
| **MASCI archive (server-side)** | **MASCI** | **MASCI operates, monitors, backs up** |
| Archive integrity verification | Shared | Emergent provides checksums · MASCI validates on receipt |
| Archive retention | **MASCI** | MASCI defines and enforces per their policy |

### 5.3 · Retention separation

- **R2 retention:** rolling operational window managed by Emergent's backup-verification system. Retention here is sized for operational restore, not historical record.
- **MASCI archive retention:** indefinite (or per MASCI policy). The two retention windows are explicitly different and that is intentional.
- **No coordination required** between the two retention layers. R2 may age out files that MASCI has already pulled and retained. That is the design.

### 5.4 · Operational responsibility boundaries

| Operational concern | Emergent | MASCI |
|---|---|---|
| Generating exports | ✅ | |
| Writing to R2 | ✅ | |
| R2 bucket health, integrity, encryption | ✅ | |
| Providing read-only R2 credentials to MASCI | ✅ | |
| Scheduled pull from R2 (or SFTP receive) | | ✅ |
| Archive volume health and capacity | | ✅ |
| MASCI-side backup of the archive | | ✅ |
| Monitoring the daily archive job | | ✅ |
| Long-term retention and access policies | | ✅ |
| Restoring from MASCI archive if ever needed | | ✅ |
| Restoring from R2 if ever needed | ✅ | |

### 5.5 · Disaster recovery philosophy

There are now **three layers** of MASCI record protection:

1. **Live database** (Emergent infrastructure) — primary operational copy.
2. **Cloudflare R2** (Emergent-managed) — operational disaster-recovery
   restore target. Used if the live database needs to be reconstructed.
3. **MASCI server archive** (MASCI-owned) — long-term company-owned
   human-readable record. Used if (a) MASCI needs records independent of
   Emergent or (b) records are needed for audit / compliance / legal
   without going through the operational platform.

Each layer protects against a different failure mode. None replaces the
others. This is intentional defense-in-depth.

---

## 6 · Out of Scope (Explicitly)

The following are NOT part of this integration:

- ❌ Hosting the live production database on MASCI infrastructure
- ❌ Running the application stack on MASCI infrastructure
- ❌ Real-time bidirectional sync
- ❌ Allowing MASCI infrastructure to write back into the production platform
- ❌ Exposing MASCI internal systems to the public internet
- ❌ Replacing the existing Cloudflare R2 backup target
- ❌ Replacing existing MASCI backup procedures
- ❌ Migrating off Emergent
- ❌ Any change to operational platform behavior visible to end users

If any of these surface later as MASCI requirements, they are **separate
projects** requiring their own briefs.

---

## 7 · Suggested Next Steps

This is a planning document. No implementation will begin without explicit
sign-off. Suggested sequence:

1. **MASCI IT review** of this brief.
2. **MASCI IT response** providing the items requested in Section 4.
3. **Joint review call** (Emergent + MASCI IT) — 30 minutes — to clarify
   any architectural questions before implementation.
4. **Implementation phase** (Emergent side) — provisioning the dedicated R2
   bucket prefix, generating the read-only credentials, providing setup
   documentation for the MASCI-side pull job.
5. **Test cycle** — run the pull for one week against a non-production
   archive subset to validate the integration before going live.
6. **Production cutover** — start daily archive runs.

Total elapsed time (assuming MASCI IT responsiveness): **2 – 4 weeks**.

---

## 8 · Appendix · Glossary for Non-Technical Reviewers

| Term | Plain-English meaning |
|---|---|
| **Cloudflare R2** | An Amazon S3-compatible cloud storage service. Used as the platform's backup target. |
| **S3-compatible** | Speaks the same protocol as Amazon S3, the de-facto standard for cloud file storage. Most backup tools speak it. |
| **rclone** | Free, open-source command-line tool for syncing files between cloud storage and local servers. Industry-standard. |
| **SFTP** | Secure File Transfer Protocol. The encrypted version of FTP. Used for moving files between servers securely. |
| **SMB / CIFS** | The protocol Windows uses for file shares (the "shared folder" experience). |
| **VPN** | Virtual Private Network. A secure tunnel between two networks. |
| **TLS** | Transport Layer Security. The encryption used in HTTPS. |
| **Cron** | A Linux scheduled-task system. Equivalent to Windows Task Scheduler. |
| **Archive bundle** | A grouped collection of related records exported as a single package (e.g., a month of daily reports + their photos). |
| **Restore-grade backup** | A backup designed to fully rebuild the system from scratch. Different from a human-readable archive. |
| **Human-readable archive** | Records in formats a human can open directly (PDF, CSV, JPG) without needing the platform. |

---

## 9 · Document Control

- **Document type:** External planning / integration brief
- **Audience:** MASCI IT Leadership · technical and non-technical
- **Status:** Draft for review · no implementation has begun · awaiting MASCI IT input
- **Prepared:** 2026-05-18
- **Next revision:** after MASCI IT response to Section 4

---

*This brief contains no implementation work. It is a request for MASCI IT
input to enable a future implementation phase. The MASCI Operations
Platform continues to operate normally during the planning period.*
