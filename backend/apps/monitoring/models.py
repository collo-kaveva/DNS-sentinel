"""
DNS Sentinel — Monitoring app.

Models for monitoring configuration, change detection, and monitoring history.
Integrates with existing ScanJob, Evidence, and observation systems.
"""
import uuid
from django.db import models
from django.conf import settings

from apps.dns_intelligence.models import Domain


class MonitoringConfig(models.Model):
    """
    Monitoring configuration for a domain.
    
    This model stores what aspects of a domain should be monitored,
    how frequently, and by whom. Per-user ownership is enforced.
    """
    class MonitorType(models.TextChoices):
        DNS = "DNS", "DNS"
        IP = "IP", "IP Address"
        CERTIFICATE = "CERTIFICATE", "Certificate"
        SERVICE = "SERVICE", "Service"
        ASN = "ASN", "ASN/Provider"
        LIFECYCLE = "LIFECYCLE", "Lifecycle"
    
    class Frequency(models.TextChoices):
        HOURLY = "HOURLY", "Hourly"
        DAILY = "DAILY", "Daily"
        WEEKLY = "WEEKLY", "Weekly"
        MONTHLY = "MONTHLY", "Monthly"
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Ownership
    domain = models.ForeignKey(Domain, on_delete=models.CASCADE, related_name="monitoring_configs")
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="monitoring_configs")
    
    # Monitoring configuration
    monitor_type = models.CharField(max_length=20, choices=MonitorType.choices)
    is_enabled = models.BooleanField(default=True)
    frequency = models.CharField(max_length=20, choices=Frequency.choices, default=Frequency.DAILY)
    
    # Alert configuration
    alert_on_change = models.BooleanField(default=True)
    alert_on_failure = models.BooleanField(default=False)
    
    # Scheduling
    next_check_scheduled = models.DateTimeField(null=True, blank=True, db_index=True)
    last_check_completed = models.DateTimeField(null=True, blank=True)
    
    # Metadata
    notes = models.TextField(blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ("domain", "monitor_type", "owner")
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["domain", "monitor_type"]),
            models.Index(fields=["owner", "is_enabled"]),
            models.Index(fields=["next_check_scheduled"]),
        ]
    
    def __str__(self):
        return f"{self.domain.name} - {self.monitor_type} ({'enabled' if self.is_enabled else 'disabled'})"


class MonitoringResult(models.Model):
    """
    Result of a monitoring check.
    
    This model stores the actual results of monitoring jobs,
    including the observation, evidence reference, and any changes detected.
    """
    class CheckStatus(models.TextChoices):
        SUCCESS = "SUCCESS", "Success"
        FAILURE = "FAILURE", "Failure"
        PARTIAL = "PARTIAL", "Partial"
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Context
    domain = models.ForeignKey(Domain, on_delete=models.CASCADE, related_name="monitoring_results")
    monitoring_config = models.ForeignKey(MonitoringConfig, on_delete=models.CASCADE, related_name="results")
    
    # Check information
    monitor_type = models.CharField(max_length=20, choices=MonitoringConfig.MonitorType.choices)
    status = models.CharField(max_length=20, choices=CheckStatus.choices)
    
    # Observation reference
    observation_id = models.UUIDField(null=True, blank=True, help_text="ID of the observation this check is based on")
    observation_type = models.CharField(max_length=50, blank=True, help_text="Type of observation (DNSObservation, etc.)")
    
    # State comparison
    previous_state = models.JSONField(default=dict, blank=True, help_text="Previous state snapshot")
    new_state = models.JSONField(default=dict, blank=True, help_text="New state snapshot")
    has_changes = models.BooleanField(default=False)
    
    # Evidence reference
    evidence_id = models.UUIDField(null=True, blank=True, help_text="Evidence ID for this observation")
    
    # Job reference
    scan_job_id = models.UUIDField(null=True, blank=True, help_text="ScanJob that performed this check")
    
    # Error information
    error_message = models.TextField(blank=True)
    
    # Timing
    check_started_at = models.DateTimeField()
    check_completed_at = models.DateTimeField()
    duration_seconds = models.FloatField(null=True, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    
    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["domain", "-created_at"]),
            models.Index(fields=["monitoring_config", "-created_at"]),
            models.Index(fields=["monitor_type", "-created_at"]),
            models.Index(fields=["status"]),
            models.Index(fields=["has_changes"]),
        ]
    
    def __str__(self):
        return f"{self.domain.name} - {self.monitor_type} - {self.status} ({self.created_at})"


class ChangeEvent(models.Model):
    """
    Detected change event from monitoring.
    
    This model stores actual changes detected during monitoring,
    with proper evidence backing. Only created when real differences exist.
    """
    class EventType(models.TextChoices):
        DNS_RECORD_ADDED = "DNS_RECORD_ADDED", "DNS Record Added"
        DNS_RECORD_REMOVED = "DNS_RECORD_REMOVED", "DNS Record Removed"
        DNS_RECORD_CHANGED = "DNS_RECORD_CHANGED", "DNS Record Changed"
        IP_CHANGED = "IP_CHANGED", "IP Changed"
        CERTIFICATE_CHANGED = "CERTIFICATE_CHANGED", "Certificate Changed"
        CERTIFICATE_EXPIRED = "CERTIFICATE_EXPIRED", "Certificate Expired"
        SERVICE_APPEARED = "SERVICE_APPEARED", "Service Appeared"
        SERVICE_DISAPPEARED = "SERVICE_DISAPPEARED", "Service Disappeared"
        ASN_CHANGED = "ASN_CHANGED", "ASN Changed"
        PROVIDER_CHANGED = "PROVIDER_CHANGED", "Provider Changed"
        LIFECYCLE_CHANGED = "LIFECYCLE_CHANGED", "Lifecycle Changed"
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Context
    domain = models.ForeignKey(Domain, on_delete=models.CASCADE, related_name="change_events")
    monitoring_result = models.ForeignKey(MonitoringResult, on_delete=models.CASCADE, related_name="change_events")
    
    # Event information
    event_type = models.CharField(max_length=50, choices=EventType.choices)
    description = models.TextField(help_text="Human-readable description of the change")
    
    # State details
    previous_value = models.TextField(blank=True, help_text="Previous value (serialized if complex)")
    new_value = models.TextField(blank=True, help_text="New value (serialized if complex)")
    
    # Entity information
    entity_name = models.CharField(max_length=255, blank=True, help_text="Name of the entity that changed")
    entity_type = models.CharField(max_length=50, blank=True, help_text="Type of entity (DNS record, IP, etc.)")
    
    # Evidence reference
    evidence_id = models.UUIDField(null=True, blank=True, help_text="Evidence ID backing this change")
    
    # Alert generation
    alert_generated = models.BooleanField(default=False)
    alert_id = models.UUIDField(null=True, blank=True, help_text="Alert generated from this event")
    
    # Metadata
    metadata = models.JSONField(default=dict, blank=True, help_text="Additional event metadata")
    
    # Timestamps
    detected_at = models.DateTimeField(auto_now_add=True, db_index=True)
    
    class Meta:
        ordering = ["-detected_at"]
        indexes = [
            models.Index(fields=["domain", "-detected_at"]),
            models.Index(fields=["monitoring_result", "-detected_at"]),
            models.Index(fields=["event_type", "-detected_at"]),
            models.Index(fields=["alert_generated"]),
        ]
    
    def __str__(self):
        return f"{self.domain.name} - {self.event_type} ({self.detected_at})"
