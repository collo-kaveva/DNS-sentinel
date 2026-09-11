"""
Serializers for the monitoring app.
"""
from rest_framework import serializers
from .models import MonitoringConfig, MonitoringResult, ChangeEvent


class MonitoringConfigSerializer(serializers.ModelSerializer):
    class Meta:
        model = MonitoringConfig
        fields = (
            "id", "domain", "monitor_type", "is_enabled", "frequency",
            "alert_on_change", "alert_on_failure", "next_check_scheduled",
            "last_check_completed", "notes", "created_at", "updated_at",
        )
        read_only_fields = ("id", "created_at", "updated_at", "next_check_scheduled", "last_check_completed")


class MonitoringResultSerializer(serializers.ModelSerializer):
    domain_name = serializers.CharField(source="domain.name", read_only=True)
    
    class Meta:
        model = MonitoringResult
        fields = (
            "id", "domain", "domain_name", "monitoring_config", "monitor_type",
            "status", "observation_id", "observation_type", "previous_state",
            "new_state", "has_changes", "evidence_id", "scan_job_id",
            "error_message", "check_started_at", "check_completed_at",
            "duration_seconds", "created_at",
        )
        read_only_fields = fields


class ChangeEventSerializer(serializers.ModelSerializer):
    domain_name = serializers.CharField(source="domain.name", read_only=True)
    
    class Meta:
        model = ChangeEvent
        fields = (
            "id", "domain", "domain_name", "monitoring_result", "event_type",
            "description", "previous_value", "new_value", "entity_name",
            "entity_type", "evidence_id", "alert_generated", "alert_id",
            "metadata", "detected_at",
        )
        read_only_fields = fields