"""
DNS Sentinel — Infrastructure analyzer.

Produces passive, evidence-based signals about whether an IP is likely
CDN/proxy-fronted or shared hosting. These are heuristics with named
evidence, not certainties — the platform must never infer ownership from
an IP address alone (spec Section 11), and CDN detection specifically
must reduce downstream lifecycle-classification confidence rather than
be treated as decisive on its own (spec Section 31/34).
"""
from __future__ import annotations

# Organization/network name substrings commonly associated with CDN or
# reverse-proxy providers. This is a known-incomplete heuristic list, not
# an authoritative registry — false negatives are expected and the finding
# is always phrased as "indicator", never "confirmed".
CDN_ORG_INDICATORS = [
    "cloudflare", "akamai", "fastly", "amazon", "aws", "cloudfront",
    "google", "gcp", "microsoft", "azure", "incapsula", "imperva",
    "sucuri", "stackpath", "keycdn", "bunny", "edgecast", "limelight",
    "cachefly", "cdn77",
]

SHARED_HOSTING_ORG_INDICATORS = [
    "digitalocean", "linode", "ovh", "hetzner", "godaddy", "hostgator",
    "bluehost", "namecheap", "dreamhost", "siteground", "vultr",
]


def classify_ip(organization: str | None, reverse_dns: str | None) -> dict:
    """Returns a dict of passive indicators — never a definitive ownership claim."""
    org_lower = (organization or "").lower()
    rdns_lower = (reverse_dns or "").lower()
    haystack = f"{org_lower} {rdns_lower}"

    cdn_hits = [name for name in CDN_ORG_INDICATORS if name in haystack]
    hosting_hits = [name for name in SHARED_HOSTING_ORG_INDICATORS if name in haystack]

    return {
        "is_likely_cdn": bool(cdn_hits),
        "is_likely_shared_hosting": bool(hosting_hits),
        "cdn_indicator_source": ", ".join(cdn_hits) if cdn_hits else (
            ", ".join(hosting_hits) if hosting_hits else ""
        ),
    }


def confidence_note(is_likely_cdn: bool, is_likely_shared_hosting: bool) -> str | None:
    if is_likely_cdn:
        return (
            "This IP shows indicators of CDN or reverse-proxy infrastructure. "
            "The organization/network observed here may not be the operator of "
            "the underlying service — treat any lifecycle classification for "
            "this asset with reduced confidence."
        )
    if is_likely_shared_hosting:
        return (
            "This IP shows indicators of shared hosting infrastructure. "
            "Multiple unrelated domains may share this address."
        )
    return None
