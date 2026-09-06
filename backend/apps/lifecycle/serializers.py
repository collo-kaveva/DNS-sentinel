"""
Serializers for the lifecycle app.
"""
from rest_framework import serializers
from .models import Evidence, EvidenceRelationship, LifecycleAssessment


class EvidenceSerializer(serializers.ModelSerializer):
    """Serializer for Evidence model."""
    
    class Meta:
        model = Evidence
        fields = [
            "id",
            "domain",
            "evidence_type",
            "status",
            "confidence",
            "source",
            "collection_method",
            "observation",
            "entity_name",
            "entity_type",
            "related_object_id",
            "related_object_type",
            "metadata",
            "observed_at",
            "first_observed",
            "last_observed",
        ]
        read_only_fields = ["id", "owner", "observed_at", "first_observed", "last_observed"]


class EvidenceRelationshipSerializer(serializers.ModelSerializer):
    """Serializer for EvidenceRelationship model."""
    
    from_evidence_details = EvidenceSerializer(source="from_evidence", read_only=True)
    to_evidence_details = EvidenceSerializer(source="to_evidence", read_only=True)
    
    class Meta:
        model = EvidenceRelationship
        fields = [
            "id",
            "from_evidence",
            "to_evidence",
            "from_evidence_details",
            "to_evidence_details",
            "relationship_type",
            "confidence",
            "observed_at",
        ]
        read_only_fields = ["id", "observed_at"]


class LifecycleAssessmentSerializer(serializers.ModelSerializer):
    """Serializer for LifecycleAssessment model."""
    
    class Meta:
        model = LifecycleAssessment
        fields = [
            "id",
            "domain",
            "classification",
            "confidence",
            "supporting_evidence",
            "contradicting_evidence",
            "model_version",
            "limitations",
            "explanation",
            "generated_at",
        ]
        read_only_fields = ["id", "owner", "generated_at"]
