"""
Serializers for the alerts app.
"""
from rest_framework import serializers
from .models import Alert, AlertRule


class AlertSerializer(serializers.ModelSerializer):
    domain_name = serializers.CharField(source="domain.name", read_only=True)
    owner_username = serializers.CharField(source="owner.username", read_only=True)
    assigned_analyst_username = serializers.CharField(source="assigned_analyst.username", read_only=True, allow_null=True)
    
    class Meta:
        model = Alert
        fields = (
            "id", "domain", "domain_name", "owner", "owner_username",
            "alert_type", "severity", "status", "title", "description",
            "trigger_event_id", "trigger_event_type", "evidence_id",
            "investigation", "assigned_analyst", "assigned_analyst_username",
            "resolution_notes", "created_at", "acknowledged_at", "resolved_at", "dismissed_at",
        )
        read_only_fields = (
            "id", "domain", "owner", "created_at", "acknowledged_at",
            "resolved_at", "dismissed_at",
        )


class AlertCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating alerts (used by monitoring system)."""
    
    class Meta:
        model = Alert
        fields = (
            "domain", "alert_type", "severity", "title", "description",
            "trigger_event_id", "trigger_event_type", "evidence_id",
        )


class AlertStatusTransitionSerializer(serializers.Serializer):
    """Serializer for alert status transitions."""
    status = serializers.ChoiceField(choices=Alert.Status.choices)
    notes = serializers.CharField(required=False, allow_blank=True)


class AlertAssignmentSerializer(serializers.Serializer):
    """Serializer for assigning alerts to analysts."""
    assigned_analyst_id = serializers.IntegerField(required=False, allow_null=True)


class AlertInvestigationSerializer(serializers.Serializer):
    """Serializer for linking alerts to investigations."""
    investigation_id = serializers.UUIDField(required=False, allow_null=True)


class AlertRuleSerializer(serializers.ModelSerializer):
    owner_username = serializers.CharField(source="owner.username", read_only=True)
    
    class Meta:
        model = AlertRule
        fields = (
            "id", "owner", "owner_username", "name", "description",
            "alert_type", "severity", "apply_to_all_domains", "specific_domains",
            "enabled", "created_at", "updated_at",
        )
        read_only_fields = ("id", "owner", "created_at", "updated_at")