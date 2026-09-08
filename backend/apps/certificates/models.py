"""
DNS Sentinel — Certificate Intelligence app.

Models for TLS/SSL certificate observations and metadata.
Collects passive/public TLS metadata only with strict safety controls.
"""
import uuid

from django.db import models
from django.conf import settings

from apps.dns_intelligence.models import Domain


class Certificate(models.Model):
    """
    Current-known snapshot of a certificate for a domain.
    
    This represents the latest certificate observed for a domain.
    Historical observations are stored in CertificateObservation.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    domain = models.ForeignKey(Domain, on_delete=models.CASCADE, related_name="certificates")
    
    # Certificate identification
    subject = models.CharField(max_length=255, help_text="Certificate subject (CN or SAN)")
    issuer = models.CharField(max_length=255, help_text="Certificate issuer")
    serial_number = models.CharField(max_length=64, help_text="Certificate serial number")
    fingerprint = models.CharField(max_length=64, help_text="SHA-1 fingerprint")
    fingerprint_sha256 = models.CharField(max_length=64, help_text="SHA-256 fingerprint")
    
    # Validity period
    valid_from = models.DateTimeField(help_text="Certificate validity start")
    valid_until = models.DateTimeField(help_text="Certificate validity end")
    
    # Subject Alternative Names
    sans = models.JSONField(default=list, help_text="List of Subject Alternative Names")
    
    # Public key information
    public_key_algorithm = models.CharField(max_length=50, blank=True, help_text="Public key algorithm (RSA, ECDSA, etc.)")
    public_key_size = models.IntegerField(null=True, blank=True, help_text="Public key size in bits")
    
    # TLS information
    tls_version = models.CharField(max_length=20, blank=True, help_text="TLS version used")
    cipher_suite = models.CharField(max_length=100, blank=True, help_text="Cipher suite used")
    
    # Status
    is_valid = models.BooleanField(default=True, help_text="Whether the certificate is currently valid")
    is_expired = models.BooleanField(default=False, help_text="Whether the certificate has expired")
    is_self_signed = models.BooleanField(default=False, help_text="Whether the certificate is self-signed")
    
    # Collection metadata
    source = models.CharField(max_length=100, default="TLS Handshake", help_text="Source of certificate data")
    collection_timestamp = models.DateTimeField(auto_now_add=True, help_text="When this certificate was collected")
    
    # Timestamps
    first_seen = models.DateTimeField(auto_now_add=True)
    last_seen = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ("domain", "fingerprint_sha256")
        ordering = ["-last_seen"]
        indexes = [
            models.Index(fields=["domain", "-last_seen"]),
            models.Index(fields=["valid_until"]),
            models.Index(fields=["issuer"]),
        ]
    
    def __str__(self):
        return f"{self.subject} ({self.domain.name})"


class CertificateObservation(models.Model):
    """
    Immutable, timestamped observation of a certificate at a point in time.
    
    Historical observations are never overwritten — new rows are appended.
    This allows tracking certificate changes over time.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    domain = models.ForeignKey(Domain, on_delete=models.CASCADE, related_name="certificate_observations")
    
    # Certificate identification (immutable snapshot)
    subject = models.CharField(max_length=255)
    issuer = models.CharField(max_length=255)
    serial_number = models.CharField(max_length=64)
    fingerprint = models.CharField(max_length=64)
    fingerprint_sha256 = models.CharField(max_length=64)
    
    # Validity period
    valid_from = models.DateTimeField()
    valid_until = models.DateTimeField()
    
    # Subject Alternative Names
    sans = models.JSONField(default=list)
    
    # Public key information
    public_key_algorithm = models.CharField(max_length=50, blank=True)
    public_key_size = models.IntegerField(null=True, blank=True)
    
    # TLS information
    tls_version = models.CharField(max_length=20, blank=True)
    cipher_suite = models.CharField(max_length=100, blank=True)
    
    # Status at time of observation
    is_valid = models.BooleanField(default=True)
    is_expired = models.BooleanField(default=False)
    is_self_signed = models.BooleanField(default=False)
    
    # Collection metadata
    source = models.CharField(max_length=100, default="TLS Handshake")
    collection_method = models.CharField(max_length=100, blank=True, help_text="How the certificate was collected")
    confidence = models.CharField(
        max_length=10,
        choices=[("HIGH", "HIGH"), ("MEDIUM", "MEDIUM"), ("LOW", "LOW")],
        default="HIGH",
    )
    
    # Observation timestamp
    observed_at = models.DateTimeField(auto_now_add=True, db_index=True)
    
    class Meta:
        ordering = ["-observed_at"]
        indexes = [
            models.Index(fields=["domain", "fingerprint_sha256", "observed_at"]),
            models.Index(fields=["domain", "-observed_at"]),
            models.Index(fields=["valid_until"]),
        ]
    
    def __str__(self):
        return f"{self.subject} - {self.observed_at}"
