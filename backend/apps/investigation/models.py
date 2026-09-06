"""
DNS Sentinel — Investigation app.

Models for case management and investigation tracking.
"""
import uuid
from django.db import models
from django.conf import settings

from apps.dns_intelligence.models import Domain


class Investigation(models.Model):
    """
    Investigation/case management model for tracking security investigations.
    
    This model provides persistent state for investigations that can be
    tracked over time, with status, priority, and evidence attachments.
    """
    class Status(models.TextChoices):
        OPEN = "OPEN", "Open"
        IN_PROGRESS = "IN_PROGRESS", "In Progress"
        RESOLVED = "RESOLVED", "Resolved"
        CLOSED = "CLOSED", "Closed"
        REOPENED = "REOPENED", "Reopened"
    
    class Priority(models.TextChoices):
        LOW = "LOW", "Low"
        MEDIUM = "MEDIUM", "Medium"
        HIGH = "HIGH", "High"
        CRITICAL = "CRITICAL", "Critical"
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Asset context
    domain = models.ForeignKey(Domain, on_delete=models.CASCADE, related_name="investigations")
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="investigations")
    
    # Investigation details
    title = models.CharField(max_length=255, help_text="Investigation title")
    description = models.TextField(blank=True, help_text="Investigation description")
    
    # Status and priority
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.OPEN)
    priority = models.CharField(max_length=20, choices=Priority.choices, default=Priority.MEDIUM)
    
    # Assignment
    assigned_analyst = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="assigned_investigations",
        help_text="Analyst assigned to this investigation"
    )
    
    # Related evidence and alerts
    related_evidence = models.JSONField(default=list, blank=True, help_text="List of evidence IDs related to this investigation")
    related_alerts = models.JSONField(default=list, blank=True, help_text="List of alert IDs related to this investigation")
    
    # Observations and findings
    important_observations = models.TextField(blank=True, help_text="Key observations from the investigation")
    limitations = models.TextField(blank=True, help_text="Known limitations or missing information")
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)
    closed_at = models.DateTimeField(null=True, blank=True, help_text="When the investigation was closed")
    
    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["domain", "-created_at"]),
            models.Index(fields=["owner", "status"]),
            models.Index(fields=["status", "priority"]),
            models.Index(fields=["assigned_analyst"]),
        ]
    
    def __str__(self):
        return f"{self.title} ({self.domain.name})"


class AnalystNote(models.Model):
    """
    Analyst notes for investigations.
    
    These are separate from automated observations and represent
    human-created assessments and decisions.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Context
    investigation = models.ForeignKey(Investigation, on_delete=models.CASCADE, related_name="notes")
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="analyst_notes")
    
    # Note content
    content = models.TextField(help_text="Note content")
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["investigation", "-created_at"]),
            models.Index(fields=["author", "-created_at"]),
        ]
    
    def __str__(self):
        return f"Note by {self.author.username} on {self.investigation.title}"
