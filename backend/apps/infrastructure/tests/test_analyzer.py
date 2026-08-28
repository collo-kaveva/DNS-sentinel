from apps.infrastructure.analyzer import classify_ip, confidence_note


class TestClassifyIP:
    def test_cloudflare_org_flagged_as_cdn(self):
        result = classify_ip("Cloudflare, Inc.", None)
        assert result["is_likely_cdn"] is True
        assert "cloudflare" in result["cdn_indicator_source"]

    def test_shared_hosting_org_flagged(self):
        result = classify_ip("DigitalOcean, LLC", None)
        assert result["is_likely_shared_hosting"] is True

    def test_unrecognized_org_flags_neither(self):
        result = classify_ip("Small Regional ISP Co", None)
        assert result["is_likely_cdn"] is False
        assert result["is_likely_shared_hosting"] is False

    def test_missing_organization_never_crashes(self):
        result = classify_ip(None, None)
        assert result["is_likely_cdn"] is False

    def test_reverse_dns_can_also_signal_cdn(self):
        result = classify_ip(None, "edge.akamai.net")
        assert result["is_likely_cdn"] is True


class TestConfidenceNote:
    def test_cdn_note_present_when_flagged(self):
        note = confidence_note(is_likely_cdn=True, is_likely_shared_hosting=False)
        assert note is not None
        assert "reduced confidence" in note

    def test_no_note_when_neither_flagged(self):
        assert confidence_note(False, False) is None
