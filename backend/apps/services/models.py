"""
DNS Sentinel — Service Intelligence app.

Models for service observations and metadata.
Collects only publicly observable service metadata within DNS Sentinel's authorized/public-observation scope.
Implements strict SSRF protections and conservative observation methods.
"""
import uuid

from django.db import models
from django.conf import settings

from apps.dns_intelligence.models import Domain


class Service(models.Model):
    """
    Current-known snapshot of a service for a domain/IP.
    
    This represents the latest service observation.
    Historical observations are stored in ServiceObservation.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    domain = models.ForeignKey(Domain, on_delete=models.CASCADE, related_name="services")
    
    # Service identification
    ip_address = models.GenericIPAddressField(help_text="IP address where service was observed")
    port = models.IntegerField(help_text="Port number")
    protocol = models.CharField(max_length=20, help_text="Protocol (TCP, UDP, etc.)")
    service_type = models.CharField(max_length=50, help_text="Service type (HTTP, HTTPS, SSH, etc.)")
    
    # Service status
    is_available = models.BooleanField(default=True, help_text="Whether the service is currently available")
    http_status = models.IntegerField(null=True, blank=True, help_text="HTTP status code if applicable")
    response_time_ms = models.FloatField(null=True, blank=True, help_text="Response time in milliseconds")
    
    # Service metadata
    service_banner = models.TextField(blank=True, help_text="Service banner or version information")
    ssl_tls_enabled = models.BooleanField(default=False, help_text="Whether SSL/TLS is enabled")
    
    # Collection metadata
    source = models.CharField(max_length=100, default="Service Observation", help_text="Source of service data")
    collection_timestamp = models.DateTimeField(auto_now_add=True, help_text="When this service was observed")
    
    # Timestamps
    first_observed = models.DateTimeField(auto_now_add=True)
    last_observed = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ("domain", "ip_address", "port", "protocol")
        ordering = ["-last_observed"]
        indexes = [
            models.Index(fields=["domain", "-last_observed"]),
            models.Index(fields=["ip_address", "port"]),
            models.Index(fields=["service_type"]),
            models.Index(fields=["is_available"]),
        ]
    
    def __str__(self):
        return f"{self.service_type}://{self.ip_address}:{self.port} ({self.domain.name})"


class ServiceObservation(models.Model):
    """
    Immutable, timestamped observation of a service at a point in time.
    
    Historical observations are never overwritten — new rows are appended.
    This allows tracking service changes over time.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    domain = models.ForeignKey(Domain, on_delete=models.CASCADE, related_name="service_observations")
    
    # Service identification (immutable snapshot)
    ip_address = models.GenericIPAddressField()
    port = models.IntegerField()
    protocol = models.CharField(max_length=20)
    service_type = models.CharField(max_length=50)
    
    # Service status at time of observation
    is_available = models.BooleanField(default=True)
    http_status = models.IntegerField(null=True, blank=True)
    response_time_ms = models.FloatField(null=True, blank=True)
    
    # Service metadata
    service_banner = models.TextField(blank=True)
    ssl_tls_enabled = models.BooleanField(default=False)
    
    # Collection metadata
    source = models.CharField(max_length=100, default="Service Observation")
    collection_method = models.CharField(max_length=100, blank=True, help_text="How the service was observed")
    confidence = models.CharField(
        max_length=10,
        choices=[("HIGH", "HIGH"), ("MEDIUM", "MEDIUM"), ("LOW", "LOW")],
        default="MEDIUM",
    )
    
    # Observation timestamp
    observed_at = models.DateTimeField(auto_now_add=True, db_index=True)
    
    class Meta:
        ordering = ["-observed_at"]
        indexes = [
            models.Index(fields=["domain", "ip_address", "port", "observed_at"]),
            models.Index(fields=["domain", "-observed_at"]),
            models.Index(fields=["service_type"]),
        ]
    
    def __str__(self):
        return f"{self.service_type}://{self.ip_address}:{self.port} - {self.observed_at}"
