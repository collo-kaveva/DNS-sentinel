# Roadmap

Phases mirror the build order in the original spec ("Implementation
Priority"). Phase 1–2 are complete and working end-to-end in this
repository; the rest are scaffolded but not implemented.

## ✅ Phase 1 — Foundation
Django + DRF + PostgreSQL backend, token auth, project structure, React/TS/Vite
frontend wired to real endpoints (no mock data), CORS, throttling.

## ✅ Phase 2 — DNS
Real resolver (`dnspython`) for A/AAAA/CNAME/NS/MX/TXT/SOA/CAA/DNSKEY/DS,
response codes, TTLs, query timing, best-effort DNSSEC signal, immutable
historical observations, DNS configuration analyzer with INFO/LOW/MEDIUM/HIGH
findings that correctly distinguish query failures from genuine negative
results, background job model with step-by-step progress.

## ⬜ Phase 3 — Infrastructure
- `apps/infrastructure`: `IPAddress`, `InfrastructureObservation` models
- IP metadata: ASN, network/org (via a passive WHOIS/RDAP or BGP data
  source — needs a provider decision, see below), reverse DNS
  (`resolver.reverse_lookup` already exists), CDN/proxy heuristics
- Current vs. historical vs. estimated labeling
- Asset inventory view aggregating DNS + IP data per domain

## ⬜ Phase 4 — Certificates
- `apps/certificates`: `Certificate`, `CertificateObservation` models
- TLS handshake via `ssl`/`cryptography` to pull subject, issuer, SANs,
  validity window, fingerprint from any publicly reachable HTTPS endpoint
- Certificate Transparency lookup (crt.sh) as an optional historical source,
  gracefully degrading to "Historical data unavailable" if unreachable
- Findings: expired, near-expiry, weak/legacy TLS version, hostname mismatch

## ⬜ Phase 5 — Services
- `apps/services`: `Service`, `ServiceObservation` models
- Safe HTTP(S) GET against the root path only: status, redirect chain,
  headers, server header, response time
- Explicit `Authentication required` short-circuit on 401/403 or login
  redirects — no credential attempts, ever

## ⬜ Phase 6 — Lifecycle Engine (the core research component)
- `apps/lifecycle`: `Evidence`, `LifecycleAssessment` models
- Evidence correlation across DNS + certificate + infrastructure + service
  observations
- Transparent, configurable rule-based scoring (weights stored in DB, not
  hardcoded) per the spec's Section 5 model
- Explainable output: classification, confidence %, evidence for/against,
  limitations, recommended analyst action — never a bare number
- `UNKNOWN` as a first-class outcome when evidence is insufficient or
  conflicting
- Timeline view assembled from all historical observations across apps

## ⬜ Phase 7 — Monitoring & Alerts
- `apps/monitoring` + `apps/alerts`: `MonitoringTarget`, `Alert` models
- Celery Beat periodic re-scans at user-configured intervals
- Change detection (DNS/IP/cert/service/classification diffs) → alerts
  with the evidence that triggered them

## ⬜ Phase 8 — Reporting
- `apps/reports`: `Report` model, PDF/HTML export
- Executive summary, scope, findings, evidence, limitations, recommendations
- OBSERVED vs INFERRED vs UNKNOWN labeling throughout

## ⬜ Phase 9 — Hardening
- Rate limiting tuning per-target, input validation audit, permission test
  sweep, full README/architecture docs, CI

## Open decisions before Phase 3–4 can be fully "real" (not faked)

The spec is explicit that historical/passive data sources must never be
faked. Two integrations need a decision from whoever deploys this:

1. **ASN/network ownership**: a free/passive option is RDAP
   (`https://rdap.org` or per-RIR endpoints) — no API key required, but
   rate-limited. A paid option (e.g. a commercial BGP/ASN API) would be
   more reliable for production monitoring.
2. **Certificate history**: crt.sh (Certificate Transparency) is free and
   requires no key, but has no formal SLA and can be slow/unavailable.
   If it's down, the platform should show "Historical data unavailable —
   classification confidence reduced," never synthesize a plausible-looking
   history.

Both should be implemented with graceful degradation from day one, per the
spec's Section 43 ("Do Not Fake Functionality").
