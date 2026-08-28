# Ethical & Legal Use

DNS Sentinel is a **defensive, passive infrastructure intelligence tool**.
It is built to help security teams and researchers understand their own
(or explicitly authorized) public-facing infrastructure — not to attack,
enumerate, or gain access to systems belonging to others.

## Only investigate what you're authorized to investigate

Every domain added to the platform requires the user to affirmatively
attest (`authorized: true`) that they have permission to investigate it.
This is a self-attestation, not a technical control — the platform trusts
the user's representation the same way a vulnerability scanner or `dig`
does. Users are responsible for ensuring they have the legal right to
investigate any domain or infrastructure they add.

## What the platform does

- Queries public DNS resolvers, exactly as any DNS client would
- Reads publicly accessible certificate metadata from services that
  present it during a normal TLS handshake
- Observes publicly reachable HTTP(S) endpoints (status codes, headers,
  redirects, timing) — nothing behind authentication
- Correlates these public signals into an explainable, confidence-rated
  lifecycle assessment

## What the platform will never do

- Brute-force or guess credentials
- Bypass authentication or access controls
- Exploit known or suspected vulnerabilities
- Perform destructive scans (no fuzzing, no DoS-style request volume)
- Upload files to or execute commands on a target
- Attempt privilege escalation
- Retrieve private/authenticated content
- Circumvent firewalls, WAFs, or rate limits
- Present a `LIKELY_ABANDONED` classification as proof of vulnerability,
  or an `ACTIVE` classification as proof of security

If a target requires authentication, the platform stops and records:

```
Authentication required — deeper inspection unavailable.
```

## On classification language

The lifecycle engine (once built — see ROADMAP) will never claim
certainty it doesn't have. Findings use language like "likely abandoned
based on available public evidence," never "definitely abandoned."
Every classification carries a confidence percentage, supporting and
contradicting evidence, and an explicit `UNKNOWN` state for when the
evidence is genuinely insufficient.

## Reporting misuse

If you believe this platform (or a deployment of it) is being used to
investigate infrastructure without authorization, treat that the same
way you'd treat misuse of any network diagnostic tool — it is a policy
and legal question for the operator of that deployment, not something
the software itself can fully prevent.
