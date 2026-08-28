from rest_framework import serializers
from .models import IPAddress, InfrastructureObservation


class IPAddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = IPAddress
        fields = (
            "id", "address", "version", "association_status", "reverse_dns",
            "asn", "network", "organization", "country",
            "is_likely_cdn", "is_likely_shared_hosting", "cdn_indicator_source",
            "rdap_available", "first_seen", "last_seen",
        )
        read_only_fields = fields


class InfrastructureObservationSerializer(serializers.ModelSerializer):
    class Meta:
        model = InfrastructureObservation
        fields = (
            "id", "address", "asn", "network", "organization", "country",
            "reverse_dns", "source", "confidence", "lookup_succeeded",
            "error_detail", "observed_at",
        )
        read_only_fields = fields
