"""
Serializers for the accounts app.
"""
from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import AuditEvent, UserSettings

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "username", "email", "date_joined"]


class RegisterSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["username", "email", "password"]
        extra_kwargs = {"password": {"write_only": True}}

    def create(self, validated_data):
        password = validated_data.pop("password")
        user = User.objects.create_user(**validated_data)
        user.set_password(password)
        user.save()
        return user


class AuditEventSerializer(serializers.ModelSerializer):
    """Serializer for AuditEvent model."""
    
    actor_username = serializers.CharField(read_only=True)
    
    class Meta:
        model = AuditEvent
        fields = [
            "id",
            "actor",
            "actor_username",
            "event_type",
            "action",
            "resource_type",
            "resource_id",
            "resource_name",
            "result",
            "status_code",
            "ip_address",
            "user_agent",
            "metadata",
            "timestamp",
        ]
        read_only_fields = ["id", "actor", "actor_username", "timestamp"]


class UserSettingsSerializer(serializers.ModelSerializer):
    """Serializer for UserSettings model."""
    
    class Meta:
        model = UserSettings
        fields = [
            "date_format",
            "time_format",
            "timezone",
            "auto_refresh",
            "refresh_interval_minutes",
            "default_monitoring_behavior",
            "email_alerts",
            "alert_severity_threshold",
            "session_timeout_minutes",
            "default_dashboard_view",
            "updated_at",
        ]
        read_only_fields = ["updated_at"]
