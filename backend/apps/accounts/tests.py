"""
Tests for accounts app - AuditEvent and UserSettings.
"""
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework.test import APIClient
from rest_framework import status

from .models import AuditEvent, UserSettings
from .services import AuditService

User = get_user_model()


class AuditEventModelTests(TestCase):
    """Tests for AuditEvent model."""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123"
        )
    
    def test_create_audit_event(self):
        """Test creating an audit event."""
        event = AuditEvent.objects.create(
            actor=self.user,
            actor_username=self.user.username,
            event_type=AuditEvent.EventType.LOGIN,
            action="User logged in",
            resource_type="User",
            resource_id=str(self.user.id),
            resource_name=self.user.username,
            result=AuditEvent.ActionResult.SUCCESS,
        )
        self.assertEqual(event.actor, self.user)
        self.assertEqual(event.event_type, AuditEvent.EventType.LOGIN)
        self.assertEqual(event.result, AuditEvent.ActionResult.SUCCESS)
        self.assertIsNotNone(event.timestamp)
    
    def test_audit_event_timestamp_auto(self):
        """Test that timestamp is auto-set."""
        event = AuditEvent.objects.create(
            actor=self.user,
            actor_username=self.user.username,
            event_type=AuditEvent.EventType.LOGIN,
            action="Test",
            resource_type="User",
            resource_id=str(self.user.id),
            result=AuditEvent.ActionResult.SUCCESS,
        )
        self.assertTrue(event.timestamp <= timezone.now())
    
    def test_audit_event_metadata(self):
        """Test storing metadata."""
        metadata = {"ip_address": "192.168.1.1", "user_agent": "TestAgent"}
        event = AuditEvent.objects.create(
            actor=self.user,
            actor_username=self.user.username,
            event_type=AuditEvent.EventType.LOGIN,
            action="Test",
            resource_type="User",
            resource_id=str(self.user.id),
            result=AuditEvent.ActionResult.SUCCESS,
            metadata=metadata,
        )
        self.assertEqual(event.metadata, metadata)


class UserSettingsModelTests(TestCase):
    """Tests for UserSettings model."""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123"
        )
    
    def test_create_user_settings(self):
        """Test creating user settings."""
        settings = UserSettings.objects.create(
            user=self.user,
            date_format=UserSettings.DateFormat.ISO_8601,
            time_format=UserSettings.TimeFormat.HOUR_24,
            timezone="UTC",
            auto_refresh=True,
            refresh_interval_minutes=5,
            default_monitoring_behavior=UserSettings.MonitoringBehavior.PASSIVE,
            email_alerts=True,
            alert_severity_threshold=UserSettings.AlertSeverity.HIGH,
            session_timeout_minutes=60,
            default_dashboard_view="overview",
        )
        self.assertEqual(settings.user, self.user)
        self.assertEqual(settings.date_format, UserSettings.DateFormat.ISO_8601)
        self.assertTrue(settings.auto_refresh)
    
    def test_user_settings_defaults(self):
        """Test default values for user settings."""
        settings = UserSettings.objects.create(user=self.user)
        self.assertEqual(settings.date_format, UserSettings.DateFormat.ISO_8601)
        self.assertEqual(settings.time_format, UserSettings.TimeFormat.HOUR_24)
        self.assertEqual(settings.timezone, "UTC")
        self.assertFalse(settings.auto_refresh)
        self.assertEqual(settings.refresh_interval_minutes, 5)
    
    def test_user_settings_updated_at(self):
        """Test that updated_at is auto-set."""
        settings = UserSettings.objects.create(user=self.user)
        self.assertIsNotNone(settings.updated_at)
        
        # Update and check updated_at changes
        old_updated_at = settings.updated_at
        settings.auto_refresh = True
        settings.save()
        self.assertGreater(settings.updated_at, old_updated_at)


class AuditServiceTests(TestCase):
    """Tests for AuditService."""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123"
        )
    
    def test_log_login(self):
        """Test logging a login event."""
        event = AuditService.log_login(self.user, "192.168.1.1", "TestAgent")
        self.assertEqual(event.event_type, AuditEvent.EventType.LOGIN)
        self.assertEqual(event.action, "User logged in")
        self.assertEqual(event.result, AuditEvent.ActionResult.SUCCESS)
        self.assertEqual(event.ip_address, "192.168.1.1")
        self.assertEqual(event.user_agent, "TestAgent")
    
    def test_log_logout(self):
        """Test logging a logout event."""
        event = AuditService.log_logout(self.user)
        self.assertEqual(event.event_type, AuditEvent.EventType.LOGOUT)
        self.assertEqual(event.action, "User logged out")
    
    def test_log_registration(self):
        """Test logging a registration event."""
        event = AuditService.log_registration(self.user)
        self.assertEqual(event.event_type, AuditEvent.EventType.REGISTRATION)
        self.assertEqual(event.action, "User account created")
    
    def test_log_domain_created(self):
        """Test logging domain creation."""
        event = AuditService.log_domain_created(
            self.user, "domain-123", "example.com"
        )
        self.assertEqual(event.event_type, AuditEvent.EventType.DOMAIN_CREATED)
        self.assertEqual(event.resource_id, "domain-123")
        self.assertEqual(event.resource_name, "example.com")
    
    def test_log_settings_updated(self):
        """Test logging settings update."""
        event = AuditService.log_settings_updated(self.user)
        self.assertEqual(event.event_type, AuditEvent.EventType.SETTINGS_UPDATED)
        self.assertEqual(event.resource_type, "UserSettings")
    
    def test_log_investigation_started(self):
        """Test logging investigation start."""
        event = AuditService.log_investigation_started(
            self.user, "inv-123", "Test Investigation"
        )
        self.assertEqual(event.event_type, AuditEvent.EventType.INVESTIGATION_STARTED)
        self.assertEqual(event.resource_name, "Test Investigation")


