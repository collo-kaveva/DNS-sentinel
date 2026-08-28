from rest_framework import serializers
from .models import Domain, ScanJob, DNSRecord, DNSObservation, DNSFinding


class DomainSerializer(serializers.ModelSerializer):
    class Meta:
        model = Domain
        fields = ("id", "name", "notes", "authorized", "created_at", "updated_at")
        read_only_fields = ("id", "created_at", "updated_at")

    def validate_authorized(self, value):
        if not value:
            raise serializers.ValidationError(
                "You must attest that you are authorized to investigate this domain."
            )
        return value


class ScanJobSerializer(serializers.ModelSerializer):
    class Meta:
        model = ScanJob
        fields = (
            "id", "domain", "job_type", "status", "progress_steps",
            "error_message", "created_at", "started_at", "finished_at",
        )
        read_only_fields = fields


class DNSRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = DNSRecord
        fields = ("id", "hostname", "record_type", "value", "ttl", "is_current", "first_seen", "last_seen")


class DNSObservationSerializer(serializers.ModelSerializer):
    class Meta:
        model = DNSObservation
        fields = (
            "id", "hostname", "record_type", "values", "response_code", "ttl",
            "resolver_used", "query_time_ms", "dnssec_signed", "source",
            "confidence", "observed_at",
        )
        read_only_fields = fields


class DNSFindingSerializer(serializers.ModelSerializer):
    class Meta:
        model = DNSFinding
        fields = ("id", "severity", "title", "description", "evidence", "created_at")
        read_only_fields = fields
