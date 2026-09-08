"""
Serializers for the certificates app.
"""
from rest_framework import serializers
from .models import Certificate, CertificateObservation


class CertificateSerializer(serializers.ModelSerializer):
    """Serializer for Certificate model."""
    
    domain_name = serializers.CharField(source="domain.name", read_only=True)
    days_until_expiry = serializers.SerializerMethodField()
    
    class Meta:
        model = Certificate
        fields = [
            "id",
            "domain",
            "domain_name",
            "subject",
            "issuer",
            "serial_number",
            "fingerprint",
            "fingerprint_sha256",
            "valid_from",
            "valid_until",
            "sans",
            "public_key_algorithm",
            "public_key_size",
            "tls_version",
            "cipher_suite",
            "is_valid",
            "is_expired",
            "is_self_signed",
            "source",
            "collection_timestamp",
            "first_seen",
            "last_seen",
            "days_until_expiry",
        ]
        read_only_fields = [
            "id",
            "collection_timestamp",
            "first_seen",
            "last_seen",
        ]
    
    def get_days_until_expiry(self, obj):
        """Calculate days until certificate expiry."""
        from django.utils import timezone
        if obj.valid_until:
            delta = obj.valid_until - timezone.now()
            return delta.days
        return None


class CertificateObservationSerializer(serializers.ModelSerializer):
    """Serializer for CertificateObservation model."""
    
    domain_name = serializers.CharField(source="domain.name", read_only=True)
    
    class Meta:
        model = CertificateObservation
        fields = [
            "id",
            "domain",
            "domain_name",
            "subject",
            "issuer",
            "serial_number",
            "fingerprint",
            "fingerprint_sha256",
            "valid_from",
            "valid_until",
            "sans",
            "public_key_algorithm",
            "public_key_size",
            "tls_version",
            "cipher_suite",
            "is_valid",
            "is_expired",
            "is_self_signed",
            "source",
            "collection_method",
            "confidence",
            "observed_at",
        ]
        read_only_fields = ["id", "observed_at"]


class CertificateStatusSerializer(serializers.Serializer):
    """Serializer for certificate status summary."""
    
    domain_id = serializers.UUIDField()
    domain_name = serializers.CharField()
    has_certificate = serializers.BooleanField()
    is_valid = serializers.BooleanField()
    is_expired = serializers.BooleanField()
    days_until_expiry = serializers.IntegerField(allow_null=True)
    issuer = serializers.CharField()
    subject = serializers.CharField()
    last_observed = serializers.DateTimeField()


class IssuerDistributionSerializer(serializers.Serializer):
    """Serializer for issuer distribution."""
    
    issuer = serializers.CharField()
    count = serializers.IntegerField()
    percentage = serializers.FloatField()


class CertificateChangeSerializer(serializers.Serializer):
    """Serializer for certificate changes."""
    
    domain_id = serializers.UUIDField()
    domain_name = serializers.CharField()
    old_fingerprint = serializers.CharField()
    new_fingerprint = serializers.CharField()
    old_issuer = serializers.CharField()
    new_issuer = serializers.CharField()
    changed_at = serializers.DateTimeField()
