"""
Serializers for the reports app.
"""
from rest_framework import serializers
from .models import Report, ReportSection, ReportFinding


class ReportSerializer(serializers.ModelSerializer):
    owner_username = serializers.CharField(source="owner.username", read_only=True)
    domain_count = serializers.IntegerField(source="domains", read_only=True)
    
    class Meta:
        model = Report
        fields = (
            "id", "owner", "owner_username", "title", "domains", "scope_description",
            "format", "requested_sections", "status", "error_message", "celery_task_id",
            "content", "content_html", "generated_at", "metadata",
            "created_at", "updated_at",
        )
        read_only_fields = (
            "id", "owner", "status", "error_message", "celery_task_id",
            "content", "content_html", "generated_at", "created_at", "updated_at",
        )


class ReportCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating reports."""
    
    class Meta:
        model = Report
        fields = (
            "title", "domains", "scope_description", "format", "requested_sections",
        )


class ReportSectionSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReportSection
        fields = (
            "id", "report", "section_type", "title", "content",
            "evidence_ids", "observation_ids", "findings", "status",
            "confidence", "order", "created_at",
        )
        read_only_fields = ("id", "created_at")


class ReportFindingSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReportFinding
        fields = (
            "id", "report_section", "title", "description", "severity",
            "source_observation_id", "source_observation_type", "evidence_id",
            "asset_id", "asset_name", "asset_type", "finding_status",
            "observed_at", "metadata", "created_at",
        )
        read_only_fields = ("id", "created_at")