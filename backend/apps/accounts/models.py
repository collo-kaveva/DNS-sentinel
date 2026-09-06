"""
DNS Sentinel — Accounts app.

Extended with audit logging model and user settings model.
"""
import uuid
from django.db import models
from django.conf import settings


class AuditEvent(models.Model):
    """
    Immutable audit event model for tracking security-relevant actions.
    
    This model provides an append-only audit trail of important application
    actions such as login, asset creation, investigation starts, etc.
    Events are immutable for normal users and can only be viewed by authorized users.
    """
    class ActionResult(models.TextChoices):
        SUCCESS = "SUCCESS", "Success"
        FAILURE = "FAILURE", "Failure"
        PARTIAL = "PARTIAL", "Partial"
    
    class EventType(models.TextChoices):
        # Authentication events
        LOGIN = "LOGIN", "Login"
        LOGOUT = "LOGOUT", "Logout"
        REGISTRATION = "REGISTRATION", "Registration"
        PASSWORD_CHANGE = "PASSWORD_CHANGE", "Password Change"
        
        # Asset events
        DOMAIN_CREATED = "DOMAIN_CREATED", "Domain Created"
        DOMAIN_DELETED = "DOMAIN_DELETED", "Domain Deleted"
        DOMAIN_UPDATED = "DOMAIN_UPDATED", "Domain Updated"
        
        # Investigation events
        INVESTIGATION_STARTED = "INVESTIGATION_STARTED", "Investigation Started"
        INVESTIGATION_COMPLETED = "INVESTIGATION_COMPLETED", "Investigation Completed"
        INVESTIGATION_FAILED = "INVESTIGATION_FAILED", "Investigation Failed"
        
        # Alert events
        ALERT_ACKNOWLEDGED = "ALERT_ACKNOWLEDGED", "Alert Acknowledged"
        ALERT_RESOLVED = "ALERT_RESOLVED", "Alert Resolved"
        ALERT_REOPENED = "ALERT_REOPENED", "Alert Reopened"
        
        # Analyst events
        ANALYST_NOTE_CREATED = "ANALYST_NOTE_CREATED", "Analyst Note Created"
        ANALYST_NOTE_UPDATED = "ANALYST_NOTE_UPDATED", "Analyst Note Updated"
        ANALYST_NOTE_DELETED = "ANALYST_NOTE_DELETED", "Analyst Note Deleted"
        
        # Settings events
        SETTINGS_UPDATED = "SETTINGS_UPDATED", "Settings Updated"
        
        # Report events
        REPORT_GENERATED = "REPORT_GENERATED", "Report Generated"
        REPORT_EXPORTED = "REPORT_EXPORTED", "Report Exported"
        
        # Other events
        OTHER = "OTHER", "Other"
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Actor information
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="audit_events",
        help_text="User who performed the action"
    )
    actor_username = models.CharField(max_length=255, blank=True, help_text="Username of actor (preserved even if user deleted)")
    
    # Event information
    event_type = models.CharField(max_length=50, choices=EventType.choices)
    action = models.CharField(max_length=255, help_text="Description of the action performed")
    
    # Resource information
    resource_type = models.CharField(max_length=100, blank=True, help_text="Type of resource affected (e.g., 'Domain', 'Investigation')")
    resource_id = models.CharField(max_length=255, blank=True, help_text="ID of the affected resource")
    resource_name = models.CharField(max_length=255, blank=True, help_text="Human-readable name of the resource")
    
    # Result and status
    result = models.CharField(max_length=20, choices=ActionResult.choices, default=ActionResult.SUCCESS)
    status_code = models.IntegerField(null=True, blank=True, help_text="HTTP status code or similar")
    
    # Request metadata
    ip_address = models.GenericIPAddressField(null=True, blank=True, help_text="IP address of the request")
    user_agent = models.TextField(blank=True, help_text="User agent string")
    
    # Additional metadata
    metadata = models.JSONField(default=dict, blank=True, help_text="Structured metadata about the event")
    
    # Timestamps
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)
    
    class Meta:
        ordering = ["-timestamp"]
        indexes = [
            models.Index(fields=["actor", "-timestamp"]),
            models.Index(fields=["event_type", "-timestamp"]),
            models.Index(fields=["resource_type", "resource_id"]),
            models.Index(fields=["result", "-timestamp"]),
            models.Index(fields=["timestamp"]),
        ]
    
    def __str__(self):
        actor_str = self.actor_username or "System"
        resource_str = f"{self.resource_type}:{self.resource_name}" if self.resource_type else "N/A"
        return f"{self.timestamp} - {actor_str} - {self.event_type} - {resource_str} - {self.result}"


class UserSettings(models.Model):
    """
    User preferences and configuration settings.
    
    This model stores user-specific settings for display preferences,
    monitoring behavior, notifications, and other configurable options.
    """
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="settings",
        primary_key=True
    )
    
    # Display preferences
    date_format = models.CharField(
        max_length=20,
        choices=[
            ("ISO_8601", "ISO 8601 (YYYY-MM-DD)"),
            ("US", "US (MM/DD/YYYY)"),
            ("EUROPEAN", "European (DD/MM/YYYY)"),
        ],
        default="ISO_8601"
    )
    time_format = models.CharField(
        max_length=10,
        choices=[
            ("24_HOUR", "24-hour"),
            ("12_HOUR", "12-hour"),
        ],
        default="24_HOUR"
    )
    timezone = models.CharField(max_length=50, default="UTC")
    
    # Monitoring preferences
    auto_refresh = models.BooleanField(default=False)
    refresh_interval_minutes = models.IntegerField(default=5)
    default_monitoring_behavior = models.CharField(
        max_length=20,
        choices=[
            ("PASSIVE", "Passive (observation only)"),
            ("ACTIVE", "Active (periodic scanning)"),
        ],
        default="PASSIVE"
    )
    
    # Notification preferences
    email_alerts = models.BooleanField(default=False)
    alert_severity_threshold = models.CharField(
        max_length=10,
        choices=[
            ("INFO", "Informational"),
            ("LOW", "Low"),
            ("MEDIUM", "Medium"),
            ("HIGH", "High"),
        ],
        default="HIGH"
    )
    
    # Security preferences
    session_timeout_minutes = models.IntegerField(default=60)
    
    # Dashboard preferences
    default_dashboard_view = models.CharField(
        max_length=50,
        default="overview",
        blank=True
    )
    
    # Timestamps
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name_plural = "User Settings"
    
    def __str__(self):
        return f"Settings for {self.user.username}"
