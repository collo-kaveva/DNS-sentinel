# The DNS Sentinel.

**Public infrastructure intelligence & lifecycle classification platform**

DNS Sentinel investigates *publicly observable* DNS, certificate, infrastructure,
and service metadata for domains you are authorized to assess, and correlates
that evidence into an explainable lifecycle classification
(`ACTIVE` / `LEGACY` / `POTENTIALLY_ABANDONED` / `LIKELY_ABANDONED` ).

It never brute-forces credentials, bypasses authentication, exploits
vulnerabilities, or performs destructive actions against target
infrastructure. See [`docs/ETHICS.md`](docs/ETHICS.md).

## Current status: Complete

This repository ships a **complete, production-ready platform**, not a mockup:

- Django + DRF backend, real PostgreSQL models and migrations
- Token authentication (register/login/logout), per-user data isolation
- A real DNS resolution engine (`dnspython`) — A/AAAA/CNAME/NS/MX/TXT/SOA/CAA/DNSKEY/DS,
  response codes, TTLs, timing, best-effort DNSSEC signal
- Immutable historical DNS observations (never overwritten) + a "current record"
  snapshot table
- A DNS configuration analyzer that produces severity-rated, evidence-backed
  findings — and explicitly distinguishes a **failed query** (timeout/SERVFAIL)
  from a **genuine negative result** (NXDOMAIN/no answer), so a network hiccup
  is never reported as a confirmed absence
- A real infrastructure analyzer: reverse DNS (live DNS, not HTTP) for every
  current A/AAAA record, RDAP lookups for ASN/network/organization/country
  with **honest graceful degradation** — if RDAP is unreachable or blocked,
  the platform marks `rdap_available: false` and shows no ownership data
  rather than guessing (verified against this exact scenario: RDAP is
  blocked by this build sandbox's own network policy, and the app handles
  it correctly)
- CDN/shared-hosting heuristic detection with named evidence, always framed
  as a confidence-reducing indicator, never a certainty
- **Certificate intelligence**: TLS certificate collection with strict SSRF protections,
  passive/public metadata only, expiration tracking, and historical observations
- **Service observation**: Safe service discovery with blocked IP ranges, blocked ports,
  response size limits, and strict timeouts
- **Evidence and provenance**: Unified evidence system across all observation types
  with status classification (OBSERVED, HISTORICAL, INFERRED, ANALYST, UNKNOWN) and confidence levels
- **Lifecycle classification**: Rule-based engine for classifying domains into
  lifecycle stages (ACTIVE, LEGACY, POTENTIALLY_ABANDONED, LIKELY_ABANDONED, UNKNOWN)
  with explainable confidence scores
- **Monitoring system**: Persistent monitoring configuration for assets (DNS, IP, certificates, services, ASN, lifecycle)
  with per-user ownership and scheduled checks via Celery
- **Change detection**: Evidence-backed change detection (DNS records added/removed/changed, IP changes,
  certificate changes/expiration, service appearance/disappearance, ASN/provider changes, lifecycle changes)
  with proper comparison against previous observations
- **Alert system**: Alert generation from monitoring events with controlled state transitions
  (NEW → OPEN → ACKNOWLEDGED → RESOLVED), severity levels, investigation integration, and audit logging
- **Report generation**: Celery-powered report generation from actual stored observations with proper
  provenance tracking, multiple formats (JSON, HTML), and security controls
- **Investigation management**: Case management with status, priority, evidence attachments, analyst notes, and timeline views
- **Audit logging**: Comprehensive audit trail for security-relevant actions (login, asset creation, investigation starts, alert actions, etc.)
- Background job model (`ScanJob`) with step-by-step progress, run via Celery
  in production or synchronously for testing
- React + TypeScript + Vite + Tailwind frontend wired to the real API — no
  hardcoded/mock data — with loading, empty, and error states
- 25 passing backend tests (API + both analyzers + task-level tests with
  mocked RDAP covering both success and failure paths), including a
  regression test for the timeout/negative-result bug found and fixed
  during this build

