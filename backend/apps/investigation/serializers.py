"""
Serializers for the investigation app.
"""
from rest_framework import serializers
from .models import Investigation, AnalystNote


class InvestigationSerializer(serializers.ModelSerializer):
    """Serializer for Investigation model."""
    
    assigned_analyst_username = serializers.CharField(source="assigned_analyst.username", read_only=True)
    domain_name = serializers.CharField(source="domain.name", read_only=True)
    
    class Meta:
        model = Investigation
        fields = [
            "id",
            "domain",
            "domain_name",
            "owner",
            "title",
            "description",
            "status",
            "priority",
            "assigned_analyst",
            "assigned_analyst_username",
            "related_evidence",
            "related_alerts",
            "important_observations",
            "limitations",
            "created_at",
            "updated_at",
            "closed_at",
        ]
        read_only_fields = ["id", "owner", "created_at", "updated_at", "closed_at"]


class AnalystNoteSerializer(serializers.ModelSerializer):
    """Serializer for AnalystNote model."""
    
    author_username = serializers.CharField(source="author.username", read_only=True)
    
    class Meta:
        model = AnalystNote
        fields = [
            "id",
            "investigation",
            "author",
            "author_username",
            "content",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "author", "created_at", "updated_at"]
