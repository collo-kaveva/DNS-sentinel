"""
Tests for the certificates app.
"""
from django.test import TestCase
from django.utils import timezone
from datetime import timedelta
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status

from apps.dns_intelligence.models import Domain
from .models import Certificate, CertificateObservation
from .services import CertificateService, CertificateSecurityError, CertificateTimeoutError

User = get_user_model()


class CertificateModelTests(TestCase):
    """Tests for Certificate and CertificateObservation models."""
    
    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123"
        )
        self.domain = Domain.objects.create(
            name="example.com",
            owner=self.user
        )
    
    def test_certificate_creation(self):
        """Test creating a certificate."""
        cert = Certificate.objects.create(
            domain=self.domain,
            subject="example.com",
            issuer="Let's Encrypt",
            serial_number="1234567890ABCDEF",
            fingerprint="A1B2C3D4E5F6",
            fingerprint_sha256="A1B2C3D4E5F6A1B2C3D4E5F6A1B2C3D4E5F6A1B2C3D4E5F6A1B2C3D4E5F6A1B2",
            valid_from=timezone.now() - timedelta(days=30),
            valid_until=timezone.now() + timedelta(days=365),
            sans=["example.com", "www.example.com"],
            public_key_algorithm="RSA",
            public_key_size=2048,
            is_valid=True,
            is_expired=False,
        )
        
        self.assertEqual(cert.domain, self.domain)
        self.assertEqual(cert.subject, "example.com")
        self.assertEqual(cert.issuer, "Let's Encrypt")
        self.assertTrue(cert.is_valid)
        self.assertFalse(cert.is_expired)
    
    def test_certificate_observation_creation(self):
        """Test creating a certificate observation."""
        obs = CertificateObservation.objects.create(
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
        
        self.assertEqual(obs.domain, self.domain)
        self.assertEqual(obs.confidence, "HIGH")
        self.assertTrue(obs.is_valid)
    
    def test_certificate_unique_constraint(self):
        """Test that domain and fingerprint_sha256 are unique together."""
        Certificate.objects.create(
            domain=self.domain,
            subject="example.com",
            issuer="Let's Encrypt",
            serial_number="1234567890ABCDEF",
            fingerprint="A1B2C3D4E5F6",
            fingerprint_sha256="A1B2C3D4E5F6A1B2C3D4E5F6A1B2C3D4E5F6A1B2C3D4E5F6A1B2C3D4E5F6A1B2",
            valid_from=timezone.now() - timedelta(days=30),
            valid_until=timezone.now() + timedelta(days=365),
        )
        
        # Try to create duplicate
        with self.assertRaises(Exception):
            Certificate.objects.create(
                domain=self.domain,
                subject="example.com",
                issuer="Let's Encrypt",
                serial_number="1234567890ABCDEF",
                fingerprint="A1B2C3D4E5F6",
                fingerprint_sha256="A1B2C3D4E5F6A1B2C3D4E5F6A1B2C3D4E5F6A1B2C3D4E5F6A1B2C3D4E5F6A1B2",
                valid_from=timezone.now() - timedelta(days=30),
                valid_until=timezone.now() + timedelta(days=365),
            )


class CertificateServiceTests(TestCase):
    """Tests for CertificateService."""
    
    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123"
        )
        self.domain = Domain.objects.create(
            name="example.com",
            owner=self.user
        )
    
    def test_is_blocked_address_private(self):
        """Test that private addresses are blocked."""
        self.assertTrue(CertificateService._is_blocked_address("10.0.0.1"))
        self.assertTrue(CertificateService._is_blocked_address("192.168.1.1"))
        self.assertTrue(CertificateService._is_blocked_address("172.16.0.1"))
    
    def test_is_blocked_address_loopback(self):
        """Test that loopback addresses are blocked."""
        self.assertTrue(CertificateService._is_blocked_address("127.0.0.1"))
        self.assertTrue(CertificateService._is_blocked_address("::1"))
    
    def test_is_blocked_address_link_local(self):
        """Test that link-local addresses are blocked."""
        self.assertTrue(CertificateService._is_blocked_address("169.254.1.1"))
    
    def test_is_blocked_address_public(self):
        """Test that public addresses are not blocked."""
        self.assertFalse(CertificateService._is_blocked_address("8.8.8.8"))
        self.assertFalse(CertificateService._is_blocked_address("1.1.1.1"))
    
    def test_save_certificate_observation(self):
        """Test saving a certificate observation."""
        metadata = {
            "subject": "example.com",
            "issuer": "Let's Encrypt",
            "serial_number": "1234567890ABCDEF",
            "fingerprint": "A1B2C3D4E5F6",
            "fingerprint_sha256": "A1B2C3D4E5F6A1B2C3D4E5F6A1B2C3D4E5F6A1B2C3D4E5F6A1B2C3D4E5F6A1B2",
            "valid_from": timezone.now() - timedelta(days=30),
            "valid_until": timezone.now() + timedelta(days=365),
            "sans": ["example.com"],
            "public_key_algorithm": "RSA",
            "public_key_size": 2048,
            "tls_version": "TLSv1.3",
            "cipher_suite": "TLS_AES_256_GCM_SHA384",
            "is_valid": True,
            "is_expired": False,
            "is_self_signed": False,
        }
        
        obs = CertificateService.save_certificate_observation(self.domain, metadata)
        
        self.assertEqual(obs.domain, self.domain)
        self.assertEqual(obs.subject, "example.com")
        self.assertEqual(obs.issuer, "Let's Encrypt")
        self.assertTrue(obs.is_valid)
    
    def test_update_current_certificate(self):
        """Test updating current certificate."""
        metadata = {
            "subject": "example.com",
            "issuer": "Let's Encrypt",
            "serial_number": "1234567890ABCDEF",
            "fingerprint": "A1B2C3D4E5F6",
            "fingerprint_sha256": "A1B2C3D4E5F6A1B2C3D4E5F6A1B2C3D4E5F6A1B2C3D4E5F6A1B2C3D4E5F6A1B2",
            "valid_from": timezone.now() - timedelta(days=30),
            "valid_until": timezone.now() + timedelta(days=365),
            "sans": ["example.com"],
            "public_key_algorithm": "RSA",
            "public_key_size": 2048,
            "tls_version": "TLSv1.3",
            "cipher_suite": "TLS_AES_256_GCM_SHA384",
            "is_valid": True,
            "is_expired": False,
            "is_self_signed": False,
        }
        
        cert = CertificateService.update_current_certificate(self.domain, metadata)
        
        self.assertEqual(cert.domain, self.domain)
        self.assertEqual(cert.subject, "example.com")
        
        # Update again - should update existing
        metadata["issuer"] = "DigiCert"
        cert2 = CertificateService.update_current_certificate(self.domain, metadata)
        
        self.assertEqual(cert.id, cert2.id)
        self.assertEqual(cert2.issuer, "DigiCert")


