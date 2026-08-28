"""
DNS Sentinel — Infrastructure app.

Models for IP addresses observed for a domain and the (append-only)
infrastructure observations that back them, plus CDN/proxy heuristics
and ASN/organization metadata pulled from RDAP where available.

Ownership is never inferred from an IP address alone — see
infrastructure.rdap_client and infrastructure.analyzer for the
"Current / Historical / Estimated / Unknown" labeling this app must
always apply.
"""
import uuid

from django.db import models

from apps.dns_intelligence.models import Domain


class IPAddress(models.Model):
    """Current-known snapshot of an IP address associated with a domain."""

    class AssociationStatus(models.TextChoices):
        CURRENT = "CURRENT", "Current"
        HISTORICAL = "HISTORICAL", "Historical"
        ESTIMATED = "ESTIMATED", "Estimated"
        UNKNOWN = "UNKNOWN", "Unknown"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    domain = models.ForeignKey(Domain, on_delete=models.CASCADE, related_name="ip_addresses")
    address = models.GenericIPAddressField(db_index=True)
    version = models.CharField(max_length=4, choices=[("IPv4", "IPv4"), ("IPv6", "IPv6")])
    association_status = models.CharField(
        max_length=12, choices=AssociationStatus.choices, default=AssociationStatus.UNKNOWN
    )

    reverse_dns = models.CharField(max_length=255, blank=True, null=True)

    asn = models.CharField(max_length=32, blank=True, null=True)
    network = models.CharField(max_length=255, blank=True, null=True)
    organization = models.CharField(max_length=255, blank=True, null=True)
    country = models.CharField(max_length=8, blank=True, null=True)

    is_likely_cdn = models.BooleanField(default=False)
    is_likely_shared_hosting = models.BooleanField(default=False)
    cdn_indicator_source = models.CharField(max_length=255, blank=True)

    rdap_available = models.BooleanField(
        default=False,
        help_text="False if RDAP lookup failed/unavailable — ownership fields must not be trusted.",
    )

    first_seen = models.DateTimeField(auto_now_add=True)
    last_seen = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("domain", "address")
        ordering = ["-last_seen"]

    def __str__(self):
        return f"{self.address} ({self.domain.name})"


class InfrastructureObservation(models.Model):
    """Immutable, timestamped observation of an IP's metadata at a point in time."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    domain = models.ForeignKey(Domain, on_delete=models.CASCADE, related_name="infrastructure_observations")
    address = models.GenericIPAddressField(db_index=True)
    asn = models.CharField(max_length=32, blank=True, null=True)
    network = models.CharField(max_length=255, blank=True, null=True)
    organization = models.CharField(max_length=255, blank=True, null=True)
    country = models.CharField(max_length=8, blank=True, null=True)
    reverse_dns = models.CharField(max_length=255, blank=True, null=True)
    source = models.CharField(max_length=64, default="RDAP")
    confidence = models.CharField(
        max_length=10, choices=[("HIGH", "HIGH"), ("MEDIUM", "MEDIUM"), ("LOW", "LOW")], default="MEDIUM"
    )
    lookup_succeeded = models.BooleanField(default=True)
    error_detail = models.CharField(max_length=255, blank=True)
    observed_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ["-observed_at"]
        indexes = [models.Index(fields=["domain", "address", "observed_at"])]
