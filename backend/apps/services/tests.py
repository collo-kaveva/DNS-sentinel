"""
Tests for the services app.
"""
from django.test import TestCase
from django.utils import timezone
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status

from apps.dns_intelligence.models import Domain
from .models import Service, ServiceObservation
from .services import ServiceService, ServiceSecurityError

User = get_user_model()


class ServiceModelTests(TestCase):
    """Tests for Service and ServiceObservation models."""
    
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
    
    def test_service_creation(self):
        """Test creating a service."""
        service = Service.objects.create(
            domain=self.domain,
            ip_address="1.2.3.4",
            port=443,
            protocol="TCP",
            service_type="HTTPS",
            is_available=True,
            http_status=200,
            response_time_ms=50.5,
            ssl_tls_enabled=True,
        )
        
        self.assertEqual(service.domain, self.domain)
        self.assertEqual(service.ip_address, "1.2.3.4")
        self.assertEqual(service.port, 443)
        self.assertTrue(service.is_available)
        self.assertTrue(service.ssl_tls_enabled)
    
    def test_service_observation_creation(self):
        """Test creating a service observation."""
        obs = ServiceObservation.objects.create(
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
        
        self.assertEqual(obs.domain, self.domain)
        self.assertEqual(obs.confidence, "MEDIUM")
        self.assertTrue(obs.is_available)
    
    def test_service_unique_constraint(self):
        """Test that domain, ip_address, port, and protocol are unique together."""
        Service.objects.create(
            domain=self.domain,
            ip_address="1.2.3.4",
            port=443,
            protocol="TCP",
            service_type="HTTPS",
            is_available=True,
        )
        
        # Try to create duplicate
        with self.assertRaises(Exception):
            Service.objects.create(
                domain=self.domain,
                ip_address="1.2.3.4",
                port=443,
                protocol="TCP",
                service_type="HTTPS",
                is_available=True,
            )


class ServiceServiceTests(TestCase):
    """Tests for ServiceService."""
    
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
        self.assertTrue(ServiceService._is_blocked_address("10.0.0.1"))
        self.assertTrue(ServiceService._is_blocked_address("192.168.1.1"))
        self.assertTrue(ServiceService._is_blocked_address("172.16.0.1"))
    
    def test_is_blocked_address_loopback(self):
        """Test that loopback addresses are blocked."""
        self.assertTrue(ServiceService._is_blocked_address("127.0.0.1"))
        self.assertTrue(ServiceService._is_blocked_address("::1"))
    
    def test_is_blocked_address_link_local(self):
        """Test that link-local addresses are blocked."""
        self.assertTrue(ServiceService._is_blocked_address("169.254.1.1"))
    
    def test_is_blocked_address_public(self):
        """Test that public addresses are not blocked."""
        self.assertFalse(ServiceService._is_blocked_address("8.8.8.8"))
        self.assertFalse(ServiceService._is_blocked_address("1.1.1.1"))
    
    def test_is_blocked_port(self):
        """Test that administrative ports are blocked."""
        self.assertTrue(ServiceService._is_blocked_port(22))  # SSH
        self.assertTrue(ServiceService._is_blocked_port(25))  # SMTP
        self.assertTrue(ServiceService._is_blocked_port(3306))  # MySQL
        self.assertFalse(ServiceService._is_blocked_port(80))  # HTTP
        self.assertFalse(ServiceService._is_blocked_port(443))  # HTTPS
    
    def test_save_service_observation(self):
        """Test saving a service observation."""
        metadata = {
            "ip_address": "1.2.3.4",
            "port": 443,
            "protocol": "TCP",
            "service_type": "HTTPS",
            "is_available": True,
            "http_status": 200,
            "response_time_ms": 50.5,
            "ssl_tls_enabled": True,
        }
        
        obs = ServiceService.save_service_observation(self.domain, metadata)
        
        self.assertEqual(obs.domain, self.domain)
        self.assertEqual(obs.ip_address, "1.2.3.4")
        self.assertEqual(obs.port, 443)
        self.assertTrue(obs.is_available)
    
    def test_update_current_service(self):
        """Test updating current service."""
        metadata = {
            "ip_address": "1.2.3.4",
            "port": 443,
            "protocol": "TCP",
            "service_type": "HTTPS",
            "is_available": True,
            "http_status": 200,
            "ssl_tls_enabled": True,
        }
        
        service = ServiceService.update_current_service(self.domain, metadata)
        
        self.assertEqual(service.domain, self.domain)
        self.assertEqual(service.ip_address, "1.2.3.4")
        
        # Update again - should update existing
        metadata["is_available"] = False
        service2 = ServiceService.update_current_service(self.domain, metadata)
        
        self.assertEqual(service.id, service2.id)
        self.assertFalse(service2.is_available)


class ServiceAPITests(TestCase):
    """Tests for Service API endpoints."""
    
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
        
        self.service = Service.objects.create(
            domain=self.domain,
            ip_address="1.2.3.4",
            port=443,
            protocol="TCP",
            service_type="HTTPS",
            is_available=True,
            http_status=200,
            ssl_tls_enabled=True,
        )
    
    def test_list_services(self):
        """Test listing services."""
        response = self.client.get("/api/services/services/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 1)
    
    def test_list_services_filtered_by_domain(self):
        """Test listing services filtered by domain."""
        response = self.client.get(
            f"/api/services/services/?domain={self.domain.id}"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 1)
    
    def test_list_services_filtered_by_ip(self):
        """Test listing services filtered by IP address."""
        response = self.client.get(
            "/api/services/services/?ip_address=1.2.3.4"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 1)
    
    def test_list_services_filtered_by_port(self):
        """Test listing services filtered by port."""
        response = self.client.get(
            "/api/services/services/?port=443"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 1)
    
    def test_list_services_user_isolation(self):
        """Test that users can only see their own services."""
        other_user = User.objects.create_user(
            username="otheruser",
            email="other@example.com",
            password="testpass123"
        )
        other_domain = Domain.objects.create(
            name="other.com",
            owner=other_user
        )
        Service.objects.create(
            domain=other_domain,
            ip_address="5.6.7.8",
            port=443,
            protocol="TCP",
            service_type="HTTPS",
            is_available=True,
        )
        
        response = self.client.get("/api/services/services/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 1)
    
    def test_retrieve_service(self):
        """Test retrieving a specific service."""
        response = self.client.get(f"/api/services/services/{self.service.id}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["ip_address"], "1.2.3.4")
    
    def test_service_history(self):
        """Test getting service history."""
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
        
        response = self.client.get(
            f"/api/services/services/history/?domain_id={self.domain.id}"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(response.data), 1)
    
    def test_service_availability(self):
        """Test getting service availability."""
        response = self.client.get(
            f"/api/services/services/availability/?domain_id={self.domain.id}"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["total_services"], 1)
        self.assertEqual(response.data["available_services"], 1)
    
    def test_http_status_distribution(self):
        """Test getting HTTP status distribution."""
        response = self.client.get("/api/services/services/http_status_distribution/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreater(len(response.data), 0)
    
    def test_service_changes(self):
        """Test getting service changes."""
        # Create multiple observations with different availability
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
        
        ServiceObservation.objects.create(
            domain=self.domain,
            ip_address="1.2.3.4",
            port=443,
            protocol="TCP",
            service_type="HTTPS",
            is_available=False,
            http_status=503,
            ssl_tls_enabled=True,
            confidence="MEDIUM",
        )
        
        response = self.client.get(
            f"/api/services/services/changes/?domain_id={self.domain.id}"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
