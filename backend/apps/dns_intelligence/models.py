import uuid

from django.conf import settings
from django.db import models


class Domain(models.Model):
    """An authorized domain the user has added for investigation."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="domains")
    name = models.CharField(max_length=255, db_index=True)
    notes = models.TextField(blank=True)
    authorized = models.BooleanField(
        default=True,
        help_text="User attestation that they are authorized to investigate this domain.",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("owner", "name")
        ordering = ["-created_at"]

    def __str__(self):
        return self.name


class ScanJob(models.Model):
    """A background job that performs one phase of investigation for a domain."""

    class Status(models.TextChoices):
        QUEUED = "QUEUED", "Queued"
        RUNNING = "RUNNING", "Running"
        COMPLETED = "COMPLETED", "Completed"
        FAILED = "FAILED", "Failed"
        CANCELLED = "CANCELLED", "Cancelled"

    class JobType(models.TextChoices):
        DNS_DISCOVERY = "DNS_DISCOVERY", "DNS discovery"
        DNS_ANALYSIS = "DNS_ANALYSIS", "DNS analysis"
        CERTIFICATE_ANALYSIS = "CERTIFICATE_ANALYSIS", "Certificate analysis"
        INFRASTRUCTURE_ANALYSIS = "INFRASTRUCTURE_ANALYSIS", "Infrastructure analysis"
        SERVICE_OBSERVATION = "SERVICE_OBSERVATION", "Service observation"
        LIFECYCLE_CLASSIFICATION = "LIFECYCLE_CLASSIFICATION", "Lifecycle classification"
        FULL_INVESTIGATION = "FULL_INVESTIGATION", "Full investigation"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    domain = models.ForeignKey(Domain, on_delete=models.CASCADE, related_name="jobs")
    job_type = models.CharField(max_length=40, choices=JobType.choices)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.QUEUED)
    progress_steps = models.JSONField(default=list, blank=True)
    error_message = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    started_at = models.DateTimeField(null=True, blank=True)
    finished_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]


class DNSRecord(models.Model):
    """Current, latest-known DNS record for a domain/hostname + record type."""

    RECORD_TYPES = [
        ("A", "A"), ("AAAA", "AAAA"), ("CNAME", "CNAME"), ("NS", "NS"),
        ("MX", "MX"), ("TXT", "TXT"), ("SOA", "SOA"), ("CAA", "CAA"),
        ("PTR", "PTR"), ("DNSKEY", "DNSKEY"), ("DS", "DS"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    domain = models.ForeignKey(Domain, on_delete=models.CASCADE, related_name="dns_records")
    hostname = models.CharField(max_length=255, db_index=True)
    record_type = models.CharField(max_length=10, choices=RECORD_TYPES)
    value = models.TextField()
    ttl = models.IntegerField(null=True, blank=True)
    is_current = models.BooleanField(default=True)
    first_seen = models.DateTimeField(auto_now_add=True)
    last_seen = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [models.Index(fields=["hostname", "record_type"])]
        ordering = ["hostname", "record_type"]


class DNSObservation(models.Model):
    """
    An immutable, timestamped observation of a DNS query result.
    Historical observations are never overwritten — new rows are appended.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    domain = models.ForeignKey(Domain, on_delete=models.CASCADE, related_name="dns_observations")
    hostname = models.CharField(max_length=255, db_index=True)
    record_type = models.CharField(max_length=10)
    values = models.JSONField(default=list)  # list of strings, empty if NXDOMAIN/no answer
    response_code = models.CharField(max_length=20, blank=True)  # NOERROR, NXDOMAIN, SERVFAIL, TIMEOUT...
    ttl = models.IntegerField(null=True, blank=True)
    resolver_used = models.CharField(max_length=64, blank=True)
    query_time_ms = models.FloatField(null=True, blank=True)
    dnssec_signed = models.BooleanField(null=True)
    source = models.CharField(max_length=64, default="Public DNS")
    confidence = models.CharField(
        max_length=10,
        choices=[("HIGH", "HIGH"), ("MEDIUM", "MEDIUM"), ("LOW", "LOW")],
        default="HIGH",
    )
    observed_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ["-observed_at"]
        indexes = [models.Index(fields=["domain", "hostname", "record_type", "observed_at"])]


class DNSFinding(models.Model):
    """A finding produced by the DNS analyzer (missing records, DNSSEC gaps, etc.)."""

    SEVERITY = [("INFO", "INFO"), ("LOW", "LOW"), ("MEDIUM", "MEDIUM"), ("HIGH", "HIGH")]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    domain = models.ForeignKey(Domain, on_delete=models.CASCADE, related_name="dns_findings")
    severity = models.CharField(max_length=10, choices=SEVERITY)
    title = models.CharField(max_length=255)
    description = models.TextField()
    evidence = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
