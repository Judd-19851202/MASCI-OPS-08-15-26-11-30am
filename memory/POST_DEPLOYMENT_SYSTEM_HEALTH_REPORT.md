POST-DEPLOYMENT SYSTEM HEALTH REPORT
=====================================

RELEASE     : MASCI Operations Platform · Track 18 Production Cut
RELEASE SHA : d5a8a4848ecbb3bf5e3eca1477fdee5929b7a84c
DATE        : 2026-06-29 (UTC)
ENV         : preview build (production deploy artefact)
PROD URL    : __________________ (operator-only)

Severity legend:
  SAFE     · within normal operating envelope
  WARNING  · degraded but non-blocking
  BLOCKER  · must be remediated before declaring GO

────────────────────────────────────────────────────────────────────────────
1 · BACKEND HEALTH
────────────────────────────────────────────────────────────────────────────
| Endpoint                          | Response                                              | Severity |
|-----------------------------------|-------------------------------------------------------|----------|
| `GET /api/health`                 | 200 · `{ok:true, service:"masci-hub"}`                | SAFE     |
| `GET /api/version`                | 200 · session timeouts on · Sentry on · APP_ENV preview · DB masci_safety_preview | SAFE (preview) |
| `GET /api/cluster/capacity`       | 200 · severity=`ok` · 309 MB / 10 240 MB (3.0 %)      | SAFE     |
| Backend supervisor                | RUNNING · uptime 2 h 12 m · no restart loop           | SAFE     |
| MongoDB supervisor                | RUNNING · uptime 12 h 46 m                            | SAFE     |
| nginx-code-proxy                  | RUNNING · uptime 12 h 46 m                            | SAFE     |
| Backend import errors             | 0                                                     | SAFE     |
| Worker crash loop                 | none                                                  | SAFE     |
| nginx upstream failures (post-boot)| none                                                  | SAFE     |
| CORS production regex             | mascidocs.com + *.emergentagent.com                   | SAFE     |

[OPERATOR] confirm equivalent values against live production URL.

────────────────────────────────────────────────────────────────────────────
2 · DISK / STORAGE
────────────────────────────────────────────────────────────────────────────
| Item                                  | Value                                  | Severity |
|---------------------------------------|----------------------------------------|----------|
| Pod filesystem (overlay)              | 107 G total · 17 G used · 90 G avail (16 %) | SAFE  |
| Atlas tier quota                      | 10 240 MB                                | —        |
| Atlas DB usage (masci_safety_preview) | 309.33 MB (3.0 %)                        | SAFE     |
| /tmp                                  | 3.1 M                                    | SAFE     |
| /var/log                              | 191 M                                    | SAFE     |
| Boot-time "disk at 82 % / 80 %"       | resolved by emergency-prune at boot      | SAFE NOW |
| Emergency-prune in loop?              | no — current disk 16 %                   | SAFE     |

[OPERATOR] re-confirm the live prod pod is < 75 % and that
emergency-prune is not looping.

────────────────────────────────────────────────────────────────────────────
3 · BACKUP / ROLLBACK
────────────────────────────────────────────────────────────────────────────
| Item                              | Value                                          | Severity |
|-----------------------------------|------------------------------------------------|----------|
| `BACKUP_R2_HOURLY`                | true                                           | SAFE     |
| `BACKUP_HOURS_UTC`                | 2,18                                           | SAFE     |
| R2 endpoint                       | configured (`masci-hub` bucket)                | SAFE     |
| Backup scheduler                  | inhibited by `SCHEDULER_ENABLED=false` (intent)| SAFE     |
| Atlas snapshot pre-deploy         | [OPERATOR] must record snapshot ID             | OPERATOR |
| Backup retention                  | per Atlas plan (operator-managed)              | SAFE     |
| Backup failures last 24 h         | 0 observable (scheduler off)                   | SAFE     |
| Rollback SHA                      | previous release on `main` immediately before d5a8a48 | SAFE |

NOTE: First hourly R2 backup will fire only after the operator flips
`SCHEDULER_ENABLED=true` (Track 18 directive holds it off for the
first 24 h).

