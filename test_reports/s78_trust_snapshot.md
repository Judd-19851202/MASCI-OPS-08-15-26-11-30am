# MASCI Platform · Trust Snapshot

- Generated: **Jul 10, 2026, 1:11 AM** (your local time)
- Overall posture: **LOADING**
- Healthy: 4 · Attention: 1 · Critical: 3 · Needs wiring: 0 · Total domains: 10

## Domains

### 01 · Platform Overview · HEALTHY
- Canonical route: `/admin/executive-overview`
- Source endpoint: `/api/version`
- Metric: **0h 1m**
- Detail: Build 57d90d77 · masci-hub

### 02 · Operations Control Center · LOADING
- Canonical route: `/admin/operations-control`
- Source endpoint: `/api/admin/operations-control/overview`

### 03 · Storage & Recovery · CRITICAL
- Canonical route: `/admin/storage-recovery`
- Source endpoint: `/api/admin/recovery/snapshot`
- Metric: **0.7m**
- Detail: Backup age · target ≤ 1440m · 91 archives

### 04 · AI Operations · ATTENTION
- Canonical route: `/admin/ai-operations`
- Source endpoint: `/api/ai/gateway/status`
- Metric: **ANTHROPIC**
- Detail: Gateway ON · provider unavailable

### 05 · Communications · HEALTHY
- Canonical route: `/admin/communications`
- Source endpoint: `/api/admin/email-routing/v2/status`
- Metric: **V2**
- Detail: 49 routes configured

### 06 · Identity & Security · HEALTHY
- Canonical route: `/admin/identity-security`
- Source endpoint: `/api/admin/sessions/recent`
- Metric: **50**
- Detail: 50 active session(s) · timeouts on

### 07 · Governance & Trust · CRITICAL
- Canonical route: `/admin/governance-trust`
- Source endpoint: `/api/admin/governance/summary`
- Metric: **0%**
- Detail: 38 high/critical · 0 rules tracked

### 08 · Platform Configuration · CRITICAL
- Canonical route: `/admin/platform-configuration`
- Source endpoint: `/api/admin/integrations/health`
- Metric: **4/6**
- Detail: 2 integration(s) degraded

### 09 · Diagnostics · HEALTHY
- Canonical route: `/admin/diagnostics`
- Source endpoint: `/api/health`
- Metric: **OK**
- Detail: Service reporting healthy

### 10 · Maintenance · LOADING
- Canonical route: `/admin/maintenance`
- Source endpoint: `/api/admin/operations-control/overview`

---
Snapshot generated from live probes on the Admin OS landing at /admin. No secrets included; only summarized status, metrics, and source endpoints.