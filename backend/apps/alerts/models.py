"""
DNS Sentinel — Alerts app.

Models for alert management, including alert generation from monitoring events,
state transitions, and investigation integration.
"""
import uuid
from django.db import models
from django.conf import settings
from django.utils import timezone

from apps.dns_intelligence.models import Domain


class Alert(models.Model):
    """
    Alert model for tracking security-relevant events from monitoring.
    
    Alerts are generated from real monitoring events with evidence backing.
    They support controlled state transitions and investigation integration.
    """
    class Status(models.TextChoices):
        NEW = "NEW", "New"
        OPEN = "OPEN", "Open"
        ACKNOWLEDGED = "ACKNOWLEDGED", "Acknowledged"
        RESOLVED = "RESOLVED", "Resolved"
        DISMISSED = "DISMISSED", "Dismissed"
    
    class Severity(models.TextChoices):
        INFO = "INFO", "Informational"
        LOW = "LOW", "Low"
        MEDIUM = "MEDIUM", "Medium"
        HIGH = "HIGH", "High"
        CRITICAL = "CRITICAL", "Critical"
    
    class AlertType(models.TextChoices):
        DNS_RECORD_ADDED = "DNS_RECORD_ADDED", "DNS Record Added"
        DNS_RECORD_REMOVED = "DNS_RECORD_REMOVED", "DNS Record Removed"
        DNS_RECORD_CHANGED = "DNS_RECORD_CHANGED", "DNS Record Changed"
        IP_CHANGED = "IP_CHANGED", "IP Changed"
        CERTIFICATE_CHANGED = "CERTIFICATE_CHANGED", "Certificate Changed"
        CERTIFICATE_EXPIRED = "CERTIFICATE_EXPIRED", "Certificate Expired"
        CERTIFICATE_EXPIRING_SOON = "CERTIFICATE_EXPIRING_SOON", "Certificate Expiring Soon"
        SERVICE_APPEARED = "SERVICE_APPEARED", "Service Appeared"
        SERVICE_DISAPPEARED = "SERVICE_DISAPPEARED", "Service Disappeared"
        ASN_CHANGED = "ASN_CHANGED", "ASN Changed"
        PROVIDER_CHANGED = "PROVIDER_CHANGED", "Provider Changed"
        LIFECYCLE_CHANGED = "LIFECYCLE_CHANGED", "Lifecycle Changed"
    
    # Valid state transitions
    VALID_TRANSITIONS = {
        Status.NEW: [Status.OPEN, Status.ACKNOWLEDGED, Status.DISMISSED],
        Status.OPEN: [Status.ACKNOWLEDGED, Status.RESOLVED, Status.DISMISSED],
        Status.ACKNOWLEDGED: [Status.OPEN, Status.RESOLVED, Status.DISMISSED],
        Status.RESOLVED: [Status.OPEN],  # Can reopen resolved alerts
        Status.DISMISSED: [],  # Dismissed alerts cannot be reopened
    }
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Asset context
    domain = models.ForeignKey(Domain, on_delete=models.CASCADE, related_name="alerts")
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="alerts")
    
    # Alert information
    alert_type = models.CharField(max_length=50, choices=AlertType.choices)
    severity = models.CharField(max_length=20, choices=Severity.choices)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.NEW)
    
    # Alert details
    title = models.CharField(max_length=255, help_text="Alert title")
    description = models.TextField(help_text="Detailed description of the alert")
    
    # Trigger event
    trigger_event_id = models.UUIDField(null=True, blank=True, help_text="Change event that triggered this alert")
    trigger_event_type = models.CharField(max_length=50, blank=True, help_text="Type of trigger event")
    
    # Evidence reference
    evidence_id = models.UUIDField(null=True, blank=True, help_text="Evidence backing this alert")
    
    # Investigation integration
    investigation = models.ForeignKey(
        "investigation.Investigation",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="alerts",
        help_text="Associated investigation"
    )
    
    # Assignment
    assigned_analyst = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="assigned_alerts",
        help_text="Analyst assigned to this alert"
    )
    
    # Resolution information
    resolution_notes = models.TextField(blank=True, help_text="Notes about how this alert was resolved")
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    acknowledged_at = models.DateTimeField(null=True, blank=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    dismissed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["domain", "-created_at"]),
            models.Index(fields=["owner", "status"]),
            models.Index(fields=["status", "severity"]),
            models.Index(fields=["alert_type", "-created_at"]),
            models.Index(fields=["assigned_analyst"]),
            models.Index(fields=["investigation"]),
        ]
    
    def __str__(self):
        return f"{self.title} ({self.domain.name}) - {self.status}"
    
    def can_transition_to(self, new_status: str) -> bool:
        """Check if a state transition is valid."""
        return new_status in self.VALID_TRANSITIONS.get(self.status, [])
    
    def transition_to(self, new_status: str, user=None, notes: str = "") -> bool:
        """
        Perform a state transition with validation.
        
        Returns True if transition succeeded, False otherwise.
        """
        if not self.can_transition_to(new_status):
            return False
        
        self.status = new_status
        
        # Update timestamps based on new status
        if new_status == self.Status.ACKNOWLEDGED:
            self.acknowledged_at = timezone.now()
        elif new_status == self.Status.RESOLVED:
            self.resolved_at = timezone.now()
            if notes:
                self.resolution_notes = notes
        elif new_status == self.Status.DISMISSED:
            self.dismissed_at = timezone.now()
        
        self.save()
        
        # Create audit event
        if user:
            from apps.accounts.services import AuditService
            AuditService.log_alert_action(user, self, new_status, notes)
        
        return True


class AlertRule(models.Model):
    """
    Alert rules for automatic alert generation.
    
    Rules define when alerts should be generated based on monitoring events.
    Only create alerts for defensible, evidence-backed triggers.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Ownership
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="alert_rules")
    
    # Rule configuration
    name = models.CharField(max_length=255, help_text="Rule name")
    description = models.TextField(blank=True, help_text="Rule description")
    
    # Trigger conditions
    alert_type = models.CharField(max_length=50, choices=Alert.AlertType.choices)
    severity = models.CharField(max_length=20, choices=Alert.Severity.choices)
    
    # Scope
    apply_to_all_domains = models.BooleanField(default=False, help_text="Apply to all user domains")
    specific_domains = models.JSONField(default=list, blank=True, help_text="List of domain IDs to apply to")
    
    # Conditions
    enabled = models.BooleanField(default=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["owner", "enabled"]),
            models.Index(fields=["alert_type"]),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.alert_type})"