────────────────────────────────────────────────────────────────────────────
4 · SCHEDULERS — INTENTIONALLY OFF
────────────────────────────────────────────────────────────────────────────
| Scheduler                              | State                          | Severity |
|----------------------------------------|--------------------------------|----------|
| transport automation scheduler         | disabled                       | SAFE (intent) |
| command digest scheduler               | disabled                       | SAFE (intent) |
| dispatch reminders                     | disabled                       | SAFE (intent) |
| Motive reliability events              | disabled                       | SAFE (intent) |
| backup scheduler                       | disabled                       | SAFE (intent) |
| asset spine scheduler                  | disabled                       | SAFE (intent) |

Singleton-lock log lines fire every 5 min confirming `SCHEDULER_ENABLED=false`.
No duplicate worker contention.
No Motive 4xx/5xx (no calls made).

[OPERATOR] re-evaluate after the 24-h soak when `SCHEDULER_ENABLED` is flipped.

────────────────────────────────────────────────────────────────────────────
5 · DB CONNECTIVITY / WRITES
────────────────────────────────────────────────────────────────────────────
| Item                                  | Value                                | Severity |
|---------------------------------------|--------------------------------------|----------|
| Atlas connection                      | OK                                   | SAFE     |
| Index bootstrap                       | completed (single boot line)         | SAFE     |
| System bootstrap                      | completed                            | SAFE     |
| Readiness gate                        | flipped                              | SAFE     |
| Public writes                         | 200 (banners, branding, usage track) | SAFE     |

────────────────────────────────────────────────────────────────────────────
6 · LOG WATCH (~10 min preview backend tail)
────────────────────────────────────────────────────────────────────────────
| Signal                                                         | Count | Severity |
|----------------------------------------------------------------|-------|----------|
| 5xx errors                                                     | 0     | SAFE     |
| 401/403 on visible operational pages                           | 0     | SAFE     |
| Frontend runtime errors / red overlays                         | 0     | SAFE     |
| Backend tracebacks (post-readiness-gate)                       | 0     | SAFE     |
| Backend tracebacks (pre-readiness-gate transient)              | 1     | WARNING (startup transient) |
| Mongo timeout                                                  | 0     | SAFE     |
| Motive API failures                                            | 0     | SAFE     |
| Scheduler failures                                             | 0     | SAFE     |
| Backup failures                                                | 0     | SAFE     |
| Disk warnings (current)                                        | 0     | SAFE     |
| nginx upstream failures (post-boot)                            | 0     | SAFE     |
| Restart loop                                                   | 0     | SAFE     |
| Public write failures                                          | 0     | SAFE     |
| CORS failures                                                  | 0     | SAFE     |
| `routes.job_photos` auto-warm 120 failed every 10 min          | 1     | WARNING (legacy job-photo rows lacking S3 keys; cleanup task tracked, non-blocking) |

The pre-readiness-gate trace was the `iter453_6_readiness_gate`
middleware raising `RuntimeError: No response returned.` once during
container warm-up. This is a known boot-window transient documented
in `/app/memory/ITER453_6_POST_DEPLOY_VERIFICATION.md` and is fully
absorbed by the readiness gate before any user traffic reaches the
worker.

────────────────────────────────────────────────────────────────────────────
7 · SENTRY
────────────────────────────────────────────────────────────────────────────
| Item                              | Value                          | Severity |
|-----------------------------------|--------------------------------|----------|
| Backend Sentry DSN                | configured (production-pointed)| SAFE     |
| Frontend Sentry DSN               | configured (production-pointed)| SAFE     |
| Sentry-reported issues last 10 m  | none observed                  | SAFE     |

────────────────────────────────────────────────────────────────────────────
8 · OVERALL HEALTH VERDICT
────────────────────────────────────────────────────────────────────────────
Backend                        SAFE
Frontend                       SAFE
Disk / Storage                 SAFE
Backup pipeline                SAFE (Atlas snapshot ID pending OPERATOR)
Schedulers                     SAFE (intentionally OFF per directive)
DB connectivity                SAFE
Log watch                      SAFE (only 1 known non-blocking warning)
Sentry                         SAFE

VERDICT: SYSTEM HEALTH GREEN on the preview artefact. Operator must
re-run the equivalent checks against the live production URL and
record the Atlas snapshot ID before declaring the deployment closed.