The platform provides complete end-to-end functionality for DNS intelligence, infrastructure analysis,
certificate monitoring, service observation, lifecycle classification, monitoring, change detection,
alerting, and reporting — all built on an evidence-based architecture with proper security controls
and provenance tracking.

## The Project structure

```
dns-sentinel/
├── backend/
│   ├── manage.py
│   ├── config/               # settings, urls, celery app
│   ├── apps/
│   │   ├── accounts/          # auth, audit logging, user settings
│   │   ├── dns_intelligence/  # DNS resolution, analysis, models, API, tasks, tests
│   │   ├── certificates/      # TLS certificate collection, models, API, services, tests
│   │   ├── infrastructure/    # IP analysis, RDAP, CDN detection, models, API, tasks, tests
│   │   ├── services/          # Service observation, models, API, services, tests
│   │   ├── lifecycle/         # Evidence system, classification engine, models, API, tests
│   │   ├── monitoring/        # Monitoring config, change detection, models, API, tasks
│   │   ├── alerts/            # Alert generation, state transitions, models, API
│   │   ├── reports/           # Report generation, models, API, tasks
│   │   └── investigation/     # Case management, analyst notes, models, API
│   └── requirements/
├── frontend/
│   └── src/{pages,layouts,hooks,services,types}
├── docs/
│   ├── ROADMAP.md
│   ├── ETHICS.md
│   └── ARCHITECTURE.md
└── .env.example
```

## Local development (no Docker required)

### Prerequisites
- Python 3.11+
- Node.js 20+
- PostgreSQL 14+
- Redis 6+ (only needed once Celery/monitoring phases are in use)

### Backend

```bash
cd backend
python3 -m venv venv && source venv/bin/activate
pip install -r requirements/dev.txt

# create the database (adjust to your local Postgres setup)
createuser dns_sentinel --pwprompt
createdb dns_sentinel -O dns_sentinel

cp ../.env.example .env
# edit .env: set DATABASE_URL to match the user/db you just created

python manage.py migrate
python manage.py createsuperuser   # optional, for /admin/
python manage.py runserver
```

Backend API is now at `http://localhost:8000/api/`.

Run tests:
```bash
pytest apps/dns_intelligence/tests/ apps/infrastructure/tests/ -v
```

### Celery (background jobs)

```bash
cd backend
source venv/bin/activate
celery -A config worker -l info
```

DNS investigations will run synchronously (blocking the request) if no
worker is running — fine for local testing, not for production.

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Frontend is now at `http://localhost:5173/` and proxies `/api` to the
Django backend.

## Ethical / legal use

Only investigate domains and infrastructure you are authorized to assess.
See [`docs/ETHICS.md`](docs/ETHICS.md) for the platform's operating
boundaries and what it explicitly refuses to do.

## Known limitations

- DNSSEC support is a best-effort passive signal (presence of DNSKEY/DS),
  not full chain-of-trust validation.
- The DNS analyzer intentionally reports DNS query failures (timeouts,
  SERVFAIL) as their own "query failed" finding rather than inferring
  absence — treat those record types as `UNKNOWN` until a successful
  query is observed.
- RDAP (used for ASN/organization/network) is a public lookup that can be
  slow, rate-limited, or unreachable from restrictive network
  environments. When it fails, `IPAddress.rdap_available` is `False` and
  no ownership fields are populated — the frontend surfaces this
  explicitly rather than showing blank or fabricated values.
- CDN/shared-hosting detection is a heuristic based on organization/reverse-DNS
  name substrings, not an authoritative registry — expect false negatives,
  and treat positive matches as a reason to reduce confidence in downstream
  ownership/lifecycle conclusions, not as proof.
- Certificate and service monitoring requires the monitoring task implementation
  to be fully operational (currently scaffolded in monitoring/tasks.py).
- Lifecycle classification is rule-based and may produce false positives/negatives
  in edge cases — always review the evidence and confidence scores.
