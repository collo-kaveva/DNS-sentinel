"""
DNS Sentinel — Reports app.

Models for report generation, configuration, and provenance.
Reports are generated from actual stored observations with proper
evidence backing and security controls.
"""
import uuid
from django.db import models
from django.conf import settings

from apps.dns_intelligence.models import Domain


class Report(models.Model):
    """
    Report model for generated security reports.
    
    Reports are generated from actual stored observations and include
    proper provenance tracking. Generation is handled via Celery to avoid
    blocking Django requests.
    """
    class Status(models.TextChoices):
        QUEUED = "QUEUED", "Queued"
        GENERATING = "GENERATING", "Generating"
        COMPLETED = "COMPLETED", "Completed"
        FAILED = "FAILED", "Failed"
    
    class Format(models.TextChoices):
        JSON = "JSON", "JSON"
        HTML = "HTML", "HTML"
        PDF = "PDF", "PDF"
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Ownership and scope
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="reports")
    title = models.CharField(max_length=255, help_text="Report title")
    
    # Report scope
    domains = models.JSONField(default=list, help_text="List of domain IDs included in report")
    scope_description = models.TextField(blank=True, help_text="Description of report scope")
    
    # Report configuration
    format = models.CharField(max_length=10, choices=Format.choices, default=Format.JSON)
    requested_sections = models.JSONField(default=list, help_text="List of sections to include")
    
    # Generation status
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.QUEUED)
    error_message = models.TextField(blank=True)
    
    # Celery job reference
    celery_task_id = models.CharField(max_length=255, blank=True, help_text="Celery task ID for generation")
    
    # Report content (stored for completed reports)
    content = models.JSONField(default=dict, blank=True, help_text="Generated report content")
    content_html = models.TextField(blank=True, help_text="HTML content for HTML reports")
    
    # Metadata
    generated_at = models.DateTimeField(null=True, blank=True)
    metadata = models.JSONField(default=dict, blank=True, help_text="Report metadata")
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["owner", "-created_at"]),
            models.Index(fields=["status"]),
            models.Index(fields=["created_at"]),
        ]
    
    def __str__(self):
        return f"{self.title} ({self.status})"


class ReportSection(models.Model):
    """
    Individual section within a report.
    
    Each section represents a specific component of the report (e.g., DNS, Certificates)
    with its own provenance and supporting evidence.
    """
    class SectionType(models.TextChoices):
        EXECUTIVE_SUMMARY = "EXECUTIVE_SUMMARY", "Executive Summary"
        SCOPE = "SCOPE", "Scope"
        ASSETS = "ASSETS", "Assets"
        DNS = "DNS", "DNS"
        CERTIFICATES = "CERTIFICATES", "Certificates"
        INFRASTRUCTURE = "INFRASTRUCTURE", "Infrastructure"
        SERVICES = "SERVICES", "Services"
        LIFECYCLE = "LIFECYCLE", "Lifecycle"
        MONITORING = "MONITORING", "Monitoring"
        ALERTS = "ALERTS", "Alerts"
        HISTORY = "HISTORY", "History"
        EVIDENCE = "EVIDENCE", "Evidence"
        FINDINGS = "FINDINGS", "Findings"
        RECOMMENDATIONS = "RECOMMENDATIONS", "Recommendations"
        LIMITATIONS = "LIMITATIONS", "Limitations"
    
    class FindingStatus(models.TextChoices):
        OBSERVED = "OBSERVED", "Observed"
        HISTORICAL = "HISTORICAL", "Historical"
        INFERRED = "INFERRED", "Inferred"
        ANALYST = "ANALYST", "Analyst"
        UNKNOWN = "UNKNOWN", "Unknown"
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Context
    report = models.ForeignKey(Report, on_delete=models.CASCADE, related_name="sections")
    
    # Section information
    section_type = models.CharField(max_length=50, choices=SectionType.choices)
    title = models.CharField(max_length=255)
    content = models.TextField(help_text="Section content")
    
    # Provenance
    evidence_ids = models.JSONField(default=list, help_text="List of evidence IDs supporting this section")
    observation_ids = models.JSONField(default=list, help_text="List of observation IDs referenced")
    
    # Findings within this section
    findings = models.JSONField(default=list, help_text="List of findings with provenance")
    
    # Status classification
    status = models.CharField(
        max_length=20,
        choices=FindingStatus.choices,
        default=FindingStatus.OBSERVED,
        help_text="Classification of findings in this section"
    )
    
    # Confidence
    confidence = models.CharField(
        max_length=10,
        choices=[("HIGH", "HIGH"), ("MEDIUM", "MEDIUM"), ("LOW", "LOW")],
        default="MEDIUM"
    )
    
    # Ordering
    order = models.IntegerField(default=0, help_text="Section order within report")
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ["order", "created_at"]
        indexes = [
            models.Index(fields=["report", "order"]),
            models.Index(fields=["section_type"]),
        ]
    
    def __str__(self):
        return f"{self.title} ({self.section_type})"


class ReportFinding(models.Model):
    """
    Individual finding within a report section.
    
    Each finding preserves provenance including source observation,
    evidence, timestamp, asset, and classification.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Context
    report_section = models.ForeignKey(ReportSection, on_delete=models.CASCADE, related_name="detailed_findings")
    
    # Finding information
    title = models.CharField(max_length=255)
    description = models.TextField()
    
    # Severity
    severity = models.CharField(
        max_length=20,
        choices=[("INFO", "INFO"), ("LOW", "LOW"), ("MEDIUM", "MEDIUM"), ("HIGH", "HIGH"), ("CRITICAL", "CRITICAL")],
        default="MEDIUM"
    )
    
    # Provenance
    source_observation_id = models.UUIDField(null=True, blank=True, help_text="ID of source observation")
    source_observation_type = models.CharField(max_length=50, blank=True, help_text="Type of source observation")
    evidence_id = models.UUIDField(null=True, blank=True, help_text="Evidence ID backing this finding")
    
    # Asset context
    asset_id = models.UUIDField(null=True, blank=True, help_text="Asset ID (domain, IP, etc.)")
    asset_name = models.CharField(max_length=255, blank=True, help_text="Asset name")
    asset_type = models.CharField(max_length=50, blank=True, help_text="Asset type")
    
    # Classification
    finding_status = models.CharField(
        max_length=20,
        choices=ReportSection.FindingStatus.choices,
        default=ReportSection.FindingStatus.OBSERVED
    )
    
    # Timestamp
    observed_at = models.DateTimeField(null=True, blank=True, help_text="When the finding was observed")
    
    # Additional metadata
    metadata = models.JSONField(default=dict, blank=True, help_text="Additional finding metadata")
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ["-severity", "created_at"]
        indexes = [
            models.Index(fields=["report_section", "severity"]),
            models.Index(fields=["finding_status"]),
            models.Index(fields=["asset_id"]),
        ]
    
    def __str__(self):
        return f"{self.title} ({self.severity})"