class AuditEventAPITests(TestCase):
    """Tests for AuditEvent API endpoints."""
    
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123"
        )
        self.client.force_authenticate(user=self.user)
        
        # Create some audit events
        AuditEvent.objects.create(
            actor=self.user,
            actor_username=self.user.username,
            event_type=AuditEvent.EventType.LOGIN,
            action="User logged in",
            resource_type="User",
            resource_id=str(self.user.id),
            result=AuditEvent.ActionResult.SUCCESS,
        )
        AuditEvent.objects.create(
            actor=self.user,
            actor_username=self.user.username,
            event_type=AuditEvent.EventType.SETTINGS_UPDATED,
            action="Settings updated",
            resource_type="UserSettings",
            resource_id=str(self.user.id),
            result=AuditEvent.ActionResult.SUCCESS,
        )
    
    def test_list_audit_events(self):
        """Test listing audit events."""
        response = self.client.get("/api/auth/audit/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 2)
    
    def test_list_audit_events_filtered_by_type(self):
        """Test filtering audit events by type."""
        response = self.client.get("/api/auth/audit/?event_type=LOGIN")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 1)
        self.assertEqual(response.data["results"][0]["event_type"], "LOGIN")
    
    def test_list_audit_events_filtered_by_result(self):
        """Test filtering audit events by result."""
        response = self.client.get("/api/auth/audit/?result=SUCCESS")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 2)
    
    def test_list_audit_events_user_isolation(self):
        """Test that users only see their own audit events."""
        other_user = User.objects.create_user(
            username="otheruser",
            email="other@example.com",
            password="testpass123"
        )
        AuditEvent.objects.create(
            actor=other_user,
            actor_username=other_user.username,
            event_type=AuditEvent.EventType.LOGIN,
            action="Other user logged in",
            resource_type="User",
            resource_id=str(other_user.id),
            result=AuditEvent.ActionResult.SUCCESS,
        )
        
        response = self.client.get("/api/auth/audit/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Should only see the 2 events for self.user, not the other user's event
        self.assertEqual(len(response.data["results"]), 2)
    
    def test_get_audit_event(self):
        """Test getting a specific audit event."""
        event = AuditEvent.objects.first()
        response = self.client.get(f"/api/auth/audit/{event.id}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["id"], str(event.id))


class UserSettingsAPITests(TestCase):
    """Tests for UserSettings API endpoints."""
    
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123"
        )
        self.client.force_authenticate(user=self.user)
        
        # Create user settings
        self.settings = UserSettings.objects.create(
            user=self.user,
            date_format=UserSettings.DateFormat.ISO_8601,
            time_format=UserSettings.TimeFormat.HOUR_24,
            timezone="UTC",
            auto_refresh=False,
            refresh_interval_minutes=5,
        )
    
    def test_get_settings(self):
        """Test getting user settings."""
        response = self.client.get("/api/auth/settings/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["date_format"], "ISO_8601")
        self.assertEqual(response.data["timezone"], "UTC")
    
    def test_update_settings(self):
        """Test updating user settings."""
        response = self.client.patch(
            "/api/auth/settings/",
            {"auto_refresh": True, "refresh_interval_minutes": 10},
            format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["auto_refresh"])
        self.assertEqual(response.data["refresh_interval_minutes"], 10)
        
        # Verify in database
        self.settings.refresh_from_db()
        self.assertTrue(self.settings.auto_refresh)
        self.assertEqual(self.settings.refresh_interval_minutes, 10)
    
    def test_update_settings_ownership_enforcement(self):
        """Test that users can only update their own settings."""
        other_user = User.objects.create_user(
            username="otheruser",
            email="other@example.com",
            password="testpass123"
        )
        other_client = APIClient()
        other_client.force_authenticate(user=other_user)
        
        response = other_client.patch(
            "/api/auth/settings/",
            {"auto_refresh": True},
            format="json"
        )
        # Should create or get other user's settings, not modify self.user's
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Original settings should be unchanged
        self.settings.refresh_from_db()
        self.assertFalse(self.settings.auto_refresh)
