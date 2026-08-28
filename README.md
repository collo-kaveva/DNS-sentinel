# DNS Sentinel

**Public infrastructure intelligence & lifecycle classification platform.**

DNS Sentinel investigates *publicly observable* DNS, certificate, infrastructure,
and service metadata for domains you are authorized to assess, and correlates
that evidence into an explainable lifecycle classification
(`ACTIVE` / `LEGACY` / `POTENTIALLY_ABANDONED` / `LIKELY_ABANDONED` / `UNKNOWN`).

It never brute-forces credentials, bypasses authentication, exploits
vulnerabilities, or performs destructive actions against target
infrastructure. See [`docs/ETHICS.md`](docs/ETHICS.md).

## Current status: Phase 1–2 of a phased build

This repository ships a **complete, working vertical slice**, not a mockup:

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
- Background job model (`ScanJob`) with step-by-step progress, run via Celery
  in production or synchronously for testing
- React + TypeScript + Vite + Tailwind frontend wired to the real API — no
  hardcoded/mock data — with loading, empty, and error states
- 14 passing backend tests (API + analyzer unit tests, including a regression
  test for the timeout/negative-result bug found and fixed during this build)

The remaining apps (`certificates`, `infrastructure`, `services`,
`lifecycle`, `monitoring`, `alerts`, `reports`) are scaffolded (registered
Django apps with their own migrations folder) but intentionally left empty
rather than filled with fake data — see [`docs/ROADMAP.md`](docs/ROADMAP.md)
for the phase-by-phase plan to complete them, matching the spec's own
"Implementation Priority" phases.

## Project structure

```
dns-sentinel/
├── backend/
│   ├── manage.py
│   ├── config/               # settings, urls, celery app
│   ├── apps/
│   │   ├── accounts/          # auth
│   │   ├── dns_intelligence/  # DONE: resolver, analyzer, models, API, tasks, tests
│   │   ├── certificates/      # scaffolded, Phase 4
│   │   ├── infrastructure/    # scaffolded, Phase 3
│   │   ├── services/          # scaffolded, Phase 5
│   │   ├── lifecycle/         # scaffolded, Phase 6 (evidence + scoring engine)
│   │   ├── monitoring/        # scaffolded, Phase 7
│   │   ├── alerts/            # scaffolded, Phase 7
│   │   └── reports/           # scaffolded, Phase 8
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
pytest apps/dns_intelligence/tests/ -v
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

## Known limitations (current phase)

- No certificate, infrastructure, service, or lifecycle-classification
  functionality yet — those are the next phases.
- No monitoring/alerting/reporting yet.
- DNSSEC support is a best-effort passive signal (presence of DNSKEY/DS),
  not full chain-of-trust validation.
- The analyzer intentionally reports DNS query failures (timeouts,
  SERVFAIL) as their own "query failed" finding rather than inferring
  absence — treat those record types as `UNKNOWN` until a successful
  query is observed.
