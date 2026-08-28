"""
DNS Sentinel — DNS Resolution Engine.

Performs real, safe, read-only DNS queries against public resolvers using
dnspython. Does not perform recursive resolution itself (that work is
delegated to the configured public recursive resolver) — this module is
a client of that resolver, exactly like a normal DNS client.

No destructive actions. No brute-forcing. No zone transfer attempts
against unauthorized servers.
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Optional

import dns.resolver
import dns.reversename
import dns.exception
from django.conf import settings

RECORD_TYPES = ["A", "AAAA", "CNAME", "NS", "MX", "TXT", "SOA", "CAA", "DNSKEY", "DS"]


@dataclass
class QueryResult:
    hostname: str
    record_type: str
    values: list = field(default_factory=list)
    ttl: Optional[int] = None
    response_code: str = "NOERROR"
    resolver_used: str = ""
    query_time_ms: Optional[float] = None
    error: Optional[str] = None


def _build_resolver(nameserver: Optional[str] = None) -> dns.resolver.Resolver:
    resolver = dns.resolver.Resolver(configure=False)
    resolver.nameservers = [nameserver] if nameserver else list(settings.DNS_DEFAULT_RESOLVERS)
    resolver.timeout = settings.DNS_RESOLVER_TIMEOUT
    resolver.lifetime = settings.DNS_RESOLVER_LIFETIME
    return resolver


def query_record(hostname: str, record_type: str, nameserver: Optional[str] = None) -> QueryResult:
    """Perform a single, safe DNS query and return a structured result.

    Never raises for expected DNS conditions (NXDOMAIN, NoAnswer, timeout) —
    those are represented as response_code / error so callers can persist
    the observation regardless of outcome (a negative result is still a
    real, timestamped observation).
    """
    resolver = _build_resolver(nameserver)
    started = time.monotonic()
    try:
        answer = resolver.resolve(hostname, record_type, raise_on_no_answer=False)
        elapsed_ms = (time.monotonic() - started) * 1000

        if answer.rrset is None:
            return QueryResult(
                hostname=hostname,
                record_type=record_type,
                values=[],
                response_code="NOERROR_NO_ANSWER",
                resolver_used=resolver.nameservers[0],
                query_time_ms=round(elapsed_ms, 2),
            )

        values = [_format_rdata(record_type, rr) for rr in answer.rrset]
        ttl = answer.rrset.ttl
        return QueryResult(
            hostname=hostname,
            record_type=record_type,
            values=values,
            ttl=ttl,
            response_code="NOERROR",
            resolver_used=resolver.nameservers[0],
            query_time_ms=round(elapsed_ms, 2),
        )
    except dns.resolver.NXDOMAIN:
        elapsed_ms = (time.monotonic() - started) * 1000
        return QueryResult(
            hostname=hostname, record_type=record_type, values=[],
            response_code="NXDOMAIN", resolver_used=resolver.nameservers[0],
            query_time_ms=round(elapsed_ms, 2),
        )
    except dns.resolver.NoNameservers:
        return QueryResult(
            hostname=hostname, record_type=record_type, values=[],
            response_code="SERVFAIL", resolver_used=resolver.nameservers[0] if resolver.nameservers else "",
            error="No nameservers could answer the query",
        )
    except dns.exception.Timeout:
        return QueryResult(
            hostname=hostname, record_type=record_type, values=[],
            response_code="TIMEOUT", resolver_used=resolver.nameservers[0] if resolver.nameservers else "",
            error="Query timed out",
        )
    except Exception as exc:  # noqa: BLE001 - surfaced to caller, not swallowed silently
        return QueryResult(
            hostname=hostname, record_type=record_type, values=[],
            response_code="ERROR", error=str(exc),
        )


def _format_rdata(record_type: str, rr) -> str:
    if record_type == "MX":
        return f"{rr.preference} {rr.exchange}"
    if record_type == "SOA":
        return f"mname={rr.mname} rname={rr.rname} serial={rr.serial} refresh={rr.refresh} retry={rr.retry} expire={rr.expire} minimum={rr.minimum}"
    if record_type == "CAA":
        return f"{rr.flags} {rr.tag.decode() if isinstance(rr.tag, bytes) else rr.tag} {rr.value.decode() if isinstance(rr.value, bytes) else rr.value}"
    if record_type == "TXT":
        return " ".join(part.decode() if isinstance(part, bytes) else part for part in rr.strings)
    return str(rr)


def check_dnssec(hostname: str, nameserver: Optional[str] = None) -> bool:
    """Best-effort, passive DNSSEC signal: does a DNSKEY/DS record exist?"""
    resolver = _build_resolver(nameserver)
    for rtype in ("DNSKEY", "DS"):
        try:
            answer = resolver.resolve(hostname, rtype, raise_on_no_answer=False)
            if answer.rrset is not None:
                return True
        except dns.exception.DNSException:
            continue
    return False


def reverse_lookup(ip_address: str, nameserver: Optional[str] = None) -> Optional[str]:
    """Safe PTR / reverse DNS lookup."""
    resolver = _build_resolver(nameserver)
    try:
        rev_name = dns.reversename.from_address(ip_address)
        answer = resolver.resolve(rev_name, "PTR", raise_on_no_answer=False)
        if answer.rrset is None:
            return None
        return str(answer.rrset[0]).rstrip(".")
    except dns.exception.DNSException:
        return None


def resolve_all(hostname: str) -> dict[str, QueryResult]:
    """Query every supported record type for a hostname. Safe, read-only."""
    return {rtype: query_record(hostname, rtype) for rtype in RECORD_TYPES}
