"""
Unit tests for the DNS analyzer using local fixtures.

These never touch the network — they build QueryResult-like fixtures
directly, matching Phase 33's "safe testing mode" requirement so the
analyzer can be validated without scanning real third-party infrastructure.
"""
import pytest
from dataclasses import dataclass, field


@dataclass
class FakeResult:
    hostname: str = "example.com"
    record_type: str = "A"
    values: list = field(default_factory=list)
    response_code: str = "NOERROR"
    ttl: int = 300


def make_records(**overrides):
    base = {
        "A": FakeResult(record_type="A", values=["203.0.113.10"]),
        "AAAA": FakeResult(record_type="AAAA", values=["2001:db8::1"]),
        "NS": FakeResult(record_type="NS", values=["ns1.example.com.", "ns2.example.com."]),
        "MX": FakeResult(record_type="MX", values=["10 mail.example.com."]),
        "TXT": FakeResult(record_type="TXT", values=["v=spf1 -all"]),
        "SOA": FakeResult(record_type="SOA", values=["mname=ns1.example.com."]),
        "CAA": FakeResult(record_type="CAA", values=["0 issue letsencrypt.org"]),
    }
    base.update(overrides)
    return base


class TestAnalyzeRecords:
    def test_healthy_domain_produces_no_high_findings(self):
        from apps.dns_intelligence.analyzer import analyze_records
        findings = analyze_records(make_records())
        assert all(f["severity"] != "HIGH" for f in findings)

    def test_no_a_or_aaaa_flags_medium(self):
        from apps.dns_intelligence.analyzer import analyze_records
        recs = make_records(
            A=FakeResult(record_type="A", values=[], response_code="NXDOMAIN"),
            AAAA=FakeResult(record_type="AAAA", values=[], response_code="NXDOMAIN"),
        )
        findings = analyze_records(recs)
        titles = [f["title"] for f in findings]
        assert "No current A/AAAA record" in titles

    def test_timeout_is_never_reported_as_confirmed_absence(self):
        """Regression test: a TIMEOUT must not be conflated with a genuine
        negative (NXDOMAIN / empty answer). See analyzer._failed()."""
        from apps.dns_intelligence.analyzer import analyze_records
        recs = make_records(
            TXT=FakeResult(record_type="TXT", values=[], response_code="TIMEOUT")
        )
        findings = analyze_records(recs)
        titles = [f["title"] for f in findings]
        assert "No TXT records observed" not in titles
        assert "No SPF record detected in TXT records" not in titles
        assert any("DNS query failed" in t for t in titles)

    def test_single_nameserver_flagged_low(self):
        from apps.dns_intelligence.analyzer import analyze_records
        recs = make_records(NS=FakeResult(record_type="NS", values=["ns1.example.com."]))
        findings = analyze_records(recs)
        assert any("nameserver" in f["title"].lower() for f in findings)

    def test_missing_spf_flagged_when_txt_present_but_no_spf(self):
        from apps.dns_intelligence.analyzer import analyze_records
        recs = make_records(TXT=FakeResult(record_type="TXT", values=["some-verification=abc123"]))
        findings = analyze_records(recs)
        assert any("SPF" in f["title"] for f in findings)

    def test_no_caa_flagged_low(self):
        from apps.dns_intelligence.analyzer import analyze_records
        recs = make_records(CAA=FakeResult(record_type="CAA", values=[]))
        findings = analyze_records(recs)
        assert any("CAA" in f["title"] for f in findings)