class CertificateAPITests(TestCase):
    """Tests for Certificate API endpoints."""
    
    def setUp(self):
        """Set up test data."""
        self.client = APIClient()
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123"
        )
        self.client.force_authenticate(user=self.user)
        
        self.domain = Domain.objects.create(
            name="example.com",
            owner=self.user
        )
        
        self.cert = Certificate.objects.create(
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
        )
    
    def test_list_certificates(self):
        """Test listing certificates."""
        response = self.client.get("/api/certificates/certificates/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 1)
    
    def test_list_certificates_filtered_by_domain(self):
        """Test listing certificates filtered by domain."""
        response = self.client.get(
            f"/api/certificates/certificates/?domain={self.domain.id}"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 1)
    
    def test_list_certificates_user_isolation(self):
        """Test that users can only see their own certificates."""
        other_user = User.objects.create_user(
            username="otheruser",
            email="other@example.com",
            password="testpass123"
        )
        other_domain = Domain.objects.create(
            name="other.com",
            owner=other_user
        )
        Certificate.objects.create(
            domain=other_domain,
            subject="other.com",
            issuer="Let's Encrypt",
            serial_number="ABCDEF1234567890",
            fingerprint="F6E5D4C3B2A1",
            fingerprint_sha256="F6E5D4C3B2A1F6E5D4C3B2A1F6E5D4C3B2A1F6E5D4C3B2A1F6E5D4C3B2A1F6E5",
            valid_from=timezone.now() - timedelta(days=30),
            valid_until=timezone.now() + timedelta(days=365),
            sans=["other.com"],
            is_valid=True,
            is_expired=False,
        )
        
        response = self.client.get("/api/certificates/certificates/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 1)
    
    def test_retrieve_certificate(self):
        """Test retrieving a specific certificate."""
        response = self.client.get(f"/api/certificates/certificates/{self.cert.id}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["subject"], "example.com")
    
    def test_certificate_history(self):
        """Test getting certificate history."""
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
            f"/api/certificates/certificates/history/?domain_id={self.domain.id}"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(response.data), 1)
    
    def test_certificate_status(self):
        """Test getting certificate status."""
        response = self.client.get(
            f"/api/certificates/certificates/status/?domain_id={self.domain.id}"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["has_certificate"])
        self.assertTrue(response.data["is_valid"])
    
    def test_certificate_issuer_distribution(self):
        """Test getting issuer distribution."""
        response = self.client.get("/api/certificates/certificates/issuer_distribution/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreater(len(response.data), 0)
    
    def test_certificate_changes(self):
        """Test getting certificate changes."""
        # Create multiple observations with different fingerprints
        CertificateObservation.objects.create(
            domain=self.domain,
            subject="example.com",
            issuer="Let's Encrypt",
            serial_number="1234567890ABCDEF",
            fingerprint="A1B2C3D4E5F6",
            fingerprint_sha256="A1B2C3D4E5F6A1B2C3D4E5F6A1B2C3D4E5F6A1B2C3D4E5F6A1B2C3D4E5F6A1B2",
            valid_from=timezone.now() - timedelta(days=60),
            valid_until=timezone.now() + timedelta(days=300),
            sans=["example.com"],
            is_valid=True,
            is_expired=False,
            confidence="HIGH",
        )
        
        CertificateObservation.objects.create(
            domain=self.domain,
            subject="example.com",
            issuer="DigiCert",
            serial_number="FEDCBA0987654321",
            fingerprint="F6E5D4C3B2A1",
            fingerprint_sha256="F6E5D4C3B2A1F6E5D4C3B2A1F6E5D4C3B2A1F6E5D4C3B2A1F6E5D4C3B2A1F6E5",
            valid_from=timezone.now() - timedelta(days=30),
            valid_until=timezone.now() + timedelta(days=365),
            sans=["example.com"],
            is_valid=True,
            is_expired=False,
            confidence="HIGH",
        )
        
        response = self.client.get(
            f"/api/certificates/certificates/changes/?domain_id={self.domain.id}"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
