"""
DNS Sentinel — RDAP client.

RDAP (RFC 7482/9082/9083) is the modern, structured replacement for
legacy WHOIS and requires no API key. This client is intentionally
defensive: any failure (network error, timeout, non-2xx response,
malformed body, or the lookup host being unreachable — e.g. blocked by
a restrictive network egress policy) results in `available=False` and
NO fabricated ASN/organization/network data. Callers must check
`available` before trusting any ownership field, per the platform's
"never infer ownership solely from an IP address" and "do not fake
functionality" requirements.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import requests

RDAP_BOOTSTRAP_URL = "https://rdap.org/ip/{address}"
REQUEST_TIMEOUT = 6


@dataclass
class RDAPResult:
    address: str
    available: bool
    asn: Optional[str] = None
    network: Optional[str] = None
    organization: Optional[str] = None
    country: Optional[str] = None
    error: Optional[str] = None


def lookup_ip(address: str) -> RDAPResult:
    """Best-effort, passive RDAP lookup for an IP address.

    Never raises — any failure mode returns available=False with the
    error recorded, so the caller can honestly show
    "Historical/ownership data unavailable" rather than guessing.
    """
    try:
        resp = requests.get(
            RDAP_BOOTSTRAP_URL.format(address=address),
            timeout=REQUEST_TIMEOUT,
            headers={"Accept": "application/rdap+json"},
        )
    except requests.RequestException as exc:
        return RDAPResult(address=address, available=False, error=f"Network error: {exc}")

    if resp.status_code != 200:
        return RDAPResult(
            address=address, available=False,
            error=f"RDAP lookup returned HTTP {resp.status_code}",
        )

    try:
        data = resp.json()
    except ValueError:
        return RDAPResult(address=address, available=False, error="RDAP response was not valid JSON")

    try:
        network_name = data.get("name")
        handle = data.get("handle")
        country = data.get("country")

        org = None
        for entity in data.get("entities", []):
            vcard = entity.get("vcardArray")
            if vcard and len(vcard) > 1:
                for field in vcard[1]:
                    if field[0] == "fn":
                        org = field[3]
                        break
            if org:
                break
        if not org:
            org = data.get("name")

        asn = None
        for link in data.get("links", []) or []:
            if "autnum" in (link.get("href") or ""):
                asn = link["href"].rstrip("/").split("/")[-1]
                break

        return RDAPResult(
            address=address,
            available=True,
            asn=asn,
            network=network_name or handle,
            organization=org,
            country=country,
        )
    except Exception as exc:  # noqa: BLE001 - malformed RDAP body, degrade rather than crash
        return RDAPResult(address=address, available=False, error=f"Could not parse RDAP response: {exc}")
