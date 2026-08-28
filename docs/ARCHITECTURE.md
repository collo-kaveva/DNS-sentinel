# Architecture

## Data flow (current: DNS phase)

```
React frontend (Vite dev proxy → /api)
        │  fetch + Token auth header
        ▼
Django REST Framework
        │
        ├── apps.accounts        — register/login/logout/me (DRF TokenAuth)
        │
        └── apps.dns_intelligence
                ├── models.py     — Domain, ScanJob, DNSRecord,
                │                   DNSObservation (immutable, append-only),
                │                   DNSFinding
                ├── resolver.py   — dnspython client: safe, read-only queries
                │                   against configured public resolvers
                ├── analyzer.py   — pure function: QueryResult dict → findings
                ├── tasks.py      — Celery task orchestrating discovery +
                │                   analysis, updates ScanJob.progress_steps
                └── views.py      — DomainViewSet (+ nested actions: dns/,
                                    observations/, findings/, jobs/,
                                    investigate/)
```

## Why observations are append-only

`DNSObservation` rows are never updated or deleted by normal operation —
each resolution creates a new timestamped row. `DNSRecord` is a derived
"current snapshot" table (old rows flipped to `is_current=False`, new ones
inserted) used for fast "what does this resolve to right now" queries.
This split is what will let the Phase 6 lifecycle engine build an honest
timeline later without re-querying live DNS for historical state.

## Why query failures are modeled separately from negative results

`DNSObservation.response_code` distinguishes `NOERROR` /
`NOERROR_NO_ANSWER` / `NXDOMAIN` (genuine results) from `TIMEOUT` /
`SERVFAIL` / `ERROR` (the query itself failed). `analyzer.py` only draws
conclusions from genuine results — see `analyzer._failed()`. This was a
real bug found and fixed during this build (a TXT query timeout was
initially reported as "no TXT records observed"); the regression test in
`tests/test_analyzer.py::test_timeout_is_never_reported_as_confirmed_absence`
guards against it recurring, and the same failed/negative distinction
should be carried into every future analyzer (certificates, infrastructure,
services) and ultimately into the lifecycle scoring engine, where
conflating "we couldn't check" with "it's not there" would directly
undermine the platform's core promise of not over-claiming abandonment.

## Background jobs

`ScanJob` tracks phase-by-phase progress (`progress_steps`, a JSON list of
`{label, status}`). The Celery task updates it as it goes so the frontend
can poll and render a step-by-step progress view. In this phase there's
one job type (`DNS_DISCOVERY`, which also runs analysis); later phases add
`CERTIFICATE_ANALYSIS`, `INFRASTRUCTURE_ANALYSIS`, `SERVICE_OBSERVATION`,
`LIFECYCLE_CLASSIFICATION`, and a `FULL_INVESTIGATION` job type that chains
them.

## Auth & isolation

DRF `TokenAuthentication`. Every queryset in `dns_intelligence` is filtered
by `owner=request.user` (directly on `Domain`, via `domain__owner` on
everything else) — verified by `test_domain_scoped_to_owner`.

## Safety controls already in place

- `SCAN_MAX_CONCURRENT_TARGETS`, `SCAN_REQUEST_DELAY_SECONDS`,
  `DNS_RESOLVER_TIMEOUT`/`LIFETIME` in settings — used to keep the resolver
  well-behaved.
- DRF throttle scope `scan` (10/min) applied specifically to the
  `investigate` action, separate from general API throttling.
- `authorized` flag required and enforced server-side (403 if false) before
  any investigation can run.
