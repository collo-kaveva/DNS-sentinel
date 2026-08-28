"""
DNS Sentinel — DNS configuration analyzer.

Produces explainable, evidence-backed findings from currently-observed
DNS records. This module is deliberately conservative: it will not label
a configuration "vulnerable" without direct supporting evidence, and it
never asserts abandonment — that is the job of the lifecycle engine,
which combines this signal with certificate, infrastructure, and service
evidence.
"""
from __future__ import annotations

from typing import Iterable


FAILURE_CODES = {"TIMEOUT", "SERVFAIL", "ERROR"}


def _failed(result) -> bool:
    """True if the query itself failed (network/server issue) rather than
    returning a genuine negative result (NXDOMAIN / NOERROR_NO_ANSWER)."""
    return bool(result) and result.response_code in FAILURE_CODES


def analyze_records(records: dict) -> list[dict]:
    """records: {record_type: QueryResult-like dict with .values / .response_code}

    Queries that failed (timeout, SERVFAIL, error) are never treated as a
    confirmed absence of a record — that would misrepresent an UNKNOWN
    result as an OBSERVED negative. Failures are surfaced as their own
    finding instead.
    """
    findings: list[dict] = []

    a = records.get("A")
    aaaa = records.get("AAAA")
    ns = records.get("NS")
    mx = records.get("MX")
    txt = records.get("TXT")
    caa = records.get("CAA")
    soa = records.get("SOA")

    failed_types = [rt for rt, r in records.items() if _failed(r)]
    if failed_types:
        findings.append({
            "severity": "LOW",
            "title": f"DNS query failed for: {', '.join(failed_types)}",
            "description": (
                "These queries did not return a result due to a timeout or "
                "server error, not a confirmed absence of the record. "
                "Treat coverage for these record types as UNKNOWN and retry."
            ),
            "evidence": {rt: records[rt].response_code for rt in failed_types},
        })

    # No current resolution at all (only counts genuine negative results,
    # not failed queries)
    if (not a or _failed(a) or not a.values) and (not aaaa or _failed(aaaa) or not aaaa.values) \
            and not (_failed(a) or _failed(aaaa)):
        findings.append({
            "severity": "MEDIUM",
            "title": "No current A/AAAA record",
            "description": (
                "No IPv4 or IPv6 address currently resolves for this hostname. "
                "This alone does not confirm abandonment — the record may have "
                "been intentionally decommissioned, or resolution may be "
                "temporarily unavailable."
            ),
            "evidence": {"A": a.response_code if a else None, "AAAA": aaaa.response_code if aaaa else None},
        })

    if aaaa and not _failed(aaaa) and not aaaa.values:
        findings.append({
            "severity": "INFO",
            "title": "No IPv6 (AAAA) record",
            "description": "IPv6 is not configured. Common and not inherently a problem.",
            "evidence": {},
        })

    if ns and not _failed(ns) and len(ns.values) < 2:
        findings.append({
            "severity": "LOW",
            "title": "Fewer than 2 authoritative nameservers observed",
            "description": "Best practice recommends at least two independent authoritative nameservers for redundancy.",
            "evidence": {"NS": ns.values},
        })

    if mx and not _failed(mx) and not mx.values:
        findings.append({
            "severity": "INFO",
            "title": "No MX record",
            "description": "No mail exchanger configured. May be intentional if the domain does not receive mail.",
            "evidence": {},
        })

    if txt and not _failed(txt):
        if txt.values:
            spf_present = any(v.lower().startswith("v=spf1") for v in txt.values)
            if not spf_present:
                findings.append({
                    "severity": "LOW",
                    "title": "No SPF record detected in TXT records",
                    "description": "No v=spf1 TXT record was found at the apex. If this domain sends mail, absence of SPF can weaken anti-spoofing posture.",
                    "evidence": {},
                })
        else:
            findings.append({
                "severity": "INFO",
                "title": "No TXT records observed",
                "description": "No SPF/verification TXT records found at the apex.",
                "evidence": {},
            })

    if caa and not _failed(caa) and not caa.values:
        findings.append({
            "severity": "LOW",
            "title": "No CAA record",
            "description": "No Certificate Authority Authorization record restricts which CAs may issue certificates for this domain.",
            "evidence": {},
        })

    if soa and soa.response_code not in ("NOERROR",) and not _failed(soa):
        findings.append({
            "severity": "HIGH",
            "title": "SOA record could not be retrieved",
            "description": "Unable to retrieve the Start of Authority record, which may indicate a delegation or authoritative-server problem.",
            "evidence": {"response_code": soa.response_code},
        })

    return findings


def dmarc_lookup_hostname(hostname: str) -> str:
    return f"_dmarc.{hostname}"
