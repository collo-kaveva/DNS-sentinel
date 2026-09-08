"""
Serializers for the services app.
"""
from rest_framework import serializers
from .models import Service, ServiceObservation


class ServiceSerializer(serializers.ModelSerializer):
    """Serializer for Service model."""
    
    domain_name = serializers.CharField(source="domain.name", read_only=True)
    
    class Meta:
        model = Service
        fields = [
            "id",
            "domain",
            "domain_name",
            "ip_address",
            "port",
            "protocol",
            "service_type",
            "is_available",
            "http_status",
            "response_time_ms",
            "service_banner",
            "ssl_tls_enabled",
            "source",
            "collection_timestamp",
            "first_observed",
            "last_observed",
        ]
        read_only_fields = [
            "id",
            "collection_timestamp",
            "first_observed",
            "last_observed",
        ]


class ServiceObservationSerializer(serializers.ModelSerializer):
    """Serializer for ServiceObservation model."""
    
    domain_name = serializers.CharField(source="domain.name", read_only=True)
    
    class Meta:
        model = ServiceObservation
        fields = [
            "id",
            "domain",
            "domain_name",
            "ip_address",
            "port",
            "protocol",
            "service_type",
            "is_available",
            "http_status",
            "response_time_ms",
            "service_banner",
            "ssl_tls_enabled",
            "source",
            "collection_method",
            "confidence",
            "observed_at",
        ]
        read_only_fields = ["id", "observed_at"]


class ServiceAvailabilitySerializer(serializers.Serializer):
    """Serializer for service availability summary."""
    
    domain_id = serializers.UUIDField()
    domain_name = serializers.CharField()
    total_services = serializers.IntegerField()
    available_services = serializers.IntegerField()
    unavailable_services = serializers.IntegerField()
    availability_percentage = serializers.FloatField()


class HTTPStatusDistributionSerializer(serializers.Serializer):
    """Serializer for HTTP status distribution."""
    
    http_status = serializers.IntegerField()
    count = serializers.IntegerField()
    percentage = serializers.FloatField()


class ServiceChangeSerializer(serializers.Serializer):
    """Serializer for service changes."""
    
    domain_id = serializers.UUIDField()
    domain_name = serializers.CharField()
    ip_address = serializers.CharField()
    port = serializers.IntegerField()
    service_type = serializers.CharField()
    old_status = serializers.BooleanField()
    new_status = serializers.BooleanField()
    changed_at = serializers.DateTimeField()
