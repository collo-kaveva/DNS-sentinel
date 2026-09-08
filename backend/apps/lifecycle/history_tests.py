"""
Tests for the Unified History API.
"""
from django.test import TestCase
from django.utils import timezone
from datetime import timedelta
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status

from apps.dns_intelligence.models import Domain, DNSObservation
from apps.certificates.models import CertificateObservation
from apps.services.models import ServiceObservation
from .models import LifecycleAssessment
from .history_api import UnifiedHistoryViewSet

User = get_user_model()


class HistoryAPITests(TestCase):
    """Tests for Unified History API endpoints."""
    
    def setUp(self):
        """Set up test data."""
        self.client = APIClient()
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123"
        )
        self.domain = Domain.objects.create(
            name="example.com",
            owner=self.user
        )
        self.client.force_authenticate(user=self.user)
    
    def test_timeline_endpoint(self):
        """Test getting unified timeline for a domain."""
        # Create some observations
        DNSObservation.objects.create(
            domain=self.domain,
            hostname="example.com",
            record_type="A",
            values=["1.2.3.4"],
            response_code="NOERROR",
            source="DNS Resolver",
            confidence="HIGH",
            observed_at=timezone.now() - timedelta(days=10),
        )
        
        CertificateObservation.objects.create(
            domain=self.domain,
            subject="example.com",
            issuer="Let's Encrypt",
            serial_number="1234567890ABCDEF",
            fingerprint="A1B2C3D4E5F6",
            fingerprint_sha256="A1B2C3D4E5F6A1B2C3D4E5F6A1B2C3D4E5F6A1B2C3D4E5F6A1B2C3D4E5F6A1B2",
            valid_from=timezone.now() - timedelta(days=30),
            valid_until=timezone.now() + timedelta(days=365),
            sans=["example.com"],
            is_valid=True,
            is_expired=False,
            confidence="HIGH",
        )
        
        response = self.client.get(
            f"/api/lifecycle/history/timeline/?domain_id={self.domain.id}"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("events", response.data)
        self.assertIn("domain_id", response.data)
        self.assertGreater(len(response.data["events"]), 0)
    
    def test_timeline_filtered_by_event_type(self):
        """Test filtering timeline by event type."""
        DNSObservation.objects.create(
            domain=self.domain,
            hostname="example.com",
            record_type="A",
            values=["1.2.3.4"],
            response_code="NOERROR",
            source="DNS Resolver",
            confidence="HIGH",
            observed_at=timezone.now() - timedelta(days=10),
        )
        
        response = self.client.get(
            f"/api/lifecycle/history/timeline/?domain_id={self.domain.id}&event_type=DNS_OBSERVATION"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Check that only DNS events are returned
        for event in response.data["events"]:
            self.assertEqual(event["event_type"], "DNS_OBSERVATION")
    
    def test_timeline_filtered_by_date_range(self):
        """Test filtering timeline by date range."""
        DNSObservation.objects.create(
            domain=self.domain,
            hostname="example.com",
            record_type="A",
            values=["1.2.3.4"],
            response_code="NOERROR",
            source="DNS Resolver",
            confidence="HIGH",
            observed_at=timezone.now() - timedelta(days=10),
        )
        
        date_from = (timezone.now() - timedelta(days=15)).strftime("%Y-%m-%d %H:%M:%S")
        date_to = (timezone.now() - timedelta(days=5)).strftime("%Y-%m-%d %H:%M:%S")
        
        response = self.client.get(
            f"/api/lifecycle/history/timeline/?domain_id={self.domain.id}&date_from={date_from}&date_to={date_to}"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_timeline_user_isolation(self):
        """Test that users can only see their own domain timeline."""
        other_user = User.objects.create_user(
            username="otheruser",
            email="other@example.com",
            password="testpass123"
        )
        other_domain = Domain.objects.create(
            name="other.com",
            owner=other_user
        )
        
        DNSObservation.objects.create(
            domain=other_domain,
            hostname="other.com",
            record_type="A",
            values=["5.6.7.8"],
            response_code="NOERROR",
            source="DNS Resolver",
            confidence="HIGH",
            observed_at=timezone.now() - timedelta(days=10),
        )
        
        response = self.client.get(
            f"/api/lifecycle/history/timeline/?domain_id={other_domain.id}"
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    def test_asset_history_dns(self):
        """Test getting DNS asset history."""
        DNSObservation.objects.create(
            domain=self.domain,
            hostname="example.com",
            record_type="A",
            values=["1.2.3.4"],
            response_code="NOERROR",
            source="DNS Resolver",
            confidence="HIGH",
            observed_at=timezone.now() - timedelta(days=10),
        )
        
        response = self.client.get(
            f"/api/lifecycle/history/asset/?domain_id={self.domain.id}&asset_type=DNS&asset_identifier=example.com"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("history", response.data)
        self.assertGreater(len(response.data["history"]), 0)
    
    def test_asset_history_certificate(self):
        """Test getting certificate asset history."""
        cert = CertificateObservation.objects.create(
            domain=self.domain,
            subject="example.com",
            issuer="Let's Encrypt",
            serial_number="1234567890ABCDEF",
            fingerprint="A1B2C3D4E5F6",
            fingerprint_sha256="A1B2C3D4E5F6A1B2C3D4E5F6A1B2C3D4E5F6A1B2C3D4E5F6A1B2C3D4E5F6A1B2",
            valid_from=timezone.now() - timedelta(days=30),
            valid_until=timezone.now() + timedelta(days=365),
            sans=["example.com"],
            is_valid=True,
            is_expired=False,
            confidence="HIGH",
        )
        
        response = self.client.get(
            f"/api/lifecycle/history/asset/?domain_id={self.domain.id}&asset_type=CERTIFICATE&asset_identifier={cert.fingerprint_sha256}"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("history", response.data)
    
    def test_asset_history_service(self):
        """Test getting service asset history."""
        service = ServiceObservation.objects.create(
            domain=self.domain,
            ip_address="1.2.3.4",
            port=443,
            protocol="TCP",
            service_type="HTTPS",
            is_available=True,
            http_status=200,
            ssl_tls_enabled=True,
            confidence="MEDIUM",
        )
        
        response = self.client.get(
            f"/api/lifecycle/history/asset/?domain_id={self.domain.id}&asset_type=SERVICE&asset_identifier=1.2.3.4:443"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("history", response.data)
    
    def test_asset_history_invalid_asset_type(self):
        """Test that invalid asset type returns error."""
        response = self.client.get(
            f"/api/lifecycle/history/asset/?domain_id={self.domain.id}&asset_type=INVALID&asset_identifier=test"
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_asset_history_missing_parameters(self):
        """Test that missing parameters return error."""
        response = self.client.get(
            f"/api/lifecycle/history/asset/?domain_id={self.domain.id}"
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_timeline_limit_parameter(self):
        """Test that limit parameter works correctly."""
        # Create multiple observations
        for i in range(10):
            DNSObservation.objects.create(
                domain=self.domain,
                hostname="example.com",
                record_type="A",
                values=[f"1.2.3.{i}"],
                response_code="NOERROR",
                source="DNS Resolver",
                confidence="HIGH",
                observed_at=timezone.now() - timedelta(days=i),
            )
        
        response = self.client.get(
            f"/api/lifecycle/history/timeline/?domain_id={self.domain.id}&limit=5"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertLessEqual(len(response.data["events"]), 5)
    
    def test_timeline_includes_all_event_types(self):
        """Test that timeline includes all event types."""
        DNSObservation.objects.create(
            domain=self.domain,
            hostname="example.com",
            record_type="A",
            values=["1.2.3.4"],
            response_code="NOERROR",
            source="DNS Resolver",
            confidence="HIGH",
            observed_at=timezone.now() - timedelta(days=10),
        )
        
        CertificateObservation.objects.create(
            domain=self.domain,
            subject="example.com",
            issuer="Let's Encrypt",
            serial_number="1234567890ABCDEF",
            fingerprint="A1B2C3D4E5F6",
            fingerprint_sha256="A1B2C3D4E5F6A1B2C3D4E5F6A1B2C3D4E5F6A1B2C3D4E5F6A1B2C3D4E5F6A1B2",
            valid_from=timezone.now() - timedelta(days=30),
            valid_until=timezone.now() + timedelta(days=365),
            sans=["example.com"],
            is_valid=True,
            is_expired=False,
            confidence="HIGH",
        )
        
        ServiceObservation.objects.create(
            domain=self.domain,
            ip_address="1.2.3.4",
            port=443,
            protocol="TCP",
            service_type="HTTPS",
            is_available=True,
            http_status=200,
            ssl_tls_enabled=True,
            confidence="MEDIUM",
        )
        
        LifecycleAssessment.objects.create(
            domain=self.domain,
            owner=self.user,
            classification="ACTIVE",
            confidence=0.85,
            supporting_evidence=[],
            contradicting_evidence=[],
            model_version="1.0",
            explanation="Test",
        )
        
        response = self.client.get(
            f"/api/lifecycle/history/timeline/?domain_id={self.domain.id}"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        event_types = set(event["event_type"] for event in response.data["events"])
        self.assertIn("DNS_OBSERVATION", event_types)
        self.assertIn("CERTIFICATE", event_types)
        self.assertIn("SERVICE", event_types)
        self.assertIn("LIFECYCLE", event_types)
