"""
DNS Sentinel — Lifecycle app.

Evidence and provenance models for the lifecycle classification engine.
This provides the foundation for evidence correlation across all observation types.
"""
import uuid

from django.db import models
from django.conf import settings

from apps.dns_intelligence.models import Domain


class EvidenceType(models.TextChoices):
    """Types of evidence that can be collected."""
    DNS_OBSERVATION = "DNS_OBSERVATION", "DNS Observation"
    DNS_RECORD = "DNS_RECORD", "DNS Record"
    IP_ADDRESS = "IP_ADDRESS", "IP Address"
    CERTIFICATE = "CERTIFICATE", "Certificate"
    SERVICE = "SERVICE", "Service"
    ASN = "ASN", "ASN"
    PROVIDER = "PROVIDER", "Provider"
    ALERT = "ALERT", "Alert"
    LIFECYCLE_ASSESSMENT = "LIFECYCLE_ASSESSMENT", "Lifecycle Assessment"
    ANALYST_NOTE = "ANALYST_NOTE", "Analyst Note"


class EvidenceStatus(models.TextChoices):
    """Status of evidence: current, historical, or unknown."""
    OBSERVED = "OBSERVED", "Observed"
    HISTORICAL = "HISTORICAL", "Historical"
    INFERRED = "INFERRED", "Inferred"
    ANALYST = "ANALYST", "Analyst"
    UNKNOWN = "UNKNOWN", "Unknown"


class Confidence(models.TextChoices):
    """Confidence levels for evidence."""
    HIGH = "HIGH", "High"
    MEDIUM = "MEDIUM", "Medium"
    LOW = "LOW", "Low"


class Evidence(models.Model):
    """
    Core evidence model for tracking observations across all subsystems.
    
    This model provides a unified provenance layer for all observations,
    allowing the lifecycle engine to correlate evidence from DNS, infrastructure,
    certificates, services, and other sources.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Ownership and asset context
    domain = models.ForeignKey(Domain, on_delete=models.CASCADE, related_name="evidence")
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="evidence")
    
    # Evidence classification
    evidence_type = models.CharField(max_length=50, choices=EvidenceType.choices)
    status = models.CharField(max_length=20, choices=EvidenceStatus.choices, default=EvidenceStatus.OBSERVED)
    confidence = models.CharField(max_length=10, choices=Confidence.choices, default=Confidence.MEDIUM)
    
    # Provenance
    source = models.CharField(max_length=100, default="Unknown", help_text="Source of the evidence (e.g., 'Public DNS', 'RDAP', 'TLS Handshake')")
    collection_method = models.CharField(max_length=100, blank=True, help_text="How the evidence was collected")
    
    # Content
    observation = models.TextField(help_text="The actual observation or finding")
    entity_name = models.CharField(max_length=255, blank=True, help_text="Name of the entity this evidence relates to")
    entity_type = models.CharField(max_length=50, blank=True, help_text="Type of entity (domain, IP, certificate, etc.)")
    
    # Related objects for cross-referencing
    related_object_id = models.UUIDField(null=True, blank=True, help_text="ID of related object in its own table")
    related_object_type = models.CharField(max_length=100, blank=True, help_text="Type of related object (app_label.model)")
    
    # Metadata
    metadata = models.JSONField(default=dict, blank=True, help_text="Structured metadata about the evidence")
    
    # Timestamps
    observed_at = models.DateTimeField(auto_now_add=True, db_index=True, help_text="When the evidence was observed")
    first_observed = models.DateTimeField(auto_now_add=True, help_text="First time this evidence was observed")
    last_observed = models.DateTimeField(auto_now=True, help_text="Most recent observation timestamp")
    
    class Meta:
        ordering = ["-observed_at"]
        indexes = [
            models.Index(fields=["domain", "evidence_type", "observed_at"]),
            models.Index(fields=["owner", "evidence_type"]),
            models.Index(fields=["status"]),
            models.Index(fields=["confidence"]),
            models.Index(fields=["source"]),
        ]
    
    def __str__(self):
        return f"{self.evidence_type}: {self.entity_name or self.observation[:50]}"


class EvidenceRelationship(models.Model):
    """
    Relationships between evidence items.
    
    This allows the platform to model how different evidence items are connected,
    such as Domain → IP → Certificate → Service relationships.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # The two pieces of evidence being related
    from_evidence = models.ForeignKey(Evidence, on_delete=models.CASCADE, related_name="relationships_from")
    to_evidence = models.ForeignKey(Evidence, on_delete=models.CASCADE, related_name="relationships_to")
    
    # Relationship type
    relationship_type = models.CharField(max_length=100, help_text="Type of relationship (e.g., 'resolves_to', 'secured_by')")
    
    # Confidence in this relationship
    confidence = models.CharField(max_length=10, choices=Confidence.choices, default=Confidence.MEDIUM)
    
    # When this relationship was observed
    observed_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ["-observed_at"]
        indexes = [
            models.Index(fields=["from_evidence", "relationship_type"]),
            models.Index(fields=["to_evidence", "relationship_type"]),
        ]
        unique_together = [["from_evidence", "to_evidence", "relationship_type"]]
    
    def __str__(self):
        return f"{self.from_evidence} → {self.to_evidence} ({self.relationship_type})"


class LifecycleAssessment(models.Model):
    """
    Lifecycle classification result for a domain.
    
    This stores the output of the lifecycle classification engine,
    including the classification, confidence, supporting evidence, and limitations.
    """
    class LifecycleStatus(models.TextChoices):
        ACTIVE = "ACTIVE", "Active"
        LEGACY = "LEGACY", "Legacy"
        POTENTIALLY_ABANDONED = "POTENTIALLY_ABANDONED", "Potentially Abandoned"
        LIKELY_ABANDONED = "LIKELY_ABANDONED", "Likely Abandoned"
        UNKNOWN = "UNKNOWN", "Unknown"
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Asset context
    domain = models.ForeignKey(Domain, on_delete=models.CASCADE, related_name="lifecycle_assessments")
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="lifecycle_assessments")
    
    # Classification result
    classification = models.CharField(max_length=30, choices=LifecycleStatus.choices)
    confidence = models.DecimalField(max_digits=3, decimal_places=2, help_text="Confidence score (0.00-1.00)")
    
    # Evidence supporting the classification
    supporting_evidence = models.JSONField(default=list, blank=True, help_text="List of evidence IDs supporting this classification")
    contradicting_evidence = models.JSONField(default=list, blank=True, help_text="List of evidence IDs contradicting this classification")
    
    # Model information
    model_version = models.CharField(max_length=50, default="1.0", help_text="Version of the classification model used")
    
    # Limitations and explanations
    limitations = models.TextField(blank=True, help_text="Known limitations or missing data that affected this classification")
    explanation = models.TextField(blank=True, help_text="Human-readable explanation of the classification")
    
    # Timestamps
    generated_at = models.DateTimeField(auto_now_add=True, db_index=True)
    
    class Meta:
        ordering = ["-generated_at"]
        indexes = [
            models.Index(fields=["domain", "-generated_at"]),
            models.Index(fields=["classification"]),
            models.Index(fields=["owner", "classification"]),
        ]
    
    def __str__(self):
        return f"{self.domain.name}: {self.classification} ({self.confidence})"
